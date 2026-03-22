"""
User Routes — Profile management, usage stats.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.models import User, ScanResult
from app.models.schemas import UserResponse, UserUpdate
from app.auth.jwt_handler import get_current_user

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile fields."""
    if data.full_name is not None:
        current_user.full_name = data.full_name
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's scan statistics for dashboard."""
    # Count scans by status
    result = await db.execute(
        select(ScanResult.status, func.count(ScanResult.id))
        .where(ScanResult.user_id == current_user.id)
        .group_by(ScanResult.status)
    )
    status_counts = dict(result.all())

    # Average risk score
    avg_result = await db.execute(
        select(func.avg(ScanResult.risk_score))
        .where(
            ScanResult.user_id == current_user.id,
            ScanResult.risk_score.isnot(None),
        )
    )
    avg_risk = avg_result.scalar_one_or_none()

    # Recent scans with high risk
    high_risk_result = await db.execute(
        select(func.count(ScanResult.id)).where(
            ScanResult.user_id == current_user.id,
            ScanResult.risk_score >= 70,
        )
    )
    high_risk_count = high_risk_result.scalar_one_or_none() or 0

    return {
        "total_scans": current_user.total_scans,
        "scans_today": current_user.scans_today,
        "plan": current_user.plan,
        "status_breakdown": status_counts,
        "average_risk_score": round(float(avg_risk), 1) if avg_risk else None,
        "high_risk_scans": high_risk_count,
    }


@router.get("/test-email")
async def test_email(current_user: User = Depends(get_current_user)):
    """Debug: test email + PDF pipeline and return exact error."""
    import traceback
    from app.core.config import settings
    result = {"user_email": current_user.email, "resend_configured": bool(settings.RESEND_API_KEY), "steps": {}}

    # Step 1: PDF
    try:
        from app.services.pdf_generator import generate_pdf_report
        class FakeScan:
            target_url = "https://example.com"
            risk_score = 42.0
            overall_severity = "medium"
            summary = "Test scan"
            vulnerabilities = []
            raw_findings = []
            ssl_valid = True
            ssl_expiry_days = 90
            server_header = None
            response_time_ms = 200
            critical_count = 0
            high_count = 0
            medium_count = 1
            low_count = 2
            id = "test-123"
            from datetime import datetime, timezone
            created_at = datetime.now(timezone.utc)

        pdf_bytes = generate_pdf_report(FakeScan())
        result["steps"]["pdf"] = f"OK - {len(pdf_bytes)} bytes"
    except Exception as e:
        result["steps"]["pdf"] = f"FAILED: {traceback.format_exc()}"
        return result

    # Step 2: Email via Resend
    try:
        from app.services.email_service import send_report_email
        sent = await send_report_email(
            to_email=current_user.email,
            to_name=current_user.full_name or "",
            target_url="https://example.com",
            risk_score=42.0,
            pdf_bytes=pdf_bytes,
            scan_id="test-123",
        )
        result["steps"]["email"] = f"OK - sent={sent}"
    except Exception as e:
        result["steps"]["email"] = f"FAILED: {traceback.format_exc()}"

    return result
