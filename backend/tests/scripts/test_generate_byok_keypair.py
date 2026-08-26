"""Tests for backend/scripts/generate_byok_keypair.py.

RSA-OAEP roundtrip against the keypair this script produces is the primary
crypto-correctness guard for ADR-0018 — if key size, PEM format, or padding
choices ever drift out of sync with what the frontend's Web Crypto
``importKey``/``encrypt`` calls expect, this is where it breaks first.
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.scripts.generate_byok_keypair import (
    KEY_SIZE,
    _env_escape,
    generate_keypair,
)


class TestGenerateKeypair:
    def test_private_key_is_pkcs8_pem_rsa(self):
        private_pem, _ = generate_keypair()
        key = serialization.load_pem_private_key(
            private_pem.encode("utf-8"), password=None
        )
        assert isinstance(key, rsa.RSAPrivateKey)
        assert "BEGIN PRIVATE KEY" in private_pem  # PKCS8 header, not PKCS1

    def test_public_key_is_spki_pem(self):
        _, public_pem = generate_keypair()
        key = serialization.load_pem_public_key(public_pem.encode("utf-8"))
        assert isinstance(key, rsa.RSAPublicKey)
        # SPKI header — Web Crypto's importKey only accepts this, not PKCS1
        # (the format jin-t-backend used for JSEncrypt compatibility).
        assert "BEGIN PUBLIC KEY" in public_pem

    def test_key_size_is_4096(self):
        private_pem, _ = generate_keypair()
        key = serialization.load_pem_private_key(
            private_pem.encode("utf-8"), password=None
        )
        assert key.key_size == KEY_SIZE == 4096

    def test_public_key_matches_private_key(self):
        private_pem, public_pem = generate_keypair()
        private_key = serialization.load_pem_private_key(
            private_pem.encode("utf-8"), password=None
        )
        public_key = serialization.load_pem_public_key(public_pem.encode("utf-8"))
        assert private_key.public_key().public_numbers() == public_key.public_numbers()

    def test_each_call_generates_a_fresh_keypair(self):
        private_pem_1, _ = generate_keypair()
        private_pem_2, _ = generate_keypair()
        assert private_pem_1 != private_pem_2


class TestEnvEscape:
    def test_collapses_newlines_to_literal_backslash_n(self):
        pem = "-----BEGIN PRIVATE KEY-----\nABCD\nEFGH\n-----END PRIVATE KEY-----\n"
        escaped = _env_escape(pem)
        assert "\n" not in escaped
        assert escaped == (
            "-----BEGIN PRIVATE KEY-----\\nABCD\\nEFGH\\n-----END PRIVATE KEY-----\\n"
        )
