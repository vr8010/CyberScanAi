"""
Scan Service — Orchestrates scanner engine, AI report, and DB persistence.
"""

from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from app.models.models import ScanResult, ScanStatus, SeverityLevel, User, UserPlan
from app.models.schemas import ScanRequest
from app.services.scanner import ScannerEngine, calculate_risk_score, get_overall_severity
from app.services.ai_reporter import get_report_generator
from app.core.config import settings
from fastapi import HTTPException

logger = structlog.get_logger()


class ScanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = ScannerEngine()

    async def check_scan_limit(self, user: User) -> bool:
        """
        Check if user has remaining scans for today.
        Resets count at midnight UTC.
        Returns True if scan is allowed, raises HTTPException if not.
        """
        today = date.today()
        last_scan_date = user.last_scan_date

        # Reset counter if it's a new day
        if last_scan_date and last_scan_date.date() < today:
            user.scans_today = 0
            await self.db.commit()

        limit = (
            settings.FREE_SCANS_PER_DAY
            if user.plan == UserPlan.FREE
            else settings.PRO_SCANS_PER_DAY
        )

        if user.scans_today >= limit:
            plan_name = "Free" if user.plan == UserPlan.FREE else "Pro"
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "scan_limit_exceeded",
                    "message": f"You've reached your daily scan limit ({limit} scan/day on {plan_name} plan).",
                    "upgrade_required": user.plan == UserPlan.FREE,
                },
            )
        return True

    async def create_scan(self, user: User, request: ScanRequest) -> ScanResult:
        """Create a pending scan record in the DB."""
        scan = ScanResult(
            user_id=user.id,
            target_url=request.url,
            status=ScanStatus.PENDING,
        )
        self.db.add(scan)
        await self.db.commit()
        await self.db.refresh(scan)
        return scan

    async def run_scan(self, scan_id: str, user: User) -> ScanResult:
        """
        Execute the full scan pipeline:
        1. Fetch scan record
        2. Run scanner engine
        3. Generate AI report
        4. Update DB
        5. Update user scan counters
        """
        # Fetch scan
        result = await self.db.execute(
            select(ScanResult).where(ScanResult.id == scan_id)
        )
        scan = result.scalar_one_or_none()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        # Mark as running
        scan.status = ScanStatus.RUNNING
        await self.db.commit()

        try:
            logger.info("scan_start", scan_id=scan_id, url=scan.target_url)

            # ── Step 1: Run scanner engine ─────────────────────────────────
            scan_data = await self.engine.full_scan(scan.target_url)

            vulnerabilities = scan_data.get("vulnerabilities", [])
            raw_findings = scan_data.get("raw_findings", [])

            # ── Step 2: Calculate risk score ───────────────────────────────
            risk_score = calculate_risk_score(vulnerabilities)
            overall_severity = get_overall_severity(risk_score)

            # Count by severity
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for v in vulnerabilities:
                sev = v.get("severity", "low")
                sev_counts[sev] = sev_counts.get(sev, 0) + 1

            # ── Step 3: Generate AI report ────────────────────────────────
            reporter = get_report_generator()
            ai_report = await reporter.generate_report(
                url=scan.target_url,
                risk_score=risk_score,
                overall_severity=overall_severity,
                raw_findings=raw_findings,
                vulnerabilities=vulnerabilities,
                ssl_valid=scan_data.get("ssl_valid"),
                ssl_expiry_days=scan_data.get("ssl_expiry_days"),
                response_time_ms=scan_data.get("response_time_ms"),
            )

            # ── Step 4: Update scan record ────────────────────────────────
            scan.status = ScanStatus.COMPLETED
            scan.risk_score = risk_score
            scan.overall_severity = overall_severity
            scan.vulnerabilities = vulnerabilities
            scan.raw_findings = raw_findings
            scan.ai_report = ai_report
            scan.ssl_valid = scan_data.get("ssl_valid")
            scan.ssl_expiry_days = scan_data.get("ssl_expiry_days")
            scan.server_header = scan_data.get("server_header")
            scan.response_time_ms = scan_data.get("response_time_ms")
            scan.critical_count = sev_counts["critical"]
            scan.high_count = sev_counts["high"]
            scan.medium_count = sev_counts["medium"]
            scan.low_count = sev_counts["low"]
            scan.scan_duration_ms = scan_data.get("scan_duration_ms")
            scan.completed_at = datetime.now(timezone.utc)

            # Build executive summary
            scan.summary = (
                f"Found {len(vulnerabilities)} issue(s) with a risk score of {risk_score}/100. "
                f"Overall severity: {overall_severity.upper()}. "
                f"{sev_counts['critical']} critical, {sev_counts['high']} high, "
                f"{sev_counts['medium']} medium, {sev_counts['low']} low severity issues."
            )

            # ── Step 5: Update user counters ──────────────────────────────
            user.scans_today += 1
            user.total_scans += 1
            user.last_scan_date = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(scan)

            # ── Step 6: Send email report ─────────────────────────────────
            if settings.SMTP_USER:
                try:
                    from app.services.pdf_generator import generate_pdf_report
                    from app.services.email_service import send_report_email
                    pdf_bytes = generate_pdf_report(scan)
                    await send_report_email(
                        to_email=user.email,
                        to_name=user.full_name or "",
                        target_url=scan.target_url,
                        risk_score=risk_score,
                        pdf_bytes=pdf_bytes,
                        scan_id=scan.id,
                    )
                except Exception as email_err:
                    logger.warning("email_report_failed", error=str(email_err))

            logger.info(
                "scan_complete",
                scan_id=scan_id,
                url=scan.target_url,
                risk_score=risk_score,
                vuln_count=len(vulnerabilities),
            )
            return scan

        except HTTPException:
            raise
        except Exception as e:
            logger.error("scan_failed", scan_id=scan_id, error=str(e))
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)[:500]
            await self.db.commit()
            raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

    async def get_scan_history(
        self, user_id: str, limit: int = 20, offset: int = 0
    ):
        """Fetch paginated scan history for a user."""
        result = await self.db.execute(
            select(ScanResult)
            .where(ScanResult.user_id == user_id)
            .order_by(ScanResult.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_scan_by_id(self, scan_id: str, user_id: str) -> ScanResult:
        """Fetch a specific scan, ensuring ownership."""
        result = await self.db.execute(
            select(ScanResult).where(
                ScanResult.id == scan_id,
                ScanResult.user_id == user_id,
            )
        )
        scan = result.scalar_one_or_none()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        return scan
