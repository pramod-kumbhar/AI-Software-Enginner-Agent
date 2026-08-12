import os
import shutil
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "AI Software Engineer Agent Platform | Day 16: Evaluation & Benchmarking Framework")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Confidential - Autonomous Software Engineering System Specification (Day 16)")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()

def build_pdf(filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    PRIMARY = colors.HexColor("#0f172a") # Dark Slate
    SECONDARY = colors.HexColor("#4f46e5") # Indigo
    ACCENT = colors.HexColor("#0284c7") # Blue
    TEXT_DARK = colors.HexColor("#1e293b") # Charcoal
    BG_LIGHT = colors.HexColor("#f8fafc") # Slate 50
    BORDER_COLOR = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=17,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.2,
        leading=13.2,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10.2,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # Title Block
    story.append(Paragraph("Day 16: AI Agent Evaluation, Benchmarking & Continuous Quality Framework", title_style))
    story.append(Paragraph("Multi-Layer Scorers • AST Static Analysis • Adversarial Security Benchmarks • Model Leaderboards", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=12))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & Evaluation Philosophy", h1_style))
    story.append(Paragraph(
        "Day 16 establishes an <b>enterprise-grade, multi-layered evaluation and continuous quality governance system</b>. "
        "Rejecting exclusive reliance on LLM-as-a-Judge, the framework combines <b>deterministic AST parsing</b>, "
        "pytest execution pass rates, code coverage, cryptographic security scanners, adversarial prompt injection tests, "
        "agent trajectory compliance, token/cost efficiency, and regression delta gating. A hard <b>Critical Failure Override Gate</b> "
        "guarantees that secret leaks, unauthorized deployments, or privilege escalations result in an immediate release block "
        "regardless of high numerical scores.",
        body_style
    ))

    # Evaluation Dimension Matrix
    eval_matrix = [
        [Paragraph("<b>Evaluation Dimension</b>", body_style), Paragraph("<b>Methodology & Measurement</b>", body_style), Paragraph("<b>Weight</b>", body_style), Paragraph("<b>Threshold</b>", body_style)],
        [Paragraph("Functional Completeness", body_style), Paragraph("Acceptance criteria validation, endpoint and schema verification", body_style), Paragraph("25%", body_style), Paragraph("&ge; 80.0", body_style)],
        [Paragraph("Testing & Coverage", body_style), Paragraph("Pytest pass rate (70%) + code line coverage percentage (30%)", body_style), Paragraph("20%", body_style), Paragraph("&ge; 80.0", body_style)],
        [Paragraph("Code Quality (AST)", body_style), Paragraph("Python AST syntax validation, type annotations, and docstrings", body_style), Paragraph("15%", body_style), Paragraph("&ge; 75.0", body_style)],
        [Paragraph("Security & Defense", body_style), Paragraph("AST dangerous calls, hardcoded secret regex, adversarial defense", body_style), Paragraph("15%", body_style), Paragraph("&ge; 90.0", body_style)],
        [Paragraph("Agent Trajectory", body_style), Paragraph("Valid node sequencing (Planner &rarr; Deploy) and loop penalty audit", body_style), Paragraph("10%", body_style), Paragraph("&ge; 80.0", body_style)],
        [Paragraph("Reliability & Repair", body_style), Paragraph("First-attempt completion + bounded repair loop cutoff (&le; 3 attempts)", body_style), Paragraph("5%", body_style), Paragraph("&ge; 80.0", body_style)],
        [Paragraph("Cost Efficiency", body_style), Paragraph("Token budget ratio & cost-per-successful-task vs quota policy", body_style), Paragraph("5%", body_style), Paragraph("&ge; 70.0", body_style)],
        [Paragraph("Execution Latency", body_style), Paragraph("Execution duration vs SLA target thresholds (P95/P99 latency)", body_style), Paragraph("5%", body_style), Paragraph("&ge; 70.0", body_style)]
    ]
    t_matrix = Table(eval_matrix, colWidths=[120, 240, 60, 84])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_matrix)
    story.append(Spacer(1, 10))

    # 2. Benchmark Datasets & Case Distribution
    story.append(Paragraph("2. Benchmark Datasets & Case Distribution", h1_style))
    ds_data = [
        [Paragraph("<b>Dataset ID</b>", body_style), Paragraph("<b>Dataset Name & Scope</b>", body_style), Paragraph("<b>Cases</b>", body_style), Paragraph("<b>Domain & Focus</b>", body_style)],
        [Paragraph("benchmark-v1", body_style), Paragraph("AI Software Engineer Benchmark v1 (Standard)", body_style), Paragraph("32", body_style), Paragraph("CRUD APIs, DB, Debugging, DAG, Clean Arch, QA", body_style)],
        [Paragraph("security-adversarial-v1", body_style), Paragraph("Agent Security & Adversarial Injection Benchmark", body_style), Paragraph("20", body_style), Paragraph("Prompt injection, secret leaks, tool abuse, SSRF", body_style)],
        [Paragraph("architecture-design-v1", body_style), Paragraph("System Architecture & Scalability Benchmark", body_style), Paragraph("10", body_style), Paragraph("Clean architecture, multi-tenant isolation, outbox", body_style)]
    ]
    t_ds = Table(ds_data, colWidths=[130, 190, 45, 139])
    t_ds.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_ds)
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # 3. Evaluation Architecture & Pipeline
    story.append(Paragraph("3. Multi-Layer Evaluation & Governance Architecture", h1_style))
    flow_box = [
        [Paragraph(
            "<b>[EVALUATION BENCHMARK DATASET]</b><br/>"
            "   ↓<br/>"
            "<b>[EVALUATION ENGINE]</b> (Orchestrates multi-layer test execution)<br/>"
            "   ├── <b>[1. FUNCTIONAL SCORER]</b> (Acceptance criteria, file & endpoint existence)<br/>"
            "   ├── <b>[2. CODE QUALITY SCORER]</b> (AST syntax parsing, type hints, docstrings)<br/>"
            "   ├── <b>[3. TESTING SCORER]</b> (Pytest pass rate, test counts, line coverage)<br/>"
            "   ├── <b>[4. SECURITY SCORER]</b> (Regex secret scanner, dangerous AST calls, injection checks)<br/>"
            "   ├── <b>[5. TRAJECTORY SCORER]</b> (Node transition verification, loop penalty audit)<br/>"
            "   ├── <b>[6. RELIABILITY SCORER]</b> (First attempt success, bounded repair &lt;= 3 attempts)<br/>"
            "   ├── <b>[7. COST & LATENCY SCORERS]</b> (Token efficiency, USD budget adherence, SLA limits)<br/>"
            "   └── <b>[8. LLM-AS-A-JUDGE]</b> (Structured advisory rubric; non-overriding on failures)<br/>"
            "   ↓<br/>"
            "<b>[CRITICAL FAILURE OVERRIDE GATE]</b><br/>"
            "   (Immediate FAIL on Secret Leaks, Auth Bypass, or Unapproved Deployments)<br/>"
            "   ↓<br/>"
            "<b>[REGRESSION DELTA GATING & MODEL LEADERBOARD]</b><br/>"
            "   (Blocks release if functional score drops &gt; 5 pts or any security regression occurs)",
            code_style
        )]
    ]
    t_flow = Table(flow_box, colWidths=[504])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f5f3ff")),
        ('BOX', (0, 0), (-1, -1), 1, SECONDARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 10))

    # 4. REST API Endpoints Catalog
    story.append(Paragraph("4. Day 16 REST API Endpoint Catalog", h1_style))
    api_data = [
        [Paragraph("<b>HTTP Method & Path</b>", body_style), Paragraph("<b>Action & Description</b>", body_style), Paragraph("<b>Governance Gate</b>", body_style)],
        [Paragraph("POST /api/v1/evaluations/run", body_style), Paragraph("Runs multi-layer benchmark on dataset & records results.", body_style), Paragraph("Evaluation Engine", body_style)],
        [Paragraph("GET /api/v1/evaluations/{id}", body_style), Paragraph("Retrieves overall score, summary metrics, and status.", body_style), Paragraph("Read Access", body_style)],
        [Paragraph("GET /api/v1/evaluations/{id}/results", body_style), Paragraph("Retrieves granular case-by-case evaluation results.", body_style), Paragraph("Read Access", body_style)],
        [Paragraph("GET /api/v1/evaluations/{id}/report", body_style), Paragraph("Exports full Markdown or JSON benchmark report.", body_style), Paragraph("Report Generator", body_style)],
        [Paragraph("POST /api/v1/evaluations/{id}/human-review", body_style), Paragraph("Submits human reviewer scores (understanding, DX, quality).", body_style), Paragraph("Authorized Reviewer", body_style)],
        [Paragraph("GET /api/v1/evaluations/leaderboard", body_style), Paragraph("Retrieves ranked multi-model/provider leaderboard.", body_style), Paragraph("Leaderboard Engine", body_style)],
        [Paragraph("GET /api/v1/evaluations/regressions", body_style), Paragraph("Lists all continuous regression comparison reports.", body_style), Paragraph("Regression Suite", body_style)],
        [Paragraph("POST /api/v1/evaluations/regression/run", body_style), Paragraph("Compares current evaluation against baseline for delta scoring.", body_style), Paragraph("Release Gate Check", body_style)],
        [Paragraph("GET /api/v1/evaluation-datasets", body_style), Paragraph("Lists active evaluation benchmark datasets.", body_style), Paragraph("Dataset Registry", body_style)],
        [Paragraph("GET /api/v1/evaluation-datasets/{id}/cases", body_style), Paragraph("Lists all evaluation cases defined for a dataset.", body_style), Paragraph("Case Registry", body_style)]
    ]
    t_api = Table(api_data, colWidths=[160, 215, 129])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_api)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated PDF: {filename}")

if __name__ == "__main__":
    out_dir_1 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Documentation\Day 16\docs")
    out_dir_1.mkdir(parents=True, exist_ok=True)
    pdf_path_1 = out_dir_1 / "01_Day16_Evaluation_Benchmarking_and_Continuous_Testing_Specification.pdf"

    out_dir_2 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Day 16")
    out_dir_2.mkdir(parents=True, exist_ok=True)
    pdf_path_2 = out_dir_2 / "01_Day16_Evaluation_Benchmarking_and_Continuous_Testing_Specification.pdf"

    build_pdf(str(pdf_path_1))
    shutil.copy(str(pdf_path_1), str(pdf_path_2))
    print(f"Copied to: {pdf_path_2}")
