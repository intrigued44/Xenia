import uuid
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from client.db import get_connection

@dataclass
class PlanStep:
    id: str
    tool_name: str
    params: dict
    depends_on: list[str]
    permission_tier: str
    success_criteria: str
    retry_count: int = 1
    timeout_seconds: int = 30
    status: str = "pending"

@dataclass
class Plan:
    id: str
    goal: str
    tenant_id: str
    steps: list[PlanStep]
    status: str = "pending"
    created_at: int = int(time.time())
    completed_at: Optional[int] = None

@dataclass
class PlanResult:
    plan_id: str
    step_results: dict
    overall_status: str
    failed_step: Optional[str] = None

class OrchestrationEngine:
    def __init__(self, tool_registry, db_connection=None):
        self.registry = tool_registry
        self._db = db_connection or get_connection

    def _topological_sort(self, steps: List[PlanStep]) -> List[PlanStep]:
        ordered = []
        visited = set()
        step_map = {s.id: s for s in steps}
        
        def visit(step_id):
            if step_id in visited: return
            for dep in step_map[step_id].depends_on:
                visit(dep)
            visited.add(step_id)
            ordered.append(step_map[step_id])
            
        for s in steps:
            visit(s.id)
        return ordered

    def execute(self, plan: Plan) -> PlanResult:
        # 1. Validate plan
        for step in plan.steps:
            if not self.registry.get(step.tool_name):
                return PlanResult(plan.id, {}, "failed", step.id)
                
        # 2. Sort
        ordered_steps = self._topological_sort(plan.steps)
        step_results = {}
        
        # 3. Execute
        for step in ordered_steps:
            # check dependencies
            for dep in step.depends_on:
                if step_results.get(dep, {}).get("success") is not True:
                    return PlanResult(plan.id, step_results, "failed", step.id)
                    
            if step.permission_tier in ["confirm", "review"]:
                approval_id = self._request_approval(plan.id, step, plan.tenant_id)
                step.status = "paused_for_approval"
                return PlanResult(plan.id, step_results, "paused", None)
                
            tool = self.registry.get(step.tool_name)
            res = tool.execute(step.params, plan.tenant_id)
            
            if not res.get("success") and step.retry_count > 0:
                step.retry_count -= 1
                res = tool.execute(step.params, plan.tenant_id)
                
            self._log_execution(plan.id, step, res, plan.tenant_id)
            step_results[step.id] = res
            
            if not res.get("success"):
                return PlanResult(plan.id, step_results, "failed", step.id)
                
        plan.status = "completed"
        return PlanResult(plan.id, step_results, "completed", None)

    def resume(self, plan_id: str, approval_id: str, tenant_id: str) -> PlanResult:
        # Mock resume execution logic
        pass

    def _request_approval(self, plan_id: str, step: PlanStep, tenant_id: str) -> str:
        appr_id = str(uuid.uuid4())
        conn = self._db()
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO pending_approvals (id, plan_id, step_id, tool_name, params_summary, status, tenant_id, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            ''', (appr_id, plan_id, step.id, step.tool_name, str(step.params), tenant_id, int(time.time())))
            conn.commit()
        except Exception as e:
            import logging
            logging.error(f"context: {e}", exc_info=True) # fallback for testing
        finally:
            conn.close()
        return appr_id

    def _log_execution(self, plan_id: str, step: PlanStep, result: dict, tenant_id: str):
        conn = self._db()
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO plan_execution_log (plan_id, step_id, tool_name, status, result_summary, execution_time_ms, timestamp, tenant_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (plan_id, step.id, step.tool_name, "success" if result.get("success") else "failed", 
                  str(result.get("output", result.get("error"))), result.get("execution_time_ms", 0), int(time.time()), tenant_id))
            conn.commit()
        except Exception as e:
            import logging
            logging.error(f"context: {e}", exc_info=True) # fallback for testing
        finally:
            conn.close()
