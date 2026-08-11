import tempfile
from pathlib import Path
from app.tools.git.handlers import GitToolHandlers

def test_git_tools_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file
        f = Path(tmpdir) / "README.md"
        f.write_text("# Test Project\n", encoding="utf-8")
        
        # Git status
        status = GitToolHandlers.git_status(workspace_root=tmpdir)
        assert "README.md" in status["untracked_files"] or "README.md" in status["modified_files"] or status["is_clean"] is False
        
        # Git branch creation
        branch_res = GitToolHandlers.git_create_branch("ai-agent/feature-01", workspace_root=tmpdir)
        assert branch_res["branch_name"] == "ai-agent/feature-01"
        
        # Git stage
        stage_res = GitToolHandlers.git_stage_files(["README.md"], workspace_root=tmpdir)
        assert stage_res["success"] is True
        
        # Git diff (staged)
        diff_res = GitToolHandlers.git_diff(workspace_root=tmpdir, staged_only=True)
        assert diff_res["has_changes"] is True
        
        # Git commit
        commit_res = GitToolHandlers.git_commit("Initial commit from AI agent", workspace_root=tmpdir)
        assert commit_res["success"] is True
        assert commit_res["commit_hash"] != "unknown"
        
        # Git log
        log_res = GitToolHandlers.git_log(workspace_root=tmpdir, max_commits=5)
        assert log_res["total_commits"] >= 1
