from platform_core.agents_ext.workflow_agent import WorkflowAgent
from platform_core.agents_ext.knowledge_agent import KnowledgeAgent
from platform_core.agents_ext.scout_agent import ScoutAgent
from platform_core.agents_ext.operator_agent import OperatorAgent
from platform_core.agents_ext.closer_agent import CloserAgent
from platform_core.agents_ext.architect_agent import ArchitectAgent
from platform_core.agents_ext.strategist_agent import StrategistAgent

class AgentOrchestrator:
    def __init__(self):
        self.agents = [
            WorkflowAgent(),
            KnowledgeAgent(),
            ScoutAgent(),
            OperatorAgent(),
            CloserAgent(),
            ArchitectAgent(),
            StrategistAgent()
        ]

    def run_all(self, tenant_id: str):
        """
        Runs the full autonomous operating team sequentially.
        For each agent, it calls perceive() -> plan() -> execute() -> learn().
        """
        for agent in self.agents:
            try:
                # 1. Perceive
                context = {"tenant_id": tenant_id}
                observation = agent.perceive(context)
                
                # 2. Plan
                plan = agent.plan(observation)
                
                # 3. Execute
                # Pass a mock/empty tools dict or integrate with real tool registry if needed by specific agents
                result = agent.execute(plan, tools={})
                
                # 4. Learn
                agent.learn(result, feedback={})
                
            except Exception as e:
                print(f"Error running agent {agent.__class__.__name__}: {e}")
                
        # Run and test all registered skills to drive the self-improving learning loop
        try:
            from client.db import get_connection
            from platform_core.intelligence.skills_engine import run_and_heal_skill
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, code_content FROM agent_skills WHERE tenant_id = ?", (tenant_id,))
            skills = cursor.fetchall()
            conn.close()
            for skill_name, code_content in skills:
                print(f"[Orchestrator] Running and verifying skill '{skill_name}'...")
                run_and_heal_skill(skill_name, code_content, tenant_id)
        except Exception as se:
            print(f"[Orchestrator] Error running skills verification: {se}")
            
        return {"status": "success", "agents_run": len(self.agents)}
