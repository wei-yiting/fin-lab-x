"""BYOK (bring-your-own-key) engine-side concerns (DEV-189, ADR-0018).

``backend/api/byok.py`` owns RSA transport — decrypting the header into a
plaintext key. This module owns everything that happens once a plaintext
key is in hand and touches the provider SDK: validating it, and
classifying a provider auth failure as "the user's own key was rejected"
vs. an unrelated failure. Kept out of ``backend/api/`` per AGENTS.md §4 —
provider-SDK interactions belong to the engine, not the HTTP layer.
"""

import logging
from typing import Literal

import openai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

_VALIDATION_TIMEOUT_SECONDS = 10.0

BYOK_KEY_REJECTED_MESSAGE = (
    "Your API key was rejected by the provider. Check it in Settings and try again."
)

ByokValidationStatus = Literal["valid", "invalid", "unexpected_error"]


class ByokKeyRejectedError(Exception):
    """A BYOK key decrypted fine but was rejected by the provider (revoked,
    exhausted, etc.). Raised by ``Orchestrator.arun`` so ``backend/api/``
    only ever needs to catch one domain exception, never inspect a
    provider SDK's own exception hierarchy directly.
    """


def is_byok_auth_rejection(exc: Exception, *, api_key: str | None) -> bool:
    """True only when the provider rejected a BYOK-supplied key.

    Never true for a server-key failure (``api_key is None``) — that's an
    operator problem, not a signal to tell a free-tier user their
    nonexistent key is invalid.
    """
    return api_key is not None and isinstance(exc, openai.AuthenticationError)


async def validate_openai_api_key(api_key: str) -> ByokValidationStatus:
    """Check whether ``api_key`` works by calling OpenAI's own models-list
    endpoint with it — zero cost to the operator, since the call is billed
    to the caller's own key.
    """
    client = AsyncOpenAI(api_key=api_key, timeout=_VALIDATION_TIMEOUT_SECONDS)
    try:
        await client.models.list()
        return "valid"
    except openai.AuthenticationError:
        return "invalid"
    except Exception:
        logger.warning("BYOK key validation hit an unexpected error.")
        return "unexpected_error"
