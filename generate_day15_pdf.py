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
            self.drawString(54, 750, "AI Software Engineer Agent Platform | Day 15: Human-in-the-Loop & Durable Execution")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Confidential - Autonomous Software Engineering System Specification (Day 15)")
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
    SECONDARY = colors.HexColor("#6366f1") # Indigo / HITL
    ACCENT = colors.HexColor("#0284c7") # Sky Blue
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
    story.append(Paragraph("Day 15: Human-in-the-Loop, Checkpointing & Durable Execution", title_style))
    story.append(Paragraph("LangGraph Interrupt Gates • Cryptographic Action Hashing • Rejection & Rework • RBAC Sign-offs", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=12))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & Human-Supervised Architecture", h1_style))
    story.append(Paragraph(
        "Day 15 transitions the platform from pure autonomous execution into a <b>production-grade, human-supervised "
        "agentic engineering system</b>. Using LangGraph checkpointing and stateful interrupt gates, the agentic pipeline "
        "pauses at high-risk boundaries (Architecture Authorization, Production Deployment), requests human decision via "
        "cryptographic action hashing, and supports seamless approval, rejection with feedback, and bounded rework loops without "
        "restarting completed nodes.",
        body_style
    ))

    # Metrics Table
    metrics_data = [
        [Paragraph("<b>Governance Dimension</b>", body_style), Paragraph("<b>Day 15 Implementation Standard</b>", body_style), Paragraph("<b>Verification</b>", body_style)],
        [Paragraph("Workflow Orchestration", body_style), Paragraph("LangGraph StateGraph with MemorySaver durable checkpointer & interrupt points", body_style), Paragraph("Active (100%)", body_style)],
        [Paragraph("Approval Gate Engine", body_style), Paragraph("ApprovalService enforcing RBAC, Separation of Duties, and 24h Expiration", body_style), Paragraph("Enforced", body_style)],
        [Paragraph("Cryptographic Fencing", body_style), Paragraph("SHA-256 action_hash validation preventing stale or altered action execution", body_style), Paragraph("Secured", body_style)],
        [Paragraph("Rejection / Rework Loop", body_style), Paragraph("Structured human feedback injection with bounded rework cutoff (MAX 3 attempts)", body_style), Paragraph("Bounded", body_style)],
        [Paragraph("Observability & Timeline", body_style), Paragraph("TimelineService tracking fine-grained node events, latencies, and human decisions", body_style), Paragraph("Auditable", body_style)],
        [Paragraph("Production Deployment", body_style), Paragraph("Mandatory human release approval gate prior to executing container rollouts", body_style), Paragraph("Gated", body_style)],
        [Paragraph("Automated Test Suite", body_style), Paragraph("132 / 132 Automated Tests Passing Across Days 1–15 (100% Pass Rate)", body_style), Paragraph("Verified (100%)", body_style)]
    ]
    t_metrics = Table(metrics_data, colWidths=[130, 280, 94])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 10))

    # 2. Role-Based Approval Policy Matrix
    story.append(Paragraph("2. Role-Based Approval Authorization & Hierarchy", h1_style))
    rbac_data = [
        [Paragraph("<b>Approval Type</b>", body_style), Paragraph("<b>Risk Level</b>", body_style), Paragraph("<b>Required Role</b>", body_style), Paragraph("<b>Approval Policy</b>", body_style)],
        [Paragraph("ARCHITECTURE_APPROVAL", body_style), Paragraph("HIGH", body_style), Paragraph("TECH_LEAD / ADMIN", body_style), Paragraph("Authorizes framework, DB schema, and component design.", body_style)],
        [Paragraph("CODE_APPROVAL", body_style), Paragraph("MEDIUM / HIGH", body_style), Paragraph("DEVELOPER / TECH_LEAD", body_style), Paragraph("Reviews PR diffs, generated tests, and coverage.", body_style)],
        [Paragraph("DATABASE_MIGRATION_APPROVAL", body_style), Paragraph("HIGH", body_style), Paragraph("TECH_LEAD / ADMIN", body_style), Paragraph("Gated for schema-breaking changes & DDL migrations.", body_style)],
        [Paragraph("SECURITY_APPROVAL", body_style), Paragraph("HIGH", body_style), Paragraph("SECURITY_ENGINEER", body_style), Paragraph("Required for auth, secrets, sandbox, or IAM updates.", body_style)],
        [Paragraph("PRODUCTION_DEPLOYMENT_APPROVAL", body_style), Paragraph("CRITICAL", body_style), Paragraph("RELEASE_MANAGER / ADMIN", body_style), Paragraph("Mandatory sign-off prior to production traffic routing.", body_style)],
        [Paragraph("HIGH_RISK_TOOL_APPROVAL", body_style), Paragraph("HIGH / CRITICAL", body_style), Paragraph("TECH_LEAD / ADMIN", body_style), Paragraph("Gated for git force pushes, shell execution, DB wipes.", body_style)]
    ]
    t_rbac = Table(rbac_data, colWidths=[140, 75, 115, 174])
    t_rbac.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_rbac)
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # 3. End-to-End Human-in-the-Loop Workflow
    story.append(Paragraph("3. End-to-End Human-in-the-Loop Execution Pipeline", h1_style))
    flow_box = [
        [Paragraph(
            "<b>[USER PROJECT INITIATION]</b><br/>"
            "   ↓<br/>"
            "<b>[1. PLANNER AGENT]</b> (Decomposes requirements into tasks, risks & DAG)<br/>"
            "   ↓<br/>"
            "<b>[2. ARCHITECT AGENT]</b> (Designs modular blueprint, components & database entities)<br/>"
            "   ↓<br/>"
            "<b>[3. HUMAN ARCHITECTURE APPROVAL GATE]</b> (Calculates action hash; pauses workflow)<br/>"
            "   ├── <b>[REJECT / REQUEST CHANGES]</b> ──→ <b>[ARCHITECT REWORK]</b> (Injects feedback, attempt &lt;= 3)<br/>"
            "   │                                           ↓ (Regenerates Architecture)<br/>"
            "   │                                     [HUMAN ARCH APPROVAL GATE]<br/>"
            "   └── <b>[APPROVE (TECH_LEAD)]</b><br/>"
            "         ↓<br/>"
            "<b>[4. DEVELOPER AGENT]</b> (Generates clean Python modules, endpoints & tests)<br/>"
            "   ↓<br/>"
            "<b>[5. QA AGENT]</b> (Executes automated test suite; verifies coverage &gt;= 80%)<br/>"
            "   ↓<br/>"
            "<b>[6. SECURITY AGENT]</b> (Scans AST, secrets, prompt injection, and threat model)<br/>"
            "   ↓<br/>"
            "<b>[7. RELEASE AGENT]</b> (Evaluates policy engine; prepares deployment readiness artifact)<br/>"
            "   ↓<br/>"
            "<b>[8. HUMAN DEPLOYMENT APPROVAL GATE]</b> (CRITICAL risk gate; halts deployment)<br/>"
            "   └── <b>[APPROVE (RELEASE_MANAGER / ADMIN)]</b><br/>"
            "         ↓<br/>"
            "<b>[9. PRODUCTION DEPLOYMENT & HEALTH CHECK]</b> (Promotes release & monitors probes)<br/>"
            "         ↓<br/>"
            "<b>[10. WORKFLOW COMPLETED & AUDIT PERSISTED]</b>",
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

    # 4. REST API Endpoint Catalog
    story.append(Paragraph("4. Day 15 REST API Endpoint Catalog", h1_style))
    api_data = [
        [Paragraph("<b>HTTP Method & Path</b>", body_style), Paragraph("<b>Action & Behavior</b>", body_style), Paragraph("<b>Authorization Gate</b>", body_style)],
        [Paragraph("POST /api/v1/agent/execute", body_style), Paragraph("Starts durable multi-agent workflow until first HITL gate.", body_style), Paragraph("Authenticated User", body_style)],
        [Paragraph("GET /api/v1/agent/{id}/state", body_style), Paragraph("Returns full persistent AgentState from checkpoint.", body_style), Paragraph("Tenant / Project RBAC", body_style)],
        [Paragraph("GET /api/v1/agent/{id}/timeline", body_style), Paragraph("Returns chronological execution events and durations.", body_style), Paragraph("Read Access", body_style)],
        [Paragraph("POST /api/v1/agent/{id}/resume", body_style), Paragraph("Resumes interrupted thread after human decision.", body_style), Paragraph("Authorized Reviewer", body_style)],
        [Paragraph("POST /api/v1/agent/{id}/pause", body_style), Paragraph("Safely pauses workflow at current node boundary.", body_style), Paragraph("Operator / Admin", body_style)],
        [Paragraph("POST /api/v1/agent/{id}/cancel", body_style), Paragraph("Safely cancels execution and rolls back uncommitted actions.", body_style), Paragraph("Operator / Admin", body_style)],
        [Paragraph("GET /api/v1/approvals", body_style), Paragraph("Lists pending, approved, and rejected authorization requests.", body_style), Paragraph("Reviewer / Lead", body_style)],
        [Paragraph("POST /api/v1/approvals/{id}/approve", body_style), Paragraph("Applies APPROVE decision with action hash validation.", body_style), Paragraph("Role-Validated Approver", body_style)],
        [Paragraph("POST /api/v1/approvals/{id}/request-changes", body_style), Paragraph("Sends structured rework feedback back to agent node.", body_style), Paragraph("Role-Validated Approver", body_style)]
    ]
    t_api = Table(api_data, colWidths=[155, 215, 134])
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
    out_dir_1 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Documentation\Day 15\docs")
    out_dir_1.mkdir(parents=True, exist_ok=True)
    pdf_path_1 = out_dir_1 / "01_Day15_Human_in_the_Loop_and_Durable_Execution_Specification.pdf"

    out_dir_2 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Day 15")
    out_dir_2.mkdir(parents=True, exist_ok=True)
    pdf_path_2 = out_dir_2 / "01_Day15_Human_in_the_Loop_and_Durable_Execution_Specification.pdf"

    build_pdf(str(pdf_path_1))
    shutil.copy(str(pdf_path_1), str(pdf_path_2))
    print(f"Copied to: {pdf_path_2}")
