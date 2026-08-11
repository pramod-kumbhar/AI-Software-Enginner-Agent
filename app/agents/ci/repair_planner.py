import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.schemas.ci import CIFailure, RepairPlan, RepairabilityEnum, CIFailureTypeEnum, FailureSeverityEnum

class RepairPlanner:
    """
    Synthesizes structured RepairPlans based on CIFailure classifications.
    Enforces policy checks for approval requirements and bounds repair instructions.
    """

    @classmethod
    def create_repair_plan(cls, failure: CIFailure, task_id: Optional[str] = None) -> RepairPlan:
        repair_id = f"repair_{uuid.uuid4().hex[:8]}"
        t_id = task_id or failure.developer_task_id or f"task_{uuid.uuid4().hex[:6]}"

        # Policy Rule: High-risk areas strictly require human approval
        approval_required = (
            failure.repairability == RepairabilityEnum.AUTO_REPAIR_WITH_APPROVAL or
            failure.severity == FailureSeverityEnum.CRITICAL or
            failure.failure_type in (
                CIFailureTypeEnum.AUTHENTICATION_FAILURE,
                CIFailureTypeEnum.DATABASE_MIGRATION_FAILURE
            )
        )

        required_changes: List[str] = []
        developer_instructions: List[str] = []

        if failure.failure_type == CIFailureTypeEnum.SYNTAX_ERROR:
            required_changes.append(f"Fix Python syntax error in affected file: {', '.join(failure.affected_files)}")
            developer_instructions.append("Inspect offending line indicated in traceback and fix syntax/indentation/quotes.")
            risk_level = "LOW_RISK"
            complexity = "XS"

        elif failure.failure_type == CIFailureTypeEnum.IMPORT_ERROR:
            required_changes.append(f"Correct broken import or missing symbol in: {', '.join(failure.affected_files)}")
            developer_instructions.append("Verify module exports, fix relative/absolute import path or export missing class/function.")
            risk_level = "LOW_RISK"
            complexity = "S"

        elif failure.failure_type == CIFailureTypeEnum.LINT_FAILURE:
            required_changes.append("Format code and resolve linting violations.")
            developer_instructions.append("Run formatting/lint rules and clean unused imports or style violations.")
            risk_level = "LOW_RISK"
            complexity = "XS"

        elif failure.failure_type == CIFailureTypeEnum.AUTHENTICATION_FAILURE:
            required_changes.append("Align authentication token header format or permission validation.")
            developer_instructions.append("Ensure JWT Bearer token format is parsed properly and authorization dependency matches security specs.")
            risk_level = "HIGH_RISK"
            complexity = "M"

        elif failure.failure_type == CIFailureTypeEnum.TEST_FAILURE:
            required_changes.append(f"Align implementation logic with expected test behavior in: {', '.join(failure.affected_files)}")
            developer_instructions.append(f"Root cause: {failure.root_cause}. Adjust service/router handler to return expected status code and schema.")
            risk_level = "MEDIUM_RISK" if not approval_required else "HIGH_RISK"
            complexity = "S"

        else:
            required_changes.append(f"Resolve failure in step: {failure.failed_step}")
            developer_instructions.append("Inspect failure traceback and apply minimal targeted fix.")
            risk_level = "MEDIUM_RISK"
            complexity = "M"

        tests_to_run = list(failure.affected_tests) if failure.affected_tests else ["tests/"]

        return RepairPlan(
            repair_id=repair_id,
            failure_id=failure.failure_id,
            project_id=failure.project_id,
            task_id=t_id,
            summary=f"Automated repair for {failure.failure_type.value}: {failure.error_summary[:100]}",
            root_cause=failure.root_cause,
            affected_files=failure.affected_files,
            required_changes=required_changes,
            tests_to_run=tests_to_run,
            risk_level=risk_level,
            estimated_complexity=complexity,
            approval_required=approval_required,
            developer_instructions="\n".join(developer_instructions),
            rollback_strategy="Reset workspace to previous git commit and discard changes if tests fail.",
            verification_plan="Run affected tests, execute full pytest regression suite, and run QA evaluation."
        )

repair_planner = RepairPlanner()
