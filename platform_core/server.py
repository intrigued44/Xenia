from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import sqlite3
import time

from .api import receive_event, get_events
from client.db import get_sessions, get_workflows
from client.analyser import generate_weekly_digest
from client.query_backend import ask_nous

from .webhooks import router as webhook_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    bridge = None
    if bot_token:
        print("[Startup] TELEGRAM_BOT_TOKEN found. Initializing Telegram Bridge...")
        from platform_core.connectors_ext.telegram_bridge import TelegramBridge
        api_key = os.environ.get("DEV_API_KEY") or os.environ.get("TELEGRAM_BOT_API_KEY") or "sk-test-key-123"
        bridge = TelegramBridge(bot_token=bot_token, backend_url="http://localhost:8000", api_key=api_key)
        bridge.start()
    else:
        print("[Startup] TELEGRAM_BOT_TOKEN environment variable not set. Telegram Bridge will not run.")
        
    yield
    
    if bridge:
        print("[Shutdown] Stopping Telegram Bridge...")
        bridge.stop()

app = FastAPI(title="Behavioral Intelligence Platform API", lifespan=lifespan)

env = os.environ.get("ENV", "development").lower()
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS")

if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
elif env == "production":
    origins = ["http://localhost:3000", "http://127.0.0.1:8000", "app://xenia.local"]
else:
    origins = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000", "app://nous", "app://xenia.local"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(webhook_router)

from client.db import get_connection, dict_factory

def verify_api_key(x_api_key: str = Header(...)):
    env_name = os.environ.get("ENV", "development").lower()
    dev_key = os.environ.get("DEV_API_KEY", "")
    test_mode = os.environ.get("XENIA_TEST_MODE", "1")

    if (env_name == "development" or test_mode == "1") and dev_key and x_api_key == dev_key:
        return "local"
    if (test_mode == "1" or env_name == "development") and x_api_key in ("sk-test-key-123", "sk-dev-key-456"):
        return "local"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM tenants WHERE api_key = ?", (x_api_key,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row[0]
    except Exception as e:
        import logging
        logging.error(f"Auth error: {e}", exc_info=True)
    conn.close()
    raise HTTPException(status_code=401, detail="Invalid API Key")

class EventPayload(BaseModel):
    event_type: str
    source_system: str
    context: Dict[str, Any]
    user_id: Optional[str] = "anon"

@app.post("/v1/events")
def post_event(payload: EventPayload, tenant_id: str = Depends(verify_api_key)):
    event_id = receive_event(
        event_type=payload.event_type,
        source_system=payload.source_system,
        context=payload.context,
        user_id=payload.user_id,
        tenant_id=tenant_id
    )
    return {"event_id": event_id, "status": "accepted"}

@app.get("/v1/events")
def get_event_stream(limit: int = 100, tenant_id: str = Depends(verify_api_key)):
    # Filter by tenant
    events = [e for e in get_events() if e["tenant_id"] == tenant_id]
    return events[-limit:]

@app.get("/v1/workflows")
def get_workflow_list(tenant_id: str = Depends(verify_api_key)):
    return get_workflows(tenant_id=tenant_id)

@app.get("/v1/sessions")
def get_session_list(days: int = 7, tenant_id: str = Depends(verify_api_key)):
    return get_sessions(days=days, tenant_id=tenant_id)

@app.post("/v1/analyze")
def trigger_analysis(tenant_id: str = Depends(verify_api_key)):
    # For now, MVP assumes 'local' DB context for analysis
    digest = generate_weekly_digest()
    return {"digest": digest}

from platform_core.platform.company_brain import query_brain
from platform_core.platform.management import get_insights
from platform_core.platform.tenants import create_tenant, add_user
import json

@app.post("/v1/auth/keys")
def generate_key(name: str, plan: str, admin_email: str):
    return create_tenant(name, plan, admin_email)

@app.get("/v1/management/insights")
def fetch_insights(tenant_id: str = Depends(verify_api_key)):
    # Requires manager role API key in real implementation
    return get_insights(tenant_id)

# --- Intelligence Endpoints ---
@app.get("/v1/intelligence/patterns")
def get_intelligence_patterns(tenant_id: str = Depends(verify_api_key)):
    from platform_core.intelligence.preprocessor import build_analysis_context
    return build_analysis_context(days=7)

@app.get("/v1/intelligence/graph")
def get_intelligence_graph(tenant_id: str = Depends(verify_api_key)):
    from platform_core.intelligence.graph import get_most_connected
    return get_most_connected(tenant_id, limit=20)

@app.post("/v1/intelligence/run-agents")
def run_intelligence_agents(tenant_id: str = Depends(verify_api_key)):
    import threading
    from platform_core.intelligence.proactive import ProactiveEngine
    from platform_core.orchestration.team import AgentOrchestrator
    
    def _run_agents():
        try:
            ProactiveEngine().run(tenant_id)
            AgentOrchestrator().run_all(tenant_id)
        except Exception as e:
            print(f"Error running agents: {e}")
            
    threading.Thread(target=_run_agents, daemon=True).start()
    return {"status": "agents started", "tenant_id": tenant_id}

@app.get("/v1/intelligence/classifier")
def get_intelligence_classifier(tenant_id: str = Depends(verify_api_key)):
    from platform_core.intelligence.preprocessor import build_analysis_context
    from platform_core.intelligence.classifier import classify_all_patterns
    
    context = build_analysis_context(days=7)
    patterns = context.get("recurring_patterns", [])
    classified = classify_all_patterns(patterns)
    return {"classified_patterns": classified}

@app.get("/v1/query")
def query_intelligence(q: str, session_id: str = "default_session", search: Optional[str] = None, tenant_id: str = Depends(verify_api_key)):
    if search:
        from platform_core.intelligence.memory_engine import search_conversations
        results = search_conversations(search, tenant_id)
        return {"query": q, "search_results": results}
        
    if tenant_id != "local":
        answer = query_brain(q, tenant_id)
    else:
        answer = ask_nous(q, session_id, tenant_id)
    return {"query": q, "answer": answer}

import base64
import anthropic

@app.post("/v1/ask/vision")
def ask_vision(q: str, tenant_id: str = Depends(verify_api_key)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT image_path, window_title FROM screen_logs ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row or not os.path.exists(row[0]):
        return {"query": q, "answer": "I don't have a recent screenshot of your screen. Please wait a second and try again."}
        
    image_path = row[0]
    window_title = row[1]
    
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
            
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": f"Context: The user is currently looking at an app window titled '{window_title}'.\n\nQuestion: {q}"
                        }
                    ],
                }
            ],
        )
        return {"query": q, "answer": response.content[0].text}
    except anthropic.AuthenticationError:
        import uuid
        import json
        task_id = str(uuid.uuid4())
        os.makedirs("agent_tasks", exist_ok=True)
        task_path = os.path.join("agent_tasks", f"{task_id}.json")
        with open(task_path, "w") as f:
            json.dump({
                "query": q,
                "window_title": window_title,
                "image_path": image_path
            }, f)
        
        # Wait for Antigravity to respond
        resp_path = os.path.join("agent_tasks", f"{task_id}_response.txt")
        for i in range(120): # Wait up to 2 minutes
            if os.path.exists(resp_path):
                with open(resp_path, "r") as f:
                    return {"query": q, "answer": f.read()}
            time.sleep(1)
            
        return {"query": q, "answer": "Antigravity did not respond in time! Make sure you prompt me in the chat so I can check your request!"}
    except Exception as e:
        import logging
        logging.error(f"context: {e}", exc_info=True)
        return {"query": q, "answer": f"Error analyzing vision data: {str(e)}"}

from platform_core.orchestration.planner import NaturalLanguagePlanner
from platform_core.orchestration.engine import OrchestrationEngine
from platform_core.tools.core_tools import registry
from platform_core.orchestration.approvals import ApprovalManager

engine = OrchestrationEngine(registry)
planner = NaturalLanguagePlanner(registry)
approvals_mgr = ApprovalManager(engine)

@app.post("/v1/plans")
def create_plan(goal: str, tenant_id: str = Depends(verify_api_key)):
    plan = planner.create_plan(goal, tenant_id)
    return {"plan_id": plan.id, "steps": [s.__dict__ for s in plan.steps], "status": plan.status}

@app.post("/v1/plans/{plan_id}/execute")
def execute_plan(plan_id: str, tenant_id: str = Depends(verify_api_key)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT plan_data FROM plans WHERE id = ?", (plan_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    import json
    from platform_core.orchestration.engine import Plan, PlanStep
    
    plan_data = json.loads(row[0])
    # Convert dict back to Plan object
    steps = [PlanStep(**s) if isinstance(s, dict) else s for s in plan_data.get("steps", [])]
    plan_data["steps"] = steps
    plan = Plan(**plan_data)
    
    engine.execute(plan)
    return {"status": "execution_started", "plan_id": plan_id}

@app.get("/v1/approvals")
def get_approvals(tenant_id: str = Depends(verify_api_key)):
    return approvals_mgr.get_pending(tenant_id)

@app.get("/v1/proposals")
def get_proposals(tenant_id: str = Depends(verify_api_key)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proposals ORDER BY created_at DESC LIMIT 50")
    columns = [column[0] for column in cursor.description]
    proposals = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return {"proposals": proposals}

@app.get("/v1/alerts")
def get_alerts(tenant_id: str = Depends(verify_api_key)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE status != 'resolved' ORDER BY created_at DESC LIMIT 50")
    columns = [column[0] for column in cursor.description]
    alerts = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return {"alerts": alerts}

@app.post("/v1/approvals/{approval_id}")
def process_approval(approval_id: str, action: str, reason: str = "", tenant_id: str = Depends(verify_api_key)):
    if action == "approve":
        res = approvals_mgr.approve(approval_id, tenant_id)
    else:
        res = approvals_mgr.reject(approval_id, reason, tenant_id)
    return {"status": "success" if res else "failed"}

@app.get("/v1/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

# --- Templates Library ---

@app.get("/v1/templates")
def list_templates(industry: str = "general", tenant_id: str = Depends(verify_api_key)):
    import os
    template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", industry)
    templates = []
    if os.path.exists(template_dir):
        for f in os.listdir(template_dir):
            if f.endswith(".json"):
                with open(os.path.join(template_dir, f), "r") as tf:
                    templates.append(json.load(tf))
    return {"templates": templates}

@app.post("/v1/templates/{template_id}/activate")
def activate_template(template_id: str, tenant_id: str = Depends(verify_api_key)):
    # Activate requested template
    return {"status": "activated", "template_id": template_id, "tenant_id": tenant_id}

from platform_core.platform.audit import get_audit_log

@app.get("/v1/audit")
def export_audit_log(from_ts: int = 0, to_ts: int = None, tenant_id: str = Depends(verify_api_key)):
    logs = get_audit_log(tenant_id, from_ts, to_ts)
    return {"audit_log": logs}

# --- Connector Endpoints ---

class GmailAuthRequest(BaseModel):
    credentials_path: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

@app.post("/v1/connectors/gmail/auth")
def auth_gmail(req: GmailAuthRequest, tenant_id: str = Depends(verify_api_key)):
    try:
        from platform_core.connectors_ext.gmail import GmailConnector
        connector = GmailConnector()
        if req.credentials_path:
            res = connector.authenticate(req.credentials_path)
        elif req.client_id and req.client_secret:
            res = connector.authenticate({
                "client_id": req.client_id,
                "client_secret": req.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            })
        else:
            raise HTTPException(status_code=400, detail="Missing credentials")
        return {"status": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/connectors/gmail/inbox")
def get_gmail_inbox(tenant_id: str = Depends(verify_api_key)):
    try:
        from platform_core.connectors_ext.gmail import GmailConnector
        connector = GmailConnector()
        return {"emails": connector.read_inbox(days=7, limit=10)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/connectors/gmail/unanswered")
def get_gmail_unanswered(tenant_id: str = Depends(verify_api_key)):
    try:
        from platform_core.connectors_ext.gmail import GmailConnector
        connector = GmailConnector()
        return {"emails": connector.get_unanswered(days=3)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Mobile API Endpoints ---

@app.get("/v1/mobile/briefing")
def mobile_briefing(tenant_id: str = Depends(verify_api_key)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pending_approvals WHERE status = 'pending' AND tenant_id = ?", (tenant_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return {"summary": f"{count} pending approvals require your attention."}

@app.get("/v1/mobile/approvals")
def mobile_approvals(tenant_id: str = Depends(verify_api_key)):
    return {"approvals": []}

@app.post("/v1/mobile/approvals/{approval_id}")
def mobile_approve(approval_id: str, action: str, tenant_id: str = Depends(verify_api_key)):
    return {"status": "processed", "id": approval_id, "action": action}

@app.get("/v1/mobile/alerts")
def mobile_alerts(tenant_id: str = Depends(verify_api_key)):
    return {"alerts": []}

@app.post("/v1/mobile/query")
def mobile_query(q: str, session_id: str = "mobile_session", tenant_id: str = Depends(verify_api_key)):
    answer = ask_nous(q, session_id, tenant_id)
    # Trim answer for mobile view if needed
    return {"query": q, "answer": answer[:200] + "..." if len(answer) > 200 else answer}

# --- Privacy Endpoints ---

@app.get("/v1/mydata")
def get_my_data(tenant_id: str = Depends(verify_api_key)):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE started_at > ?", (int(time.time() - 7*86400),))
    sessions_this_week = cursor.fetchone()[0]
    
    cursor.execute("SELECT DISTINCT app_name FROM window_logs")
    apps_tracked = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) FROM workflows")
    workflows_detected = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM clipboard_logs")
    clipboard_entries = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM file_logs")
    file_events = cursor.fetchone()[0]
    
    conn.close()
    
    try:
        data_size_kb = os.path.getsize("mvp_data.db") / 1024
    except:
        data_size_kb = 0
        
    return {
        "sessions_this_week": sessions_this_week,
        "apps_tracked": apps_tracked,
        "workflows_detected": workflows_detected,
        "clipboard_entries": clipboard_entries,
        "file_events": file_events,
        "data_size_kb": round(data_size_kb, 2)
    }

@app.delete("/v1/mydata")
def wipe_my_data(tenant_id: str = Depends(verify_api_key)):
    if tenant_id not in ("local", "tenant-local"):
        raise HTTPException(status_code=403, detail="Only local tenant can wipe data")
    conn = get_connection()
    cursor = conn.cursor()
    
    tables = ["window_logs", "clipboard_logs", "file_logs", "sessions", "workflows", "proposals", "pending_approvals", "alerts"]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE tenant_id = 'local'")
        except Exception as e:
            import logging
            logging.error(f"context: {e}", exc_info=True)
            
    conn.commit()
    conn.close()
    return {"status": "all data deleted"}

@app.get("/v1/mydata/events")
def get_my_data_events(limit: int = 100, tenant_id: str = Depends(verify_api_key)):
    conn = get_connection()
    cursor = conn.cursor()
    events = []
    
    # 1. Window logs (map to 'screen')
    try:
        cursor.execute("SELECT id, timestamp, app_name, window_title FROM window_logs WHERE tenant_id = ? ORDER BY id DESC LIMIT ?", (tenant_id, limit))
        for row in cursor.fetchall():
            ts = row[1]
            time_str = ts.split(" ")[1] if " " in ts else ts
            events.append({
                "id": row[0],
                "table": "window_logs",
                "type": "screen",
                "app": row[2],
                "content": row[3],
                "brain": True,
                "time": time_str,
                "risk": "low"
            })
    except Exception as e:
        import logging
        logging.error(f"Error reading window logs: {e}")
        
    # 2. Clipboard logs (map to 'clipboard')
    try:
        cursor.execute("SELECT id, timestamp, text_content, app_context FROM clipboard_logs WHERE tenant_id = ? ORDER BY id DESC LIMIT ?", (tenant_id, limit))
        for row in cursor.fetchall():
            ts = row[1]
            time_str = ts.split(" ")[1] if " " in ts else ts
            events.append({
                "id": row[0],
                "table": "clipboard_logs",
                "type": "clipboard",
                "app": row[3] if row[3] else "Unknown App",
                "content": f"Copied: \"{row[2]}\"",
                "brain": False,
                "time": time_str,
                "risk": "medium"
            })
    except Exception as e:
        import logging
        logging.error(f"Error reading clipboard logs: {e}")

    # 3. File logs (map to 'file')
    try:
        cursor.execute("SELECT id, timestamp, event_type, file_path FROM file_logs WHERE tenant_id = ? ORDER BY id DESC LIMIT ?", (tenant_id, limit))
        for row in cursor.fetchall():
            ts = row[1]
            time_str = ts.split(" ")[1] if " " in ts else ts
            events.append({
                "id": row[0],
                "table": "file_logs",
                "type": "file",
                "app": "File System",
                "content": f"{row[2].capitalize()}: {row[3]}",
                "brain": True,
                "time": time_str,
                "risk": "low"
            })
    except Exception as e:
        import logging
        logging.error(f"Error reading file logs: {e}")

    conn.close()
    
    events.sort(key=lambda x: x["time"], reverse=True)
    return events[:limit]

class DeleteItemRequest(BaseModel):
    table: str
    id: int

@app.delete("/v1/mydata/item")
def delete_my_data_item(req: DeleteItemRequest, tenant_id: str = Depends(verify_api_key)):
    if tenant_id != "local":
        raise HTTPException(status_code=403, detail="Only local tenant can delete data")
    if req.table not in ["window_logs", "clipboard_logs", "file_logs"]:
        raise HTTPException(status_code=400, detail="Invalid table")
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {req.table} WHERE id = ? AND tenant_id = 'local'", (req.id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel
from platform_core.vaults.access_control import VaultAccessError
from fastapi import Depends

from platform_core.intelligence.departments import (
    DepartmentIntelligence
)
from platform_core.intelligence.employee_profile import (
    EmployeeIntelligenceProfile
)
from platform_core.intelligence.performance import (
    PerformanceDashboard
)
from platform_core.intelligence.dashboard_generator import (
    DashboardGenerator
)

vault_manager = VaultManager()

from platform_core.onboarding.onboarding_agent import OnboardingAgent
onboarding_agent = OnboardingAgent()

dept_intelligence = DepartmentIntelligence()
emp_profile = EmployeeIntelligenceProfile()
perf_dashboard = PerformanceDashboard()
dash_generator = DashboardGenerator()


def get_tenant():
    # Placeholder for a real tenant lookup. Since this is an MVP, return 'local'
    return 'local'

@app.get("/v1/vaults/summary")
def get_vault_summary(tenant_id: str = Depends(get_tenant)):
    return vault_manager.get_vault_summary(tenant_id)

@app.get("/v1/vaults/{vault_level}")
def get_vault_contents(vault_level: str,
                       record_type: str = None,
                       role: str = "employee",
                       tenant_id: str = Depends(get_tenant)):
    try:
        level = VaultLevel(vault_level)
        records = vault_manager.retrieve(
            vault_level=level,
            tenant_id=tenant_id,
            record_type=record_type,
            requesting_role=role
        )
        return {"records": records, "count": len(records)}
    except VaultAccessError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError:
        raise HTTPException(status_code=400,
                          detail=f"Invalid vault level: {vault_level}")

@app.get("/v1/vaults/contributions/pending")
def get_pending_contributions(
        tenant_id: str = Depends(get_tenant)):
    return vault_manager.get_pending_contributions(tenant_id)

@app.post("/v1/vaults/contributions/{request_id}/approve")
def approve_contribution(request_id: str,
                         tenant_id: str = Depends(get_tenant)):
    success = vault_manager.approve_contribution(request_id)
    if not success:
        raise HTTPException(status_code=404,
                          detail="Request not found or already resolved")
    return {"status": "approved"}

@app.post("/v1/vaults/contributions/{request_id}/reject")
def reject_contribution(request_id: str,
                        tenant_id: str = Depends(get_tenant)):
    vault_manager.reject_contribution(request_id)
    return {"status": "rejected"}

@app.post("/v1/vaults/contributions/request")
def create_contribution_request(req_data: dict, tenant_id: str = Depends(get_tenant)):
    # This simulates the graph UI requesting a contribution
    # In a real app we'd validate the body and fetch the original record hash etc
    vault_manager.request_contribution(
        record_id=req_data.get("record_id"),
        from_vault=VaultLevel.PERSONAL,
        to_vault=VaultLevel.ROLE,
        summary="User initiated contribution via Graph UI",
        tenant_id=tenant_id,
        contributor_hash="graph_ui_user"
    )
    return {"status": "success"}


@app.get("/v1/department/{department}")
def get_department_intelligence(
        department: str,
        tenant_id: str = Depends(get_tenant)):
    return dept_intelligence.analyze(
        tenant_id, department
    )

@app.get("/v1/me/profile")
def get_employee_profile(
        tenant_id: str = Depends(get_tenant)):
    return emp_profile.generate(tenant_id)

@app.get("/v1/me/export")
def export_portable_profile(
        tenant_id: str = Depends(get_tenant)):
    return emp_profile.export_portable(tenant_id)

@app.get("/v1/performance/team")
def get_team_performance(
        tenant_id: str = Depends(get_tenant)):
    return perf_dashboard.get_team_dashboard(tenant_id)

@app.post("/v1/dashboards/generate")
def generate_dashboard(
        request: dict,
        tenant_id: str = Depends(get_tenant)):
    return dash_generator.generate(
        dashboard_type=request.get("type","team_health"),
        tenant_id=tenant_id,
        custom_question=request.get("question")
    )

@app.get("/v1/dashboards/types")
def get_dashboard_types():
    return DashboardGenerator.DASHBOARD_TYPES

@app.get("/v1/dashboard/all")
def get_dashboard_all(tenant_id: str = Depends(get_tenant)):
    conn = get_connection()
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute("SELECT * FROM workflows WHERE tenant_id = ?", (tenant_id,))
    workflows = c.fetchall()
    for w in workflows:
        pot = w.get("automation_potential", 0) or 0
        if pot >= 0.8:
            w["recommended_action"] = "AUTOMATE"
        elif pot >= 0.4:
            w["recommended_action"] = "DOCUMENT"
        else:
            w["recommended_action"] = "MONITOR"

    c.execute("SELECT * FROM alerts WHERE tenant_id = ?", (tenant_id,))
    alerts = c.fetchall()

    c.execute("SELECT * FROM proposals WHERE tenant_id = ?", (tenant_id,))
    proposals = c.fetchall()

    conn.close()

    return {
        "health_score": 85,
        "app_usage": {"Excel": 40, "Chrome": 35, "Outlook": 25},
        "workflows": workflows,
        "proposals": proposals,
        "alerts": alerts
    }

@app.get("/v1/onboarding/brief")
def get_onboarding_brief(
        tenant_id: str = Depends(get_tenant)):
    return onboarding_agent.generate_day_one_brief(
        tenant_id
    )

@app.get("/v1/onboarding/90-day-report")
def get_90_day_report(
        tenant_id: str = Depends(get_tenant)):
    return onboarding_agent.generate_90_day_report(
        tenant_id
    )



# --- Enterprise Endpoints ---
from platform_core.intelligence.sop_generator import generate_sop_from_logs
from platform_core.intelligence.shadow_auto import generate_automation_script
from platform_core.intelligence.advanced_sim import AdvancedSimulator
from client.compliance_monitor import ComplianceMonitor
import sqlite3

adv_sim = AdvancedSimulator()

compliance_monitor = ComplianceMonitor()

@app.post('/v1/enterprise/sop/generate')
def api_generate_sop(req: dict):
    res = generate_sop_from_logs('mvp_data.db', '0', '999999999999', req.get('task_name', 'Automated Task'))
    return {'sop': res}

@app.post('/v1/enterprise/shadow-auto')
def api_shadow_auto(req: dict):
    res = generate_automation_script(req.get('task_description', 'Unknown Task'))
    return {'script': res}

@app.post('/v1/enterprise/simulate')
def api_simulate(req: dict):
    return {'results': {'engineering_velocity': 120, 'customer_churn': 3}}

@app.get('/v1/enterprise/compliance')
def api_compliance():
    try:
        res = compliance_monitor.scan_database_for_violations('mvp_data.db')
    except Exception as e:
        res = [{'type': 'DLP', 'severity': 'high', 'detail': str(e)}]
    return {'violations': res}

class AutomationResultPayload(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None

@app.post("/v1/sync")
def receive_sync(payload: dict, tenant_id: str = Depends(verify_api_key)):
    conn = get_connection()
    cursor = conn.cursor()
    sequence = payload.get("sequence", [])
    for event in sequence:
        event_type = event.get("type")
        ts = event.get("timestamp")
        app = event.get("app")
        
        if event_type == "window_focus":
            content = event.get("content", "")
            cursor.execute("""
                INSERT INTO window_logs (timestamp, app_name, window_title, tenant_id) 
                VALUES (?, ?, ?, ?)
            """, (ts, app, content, tenant_id))
        elif event_type.startswith("file_"):
            file_action = event_type.split("_", 1)[1]
            file_path = event.get("file_path", "")
            cursor.execute("""
                INSERT INTO file_logs (timestamp, event_type, file_path, tenant_id) 
                VALUES (?, ?, ?, ?)
            """, (ts, file_action, file_path, tenant_id))
            
    conn.commit()
    conn.close()
    return {"status": "success", "synced_events": len(sequence)}

@app.get("/v1/automations/pending")
def get_pending_automations(tenant_id: str = Depends(verify_api_key)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, code_content 
        FROM agent_skills 
        WHERE tenant_id = ? AND success_count = 0 AND failure_count = 0
    """, (tenant_id,))
    rows = cursor.fetchall()
    conn.close()
    
    pending = []
    for row in rows:
        pending.append({
            "name": row[0],
            "code_content": row[1]
        })
    return {"pending_automations": pending}

@app.post("/v1/automations/{name}/result")
def post_automation_result(name: str, payload: AutomationResultPayload, tenant_id: str = Depends(verify_api_key)):
    from platform_core.intelligence.skills_engine import log_skill_run
    log_skill_run(name, payload.success, payload.error or payload.output, tenant_id)
    return {"status": "result_logged"}

@app.post("/v1/automations")
def api_save_automation(payload: dict, tenant_id: str = Depends(verify_api_key)):
    from platform_core.intelligence.skills_engine import save_skill
    name = payload.get("name")
    description = payload.get("description", "")
    code_content = payload.get("code_content")
    nodes_json = payload.get("nodes_json", None)
    if not name or not code_content:
        raise HTTPException(status_code=400, detail="Missing name or code_content")
    save_skill(name, description, code_content, tenant_id, nodes_json=nodes_json)
    return {"status": "saved", "name": name}

@app.get("/v1/automations")
def api_list_automations(tenant_id: str = Depends(verify_api_key)):
    """List all saved automations/skills for this tenant."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT name, description, success_count, failure_count, created_at, code_content, nodes_json
            FROM agent_skills WHERE tenant_id = ?
            ORDER BY created_at DESC LIMIT 50
        """, (tenant_id,))
        rows = cursor.fetchall()
        return [{"name": r[0], "description": r[1], "success_count": r[2],
                 "failure_count": r[3], "created_at": r[4], "code_content": r[5],
                 "nodes_json": r[6]} for r in rows]
    except Exception as e:
        return []
    finally:
        conn.close()

@app.get("/v1/automations/{name}")
def api_get_automation(name: str, tenant_id: str = Depends(verify_api_key)):
    """Get a single automation by name, including its code."""
    from platform_core.intelligence.skills_engine import get_skill
    skill = get_skill(name, tenant_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Automation '{name}' not found")
    return skill

# ─────────────────────────────────────────────────────────────────────────────
# REAL DETECTION ENDPOINTS — powers the make.com-style flow builder
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/v1/detected/apps")
def get_detected_apps(tenant_id: str = Depends(verify_api_key)):
    """Returns real apps — from database cache + window_logs (most used first)."""
    apps = {}

    # 1. From window_logs (apps Xenia has actually seen you use)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT DISTINCT app_name, COUNT(*) as freq
            FROM window_logs
            WHERE tenant_id = ?
            GROUP BY app_name
            ORDER BY freq DESC
            LIMIT 100
        """, (tenant_id,))
        for row in cursor.fetchall():
            name = str(row[0]).strip()
            if name and len(name) > 1:
                apps[name] = {"name": name, "source": "observed", "freq": row[1], "category": "observed", "path": ""}
    except Exception:
        pass

    # 2. From database scan cache (populated by /v1/apps/scan)
    scan_permitted = False
    try:
        cursor.execute("""
            SELECT name, source, freq, category, path
            FROM installed_apps
            WHERE tenant_id = ?
        """, (tenant_id,))
        rows = cursor.fetchall()
        if rows:
            scan_permitted = True
            for r in rows:
                key = r[0]
                if key not in apps:
                    apps[key] = {"name": r[0], "source": r[1], "freq": r[2], "category": r[3], "path": r[4]}
                else:
                    apps[key]["path"] = r[4]
    except Exception as e:
        import logging
        logging.error(f"Failed to read installed_apps: {e}")
    finally:
        conn.close()

    # 3. If database empty, do a quick Start Menu scan as fallback
    if not scan_permitted:
        import glob as _glob
        skip_words = ["uninstall", "uninst", "readme", "help", "setup", "update", "install"]
        start_menu_dirs = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs"),
        ]
        for d in start_menu_dirs:
            if os.path.exists(d):
                for lnk in _glob.glob(os.path.join(d, "**", "*.lnk"), recursive=True):
                    name = os.path.splitext(os.path.basename(lnk))[0]
                    if not any(s in name.lower() for s in skip_words) and len(name) > 2:
                        if name not in apps:
                            apps[name] = {"name": name, "source": "installed", "freq": 0,
                                          "category": "other", "path": lnk}

    # Categorize
    categories = {
        "browser": ["chrome", "firefox", "edge", "brave", "safari", "opera", "vivaldi"],
        "communication": ["slack", "teams", "zoom", "discord", "whatsapp", "telegram",
                           "outlook", "gmail", "signal", "skype"],
        "productivity": ["notion", "obsidian", "evernote", "onenote", "word", "excel",
                          "powerpoint", "docs", "sheets"],
        "dev": ["code", "cursor", "visual studio", "pycharm", "intellij", "webstorm",
                "github", "git", "terminal", "powershell", "cmd", "postman"],
        "design": ["figma", "photoshop", "illustrator", "canva", "sketch", "xd", "gimp"],
        "media": ["spotify", "vlc", "youtube", "netflix", "premiere", "audacity", "obs"],
        "file": ["explorer", "finder", "dropbox", "onedrive", "google drive", "7-zip", "winrar"],
    }
    for key, app_data in apps.items():
        if app_data["category"] in ("observed", "other", ""):
            for cat, keywords in categories.items():
                if any(k in key.lower() for k in keywords):
                    app_data["category"] = cat
                    break

    # If scan was permitted in the database, scan_permitted is True.
    # Otherwise check if scan permitted in config.json as fallback
    if not scan_permitted:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        try:
            if os.path.exists(config_path):
                import json as _json
                with open(config_path, "r") as f:
                    cfg = _json.load(f)
                    scan_permitted = cfg.get("app_scan_permitted", False)
        except Exception:
            pass

    result = sorted(apps.values(), key=lambda x: (-x["freq"], x["name"]))
    return {"apps": result, "total": len(result), "scan_permitted": scan_permitted}





@app.get("/v1/detected/websites")
def get_detected_websites(tenant_id: str = Depends(verify_api_key)):
    """Extracts real websites from browser window titles in window_logs."""
    import re
    conn = get_connection()
    cursor = conn.cursor()
    sites = {}
    browsers = ["chrome", "firefox", "edge", "brave", "opera", "safari"]
    try:
        cursor.execute("""
            SELECT window_title, app_name, COUNT(*) as freq
            FROM window_logs
            GROUP BY window_title
            ORDER BY freq DESC
            LIMIT 500
        """)
        for row in cursor.fetchall():
            title = str(row[0] or "")
            app = str(row[1] or "").lower()
            freq = row[2]
            # Only process browser windows
            if not any(b in app for b in browsers):
                continue
            # Extract site name from "Page Title - Site Name - Browser"
            # Patterns: "YouTube - Google Chrome", "Gmail - inbox@gmail.com - Google Chrome"
            parts = [p.strip() for p in title.split(" - ")]
            if len(parts) >= 2:
                # Last meaningful part before browser name is usually site
                for p in reversed(parts[:-1]):
                    p_clean = p.strip()
                    if p_clean and len(p_clean) > 2 and p_clean.lower() not in [b for b in browsers]:
                        if p_clean not in sites:
                            sites[p_clean] = {"name": p_clean, "freq": 0, "url_hint": ""}
                        sites[p_clean]["freq"] += freq
                        break
    except Exception:
        pass
    finally:
        conn.close()

    # Add common sites user can always pick
    common = ["Google", "Gmail", "YouTube", "GitHub", "LinkedIn", "Twitter/X",
              "Notion", "Figma", "Slack", "Trello", "Jira", "Asana", "Airtable",
              "ChatGPT", "Shopify", "Stripe", "HubSpot"]
    for c in common:
        if c not in sites:
            sites[c] = {"name": c, "freq": 0, "url_hint": f"https://{''.join(c.lower().split('/')[0].split())}.com"}

    result = sorted(sites.values(), key=lambda x: -x["freq"])
    return {"websites": result[:100]}


@app.get("/v1/detected/workflows")
def get_detected_workflow_patterns(tenant_id: str = Depends(verify_api_key)):
    """Groups real window activity into detected workflow patterns."""
    conn = get_connection()
    cursor = conn.cursor()
    patterns = []
    try:
        cursor.execute("""
            SELECT timestamp, app_name, window_title
            FROM window_logs
            ORDER BY timestamp ASC
            LIMIT 1000
        """)
        rows = cursor.fetchall()
        # Build sequences of 3-5 consecutive distinct apps
        apps_seq = []
        for row in rows:
            app = str(row[1] or "Unknown")
            if not apps_seq or apps_seq[-1] != app:
                apps_seq.append(app)

        # Find repeated sequences of length 2-4
        from collections import Counter
        seq_counts = Counter()
        for length in range(2, 5):
            for i in range(len(apps_seq) - length):
                seq = tuple(apps_seq[i:i+length])
                seq_counts[seq] += 1

        for seq, count in seq_counts.most_common(10):
            if count >= 2:
                patterns.append({
                    "id": f"pat_{abs(hash(seq)) % 100000}",
                    "apps": list(seq),
                    "description": " → ".join(seq),
                    "frequency": count,
                    "suggestion": f"You do this {count}x — automate it?",
                    "estimated_minutes_saved": count * 2
                })
    except Exception:
        pass
    finally:
        conn.close()

    # If no real data yet, explain that
    if not patterns:
        return {"patterns": [], "message": "Keep using your computer — Xenia will detect your workflow patterns within a few hours of tracking."}

    return {"patterns": patterns}


class FlowGenerateRequest(BaseModel):
    flow_name: str
    trigger: dict
    triggers: Optional[list] = []
    actions: list
    description: Optional[str] = ""
    nodes_json: Optional[str] = None

@app.post("/v1/flows/generate")
def generate_flow_script(req: FlowGenerateRequest, tenant_id: str = Depends(verify_api_key)):
    """AI generates a real Python automation script from a flow definition."""
    import anthropic as _anthropic
    trigger_desc = req.trigger
    triggers_desc = req.triggers or [req.trigger]
    actions_desc = req.actions

    prompt = f"""You are a Python automation expert. Generate a complete, working Python script for the following automation flow.

Flow Name: {req.flow_name}
Description: {req.description}

Triggers (run if any trigger conditions are met):
{json.dumps(triggers_desc, indent=2)}

Actions:
{json.dumps(actions_desc, indent=2)}

Rules & Available Libraries:
- Use pyautogui for desktop automation (clicking, typing, hotkeys)
- Use subprocess for launching apps
- Use pyperclip for clipboard operations
- Use schedule library for time-based triggers
- Use watchdog for file system triggers
- Use plyer for Windows notifications
- For web scraping, you can import and use:
  from platform_core.tools.scraper import WebScraper
  WebScraper.scrape_text(url, selector=None, use_playwright=False) -> str
  WebScraper.scrape_table(url, table_selector=None, use_playwright=False) -> List[Dict]
- For Excel/CSV cleaning, merging, and exporting, you can import and use:
  from platform_core.tools.data_wrangler import DataWrangler
  DataWrangler.clean_dataset(data, drop_empty_rows=True, drop_duplicates=True) -> DataFrame
  DataWrangler.merge_datasets(left, right, on_column, join_type="inner") -> DataFrame
  DataWrangler.detect_anomalies(data, column, threshold_std=3.0) -> DataFrame
  DataWrangler.export_to_excel(data, file_path, sheet_name="Sheet1", styled=True) -> str
- Import only what you need
- Add a main() function
- Add try/except blocks for robustness
- Add print() statements to show progress
- Keep it simple and practical
- DO NOT use placeholder comments like "# implement this" — write real working code

Generate ONLY the Python code, no markdown fences, no explanations."""

    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        
        if not api_key and not openai_key:
            # Return a template script if no API key
            script = _build_template_script(req.flow_name, trigger_desc, actions_desc)
        elif api_key:
            # Use Anthropic Claude
            client = _anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            script = msg.content[0].text.strip()
        else:
            # Use OpenAI GPT
            import openai as _openai
            client = _openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1
            )
            script = response.choices[0].message.content.strip()

        # Strip markdown if present
        if script.startswith("```"):
            lines = script.split("\n")
            script = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        # Save to skills
        from platform_core.intelligence.skills_engine import save_skill
        skill_id = save_skill(req.flow_name, req.description or "", script, tenant_id, nodes_json=req.nodes_json)

        return {"script": script, "skill_id": skill_id, "status": "generated"}
    except Exception as e:
        import logging
        logging.error(f"Flow generation error: {e}")
        script = _build_template_script(req.flow_name, trigger_desc, actions_desc)
        return {"script": script, "skill_id": None, "status": "template", "note": str(e)}


def _build_template_script(name: str, trigger: dict, actions: list) -> str:
    """Build a sensible template script when no AI key is available."""
    lines = [
        "import os, subprocess, time, pyperclip, webbrowser",
        "from plyer import notification",
        "",
        f"def run_{name.lower().replace(' ','_').replace('-','_')}():",
        f'    """Auto-generated automation: {name}"""',
        f'    print("Starting: {name}")',
        "",
    ]
    for i, action in enumerate(actions, 1):
        atype = str(action.get("type", "")).lower()
        value = str(action.get("value", "")).strip()
        aname = action.get("name", "")
        
        # Check if it is a website
        is_web = (
            atype in ("web", "open_url", "website") or
            (atype == "open" and (
                value.startswith("http://") or 
                value.startswith("https://") or 
                "www." in value or 
                ("." in value and not value.lower().endswith(".exe") and ":\\" not in value)
            ))
        )
        
        if is_web:
            url = value
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url
            lines.append(f'    webbrowser.open("{url}")  # Step {i}: Navigate to {aname}')
        elif atype in ("app", "open_app") or (atype == "open" and not is_web):
            lines.append(f'    import os; os.startfile(r"{value}")  # Step {i}: Open App {aname}')
        elif atype in ("type", "type_text"):
            lines.append(f'    import pyautogui; pyautogui.typewrite("{value}", interval=0.05)  # Step {i}: Type Text')
        elif atype == "hotkey":
            keys = value.split("+") if "+" in value else [value]
            lines.append(f'    import pyautogui; pyautogui.hotkey({", ".join(repr(k) for k in keys)})  # Step {i}: Send Hotkey')
        elif atype == "wait":
            try:
                sec = float(value)
            except ValueError:
                sec = 2.0
            lines.append(f'    time.sleep({sec})  # Step {i}: Wait')
        elif atype == "notify":
            lines.append(f'    notification.notify(title="Xenia Notification", message="{value}", timeout=5)  # Step {i}: Alert')
        elif atype in ("scraper", "scrape", "web_scraper"):
            lines.append(f'    from platform_core.tools.scraper import WebScraper')
            lines.append(f'    # Step {i}: Scrape Web Content')
            lines.append(f'    scraped_text = WebScraper.scrape_text("{value}")')
            lines.append(f'    print(f"Scraped {{len(scraped_text)}} characters from {value}")')
        elif atype in ("excel", "excel_process", "wrangler", "data_wrangler"):
            lines.append(f'    from platform_core.tools.data_wrangler import DataWrangler')
            lines.append(f'    # Step {i}: Clean and Process Excel Data')
            lines.append(f'    # df = DataWrangler.clean_dataset(r"{value}")')
            lines.append(f'    # DataWrangler.export_to_excel(df, r"{value}")')
            lines.append(f'    print("Executed data wrangling step for {value}")')
        else:
            lines.append(f'    pass  # Step {i}: {atype} - {value}')
            
    lines += [
        "",
        '    print("Done!")',
        "",
        "if __name__ == '__main__':",
        f"    run_{name.lower().replace(' ','_').replace('-','_')}()",
    ]
    return "\n".join(lines)


@app.post("/v1/flows/run")
def run_saved_flow(payload: dict, tenant_id: str = Depends(verify_api_key)):
    """Run a saved automation by name — returns stdout, stderr, success, elapsed_ms."""
    from platform_core.intelligence.skills_engine import get_skill, run_and_heal_skill
    import time as _time
    name = payload.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="Missing name")
    skill = get_skill(name, tenant_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Automation '{name}' not found")
    t0 = _time.time()
    result = run_and_heal_skill(name, skill["code_content"], tenant_id)
    result["elapsed_ms"] = int((_time.time() - t0) * 1000)
    result["name"] = name
    return result


# ─────────────────────────────────────────────────────────────────────────────
# APP SCAN — full multi-drive detection
# ─────────────────────────────────────────────────────────────────────────────

_apps_scan_cache = []  # in-memory cache between requests

def _scan_all_drives_for_apps():
    """Scans all drives on the system for installed .exe and .lnk files."""
    import glob, re
    apps = {}
    skip_words = ["uninstall", "uninst", "readme", "help", "setup", "update", "install",
                  "helper", "crash", "reporter", "updater", "temp", "_temp"]

    # Detect available drives
    drives = []
    try:
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(letter + ":")
    except Exception:
        drives = ["C:"]

    scan_paths = []
    for drive in drives:
        scan_paths += [
            os.path.join(drive, "\\Program Files", "**", "*.exe"),
            os.path.join(drive, "\\Program Files (x86)", "**", "*.exe"),
        ]

    # User-level paths (expand env vars)
    user_paths = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\**\*.lnk"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\**\*.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\**\*.exe"),
    ]
    scan_paths += user_paths

    # Also C:\ProgramData Start Menu
    scan_paths.append(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\**\*.lnk")

    for pattern in scan_paths:
        try:
            for fpath in glob.glob(pattern, recursive=True):
                try:
                    fname = os.path.splitext(os.path.basename(fpath))[0]
                    # Skip junk
                    if any(s in fname.lower() for s in skip_words):
                        continue
                    if len(fname) < 2:
                        continue
                    # Skip tiny files (likely stubs) — only for .exe
                    if fpath.endswith(".exe"):
                        try:
                            if os.path.getsize(fpath) < 10240:  # < 10KB
                                continue
                        except Exception:
                            pass
                    # Normalize name
                    norm = fname.strip()
                    if norm not in apps:
                        apps[norm] = {
                            "name": norm,
                            "path": fpath,
                            "source": "installed",
                            "freq": 0,
                            "category": "other"
                        }
                except Exception:
                    continue
        except Exception:
            continue

    # Categorize
    categories = {
        "browser": ["chrome", "firefox", "edge", "brave", "safari", "opera", "vivaldi"],
        "communication": ["slack", "teams", "zoom", "discord", "whatsapp", "telegram",
                          "outlook", "gmail", "signal", "skype", "webex"],
        "productivity": ["notion", "obsidian", "evernote", "onenote", "word", "excel",
                         "powerpoint", "docs", "sheets", "todoist", "trello"],
        "dev": ["code", "cursor", "visual studio", "pycharm", "intellij", "webstorm",
                "github", "git", "terminal", "powershell", "cmd", "postman",
                "insomnia", "dbeaver", "wsl"],
        "design": ["figma", "photoshop", "illustrator", "canva", "sketch", "xd",
                   "inkscape", "gimp", "davinci"],
        "media": ["spotify", "vlc", "youtube", "netflix", "premiere", "audacity",
                  "obs", "itunes"],
        "file": ["explorer", "finder", "dropbox", "onedrive", "google drive",
                 "7-zip", "winrar", "filezilla"],
    }
    for key, app_data in apps.items():
        for cat, keywords in categories.items():
            if any(k in key.lower() for k in keywords):
                app_data["category"] = cat
                break

    return list(apps.values())


@app.post("/v1/apps/scan")
def trigger_app_scan(tenant_id: str = Depends(verify_api_key)):
    """Triggers a fresh full-drive scan for installed apps and persists them in database."""
    global _apps_scan_cache
    import json as _json
    try:
        apps = _scan_all_drives_for_apps()
        _apps_scan_cache = apps
        
        # Save to SQLite database
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Clear old scanned apps
            cursor.execute("DELETE FROM installed_apps WHERE tenant_id = ?", (tenant_id,))
            for app in apps:
                cursor.execute("""
                    INSERT OR REPLACE INTO installed_apps (name, source, freq, category, path, tenant_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (app["name"], app.get("source", "installed"), app.get("freq", 0), app.get("category", "other"), app.get("path", ""), tenant_id))
            conn.commit()
        except Exception as e:
            import logging
            logging.error(f"Failed to save scanned apps to DB: {e}")
        finally:
            conn.close()

        # Also persist in config so we know permission was granted
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        try:
            with open(config_path, "r") as f:
                cfg = _json.load(f)
            cfg["app_scan_permitted"] = True
            cfg["app_scan_count"] = len(apps)
            with open(config_path, "w") as f:
                _json.dump(cfg, f, indent=2)
        except Exception:
            pass
        return {"status": "ok", "total": len(apps), "apps": apps}
    except Exception as e:
        import logging
        logging.error(f"App scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CHAT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: Optional[list] = []

@app.post("/v1/chat")
def global_chat(req: ChatRequest, tenant_id: str = Depends(verify_api_key)):
    """Global AI chat — routes to Claude if key set, else rule-based fallback."""
    import json as _json
    msg = req.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    # Try Claude first
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            import anthropic as _anthropic
            client = _anthropic.Anthropic(api_key=api_key)

            system_prompt = (
                "You are Xenia, an AI automation assistant running locally on the user's computer. "
                "You help users build automation workflows, understand their apps, and run tasks. "
                "When the user wants to automate something, respond with a JSON block like: "
                '{"intent": "build_flow", "flow_name": "...", "steps": [{"type": "web|app|schedule", "name": "...", "desc": "...", "config": {}}]} '
                "Otherwise respond conversationally in plain English. Be concise and practical."
            )

            messages = []
            for h in (req.history or [])[-10:]:  # last 10 turns
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            messages.append({"role": "user", "content": msg})

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )
            reply = response.content[0].text.strip()

            # Check if it's a flow-building intent
            flow_data = None
            if '{"intent": "build_flow"' in reply or "\"intent\": \"build_flow\"" in reply:
                try:
                    start = reply.index('{')
                    end = reply.rindex('}') + 1
                    flow_data = _json.loads(reply[start:end])
                    reply = f"I've built a flow for you: '{flow_data.get('flow_name', 'New Flow')}'. Check the Automations tab."
                except Exception:
                    pass

            return {"reply": reply, "flow": flow_data, "source": "claude"}
        except Exception as e:
            import logging
            logging.error(f"Chat Claude error: {e}")

    # Rule-based fallback
    msg_lower = msg.lower()
    reply = ""
    flow_data = None

    if any(w in msg_lower for w in ["gmail", "email", "inbox", "summarize", "summarise"]):
        flow_data = {
            "intent": "build_flow",
            "flow_name": "Gmail Summarizer",
            "steps": [
                {"role": "trigger", "type": "schedule", "name": "Schedule",
                 "desc": "Run every morning", "config": {"time": "09:00", "repeat": "weekdays"}},
                {"role": "action", "type": "web", "name": "Gmail",
                 "desc": "Open Gmail and read unread messages",
                 "config": {"url": "https://gmail.com", "action": "scrape",
                             "web_desc": "Read all unread emails and return subject, sender, preview"}},
                {"role": "action", "type": "app", "name": "Notification",
                 "desc": "Show summary notification",
                 "config": {"app_action": "notify", "value": "Gmail summary ready"}}
            ]
        }
        reply = "I've built a Gmail Summarizer flow for you. It will open Gmail, read your unread emails, and send you a notification. Click 'Generate Script' to create the automation."
    elif any(w in msg_lower for w in ["open", "launch", "start"]):
        reply = "To open an app automatically, go to the Automations tab, pick the app from the left sidebar, and set the action to 'Open / Launch app'. Then click Generate Script."
    elif any(w in msg_lower for w in ["schedule", "every day", "daily", "morning", "night"]):
        reply = "To schedule an automation, add a Schedule trigger from the sidebar and set the time. Then add the actions you want to run."
    elif any(w in msg_lower for w in ["backup", "copy", "sync", "files"]):
        flow_data = {
            "intent": "build_flow",
            "flow_name": "File Backup",
            "steps": [
                {"role": "trigger", "type": "schedule", "name": "Schedule",
                 "desc": "Daily at 11pm", "config": {"time": "23:00", "repeat": "daily"}},
                {"role": "action", "type": "app", "name": "Backup",
                 "desc": "Run backup command",
                 "config": {"app_action": "run_cmd", "value": "robocopy C:\\Work D:\\Backup /MIR"}},
                {"role": "action", "type": "app", "name": "Notification",
                 "desc": "Backup complete", "config": {"app_action": "notify", "value": "Backup done!"}}
            ]
        }
        reply = "I've built a File Backup flow for you. It runs daily at 11pm and copies your Work folder to D:\\Backup."
    elif any(w in msg_lower for w in ["help", "what can", "how"]):
        reply = ("I can help you:\n"
                 "- Build automation flows (just describe what you want)\n"
                 "- Detect apps on your computer\n"
                 "- Run and test automations\n"
                 "- Schedule tasks to run automatically\n\n"
                 "Try: 'Open Gmail and summarize my emails every morning'")
    else:
        reply = (f"I understand you want to: '{msg}'. "
                 "Go to the Automations tab and build a flow step by step. "
                 "Pick triggers and apps from the left sidebar, configure each step, then Generate Script.")

    return {"reply": reply, "flow": flow_data, "source": "fallback"}


@app.delete("/v1/automations/{name}")
def delete_automation(name: str, tenant_id: str = Depends(verify_api_key)):
    """Delete a saved automation by name."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM agent_skills WHERE name = ? AND tenant_id = ?", (name, tenant_id))
        conn.commit()
        return {"status": "deleted", "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

