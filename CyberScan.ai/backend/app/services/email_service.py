"""
Email Service — sends security reports and notifications via SMTP.
"""

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import structlog

from app.core.config import settings

logger = structlog.get_logger()


async def send_report_email(
    to_email: str,
    to_name: str,
    target_url: str,
    risk_score: float,
    pdf_bytes: bytes,
    scan_id: str,
):
    """Send a security report PDF via email."""
    if not settings.SMTP_USER:
        logger.warning("email_skipped", reason="SMTP not configured")
        return False

    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"CyberScan.Ai Report: {target_url}"
        msg["From"] = f"CyberScan.Ai <{settings.FROM_EMAIL}>"
        msg["To"] = to_email

        # HTML body
        severity_color = (
            "#EF4444" if risk_score >= 70
            else "#F59E0B" if risk_score >= 40
            else "#10B981"
        )
        html_body = f"""
        <html><body style="font-family: Arial, sans-serif; background: #F8FAFC; padding: 20px;">
          <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h1 style="color: #0F172A; margin-bottom: 4px;">🛡 CyberScan.Ai</h1>
            <p style="color: #64748B; margin-top: 0;">Security Report Ready</p>
            <hr style="border: none; border-top: 2px solid #E2E8F0; margin: 24px 0;">
            <p>Hi {to_name or 'there'},</p>
            <p>Your security scan for <strong>{target_url}</strong> is complete.</p>
            <div style="background: #F1F5F9; border-radius: 8px; padding: 16px; margin: 24px 0; text-align: center;">
              <p style="margin: 0; font-size: 14px; color: #64748B;">Risk Score</p>
              <p style="margin: 4px 0; font-size: 48px; font-weight: bold; color: {severity_color};">{risk_score:.0f}</p>
              <p style="margin: 0; font-size: 12px; color: #94A3B8;">out of 100</p>
            </div>
            <p>The full detailed report is attached as a PDF. You can also view it in your <a href="{settings.FRONTEND_URL}/dashboard/scans/{scan_id}" style="color: #3B82F6;">CyberScan.Ai dashboard</a>.</p>
            <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 24px 0;">
            <p style="font-size: 12px; color: #94A3B8;">CyberScan.Ai | AI-Powered Website Security</p>
          </div>
        </body></html>
        """
        msg.attach(MIMEText(html_body, "html"))

        # Attach PDF
        attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"security-report-{scan_id[:8]}.pdf",
        )
        msg.attach(attachment)

        # Send
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("report_email_sent", to=to_email, scan_id=scan_id)
        return True

    except Exception as e:
        logger.error("email_send_error", error=str(e), to=to_email)
        return False


async def send_welcome_email(to_email: str, to_name: str):
    """Send a welcome email after registration."""
    if not settings.SMTP_USER:
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to CyberScan.Ai 🛡"
        msg["From"] = f"CyberScan.Ai <{settings.FROM_EMAIL}>"
        msg["To"] = to_email

        html = f"""
        <html><body style="font-family: Arial, sans-serif; background: #F8FAFC; padding: 20px;">
          <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 32px;">
            <h1 style="color: #0F172A;">Welcome to CyberScan.Ai, {to_name or 'there'}! 🛡</h1>
            <p>Your account is ready. Start securing your websites today.</p>
            <a href="{settings.FRONTEND_URL}/dashboard" 
               style="display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 16px;">
              Go to Dashboard →
            </a>
            <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 32px 0;">
            <p style="font-size: 12px; color: #94A3B8;">CyberScan.Ai | AI-Powered Website Security</p>
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
        return True
    except Exception as e:
        logger.error("welcome_email_error", error=str(e))
        return False
