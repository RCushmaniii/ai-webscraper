"""
Report Export Service

Generates PDF and CSV exports from cached crawl reports.
"""

import io
import csv
import logging
from typing import Dict, Any, List
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

logger = logging.getLogger(__name__)

# CushLabs brand colors
BRAND_PRIMARY = colors.HexColor("#1E293B")  # Deep slate
BRAND_SECONDARY = colors.HexColor("#F97316")  # Warm orange
BRAND_LIGHT = colors.HexColor("#FFF7ED")  # Soft orange bg
BRAND_GREEN = colors.HexColor("#059669")
BRAND_RED = colors.HexColor("#DC2626")
BRAND_YELLOW = colors.HexColor("#D97706")
BRAND_GRAY = colors.HexColor("#6B7280")


def _score_color(score: float) -> colors.Color:
    if score >= 80:
        return BRAND_GREEN
    if score >= 60:
        return BRAND_YELLOW
    return BRAND_RED


def _build_styles() -> Dict[str, ParagraphStyle]:
    """Build custom paragraph styles for the PDF."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontSize=24,
            textColor=BRAND_PRIMARY,
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=BRAND_GRAY,
            spaceAfter=20,
        ),
        "h2": ParagraphStyle(
            "SectionH2",
            parent=base["Heading2"],
            fontSize=16,
            textColor=BRAND_PRIMARY,
            spaceBefore=16,
            spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "SectionH3",
            parent=base["Heading3"],
            fontSize=13,
            textColor=BRAND_PRIMARY,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BodyText",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#374151"),
            leading=14,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "SmallText",
            parent=base["Normal"],
            fontSize=8,
            textColor=BRAND_GRAY,
        ),
        "score": ParagraphStyle(
            "ScoreText",
            parent=base["Normal"],
            fontSize=36,
            alignment=1,  # CENTER
            spaceAfter=4,
        ),
    }


def generate_pdf_report(report_data: Dict[str, Any], crawl_data: Dict[str, Any]) -> bytes:
    """
    Generate a branded PDF report from cached report data.

    Args:
        report_data: The report dict (from crawls.ai_report)
        crawl_data: Crawl metadata (name, url, etc.)

    Returns:
        PDF file content as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = _build_styles()
    elements: List[Any] = []

    exec_summary = report_data.get("executive_summary", {})
    metrics = report_data.get("metrics", {})
    summary_stats = report_data.get("summary_stats", {})
    page_audits = report_data.get("page_audits", [])
    data_findings = report_data.get("data_findings", [])

    # --- HEADER ---
    elements.append(Paragraph("Website Analysis Report", styles["title"]))
    site_url = crawl_data.get("url", "Unknown")
    crawl_name = crawl_data.get("name", "")
    generated_at = crawl_data.get("ai_report_generated_at", "")
    subtitle_parts = [f"<b>{site_url}</b>"]
    if crawl_name:
        subtitle_parts.append(f" &mdash; {crawl_name}")
    if generated_at:
        try:
            dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            subtitle_parts.append(f"<br/>Generated: {dt.strftime('%B %d, %Y at %I:%M %p UTC')}")
        except Exception:
            subtitle_parts.append(f"<br/>Generated: {generated_at}")
    elements.append(Paragraph("".join(subtitle_parts), styles["subtitle"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=BRAND_SECONDARY, spaceAfter=16))

    # --- HEALTH SCORE ---
    health_score = exec_summary.get("site_health_score", 0)
    score_style = ParagraphStyle(
        "HealthScore", parent=styles["score"], textColor=_score_color(health_score)
    )
    elements.append(Paragraph(f"<b>{health_score}</b> / 100", score_style))
    one_liner = exec_summary.get("one_line_summary", "")
    if one_liner:
        centered = ParagraphStyle("Centered", parent=styles["body"], alignment=1)
        elements.append(Paragraph(one_liner, centered))
    elements.append(Spacer(1, 12))

    # --- SCORE BREAKDOWN ---
    elements.append(Paragraph("Score Breakdown", styles["h2"]))
    score_data = [
        ["Technical SEO", "Content Quality", "User Experience", "Trust Signals"],
        [
            str(exec_summary.get("technical_seo_score", 0)),
            str(exec_summary.get("content_quality_score", 0)),
            str(exec_summary.get("user_experience_score", 0)),
            str(exec_summary.get("trust_signals_score", 0)),
        ],
    ]
    score_table = Table(score_data, colWidths=[1.75 * inch] * 4)
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, 1), 18),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 1), (-1, 1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 12))

    # --- CRAWL METRICS ---
    elements.append(Paragraph("Crawl Metrics", styles["h2"]))
    metrics_data = [
        ["Pages Crawled", "Total Issues", "Broken Links", "Missing Meta"],
        [
            str(metrics.get("total_pages", 0)),
            str(metrics.get("total_issues", 0)),
            str(metrics.get("broken_links", 0)),
            str(metrics.get("missing_meta", 0)),
        ],
    ]
    metrics_table = Table(metrics_data, colWidths=[1.75 * inch] * 4)
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, 1), 16),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 1), (-1, 1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 12))

    # --- SEO PASS RATES ---
    if summary_stats:
        elements.append(Paragraph("SEO Pass Rates", styles["h2"]))
        pass_data = [
            ["Title Tags", "Meta Descriptions", "H1 Tags", "Content Depth", "Response Time"],
            [
                f"{summary_stats.get('title_pass_rate', 0)}%",
                f"{summary_stats.get('meta_pass_rate', 0)}%",
                f"{summary_stats.get('h1_pass_rate', 0)}%",
                f"{summary_stats.get('content_pass_rate', 0)}%",
                f"{summary_stats.get('performance_pass_rate', 0)}%",
            ],
        ]
        pass_table = Table(pass_data, colWidths=[1.4 * inch] * 5)
        pass_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, 1), 14),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 1), (-1, 1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]))
        elements.append(pass_table)
        elements.append(Spacer(1, 12))

    # --- CRITICAL ISSUES ---
    critical = exec_summary.get("critical_issues", [])
    if critical:
        elements.append(Paragraph("Critical Issues", styles["h2"]))
        for issue in critical:
            title = issue.get("title", "")
            desc = issue.get("description", "")
            action = issue.get("recommended_action", "")
            affected = issue.get("pages_affected", 0)
            elements.append(Paragraph(
                f"<b>{title}</b> &mdash; affects {affected} page{'s' if affected != 1 else ''}",
                styles["body"]
            ))
            if desc:
                elements.append(Paragraph(desc, styles["body"]))
            if action:
                elements.append(Paragraph(f"<i>Action: {action}</i>", styles["body"]))
            elements.append(Spacer(1, 4))

    # --- QUICK WINS ---
    quick_wins = exec_summary.get("quick_wins", [])
    if quick_wins:
        elements.append(Paragraph("Quick Wins", styles["h2"]))
        for win in quick_wins:
            elements.append(Paragraph(f"&bull; {win}", styles["body"]))

    # --- STRATEGIC RECOMMENDATIONS ---
    recs = exec_summary.get("strategic_recommendations", [])
    if recs:
        elements.append(Paragraph("Strategic Recommendations", styles["h2"]))
        for rec in recs:
            title = rec.get("title", "")
            desc = rec.get("description", "")
            impact = rec.get("expected_impact", "")
            effort = rec.get("effort_estimate", "")
            elements.append(Paragraph(f"<b>{title}</b>", styles["body"]))
            if desc:
                elements.append(Paragraph(desc, styles["body"]))
            if impact or effort:
                elements.append(Paragraph(
                    f"<i>Impact: {impact} | Effort: {effort}</i>", styles["small"]
                ))
            elements.append(Spacer(1, 4))

    # --- STRENGTHS & WEAKNESSES ---
    strengths = exec_summary.get("strengths_summary", "")
    weaknesses = exec_summary.get("weaknesses_summary", "")
    if strengths or weaknesses:
        elements.append(Paragraph("Strengths & Weaknesses", styles["h2"]))
        if strengths:
            elements.append(Paragraph(f"<b>Strengths:</b> {strengths}", styles["body"]))
        if weaknesses:
            elements.append(Paragraph(f"<b>Areas for Improvement:</b> {weaknesses}", styles["body"]))

    # --- ACTION PLAN ---
    action_plan = exec_summary.get("action_plan_summary", "")
    if action_plan:
        elements.append(Paragraph("Recommended Action Plan", styles["h2"]))
        elements.append(Paragraph(action_plan, styles["body"]))

    # --- PAGE AUDIT TABLE ---
    if page_audits:
        elements.append(Paragraph("Page-by-Page Audit", styles["h2"]))
        header = ["Page", "Score", "Title", "Meta", "H1", "Content", "Speed", "Issues"]
        rows = [header]
        for pa in page_audits[:50]:  # Cap at 50 rows for PDF readability
            url_path = pa.get("url", "").split("//", 1)[-1].split("/", 1)[-1] or "/"
            if len(url_path) > 35:
                url_path = url_path[:32] + "..."
            checks = pa.get("checks", {})
            rows.append([
                url_path,
                str(pa.get("score", 0)),
                _check_symbol(checks.get("title", {}).get("status", "")),
                _check_symbol(checks.get("meta_description", {}).get("status", "")),
                _check_symbol(checks.get("h1", {}).get("status", "")),
                _check_symbol(checks.get("content_depth", {}).get("status", "")),
                _check_symbol(checks.get("response_time", {}).get("status", "")),
                str(pa.get("issue_count", 0)),
            ])

        col_widths = [2.2 * inch, 0.6 * inch, 0.5 * inch, 0.5 * inch, 0.5 * inch, 0.6 * inch, 0.5 * inch, 0.6 * inch]
        audit_table = Table(rows, colWidths=col_widths, repeatRows=1)
        audit_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(audit_table)
        elements.append(Spacer(1, 12))

    # --- DATA FINDINGS TABLE ---
    if data_findings:
        elements.append(Paragraph("Detailed Findings", styles["h2"]))
        header = ["Severity", "Category", "Finding", "Target"]
        rows = [header]
        for f in data_findings[:50]:
            finding_text = f.get("finding", "")
            if len(finding_text) > 60:
                finding_text = finding_text[:57] + "..."
            rows.append([
                f.get("severity", "").upper(),
                f.get("category", ""),
                finding_text,
                f.get("target", "-"),
            ])

        finding_table = Table(rows, colWidths=[0.8 * inch, 1.2 * inch, 3.5 * inch, 1.5 * inch], repeatRows=1)
        finding_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(finding_table)

    # --- FOOTER ---
    elements.append(Spacer(1, 24))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_GRAY, spaceAfter=8))
    elements.append(Paragraph(
        "Generated by <b>CushLabs AI Web Scraper</b> &mdash; ai-webscraper.cushlabs.com",
        styles["small"]
    ))

    doc.build(elements)
    return buffer.getvalue()


def _check_symbol(status: str) -> str:
    """Convert check status to a PDF-safe symbol."""
    if status == "pass":
        return "PASS"
    if status in ("missing", "empty"):
        return "FAIL"
    return "WARN"


def generate_csv_export(report_data: Dict[str, Any], export_type: str) -> str:
    """
    Generate CSV export of report data.

    Args:
        report_data: The report dict (from crawls.ai_report)
        export_type: "page_audits" or "findings"

    Returns:
        CSV content as string
    """
    output = io.StringIO()

    if export_type == "page_audits":
        page_audits = report_data.get("page_audits", [])
        writer = csv.writer(output)
        writer.writerow(["URL", "Score", "Title Status", "Meta Status", "H1 Status",
                         "Content Status", "Speed Status", "Issue Count"])
        for pa in page_audits:
            checks = pa.get("checks", {})
            writer.writerow([
                pa.get("url", ""),
                pa.get("score", 0),
                checks.get("title", {}).get("status", ""),
                checks.get("meta_description", {}).get("status", ""),
                checks.get("h1", {}).get("status", ""),
                checks.get("content_depth", {}).get("status", ""),
                checks.get("response_time", {}).get("status", ""),
                pa.get("issue_count", 0),
            ])

    elif export_type == "findings":
        findings = report_data.get("data_findings", [])
        writer = csv.writer(output)
        writer.writerow(["Severity", "Category", "Finding", "Current Value",
                         "Current Length", "Target", "URL"])
        for f in findings:
            writer.writerow([
                f.get("severity", ""),
                f.get("category", ""),
                f.get("finding", ""),
                f.get("current_value", ""),
                f.get("current_length", ""),
                f.get("target", ""),
                f.get("url", ""),
            ])

    else:
        raise ValueError(f"Unknown export type: {export_type}")

    return output.getvalue()
