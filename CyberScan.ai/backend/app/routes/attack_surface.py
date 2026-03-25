"""
Attack Surface Discovery Routes — run discovery and persist history.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, validator
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.auth.jwt_handler import get_current_user
from app.models.models import User, AttackSurfaceResult
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


# ── Run + Save ────────────────────────────────────────────────────────────────

@router.post("/")
async def discover_attack_surface(
    request: AttackSurfaceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.attack_surface import run_attack_surface_discovery
    try:
        result = await run_attack_surface_discovery(request.url)

        # Persist to DB
        record = AttackSurfaceResult(
            user_id=current_user.id,
            domain=result.get("domain", ""),
            url=request.url,
            result=result,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        return {**result, "id": record.id, "created_at": record.created_at}

    except Exception as e:
        logger.error("attack_surface_error", url=request.url, error=str(e))
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AttackSurfaceResult)
        .where(AttackSurfaceResult.user_id == current_user.id)
        .order_by(AttackSurfaceResult.created_at.desc())
        .limit(50)
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "domain": r.domain,
            "url": r.url,
            "created_at": r.created_at,
            "summary": r.result.get("summary", {}),
        }
        for r in rows
    ]


@router.get("/history/{record_id}")
async def get_history_item(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AttackSurfaceResult).where(
            AttackSurfaceResult.id == record_id,
            AttackSurfaceResult.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    return {**record.result, "id": record.id, "created_at": record.created_at}


@router.delete("/history/{record_id}")
async def delete_history_item(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AttackSurfaceResult).where(
            AttackSurfaceResult.id == record_id,
            AttackSurfaceResult.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(record)
    await db.commit()
    return {"message": "Deleted"}
