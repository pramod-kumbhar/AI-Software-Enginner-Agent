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
            self.drawString(54, 750, "AI Software Engineer Agent Platform | Day 14: Configuration, Secrets, Providers & FinOps")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Confidential - Autonomous Software Engineering System Specification (Day 14)")
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
    SECONDARY = colors.HexColor("#0284c7") # Sky Blue / FinOps
    ACCENT = colors.HexColor("#16a34a") # Green / Budget
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
    story.append(Paragraph("Day 14: Configuration, Secrets, Providers & FinOps Governance", title_style))
    story.append(Paragraph("Local-First Architecture • Zero-Secret Leakage • Token Telemetry • Quota & Budget Enforcement", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceAfter=12))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & Core Architectural Principles", h1_style))
    story.append(Paragraph(
        "Day 14 embeds a production-grade <b>Configuration Management, Secrets Management, Provider Management, "
        "Token Usage Tracking, FinOps Cost Estimation, and Quota Enforcement Layer</b> into the platform. "
        "Built under the <b>Local-First and Free Principle</b>, the system operates completely offline using Ollama and Mock providers "
        "with zero dependency on paid cloud services. Sensitive credentials (API keys, passwords, JWT secrets) are never hardcoded, "
        "never committed to version control, and strictly scrubbed from all API responses and logs.",
        body_style
    ))

    # Core Metrics Table
    metrics_data = [
        [Paragraph("<b>FinOps & Governance Layer</b>", body_style), Paragraph("<b>Enforced Platform Guardrail</b>", body_style), Paragraph("<b>Verification</b>", body_style)],
        [Paragraph("Configuration Management", body_style), Paragraph("Multi-environment (dev/test/staging/prod) with Pydantic Settings & safe defaults", body_style), Paragraph("Active (100%)", body_style)],
        [Paragraph("Provider Abstraction", body_style), Paragraph("ProviderManager supporting Ollama, Mock, Groq, OpenAI, Anthropic, Google", body_style), Paragraph("Local First", body_style)],
        [Paragraph("Token Telemetry", body_style), Paragraph("UsageTracker recording input/output tokens, latencies, and agent breakdowns", body_style), Paragraph("Active (100%)", body_style)],
        [Paragraph("Cost Calculation", body_style), Paragraph("CostCalculator with dynamic ModelPricing catalog ($0 API cost for local models)", body_style), Paragraph("FinOps Ready", body_style)],
        [Paragraph("Quota Management", body_style), Paragraph("QuotaManager enforcing per-request (6k), daily (100k), and budget ($5) ceilings", body_style), Paragraph("Enforced", body_style)],
        [Paragraph("Circuit Breakers", body_style), Paragraph("Hard limits on agent iterations (max 10) and repair attempts (max 3)", body_style), Paragraph("Bounded", body_style)],
        [Paragraph("Security Config Audit", body_style), Paragraph("ConfigurationSecurityScanner verifying DEBUG, JWT, and CORS compliance", body_style), Paragraph("Compliant", body_style)],
        [Paragraph("Automated Test Suite", body_style), Paragraph("123 / 123 Automated Tests Passing Across Days 1–14 (100% Pass Rate)", body_style), Paragraph("Verified (100%)", body_style)]
    ]
    t_metrics = Table(metrics_data, colWidths=[130, 280, 94])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 10))

    # 2. Provider Abstraction Architecture
    story.append(Paragraph("2. Provider Abstraction & Local-First Strategy", h1_style))
    prov_data = [
        [Paragraph("<b>Provider Name</b>", body_style), Paragraph("<b>Type & Access Mode</b>", body_style), Paragraph("<b>Default Model</b>", body_style), Paragraph("<b>API Cost / 1k</b>", body_style)],
        [Paragraph("Ollama (Primary)", body_style), Paragraph("Local / Free / Self-Hosted", body_style), Paragraph("llama3:latest", body_style), Paragraph("$0.000000", body_style)],
        [Paragraph("Mock (Testing / CI)", body_style), Paragraph("Local / Free / Zero-Network", body_style), Paragraph("mock-llama-3-8b", body_style), Paragraph("$0.000000", body_style)],
        [Paragraph("Groq (Optional)", body_style), Paragraph("Cloud / Accelerated Inference", body_style), Paragraph("llama-3.1-70b", body_style), Paragraph("$0.000590", body_style)],
        [Paragraph("OpenAI (Optional)", body_style), Paragraph("Cloud / Commercial API", body_style), Paragraph("gpt-4o-mini", body_style), Paragraph("$0.000150", body_style)],
        [Paragraph("Anthropic (Optional)", body_style), Paragraph("Cloud / Commercial API", body_style), Paragraph("claude-3-5-sonnet", body_style), Paragraph("$0.003000", body_style)],
        [Paragraph("Google (Optional)", body_style), Paragraph("Cloud / Commercial API", body_style), Paragraph("gemini-1.5-flash", body_style), Paragraph("$0.000075", body_style)]
    ]
    t_prov = Table(prov_data, colWidths=[110, 154, 130, 110])
    t_prov.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_prov)
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # 3. Quota & Budget Enforcement Matrix
    story.append(Paragraph("3. Quota, Budget & Agent Loop Guardrails", h1_style))
    quota_data = [
        [Paragraph("<b>Governance Dimension</b>", body_style), Paragraph("<b>Threshold / Ceiling</b>", body_style), Paragraph("<b>Enforced Action & Behavior</b>", body_style)],
        [Paragraph("Per-Request Token Limit", body_style), Paragraph("6,000 Tokens", body_style), Paragraph("Rejects request with BLOCKED; triggers TOKEN_THRESHOLD alert.", body_style)],
        [Paragraph("Project Daily Token Quota", body_style), Paragraph("100,000 Tokens / Day", body_style), Paragraph("Rejects inference calls exceeding daily aggregate project quota.", body_style)],
        [Paragraph("Project Daily Dollar Budget", body_style), Paragraph("$5.00 USD / Day", body_style), Paragraph("Blocks additional cloud inference; prevents runaway cloud spending.", body_style)],
        [Paragraph("Max Agent Iterations", body_style), Paragraph("10 Iterations", body_style), Paragraph("Halts runaway multi-agent loops and flags for human review.", body_style)],
        [Paragraph("Max Repair Attempts", body_style), Paragraph("3 Attempts", body_style), Paragraph("Circuit breaker stops endless self-healing loops on persistent bugs.", body_style)]
    ]
    t_quota = Table(quota_data, colWidths=[140, 130, 234])
    t_quota.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_quota)
    story.append(Spacer(1, 10))

    # 4. REST API Endpoint Catalog
    story.append(Paragraph("4. Day 14 REST API Endpoint Catalog", h1_style))
    api_data = [
        [Paragraph("<b>HTTP & Path</b>", body_style), Paragraph("<b>Purpose</b>", body_style), Paragraph("<b>Secret Protection</b>", body_style)],
        [Paragraph("GET /api/v1/config/status", body_style), Paragraph("Returns active environment & service flags.", body_style), Paragraph("Masks all credentials & API keys.", body_style)],
        [Paragraph("GET /api/v1/config/audit", body_style), Paragraph("Audits configuration security hygiene.", body_style), Paragraph("Zero-secret audit logs.", body_style)],
        [Paragraph("GET /api/v1/providers", body_style), Paragraph("Lists all configured LLM/embedding providers.", body_style), Paragraph("Never returns provider API keys.", body_style)],
        [Paragraph("GET /api/v1/providers/{p}/health", body_style), Paragraph("Probes provider responsiveness & latency.", body_style), Paragraph("Safe latency/error metadata only.", body_style)],
        [Paragraph("GET /api/v1/usage/summary", body_style), Paragraph("Global token usage, latencies & breakdowns.", body_style), Paragraph("Aggregated telemetry metrics.", body_style)],
        [Paragraph("GET /api/v1/cost/project/{id}", body_style), Paragraph("Returns estimated USD project cost.", body_style), Paragraph("FinOps cost calculations.", body_style)],
        [Paragraph("POST /api/v1/quotas/check", body_style), Paragraph("Pre-flight quota evaluation for tokens/cost.", body_style), Paragraph("Deterministic ALLOWED / BLOCKED.", body_style)]
    ]
    t_api = Table(api_data, colWidths=[150, 204, 150])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_api)
    story.append(Spacer(1, 10))

    # 5. Integrated Execution Workflow
    story.append(Paragraph("5. Integrated Agent & FinOps Execution Pipeline", h1_style))
    flow_box = [
        [Paragraph(
            "<b>[INCOMING TASK REQUEST]</b><br/>"
            "   ↓<br/>"
            "<b>[1. CONFIGURATION AUDIT & AUTH CHECK]</b> (Validates environment & agent role)<br/>"
            "   ↓<br/>"
            "<b>[2. PRE-FLIGHT QUOTA & BUDGET EVALUATION]</b><br/>"
            "   ├── <b>ESTIMATE > 6,000 TOKENS OR DAILY LIMIT EXCEEDED</b> → <b>[QUOTA_BLOCKED]</b><br/>"
            "   └── <b>ESTIMATE WITHIN LIMITS (0-80%)</b> → [ALLOWED]<br/>"
            "         ↓<br/>"
            "<b>[3. LOCAL-FIRST PROVIDER RESOLUTION]</b> (Ollama / Mock / Configured Cloud)<br/>"
            "         ↓<br/>"
            "<b>[4. STRUCTURED INFERENCE & TOOL EXECUTION]</b> (Schema parsing, PromptGuard & MCP)<br/>"
            "         ↓<br/>"
            "<b>[5. TOKEN USAGE & COST TELEMETRY]</b> (Records input/output tokens, cost, latency)<br/>"
            "         ↓<br/>"
            "<b>[6. AUDIT & METRICS PERSISTENCE]</b> (Zero-secret audit logs stored in StorageService)",
            code_style
        )]
    ]
    t_flow = Table(flow_box, colWidths=[504])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ('BOX', (0, 0), (-1, -1), 1, ACCENT),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
    ]))
    story.append(t_flow)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated PDF: {filename}")

if __name__ == "__main__":
    out_dir_1 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Documentation\Day 14\docs")
    out_dir_1.mkdir(parents=True, exist_ok=True)
    pdf_path_1 = out_dir_1 / "01_Day14_Configuration_Management_Secrets_and_FinOps_Specification.pdf"

    out_dir_2 = Path(r"C:\Users\pramod\OneDrive\Desktop\Software team\Day 14")
    out_dir_2.mkdir(parents=True, exist_ok=True)
    pdf_path_2 = out_dir_2 / "01_Day14_Configuration_Management_Secrets_and_FinOps_Specification.pdf"

    build_pdf(str(pdf_path_1))
    shutil.copy(str(pdf_path_1), str(pdf_path_2))
    print(f"Copied to: {pdf_path_2}")
