import os
import json
import uuid
from anthropic import Anthropic
from platform_core.orchestration.engine import Plan, PlanStep

class NaturalLanguagePlanner:
    def __init__(self, tool_registry):
        self.registry = tool_registry

    def create_plan(self, goal: str, tenant_id: str) -> Plan:
        tools_context = []
        for name, tool in self.registry.list_tools().items():
            tools_context.append(f"- {name} [{tool.permission_tier}]: {tool.description}")
        tools_context_str = "\n".join(tools_context)

        system_prompt = "You are an execution planner for the Nous platform. Given a goal and available tools, produce a JSON execution plan. Think step by step. Identify information dependencies. Mark steps that need human approval correctly."
        
        PLAN_SCHEMA = """
        {
          "goal_interpreted": "string",
          "steps": [
            {
              "id": "step_1",
              "tool_name": "web_tool.search",
              "params": {},
              "depends_on": [],
              "permission_tier": "auto",
              "success_criteria": "string"
            }
          ]
        }
        """

        prompt = f"Goal: {goal}\n\nAvailable tools:\n{tools_context_str}\n\nReturn ONLY valid JSON matching this schema: {PLAN_SCHEMA}"

        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "mock_key"))
        
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.content[0].text
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            plan_data = json.loads(response_text.strip())
            
            steps = []
            for s in plan_data.get("steps", []):
                steps.append(PlanStep(
                    id=s["id"],
                    tool_name=s["tool_name"],
                    params=s.get("params", {}),
                    depends_on=s.get("depends_on", []),
                    permission_tier=s.get("permission_tier", "auto"),
                    success_criteria=s.get("success_criteria", "")
                ))
                
            return Plan(id=str(uuid.uuid4()), goal=goal, tenant_id=tenant_id, steps=steps)
            
        except Exception as e:
            raise Exception(f"PlanningError: {str(e)}")
