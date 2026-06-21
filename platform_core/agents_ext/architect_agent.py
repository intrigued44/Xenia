
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
import uuid
import time
import os
from datetime import datetime
import client.db as db

class ArchitectAgent:
    def perceive(self, context: dict) -> dict:
        tenant_id = context.get("tenant_id", "local")
        
        from platform_core.intelligence.classifier import classify_all_patterns
        from platform_core.intelligence.preprocessor import build_analysis_context
        
        analysis = build_analysis_context(days=14)
        classified = classify_all_patterns(analysis.get("recurring_patterns", []))
        workflows = db.get_workflows(tenant_id)
        
        # Find redundancies: multiple workflows using same apps
        app_to_workflows = {}
        for wf in workflows:
            apps = [a.strip() for a in wf.get("app_sequence","").split(",") if a.strip()]
            for app in apps:
                if app not in app_to_workflows:
                    app_to_workflows[app] = []
                app_to_workflows[app].append(wf.get("name"))
        
        redundancies = {
            app: wfs for app, wfs in app_to_workflows.items() 
            if len(wfs) > 2
        }
        
        return {
            "tenant_id": tenant_id,
            "high_value_patterns": [
                p for p in classified 
                if p.get("recommended_action") == "AUTOMATE"
            ],
            "redundancies": redundancies,
            "total_automatable_minutes": sum(
                p.get("time_cost_score", 0) * 120 # Inverse logic from classification math to roughly get minutes
                for p in classified 
                if p.get("recommended_action") == "AUTOMATE"
            )
        }

    def plan(self, observation: dict) -> dict:
        improvements = []
        
        # High value automation targets
        for pattern in observation.get("high_value_patterns", [])[:3]:
            improvements.append({
                "type": "AUTOMATION_DESIGN",
                "pattern": pattern.get("app_sequence", []),
                "score": pattern.get("overall_score", 0),
                "time_minutes": pattern.get("time_cost_score", 0) * 120
            })
        
        # Redundancy consolidation
        for app, workflows in observation.get("redundancies", {}).items():
            improvements.append({
                "type": "CONSOLIDATION",
                "app": app,
                "workflows": workflows,
                "message": f"{len(workflows)} workflows all use {app} — consider a standard process"
            })
        
        return {
            "improvements": improvements,
            "total_recoverable_minutes": observation.get("total_automatable_minutes", 0),
            "tenant_id": observation["tenant_id"]
        }

    def execute(self, plan: dict, tools: dict = None) -> dict:
        proposals_created = 0
        vault_manager = VaultManager()
        
        for imp in plan.get("improvements", []):
            
            vault_manager.store_as_agent(VaultRecord(
                id=str(uuid.uuid4()),
                vault_level=VaultLevel.TEAM,
                tenant_id=plan["tenant_id"],
                record_type="improvement",
                content={
                    "type": imp["type"],
                    "description": imp.get("message", ""),
                    "pattern": imp.get("pattern", []),
                    "estimated_time_recovery_minutes": imp.get("time_minutes", 0)
                },
                created_at=int(time.time())
            ), agent_name="architect")
            
            if imp["type"] == "AUTOMATION_DESIGN":
                seq_str = " → ".join(imp["pattern"])
                time_hrs = round(imp["time_minutes"] / 60, 1)
                
                db.insert_proposal({
                    "type": "automation_opportunity",
                    "title": f"Automation opportunity: {seq_str}",
                    "description": f"This pattern runs regularly and consumes ~{time_hrs} hours/week. Automation score: {int(imp['score']*100)}%.",
                    "proposed_action": "Review and build automation",
                    "permission_tier": "confirm",
                    "estimated_value_minutes": int(imp["time_minutes"]),
                    "status": "pending",
                    "tenant_id": plan["tenant_id"],
                    "created_at": int(time.time())
                })
                proposals_created += 1
            
            elif imp["type"] == "CONSOLIDATION":
                db.insert_proposal({
                    "type": "process_improvement",
                    "title": f"Process consolidation: {imp['app']}",
                    "description": imp["message"],
                    "proposed_action": "Create a standard workflow",
                    "permission_tier": "auto",
                    "estimated_value_minutes": 30,
                    "status": "pending",
                    "tenant_id": plan["tenant_id"],
                    "created_at": int(time.time())
                })
                proposals_created += 1
        
        # Weekly efficiency report
        if plan.get("total_recoverable_minutes", 0) > 60:
            hrs = round(plan["total_recoverable_minutes"] / 60, 1)
            os.makedirs("reports", exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            with open(f"reports/{date_str}_efficiency.md", "w") as f:
                f.write(
                    f"# Efficiency Report — {date_str}\n\n"
                    f"**Total recoverable time: {hrs} hours/week**\n\n"
                    f"Top automation targets identified: {len(plan['improvements'])}\n"
                )
        
        return {"proposals_created": proposals_created}

    def learn(self, result: dict, feedback: dict):
        pass
