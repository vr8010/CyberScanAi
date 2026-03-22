"""
Scan Routes — Trigger scans, retrieve results, download PDF reports.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import io
import structlog

from app.core.database import get_db
from app.models.models import User
from app.models.schemas import ScanRequest, ScanResultResponse, ScanHistoryItem
from app.auth.jwt_handler import get_current_user
from app.services.scan_service import ScanService
from app.services.pdf_generator import generate_pdf_report

router = APIRouter()
logger = structlog.get_logger()


@router.post("/", response_model=ScanResultResponse)
async def start_scan(
    request: ScanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new security scan for the given URL.
    Runs synchronously (awaits completion) for simplicity.
    For large scale, move to Celery background tasks.
    """
    service = ScanService(db)

    # Check daily rate limit
    await service.check_scan_limit(current_user)

    # Create pending scan record
    scan = await service.create_scan(current_user, request)

    # Run scan (this takes 5–15 seconds typically)
    scan = await service.run_scan(scan.id, current_user)

    logger.info("scan_endpoint_complete", scan_id=scan.id, user_id=current_user.id)
    return ScanResultResponse.model_validate(scan)


@router.get("/history", response_model=List[ScanHistoryItem])
async def get_scan_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated scan history for the current user."""
    service = ScanService(db)
    scans = await service.get_scan_history(current_user.id, limit, offset)
    return [ScanHistoryItem.model_validate(s) for s in scans]


@router.get("/{scan_id}", response_model=ScanResultResponse)
async def get_scan_result(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full result of a specific scan."""
    service = ScanService(db)
    scan = await service.get_scan_by_id(scan_id, current_user.id)
    return ScanResultResponse.model_validate(scan)


@router.get("/{scan_id}/pdf")
async def download_pdf_report(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the scan result as a PDF report."""
    service = ScanService(db)
    scan = await service.get_scan_by_id(scan_id, current_user.id)

    if scan.status != "completed":
        raise HTTPException(status_code=400, detail="Scan is not completed yet")

    try:
        pdf_bytes = generate_pdf_report(scan)
    except Exception as e:
        logger.error("pdf_generation_error", scan_id=scan_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

    filename = f"security-report-{scan.target_url.replace('https://', '').replace('http://', '').replace('/', '-')[:50]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.delete("/{scan_id}")
async def delete_scan(
    scan_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a scan result."""
    service = ScanService(db)
    scan = await service.get_scan_by_id(scan_id, current_user.id)
    await db.delete(scan)
    await db.commit()
    return {"message": "Scan deleted successfully"}
