"""
Admin Routes — Full platform management. Requires admin role.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List, Optional
from datetime import date
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import User, ScanResult, UserPlan
from app.models.schemas import UserResponse, AdminStats, ScanResultResponse
from app.auth.jwt_handler import get_current_admin

router = APIRouter()


# ── Bootstrap (one-time admin setup) ─────────────────────────────────────────

@router.post("/bootstrap")
async def bootstrap_admin(
    secret: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Make the first registered user an admin. Requires BOOTSTRAP_SECRET env var."""
    from app.core.config import settings
    if not settings.BOOTSTRAP_SECRET or secret != settings.BOOTSTRAP_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    result = await db.execute(select(User).order_by(User.created_at.asc()).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    user.is_admin = True
    await db.commit()
    return {"message": f"{user.email} is now admin"}


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStats)
async def get_platform_stats(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    pro_users   = (await db.execute(select(func.count(User.id)).where(User.plan == UserPlan.PRO))).scalar_one()
    total_scans = (await db.execute(select(func.count(ScanResult.id)))).scalar_one()
    today_scans = (await db.execute(
        select(func.count(ScanResult.id)).where(func.date(ScanResult.created_at) == date.today())
    )).scalar_one()
    avg_risk = (await db.execute(
        select(func.avg(ScanResult.risk_score)).where(ScanResult.risk_score.isnot(None))
    )).scalar_one_or_none()

    return AdminStats(
        total_users=total_users,
        pro_users=pro_users,
        free_users=total_users - pro_users,
        total_scans=total_scans,
        scans_today=today_scans,
        avg_risk_score=round(float(avg_risk), 1) if avg_risk else None,
    )


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(limit).offset(offset))
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


@router.patch("/users/{user_id}/plan")
async def change_user_plan(
    user_id: str,
    plan: str = Query(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.plan = plan
    await db.commit()
    return {"message": f"Plan updated to {plan}"}


@router.patch("/users/{user_id}/admin")
async def toggle_admin(
    user_id: str,
    is_admin: bool = Query(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own admin status")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = is_admin
    await db.commit()
    return {"message": f"Admin set to {is_admin}"}


@router.patch("/users/{user_id}/ban")
async def toggle_ban(
    user_id: str,
    is_active: bool = Query(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot ban yourself")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = is_active
    await db.commit()
    return {"message": "User " + ("unbanned" if is_active else "banned")}


@router.patch("/users/{user_id}/scan-limit")
async def set_scan_limit(
    user_id: str,
    scans_today: int = Query(..., ge=0),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.scans_today = scans_today
    await db.commit()
    return {"message": f"Scan count reset to {scans_today}"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return {"message": "User deleted"}


# ── Scans ─────────────────────────────────────────────────────────────────────

@router.get("/scans")
async def list_all_scans(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ScanResult).order_by(ScanResult.created_at.desc()).limit(limit).offset(offset)
    )
    return [
        {
            "id": s.id, "user_id": s.user_id, "target_url": s.target_url,
            "status": s.status, "risk_score": s.risk_score,
            "overall_severity": s.overall_severity,
            "critical_count": s.critical_count, "high_count": s.high_count,
            "medium_count": s.medium_count, "low_count": s.low_count,
            "created_at": s.created_at,
        }
        for s in result.scalars().all()
    ]


@router.get("/scans/{scan_id}", response_model=ScanResultResponse)
async def get_any_scan(
    scan_id: str,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    scan = (await db.execute(select(ScanResult).where(ScanResult.id == scan_id))).scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return ScanResultResponse.model_validate(scan)


@router.delete("/scans/{scan_id}")
async def delete_scan(
    scan_id: str,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(ScanResult).where(ScanResult.id == scan_id))
    await db.commit()
    return {"message": "Scan deleted"}


# ── Email ─────────────────────────────────────────────────────────────────────

class EmailRequest(BaseModel):
    to_email: str
    subject: str
    message: str


@router.post("/send-email")
async def send_custom_email(
    data: EmailRequest,
    _: User = Depends(get_current_admin),
):
    from app.core.config import settings
    import aiosmtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    if not settings.SMTP_USER:
        raise HTTPException(status_code=503, detail="SMTP not configured")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = data.subject
    msg["From"]    = f"CyberScan.Ai Admin <{settings.FROM_EMAIL}>"
    msg["To"]      = data.to_email

    html = f"""
    <html><body style="font-family:Arial,sans-serif;padding:20px;background:#F8FAFC;">
      <div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;padding:32px;">
        <h2 style="color:#0F172A;">CyberScan.Ai</h2>
        <div style="color:#334155;line-height:1.6;">{data.message.replace(chr(10),'<br>')}</div>
        <hr style="border:none;border-top:1px solid #E2E8F0;margin:24px 0;">
        <p style="font-size:12px;color:#94A3B8;">CyberScan.Ai Admin</p>
      </div>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )
    return {"message": f"Email sent to {data.to_email}"}


# ── System Settings ───────────────────────────────────────────────────────────

class SystemSettings(BaseModel):
    free_scans_per_day: Optional[int] = None
    pro_scans_per_day: Optional[int] = None


@router.get("/settings")
async def get_settings(_: User = Depends(get_current_admin)):
    from app.core.config import settings
    return {
        "free_scans_per_day": settings.FREE_SCANS_PER_DAY,
        "pro_scans_per_day": settings.PRO_SCANS_PER_DAY,
        "environment": settings.ENVIRONMENT,
        "smtp_configured": bool(settings.SMTP_USER),
        "groq_configured": bool(settings.GROQ_API_KEY),
    }


@router.patch("/settings")
async def update_settings(data: SystemSettings, _: User = Depends(get_current_admin)):
    from app.core.config import settings
    if data.free_scans_per_day is not None:
        settings.FREE_SCANS_PER_DAY = data.free_scans_per_day
    if data.pro_scans_per_day is not None:
        settings.PRO_SCANS_PER_DAY = data.pro_scans_per_day
    return {"message": "Settings updated"}
