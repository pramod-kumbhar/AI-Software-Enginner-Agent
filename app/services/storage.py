import json
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

class StorageService:
    """
    Thread-safe unified storage service for Plans, Architectures, Developer Implementation runs,
    Tool executions, Human approvals, Audit logs, and GitHub integrations.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StorageService, cls).__new__(cls)
                cls._instance._plans: Dict[str, Any] = {}
                cls._instance._architectures: Dict[str, Any] = {}
                cls._instance._developer_runs: Dict[str, Any] = {}
                cls._instance._tool_requests: Dict[str, Any] = {}
                cls._instance._tool_audit_logs: List[Dict[str, Any]] = []
                cls._instance._github_integrations: Dict[str, Any] = {}
                cls._instance._ci_runs: Dict[str, Any] = {}
                cls._instance._ci_failures: Dict[str, Any] = {}
                cls._instance._repair_plans: Dict[str, Any] = {}
                cls._instance._repair_attempts: Dict[str, List[Any]] = {}
                cls._instance._repair_results: Dict[str, Any] = {}
                cls._instance._ci_events: List[Dict[str, Any]] = []
                cls._instance._failure_fingerprints: Dict[str, str] = {}
                # Day 12 Release & Deployment Storage
                cls._instance._releases: Dict[str, Any] = {}
                cls._instance._release_validations: Dict[str, Any] = {}
                cls._instance._deployment_runs: Dict[str, Any] = {}
                cls._instance._rollback_events: Dict[str, Any] = {}
                cls._instance._deployment_audit_logs: List[Dict[str, Any]] = []
            return cls._instance

    # 1. Planner Storage
    def save_plan(self, task_id: str, plan_data: Any) -> None:
        with self._lock:
            self._plans[task_id] = {
                "task_id": task_id,
                "data": plan_data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

    def get_plan(self, task_id: str) -> Optional[Any]:
        with self._lock:
            entry = self._plans.get(task_id)
            return entry.get("data") if entry else None

    # 2. Architect Storage
    def save_architecture(self, task_id: str, arch_data: Any) -> None:
        with self._lock:
            self._architectures[task_id] = {
                "task_id": task_id,
                "data": arch_data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

    def get_architecture(self, task_id: str) -> Optional[Any]:
        with self._lock:
            entry = self._architectures.get(task_id)
            return entry.get("data") if entry else None

    def update_architecture_approval(self, task_id: str, status: str, reviewer: str, notes: Optional[str] = None) -> bool:
        with self._lock:
            if task_id not in self._architectures:
                return False
            arch = self._architectures[task_id]["data"]
            if hasattr(arch, "human_approval") and arch.human_approval:
                arch.human_approval.status = status
                arch.human_approval.approved_by = reviewer
                arch.human_approval.comments = notes
                arch.human_approval.timestamp = datetime.now(timezone.utc).isoformat()
            self._architectures[task_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            return True

    # 3. Developer Storage
    def save_developer_run(self, task_id: str, dev_data: Any) -> None:
        with self._lock:
            self._developer_runs[task_id] = {
                "task_id": task_id,
                "data": dev_data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

    def get_developer_run(self, task_id: str) -> Optional[Any]:
        with self._lock:
            entry = self._developer_runs.get(task_id)
            return entry.get("data") if entry else None

    def update_developer_approval(self, task_id: str, status: str, reviewer: str, notes: Optional[str] = None) -> bool:
        with self._lock:
            if task_id not in self._developer_runs:
                return False
            dev = self._developer_runs[task_id]["data"]
            if hasattr(dev, "human_approval") and dev.human_approval:
                dev.human_approval.status = status
                dev.human_approval.approved_by = reviewer
                dev.human_approval.comments = notes
                dev.human_approval.timestamp = datetime.now(timezone.utc).isoformat()
            self._developer_runs[task_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            return True

    # 4. Tool Requests & Executions Storage
    def save_tool_request(self, request_id: str, request_data: Any) -> None:
        with self._lock:
            self._tool_requests[request_id] = {
                "request_id": request_id,
                "data": request_data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

    def get_tool_request(self, request_id: str) -> Optional[Any]:
        with self._lock:
            entry = self._tool_requests.get(request_id)
            return entry.get("data") if entry else None

    def list_tool_requests(self) -> List[Any]:
        with self._lock:
            return [entry["data"] for entry in self._tool_requests.values()]

    # 5. Audit Logging Storage
    def append_audit_log(self, log_record: Dict[str, Any]) -> None:
        with self._lock:
            self._tool_audit_logs.append(log_record)

    def get_audit_logs(self, project_id: Optional[str] = None, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            logs = self._tool_audit_logs
            if request_id:
                logs = [l for l in logs if l.get("request_id") == request_id]
            if project_id:
                logs = [l for l in logs if l.get("project_id") == project_id]
            return list(logs)

    # 6. GitHub Integration Storage
    def save_github_pr(self, pr_id: str, pr_data: Dict[str, Any]) -> None:
        with self._lock:
            self._github_integrations[pr_id] = {
                "pr_id": pr_id,
                "data": pr_data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

    def get_github_pr(self, pr_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._github_integrations.get(pr_id)
            return entry.get("data") if entry else None

    def list_github_prs(self, repo: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            prs = [entry["data"] for entry in self._github_integrations.values()]
            if repo:
                prs = [p for p in prs if p.get("repository") == repo]
            return prs

    # 7. Day 11 CI/CD & Autonomous Repair Storage
    def save_ci_run(self, run_id: str, run_data: Any) -> None:
        with self._lock:
            self._ci_runs[run_id] = {
                "run_id": run_id,
                "data": run_data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

    def get_ci_run(self, run_id: str) -> Optional[Any]:
        with self._lock:
            entry = self._ci_runs.get(run_id)
            return entry.get("data") if entry else None

    def list_ci_runs(self) -> List[Any]:
        with self._lock:
            return [e["data"] for e in self._ci_runs.values()]

    def save_ci_failure(self, failure_id: str, failure_data: Any) -> None:
        with self._lock:
            self._ci_failures[failure_id] = failure_data

    def get_ci_failure(self, failure_id: str) -> Optional[Any]:
        with self._lock:
            return self._ci_failures.get(failure_id)

    def save_repair_plan(self, repair_id: str, plan_data: Any) -> None:
        with self._lock:
            self._repair_plans[repair_id] = plan_data

    def get_repair_plan(self, repair_id: str) -> Optional[Any]:
        with self._lock:
            return self._repair_plans.get(repair_id)

    def append_repair_attempt(self, repair_id: str, attempt_data: Any) -> None:
        with self._lock:
            if repair_id not in self._repair_attempts:
                self._repair_attempts[repair_id] = []
            self._repair_attempts[repair_id].append(attempt_data)

    def get_repair_attempts(self, repair_id: str) -> List[Any]:
        with self._lock:
            return list(self._repair_attempts.get(repair_id, []))

    def save_repair_result(self, repair_id: str, result_data: Any) -> None:
        with self._lock:
            self._repair_results[repair_id] = result_data

    def get_repair_result(self, repair_id: str) -> Optional[Any]:
        with self._lock:
            return self._repair_results.get(repair_id)

    def record_ci_event(self, event: Dict[str, Any]) -> None:
        with self._lock:
            event["timestamp"] = datetime.now(timezone.utc).isoformat()
            self._ci_events.append(event)

    def get_ci_events(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            if run_id:
                return [e for e in self._ci_events if e.get("run_id") == run_id]
            return list(self._ci_events)

    def check_or_register_fingerprint(self, fingerprint: str, repair_id: str) -> Optional[str]:
        """
        Idempotency check: Returns existing repair_id if fingerprint exists, else registers it and returns None.
        """
        with self._lock:
            if fingerprint in self._failure_fingerprints:
                return self._failure_fingerprints[fingerprint]
            self._failure_fingerprints[fingerprint] = repair_id
            return None

    # 8. Day 12 Release Governance & Deployment Storage
    def save_release(self, release_id: str, release_data: Any) -> None:
        with self._lock:
            data = release_data.model_dump() if hasattr(release_data, "model_dump") else release_data
            self._releases[release_id] = data

    def get_release(self, release_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._releases.get(release_id)

    def list_releases(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            releases = list(self._releases.values())
            if project_id:
                releases = [r for r in releases if r.get("project_id") == project_id]
            return releases

    def save_release_validation(self, release_id: str, validation_data: Any) -> None:
        with self._lock:
            data = validation_data.model_dump() if hasattr(validation_data, "model_dump") else validation_data
            self._release_validations[release_id] = data

    def get_release_validation(self, release_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._release_validations.get(release_id)

    def save_deployment_run(self, deployment_id: str, run_data: Any) -> None:
        with self._lock:
            data = run_data.model_dump() if hasattr(run_data, "model_dump") else run_data
            self._deployment_runs[deployment_id] = data

    def get_deployment_run(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._deployment_runs.get(deployment_id)

    def list_deployment_runs(self, release_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            runs = list(self._deployment_runs.values())
            if release_id:
                runs = [r for r in runs if r.get("release_id") == release_id]
            return runs

    def save_rollback_event(self, event: Any) -> None:
        with self._lock:
            data = event.model_dump() if hasattr(event, "model_dump") else event
            rb_id = data.get("rollback_id", f"rb_{len(self._rollback_events)}")
            self._rollback_events[rb_id] = data

    def list_rollback_events(self, release_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            events = list(self._rollback_events.values())
            if release_id:
                events = [e for e in events if e.get("release_id") == release_id]
            return events

    # 6. Generic & Security Metadata Storage
    def save_metadata(self, key: str, data: Any) -> None:
        with self._lock:
            if not hasattr(self, "_generic_metadata"):
                self._generic_metadata: Dict[str, Any] = {}
            val = data.model_dump() if hasattr(data, "model_dump") else data
            self._generic_metadata[key] = val

    def get_metadata(self, key: str) -> Optional[Any]:
        with self._lock:
            if not hasattr(self, "_generic_metadata"):
                self._generic_metadata: Dict[str, Any] = {}
            return self._generic_metadata.get(key)

storage_service = StorageService()


