"""
Schedule Routes — CRUD for scheduled scans.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.models import ScheduledScan, User
from app.models.schemas import ScheduledScanCreate, ScheduledScanUpdate, ScheduledScanResponse
from app.auth.jwt_handler import get_current_user
from app.services.scheduler import add_schedule_job, remove_schedule_job, _next_run

router = APIRouter()

MAX_SCHEDULES = 10  # per user


@router.get("/", response_model=List[ScheduledScanResponse])
async def list_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ScheduledScan)
        .where(ScheduledScan.user_id == current_user.id)
        .order_by(ScheduledScan.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=ScheduledScanResponse)
async def create_schedule(
    data: ScheduledScanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Limit per user
    count_result = await db.execute(
        select(ScheduledScan).where(ScheduledScan.user_id == current_user.id)
    )
    if len(count_result.scalars().all()) >= MAX_SCHEDULES:
        raise HTTPException(status_code=400, detail=f"Max {MAX_SCHEDULES} schedules allowed per user")

    next_run = _next_run(data.frequency, data.day_of_week, data.hour)

    schedule = ScheduledScan(
        user_id=current_user.id,
        url=data.url,
        frequency=data.frequency,
        day_of_week=data.day_of_week,
        hour=data.hour,
        email_notify=data.email_notify,
        next_run_at=next_run,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    # Register with APScheduler
    add_schedule_job(schedule.id, schedule.frequency, schedule.day_of_week, schedule.hour)

    return schedule


@router.patch("/{schedule_id}", response_model=ScheduledScanResponse)
async def update_schedule(
    schedule_id: str,
    data: ScheduledScanUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ScheduledScan).where(
            ScheduledScan.id == schedule_id,
            ScheduledScan.user_id == current_user.id,
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(schedule, field, value)

    schedule.next_run_at = _next_run(schedule.frequency, schedule.day_of_week, schedule.hour)
    await db.commit()
    await db.refresh(schedule)

    # Re-register job
    if schedule.is_active:
        add_schedule_job(schedule.id, schedule.frequency, schedule.day_of_week, schedule.hour)
    else:
        remove_schedule_job(schedule.id)

    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ScheduledScan).where(
            ScheduledScan.id == schedule_id,
            ScheduledScan.user_id == current_user.id,
        )
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    remove_schedule_job(schedule.id)
    await db.delete(schedule)
    await db.commit()
    return {"message": "Schedule deleted"}
