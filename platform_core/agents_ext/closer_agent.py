import time
import json
import client.db as db
from platform_core.agents_ext import call_claude

class CloserAgent:
    def perceive(self, context: dict) -> dict:
        tenant_id = context.get("tenant_id", "local")
        
        # Check Gmail if connected
        email_gaps = []
        try:
            from platform_core.connectors_ext.gmail import GmailConnector
            from platform_core.connectors_ext import registry
            connector = registry.get("gmail", tenant_id)
            if connector and connector.is_authenticated():
                email_gaps = connector.get_unanswered(days=3)
        except Exception as e:
            import logging
            logging.error(f"context: {e}", exc_info=True)
        
        # Check clipboard logs for any email-like patterns
        # (names, @mentions, action items)
        recent_logs = db.get_recent_logs(days=3, tenant_id=tenant_id)
        clipboard_items = [
            c[1] for c in recent_logs["clipboard_logs"] 
            if c[1] and len(c[1]) > 20
        ]
        
        return {
            "tenant_id": tenant_id,
            "email_gaps": email_gaps,
            "clipboard_sample": clipboard_items[:10]
        }

    def plan(self, observation: dict) -> dict:
        follow_ups = []
        
        for email in observation["email_gaps"]:
            follow_ups.append({
                "type": "EMAIL_FOLLOWUP",
                "thread_id": email.get("thread_id"),
                "sent_to": email.get("sent_to"),
                "subject": email.get("subject"),
                "days_waiting": email.get("days_since_sent", 0)
            })
        
        # Use Claude to identify any commitments in clipboard
        if observation["clipboard_sample"]:
            commitment_prompt = f"""
            Review these text snippets copied from work applications.
            Identify any that contain: deadlines, commitments, 
            action items, or things someone said they would do.
            
            Return JSON:
            {{"commitments": [
              {{"text": "string", "urgency": "high|medium|low"}}
            ]}}
            
            Snippets: {json.dumps(observation['clipboard_sample'])}
            """
            try:
                result = json.loads(call_claude(commitment_prompt))
                for c in result.get("commitments", []):
                    if c.get("urgency") in ["high", "medium"]:
                        follow_ups.append({
                            "type": "COMMITMENT",
                            "text": c.get("text"),
                            "urgency": c.get("urgency")
                        })
            except Exception as e:
                import logging
                logging.error(f"context: {e}", exc_info=True)
        
        return {
            "follow_ups": follow_ups,
            "tenant_id": observation["tenant_id"]
        }

    def execute(self, plan: dict, tools: dict = None) -> dict:
        proposals_created = 0
        
        for fu in plan.get("follow_ups", []):
            if fu["type"] == "EMAIL_FOLLOWUP":
                db.insert_proposal({
                    "type": "followup",
                    "title": f"No reply: {fu.get('subject','(no subject)')}",
                    "description": f"Sent to {fu.get('sent_to')}. Waiting {fu.get('days_waiting')} days.",
                    "proposed_action": "Draft follow-up email",
                    "permission_tier": "confirm",
                    "estimated_value_minutes": 10,
                    "status": "pending",
                    "tenant_id": plan["tenant_id"],
                    "created_at": int(time.time())
                })
                proposals_created += 1
            
            elif fu["type"] == "COMMITMENT":
                db.insert_proposal({
                    "type": "reminder",
                    "title": "Pending commitment detected",
                    "description": str(fu.get("text", ""))[:200],
                    "proposed_action": "Review and action this commitment",
                    "permission_tier": "auto",
                    "estimated_value_minutes": 5,
                    "status": "pending",
                    "tenant_id": plan["tenant_id"],
                    "created_at": int(time.time())
                })
                proposals_created += 1
        
        return {"proposals_created": proposals_created}

    def learn(self, result: dict, feedback: dict):
        pass
