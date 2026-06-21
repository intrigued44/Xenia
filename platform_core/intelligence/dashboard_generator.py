import json
import time
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel
from platform_core.agents_ext import call_claude

class DashboardGenerator:

    DASHBOARD_TYPES = {
        "team_health": "How is the team operating?",
        "process_efficiency": 
            "Where is time being lost?",
        "knowledge_map": 
            "Where does knowledge live?",
        "growth_tracker": 
            "How is everyone developing?",
        "automation_opportunities": 
            "What should we automate?",
        "risk_assessment": 
            "What could break?",
        "onboarding_readiness": 
            "Are we ready to onboard someone?",
        "department_comparison": 
            "How do departments compare?"
    }

    def generate(self, dashboard_type: str,
                 tenant_id: str,
                 custom_question: str = None) -> dict:
        
        vault_manager = VaultManager()
        question = custom_question or \
            self.DASHBOARD_TYPES.get(
                dashboard_type,
                "What is the state of operations?"
            )
        
        # Pull relevant data for the question
        all_data = {
            "personal_workflows": 
                len(vault_manager.retrieve_as_agent(
                    VaultLevel.PERSONAL, tenant_id,
                    agent_name="workflow"
                )),
            "role_patterns": 
                len(vault_manager.retrieve_as_agent(
                    VaultLevel.ROLE, tenant_id,
                    agent_name="architect"
                )),
            "team_intelligence": 
                len(vault_manager.retrieve_as_agent(
                    VaultLevel.TEAM, tenant_id,
                    agent_name="architect"
                )),
            "org_intelligence": 
                len(vault_manager.retrieve_as_agent(
                    VaultLevel.ORGANIZATION, tenant_id,
                    agent_name="strategist"
                ))
        }
        
        prompt = f"""
You are generating a business intelligence dashboard
to answer this question: "{question}"

Available data summary:
{json.dumps(all_data, indent=2)}

Generate a dashboard specification with real
calculated metrics and visualisation recommendations.
Return ONLY valid JSON:
{{
    "title": "Dashboard title",
    "question_answered": "{question}",
    "summary": "2 sentence answer to the question",
    "key_metrics": [
        {{
            "label": "metric name",
            "value": "calculated value or N/A",
            "trend": "up|down|stable|unknown",
            "interpretation": "what this means"
        }}
    ],
    "charts": [
        {{
            "type": "bar|line|pie|number|table",
            "title": "chart title",
            "data_source": "which vault",
            "insight": "what this chart reveals"
        }}
    ],
    "top_finding": "the single most important thing",
    "recommended_action": "what to do about it"
}}
"""
        
        try:
            dashboard = json.loads(
                call_claude(prompt, max_tokens=1000)
            )
            dashboard["generated_at"] = int(time.time())
            dashboard["data_freshness"] = "real-time"
            return {
                "status": "ready",
                "dashboard": dashboard
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
