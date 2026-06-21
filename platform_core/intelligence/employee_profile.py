import json
import time
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel
from platform_core.agents_ext import call_claude

class EmployeeIntelligenceProfile:

    def generate(self, tenant_id: str) -> dict:
        vault_manager = VaultManager()
        
        # Everything from personal vault
        my_workflows = vault_manager.retrieve_as_agent(
            VaultLevel.PERSONAL, tenant_id,
            agent_name="workflow",
            record_type="workflow"
        )
        
        my_knowledge = vault_manager.retrieve_as_agent(
            VaultLevel.PERSONAL, tenant_id,
            agent_name="knowledge",
            record_type="knowledge"
        )
        
        my_tools = vault_manager.retrieve_as_agent(
            VaultLevel.PERSONAL, tenant_id,
            agent_name="knowledge",
            record_type="tool_usage"
        )
        
        contributions = vault_manager\
            .get_pending_contributions(tenant_id)
        
        # Real contribution metrics
        workflows_owned = len(my_workflows)
        knowledge_created = len(my_knowledge)
        
        tool_usage = {}
        if my_tools:
            tool_usage = my_tools[0].get(
                "content", {}
            )
        
        top_tools = sorted(
            tool_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5] if tool_usage else []
        
        automation_potential_avg = (
            sum(
                w["content"].get(
                    "automation_potential", 0
                )
                for w in my_workflows
            ) / len(my_workflows)
            if my_workflows else 0
        )
        
        total_weekly_hours = sum(
            w["content"].get(
                "frequency_per_week", 0
            ) *
            w["content"].get(
                "avg_duration_seconds", 0
            ) / 3600
            for w in my_workflows
        )
        
        if not my_workflows:
            return {
                "status": "building",
                "message": "Your intelligence profile "
                           "is building. Keep working "
                           "normally."
            }
        
        prompt = f"""
You are generating an employee intelligence profile.
This is owned by the employee, not their employer.
It captures their real skills and contributions.

Real behavioral data:
- Workflows mastered: {workflows_owned}
- Knowledge assets created: {knowledge_created}
- Top tools by usage: {top_tools}
- Weekly hours in productive workflows: 
  {round(total_weekly_hours,1)}
- Automation thinking score: 
  {round(automation_potential_avg*100,0)}%
- Patterns contributed to team: {len(contributions)}

Workflow names: {[
    w["content"].get("name","")
    for w in my_workflows[:10]
]}

Generate an honest intelligence profile.
This is for the employee to understand themselves
and present their case for growth.
Return ONLY valid JSON:
{{
    "capability_summary": "2 sentences about what this person is genuinely good at based on the data",
    "top_skills": [
        {{"skill": "string", "evidence": "string"}}
    ],
    "workflow_mastery": [
        {{"workflow": "string", "proficiency": "building|competent|expert"}}
    ],
    "contribution_score": 0-100,
    "contribution_breakdown": {{
        "workflows_owned": {workflows_owned},
        "knowledge_created": {knowledge_created},
        "team_contributions": {len(contributions)},
        "weekly_productive_hours": 
            {round(total_weekly_hours,1)}
    }},
    "growth_opportunities": [
        "specific opportunity based on the data"
    ],
    "promotion_case": "2-3 sentences this employee could use as evidence in a performance review",
    "career_trajectory": "what this person is becoming based on their behavioral patterns"
}}
"""
        
        try:
            profile = json.loads(
                call_claude(prompt, max_tokens=1200)
            )
            return {
                "status": "ready",
                "profile": profile,
                "raw_metrics": {
                    "workflows_owned": workflows_owned,
                    "knowledge_created": knowledge_created,
                    "team_contributions": 
                        len(contributions),
                    "top_tools": top_tools,
                    "weekly_hours": 
                        round(total_weekly_hours,1)
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def export_portable(self, tenant_id: str) -> dict:
        # The career brain they take with them
        profile = self.generate(tenant_id)
        vault_manager = VaultManager()
        
        my_workflows = vault_manager.retrieve_as_agent(
            VaultLevel.PERSONAL, tenant_id,
            agent_name="workflow",
            record_type="workflow"
        )
        
        return {
            "nous_profile_version": "1.0",
            "exported_at": int(time.time()),
            "tenant_id": "portable",
            "profile": profile,
            "workflows": [
                {
                    "name": w["content"].get("name"),
                    "description": w["content"].get(
                        "description"
                    ),
                    "app_sequence": w["content"].get(
                        "app_sequence"
                    ),
                    "proficiency_signals": {
                        "frequency": w["content"].get(
                            "frequency_per_week"
                        ),
                        "consistency": "high"
                    }
                }
                for w in my_workflows
            ],
            "portable_note": (
                "This profile was generated by Nous. "
                "It contains behavioral intelligence "
                "owned entirely by the employee. "
                "Bring this to your next organization."
            )
        }
