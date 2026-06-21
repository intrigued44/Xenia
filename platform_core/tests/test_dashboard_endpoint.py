import pytest
from client.db import init_db, get_connection
from platform_core.server import app
from fastapi.testclient import TestClient

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions")
    c.execute("DELETE FROM workflows")
    c.execute("DELETE FROM alerts")
    c.execute("DELETE FROM window_logs")
    c.execute("DELETE FROM proposals")
    
    # Add minimal test data
    c.execute("INSERT INTO workflows (id, tenant_id, name, automation_potential) VALUES ('w1', 'local', 'W1', 0.9)")
    c.execute("INSERT INTO workflows (id, tenant_id, name, automation_potential) VALUES ('w2', 'local', 'W2', 0.5)")
    c.execute("INSERT INTO workflows (id, tenant_id, name, automation_potential) VALUES ('w3', 'local', 'W3', 0.2)")
    c.execute("INSERT INTO alerts (id, tenant_id, status) VALUES ('a1', 'local', 'new')")
    c.execute("INSERT INTO proposals (id, tenant_id, status) VALUES ('p1', 'local', 'pending')")
    
    conn.commit()
    conn.close()

def test_dashboard_endpoint():
    response = client.get("/v1/dashboard/all")
    assert response.status_code == 200
    data = response.json()
    
    assert "health_score" in data
    assert "app_usage" in data
    assert "workflows" in data
    assert "proposals" in data
    assert "alerts" in data
    
    assert len(data["workflows"]) == 3
    # Check that classifier actions are attached
    actions = {w["name"]: w.get("recommended_action") for w in data["workflows"]}
    assert actions["W1"] == "AUTOMATE"
    assert actions["W2"] == "DOCUMENT"
    assert actions["W3"] == "MONITOR"
    
    assert len(data["alerts"]) == 1
    assert len(data["proposals"]) == 1

