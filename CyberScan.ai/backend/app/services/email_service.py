"""
Email Service — sends security reports via Brevo SMTP (port 587).
"""

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import structlog

from app.core.config import settings

logger = structlog.get_logger()


async def _send(msg: MIMEMultipart) -> None:
    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
        timeout=30,
    )


async def send_report_email(
    to_email: str,
    to_name: str,
    target_url: str,
    risk_score: float,
    pdf_bytes: bytes,
    scan_id: str,
) -> bool:
    if not settings.SMTP_USER:
        logger.warning("email_skipped", reason="SMTP not configured")
        return False

    severity_color = (
        "#EF4444" if risk_score >= 70
        else "#F59E0B" if risk_score >= 40
        else "#10B981"
    )

    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"CyberScan.Ai Report: {target_url}"
    msg["From"]    = f"CyberScan.Ai <{settings.FROM_EMAIL}>"
    msg["To"]      = to_email

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
          <p style="margin:4px 0;font-size:48px;font-weight:bold;color:{severity_color};">{risk_score:.0f}</p>
          <p style="margin:0;font-size:12px;color:#94A3B8;">out of 100</p>
        </div>
        <p>Full report attached as PDF. View in your
          <a href="{settings.FRONTEND_URL}/dashboard/scans/{scan_id}" style="color:#3B82F6;">dashboard</a>.
        </p>
        <hr style="border:none;border-top:1px solid #E2E8F0;margin:24px 0;">
        <p style="font-size:12px;color:#94A3B8;">CyberScan.Ai | AI-Powered Website Security</p>
      </div>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))

    att = MIMEApplication(pdf_bytes, _subtype="pdf")
    att.add_header("Content-Disposition", "attachment",
                   filename=f"security-report-{scan_id[:8]}.pdf")
    msg.attach(att)

    await _send(msg)
    logger.info("report_email_sent", to=to_email, scan_id=scan_id)
    return True


async def send_welcome_email(to_email: str, to_name: str) -> bool:
    if not settings.SMTP_USER:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Welcome to CyberScan.Ai"
    msg["From"]    = f"CyberScan.Ai <{settings.FROM_EMAIL}>"
    msg["To"]      = to_email

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
    msg.attach(MIMEText(html, "html"))

    try:
        await _send(msg)
        return True
    except Exception as e:
        logger.error("welcome_email_error", error=str(e))
        return False


# Keep Resend helper for admin send-email route (fallback)
async def _send_via_resend(to_email: str, subject: str, html: str, **kwargs) -> bool:
    """Fallback: send via Resend API if RESEND_API_KEY is set."""
    import httpx, base64
    if not settings.RESEND_API_KEY:
        raise RuntimeError("Neither SMTP nor Resend configured")
    payload = {"from": settings.FROM_EMAIL, "to": [to_email], "subject": subject, "html": html}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}", "Content-Type": "application/json"},
            json=payload,
        )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text}")
    return True
