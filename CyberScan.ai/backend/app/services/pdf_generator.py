"""
PDF Report Generator using ReportLab.
Converts scan results into a downloadable PDF report.
"""

import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import structlog

logger = structlog.get_logger()

# Brand colors
PRIMARY = colors.HexColor("#0F172A")    # Dark navy
ACCENT = colors.HexColor("#3B82F6")    # Blue
DANGER = colors.HexColor("#EF4444")    # Red
WARNING = colors.HexColor("#F59E0B")   # Amber
SUCCESS = colors.HexColor("#10B981")   # Green
INFO = colors.HexColor("#6366F1")      # Indigo
LIGHT_BG = colors.HexColor("#F8FAFC") # Light gray

SEVERITY_COLORS = {
    "critical": DANGER,
    "high": colors.HexColor("#F97316"),
    "medium": WARNING,
    "low": SUCCESS,
}


def generate_pdf_report(scan_result) -> bytes:
    """
    Generate a PDF security report from a ScanResult object.
    Returns PDF bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Security Report — {scan_result.target_url}",
        author="CyberScan.Ai",
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Custom Styles ─────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=26, textColor=ACCENT, spaceAfter=0.2 * cm, alignment=TA_LEFT,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#64748B"), spaceAfter=0.5 * cm
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=14, textColor=PRIMARY, spaceBefore=0.5 * cm, spaceAfter=0.2 * cm
    )
    h3_style = ParagraphStyle(
        "H3", parent=styles["Heading3"],
        fontSize=11, textColor=colors.HexColor("#1E40AF"), spaceBefore=0.3 * cm
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=14, textColor=colors.HexColor("#334155")
    )
    code_style = ParagraphStyle(
        "Code", parent=styles["Code"],
        fontSize=9, textColor=colors.HexColor("#475569"),
        backColor=colors.HexColor("#F1F5F9"), borderPadding=4
    )

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("CyberScan.Ai", title_style))
    story.append(Paragraph("AI-Powered Website Security Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=0.4 * cm))

    # ── Scan Info Table ───────────────────────────────────────────────────────
    scan_date = scan_result.created_at.strftime("%B %d, %Y at %H:%M UTC") if scan_result.created_at else "N/A"
    info_data = [
        ["Target URL", scan_result.target_url],
        ["Scan Date", scan_date],
        ["Overall Risk Score", f"{scan_result.risk_score or 0:.1f} / 100"],
        ["Overall Severity", (scan_result.overall_severity or "unknown").upper()],
        ["SSL Certificate", "Valid ✓" if scan_result.ssl_valid else "Invalid/Missing ✗"],
        ["Response Time", f"{scan_result.response_time_ms or 'N/A'} ms"],
    ]
    info_table = Table(info_data, colWidths=[4 * cm, 13 * cm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT_BG]),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Risk Score Visualization ──────────────────────────────────────────────
    risk = scan_result.risk_score or 0
    risk_color = DANGER if risk >= 70 else WARNING if risk >= 40 else SUCCESS
    story.append(Paragraph("Risk Score Breakdown", h2_style))

    score_data = [
        [
            Paragraph(f'<b>{risk:.0f}</b>', ParagraphStyle("BigScore", parent=body_style, fontSize=28, textColor=risk_color)),
            Paragraph(
                f"<b>Critical:</b> {scan_result.critical_count} &nbsp;&nbsp;"
                f"<b>High:</b> {scan_result.high_count} &nbsp;&nbsp;"
                f"<b>Medium:</b> {scan_result.medium_count} &nbsp;&nbsp;"
                f"<b>Low:</b> {scan_result.low_count}",
                body_style,
            ),
        ]
    ]
    score_table = Table(score_data, colWidths=[3 * cm, 14 * cm])
    score_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── Summary ───────────────────────────────────────────────────────────────
    if scan_result.summary:
        story.append(Paragraph("Executive Summary", h2_style))
        story.append(Paragraph(scan_result.summary, body_style))
        story.append(Spacer(1, 0.3 * cm))

    # ── Vulnerabilities Table ─────────────────────────────────────────────────
    vulnerabilities = scan_result.vulnerabilities or []
    if vulnerabilities:
        story.append(Paragraph(f"Vulnerabilities Found ({len(vulnerabilities)})", h2_style))

        for vuln in vulnerabilities:
            sev = vuln.get("severity", "low")
            sev_color = SEVERITY_COLORS.get(sev, colors.grey)

            sev_badge = Table(
                [[Paragraph(f'<b> {sev.upper()} </b>', body_style)]],
                colWidths=[1.8 * cm],
            )
            sev_badge.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), sev_color),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))

            vuln_data = [
                [sev_badge, Paragraph(f"<b>{vuln.get('name', 'Unknown Issue')}</b>", h3_style)],
                ["", Paragraph(vuln.get("description", ""), body_style)],
                ["", Paragraph(f"<b>Fix:</b> {vuln.get('recommendation', '')}", body_style)],
            ]
            vuln_table = Table(vuln_data, colWidths=[2 * cm, 15 * cm])
            vuln_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("SPAN", (0, 0), (0, -1)),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
            ]))
            story.append(vuln_table)
            story.append(Spacer(1, 0.2 * cm))

    # ── Raw Findings Table ────────────────────────────────────────────────────
    raw_findings = scan_result.raw_findings or []
    if raw_findings:
        story.append(PageBreak())
        story.append(Paragraph("Detailed Check Results", h2_style))

        table_data = [["Check", "Status", "Detail"]]
        row_colors = []
        for f in raw_findings:
            status = f.get("status", "")
            status_text = "✓ PASS" if status == "pass" else "✗ FAIL" if status == "fail" else "⚠ WARN"
            row_colors.append(SUCCESS if status == "pass" else DANGER if status == "fail" else WARNING)
            table_data.append([
                Paragraph(f.get("check", ""), body_style),
                Paragraph(f'<b>{status_text}</b>', body_style),
                Paragraph(f.get("detail", ""), body_style),
            ])

        findings_table = Table(table_data, colWidths=[5.5 * cm, 2.5 * cm, 9 * cm])
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        for idx, rc in enumerate(row_colors):
            style_cmds.append(("TEXTCOLOR", (1, idx + 1), (1, idx + 1), rc))
        findings_table.setStyle(TableStyle(style_cmds))
        story.append(findings_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0")))
    story.append(Paragraph(
        f"Generated by CyberScan.Ai on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | "
        "This report is for informational purposes. Always consult a security professional.",
        ParagraphStyle("Footer", parent=body_style, fontSize=8, textColor=colors.HexColor("#94A3B8"), alignment=TA_CENTER),
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
