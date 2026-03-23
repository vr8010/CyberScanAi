"""
Email Service — Resend HTTP API.
Brevo/SMTP ports blocked on Render free tier; Resend uses HTTPS only.
"""

import httpx
import base64
import structlog
from app.core.config import settings

logger = structlog.get_logger()


async def _send(
    to_email: str,
    to_name: str,
    subject: str,
    html: str,
    pdf_bytes: bytes | None = None,
    pdf_filename: str = "report.pdf",
) -> bool:
    """Send via Resend API."""
    if not settings.RESEND_API_KEY:
        logger.warning("email_skipped", reason="RESEND_API_KEY not set")
        return False

    payload: dict = {
        "from": f"CyberScan.Ai <{settings.FROM_EMAIL}>",
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    if pdf_bytes:
        payload["attachments"] = [{
            "filename": pdf_filename,
            "content": base64.b64encode(pdf_bytes).decode("utf-8"),
        }]

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if resp.status_code in (200, 201):
        logger.info("email_sent", to=to_email, subject=subject)
        return True

    logger.error("email_failed", to=to_email, status=resp.status_code, body=resp.text)
    raise RuntimeError(f"Resend error {resp.status_code}: {resp.text}")


async def send_report_email(
    to_email: str,
    to_name: str,
    target_url: str,
    risk_score: float,
    pdf_bytes: bytes,
    scan_id: str,
) -> bool:
    if not settings.RESEND_API_KEY:
        logger.warning("email_skipped", reason="RESEND_API_KEY not configured")
        return False

    color = "#EF4444" if risk_score >= 70 else "#F59E0B" if risk_score >= 40 else "#10B981"

    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#F8FAFC;padding:20px;">
      <div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;padding:32px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
        <h1 style="color:#0F172A;margin-bottom:4px;">&#128737; CyberScan.Ai</h1>
        <p style="color:#64748B;margin-top:0;">Security Report Ready</p>
        <hr style="border:none;border-top:2px solid #E2E8F0;margin:24px 0;">
        <p>Hi {to_name or 'there'},</p>
        <p>Your security scan for <strong>{target_url}</strong> is complete.</p>
        <div style="background:#F1F5F9;border-radius:8px;padding:16px;margin:24px 0;text-align:center;">
          <p style="margin:0;font-size:14px;color:#64748B;">Risk Score</p>
          <p style="margin:4px 0;font-size:48px;font-weight:bold;color:{color};">{risk_score:.0f}</p>
          <p style="margin:0;font-size:12px;color:#94A3B8;">out of 100</p>
        </div>
        <p>Full PDF report is attached. Also view in your
          <a href="{settings.FRONTEND_URL}/dashboard/scans/{scan_id}" style="color:#3B82F6;">dashboard</a>.
        </p>
        <hr style="border:none;border-top:1px solid #E2E8F0;margin:24px 0;">
        <p style="font-size:12px;color:#94A3B8;">CyberScan.Ai | AI-Powered Website Security</p>
      </div>
    </body></html>
    """

    return await _send(
        to_email=to_email,
        to_name=to_name,
        subject=f"CyberScan.Ai Security Report: {target_url}",
        html=html,
        pdf_bytes=pdf_bytes,
        pdf_filename=f"security-report-{scan_id[:8]}.pdf",
    )


async def send_welcome_email(to_email: str, to_name: str) -> bool:
    if not settings.RESEND_API_KEY:
        return False
    html = f"""
    <html><body style="font-family:Arial,sans-serif;background:#F8FAFC;padding:20px;">
      <div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;padding:32px;">
        <h1 style="color:#0F172A;">Welcome to CyberScan.Ai, {to_name or 'there'}!</h1>
        <p>Your account is ready. Start securing your websites today.</p>
        <a href="{settings.FRONTEND_URL}/dashboard"
           style="display:inline-block;background:#3B82F6;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold;margin-top:16px;">
          Go to Dashboard
        </a>
        <hr style="border:none;border-top:1px solid #E2E8F0;margin:32px 0;">
        <p style="font-size:12px;color:#94A3B8;">CyberScan.Ai | AI-Powered Website Security</p>
      </div>
    </body></html>
    """
    try:
        return await _send(to_email=to_email, to_name=to_name,
                           subject="Welcome to CyberScan.Ai", html=html)
    except Exception as e:
        logger.error("welcome_email_error", error=str(e))
        return False


# Alias used by admin route
async def _send_via_resend(to_email: str, subject: str, html: str, **kwargs) -> bool:
    return await _send(to_email=to_email, to_name="", subject=subject, html=html)
