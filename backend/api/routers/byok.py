"""BYOK API key validation endpoint (DEV-189)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.agent_engine.byok import ByokValidationStatus, validate_openai_api_key
from backend.api.byok import require_byok_api_key

router = APIRouter(prefix="/api/v1/byok", tags=["byok"])


class ValidateKeyResponse(BaseModel):
    status: ByokValidationStatus


@router.post("/validate-key", response_model=ValidateKeyResponse)
async def validate_key(
    api_key: str = Depends(require_byok_api_key),
) -> ValidateKeyResponse:
    """Validate a BYOK key. Reuses the same encrypted-header transport as
    the chat routes, so a successful validation also proves that
    transport path end to end; the actual provider call lives in the
    engine (``backend.agent_engine.byok``) per AGENTS.md §4.
    """
    status = await validate_openai_api_key(api_key)
    return ValidateKeyResponse(status=status)
