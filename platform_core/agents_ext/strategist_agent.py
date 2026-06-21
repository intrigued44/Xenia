
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
import uuid
import time
import os
import json
from datetime import datetime
import client.db as db
from platform_core.agents_ext import call_claude

class StrategistAgent:
    def perceive(self, context: dict) -> dict:
        tenant_id = context.get("tenant_id", "local")
        
        # Collect everything from the past week
        proposals = db.get_proposals(tenant_id, status="pending")
        alerts = db.get_unread_alerts(tenant_id)
        workflows = db.get_workflows(tenant_id)
        sessions = db.get_sessions(days=7, tenant_id=tenant_id)
        
        # Load today's briefing if exists
        briefing = ""
        date_str = datetime.now().strftime("%Y-%m-%d")
        briefing_path = f"briefings/{date_str}_morning.md"
        if os.path.exists(briefing_path):
            with open(briefing_path) as f:
                briefing = f.read()
        
        # Load efficiency report if exists
        efficiency = ""
        efficiency_path = f"reports/{date_str}_efficiency.md"
        if os.path.exists(efficiency_path):
            with open(efficiency_path) as f:
                efficiency = f.read()
        
        return {
            "tenant_id": tenant_id,
            "proposals_pending": len(proposals),
            "alerts_unread": len(alerts),
            "workflows_total": len(workflows),
            "sessions_this_week": len(sessions),
            "morning_briefing": briefing,
            "efficiency_report": efficiency,
            "proposal_types": [p.get("type") for p in proposals]
        }

    def plan(self, observation: dict) -> dict:
        # Strategist always generates a synthesis
        return {
            "generate_digest": True,
            "observation": observation,
            "tenant_id": observation["tenant_id"]
        }

    def execute(self, plan: dict, tools: dict = None) -> dict:
        obs = plan["observation"]
        
        synthesis_prompt = f"""
        You are the STRATEGIST agent for Nous. 
        You have read all reports from the other agents this week.
        Generate a concise strategic digest for the business owner.
        
        Data this week:
        - Pending proposals needing attention: {obs['proposals_pending']}
        - Unread operational alerts: {obs['alerts_unread']}
        - Active workflows tracked: {obs['workflows_total']}
        - Work sessions logged: {obs['sessions_this_week']}
        - Proposal types: {obs['proposal_types']}
        
        Morning intelligence briefing:
        {obs['morning_briefing'][:500] if obs['morning_briefing'] else 'Not available'}
        
        Efficiency report:
        {obs['efficiency_report'][:300] if obs['efficiency_report'] else 'Not available'}
        
        Generate a weekly strategic digest with:
        1. State of operations (2 sentences)
        2. Top 3 decisions the owner should make this week
        3. Biggest opportunity identified
        4. Biggest risk identified
        5. One thing that is working well
        
        Keep under 300 words. Executive-level. No fluff.
        Return JSON: {{"digest": "string"}}
        """
        
        try:
            digest = json.loads(call_claude(synthesis_prompt))["digest"]
        except Exception:
            digest = "Strategic synthesis failed."
        
        # Save weekly digest
        os.makedirs("digests", exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        path = f"digests/{date_str}_strategic.md"
        with open(path, "w") as f:
            f.write(f"# Strategic Digest — {date_str}\n\n{digest}\n")
            
        vault_manager = VaultManager()
        vault_manager.store_as_agent(VaultRecord(
            id=str(uuid.uuid4()),
            vault_level=VaultLevel.ORGANIZATION,
            tenant_id=plan["tenant_id"],
            record_type="strategic_digest",
            content={
                "digest": digest,
                "date": date_str,
                "data_sources": {
                    "proposals": obs["proposals_pending"],
                    "alerts": obs["alerts_unread"],
                    "sessions": obs["sessions_this_week"]
                }
            },
            created_at=int(time.time())
        ), agent_name="strategist")
        
        # Surface as high-priority proposal
        db.insert_proposal({
            "type": "strategic_digest",
            "title": "Weekly Strategic Digest Ready",
            "description": digest[:300] + "...",
            "proposed_action": "Read full digest in Insights tab",
            "permission_tier": "auto",
            "estimated_value_minutes": 10,
            "status": "pending",
            "tenant_id": plan["tenant_id"],
            "created_at": int(time.time())
        })
        
        return {"digest_saved": True, "path": path}

    def learn(self, result: dict, feedback: dict):
        pass
