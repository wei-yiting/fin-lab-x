"""Generate an RSA-4096 keypair for BYOK per-request key transport (ADR-0018).

Prints two lines ready to paste directly into env configuration —
BYOK_RSA_PRIVATE_KEY for the backend deployment environment,
VITE_BYOK_RSA_PUBLIC_KEY for the frontend build environment. Never writes
key material to disk: the keypair exists only in this process's memory and
on stdout, so it can never end up committed by accident.

Run with: uv run python backend/scripts/generate_byok_keypair.py
"""

import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

KEY_SIZE = 4096


def generate_keypair() -> tuple[str, str]:
    """Generate a fresh RSA keypair, returning ``(private_pem, public_pem)``.

    Private key is PKCS8 PEM; public key is SPKI PEM. SPKI (not the PKCS1
    format used by JSEncrypt-based prior art) is required because the
    frontend's Web Crypto ``importKey`` only accepts SPKI-formatted public
    keys — see ADR-0018.
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_pem, public_pem


def _env_escape(pem: str) -> str:
    """Collapse a multi-line PEM into the single-line ``\\n``-escaped form
    env files expect."""
    return pem.replace("\n", "\\n")


def main() -> int:
    private_pem, public_pem = generate_keypair()
    print(f"BYOK_RSA_PRIVATE_KEY={_env_escape(private_pem)}")
    print()
    print(f"VITE_BYOK_RSA_PUBLIC_KEY={_env_escape(public_pem)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
