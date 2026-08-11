from typing import List, Dict, Set, Tuple
from collections import defaultdict, deque
from app.schemas.plan import AtomicTask, FunctionalReq

class PlanValidator:
    """
    Deterministic Python Validation Engine for Planner Agent.
    Executes Kahn's Algorithm for DAG cycle detection and audits structural completeness.
    """
    
    @staticmethod
    def validate_task_dag(tasks: List[AtomicTask]) -> Tuple[bool, List[str], List[str]]:
        """
        Validates the task DAG using Kahn's algorithm.
        Returns:
            - is_valid (bool): True if DAG is valid, acyclic, and has no orphan dependencies
            - errors (List[str]): List of identified errors
            - topological_order (List[str]): Topologically sorted list of task_ids
        """
        errors = []
        if not tasks:
            return False, ["Task list is empty."], []
            
        task_ids = {t.task_id for t in tasks}
        in_degree: Dict[str, int] = {t.task_id: 0 for t in tasks}
        adjacency_list: Dict[str, List[str]] = defaultdict(list)
        
        # 1. Build graph & Audit orphan upstream dependencies
        for task in tasks:
            if len(task.acceptance_criteria) < 2:
                errors.append(f"Task '{task.task_id}' must have at least 2 acceptance criteria (found {len(task.acceptance_criteria)}).")
                
            for parent_id in task.upstream_dependencies:
                if parent_id not in task_ids:
                    errors.append(f"Task '{task.task_id}' references non-existent upstream parent '{parent_id}'.")
                else:
                    adjacency_list[parent_id].append(task.task_id)
                    in_degree[task.task_id] += 1

        # 2. Kahn's Algorithm for Topological Sort & Cycle Detection
        queue = deque([task_id for task_id, deg in in_degree.items() if deg == 0])
        topological_order = []
        
        while queue:
            node = queue.popleft()
            topological_order.append(node)
            
            for neighbor in adjacency_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        # Cycle Check
        if len(topological_order) != len(tasks):
            cyclic_nodes = [task_id for task_id, deg in in_degree.items() if deg > 0]
            errors.append(f"Circular dependency detected in tasks: {', '.join(cyclic_nodes)}.")
            return False, errors, []
            
        is_valid = len(errors) == 0
        return is_valid, errors, topological_order

    @staticmethod
    def calculate_critical_path(tasks: List[AtomicTask], topological_order: List[str]) -> List[str]:
        """Calculates the critical path through the DAG based on estimated task hours."""
        task_map = {t.task_id: t for t in tasks}
        earliest_finish: Dict[str, float] = {}
        predecessors: Dict[str, str] = {}
        
        for task_id in topological_order:
            task = task_map.get(task_id)
            if not task:
                continue
            max_pred_finish = 0.0
            best_pred = None
            
            for parent_id in task.upstream_dependencies:
                if parent_id in earliest_finish and earliest_finish[parent_id] > max_pred_finish:
                    max_pred_finish = earliest_finish[parent_id]
                    best_pred = parent_id
                    
            earliest_finish[task_id] = max_pred_finish + task.estimated_hours
            if best_pred:
                predecessors[task_id] = best_pred

        if not earliest_finish:
            return []
            
        end_node = max(earliest_finish, key=earliest_finish.get)
        path = []
        curr = end_node
        while curr:
            path.append(curr)
            curr = predecessors.get(curr)
            
        path.reverse()
        return path

    @staticmethod
    def audit_coverage(tasks: List[AtomicTask], functional_reqs: List[FunctionalReq]) -> List[str]:
        """Audits that functional requirements have matching tasks without false positives."""
        warnings = []
        task_feature_ids = {t.feature_id.lower() for t in tasks}
        task_titles = " ".join(t.title.lower() for t in tasks)
        
        for fr in functional_reqs:
            module_name = fr.module.lower().replace(" ", "").replace("_", "")
            req_id = fr.id.lower()
            # Match by module name, feature ID or title text
            matched = any(
                module_name in t.feature_id.lower().replace(" ", "").replace("_", "") or
                module_name in t.title.lower().replace(" ", "").replace("_", "") or
                req_id in t.title.lower()
                for t in tasks
            )
            if not matched and not any(word in task_titles for word in module_name.split() if len(word) > 3):
                warnings.append(f"Requirement '{fr.id}: {fr.title}' has no corresponding implementation tasks.")
                
        return warnings

validator = PlanValidator()
