
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
import uuid
import time
import client.db as db
from platform_core.tools.core_tools import NotificationTool

class OperatorAgent:
    def perceive(self, context: dict) -> dict:
        tenant_id = context.get("tenant_id", "local")
        
        workflows = db.get_workflows(tenant_id)
        sessions_today = db.get_sessions(days=1, tenant_id=tenant_id)
        sessions_this_week = db.get_sessions(days=7, tenant_id=tenant_id)
        alerts_unread = db.get_unread_alerts(tenant_id)
        pending_approvals = db.get_pending_approvals(tenant_id)
        
        # Which workflows ran today vs expected
        apps_today = {s["primary_app"] for s in sessions_today if s.get("primary_app")}
        
        expected_today = []
        missing_today = []
        for wf in workflows:
            if not wf.get("frequency_per_week", 0):
                continue
            first_app = (wf.get("app_sequence","").split(",")[0].strip())
            if wf["frequency_per_week"] >= 1:
                if first_app in apps_today:
                    expected_today.append(wf["name"])
                else:
                    missing_today.append(wf["name"])
        
        return {
            "tenant_id": tenant_id,
            "workflows_total": len(workflows),
            "sessions_today": len(sessions_today),
            "sessions_this_week": len(sessions_this_week),
            "workflows_running_today": expected_today,
            "workflows_missing_today": missing_today,
            "unread_alerts": len(alerts_unread),
            "pending_approvals": len(pending_approvals)
        }

    def plan(self, observation: dict) -> dict:
        actions = []
        
        # Flag missing workflows
        for wf_name in observation["workflows_missing_today"]:
            actions.append({
                "type": "NUDGE",
                "target": wf_name,
                "message": f"Recurring workflow not started today: {wf_name}"
            })
        
        # Flag alert backlog
        if observation["unread_alerts"] > 5:
            actions.append({
                "type": "ESCALATE",
                "message": f"{observation['unread_alerts']} unread alerts require attention"
            })
        
        # Flag approval backlog
        if observation["pending_approvals"] > 3:
            actions.append({
                "type": "ESCALATE", 
                "message": f"{observation['pending_approvals']} approvals are waiting"
            })
        
        return {"actions": actions, "tenant_id": observation["tenant_id"]}

    def execute(self, plan: dict, tools: dict = None) -> dict:
        notifier = NotificationTool()
        nudges_sent = 0
        escalations = 0
        
        for action in plan.get("actions", []):
            if action["type"] == "NUDGE":
                notifier.execute({
                    "title": "Nous Operator",
                    "message": action["message"]
                }, plan["tenant_id"])
                nudges_sent += 1
            
            elif action["type"] == "ESCALATE":
                db.insert_alert({
                    "tenant_id": plan["tenant_id"],
                    "severity": "medium",
                    "title": "Operator Alert",
                    "description": action["message"]
                })
                
                vault_manager = VaultManager()
                vault_manager.store_as_agent(VaultRecord(
                    id=str(uuid.uuid4()),
                    vault_level=VaultLevel.TEAM,
                    tenant_id=plan["tenant_id"],
                    record_type="operational_alert",
                    content={
                        "message": action["message"],
                        "type": action["type"],
                        "timestamp": int(time.time())
                    },
                    created_at=int(time.time())
                ), agent_name="operator")
                
                escalations += 1
        
        return {"nudges_sent": nudges_sent, "escalations": escalations}

    def learn(self, result: dict, feedback: dict):
        pass
