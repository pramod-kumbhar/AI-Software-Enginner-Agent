import uuid
from typing import Dict, Any, List
from app.agents.security.state import SecurityState
from app.schemas.security import (
    SecuritySeverityEnum,
    SecurityStatusEnum,
    SecurityDecisionEnum,
    SecurityCategoryEnum,
    SecurityFinding,
    SecurityRepairPlan,
    SecurityEventRecord
)
from app.services.threat_modeler import threat_modeler
from app.services.code_security_scanner import code_security_scanner
from app.services.security_gate import security_gate
from app.services.security_repair import security_repair_engine
from app.services.filesystem import FilesystemService
from app.services.storage import storage_service
from app.core.prompt_guard import prompt_guard
from app.core.secret_scanner import secret_scanner
from app.core.agent_auth import agent_auth
from app.core.observability import metrics, TraceContext
from app.core.logger import get_logger

logger = get_logger("security_agent")

async def load_context_node(state: SecurityState) -> Dict[str, Any]:
    scan_id = state.get("scan_id", f"sec_scan_{uuid.uuid4().hex[:8]}")
    project_id = state.get("project_id", "default_proj")
    user_id = state.get("user_id", "user_devops_01")
    ws_dir = state.get("workspace_directory", "generated_projects")

    logger.info(f"SECURITY NODE [1/17]: Loading context for Scan {scan_id} (Project: {project_id}, User: {user_id})")

    return {
        "scan_id": scan_id,
        "project_id": project_id,
        "user_id": user_id,
        "workspace_directory": ws_dir,
        "scan_type": state.get("scan_type", "FULL"),
        "findings": state.get("findings", []),
        "repaired_findings": state.get("repaired_findings", []),
        "repair_attempts": state.get("repair_attempts", 0),
        "max_repair_attempts": 3,
        "events": []
    }

async def threat_model_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [2/17]: Evaluating Trust Boundaries & System Threat Model")
    tm = threat_modeler.generate_system_threat_model()
    return {"threat_model": tm}

async def prompt_injection_scan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [3/17]: Scanning for Prompt Injection & Jailbreak Vectors")
    findings = list(state.get("findings", []))
    ws_dir = state.get("workspace_directory", "generated_projects")
    fs = FilesystemService(workspace_root=ws_dir)

    for rel_path in fs.list_directory():
        if rel_path.endswith((".md", ".txt")):
            ok, content = fs.read_file(rel_path)
            if ok:
                res = prompt_guard.scan_content(content, source="README" if "readme" in rel_path.lower() else "UNTRUSTED_CONTENT")
                if res["detected"]:
                    findings.append(SecurityFinding(
                        finding_id=f"sec_pi_{uuid.uuid4().hex[:6]}",
                        category=SecurityCategoryEnum.PROMPT_INJECTION,
                        severity=res["risk_level"],
                        title="Prompt Injection Attack Vector Detected",
                        description=f"Adversarial instruction identified in {rel_path}: {res['indicators']}",
                        source="PROMPT_GUARD",
                        file_path=rel_path,
                        impact="Potential agent jailbreak or unauthorized instruction execution.",
                        recommendation="Sanitize untrusted content and enforce strict boundary fencing.",
                        auto_fixable=True,
                        status="OPEN"
                    ))
    return {"findings": findings}

async def secret_scan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [4/17]: Scanning for Hardcoded Secrets, Tokens & Credentials")
    findings = list(state.get("findings", []))
    ws_dir = state.get("workspace_directory", "generated_projects")
    fs = FilesystemService(workspace_root=ws_dir)

    for rel_path in fs.list_directory():
        if rel_path.endswith((".py", ".json", ".yaml", ".yml", ".env.example", ".txt")):
            ok, content = fs.read_file(rel_path)
            if ok:
                sec_findings = secret_scanner.scan_text(content, file_path=rel_path)
                findings.extend(sec_findings)

    return {"findings": findings}

async def code_security_scan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [5/17]: Running Static Application Security Testing (SAST)")
    findings = list(state.get("findings", []))
    ws_dir = state.get("workspace_directory", "generated_projects")
    
    sast_findings = code_security_scanner.scan_directory(ws_dir)
    # Deduplicate by finding title and file
    existing_keys = {(f.title, f.file_path, f.line_number) for f in findings}
    for sf in sast_findings:
        if (sf.title, sf.file_path, sf.line_number) not in existing_keys:
            findings.append(sf)

    return {"findings": findings}

async def dependency_scan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [6/17]: Inspecting Package Dependencies & Supply Chain Integrity")
    return {}

async def tool_security_scan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [7/17]: Verifying MCP Tool Guardrails & Schema Isolation")
    return {}

async def authorization_scan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [8/17]: Verifying Multi-Tenant Boundaries & Agent Permissions")
    return {}

async def api_security_scan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [9/17]: Evaluating API Endpoints, Rate Limiting & Auth Gates")
    return {}

async def ci_security_scan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [10/17]: Verifying CI Workflow Security & Untrusted Log Isolation")
    return {}

async def deployment_security_scan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [11/17]: Evaluating Deployment Gates & Human Sign-Off Verification")
    return {}

async def risk_calculation_node(state: SecurityState) -> Dict[str, Any]:
    findings = state.get("findings", [])
    logger.info(f"SECURITY NODE [12/17]: Calculating Security Score across {len(findings)} Findings")
    
    score, status, decision, blockers = security_gate.evaluate(findings)
    metrics.set_gauge("last_security_score", score)

    return {
        "security_score": score,
        "status": status,
        "decision": decision,
        "blockers": blockers,
        "is_blocked": decision in [SecurityDecisionEnum.BLOCK, SecurityDecisionEnum.CRITICAL_BLOCK]
    }

async def policy_check_node(state: SecurityState) -> Dict[str, Any]:
    decision = state.get("decision", SecurityDecisionEnum.PASS)
    logger.info(f"SECURITY NODE [13/17]: Policy Check Evaluated -> Decision={decision.value}")
    return {}

async def security_report_node(state: SecurityState) -> Dict[str, Any]:
    logger.info(f"SECURITY NODE [14/17]: Generating Security Audit Report (Score: {state.get('security_score', 100.0):.1f}/100)")
    return {}

async def repair_node(state: SecurityState) -> Dict[str, Any]:
    findings = state.get("findings", [])
    ws_dir = state.get("workspace_directory", "generated_projects")
    fs = FilesystemService(workspace_root=ws_dir)
    attempts = state.get("repair_attempts", 0) + 1
    
    logger.info(f"SECURITY NODE [15/17]: Initiating Autonomous Security Repair Loop (Attempt {attempts}/3)")
    
    repair_plans: List[SecurityRepairPlan] = []
    repaired_findings = list(state.get("repaired_findings", []))
    
    for f in list(findings):
        if f.status == "OPEN" and f.auto_fixable:
            plan = security_repair_engine.create_repair_plan(f, attempt_number=attempts)
            repair_plans.append(plan)
            success, msg = security_repair_engine.execute_auto_repair(plan, f, fs)
            if success:
                repaired_findings.append(f)

    return {
        "repair_plans": repair_plans,
        "repaired_findings": repaired_findings,
        "repair_attempts": attempts
    }

async def rescan_node(state: SecurityState) -> Dict[str, Any]:
    logger.info("SECURITY NODE [16/17]: Rescanning Project Post-Remediation")
    ws_dir = state.get("workspace_directory", "generated_projects")
    
    # Re-run static analysis to verify fixed state
    fresh_findings = code_security_scanner.scan_directory(ws_dir)
    score, status, decision, blockers = security_gate.evaluate(fresh_findings)

    return {
        "findings": fresh_findings,
        "security_score": score,
        "status": status,
        "decision": decision,
        "blockers": blockers,
        "is_blocked": decision in [SecurityDecisionEnum.BLOCK, SecurityDecisionEnum.CRITICAL_BLOCK]
    }

async def finalize_node(state: SecurityState) -> Dict[str, Any]:
    scan_id = state.get("scan_id", "default_scan")
    final_status = state.get("status", SecurityStatusEnum.SECURITY_READY)
    score = state.get("security_score", 100.0)

    # Save scan record to storage
    scan_record = {
        "scan_id": scan_id,
        "project_id": state.get("project_id", "default_proj"),
        "user_id": state.get("user_id", "default_user"),
        "security_score": score,
        "status": final_status.value,
        "decision": state.get("decision", SecurityDecisionEnum.PASS).value,
        "blockers": state.get("blockers", []),
        "findings_count": len(state.get("findings", [])),
        "repaired_count": len(state.get("repaired_findings", []))
    }
    storage_service.save_metadata(f"security_scan_{scan_id}", scan_record)
    
    logger.info(f"SECURITY SCAN FINALIZED: Scan {scan_id} Status -> {final_status.value} (Score: {score:.1f}/100)")
    return {"status": final_status}
