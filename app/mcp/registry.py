from typing import Dict, Any, List, Optional, Callable
from app.mcp.schemas import (
    ToolDefinition,
    ToolCategoryEnum,
    RiskLevelEnum
)
from app.tools.filesystem.handlers import FilesystemToolHandlers
from app.tools.testing.handlers import TestingToolHandlers
from app.tools.git.handlers import GitToolHandlers
from app.tools.github.handlers import GitHubToolHandlers
from app.tools.github.actions_handlers import GitHubActionsToolHandlers
from app.tools.deployment.handlers import DeploymentToolHandlers

class ToolRegistry:
    """
    Central repository of registered tools with metadata, schemas, risk levels, and dispatch targets.
    """
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
        self._register_default_tools()

    def register_tool(self, tool_def: ToolDefinition, handler: Callable) -> None:
        self._tools[tool_def.name] = tool_def
        self._handlers[tool_def.name] = handler

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def get_handler(self, name: str) -> Optional[Callable]:
        return self._handlers.get(name)

    def list_tools(self, role: Optional[str] = None, category: Optional[ToolCategoryEnum] = None) -> List[ToolDefinition]:
        tools = list(self._tools.values())
        if role and role != "ADMIN":
            tools = [t for t in tools if role in t.allowed_roles or "ALL" in t.allowed_roles]
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def _register_default_tools(self):
        # 1. Filesystem Tools
        self.register_tool(
            ToolDefinition(
                name="filesystem.list_files",
                description="List files in a relative directory within the sandboxed project workspace.",
                category=ToolCategoryEnum.FILESYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["PLANNER", "ARCHITECT", "DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {"directory": {"type": "string"}}}
            ),
            FilesystemToolHandlers.list_files
        )
        self.register_tool(
            ToolDefinition(
                name="filesystem.read_file",
                description="Read contents of a file inside the sandboxed workspace.",
                category=ToolCategoryEnum.FILESYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["PLANNER", "ARCHITECT", "DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["file_path"], "properties": {"file_path": {"type": "string"}}}
            ),
            FilesystemToolHandlers.read_file
        )
        self.register_tool(
            ToolDefinition(
                name="filesystem.file_exists",
                description="Check if a file exists in the workspace.",
                category=ToolCategoryEnum.FILESYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["file_path"], "properties": {"file_path": {"type": "string"}}}
            ),
            FilesystemToolHandlers.file_exists
        )
        self.register_tool(
            ToolDefinition(
                name="filesystem.create_file",
                description="Create a new file in the sandboxed workspace.",
                category=ToolCategoryEnum.FILESYSTEM,
                risk_level=RiskLevelEnum.LOW_RISK,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "required": ["file_path", "content"], "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}, "overwrite": {"type": "boolean"}}}
            ),
            FilesystemToolHandlers.create_file
        )
        self.register_tool(
            ToolDefinition(
                name="filesystem.modify_file",
                description="Modify existing file contents in the workspace.",
                category=ToolCategoryEnum.FILESYSTEM,
                risk_level=RiskLevelEnum.MEDIUM_RISK,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "required": ["file_path", "content"], "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}}}
            ),
            FilesystemToolHandlers.modify_file
        )
        self.register_tool(
            ToolDefinition(
                name="filesystem.create_directory",
                description="Create a sub-directory in the sandboxed workspace.",
                category=ToolCategoryEnum.FILESYSTEM,
                risk_level=RiskLevelEnum.LOW_RISK,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "required": ["directory"], "properties": {"directory": {"type": "string"}}}
            ),
            FilesystemToolHandlers.create_directory
        )
        self.register_tool(
            ToolDefinition(
                name="filesystem.get_file_metadata",
                description="Retrieve file size, directory status, and modification timestamp.",
                category=ToolCategoryEnum.FILESYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["file_path"], "properties": {"file_path": {"type": "string"}}}
            ),
            FilesystemToolHandlers.get_file_metadata
        )

        # 2. Testing Tools
        self.register_tool(
            ToolDefinition(
                name="testing.run_tests",
                description="Execute automated pytest suite inside the sandboxed workspace.",
                category=ToolCategoryEnum.TESTING,
                risk_level=RiskLevelEnum.LOW_RISK,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {"test_filter": {"type": "string"}, "timeout_seconds": {"type": "number"}}}
            ),
            TestingToolHandlers.run_tests
        )
        self.register_tool(
            ToolDefinition(
                name="testing.run_single_test",
                description="Execute a specific pytest file or test method.",
                category=ToolCategoryEnum.TESTING,
                risk_level=RiskLevelEnum.LOW_RISK,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["test_path"], "properties": {"test_path": {"type": "string"}}}
            ),
            TestingToolHandlers.run_single_test
        )
        self.register_tool(
            ToolDefinition(
                name="testing.get_test_summary",
                description="Retrieve high-level test pass/fail metrics and execution rate.",
                category=ToolCategoryEnum.TESTING,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object"}
            ),
            TestingToolHandlers.get_test_summary
        )

        # 3. Git Tools
        self.register_tool(
            ToolDefinition(
                name="git.status",
                description="Inspect local git working directory changes and untracked files.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object"}
            ),
            GitToolHandlers.git_status
        )
        self.register_tool(
            ToolDefinition(
                name="git.diff",
                description="Retrieve unified diff of unstaged or staged repository changes.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {"staged_only": {"type": "boolean"}}}
            ),
            GitToolHandlers.git_diff
        )
        self.register_tool(
            ToolDefinition(
                name="git.log",
                description="Retrieve recent git commit history.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {"max_commits": {"type": "integer"}}}
            ),
            GitToolHandlers.git_log
        )
        self.register_tool(
            ToolDefinition(
                name="git.create_branch",
                description="Create a dedicated feature branch for the task.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.MEDIUM_RISK,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "required": ["branch_name"], "properties": {"branch_name": {"type": "string"}}}
            ),
            GitToolHandlers.git_create_branch
        )
        self.register_tool(
            ToolDefinition(
                name="git.checkout_branch",
                description="Switch to an existing local git branch.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.LOW_RISK,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "required": ["branch_name"], "properties": {"branch_name": {"type": "string"}}}
            ),
            GitToolHandlers.git_checkout_branch
        )
        self.register_tool(
            ToolDefinition(
                name="git.current_branch",
                description="Get current active git branch name.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object"}
            ),
            GitToolHandlers.git_current_branch
        )
        self.register_tool(
            ToolDefinition(
                name="git.stage_files",
                description="Stage specified files for commit.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.LOW_RISK,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "properties": {"file_paths": {"type": "array", "items": {"type": "string"}}}}
            ),
            GitToolHandlers.git_stage_files
        )
        self.register_tool(
            ToolDefinition(
                name="git.commit",
                description="Commit staged changes with a descriptive message.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.MEDIUM_RISK,
                requires_approval=True,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "required": ["message"], "properties": {"message": {"type": "string"}, "author": {"type": "string"}}}
            ),
            GitToolHandlers.git_commit
        )

        self.register_tool(
            ToolDefinition(
                name="git.get_diff",
                description="Get current git diff for modified or staged files.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {"staged_only": {"type": "boolean"}}}
            ),
            GitToolHandlers.get_diff
        )
        self.register_tool(
            ToolDefinition(
                name="git.get_changed_files",
                description="Get list of modified, staged, and untracked files.",
                category=ToolCategoryEnum.GIT,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {}}
            ),
            GitToolHandlers.get_changed_files
        )

        # Testing Targeted & Regression Tools
        self.register_tool(
            ToolDefinition(
                name="testing.run_failed_tests",
                description="Run only the specified failing test paths.",
                category=ToolCategoryEnum.TESTING,
                risk_level=RiskLevelEnum.LOW_RISK,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["failed_test_paths"], "properties": {"failed_test_paths": {"type": "array", "items": {"type": "string"}}, "timeout_seconds": {"type": "number"}}}
            ),
            TestingToolHandlers.run_failed_tests
        )
        self.register_tool(
            ToolDefinition(
                name="testing.run_regression_tests",
                description="Execute full regression test suite across the workspace.",
                category=ToolCategoryEnum.TESTING,
                risk_level=RiskLevelEnum.LOW_RISK,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {"timeout_seconds": {"type": "number"}}}
            ),
            TestingToolHandlers.run_regression_tests
        )

        # 4. GitHub & CI/CD Actions Tools
        self.register_tool(
            ToolDefinition(
                name="github.get_repository",
                description="Fetch repository metadata from GitHub REST API.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["PLANNER", "ARCHITECT", "DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}}}
            ),
            GitHubToolHandlers.get_repository
        )
        self.register_tool(
            ToolDefinition(
                name="github.get_file",
                description="Retrieve file content from a GitHub repository via REST API.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["file_path"], "properties": {"file_path": {"type": "string"}, "owner": {"type": "string"}, "repo": {"type": "string"}, "ref": {"type": "string"}}}
            ),
            GitHubToolHandlers.get_repository_file
        )
        self.register_tool(
            ToolDefinition(
                name="github.create_branch",
                description="Create a remote branch on GitHub.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.MEDIUM_RISK,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "required": ["branch_name"], "properties": {"branch_name": {"type": "string"}, "owner": {"type": "string"}, "repo": {"type": "string"}, "source_branch": {"type": "string"}}}
            ),
            GitHubToolHandlers.create_branch
        )
        self.register_tool(
            ToolDefinition(
                name="github.create_pull_request",
                description="Create a Pull Request on GitHub.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.HIGH_RISK,
                requires_approval=True,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "required": ["title", "body", "head_branch"], "properties": {"title": {"type": "string"}, "body": {"type": "string"}, "head_branch": {"type": "string"}, "base_branch": {"type": "string"}}}
            ),
            GitHubToolHandlers.create_pull_request
        )
        self.register_tool(
            ToolDefinition(
                name="github.get_pull_request",
                description="Fetch Pull Request details by number.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["pull_number"], "properties": {"pull_number": {"type": "integer"}}}
            ),
            GitHubToolHandlers.get_pull_request
        )
        self.register_tool(
            ToolDefinition(
                name="github.comment_pull_request",
                description="Post a review comment on a GitHub Pull Request.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.MEDIUM_RISK,
                requires_approval=True,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["pull_number", "comment"], "properties": {"pull_number": {"type": "integer"}, "comment": {"type": "string"}}}
            ),
            GitHubToolHandlers.comment_on_pull_request
        )
        self.register_tool(
            ToolDefinition(
                name="github.get_ci_status",
                description="Monitor CI/CD workflow status and jobs via GitHub Actions API.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {"repository": {"type": "string"}, "branch": {"type": "string"}, "pull_request_number": {"type": "integer"}, "workflow_run_id": {"type": "integer"}}}
            ),
            GitHubActionsToolHandlers.get_ci_status
        )
        self.register_tool(
            ToolDefinition(
                name="github.get_failed_jobs",
                description="Extract failed jobs and failing step names from GitHub Actions run.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["workflow_run_id"], "properties": {"workflow_run_id": {"type": "integer"}, "repository": {"type": "string"}}}
            ),
            GitHubActionsToolHandlers.get_failed_jobs
        )
        self.register_tool(
            ToolDefinition(
                name="github.get_failure_logs",
                description="Retrieve sanitized and bounded failure logs for a failed GitHub Actions job.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["workflow_run_id", "job_id"], "properties": {"workflow_run_id": {"type": "integer"}, "job_id": {"type": "integer"}, "repository": {"type": "string"}, "max_chars": {"type": "integer"}}}
            ),
            GitHubActionsToolHandlers.get_failure_logs
        )
        self.register_tool(
            ToolDefinition(
                name="github.trigger_ci",
                description="Trigger workflow dispatch event to re-run CI pipeline.",
                category=ToolCategoryEnum.GITHUB,
                risk_level=RiskLevelEnum.LOW_RISK,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "properties": {"workflow_id_or_name": {"type": "string"}, "repository": {"type": "string"}, "branch": {"type": "string"}, "inputs": {"type": "object"}}}
            ),
            GitHubActionsToolHandlers.trigger_ci
        )

        # 5. Day 12 Deployment, Release Governance & Observability Tools
        self.register_tool(
            ToolDefinition(
                name="deployment.get_status",
                description="Retrieve status and metrics of a deployment run.",
                category=ToolCategoryEnum.SYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN", "PLANNER"],
                input_schema={"type": "object", "required": ["deployment_id"], "properties": {"deployment_id": {"type": "string"}}}
            ),
            DeploymentToolHandlers.get_status
        )
        self.register_tool(
            ToolDefinition(
                name="deployment.deploy_staging",
                description="Trigger automated deployment to the staging environment.",
                category=ToolCategoryEnum.SYSTEM,
                risk_level=RiskLevelEnum.MEDIUM_RISK,
                allowed_roles=["DEVELOPER", "ADMIN"],
                input_schema={"type": "object", "required": ["release_id", "project_id", "commit_sha", "branch"], "properties": {"release_id": {"type": "string"}, "project_id": {"type": "string"}, "commit_sha": {"type": "string"}, "branch": {"type": "string"}, "version": {"type": "string"}, "qa_score": {"type": "number"}}}
            ),
            DeploymentToolHandlers.deploy_staging
        )
        self.register_tool(
            ToolDefinition(
                name="deployment.deploy_production",
                description="Trigger production deployment after strict human approval and staging validation.",
                category=ToolCategoryEnum.SYSTEM,
                risk_level=RiskLevelEnum.CRITICAL,
                requires_approval=True,
                allowed_roles=["ADMIN"],
                input_schema={"type": "object", "required": ["release_id", "project_id", "commit_sha", "branch", "approved_by"], "properties": {"release_id": {"type": "string"}, "project_id": {"type": "string"}, "commit_sha": {"type": "string"}, "branch": {"type": "string"}, "version": {"type": "string"}, "qa_score": {"type": "number"}, "approved_by": {"type": "string"}}}
            ),
            DeploymentToolHandlers.deploy_production
        )
        self.register_tool(
            ToolDefinition(
                name="deployment.health_check",
                description="Run live health and smoke probes on specified environment.",
                category=ToolCategoryEnum.SYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["DEVELOPER", "QA", "ADMIN", "PLANNER"],
                input_schema={"type": "object", "properties": {"environment": {"type": "string"}}}
            ),
            DeploymentToolHandlers.health_check
        )
        self.register_tool(
            ToolDefinition(
                name="deployment.rollback",
                description="Execute controlled autonomous rollback to previous verified known-good version.",
                category=ToolCategoryEnum.SYSTEM,
                risk_level=RiskLevelEnum.HIGH_RISK,
                requires_approval=False,
                allowed_roles=["DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["release_id", "failed_version"], "properties": {"release_id": {"type": "string"}, "failed_version": {"type": "string"}, "environment": {"type": "string"}, "target_version": {"type": "string"}, "reason": {"type": "string"}}}
            ),
            DeploymentToolHandlers.rollback
        )
        self.register_tool(
            ToolDefinition(
                name="release.get_readiness",
                description="Retrieve structured release readiness matrix, risk score, and policy blockers.",
                category=ToolCategoryEnum.SYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["PLANNER", "ARCHITECT", "DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "required": ["release_id"], "properties": {"release_id": {"type": "string"}}}
            ),
            DeploymentToolHandlers.get_readiness
        )
        self.register_tool(
            ToolDefinition(
                name="release.get_history",
                description="Retrieve historical deployment runs, releases, and rollback audit logs.",
                category=ToolCategoryEnum.SYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["PLANNER", "ARCHITECT", "DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {"project_id": {"type": "string"}}}
            ),
            DeploymentToolHandlers.get_history
        )
        self.register_tool(
            ToolDefinition(
                name="observability.get_metrics",
                description="Retrieve real-time metrics summary (request count, latency, rollbacks).",
                category=ToolCategoryEnum.SYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["PLANNER", "ARCHITECT", "DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {}}
            ),
            DeploymentToolHandlers.get_metrics
        )
        self.register_tool(
            ToolDefinition(
                name="observability.get_health",
                description="Probe live platform health, database, and cache readiness.",
                category=ToolCategoryEnum.SYSTEM,
                risk_level=RiskLevelEnum.READ_ONLY,
                allowed_roles=["PLANNER", "ARCHITECT", "DEVELOPER", "QA", "ADMIN"],
                input_schema={"type": "object", "properties": {}}
            ),
            DeploymentToolHandlers.get_health
        )

tool_registry = ToolRegistry()
