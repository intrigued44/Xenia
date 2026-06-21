import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from platform_core.server import app

client = TestClient(app)
HEADERS = {"x-api-key": "sk-test-key-123"}
import os
os.environ["DEV_API_KEY"] = "sk-test-key-123"
os.environ["ENV"] = "development"

from client.db import init_db
init_db()
from platform_core.intelligence.graph import init_graph
init_graph()

def test_health():
    response = client.get("/v1/health")
    assert response.status_code == 200

def test_events_flow():
    # POST event
    payload = {
        "event_type": "click",
        "source_system": "browser",
        "context": {"url": "https://google.com"},
        "user_id": "test_user"
    }
    response = client.post("/v1/events", json=payload, headers=HEADERS)
    assert response.status_code == 200
    assert "event_id" in response.json()

    # GET events
    response = client.get("/v1/events", headers=HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_sessions_and_workflows():
    response = client.get("/v1/sessions", headers=HEADERS)
    assert response.status_code == 200
    
    response = client.get("/v1/workflows", headers=HEADERS)
    assert response.status_code == 200

@patch("platform_core.server.classify_all_patterns", create=True)
def test_intelligence_endpoints(mock_classify):
    mock_classify.return_value = []
    endpoints = [
        "/v1/intelligence/patterns",
        "/v1/intelligence/graph",
        "/v1/intelligence/classifier"
    ]
    for ep in endpoints:
        response = client.get(ep, headers=HEADERS)
        assert response.status_code == 200

    response = client.post("/v1/intelligence/run-agents", headers=HEADERS)
    assert response.status_code == 200

def test_vaults_endpoints():
    response = client.get("/v1/vaults/summary", headers=HEADERS)
    assert response.status_code == 200
    
    response = client.get("/v1/vaults/personal", headers=HEADERS)
    assert response.status_code == 200
    
    response = client.get("/v1/vaults/contributions/pending", headers=HEADERS)
    assert response.status_code == 200

from unittest.mock import patch
from platform_core.orchestration.engine import Plan

@patch("platform_core.server.planner.create_plan")
@patch("platform_core.server.get_connection")
def test_plan_execution(mock_get_conn, mock_create_plan):
    # Mock the returned plan
    mock_plan = Plan(id="test_plan_id", goal="test_goal", tenant_id="local", steps=[])
    mock_create_plan.return_value = mock_plan
    
    # Mock DB row
    import json
    class MockCursor:
        def execute(self, *args, **kwargs): pass
        def fetchone(self): return [json.dumps({"id": "test_plan_id", "goal": "test_goal", "tenant_id": "local", "steps": []})]
    
    class MockConn:
        def cursor(self): return MockCursor()
        def close(self): pass
        
    mock_get_conn.return_value = MockConn()
    
    # Create plan
    response = client.post("/v1/plans?goal=test_goal", headers=HEADERS)
    assert response.status_code == 200
    plan_id = response.json().get("plan_id")
    assert plan_id is not None
    
    # Execute plan
    response = client.post(f"/v1/plans/{plan_id}/execute", headers=HEADERS)
    assert response.status_code == 200

def test_other_get_endpoints():
    get_endpoints = [
        "/v1/approvals",
        "/v1/proposals",
        "/v1/alerts",
        "/v1/templates",
        "/v1/audit",
        "/v1/mobile/briefing",
        "/v1/mobile/approvals",
        "/v1/mobile/alerts",
        "/v1/mydata",
        "/v1/department/engineering",
        "/v1/me/profile",
        "/v1/me/export",
        "/v1/performance/team",
        "/v1/dashboards/types",
        "/v1/onboarding/brief",
        "/v1/onboarding/90-day-report",
        "/v1/management/insights"
    ]
    for ep in get_endpoints:
        response = client.get(ep, headers=HEADERS)
        # We just want to make sure it doesn't 500 error. 
        # Some might return 401/403/404 if data missing, but we shouldn't see 500 crashes
        assert response.status_code < 500, f"Endpoint {ep} crashed with {response.status_code}"

def test_query_endpoints():
    response = client.get("/v1/query?q=hello", headers=HEADERS)
    assert response.status_code == 200

    response = client.post("/v1/mobile/query?q=hello", headers=HEADERS)
    assert response.status_code == 200

def test_save_automation():
    payload = {
        "name": "test_saved_rpa_script",
        "description": "Verify script saving",
        "code_content": "print('Hello automation')"
    }
    response = client.post("/v1/automations", json=payload, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "saved"
    
    # Check if registered as pending skill
    response = client.get("/v1/automations/pending", headers=HEADERS)
    assert response.status_code == 200
    pending = response.json().get("pending_automations", [])
    assert any(x["name"] == "test_saved_rpa_script" for x in pending)

