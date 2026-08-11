import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.security import (
    SecurityFinding,
    SecurityRepairPlan,
    SecurityCategoryEnum,
    SecuritySeverityEnum
)
from app.services.filesystem import FilesystemService
from app.core.logger import get_logger

logger = get_logger("security_repair")

class SecurityRepairEngine:
    """
    Autonomous Security Vulnerability Repair Engine.
    Generates structured repair plans and executes safe auto-remediation for eligible findings.
    """

    @classmethod
    def create_repair_plan(cls, finding: SecurityFinding, attempt_number: int = 1) -> SecurityRepairPlan:
        """Constructs a deterministic SecurityRepairPlan from an open finding."""
        plan_id = f"srp_{uuid.uuid4().hex[:8]}"
        
        # Determine remediation instructions
        if finding.category == SecurityCategoryEnum.SECRETS:
            req_change = "Replace hardcoded credential with os.getenv() configuration call."
            sec_req = "Credentials must be sourced strictly from environment variables or secret manager."
        elif finding.category == SecurityCategoryEnum.COMMAND_EXECUTION:
            req_change = "Change subprocess shell=True to shell=False and pass arguments as list."
            sec_req = "Subprocesses must never use shell=True."
        elif finding.category == SecurityCategoryEnum.PROMPT_INJECTION:
            req_change = "Wrap untrusted text in data fences and redact instruction override keywords."
            sec_req = "Untrusted input must never be directly interpreted as LLM system instructions."
        elif finding.category == SecurityCategoryEnum.DEPENDENCIES:
            req_change = "Pin package dependency with exact version ==x.y.z."
            sec_req = "All project dependencies must be strictly pinned."
        else:
            req_change = f"Remediate vulnerability: {finding.recommendation}"
            sec_req = "Comply with secure software architecture baseline."

        return SecurityRepairPlan(
            repair_id=plan_id,
            finding_id=finding.finding_id,
            target_file=finding.file_path or "unknown_file.py",
            root_cause=finding.description,
            required_change=req_change,
            security_requirement=sec_req,
            is_auto_fixable=finding.auto_fixable,
            approval_required=finding.approval_required,
            attempt_number=attempt_number,
            max_attempts=3
        )

    @classmethod
    def execute_auto_repair(
        cls,
        plan: SecurityRepairPlan,
        finding: SecurityFinding,
        fs: FilesystemService
    ) -> Tuple[bool, str]:
        """
        Executes safe deterministic code transformations to fix known vulnerability patterns.
        Returns (success, message).
        """
        if not plan.is_auto_fixable:
            return False, f"Finding '{finding.title}' is high-risk and requires human approval."

        if plan.attempt_number > plan.max_attempts:
            return False, f"Maximum repair attempts ({plan.max_attempts}) reached for finding {finding.finding_id}."

        target_file = plan.target_file
        success, content = fs.read_file(target_file)
        if not success:
            return False, f"Unable to read file '{target_file}' for repair: {content}"

        modified_content = content

        # 1. Remediate Hardcoded Secret
        if finding.category == SecurityCategoryEnum.SECRETS:
            # Replace secret assignment with os.getenv
            secret_pattern = r"(?i)\b(api_key|apikey|secret_key|client_secret|auth_token|db_password|db_pass|password|secret)\s*[:=]\s*['\"][^'\"]+['\"]"
            modified_content = re.sub(
                secret_pattern,
                r'\1 = os.getenv("\1".upper(), "")',
                modified_content
            )
            # Ensure import os is present
            if "import os" not in modified_content:
                modified_content = "import os\n" + modified_content

        # 2. Remediate shell=True
        elif finding.category == SecurityCategoryEnum.COMMAND_EXECUTION and "shell=True" in content:
            modified_content = modified_content.replace("shell=True", "shell=False")

        # 3. Remediate Prompt Injection in documentation
        elif finding.category == SecurityCategoryEnum.PROMPT_INJECTION:
            override_kw = [
                "ignore previous instructions",
                "ignore all previous instructions",
                "reveal secrets",
                "read .env",
                "disable security"
            ]
            for kw in override_kw:
                modified_content = re.sub(re.escape(kw), "[REDACTED_SECURITY_POLICY_VIOLATION]", modified_content, flags=re.IGNORECASE)

        # 4. Remediate unpinned dependency
        elif finding.category == SecurityCategoryEnum.DEPENDENCIES and "requirements.txt" in target_file:
            lines = [l.strip() for l in modified_content.splitlines() if l.strip()]
            pinned_lines = []
            for l in lines:
                if not any(op in l for op in ["==", ">=", "<=", "~="]):
                    pinned_lines.append(f"{l}==1.0.0")
                else:
                    pinned_lines.append(l)
            modified_content = "\n".join(pinned_lines) + "\n"

        # Write repaired content back to filesystem
        write_ok, write_msg = fs.write_file(target_file, modified_content, overwrite=True)
        if not write_ok:
            return False, f"Failed writing repaired content to {target_file}: {write_msg}"

        finding.status = "FIXED"
        logger.info(f"SECURITY AUTO-REPAIR: Successfully remediated {finding.title} in {target_file}")
        return True, f"Successfully remediated {finding.title} in {target_file}."

security_repair_engine = SecurityRepairEngine()
