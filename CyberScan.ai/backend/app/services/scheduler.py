"""
Scheduler Service — APScheduler-based scheduled scan runner.
Loads all active schedules from DB on startup and runs them at configured times.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
from sqlalchemy import select
import structlog

logger = structlog.get_logger()

scheduler = AsyncIOScheduler(timezone="UTC")


def _cron_trigger(frequency: str, day_of_week: str | None, hour: int) -> CronTrigger:
    """Build a CronTrigger from schedule config."""
    if frequency == "daily":
        return CronTrigger(hour=hour, minute=0)
    elif frequency == "weekly":
        return CronTrigger(day_of_week=day_of_week or "mon", hour=hour, minute=0)
    else:  # monthly
        return CronTrigger(day=1, hour=hour, minute=0)


def _next_run(frequency: str, day_of_week: str | None, hour: int) -> datetime:
    """Calculate next run time for display."""
    trigger = _cron_trigger(frequency, day_of_week, hour)
    return trigger.get_next_fire_time(None, datetime.now(timezone.utc))


async def _execute_scheduled_scan(schedule_id: str):
    """Run a single scheduled scan — called by APScheduler."""
    from app.core.database import AsyncSessionLocal
    from app.models.models import ScheduledScan, User
    from app.models.schemas import ScanRequest
    from app.services.scan_service import ScanService

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledScan).where(ScheduledScan.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule or not schedule.is_active:
            return

        user_result = await db.execute(select(User).where(User.id == schedule.user_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active:
            return

        logger.info("scheduled_scan_start", schedule_id=schedule_id, url=schedule.url)

        service = ScanService(db)
        try:
            scan = await service.create_scan(user, ScanRequest(url=schedule.url))
            await service.run_scan(scan.id, user)

            # Update counters
            schedule.last_run_at = datetime.now(timezone.utc)
            schedule.run_count += 1
            schedule.next_run_at = _next_run(schedule.frequency, schedule.day_of_week, schedule.hour)
            await db.commit()

            logger.info("scheduled_scan_done", schedule_id=schedule_id, scan_id=scan.id)
        except Exception as e:
            logger.error("scheduled_scan_failed", schedule_id=schedule_id, error=str(e))


def add_schedule_job(schedule_id: str, frequency: str, day_of_week: str | None, hour: int):
    """Add or replace a job in the scheduler."""
    job_id = f"scan_{schedule_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(
        _execute_scheduled_scan,
        trigger=_cron_trigger(frequency, day_of_week, hour),
        id=job_id,
        args=[schedule_id],
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("job_added", job_id=job_id, frequency=frequency, hour=hour)


def remove_schedule_job(schedule_id: str):
    job_id = f"scan_{schedule_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


async def load_all_schedules():
    """Load all active schedules from DB into APScheduler on startup."""
    from app.core.database import AsyncSessionLocal
    from app.models.models import ScheduledScan

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledScan).where(ScheduledScan.is_active == True)
        )
        schedules = result.scalars().all()
        for s in schedules:
            add_schedule_job(s.id, s.frequency, s.day_of_week, s.hour)
        logger.info("schedules_loaded", count=len(schedules))
