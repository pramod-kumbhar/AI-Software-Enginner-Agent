import os
import shutil
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
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
            self.drawString(54, 750, "AI Software Engineer Agent Platform | Day 11: CI/CD Monitoring & Autonomous Repair")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Confidential - Autonomous Software Engineering System Specification (Day 11)")
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
    
    # Custom Palette
    PRIMARY = colors.HexColor("#0f172a") # Dark Slate
    SECONDARY = colors.HexColor("#1e40af") # Deep Blue
    ACCENT = colors.HexColor("#0284c7") # Sky Blue
    TEXT_DARK = colors.HexColor("#1e293b") # Charcoal
    BG_LIGHT = colors.HexColor("#f8fafc") # Very light slate
    BORDER_COLOR = colors.HexColor("#cbd5e1")
    ALERT_BG = colors.HexColor("#fef2f2")
    ALERT_BORDER = colors.HexColor("#ef4444")
    SUCCESS_BG = colors.HexColor("#f0fdf4")
    SUCCESS_BORDER = colors.HexColor("#22c55e")

    # Typography Styles
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
        fontSize=15,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
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
    story.append(Paragraph("Day 11: CI/CD Monitoring, Failure Analysis & Bounded Autonomous Repair", title_style))
    story.append(Paragraph("Production Architecture Specification • GitHub Actions Integration • Multi-Factor Governance", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=12))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "Day 11 introduces a complete production-grade <b>CI/CD Monitoring Agent</b>, a dedicated <b>Failure Analysis & Root Cause Engine</b>, "
        "and a strictly <b>Bounded Autonomous Software Repair State Machine</b>. The system closes the loop on autonomous development: "
        "detecting CI failures from GitHub Actions, retrieving and sanitizing failure logs, determining root causes, generating targeted "
        "repair plans, invoking Developer Agent code modification via MCP tools, running local test and QA verification, updating branch pull requests, "
        "and enforcing a strict 3-attempt circuit breaker with <b>zero automatic merges</b>.",
        body_style
    ))

    # Core Metrics Table
    metrics_data = [
        [Paragraph("<b>Component / Dimension</b>", body_style), Paragraph("<b>Specification & Enforced Guardrails</b>", body_style), Paragraph("<b>Status</b>", body_style)],
        [Paragraph("CI Protocol Engine", body_style), Paragraph("Official GitHub REST API v3 (Actions Workflows, Runs, Jobs, Logs)", body_style), Paragraph("Verified (100%)", body_style)],
        [Paragraph("Failure Classification", body_style), Paragraph("17 Failure Types, 5 Severity Levels, 5 Repairability Categories", body_style), Paragraph("Verified (100%)", body_style)],
        [Paragraph("Prompt Injection Defense", body_style), Paragraph("CI Logs, Test Output, Commit Messages treated as UNTRUSTED DATA", body_style), Paragraph("Enforced (Shield Active)", body_style)],
        [Paragraph("Bounded State Machine", body_style), Paragraph("LangGraph DAG with Max 3 Repair Attempts & Circuit Breaker", body_style), Paragraph("No Infinite Loops", body_style)],
        [Paragraph("Human Governance Gate", body_style), Paragraph("High-Risk / Security / Auth fixes require Lead DevOps Approval", body_style), Paragraph("Gate Enforced", body_style)],
        [Paragraph("Auto-Merge Guard", body_style), Paragraph("github.merge_pull_request is strictly BLOCKED across all roles", body_style), Paragraph("Prohibited (100% Safe)", body_style)],
        [Paragraph("Regression Pass Rate", body_style), Paragraph("51 / 51 Automated Pytest Suites Passing Across Entire Platform", body_style), Paragraph("100.0% Pass Rate", body_style)]
    ]
    t_metrics = Table(metrics_data, colWidths=[130, 280, 94])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 10))

    # Architecture Workflow
    story.append(Paragraph("2. Autonomous CI/CD Monitoring & Repair Workflow", h1_style))
    story.append(Paragraph(
        "The autonomous repair lifecycle operates as a finite state machine compiled via LangGraph with bounded conditional edges:",
        body_style
    ))

    flow_box = [
        [Paragraph(
            "<b>[START]</b><br/>"
            "   ↓<br/>"
            "<b>[1. GITHUB ACTIONS CI RUN]</b> (PR or branch push triggers ci.yml pipeline)<br/>"
            "   ↓<br/>"
            "<b>[2. CI MONITOR AGENT]</b> (Polls /actions/runs with bounded 10s backoff & timeout)<br/>"
            "   ├── <b>CI PASSED</b> → [QA Check] → [Human Review] → <b>[END SUCCESS]</b><br/>"
            "   └── <b>CI FAILED</b> → [Extract Failed Jobs & Steps]<br/>"
            "         ↓<br/>"
            "<b>[3. SANITIZED LOG EXTRACTION]</b> (Bounds logs to max 20,000 chars, scrubs tokens & secrets)<br/>"
            "         ↓<br/>"
            "<b>[4. FAILURE CLASSIFICATION & RCA]</b> (Classifies type, severity, affected files, repairability)<br/>"
            "         ↓<br/>"
            "<b>[5. REPAIRABILITY CHECK]</b> (If NOT_REPAIRABLE / EXTERNAL_DEPENDENCY → <b>[ESCALATE BLOCKED]</b>)<br/>"
            "         ↓<br/>"
            "<b>[6. REPAIR PLANNING]</b> (Synthesizes bounded RepairPlan with targeted files & instructions)<br/>"
            "         ↓<br/>"
            "<b>[7. APPROVAL POLICY CHECK]</b> (If AUTO_REPAIR_WITH_APPROVAL → Halts for Human DevOps Sign-Off)<br/>"
            "         ↓<br/>"
            "<b>[8. DEVELOPER AGENT PATCH]</b> (Applies targeted AST repair via sandboxed MCP Tool Layer)<br/>"
            "         ↓<br/>"
            "<b>[9. LOCAL TEST VERIFICATION]</b> (Executes pytest subprocess runner with 15s timeout)<br/>"
            "         ↓<br/>"
            "<b>[10. QA AGENT SCORING]</b> (Evaluates architecture compliance & security score >= 80/100)<br/>"
            "         ↓<br/>"
            "<b>[11. GIT STAGE & COMMIT]</b> (Creates commit 'fix: resolve <issue>' on task branch)<br/>"
            "         ↓<br/>"
            "<b>[12. RE-TRIGGER CI]</b> (Dispatches GitHub Actions workflow retry, Attempt += 1)<br/>"
            "         ↓<br/>"
            "<b>[RETRY LIMIT GUARD]</b> (If Attempt &gt; 3 → <b>[STATUS: BLOCKED (Require Human Intervene)]</b>)",
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

    # Page Break for Failure Taxonomy
    story.append(PageBreak())

    story.append(Paragraph("3. CI Failure Classification Taxonomy", h1_style))
    story.append(Paragraph(
        "Failures detected in GitHub Actions workflows are classified into strongly typed taxonomies with explicit severity and repairability policies:",
        body_style
    ))

    fail_data = [
        [Paragraph("<b>Failure Type</b>", body_style), Paragraph("<b>Severity</b>", body_style), Paragraph("<b>Repairability</b>", body_style), Paragraph("<b>System Action & Policy</b>", body_style)],
        [Paragraph("SYNTAX_ERROR", body_style), Paragraph("HIGH", body_style), Paragraph("AUTO_REPAIR_SAFE", body_style), Paragraph("Inspect traceback line and patch syntax/indentation/quotes automatically.", body_style)],
        [Paragraph("IMPORT_ERROR", body_style), Paragraph("HIGH", body_style), Paragraph("AUTO_REPAIR_SAFE", body_style), Paragraph("Resolve missing module exports or correct relative/absolute import paths.", body_style)],
        [Paragraph("TEST_FAILURE", body_style), Paragraph("HIGH", body_style), Paragraph("AUTO_REPAIR_SAFE / WITH_APPROVAL", body_style), Paragraph("Adjust service/router handler to match expected schema & status codes.", body_style)],
        [Paragraph("AUTHENTICATION_FAILURE", body_style), Paragraph("HIGH", body_style), Paragraph("AUTO_REPAIR_WITH_APPROVAL", body_style), Paragraph("Fix JWT Bearer header or permission dependency. Requires human approval.", body_style)],
        [Paragraph("DATABASE_MIGRATION_FAILURE", body_style), Paragraph("HIGH", body_style), Paragraph("AUTO_REPAIR_WITH_APPROVAL", body_style), Paragraph("Destructive DDL is blocked; safe schema adjustments require review.", body_style)],
        [Paragraph("LINT_FAILURE", body_style), Paragraph("LOW", body_style), Paragraph("AUTO_REPAIR_SAFE", body_style), Paragraph("Auto-format code and clean unused imports with linter.", body_style)],
        [Paragraph("TYPE_CHECK_FAILURE", body_style), Paragraph("LOW", body_style), Paragraph("AUTO_REPAIR_SAFE", body_style), Paragraph("Add type annotations and resolve union type discrepancies.", body_style)],
        [Paragraph("TIMEOUT", body_style), Paragraph("MEDIUM", body_style), Paragraph("AUTO_REPAIR_SAFE", body_style), Paragraph("Optimize slow queries or increase execution deadline thresholds.", body_style)],
        [Paragraph("FLAKY_TEST", body_style), Paragraph("MEDIUM", body_style), Paragraph("NOT_REPAIRABLE", body_style), Paragraph("Flag for human review. Do not corrupt production code to fix flaky test.", body_style)],
        [Paragraph("NETWORK_FAILURE", body_style), Paragraph("MEDIUM", body_style), Paragraph("EXTERNAL_DEPENDENCY", body_style), Paragraph("Wait for external outage resolution. Automatic code changes blocked.", body_style)]
    ]
    t_fail = Table(fail_data, colWidths=[120, 60, 120, 204])
    t_fail.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_fail)
    story.append(Spacer(1, 10))

    # Security & Prompt Injection
    story.append(Paragraph("4. Defense-in-Depth Security & Prompt Injection Shields", h1_style))
    story.append(Paragraph(
        "Because CI logs and repository source files originate from dynamic execution environments, they represent <b>untrusted inputs</b>. "
        "The system enforces strict security boundaries:",
        body_style
    ))
    story.append(Paragraph("• <b>Untrusted Log Sanitization:</b> All CI logs, stdout, stderr, and test traces are parsed strictly as passive data, never as executable agent instructions.", bullet_style))
    story.append(Paragraph("• <b>Zero Direct Shell Execution:</b> Agents have no raw bash/powershell access; all actions route through validated MCP tools.", bullet_style))
    story.append(Paragraph("• <b>Path Traversal Prevention:</b> FilesystemService canonicalizes paths and rejects '../' escaping workspace boundaries with SecurityViolationError.", bullet_style))
    story.append(Paragraph("• <b>Automated Secret Masker:</b> GitHub tokens (ghp_*, github_pat_*), Bearer tokens, and passwords are automatically scrubbed from logs.", bullet_style))
    story.append(Paragraph("• <b>Deterministic Idempotency Fingerprint:</b> SHA-256 hash of (repo + branch + commit + job + error_sig) prevents duplicate repair loops.", bullet_style))
    story.append(Spacer(1, 10))

    # FastAPI Endpoints
    story.append(Paragraph("5. Day 11 REST API Surface", h1_style))
    api_data = [
        [Paragraph("<b>HTTP Method & Route</b>", body_style), Paragraph("<b>Description & Request Body</b>", body_style)],
        [Paragraph("POST /api/v1/ci/monitor", body_style), Paragraph("Triggers CI monitoring & autonomous repair workflow. Body: CIMonitorRequest.", body_style)],
        [Paragraph("GET /api/v1/ci/{run_id}", body_style), Paragraph("Retrieves CI run record, current status, workflow ID, and repair results.", body_style)],
        [Paragraph("GET /api/v1/ci/{run_id}/failures", body_style), Paragraph("Retrieves classified failure records, root cause, and affected files.", body_style)],
        [Paragraph("POST /api/v1/ci/{run_id}/approve", body_style), Paragraph("Human approval gate for high-risk autonomous repairs. Body: CIApprovalRequest.", body_style)],
        [Paragraph("POST /api/v1/ci/{run_id}/reject", body_style), Paragraph("Rejects repair attempt and marks CI run status as BLOCKED.", body_style)],
        [Paragraph("GET /api/v1/repairs/{repair_id}", body_style), Paragraph("Retrieves structured RepairPlan, required changes, and execution results.", body_style)],
        [Paragraph("GET /api/v1/repairs/{repair_id}/attempts", body_style), Paragraph("Retrieves full history of attempts (1..3) with test pass counts and commit SHAs.", body_style)]
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
    out_dir_1 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Documentation\Day 11\docs")
    out_dir_1.mkdir(parents=True, exist_ok=True)
    pdf_path_1 = out_dir_1 / "01_Day11_CI_CD_Monitoring_and_Autonomous_Repair_Specification.pdf"

    out_dir_2 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Day 11")
    out_dir_2.mkdir(parents=True, exist_ok=True)
    pdf_path_2 = out_dir_2 / "01_Day11_CI_CD_Monitoring_and_Autonomous_Repair_Specification.pdf"

    build_pdf(str(pdf_path_1))
    shutil.copy(str(pdf_path_1), str(pdf_path_2))
    print(f"Copied to: {pdf_path_2}")
