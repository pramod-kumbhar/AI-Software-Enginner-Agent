import os
import re
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import logger
from app.core.security import SecretMasker

class GitHubActionsToolHandlers:
    """
    GitHub Actions REST API v3 tool handlers.
    Provides workflow run monitoring, job extraction, log sanitization, and workflow dispatching.
    Includes rate-limit awareness and offline deterministic mock support.
    """

    @staticmethod
    def _get_headers(token: Optional[str] = None) -> Dict[str, str]:
        auth_token = token or settings.GITHUB_TOKEN or os.getenv("GITHUB_TOKEN")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AI-Software-Engineer-Agent"
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    @classmethod
    def _parse_repo(cls, repository: Optional[str] = None) -> tuple[str, str]:
        repo_str = repository or f"{settings.GITHUB_OWNER or 'pramod-kumbhar'}/{settings.GITHUB_REPOSITORY or 'ai-software-engineer-agent'}"
        parts = repo_str.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]
        return "pramod-kumbhar", "ai-software-engineer-agent"

    @classmethod
    async def get_ci_status(
        cls,
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        pull_request_number: Optional[int] = None,
        workflow_run_id: Optional[int] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves CI workflow run status, conclusion, jobs summary, and HTML URL.
        """
        owner, repo = cls._parse_repo(repository)
        headers = cls._get_headers(token)

        # 1. Offline Mock fallback if token is not available or in test mode
        if settings.is_test or not headers.get("Authorization"):
            run_id = workflow_run_id or 100201
            return {
                "status": "completed",
                "conclusion": "failure",
                "workflow_run_id": run_id,
                "workflow_name": "CI",
                "branch": branch or "main",
                "commit_sha": "mock_sha_ci_fail_01",
                "html_url": f"https://github.com/{owner}/{repo}/actions/runs/{run_id}",
                "total_jobs": 2,
                "completed_jobs": 2,
                "failed_jobs": 1,
                "jobs": [
                    {
                        "job_id": 2001,
                        "job_name": "lint-and-format",
                        "status": "completed",
                        "conclusion": "success",
                        "failed_steps": []
                    },
                    {
                        "job_id": 2002,
                        "job_name": "pytest-suite",
                        "status": "completed",
                        "conclusion": "failure",
                        "failed_steps": ["Run pytest unit & integration tests"]
                    }
                ],
                "is_mock": True
            }

        # 2. Live GitHub Actions REST API
        async with httpx.AsyncClient(timeout=15.0) as client:
            if workflow_run_id:
                url = f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/actions/runs/{workflow_run_id}"
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    raise RuntimeError(f"GitHub API Error [{resp.status_code}]: {resp.text}")
                run_data = resp.json()
            else:
                url = f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/actions/runs"
                params = {"per_page": 5}
                if branch:
                    params["branch"] = branch
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code != 200:
                    raise RuntimeError(f"GitHub API Error [{resp.status_code}]: {resp.text}")
                runs = resp.json().get("workflow_runs", [])
                if not runs:
                    return {
                        "status": "queued",
                        "conclusion": None,
                        "workflow_run_id": 0,
                        "branch": branch or "main",
                        "total_jobs": 0,
                        "failed_jobs": 0,
                        "jobs": []
                    }
                run_data = runs[0]

            run_id = run_data.get("id")
            # Fetch jobs for this run
            jobs_url = f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/actions/runs/{run_id}/jobs"
            jobs_resp = await client.get(jobs_url, headers=headers)
            jobs_data = jobs_resp.json().get("jobs", []) if jobs_resp.status_code == 200 else []

            jobs_summary = []
            failed_jobs_count = 0
            for j in jobs_data:
                failed_steps = [s.get("name") for s in j.get("steps", []) if s.get("conclusion") == "failure"]
                if j.get("conclusion") == "failure":
                    failed_jobs_count += 1
                jobs_summary.append({
                    "job_id": j.get("id"),
                    "job_name": j.get("name"),
                    "status": j.get("status"),
                    "conclusion": j.get("conclusion"),
                    "failed_steps": failed_steps
                })

            return {
                "status": run_data.get("status"),
                "conclusion": run_data.get("conclusion"),
                "workflow_run_id": run_id,
                "workflow_name": run_data.get("name", "CI"),
                "branch": run_data.get("head_branch"),
                "commit_sha": run_data.get("head_sha"),
                "html_url": run_data.get("html_url"),
                "total_jobs": len(jobs_summary),
                "completed_jobs": sum(1 for j in jobs_summary if j["status"] == "completed"),
                "failed_jobs": failed_jobs_count,
                "jobs": jobs_summary,
                "is_mock": False
            }

    @classmethod
    async def get_failed_jobs(
        cls,
        workflow_run_id: int,
        repository: Optional[str] = None,
        token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts only the failed jobs and failing step names from a workflow run.
        """
        owner, repo = cls._parse_repo(repository)
        headers = cls._get_headers(token)

        if settings.is_test or not headers.get("Authorization"):
            return [{
                "job_id": 2002,
                "job_name": "pytest-suite",
                "status": "completed",
                "conclusion": "failure",
                "failed_steps": ["Run pytest unit & integration tests"],
                "html_url": f"https://github.com/{owner}/{repo}/actions/runs/{workflow_run_id}/job/2002"
            }]

        async with httpx.AsyncClient(timeout=15.0) as client:
            jobs_url = f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/actions/runs/{workflow_run_id}/jobs"
            resp = await client.get(jobs_url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to fetch jobs for run {workflow_run_id} [{resp.status_code}]: {resp.text}")
            
            jobs = resp.json().get("jobs", [])
            failed_jobs = []
            for j in jobs:
                if j.get("conclusion") == "failure":
                    failed_steps = [s.get("name") for s in j.get("steps", []) if s.get("conclusion") == "failure"]
                    failed_jobs.append({
                        "job_id": j.get("id"),
                        "job_name": j.get("name"),
                        "status": j.get("status"),
                        "conclusion": j.get("conclusion"),
                        "failed_steps": failed_steps,
                        "html_url": j.get("html_url")
                    })
            return failed_jobs

    @classmethod
    async def get_failure_logs(
        cls,
        workflow_run_id: int,
        job_id: int,
        repository: Optional[str] = None,
        max_chars: int = 20000,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves logs for a failed job, masks any secrets, and bounds the output length to max_chars.
        """
        owner, repo = cls._parse_repo(repository)
        headers = cls._get_headers(token)

        if settings.is_test or not headers.get("Authorization"):
            # Mock failure log excerpt
            mock_raw_log = """2026-08-11T06:30:12.124Z [INFO] Setting up Python 3.11 environment
2026-08-11T06:30:15.845Z [INFO] Installing requirements: fastapi pytest httpx
2026-08-11T06:30:20.112Z [INFO] Running pytest test suite...
============================= test session starts ==============================
rootdir: /home/runner/work/ai-agent/workspace
collected 4 items

tests/test_tasks.py::test_create_task PASSED [ 25%]
tests/test_tasks.py::test_get_task PASSED    [ 50%]
tests/test_tasks.py::test_update_task FAILED [ 75%]
tests/test_tasks.py::test_delete_task PASSED [100%]

=================================== FAILURES ===================================
_______________________________ test_update_task _______________________________

    def test_update_task(client):
>       response = client.put("/api/v1/tasks/task_123", json={"title": "Updated", "status": "COMPLETED"})
E       ImportError: cannot import name 'TaskUpdateSchema' from 'app.modules.tasks.schemas' (/home/runner/work/app/modules/tasks/schemas.py)

tests/test_tasks.py:42: ImportError
=========================== short test summary info ============================
FAILED tests/test_tasks.py::test_update_task - ImportError: cannot import name 'TaskUpdateSchema' from 'app.modules.tasks.schemas'
========================= 1 failed, 3 passed in 1.45s ==========================
Error: Process completed with exit code 1.
"""
            sanitized = SecretMasker.mask_text(mock_raw_log)[:max_chars]
            return {
                "workflow_run_id": workflow_run_id,
                "job_id": job_id,
                "sanitized_log_excerpt": sanitized,
                "total_chars": len(sanitized),
                "is_truncated": len(mock_raw_log) > max_chars,
                "is_mock": True
            }

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            url = f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                raw_text = resp.text
                sanitized = SecretMasker.mask_text(raw_text)
                if len(sanitized) > max_chars:
                    # Keep the last max_chars where failure output typically resides
                    sanitized = "... [TRUNCATED EARLY LOGS] ...\n" + sanitized[-max_chars:]
                return {
                    "workflow_run_id": workflow_run_id,
                    "job_id": job_id,
                    "sanitized_log_excerpt": sanitized,
                    "total_chars": len(sanitized),
                    "is_truncated": len(resp.text) > max_chars,
                    "is_mock": False
                }
            else:
                return {
                    "workflow_run_id": workflow_run_id,
                    "job_id": job_id,
                    "sanitized_log_excerpt": f"[Log retrieval failed with status {resp.status_code}]",
                    "total_chars": 0,
                    "is_truncated": False,
                    "is_mock": False
                }

    @classmethod
    async def trigger_ci(
        cls,
        workflow_id_or_name: str = "ci.yml",
        repository: Optional[str] = None,
        branch: str = "main",
        inputs: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Triggers a workflow dispatch event on GitHub Actions.
        """
        owner, repo = cls._parse_repo(repository)
        headers = cls._get_headers(token)

        if settings.is_test or not headers.get("Authorization"):
            return {
                "triggered": True,
                "workflow": workflow_id_or_name,
                "repository": f"{owner}/{repo}",
                "branch": branch,
                "workflow_run_id": 100202,
                "is_mock": True,
                "message": f"Dispatched mock CI workflow '{workflow_id_or_name}' on branch '{branch}'"
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            url = f"{settings.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/actions/workflows/{workflow_id_or_name}/dispatches"
            payload = {
                "ref": branch,
                "inputs": inputs or {}
            }
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (204, 201, 200):
                return {
                    "triggered": True,
                    "workflow": workflow_id_or_name,
                    "repository": f"{owner}/{repo}",
                    "branch": branch,
                    "status_code": resp.status_code,
                    "message": "Workflow dispatch triggered successfully"
                }
            else:
                raise RuntimeError(f"Failed to trigger CI dispatch [{resp.status_code}]: {resp.text}")
