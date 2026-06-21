import pytest
from client.db import init_db, get_connection
from platform_core.intelligence.retrieval import DataRetriever

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM window_logs")
    c.execute("DELETE FROM workflows")
    c.execute("DELETE FROM alerts")
    c.execute("DELETE FROM proposals")
    c.execute("DELETE FROM sessions")
    c.execute("DELETE FROM clipboard_logs")
    c.execute("DELETE FROM file_logs")
    
    # Insert basic test data
    c.execute("INSERT INTO window_logs (app_name, tenant_id, timestamp) VALUES ('Excel', 'test_tenant', datetime('now'))")
    c.execute("INSERT INTO workflows (id, tenant_id, name, automation_potential) VALUES ('w1', 'test_tenant', 'Invoice', 0.8)")
    c.execute("INSERT INTO alerts (id, tenant_id, title, status) VALUES ('a1', 'test_tenant', 'Test Alert', 'new')")
    c.execute("INSERT INTO proposals (id, tenant_id, status, type) VALUES ('p1', 'test_tenant', 'pending', 'automation')")
    c.execute("INSERT INTO sessions (id, tenant_id, automation_score, started_at) VALUES ('s1', 'test_tenant', 0.9, strftime('%s','now'))")
    
    conn.commit()
    conn.close()

def test_intent_classification():
    dr = DataRetriever()
    assert dr._classify_intent("what apps am I using?") == "app_usage"
    assert dr._classify_intent("show me my workflows") == "workflows"
    assert dr._classify_intent("what should we automate?") == "automation"
    assert dr._classify_intent("any active alerts?") == "alerts"
    assert dr._classify_intent("review pending proposals") == "proposals"
    assert dr._classify_intent("what is the team health score") == "health"
    assert dr._classify_intent("show my personal profile") == "profile"
    assert dr._classify_intent("show bottleneck in the graph") == "graph"
    assert dr._classify_intent("hello world") == "general"

def test_density_calculation():
    dr = DataRetriever()
    assert dr._calculate_density(0) == 0.0
    assert dr._calculate_density(3) == 0.2
    assert dr._calculate_density(10) == 0.5
    assert dr._calculate_density(50) == 0.8
    assert dr._calculate_density(150) == 1.0

def test_retrieval_app_usage():
    dr = DataRetriever()
    res = dr.retrieve("app usage", "test_tenant")
    assert res.intent == "app_usage"
    assert "app_usage" in res.data
    assert res.summary_stats["top_app"] == "Excel"
    assert res.data_density > 0.0

def test_retrieval_workflows():
    dr = DataRetriever()
    res = dr.retrieve("workflows", "test_tenant")
    assert res.intent == "workflows"
    assert len(res.data["workflows"]) == 1

def test_retrieval_health():
    dr = DataRetriever()
    res = dr.retrieve("health", "test_tenant")
    assert res.intent == "health"
    assert res.summary_stats["health_score"] == 90.0

def test_retrieval_fallback():
    dr = DataRetriever()
    res = dr.retrieve("some random text", "test_tenant")
    assert res.intent == "general"
    assert res.summary_stats["session_count_7d"] == 1
