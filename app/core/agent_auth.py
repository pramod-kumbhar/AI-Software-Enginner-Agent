from typing import Dict, Any, List, Set, Tuple, Optional
from app.schemas.security import AgentPermission, SecuritySeverityEnum
from app.core.logger import get_logger

logger = get_logger("agent_auth")

class AgentAuthorizationPolicy:
    """
    Deny-By-Default Agent Authorization & Multi-Tenant Isolation Engine.
    Enforces strict role permissions, action scopes, and user/project boundary isolation.
    """

    # Explicit Allowlist Matrix: (agent_name, resource, action) -> (risk_level, approval_required)
    PERMISSION_MATRIX: Dict[Tuple[str, str, str], Tuple[str, bool]] = {
        # PLANNER
        ("PlannerAgent", "requirements", "read"): ("READ_ONLY", False),
        ("PlannerAgent", "plan", "write"): ("LOW", False),
        ("PlannerAgent", "project_metadata", "read"): ("READ_ONLY", False),
        
        # ARCHITECT
        ("ArchitectAgent", "plan", "read"): ("READ_ONLY", False),
        ("ArchitectAgent", "architecture", "write"): ("LOW", False),
        ("ArchitectAgent", "project_metadata", "read"): ("READ_ONLY", False),
        
        # DEVELOPER
        ("DeveloperAgent", "workspace", "read"): ("READ_ONLY", False),
        ("DeveloperAgent", "workspace", "write"): ("MEDIUM", False),
        ("DeveloperAgent", "tests", "execute"): ("LOW", False),
        ("DeveloperAgent", "git", "diff"): ("READ_ONLY", False),
        ("DeveloperAgent", "git", "status"): ("READ_ONLY", False),
        ("DeveloperAgent", "git", "commit"): ("HIGH", False),
        ("DeveloperAgent", "git", "create_branch"): ("MEDIUM", False),
        ("DeveloperAgent", "git", "create_pr"): ("HIGH", True),

        # QA
        ("QAAgent", "workspace", "read"): ("READ_ONLY", False),
        ("QAAgent", "tests", "execute"): ("LOW", False),
        ("QAAgent", "qa_report", "write"): ("LOW", False),
        ("QAAgent", "git", "diff"): ("READ_ONLY", False),

        # CI / REPAIR AGENT
        ("CIAgent", "ci_logs", "read"): ("READ_ONLY", False),
        ("CIAgent", "workspace", "read"): ("READ_ONLY", False),
        ("CIAgent", "workspace", "write"): ("MEDIUM", False),
        ("CIAgent", "tests", "execute"): ("LOW", False),

        # RELEASE AGENT
        ("ReleaseAgent", "ci", "read"): ("READ_ONLY", False),
        ("ReleaseAgent", "qa", "read"): ("READ_ONLY", False),
        ("ReleaseAgent", "security", "read"): ("READ_ONLY", False),
        ("ReleaseAgent", "deployment", "staging"): ("HIGH", False),
        ("ReleaseAgent", "deployment", "production"): ("CRITICAL", True),
        ("ReleaseAgent", "deployment", "rollback"): ("HIGH", False),
        ("ReleaseAgent", "release", "manifest"): ("LOW", False),

        # SECURITY AGENT
        ("SecurityAgent", "workspace", "read"): ("READ_ONLY", False),
        ("SecurityAgent", "security", "scan"): ("LOW", False),
        ("SecurityAgent", "repair_plan", "write"): ("LOW", False),
        ("SecurityAgent", "audit", "read"): ("READ_ONLY", False),

        # ADMIN
        ("Admin", "*", "*"): ("HIGH", False)
    }

    @classmethod
    def check_permission(
        cls,
        agent_name: str,
        resource: str,
        action: str,
        approval_granted: bool = False
    ) -> Tuple[bool, str]:
        """
        Evaluates whether an agent has permission to perform an action on a resource.
        Returns (is_allowed, reason).
        """
        # Admin override
        if agent_name.upper() == "ADMIN":
            return True, "Authorized as Administrator."

        key = (agent_name, resource.lower(), action.lower())
        
        if key not in cls.PERMISSION_MATRIX:
            logger.warning(f"AUTHORIZATION DENIED: Agent '{agent_name}' has no permission for {resource}:{action}")
            return False, f"DENY BY DEFAULT: Agent '{agent_name}' is not authorized to execute {action} on {resource}."

        risk_level, requires_approval = cls.PERMISSION_MATRIX[key]

        if requires_approval and not approval_granted:
            logger.warning(f"APPROVAL REQUIRED: Agent '{agent_name}' requested {resource}:{action} without human approval.")
            return False, f"HUMAN APPROVAL REQUIRED: Action {action} on {resource} requires explicit human sign-off."

        return True, "Authorized by policy."

    @classmethod
    def check_tenant_isolation(
        cls,
        requester_user_id: str,
        target_user_id: str,
        requester_project_id: str,
        target_project_id: str,
        is_admin: bool = False
    ) -> Tuple[bool, str]:
        """
        Validates multi-tenant and multi-user boundary isolation.
        Prevents User A from accessing User B data, or Project A from reading Project B files.
        """
        if is_admin:
            return True, "Tenant access granted for Administrator."

        if requester_user_id != target_user_id:
            logger.error(f"CROSS-USER ACCESS BLOCKED: User '{requester_user_id}' attempted to access User '{target_user_id}' resource.")
            return False, f"CROSS-USER ACCESS DENIED: User '{requester_user_id}' cannot access resources belonging to '{target_user_id}'."

        if requester_project_id != target_project_id:
            logger.error(f"CROSS-PROJECT ACCESS BLOCKED: Project '{requester_project_id}' attempted to access Project '{target_project_id}'.")
            return False, f"CROSS-PROJECT ACCESS DENIED: Cannot cross project boundary between '{requester_project_id}' and '{target_project_id}'."

        return True, "Tenant isolation verified."

agent_auth = AgentAuthorizationPolicy()
