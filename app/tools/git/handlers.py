import os
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

class GitToolHandlers:
    """
    Controlled Git tools executing bounded version control operations.
    Prevents unauthorized push, destructive branch deletions, or merge operations.
    """
    
    @staticmethod
    def _run_git_cmd(workspace_root: str, args: List[str], timeout: float = 10.0) -> subprocess.CompletedProcess:
        # Validate safe git arguments (allowlist approach)
        safe_subcommands = {"status", "diff", "log", "branch", "checkout", "add", "commit", "rev-parse", "init", "config"}
        if not args or args[0] not in safe_subcommands:
            raise ValueError(f"Git command '{args[0] if args else ''}' is prohibited by safety policy.")
            
        target_dir = Path(workspace_root).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure git repo is initialized if needed
        git_dir = target_dir / ".git"
        if not git_dir.exists() and args[0] != "init":
            subprocess.run(["git", "init"], cwd=str(target_dir), capture_output=True, text=True, timeout=5.0)
            subprocess.run(["git", "config", "user.name", "AI Software Engineer Agent"], cwd=str(target_dir), capture_output=True, text=True, timeout=5.0)
            subprocess.run(["git", "config", "user.email", "ai-agent@antigravity.internal"], cwd=str(target_dir), capture_output=True, text=True, timeout=5.0)
            
        full_cmd = ["git"] + args
        return subprocess.run(
            full_cmd,
            cwd=str(target_dir),
            capture_output=True,
            text=True,
            timeout=timeout
        )

    @classmethod
    def git_status(cls, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        root = workspace_root or "generated_projects/default"
        proc = cls._run_git_cmd(root, ["status", "--porcelain"])
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        
        modified = []
        untracked = []
        staged = []
        
        for line in lines:
            status_code = line[:2]
            file_name = line[3:]
            if status_code.startswith("??"):
                untracked.append(file_name)
            elif status_code.startswith("M ") or status_code.startswith("A "):
                staged.append(file_name)
            else:
                modified.append(file_name)
                
        return {
            "workspace_root": root,
            "is_clean": len(lines) == 0,
            "modified_files": modified,
            "untracked_files": untracked,
            "staged_files": staged,
            "raw_status": proc.stdout
        }

    @classmethod
    def git_diff(cls, workspace_root: Optional[str] = None, staged_only: bool = False) -> Dict[str, Any]:
        root = workspace_root or "generated_projects/default"
        args = ["diff", "--cached"] if staged_only else ["diff"]
        proc = cls._run_git_cmd(root, args)
        return {
            "workspace_root": root,
            "staged_only": staged_only,
            "diff": proc.stdout,
            "has_changes": len(proc.stdout.strip()) > 0
        }

    @classmethod
    def git_create_branch(cls, branch_name: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        root = workspace_root or "generated_projects/default"
        # Sanitize branch name
        safe_branch = re.sub(r'[^a-zA-Z0-9_\-\/]+', '-', branch_name).strip('-')
        proc = cls._run_git_cmd(root, ["checkout", "-b", safe_branch])
        if proc.returncode != 0 and "already exists" in proc.stderr:
            # Switch to existing
            proc = cls._run_git_cmd(root, ["checkout", safe_branch])
            
        return {
            "workspace_root": root,
            "branch_name": safe_branch,
            "created": proc.returncode == 0,
            "output": proc.stdout + proc.stderr
        }

    @classmethod
    def git_checkout_branch(cls, branch_name: str, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        root = workspace_root or "generated_projects/default"
        proc = cls._run_git_cmd(root, ["checkout", branch_name])
        return {
            "workspace_root": root,
            "branch_name": branch_name,
            "success": proc.returncode == 0,
            "output": proc.stdout + proc.stderr
        }

    @classmethod
    def git_current_branch(cls, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        root = workspace_root or "generated_projects/default"
        proc = cls._run_git_cmd(root, ["rev-parse", "--abbrev-ref", "HEAD"])
        branch = proc.stdout.strip() if proc.returncode == 0 else "main"
        return {"workspace_root": root, "current_branch": branch}

    @classmethod
    def git_stage_files(cls, file_paths: List[str], workspace_root: Optional[str] = None) -> Dict[str, Any]:
        root = workspace_root or "generated_projects/default"
        if not file_paths:
            file_paths = ["."]
        proc = cls._run_git_cmd(root, ["add"] + file_paths)
        return {
            "workspace_root": root,
            "staged_files": file_paths,
            "success": proc.returncode == 0
        }

    @classmethod
    def git_commit(cls, message: str, workspace_root: Optional[str] = None, author: Optional[str] = None) -> Dict[str, Any]:
        root = workspace_root or "generated_projects/default"
        # First ensure staged files exist, or stage all
        cls._run_git_cmd(root, ["add", "."])
        
        args = ["commit", "-m", message]
        if author:
            args.extend(["--author", author])
            
        proc = cls._run_git_cmd(root, args)
        
        # Get commit hash
        hash_proc = cls._run_git_cmd(root, ["rev-parse", "HEAD"])
        commit_hash = hash_proc.stdout.strip() if hash_proc.returncode == 0 else "unknown"
        
        return {
            "workspace_root": root,
            "message": message,
            "commit_hash": commit_hash,
            "success": proc.returncode == 0 or "nothing to commit" in proc.stdout,
            "output": proc.stdout + proc.stderr
        }

    @classmethod
    def git_log(cls, workspace_root: Optional[str] = None, max_commits: int = 10) -> Dict[str, Any]:
        root = workspace_root or "generated_projects/default"
        proc = cls._run_git_cmd(root, ["log", f"-n{max_commits}", "--oneline"])
        commits = [c.strip() for c in proc.stdout.splitlines() if c.strip()]
        return {
            "workspace_root": root,
            "total_commits": len(commits),
            "commits": commits
        }

    @classmethod
    def get_diff(cls, workspace_root: Optional[str] = None, staged_only: bool = False) -> Dict[str, Any]:
        """Alias for git_diff."""
        return cls.git_diff(workspace_root=workspace_root, staged_only=staged_only)

    @classmethod
    def get_changed_files(cls, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        """Returns list of modified, untracked, and staged files in the workspace."""
        status = cls.git_status(workspace_root=workspace_root)
        all_changed = list(set(status["modified_files"] + status["untracked_files"] + status["staged_files"]))
        return {
            "workspace_root": status["workspace_root"],
            "changed_files": all_changed,
            "total_changed": len(all_changed),
            "is_clean": status["is_clean"]
        }

