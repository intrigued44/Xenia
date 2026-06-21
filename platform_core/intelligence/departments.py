import json
import time
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel
from platform_core.agents_ext import call_claude

class DepartmentIntelligence:

    DEPARTMENTS = [
        "sales", "operations", "finance",
        "engineering", "product", "legal",
        "customer_success", "leadership",
        "hr", "marketing", "general"
    ]

    def analyze(self, tenant_id: str,
                department: str = "general") -> dict:
        
        vault_manager = VaultManager()
        
        # Pull all workflows from team vault
        workflows = vault_manager.retrieve_as_agent(
            VaultLevel.TEAM, tenant_id,
            agent_name="architect",
            record_type="workflow"
        )
        
        # Pull personal vault patterns
        personal = vault_manager.retrieve_as_agent(
            VaultLevel.PERSONAL, tenant_id,
            agent_name="workflow",
            record_type="workflow"
        )
        
        # Pull org vault intelligence
        org_intel = vault_manager.retrieve_as_agent(
            VaultLevel.ORGANIZATION, tenant_id,
            agent_name="strategist",
            record_type="strategic_digest"
        )
        
        all_workflows = workflows + personal
        
        if not all_workflows:
            return {
                "status": "insufficient_data",
                "department": department
            }
        
        # Calculate real metrics
        total_workflows = len(all_workflows)
        
        total_weekly_hours = sum(
            (w["content"].get("frequency_per_week",0) *
             w["content"].get("avg_duration_seconds",0))
            / 3600
            for w in all_workflows
        )
        
        automation_candidates = [
            w for w in all_workflows
            if w["content"].get(
                "automation_potential", 0
            ) > 0.7
        ]
        
        recoverable_hours = sum(
            (w["content"].get("frequency_per_week",0) *
             w["content"].get("avg_duration_seconds",0))
            / 3600
            for w in automation_candidates
        )
        
        undocumented = [
            w for w in all_workflows
            if not w["content"].get("description")
        ]
        
        top_workflows_list = [
            {
                "name": w["content"].get("name",""),
                "frequency": w["content"].get(
                    "frequency_per_week",0
                ),
                "automation_potential": w["content"].get(
                    "automation_potential",0
                )
            }
            for w in all_workflows[:8]
        ]

        # Use Claude to generate department analysis
        prompt = f"""
You are analyzing the operational intelligence
for the {department} function of an organization.

Real behavioral data:
- Total workflows detected: {total_workflows}
- Weekly hours in workflows: {round(total_weekly_hours,1)}
- Automation candidates: {len(automation_candidates)}
- Recoverable hours/week: {round(recoverable_hours,1)}
- Undocumented processes: {len(undocumented)}

Top workflows: {json.dumps(top_workflows_list, indent=2)}

Generate a department intelligence report.
Return ONLY valid JSON:
{{
    "health_score": 85,
    "health_label": "Critical|At Risk|Stable|Strong|Excellent",
    "biggest_opportunity": "one sentence",
    "biggest_risk": "one sentence",
    "top_insights": [
        {{"insight": "string", "impact": "high|medium|low"}}
    ],
    "recommended_actions": [
        {{"action": "string", "effort": "low|medium|high",
          "impact": "high|medium|low"}}
    ],
    "summary": "2-3 sentence executive summary"
}}
"""
        
        try:
            analysis = json.loads(
                call_claude(prompt, max_tokens=1000)
            )
        except Exception:
            analysis = {
                "health_score": 50,
                "health_label": "Stable",
                "biggest_opportunity": 
                    f"Automate {len(automation_candidates)}"
                    f" workflows",
                "biggest_risk": 
                    f"{len(undocumented)} undocumented"
                    f" processes",
                "top_insights": [],
                "recommended_actions": [],
                "summary": "Analysis unavailable"
            }
        
        return {
            "status": "ready",
            "department": department,
            "metrics": {
                "total_workflows": total_workflows,
                "weekly_hours": round(total_weekly_hours,1),
                "automation_candidates": 
                    len(automation_candidates),
                "recoverable_hours_per_week": 
                    round(recoverable_hours,1),
                "undocumented_processes": len(undocumented)
            },
            "analysis": analysis,
            "automation_targets": [
                {
                    "name": w["content"].get("name",""),
                    "potential": w["content"].get(
                        "automation_potential",0
                    ),
                    "hours_per_week": round(
                        w["content"].get(
                            "frequency_per_week",0
                        ) *
                        w["content"].get(
                            "avg_duration_seconds",0
                        ) / 3600, 1
                    )
                }
                for w in automation_candidates[:5]
            ]
        }
