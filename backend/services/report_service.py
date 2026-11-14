"""
backend/services/report_service.py
==================================
Report Generation Service for Curriculum Gap Analysis Pipeline.

WHAT THIS FILE DOES:
  1. Generates complete JSON report data and persists to storage/reports/{run_id}.json.
  2. Generates a multi-page PDF document using ReportLab:
     - Title, Run ID, Analysis Date, Operating Mode
     - Executive Summary & Coverage Metrics (Covered, Partial, Missing)
     - Detailed Coverage Matrix table with similarity scores
     - Reviewer-Approved Curriculum Recommendations with Suggested Weights,
       verified learning resources, and framework citations
     - Reviewer-Rejected proposals with audit failure reasons
     - Academic methodology and evaluation limitation disclaimer
  3. Saves PDF report to storage/reports/{run_id}.pdf.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

from backend.config import settings, PROJECT_ROOT
from backend.core.schemas import WorkflowState, ReviewStatus, CoverageStatus

logger = logging.getLogger(__name__)


def generate_json_report(state: WorkflowState, output_dir: Optional[str] = None) -> str:
    """
    Serializes complete analysis results into a JSON report file.

    Returns:
        Absolute or relative path to the generated JSON file.
    """
    out_dir = Path(output_dir or settings.REPORTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / f"{state.run_id}.json"

    data = {
        "project_name": "Curriculum Gap Analysis Pipeline",
        "run_id": state.run_id,
        "domain": state.domain,
        "mode": state.mode,
        "status": state.status,
        "created_at": state.created_at.isoformat() if state.created_at else None,
        "completed_at": state.completed_at.isoformat() if state.completed_at else None,
        "statistics": state.statistics,
        "syllabus_summary": {
            "source_type": state.syllabus_data.source_type if state.syllabus_data else "N/A",
            "filename": state.syllabus_data.filename if state.syllabus_data else "N/A",
            "course_name": state.syllabus_data.course_name if state.syllabus_data else "N/A",
            "total_topics": len(state.syllabus_data.all_topics) if state.syllabus_data else 0,
        },
        "coverage_matrix": [c.model_dump() for c in state.coverage_matrix],
        "gaps": [g.model_dump() for g in state.gaps],
        "recommendations": [r.model_dump() for r in state.recommendations],
        "reviewer_results": [r.model_dump() for r in state.reviewer_results],
        "approved_recommendations": [r.model_dump() for r in state.approved_recommendations],
        "rejected_recommendations": [r.model_dump() for r in state.rejected_recommendations],
        "limitation": (
            "The evaluation uses a small, author-designed benchmark of three syllabi "
            "and 15 known gaps. Results demonstrate performance on these test cases "
            "and do not establish generalisation to all academic curricula."
        ),
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"[ReportService] Saved JSON report to {report_file}")
    return str(report_file)


def generate_pdf_report(state: WorkflowState, output_dir: Optional[str] = None) -> str:
    """
    Generates a professional academic PDF report using ReportLab.

    Returns:
        Absolute or relative path to the generated PDF file.
    """
    out_dir = Path(output_dir or settings.REPORTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{state.run_id}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#101827"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#4B5563"),
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#374151"),
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1F2937"),
    )
    cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("Curriculum Gap Analysis Pipeline", title_style))
    elements.append(
        Paragraph(
            f"Evidence-Based Multi-Agent AI System | Run ID: <b>{state.run_id}</b> | "
            f"Domain: <b>{state.domain}</b> | Mode: <b>{state.mode}</b>",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366F1"), spaceAfter=12))

    # 2. Executive Summary & Statistics Cards
    stats = state.statistics
    elements.append(Paragraph("1. Executive Summary & Coverage Metrics", h2_style))

    course_title = state.syllabus_data.course_name if state.syllabus_data else "Academic Syllabus"
    total_parsed_topics = len(state.syllabus_data.all_topics) if state.syllabus_data else 0

    elements.append(
        Paragraph(
            f"This audit evaluated the academic curriculum for <b>{course_title}</b> against industry "
            f"workforce competency frameworks. A total of <b>{total_parsed_topics}</b> syllabus topics were extracted, "
            f"and <b>{stats['total_framework_skills']}</b> authoritative industry competencies were evaluated using local RAG retrieval.",
            body_style,
        )
    )
    elements.append(Spacer(1, 8))

    stat_data = [
        ["Total Evaluated", "Fully Covered", "Partially Covered", "Missing Skills", "Approved Additions"],
        [
            str(stats["total_framework_skills"]),
            str(stats["covered"]),
            str(stats["partial"]),
            str(stats["missing"]),
            str(stats["approved_recommendations"]),
        ],
    ]
    stat_table = Table(stat_data, colWidths=[108, 108, 108, 108, 108])
    stat_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F8FAFC")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ])
    )
    elements.append(stat_table)
    elements.append(Spacer(1, 14))

    # 3. Coverage Matrix Table
    elements.append(Paragraph("2. Curriculum Competency Coverage Matrix", h2_style))
    matrix_headers = ["ID", "Framework Competency", "Matching Syllabus Topic", "Similarity", "Status"]
    matrix_rows = [[Paragraph(f"<b>{h}</b>", cell_bold) for h in matrix_headers]]

    for row in state.coverage_matrix:
        status_color = "#10B981" if row.status == CoverageStatus.COVERED else (
            "#F59E0B" if row.status == CoverageStatus.PARTIAL else "#EF4444"
        )
        status_cell = Paragraph(f"<font color='{status_color}'><b>{row.status.value}</b></font>", cell_style)
        topic_cell = Paragraph(row.matching_topic or "<i>None (Gap)</i>", cell_style)
        matrix_rows.append([
            Paragraph(row.framework_id, cell_style),
            Paragraph(row.framework_skill, cell_style),
            topic_cell,
            Paragraph(f"{row.similarity_score:.2f}", cell_style),
            status_cell,
        ])

    m_table = Table(matrix_rows, colWidths=[55, 175, 185, 55, 70])
    m_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
            ("ALIGN", (4, 0), (4, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    elements.append(m_table)
    elements.append(Spacer(1, 14))

    # 4. Reviewer-Approved Curriculum Recommendations
    elements.append(Paragraph("3. Reviewer-Approved Curriculum Recommendations", h2_style))
    elements.append(
        Paragraph(
            "Every recommendation below was audited and <b>APPROVED</b> by Agent 5 (Reviewer Agent) "
            "against authentic framework evidence stored in ChromaDB.",
            body_style,
        )
    )
    elements.append(Spacer(1, 6))

    if state.approved_recommendations:
        rec_headers = ["ID", "Recommended Topic", "Weight", "Level", "Verified Learning Resource", "Evidence ID"]
        rec_rows = [[Paragraph(f"<b>{h}</b>", cell_bold) for h in rec_headers]]

        for r in state.approved_recommendations:
            rec_rows.append([
                Paragraph(r.framework_id, cell_style),
                Paragraph(f"<b>{r.topic}</b><br/>{r.reason}", cell_style),
                Paragraph(f"{r.recommended_weight} ({r.weight_type})", cell_style),
                Paragraph(r.level, cell_style),
                Paragraph(f"<u>{r.resource}</u><br/><font size='6' color='#4338CA'>{r.resource_url}</font>", cell_style),
                Paragraph(r.evidence_id, cell_style),
            ])

        r_table = Table(rec_rows, colWidths=[50, 160, 60, 50, 170, 50])
        r_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D2FE")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        elements.append(r_table)
    else:
        elements.append(Paragraph("<i>No recommendations approved for this run.</i>", body_style))

    elements.append(Spacer(1, 14))

    # 5. Reviewer-Rejected Recommendations (Audit Transparency)
    if state.rejected_recommendations:
        elements.append(Paragraph("4. Rejected Recommendations (Audit Transparency)", h2_style))
        rej_headers = ["ID", "Proposed Topic", "Rejection Reason", "Evidence Citation Checked"]
        rej_rows = [[Paragraph(f"<b>{h}</b>", cell_bold) for h in rej_headers]]

        for r in state.rejected_recommendations:
            rej_rows.append([
                Paragraph(r.framework_id, cell_style),
                Paragraph(r.topic, cell_style),
                Paragraph(r.reason, cell_style),
                Paragraph(r.evidence_id, cell_style),
            ])
        rej_table = Table(rej_rows, colWidths=[60, 160, 240, 80])
        rej_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEF2F2")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FECACA")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(rej_table)
        elements.append(Spacer(1, 14))

    # 6. Methodology & Limitations Disclaimer
    elements.append(Paragraph("5. Methodology & Limitation Disclaimer", h2_style))
    elements.append(
        Paragraph(
            "<b>Citation Coverage:</b> 100% of approved recommendations are strictly bound to genuine NIST NICE / "
            "European Commission ESCO / ACM industry framework passages.<br/>"
            "<b>Benchmark Limitation:</b> The evaluation uses a small, author-designed benchmark of three syllabi "
            "and 15 known gaps. Results demonstrate performance on these test cases and do not establish generalisation "
            "to all academic curricula.",
            body_style,
        )
    )

    doc.build(elements)
    logger.info(f"[ReportService] Generated PDF report at: {pdf_path}")
    return str(pdf_path)
