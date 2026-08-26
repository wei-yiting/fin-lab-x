"""Tests for backend/api/byok.py — BYOK RSA key transport (ADR-0018).

Two independent seams:
- pure crypto (``decrypt_api_key``): no env, no HTTP, roundtrip against a
  test keypair from ``generate_byok_keypair``.
- the FastAPI dependency (``get_byok_api_key``): env-driven private key
  loading + translation of crypto failures into the BYOK HTTP error
  contract (401 ``byok_key_invalid`` / 500 ``byok_not_configured``).
"""

import base64
import logging

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from backend.api import byok
from backend.common.errors import ConfigurationError
from backend.scripts.generate_byok_keypair import generate_keypair
from backend.tests.api.conftest import encrypt_with_public_key as _encrypt


@pytest.fixture()
def keypair():
    private_pem, public_pem = generate_keypair()
    private_key = byok.serialization.load_pem_private_key(
        private_pem.encode("utf-8"), password=None
    )
    public_key = byok.serialization.load_pem_public_key(public_pem.encode("utf-8"))
    return private_key, public_key, private_pem


# Cache reset is handled by the autouse fixture in conftest.py (shared
# across every test module in this directory).


# --- decrypt_api_key: pure crypto roundtrip ---


class TestDecryptApiKeyRoundtrip:
    def test_roundtrip_recovers_original_key(self, keypair):
        private_key, public_key, _ = keypair
        encrypted = _encrypt(public_key, b"sk-proj-abc123")

        result = byok.decrypt_api_key(encrypted, private_key)

        assert result == "sk-proj-abc123"

    def test_roundtrip_with_long_key_near_4096_bit_capacity(self, keypair):
        """4096-bit OAEP-SHA256 capacity is 446 bytes — well above any
        realistic OpenAI key length; confirms the size choice isn't
        marginal like 2048-bit would be (~190 byte capacity)."""
        private_key, public_key, _ = keypair
        long_key = "sk-proj-" + "x" * 300
        encrypted = _encrypt(public_key, long_key.encode("utf-8"))

        result = byok.decrypt_api_key(encrypted, private_key)

        assert result == long_key


class TestDecryptApiKeyFailures:
    def test_malformed_base64_raises(self, keypair):
        private_key, _, _ = keypair
        with pytest.raises(byok.ByokDecryptError):
            byok.decrypt_api_key("not-valid-base64!!!", private_key)

    def test_wrong_key_cannot_decrypt(self, keypair):
        private_key, _, _ = keypair
        # Encrypt with a public key from a DIFFERENT keypair than private_key.
        _, different_public_pem = generate_keypair()
        different_public_key = byok.serialization.load_pem_public_key(
            different_public_pem.encode("utf-8")
        )
        encrypted = _encrypt(different_public_key, b"sk-proj-abc123")

        with pytest.raises(byok.ByokDecryptError):
            byok.decrypt_api_key(encrypted, private_key)

    def test_corrupted_ciphertext_raises(self, keypair):
        private_key, public_key, _ = keypair
        encrypted = _encrypt(public_key, b"sk-proj-abc123")
        corrupted = base64.b64encode(b"\x00" + base64.b64decode(encrypted)[1:]).decode(
            "ascii"
        )

        with pytest.raises(byok.ByokDecryptError):
            byok.decrypt_api_key(corrupted, private_key)

    def test_decrypted_payload_not_utf8_raises(self, keypair):
        private_key, public_key, _ = keypair
        # 0xff 0xfe is not valid UTF-8.
        encrypted = _encrypt(public_key, b"\xff\xfe")

        with pytest.raises(byok.ByokDecryptError):
            byok.decrypt_api_key(encrypted, private_key)

    def test_decrypted_empty_payload_raises(self, keypair):
        private_key, public_key, _ = keypair
        encrypted = _encrypt(public_key, b"")

        with pytest.raises(byok.ByokDecryptError):
            byok.decrypt_api_key(encrypted, private_key)


# --- private key loading + startup validation ---


class TestLoadPrivateKey:
    def test_unset_env_returns_none(self, monkeypatch):
        monkeypatch.delenv(byok._PRIVATE_KEY_ENV_VAR, raising=False)
        assert byok._load_private_key() is None

    def test_valid_pem_returns_rsa_private_key(self, monkeypatch, keypair):
        _, _, private_pem = keypair
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        key = byok._load_private_key()
        assert isinstance(key, rsa.RSAPrivateKey)

    def test_malformed_pem_raises_configuration_error(self, monkeypatch):
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, "not-a-real-pem")
        with pytest.raises(ConfigurationError):
            byok._load_private_key()

    def test_result_is_cached_across_calls(self, monkeypatch, keypair):
        _, _, private_pem = keypair
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        first = byok._load_private_key()
        monkeypatch.delenv(byok._PRIVATE_KEY_ENV_VAR, raising=False)
        second = byok._load_private_key()
        assert first is second


class TestValidateByokConfig:
    def test_unset_env_does_not_raise(self, monkeypatch, caplog):
        monkeypatch.delenv(byok._PRIVATE_KEY_ENV_VAR, raising=False)
        with caplog.at_level(logging.WARNING):
            byok.validate_byok_config()
        assert "not configured" in caplog.text

    def test_valid_pem_does_not_raise(self, monkeypatch, keypair):
        _, _, private_pem = keypair
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        byok.validate_byok_config()

    def test_malformed_pem_raises_configuration_error(self, monkeypatch):
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, "garbage")
        with pytest.raises(ConfigurationError):
            byok.validate_byok_config()


# --- get_byok_api_key: FastAPI dependency ---


class TestGetByokApiKeyDependency:
    def test_no_header_returns_none(self):
        assert byok.get_byok_api_key(None) is None

    def test_empty_header_raises_401_key_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            byok.get_byok_api_key("")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "byok_key_invalid"

    def test_whitespace_only_header_raises_401_key_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            byok.get_byok_api_key("   ")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "byok_key_invalid"

    def test_malformed_header_raises_401_key_invalid(self, monkeypatch, keypair):
        _, _, private_pem = keypair
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        with pytest.raises(HTTPException) as exc_info:
            byok.get_byok_api_key("not-valid-base64!!!")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "byok_key_invalid"

    def test_header_present_but_not_configured_raises_500(self, monkeypatch):
        monkeypatch.delenv(byok._PRIVATE_KEY_ENV_VAR, raising=False)
        with pytest.raises(HTTPException) as exc_info:
            byok.get_byok_api_key("c29tZS1jaXBoZXJ0ZXh0")
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["code"] == "byok_not_configured"

    def test_valid_header_returns_decrypted_key(self, monkeypatch, keypair):
        _, public_key, private_pem = keypair
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        encrypted = _encrypt(public_key, b"sk-proj-realkey")

        result = byok.get_byok_api_key(encrypted)

        assert result == "sk-proj-realkey"

    def test_decrypt_failure_does_not_log_header_or_key_material(
        self, monkeypatch, keypair, caplog
    ):
        _, _, private_pem = keypair
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        suspicious_header = "not-valid-base64-but-distinctive-marker-zzz"
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(HTTPException):
                byok.get_byok_api_key(suspicious_header)
        assert suspicious_header not in caplog.text

    def test_success_does_not_log_decrypted_key(self, monkeypatch, keypair, caplog):
        _, public_key, private_pem = keypair
        monkeypatch.setenv(byok._PRIVATE_KEY_ENV_VAR, private_pem.replace("\n", "\\n"))
        encrypted = _encrypt(public_key, b"sk-proj-should-not-appear-in-logs")
        with caplog.at_level(logging.DEBUG):
            byok.get_byok_api_key(encrypted)
        assert "sk-proj-should-not-appear-in-logs" not in caplog.text
