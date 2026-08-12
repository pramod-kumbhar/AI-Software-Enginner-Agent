from typing import Dict, Any, Optional, Tuple
from app.schemas.approval import ToolApprovalPolicy, RiskLevelEnum, ReviewerRoleEnum

class ToolApprovalPolicyManager:
    """
    Tool Approval Policy Engine.
    Enforces risk evaluation and mandatory human authorization on high-risk MCP tools.
    """
    POLICIES: Dict[str, ToolApprovalPolicy] = {
        "github.create_pr": ToolApprovalPolicy(
            tool_name="github.create_pr",
            risk_level=RiskLevelEnum.HIGH,
            requires_approval=True,
            required_role=ReviewerRoleEnum.TECH_LEAD,
            allowed_environments=["development", "test", "staging"]
        ),
        "github.merge_pr": ToolApprovalPolicy(
            tool_name="github.merge_pr",
            risk_level=RiskLevelEnum.CRITICAL,
            requires_approval=True,
            required_role=ReviewerRoleEnum.RELEASE_MANAGER,
            allowed_environments=["development", "test", "staging"]
        ),
        "deployment.deploy_production": ToolApprovalPolicy(
            tool_name="deployment.deploy_production",
            risk_level=RiskLevelEnum.CRITICAL,
            requires_approval=True,
            required_role=ReviewerRoleEnum.RELEASE_MANAGER,
            allowed_environments=["staging", "production"]
        ),
        "deployment.deploy_staging": ToolApprovalPolicy(
            tool_name="deployment.deploy_staging",
            risk_level=RiskLevelEnum.HIGH,
            requires_approval=False,
            required_role=ReviewerRoleEnum.DEVELOPER,
            allowed_environments=["development", "test", "staging"]
        ),
        "deployment.rollback": ToolApprovalPolicy(
            tool_name="deployment.rollback",
            risk_level=RiskLevelEnum.HIGH,
            requires_approval=True,
            required_role=ReviewerRoleEnum.RELEASE_MANAGER,
            allowed_environments=["staging", "production"]
        ),
        "database.migrate": ToolApprovalPolicy(
            tool_name="database.migrate",
            risk_level=RiskLevelEnum.HIGH,
            requires_approval=True,
            required_role=ReviewerRoleEnum.TECH_LEAD,
            allowed_environments=["development", "test", "staging", "production"]
        ),
        "terminal.execute_command": ToolApprovalPolicy(
            tool_name="terminal.execute_command",
            risk_level=RiskLevelEnum.HIGH,
            requires_approval=False,
            required_role=ReviewerRoleEnum.DEVELOPER,
            allowed_environments=["development", "test"]
        )
    }

    @classmethod
    def evaluate_tool(cls, tool_name: str, environment: str = "development") -> Tuple[bool, RiskLevelEnum, ReviewerRoleEnum]:
        """
        Evaluate if tool requires human approval in the given environment.
        Returns: (requires_approval, risk_level, required_role)
        """
        policy = cls.POLICIES.get(tool_name)
        if not policy:
            # Default for low-risk standard tools
            return False, RiskLevelEnum.LOW, ReviewerRoleEnum.DEVELOPER
        
        # In production environment, high/critical tools strictly require approval
        if environment == "production":
            return True, policy.risk_level, policy.required_role
        
        return policy.requires_approval, policy.risk_level, policy.required_role

tool_approval_manager = ToolApprovalPolicyManager()
