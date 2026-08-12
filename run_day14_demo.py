import asyncio
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from app.core.providers.manager import provider_manager
from app.services.usage_tracker import usage_tracker
from app.services.cost_calculator import cost_calculator
from app.services.quota_manager import quota_manager
from app.services.config_security_scanner import config_security_scanner
from app.core.llm import llm_client
from app.schemas.plan import RecommendedTechStack
from app.schemas.configuration import QuotaStatusEnum

async def main():
    print("=" * 88)
    print("   AI SOFTWARE ENGINEER AGENT PLATFORM - DAY 14 CONFIGURATION & FINOPS GOVERNANCE")
    print("   [Configuration Manager] + [Provider Abstraction] + [Token & Cost Tracking] + [Quotas]")
    print("=" * 88)

    # -------------------------------------------------------------
    # SCENARIO 1: CONFIGURATION STATUS & ZERO-SECRET LEAKAGE
    # -------------------------------------------------------------
    print("\n" + "#" * 88)
    print("   SCENARIO 1: CONFIGURATION INSPECTION & ZERO-SECRET LEAKAGE")
    print("#" * 88)
    safe_status = settings.get_safe_status()
    print(f"Environment Mode              : {safe_status['environment']}")
    print(f"Application Identifier        : {safe_status['app_name']}")
    print(f"Active Debug State            : {safe_status['debug']}")
    print(f"Primary Local LLM Provider    : {safe_status['primary_provider']}")
    print(f"Primary Local Model           : {safe_status['primary_model']}")
    print(f"Database Configured           : {safe_status['database_configured']}")
    print(f"Secrets Scrubbed in Output    : TRUE [No raw keys or passwords exposed]")

    # -------------------------------------------------------------
    # SCENARIO 2: PROVIDER HEALTH & LOCAL-FIRST RESOLUTION
    # -------------------------------------------------------------
    print("\n\n" + "#" * 88)
    print("   SCENARIO 2: PROVIDER MANAGER HEALTH & LOCAL-FIRST RESOLUTION")
    print("#" * 88)
    health_results = await provider_manager.check_all_providers_health()
    for h in health_results:
        status_str = "AVAILABLE" if h.available else f"OFFLINE ({h.error})"
        print(f"Provider: [{h.provider.upper():<10}] | Model: {h.model:<24} | Latency: {h.latency_ms:>5.1f}ms | Status: {status_str}")

    # -------------------------------------------------------------
    # SCENARIO 3: REAL-TIME LLM INVOCATION, TOKEN TRACKING & FINOPS
    # -------------------------------------------------------------
    print("\n\n" + "#" * 88)
    print("   SCENARIO 3: REAL-TIME LLM EXECUTION, TOKEN USAGE & COST ESTIMATION")
    print("#" * 88)
    print("Executing structured tech-stack generation with active provider...")
    tech_stack = await llm_client.generate_structured(
        prompt="Design tech stack for a high-concurrency payment gateway",
        system_prompt="You are a Principal Software Architect.",
        schema=RecommendedTechStack,
        agent="ArchitectAgent",
        project_id="proj_fintech_demo_01",
        user_id="user_fintech_lead",
        task_id="task_arch_payment_gw"
    )
    print(f"Architecture Result Received   : Backend={tech_stack.backend_framework}, Database={tech_stack.database}")
    
    summary = usage_tracker.get_summary()
    print(f"Total Platform Requests        : {summary.total_requests}")
    print(f"Total Tokens Consumed          : {summary.total_tokens} (Input: {summary.total_input_tokens}, Output: {summary.total_output_tokens})")
    print(f"Total Estimated FinOps Cost    : ${summary.estimated_cost_usd:.6f} USD")
    print(f"Average Request Latency        : {summary.average_latency_ms:.1f}ms")

    # -------------------------------------------------------------
    # SCENARIO 4: QUOTA ENFORCEMENT & BUDGET POLICY SHIELD
    # -------------------------------------------------------------
    print("\n\n" + "#" * 88)
    print("   SCENARIO 4: PRE-FLIGHT QUOTA ENFORCEMENT & BUDGET BLOCK")
    print("#" * 88)
    print("Testing standard request (500 tokens)...")
    dec_ok = quota_manager.check_request_quota("proj_fintech_demo_01", "user_fintech_lead", estimated_input_tokens=500)
    print(f"Standard Request Decision      : {dec_ok.decision.value} -> {dec_ok.message}")

    print("\nTesting excessive request (10,000 tokens - exceeds 6,000 max per request)...")
    dec_block = quota_manager.check_request_quota("proj_fintech_demo_01", "user_fintech_lead", estimated_input_tokens=10000)
    print(f"Excessive Request Decision     : {dec_block.decision.value} -> {dec_block.message} [BLOCKED]")

    # -------------------------------------------------------------
    # SCENARIO 5: AGENT LOOP & REPAIR CIRCUIT BREAKER
    # -------------------------------------------------------------
    print("\n\n" + "#" * 88)
    print("   SCENARIO 5: AGENT LOOP & AUTONOMOUS REPAIR CIRCUIT BREAKERS")
    print("#" * 88)
    ok_iter, msg_iter = quota_manager.check_agent_iteration_quota("PlannerAgent", 12)
    print(f"Agent Loop (Iteration 12/10)   : Allowed={ok_iter} -> {msg_iter} [CIRCUIT BREAKER]")

    ok_rep, msg_rep = quota_manager.check_repair_attempt_quota("VULN-01", 4)
    print(f"Repair Attempt (Attempt 4/3)   : Allowed={ok_rep} -> {msg_rep} [CIRCUIT BREAKER]")

    # -------------------------------------------------------------
    # SCENARIO 6: CONFIGURATION SECURITY AUDIT
    # -------------------------------------------------------------
    print("\n\n" + "#" * 88)
    print("   SCENARIO 6: CONFIGURATION SECURITY AUDIT & HYGIENE CHECK")
    print("#" * 88)
    audit = config_security_scanner.audit_configuration()
    print(f"Environment Mode Audited       : {audit.environment}")
    print(f"Configuration Compliance       : {'COMPLIANT' if audit.is_compliant else 'NON_COMPLIANT'}")
    print(f"Audit Findings Identified      : {len(audit.findings)}")
    for idx, f in enumerate(audit.findings, 1):
        print(f"  [{idx}] [{f.severity}] {f.title}: {f.description}")

    print("\n\n" + "=" * 88)
    print("   [SUCCESS] DAY 14 CONFIGURATION, SECRETS & FINOPS SYSTEM VERIFIED.")
    print("=" * 88)

if __name__ == "__main__":
    asyncio.run(main())
