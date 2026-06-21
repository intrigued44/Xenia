
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
import hashlib
import os
import json
import uuid
import time
from platform_core.agents import Agent
from client.db import get_sessions, get_workflows, get_connection
from platform_core.tools.core_tools import registry

class KnowledgeAgent(Agent):
    name = "KnowledgeAgent"
    
    def perceive(self, context):
        tenant_id = context.get("tenant_id", "local")
        sessions = get_sessions(tenant_id=tenant_id)
        workflows = get_workflows(tenant_id=tenant_id)
        return {
            "sessions": sessions,
            "workflows": workflows,
            "tenant_id": tenant_id
        }
        
    def plan(self, observation):
        missing_docs = []
        for wf in observation.get("workflows", []):
            if not wf.get("description"):
                missing_docs.append(wf)
        
        return {
            "tenant_id": observation.get("tenant_id"),
            "generate_cards": missing_docs,
            "flag_risks": len(missing_docs) > 5,
            "sessions": observation.get("sessions", [])
        }
        
    def execute(self, plan, tools):
        tenant_id = plan.get("tenant_id", "local")
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "mock_key"))
        
        cards_generated = 0
        
        conn = get_connection()
        cursor = conn.cursor()
        
        for wf in plan.get("generate_cards", []):
            prompt = f"Write a 3-paragraph knowledge card for this process: {wf['name']} — {wf.get('description', '')}. Paragraph 1: what it is and why it matters. Paragraph 2: how it works step by step. Paragraph 3: who needs to know this and when."
            try:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                desc = response.content[0].text
                snake_name = wf['name'].lower().replace(" ", "_")
                os.makedirs("knowledge_base", exist_ok=True)
                filepath = f"knowledge_base/{snake_name}.md"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(desc)
                    
                cursor.execute("UPDATE workflows SET description = ? WHERE id = ? AND tenant_id = ?", (desc, wf["id"], tenant_id))
                
                vault_manager = VaultManager()
                vault_manager.store_as_agent(VaultRecord(
                    id=str(uuid.uuid4()),
                    vault_level=VaultLevel.PERSONAL,
                    tenant_id=tenant_id,
                    record_type="knowledge",
                    content={
                        "title": wf['name'],
                        "card_content": desc,
                        "doc_path": filepath
                    },
                    created_at=int(time.time())
                ), agent_name="knowledge")
                cards_generated += 1
            except Exception as e:
                print(f"Error generating knowledge card: {e}")
                
        # Build tool usage map
        # Request specifies: Read all sessions from db.get_sessions(days=30), Count time per app across all sessions, Save to /knowledge_base/tool_usage_map.json
        sessions = get_sessions(days=30, tenant_id=tenant_id)
        app_usage = {}
        for sess in sessions:
            app = sess.get("primary_app")
            if app and sess.get("ended_at") and sess.get("started_at"):
                duration_mins = (sess["ended_at"] - sess["started_at"]) / 60
                app_usage[app] = app_usage.get(app, 0) + duration_mins
                
        os.makedirs("knowledge_base", exist_ok=True)
        with open("knowledge_base/tool_usage_map.json", "w", encoding="utf-8") as f:
            json.dump(app_usage, f, indent=2)
            
        vault_manager = VaultManager()
        vault_manager.store_as_agent(VaultRecord(
            id=str(uuid.uuid4()),
            vault_level=VaultLevel.PERSONAL,
            tenant_id=tenant_id,
            record_type="tool_usage",
            content=app_usage,
            created_at=int(time.time())
        ), agent_name="knowledge")

        risks_flagged = False
        missing_docs = plan.get("generate_cards", [])
        if missing_docs:
            cursor.execute('''
                INSERT INTO alerts (id, tenant_id, severity, title, description, created_at, status)
                VALUES (?, ?, 'medium', 'Undocumented workflows detected', ?, ?, 'unread')
            ''', (str(uuid.uuid4()), tenant_id, f"{len(missing_docs)} workflows have no documentation", int(time.time())))
            risks_flagged = True
            
        conn.commit()
        conn.close()
            
        return {
            "cards_generated": cards_generated,
            "risks_flagged": risks_flagged
        }
        
    def learn(self, result, feedback):
        pass
