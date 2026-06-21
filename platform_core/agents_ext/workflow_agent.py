
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
import hashlib
import json
import os
import uuid
import time
from platform_core.agents import Agent
from client.preprocessor import build_analysis_context
from client.db import get_workflows, upsert_workflow, get_connection
from platform_core.intelligence.graph import get_most_connected
from platform_core.intelligence.classifier import PatternClassifier
from platform_core.tools.core_tools import registry

class WorkflowAgent(Agent):
    name = "WorkflowAgent"
    
    def perceive(self, context):
        tenant_id = context.get("tenant_id", "local")
        analysis = build_analysis_context(days=7)
        workflows = get_workflows(tenant_id)
        bottlenecks = get_most_connected(tenant_id, limit=5)
        
        classifier = PatternClassifier()
        classifier_results = classifier.classify_all_patterns(analysis.get("detected_patterns", []))
        
        return {
            "analysis": analysis,
            "existing_workflows": workflows,
            "bottlenecks": bottlenecks,
            "classified_patterns": classifier_results,
            "tenant_id": tenant_id
        }
        
    def plan(self, observation):
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "mock_key"))
        system_prompt = "You are the WorkflowAgent for Nous. Analyze the detected patterns and decide what action to take for each. Return ONLY valid JSON."
        
        schema = """
        {
          "actions": [
            {
              "pattern": "app_sequence string",
              "action": "DOCUMENT | AUTOMATE | ALERT | IGNORE",
              "rationale": "string",
              "confidence": 0.0,
              "workflow_name": "string",
              "workflow_description": "string"
            }
          ]
        }
        """
        
        prompt = f"Observation: {json.dumps(observation.get('classified_patterns', []))}\n\nSchema: {schema}"
        
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            resp_text = response.content[0].text
            if resp_text.startswith("```json"):
                resp_text = resp_text[7:]
            if resp_text.endswith("```"):
                resp_text = resp_text[:-3]
            data = json.loads(resp_text.strip())
            
            # Filter confidence
            actions = [a for a in data.get("actions", []) if a.get("confidence", 0) > 0.6]
            return {"actions": actions, "tenant_id": observation.get("tenant_id")}
        except Exception as e:
            return {"actions": [], "error": str(e)}
        
    def execute(self, plan, tools):
        tenant_id = plan.get("tenant_id", "local")
        stats = {"documented": 0, "automations_queued": 0, "alerts_created": 0}
        
        conn = get_connection()
        cursor = conn.cursor()
        
        from anthropic import Anthropic
        
        api_key = os.environ.get("ANTHROPIC_API_KEY", "mock_key")
        if api_key == "mock_key":
            client = None
        else:
            client = Anthropic(api_key=api_key)
        
        for action in plan.get("actions", []):
            wf_name = action.get("workflow_name", "Unknown")
            act_type = action.get("action")
            snake_name = wf_name.lower().replace(" ", "_")
            
            if act_type == "DOCUMENT":
                try:
                    sys_prompt = "Generate a professional process document for this workflow. Include: overview, step-by-step instructions, tools involved, common variations, and tips. Return clean Markdown."
                    if client:
                        try:
                            resp = client.messages.create(
                                model="claude-haiku-4-5-20251001",
                                max_tokens=1500,
                                system=sys_prompt,
                                messages=[{"role": "user", "content": f"Workflow Pattern: {action.get('pattern')}"}]
                            )
                            md_content = resp.content[0].text
                        except Exception:
                            md_content = "# Process Document\n\nSteps to process."
                    else:
                        md_content = "# Process Document\n\nSteps to process."
                    os.makedirs("process_docs", exist_ok=True)
                    filepath = f"process_docs/{snake_name}.md"
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(md_content)
                    
                    vault_manager = VaultManager()
                    record = VaultRecord(
                        id=str(uuid.uuid4()),
                        vault_level=VaultLevel.PERSONAL,
                        tenant_id=tenant_id,
                        record_type="workflow",
                        contributor_hash=hashlib.sha256(tenant_id.encode()).hexdigest()[:16],
                        content={
                            "name": wf_name,
                            "description": action.get("workflow_description", ""),
                            "app_sequence": action.get("pattern", "[]"),
                            "doc_path": filepath
                        },
                        created_at=int(time.time())
                    )
                    record_id = vault_manager.store_as_agent(record, agent_name="workflow")
                    
                    vault_manager.request_contribution(
                        record_id=record_id,
                        from_vault=VaultLevel.PERSONAL,
                        to_vault=VaultLevel.ROLE,
                        summary=f"Contribute '{wf_name}' pattern to your role's knowledge base? Only the process structure is shared — never your personal data.",
                        tenant_id=tenant_id,
                        contributor_hash=record.contributor_hash
                    )
                    
                    cursor.execute('''
                        INSERT INTO proposals (id, tenant_id, type, title, description, proposed_action, permission_tier, status, created_at)
                        VALUES (?, ?, 'contribution_request', ?, ?, 'Contribute to Role Vault', 'confirm', 'pending', ?)
                    ''', (str(uuid.uuid4()), tenant_id, f"Share workflow: {wf_name}?", "Nous detected a workflow pattern. Contributing helps standardize this process for your team. Only structure is shared, never content.", int(time.time())))
                    
                    stats["documented"] += 1
                except Exception as e:
                    print(f"Error documenting workflow: {e}")
                
            elif act_type == "AUTOMATE":
                try:
                    sys_prompt = f"Write a Python automation script that automates this workflow: {action.get('workflow_description')}. The script should be runnable on Windows, use only stdlib + pyperclip + pygetwindow, include comments explaining each step, and print what it's doing."
                    if client:
                        resp = client.messages.create(
                            model="claude-haiku-4-5-20251001",
                            max_tokens=2000,
                            messages=[{"role": "user", "content": sys_prompt}]
                        )
                        script_content = resp.content[0].text
                    else:
                        script_content = "print('done')"
                    if script_content.startswith("```python"):
                        script_content = script_content[9:]
                    elif script_content.startswith("```"):
                        script_content = script_content[3:]
                    if script_content.endswith("```"):
                        script_content = script_content[:-3]
                        
                    os.makedirs("automations/pending", exist_ok=True)
                    script_path = f"automations/pending/{snake_name}.py"
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(script_content.strip())
                    
                    # Save skill to database
                    from platform_core.intelligence.skills_engine import save_skill, run_and_heal_skill
                    save_skill(
                        name=snake_name, 
                        description=action.get("workflow_description", "No description"), 
                        code_content=script_content, 
                        tenant_id=tenant_id
                    )
                    
                    # Test run/execute the skill to demonstrate the learning and healing loop
                    print(f"[WorkflowAgent] Test running generated skill '{snake_name}' to check for errors...")
                    run_and_heal_skill(snake_name, script_content, tenant_id)
                    
                    # Estimate hours logic
                    # Just hardcode to 2.0 for mock fallback if not in dict
                    hours_saved = 2.0
                    
                    cursor.execute('''
                        INSERT INTO pending_automations (id, tenant_id, workflow_name, script_path, estimated_hours_saved_per_week, status, created_at)
                        VALUES (?, ?, ?, ?, ?, 'pending_review', ?)
                    ''', (str(uuid.uuid4()), tenant_id, wf_name, script_path, hours_saved, int(time.time())))
                    
                    cursor.execute('''
                        INSERT INTO pending_approvals (id, plan_id, step_id, tool_name, params_summary, status, tenant_id, created_at)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                    ''', (str(uuid.uuid4()), "automation_plan", "step_1", "deploy_automation", f"Review script for {wf_name}", tenant_id, int(time.time())))
                    
                    toast_tool = registry.get("notification_tool.toast")
                    if toast_tool:
                        toast_tool.execute({"title": "Nous", "message": f"New automation ready: {wf_name}"}, tenant_id)
                    stats["automations_queued"] += 1
                except Exception as e:
                    print(f"Error automating workflow: {e}")
                
            elif act_type == "ALERT":
                cursor.execute('''
                    INSERT INTO alerts (id, tenant_id, severity, title, description, created_at, status)
                    VALUES (?, ?, 'medium', ?, ?, ?, 'unread')
                ''', (str(uuid.uuid4()), tenant_id, f"Workflow needs attention: {wf_name}", action.get("rationale"), int(time.time())))
                stats["alerts_created"] += 1
                
        conn.commit()
        conn.close()
        return stats
        
    def learn(self, result, feedback):
        pass
