import pytest
import json
import uuid
import time
from unittest.mock import patch
from platform_core.intelligence.simulation import SimulationEngine, SimulationScenario, SimulationError
from client.db import init_db, get_connection

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS graph_nodes (id TEXT PRIMARY KEY, tenant_id TEXT, type TEXT, label TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS graph_edges (id INTEGER PRIMARY KEY, tenant_id TEXT, source_id TEXT, target_id TEXT, relation TEXT)")
    c.execute('''
        CREATE TABLE IF NOT EXISTS simulations (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            scenario_type TEXT NOT NULL,
            target TEXT NOT NULL,
            change_percent INTEGER NOT NULL,
            direction TEXT NOT NULL,
            context TEXT DEFAULT '',
            before_state TEXT NOT NULL,
            after_state TEXT NOT NULL,
            delta TEXT NOT NULL,
            narrative TEXT DEFAULT '',
            risks TEXT DEFAULT '[]',
            opportunities TEXT DEFAULT '[]',
            confidence TEXT NOT NULL,
            confidence_rationale TEXT DEFAULT '',
            affected_workflows TEXT DEFAULT '[]',
            hours_saved_per_week REAL DEFAULT 0,
            monthly_value_hours REAL DEFAULT 0,
            health_score_before REAL DEFAULT 0,
            health_score_after REAL DEFAULT 0,
            data_observations INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL,
            status TEXT DEFAULT 'active'
        )
    ''')
    c.execute("DELETE FROM workflows")
    c.execute("DELETE FROM sessions")
    c.execute("DELETE FROM graph_nodes")
    c.execute("DELETE FROM graph_edges")
    c.execute("DELETE FROM simulations")
    
    # Insert workflows
    c.execute("INSERT INTO workflows (id, tenant_id, name, app_sequence, avg_duration_seconds, frequency_per_week, automation_potential) VALUES (?, ?, ?, ?, ?, ?, ?)",
              ('w1', 'test_tenant', 'Invoice Processing', '["excel", "tally"]', 1800, 10, 0.8))
    c.execute("INSERT INTO workflows (id, tenant_id, name, app_sequence, avg_duration_seconds, frequency_per_week, automation_potential) VALUES (?, ?, ?, ?, ?, ?, ?)",
              ('w2', 'test_tenant', 'Weekly Sync', '["zoom", "calendar"]', 3600, 5, 0.1))
    c.execute("INSERT INTO workflows (id, tenant_id, name, app_sequence, avg_duration_seconds, frequency_per_week, automation_potential) VALUES (?, ?, ?, ?, ?, ?, ?)",
              ('w3', 'test_tenant', 'Client Meeting', '["teams", "chrome"]', 1800, 15, 0.2))
    
    # Insert sessions for data density & headcount proxy
    for i in range(25):
        c.execute("INSERT INTO sessions (id, tenant_id, primary_app, automation_score, started_at) VALUES (?, ?, ?, ?, ?)",
                  (f's_{i}', 'test_tenant', 'excel' if i < 15 else 'zoom', 0.5, str(int(time.time()))))
                  
    # Insert graph nodes
    c.execute("INSERT INTO graph_nodes (id, tenant_id, type, label) VALUES (?, ?, ?, ?)", ('n1', 'test_tenant', 'tool', 'excel'))
    c.execute("INSERT INTO graph_nodes (id, tenant_id, type, label) VALUES (?, ?, ?, ?)", ('n2', 'test_tenant', 'tool', 'tally'))
    
    conn.commit()
    conn.close()

def mock_claude_response(*args, **kwargs):
    return json.dumps({
        "narrative": "Test narrative",
        "risks": ["Test risk 1", "Test risk 2"],
        "opportunities": ["Test opp 1"]
    })

def test_automate_workflow_success():
    engine = SimulationEngine()
    scenario = SimulationScenario("automate_workflow", "invoice", 50, "reduce")
    
    with patch.object(engine, '_call_claude', side_effect=mock_claude_response):
        res = engine.simulate(scenario, "test_tenant")
        
    assert res.hours_saved_per_week == 2.5  # 10 freqs * 1800s / 3600 = 5.0h * 50%
    assert res.monthly_value_hours == 10.82 # 2.5 * 4.33
    assert res.confidence in ["medium", "high"]
    assert res.health_score_after <= 100.0

def test_automate_workflow_not_found():
    engine = SimulationEngine()
    scenario = SimulationScenario("automate_workflow", "nonexistent", 50, "reduce")
    with pytest.raises(SimulationError):
        engine.simulate(scenario, "test_tenant")

def test_reduce_meetings():
    engine = SimulationEngine()
    scenario = SimulationScenario("reduce_meetings", "", 30, "reduce")
    
    with patch.object(engine, '_call_claude', side_effect=mock_claude_response):
        res = engine.simulate(scenario, "test_tenant")
        
    # w2 (zoom)=5.0h, w3 (teams)=7.5h -> 12.5h total * 30% = 3.75h saved
    assert res.hours_saved_per_week == 3.75
    assert len(res.affected_workflows) == 2

def test_add_headcount():
    engine = SimulationEngine()
    scenario = SimulationScenario("add_headcount", "invoice", 100, "add")
    
    with patch.object(engine, '_call_claude', side_effect=mock_claude_response):
        res = engine.simulate(scenario, "test_tenant")
        
    assert res.confidence == "medium"
    assert "new_headcount" in res.after_state

def test_remove_bottleneck():
    engine = SimulationEngine()
    scenario = SimulationScenario("remove_bottleneck", "excel", 100, "eliminate")
    
    # We need to mock get_graph_data to return a well-formed graph with connections
    with patch('platform_core.intelligence.graph.get_graph_data') as mock_get_graph:
        mock_get_graph.return_value = {
            "nodes": [{"label": "excel", "connections": 5}, {"label": "tally", "connections": 1}],
            "most_connected": {"label": "excel", "connections": 5},
            "summary": {"nodes": 2, "edges": 1}
        }
        with patch.object(engine, '_call_claude', side_effect=mock_claude_response):
            res = engine.simulate(scenario, "test_tenant")
            
        assert res.before_state["bottleneck_node"] == "excel"
        assert res.hours_saved_per_week == 1.5 # 5.0 total dep hours * 30% elimination reduction

