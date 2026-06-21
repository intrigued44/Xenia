import json
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel
from platform_core.agents_ext import call_claude

class OnboardingAgent:

    def generate_day_one_brief(
            self, tenant_id: str,
            role: str = None) -> dict:

        vault_manager = VaultManager()

        # Pull workflows from Role Vault
        role_workflows = vault_manager.retrieve_as_agent(
            VaultLevel.ROLE, tenant_id,
            agent_name="knowledge",
            record_type="workflow"
        )

        # Pull knowledge cards from Role Vault
        knowledge_cards = vault_manager.retrieve_as_agent(
            VaultLevel.ROLE, tenant_id,
            agent_name="knowledge",
            record_type="knowledge"
        )

        if not role_workflows and not knowledge_cards:
            return {
                "status": "insufficient_data",
                "message": (
                    "Not enough team data yet. "
                    "This brief will generate once "
                    "team members contribute their "
                    "workflow patterns to the Role Vault."
                ),
                "workflows_available": 0,
                "brief": None
            }

        workflow_summary = [
            {
                "name": w["content"].get("name"),
                "description": w["content"].get(
                    "description", ""
                ),
                "app_sequence": w["content"].get(
                    "app_sequence", []
                ),
                "frequency": w["content"].get(
                    "frequency_per_week", 0
                ),
                "avg_duration_minutes": round(
                    w["content"].get(
                        "avg_duration_seconds", 0
                    ) / 60, 1
                )
            }
            for w in role_workflows[:10]
        ]

        prompt = f"""
You are generating a day-one onboarding brief
for a new employee.

These are the actual workflows observed from people
who have done this role before, captured from real
work behavior — not from a job description:

{json.dumps(workflow_summary, indent=2)}

Generate a practical onboarding brief.
Be honest, specific, and use plain language.
No corporate speak.

Return ONLY valid JSON:
{{
  "what_this_role_actually_does": "2-3 sentences describing real day-to-day work based on the workflows above",
  "tools_you_will_use": [
    {{"tool": "name", "how_used": "one sentence"}}
  ],
  "processes_to_learn_first": [
    {{
      "name": "process name",
      "why_important": "one sentence",
      "frequency": "how often",
      "rough_steps": ["step 1", "step 2", "step 3"]
    }}
  ],
  "first_week_reality": "what the first week actually looks like based on these patterns",
  "questions_you_will_have": [
    "likely question 1",
    "likely question 2",
    "likely question 3"
  ]
}}
"""

        try:
            result = json.loads(
                call_claude(prompt)
            )
            return {
                "status": "ready",
                "generated_from": (
                    f"{len(role_workflows)} "
                    f"observed workflows"
                ),
                "workflows_available": len(role_workflows),
                "brief": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "brief": None
            }

    def generate_90_day_report(
            self, tenant_id: str) -> dict:

        vault_manager = VaultManager()

        personal_workflows = vault_manager.retrieve_as_agent(
            VaultLevel.PERSONAL, tenant_id,
            agent_name="workflow"
        )

        personal_knowledge = vault_manager.retrieve_as_agent(
            VaultLevel.PERSONAL, tenant_id,
            agent_name="knowledge"
        )

        contributions = vault_manager\
            .get_pending_contributions(tenant_id)

        prompt = f"""
You are generating a 90-day contribution report
for an employee.

Data:
- Workflows mastered: {len(personal_workflows)}
- Knowledge cards created: {len(personal_knowledge)}
- Patterns contributed to team: {len(contributions)}

Workflow names: {[
    w["content"].get("name","Unknown")
    for w in personal_workflows[:10]
]}

Generate an honest, evidence-based 90-day report.
Return ONLY valid JSON:
{{
  "headline": "one sentence summary of their contribution",
  "workflows_mastered": {len(personal_workflows)},
  "knowledge_contributed": {len(personal_knowledge)},
  "team_contributions": {len(contributions)},
  "strengths_observed": ["strength 1", "strength 2"],
  "growth_areas": ["area 1", "area 2"],
  "impact_statement": "what would have been harder without this person based on the data"
}}
"""

        try:
            result = json.loads(
                call_claude(prompt)
            )
            return {"status": "ready", "report": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}
