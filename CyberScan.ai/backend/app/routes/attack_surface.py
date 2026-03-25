"""
Attack Surface Discovery Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from app.auth.jwt_handler import get_current_user
from app.models.models import User
import structlog

router = APIRouter()
logger = structlog.get_logger()


class AttackSurfaceRequest(BaseModel):
    url: str

    @validator("url")
    def clean_url(cls, v):
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        return v


@router.post("/")
async def discover_attack_surface(
    request: AttackSurfaceRequest,
    current_user: User = Depends(get_current_user),
):
    """Run full attack surface discovery on a domain."""
    from app.services.attack_surface import run_attack_surface_discovery
    try:
        result = await run_attack_surface_discovery(request.url)
        return result
    except Exception as e:
        logger.error("attack_surface_error", url=request.url, error=str(e))
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")
