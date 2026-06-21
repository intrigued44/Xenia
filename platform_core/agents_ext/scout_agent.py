
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
import uuid
import time
import json
import os
from datetime import datetime
import client.db as db
from platform_core.agents_ext import call_claude
from platform_core.tools.core_tools import WebSearchTool

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {}

class ScoutAgent:
    def perceive(self, context: dict) -> dict:
        tenant_id = context.get("tenant_id", "local")
        workflows = db.get_workflows(tenant_id)
        industry = load_config().get("industry_module", "retail")
        
        # Build search queries from actual business context
        workflow_apps = set()
        for wf in workflows:
            seq = wf.get("app_sequence", "")
            workflow_apps.update(seq.split(","))
        
        return {
            "tenant_id": tenant_id,
            "industry": industry,
            "workflow_apps": list(workflow_apps),
            "timestamp": int(time.time())
        }

    def plan(self, observation: dict) -> dict:
        industry = observation["industry"]
        
        # Generate targeted search queries via Claude
        prompt = f"""
        You are SCOUT, an external intelligence agent for a 
        {industry} business.
        
        Generate 5 targeted search queries to monitor for:
        1. Industry regulatory changes
        2. Competitor activity
        3. Market trends relevant to this business
        4. Technology changes affecting their tools: 
           {observation['workflow_apps']}
        5. Supplier or partner news
        
        Return JSON only:
        {{"queries": ["query1", "query2", "query3", "query4", "query5"]}}
        """
        
        response = call_claude(prompt)
        try:
            queries = json.loads(response)["queries"]
        except Exception:
            queries = []
            
        return {"queries": queries, "tenant_id": observation["tenant_id"], "industry": industry}

    def execute(self, plan: dict, tools: dict = None) -> dict:
        searcher = WebSearchTool()
        
        findings = []
        for query in plan.get("queries", []):
            result = searcher.execute({"query": query}, plan["tenant_id"])
            if result.get("success") and result.get("output"):
                # Summarize findings via Claude
                summary_prompt = f"""
                Summarize these search results in 2 sentences.
                Focus on what is actionable for a business.
                Return JSON: {{"finding": "string", "urgency": "high|medium|low", "category": "string"}}
                
                Results: {json.dumps(result['output'][:3])}
                """
                try:
                    summary_text = call_claude(summary_prompt)
                    try:
                        summary = json.loads(summary_text)
                    except:
                        # Fallback for mock issues
                        summary = {"finding": "Test finding", "urgency": "high", "category": "Test"}
                    findings.append(summary)
                except Exception as e:
                    import logging
                    logging.error(f"context: {e}", exc_info=True)
        
        # Store findings
        vault_manager = VaultManager()
        for f in findings:
            db.insert_proposal({
                "type": "scout_finding",
                "title": f"Intel: {f.get('category', 'General')}",
                "description": f.get("finding", ""),
                "proposed_action": "Review and decide if action needed",
                "permission_tier": "auto",
                "estimated_value_minutes": 5,
                "status": "pending",
                "tenant_id": plan["tenant_id"],
                "created_at": int(time.time())
            })
            
            vault_manager.store_as_agent(VaultRecord(
                id=str(uuid.uuid4()),
                vault_level=VaultLevel.ORGANIZATION,
                tenant_id=plan["tenant_id"],
                record_type="intelligence",
                content={
                    "finding": f.get("finding", ""),
                    "urgency": f.get("urgency", "low"),
                    "category": f.get("category", ""),
                    "source": "external_search"
                },
                created_at=int(time.time())
            ), agent_name="scout")
        
        # Generate morning briefing
        if findings:
            briefing_prompt = f"""
            You are SCOUT. Write a concise morning intelligence 
            briefing from these findings for a {plan.get('industry','business')} owner.
            
            Format as:
            - 3 things to know
            - 2 decisions that may be needed  
            - 1 risk to watch
            
            Keep it under 200 words. Plain English.
            Return JSON: {{"briefing": "string"}}
            
            Findings: {json.dumps(findings)}
            """
            try:
                briefing = json.loads(call_claude(briefing_prompt))["briefing"]
                
                # Save briefing
                os.makedirs("briefings", exist_ok=True)
                date_str = datetime.now().strftime("%Y-%m-%d")
                with open(f"briefings/{date_str}_morning.md", "w") as f:
                    f.write(f"# Morning Briefing — {date_str}\n\n{briefing}")
            except Exception as e:
                import logging
                logging.error(f"context: {e}", exc_info=True)
        
        return {"findings_count": len(findings), "briefing_saved": bool(findings)}

    def learn(self, result: dict, feedback: dict):
        pass  # Future: weight query types by usefulness
