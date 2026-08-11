import pytest
import asyncio
from app.tools.github.handlers import GitHubToolHandlers

def test_github_mock_operations():
    async def _run():
        # 1. Get repository metadata
        repo_data = await GitHubToolHandlers.get_repository(owner="pramod-kumbhar", repo="ai-software-engineer-agent")
        assert repo_data["owner"] == "pramod-kumbhar"
        assert repo_data["repository"] == "ai-software-engineer-agent"
        
        # 2. Get repository file
        file_data = await GitHubToolHandlers.get_repository_file(file_path="README.md", owner="pramod-kumbhar", repo="ai-software-engineer-agent")
        assert file_data["file_path"] == "README.md"
        assert "content" in file_data
        
        # 3. Create branch
        branch_data = await GitHubToolHandlers.create_branch("ai-agent/task-001", owner="pramod-kumbhar", repo="ai-software-engineer-agent")
        assert branch_data["branch_name"] == "ai-agent/task-001"
        assert branch_data["created"] is True
        
        # 4. Create Pull Request
        pr_data = await GitHubToolHandlers.create_pull_request(
            title="Implement Task Management Module",
            body="Autonomous PR created with verified Pytest suite.",
            head_branch="ai-agent/task-001",
            base_branch="main",
            owner="pramod-kumbhar",
            repo="ai-software-engineer-agent"
        )
        assert pr_data["pr_number"] > 0
        assert "html_url" in pr_data
        
        # 5. Comment on Pull Request
        comment_res = await GitHubToolHandlers.comment_on_pull_request(
            pull_number=pr_data["pr_number"],
            comment="Code generation completed with 100% test coverage.",
            owner="pramod-kumbhar",
            repo="ai-software-engineer-agent"
        )
        assert comment_res["posted"] is True

    asyncio.run(_run())
