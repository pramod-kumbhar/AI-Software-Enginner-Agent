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
            self.drawString(54, 750, "AI Software Engineer Agent Platform | Day 12: Production Deployment, Observability & Rollback")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Confidential - Autonomous Software Engineering System Specification (Day 12)")
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
    SECONDARY = colors.HexColor("#1e40af") # Deep Blue
    TEXT_DARK = colors.HexColor("#1e293b") # Charcoal
    BG_LIGHT = colors.HexColor("#f8fafc") # Very light slate
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
        fontSize=14,
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
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # Title Block
    story.append(Paragraph("Day 12: Production Deployment, Observability, Release Governance & Rollback", title_style))
    story.append(Paragraph("Release Readiness Engine • Deterministic Policy Rules • Live Health Probes • Autonomous Rollback", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=12))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "Day 12 completes the software engineering lifecycle by implementing a production-grade <b>Release Governance Agent</b>, "
        "a <b>Deterministic Policy Engine</b>, an <b>Observability & Tracing Layer</b>, comprehensive <b>Liveness & Readiness Health Probes</b>, "
        "and an <b>Autonomous Rollback Manager</b>. The AI evaluates release readiness and computes granular risk scores, but <b>never</b> "
        "deploys directly to production on its own. Production deployments strictly require passing staging smoke tests and explicit "
        "<b>Human Approval Sign-Off</b>.",
        body_style
    ))

    # Core Metrics Table
    metrics_data = [
        [Paragraph("<b>Governance Dimension</b>", body_style), Paragraph("<b>Enforced Platform Guardrail</b>", body_style), Paragraph("<b>Verification</b>", body_style)],
        [Paragraph("Promotion Hierarchy", body_style), Paragraph("development → staging → production (No direct dev to prod)", body_style), Paragraph("Enforced (100%)", body_style)],
        [Paragraph("Policy Engine", body_style), Paragraph("Deterministic hard blockers: CI pass, QA score >= 80, Security clean", body_style), Paragraph("Verified (100%)", body_style)],
        [Paragraph("Human Approval Gate", body_style), Paragraph("Production deployment strictly requires Lead DevOps sign-off", body_style), Paragraph("Gate Active", body_style)],
        [Paragraph("Concurrency Lock", body_style), Paragraph("DeploymentConcurrencyManager prevents parallel prod deployments", body_style), Paragraph("Thread-Safe", body_style)],
        [Paragraph("Health Probes", body_style), Paragraph("Liveness (/health/live), Readiness (/health/ready), Dependencies", body_style), Paragraph("Active Probes", body_style)],
        [Paragraph("Autonomous Rollback", body_style), Paragraph("Instant restoration of last verified known-good version upon health failure", body_style), Paragraph("Verified (100%)", body_style)],
        [Paragraph("Automated Test Suite", body_style), Paragraph("72 / 72 Automated Test Suites Passing Across Days 1–12", body_style), Paragraph("100% Pass Rate", body_style)]
    ]
    t_metrics = Table(metrics_data, colWidths=[130, 280, 94])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 10))

    # 2. Release & Deployment Workflow
    story.append(Paragraph("2. Autonomous Release Governance & Deployment Workflow", h1_style))
    flow_box = [
        [Paragraph(
            "<b>[START]</b><br/>"
            "   ↓<br/>"
            "<b>[1. LOAD RELEASE CONTEXT]</b> (Ingests commit SHA, branch, version, and PR number)<br/>"
            "   ↓<br/>"
            "<b>[2. MULTI-FACTOR VALIDATION]</b> (Verifies CI=PASS, QA Score >= 80, Security Clean, Architecture 100%)<br/>"
            "   ↓<br/>"
            "<b>[3. RISK SCORE CALCULATION]</b> (Computes 0–100 score across 12 change categories & destructive DDL check)<br/>"
            "   ↓<br/>"
            "<b>[4. DETERMINISTIC POLICY ENGINE]</b><br/>"
            "   ├── <b>BLOCKERS DETECTED</b> → <b>[STATUS: BLOCKED (Halt)]</b><br/>"
            "   └── <b>POLICY PASS</b> → [Generate Release Manifest]<br/>"
            "         ↓<br/>"
            "<b>[5. DEPLOY TO STAGING]</b> (Deploys artifact to sandboxed staging environment)<br/>"
            "         ↓<br/>"
            "<b>[6. STAGING HEALTH & SMOKE PROBES]</b> (Runs Auth, DB, API, and Mock Business Flows)<br/>"
            "   ├── <b>STAGING UNHEALTHY</b> → <b>[BLOCK PRODUCTION PROMOTION]</b><br/>"
            "   └── <b>STAGING HEALTHY</b> → [Request Human Approval Gate]<br/>"
            "         ↓<br/>"
            "<b>[7. HUMAN APPROVAL GATE]</b> (Awaits Lead DevOps Approval; never auto-deploys to prod)<br/>"
            "         ↓<br/>"
            "<b>[8. DEPLOY TO PRODUCTION]</b> (Acquires concurrency lock, executes zero-downtime release)<br/>"
            "         ↓<br/>"
            "<b>[9. POST-DEPLOYMENT PRODUCTION HEALTH CHECK]</b><br/>"
            "   ├── <b>HEALTHY</b> → [Record Observability Spans] → <b>[STATUS: RELEASED (SUCCESS)]</b><br/>"
            "   └── <b>UNHEALTHY</b> → <b>[10. AUTONOMOUS ROLLBACK]</b> (Restores last known-good version) → <b>[STATUS: ROLLED_BACK]</b>",
            code_style
        )]
    ]
    t_flow = Table(flow_box, colWidths=[504])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 1, SECONDARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 10))

    # Page Break for Risk & Policy Details
    story.append(PageBreak())

    # 3. Change Impact & Risk Scoring Table
    story.append(Paragraph("3. Change Impact Classification & Risk Weights", h1_style))
    risk_table_data = [
        [Paragraph("<b>Category</b>", body_style), Paragraph("<b>Pattern / Match</b>", body_style), Paragraph("<b>Weight</b>", body_style), Paragraph("<b>Governance Policy</b>", body_style)],
        [Paragraph("DOCUMENTATION", body_style), Paragraph("*.md, docs/, README", body_style), Paragraph("LOW (5–15)", body_style), Paragraph("Fast-track deployment without blocking gates.", body_style)],
        [Paragraph("TEST", body_style), Paragraph("tests/, test_*.py", body_style), Paragraph("LOW (10–25)", body_style), Paragraph("Standard staging validation.", body_style)],
        [Paragraph("BACKEND", body_style), Paragraph("app/services/, routers/", body_style), Paragraph("MEDIUM (25–45)", body_style), Paragraph("Full staging smoke test suite required.", body_style)],
        [Paragraph("DATABASE", body_style), Paragraph("alembic/, models/, *.sql", body_style), Paragraph("HIGH (45–65)", body_style), Paragraph("Scanned for destructive SQL (DROP/TRUNCATE).", body_style)],
        [Paragraph("AUTHENTICATION", body_style), Paragraph("auth, jwt, token, rbac", body_style), Paragraph("HIGH (50–70)", body_style), Paragraph("Strict security review and manual sign-off.", body_style)],
        [Paragraph("PAYMENT", body_style), Paragraph("payment, stripe, billing", body_style), Paragraph("CRITICAL (75–100)", body_style), Paragraph("Mandatory Lead Architect & DevOps dual approval.", body_style)],
        [Paragraph("INFRASTRUCTURE", body_style), Paragraph("Dockerfile, .github/", body_style), Paragraph("HIGH (40–60)", body_style), Paragraph("Requires container image validation.", body_style)]
    ]
    t_risk = Table(risk_table_data, colWidths=[110, 115, 85, 194])
    t_risk.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_risk)
    story.append(Spacer(1, 10))

    # 4. Observability & Tracing Architecture
    story.append(Paragraph("4. Observability, Tracing & Secret Sanitization", h1_style))
    story.append(Paragraph(
        "Observability is deeply embedded across every agent, node, tool call, and deployment event without exposing secrets:",
        body_style
    ))
    story.append(Paragraph("• <b>Distributed Trace Context:</b> Every execution creates a `trace_id` and `span_id` propagating across Planner, Architect, Developer, QA, CI, Deployment, and Rollback.", bullet_style))
    story.append(Paragraph("• <b>Zero-Leakage Scrubbing:</b> SecretMasker automatically scrubs API keys, bearer tokens, and GitHub credentials prior to logging.", bullet_style))
    story.append(Paragraph("• <b>Live Telemetry Metrics:</b> MetricsRegistry exposes counters (`deployments_total`, `rollbacks_total`, `health_checks_total`) and gauges (`last_qa_score`, `last_release_risk_score`).", bullet_style))
    story.append(Paragraph("• <b>Deep Health Probes:</b> Dedicated endpoints (`/health/live`, `/health/ready`, `/health/dependencies`) report subsystem health states.", bullet_style))
    story.append(Spacer(1, 10))

    # 5. FastAPI REST API Surface
    story.append(Paragraph("5. Day 12 REST API Surface", h1_style))
    api_data = [
        [Paragraph("<b>Route & Method</b>", body_style), Paragraph("<b>Functionality & Guardrails</b>", body_style)],
        [Paragraph("POST /api/v1/releases/create", body_style), Paragraph("Creates release and triggers automated validation pipeline.", body_style)],
        [Paragraph("POST /api/v1/releases/{id}/validate", body_style), Paragraph("Evaluates policy readiness, calculates risk, and checks blockers.", body_style)],
        [Paragraph("POST /api/v1/releases/{id}/approve", body_style), Paragraph("Human approval gate for production releases.", body_style)],
        [Paragraph("POST /api/v1/releases/{id}/deploy/staging", body_style), Paragraph("Triggers staging deployment and runs smoke tests.", body_style)],
        [Paragraph("POST /api/v1/releases/{id}/deploy/production", body_style), Paragraph("Triggers production deployment (requires approved status).", body_style)],
        [Paragraph("GET /api/v1/releases/{id}/health", body_style), Paragraph("Probes live health of target environment.", body_style)],
        [Paragraph("POST /api/v1/releases/{id}/rollback", body_style), Paragraph("Restores verified previous known-good version.", body_style)],
        [Paragraph("GET /metrics", body_style), Paragraph("Exposes platform telemetry and deployment metrics.", body_style)]
    ]
    t_api = Table(api_data, colWidths=[180, 324])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_api)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated PDF: {filename}")

if __name__ == "__main__":
    out_dir_1 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Documentation\Day 12\docs")
    out_dir_1.mkdir(parents=True, exist_ok=True)
    pdf_path_1 = out_dir_1 / "01_Day12_Production_Deployment_Observability_and_Rollback_Specification.pdf"

    out_dir_2 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Day 12")
    out_dir_2.mkdir(parents=True, exist_ok=True)
    pdf_path_2 = out_dir_2 / "01_Day12_Production_Deployment_Observability_and_Rollback_Specification.pdf"

    build_pdf(str(pdf_path_1))
    shutil.copy(str(pdf_path_1), str(pdf_path_2))
    print(f"Copied to: {pdf_path_2}")
