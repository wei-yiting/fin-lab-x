"""BYOK (bring-your-own-key) per-request RSA key transport (ADR-0018).

Users encrypt their own OpenAI API key client-side with RSA-OAEP against
this server's public key and send it on every request via the
``X-Custom-Openai-Api-Key`` header. This module owns the server-side half:
loading the private key, decrypting the header value, and translating
failures into the BYOK HTTP error contract. Decrypted keys are returned to
callers and never logged, cached, or persisted — only the RSA private key
itself is cached (process-lifetime, since the deployment env var it comes
from cannot change without a restart).
"""

import base64
import binascii
import logging
import os
from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.hashes import SHA256
from fastapi import Depends, Header, HTTPException

from backend.agent_engine.byok import BYOK_KEY_REJECTED_MESSAGE
from backend.common.errors import ConfigurationError

logger = logging.getLogger(__name__)

BYOK_KEY_HEADER = "X-Custom-Openai-Api-Key"

_PRIVATE_KEY_ENV_VAR = "BYOK_RSA_PRIVATE_KEY"

KEY_INVALID_DETAIL = {
    "code": "byok_key_invalid",
    "message": "Could not decrypt the provided API key. Re-save your key in Settings.",
}
NOT_CONFIGURED_DETAIL = {
    "code": "byok_not_configured",
    "message": "Bring-your-own-key is not available on this deployment.",
}
KEY_REJECTED_DETAIL = {
    "code": "byok_key_rejected",
    "message": BYOK_KEY_REJECTED_MESSAGE,
}


class ByokDecryptError(Exception):
    """The BYOK header could not be decrypted into a usable API key.

    Deliberately one exception for every failure mode (malformed base64,
    wrong/corrupted ciphertext, non-UTF-8 or empty plaintext) — callers
    must not distinguish them. The fix is identical for a user (re-save
    the key), and finer-grained detail would leak information about the
    decryption pipeline's internal state into an HTTP error.
    """


def decrypt_api_key(encrypted_b64: str, private_key: rsa.RSAPrivateKey) -> str:
    """Decrypt an RSA-OAEP (SHA-256) + base64 encoded API key.

    Pure function: no env access, no HTTP. Raises :class:`ByokDecryptError`
    on any failure — see the class docstring for why failure modes are not
    distinguished.
    """
    try:
        ciphertext = base64.b64decode(encrypted_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ByokDecryptError("Malformed base64 payload") from exc

    try:
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=SHA256()),
                algorithm=SHA256(),
                label=None,
            ),
        )
    except Exception as exc:
        raise ByokDecryptError("RSA decryption failed") from exc

    try:
        api_key = plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ByokDecryptError("Decrypted payload is not valid UTF-8") from exc

    if not api_key:
        raise ByokDecryptError("Decrypted payload is empty")

    return api_key


@lru_cache(maxsize=1)
def _load_private_key() -> rsa.RSAPrivateKey | None:
    """Load the RSA private key from env, once per process (DEV-189).

    Returns ``None`` when the env var is unset — BYOK is simply disabled
    for this deployment; free tier is unaffected. Raises
    :class:`ConfigurationError` when the env var IS set but fails to parse
    as a PEM-encoded RSA private key, so a misconfigured deployment fails
    fast at startup (see :func:`validate_byok_config`) instead of on the
    first BYOK request.
    """
    raw = os.getenv(_PRIVATE_KEY_ENV_VAR)
    if not raw:
        return None

    pem_bytes = raw.replace("\\n", "\n").encode("utf-8")
    try:
        key = serialization.load_pem_private_key(pem_bytes, password=None)
    except Exception as exc:
        raise ConfigurationError(
            f"{_PRIVATE_KEY_ENV_VAR} is set but could not be parsed as a "
            f"PEM private key: {exc}"
        ) from exc
    if not isinstance(key, rsa.RSAPrivateKey):
        raise ConfigurationError(f"{_PRIVATE_KEY_ENV_VAR} is not an RSA private key.")
    return key


def validate_byok_config() -> None:
    """Startup check: fail fast if ``BYOK_RSA_PRIVATE_KEY`` is set but
    malformed. Call once from the FastAPI lifespan.

    Missing entirely is not an error — that just means BYOK is disabled for
    this deployment (the local-dev default).
    """
    if not os.getenv(_PRIVATE_KEY_ENV_VAR):
        logger.warning(
            "%s not configured — BYOK is disabled; free tier is unaffected.",
            _PRIVATE_KEY_ENV_VAR,
        )
        return
    _load_private_key()


def get_byok_api_key(
    encrypted_api_key: str | None = Header(default=None, alias=BYOK_KEY_HEADER),
) -> str | None:
    """FastAPI dependency: decrypt the BYOK header into a usable API key.

    Returns ``None`` when the header is absent — the free-tier path,
    unchanged. Any other failure (empty header, malformed payload, decrypt
    failure, server not configured) raises :class:`HTTPException` so the
    caller never silently falls back to the server key (ADR-0018).
    """
    if encrypted_api_key is None:
        return None

    if not encrypted_api_key.strip():
        raise HTTPException(status_code=401, detail=KEY_INVALID_DETAIL)

    private_key = _load_private_key()
    if private_key is None:
        raise HTTPException(status_code=500, detail=NOT_CONFIGURED_DETAIL)

    try:
        return decrypt_api_key(encrypted_api_key, private_key)
    except ByokDecryptError:
        logger.warning("BYOK header failed to decrypt (detail withheld).")
        raise HTTPException(status_code=401, detail=KEY_INVALID_DETAIL) from None


def require_byok_api_key(
    api_key: str | None = Depends(get_byok_api_key),
) -> str:
    """Dependency for endpoints where a BYOK key is mandatory — e.g. the
    key-validation endpoint, which has no free-tier fallback to reuse an
    absent header for. Every other failure mode is identical to
    :func:`get_byok_api_key`; this only escalates the "header absent" case
    from ``None`` to the same 401 used for a malformed one.
    """
    if api_key is None:
        raise HTTPException(status_code=401, detail=KEY_INVALID_DETAIL)
    return api_key
