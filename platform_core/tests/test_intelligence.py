import pytest
import time
import json
import uuid
from unittest.mock import patch

from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
from platform_core.intelligence.departments import DepartmentIntelligence
from platform_core.intelligence.employee_profile import EmployeeIntelligenceProfile
from platform_core.intelligence.performance import PerformanceDashboard
from platform_core.intelligence.dashboard_generator import DashboardGenerator
from client.db import init_db, get_connection

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vault_records")
    cursor.execute("DELETE FROM contribution_requests")
    conn.commit()
    conn.close()

def test_department_intelligence_insufficient_data():
    di = DepartmentIntelligence()
    result = di.analyze("empty_tenant", "sales")
    assert result["status"] == "insufficient_data"
    assert result["department"] == "sales"

def test_department_intelligence_with_data():
    vm = VaultManager()
    vm.store_as_agent(VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.PERSONAL,
        tenant_id="test_dept",
        record_type="workflow",
        content={
            "name": "Update CRM",
            "frequency_per_week": 10,
            "avg_duration_seconds": 600,
            "automation_potential": 0.8
        },
        created_at=int(time.time()),
        status="approved"
    ), agent_name="workflow")
    
    mock_claude_response = {
        "health_score": 85,
        "health_label": "Strong",
        "biggest_opportunity": "Automate CRM updates",
        "biggest_risk": "None",
        "top_insights": [],
        "recommended_actions": [],
        "summary": "Looking good."
    }
    
    with patch("platform_core.intelligence.departments.call_claude", return_value=json.dumps(mock_claude_response)):
        di = DepartmentIntelligence()
        result = di.analyze("test_dept", "sales")
    
    assert result["status"] == "ready"
    assert result["department"] == "sales"
    assert "metrics" in result
    assert result["metrics"]["total_workflows"] >= 1
    assert "analysis" in result
    assert result["analysis"]["health_score"] == 85

def test_employee_profile_insufficient_data():
    ep = EmployeeIntelligenceProfile()
    result = ep.generate("empty_tenant")
    assert result["status"] == "building"

def test_employee_profile_with_data():
    vm = VaultManager()
    vm.store_as_agent(VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.PERSONAL,
        tenant_id="test_emp",
        record_type="workflow",
        content={
            "name": "Process Invoices",
            "frequency_per_week": 5,
            "avg_duration_seconds": 1200,
            "automation_potential": 0.9
        },
        created_at=int(time.time()),
        status="approved"
    ), agent_name="workflow")
    
    mock_claude_response = {
        "capability_summary": "Great at processing invoices",
        "top_skills": [],
        "workflow_mastery": [],
        "contribution_score": 90,
        "contribution_breakdown": {
            "workflows_owned": 1,
            "knowledge_created": 0,
            "team_contributions": 0,
            "weekly_productive_hours": 1.7
        },
        "growth_opportunities": [],
        "promotion_case": "Saved 1.7 hours a week",
        "career_trajectory": "Upwards"
    }
    
    with patch("platform_core.intelligence.employee_profile.call_claude", return_value=json.dumps(mock_claude_response)):
        ep = EmployeeIntelligenceProfile()
        result = ep.generate("test_emp")
        
    assert result["status"] == "ready"
    assert "profile" in result
    assert result["profile"]["contribution_score"] == 90
    
    export = ep.export_portable("test_emp")
    assert export["nous_profile_version"] == "1.0"
    assert export["tenant_id"] == "portable"

def test_performance_dashboard():
    vm = VaultManager()
    vm.store_as_agent(VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.TEAM,
        tenant_id="test_team",
        record_type="improvement",
        content={
            "description": "Fixed the slow query",
            "type": "database",
            "estimated_time_recovery_minutes": 30
        },
        created_at=int(time.time()),
        status="approved"
    ), agent_name="architect")
    
    pd = PerformanceDashboard()
    result = pd.get_team_dashboard("test_team")
    assert result["status"] == "ready"
    assert result["team_metrics"]["improvement_opportunities"] == 1
    assert len(result["recent_improvements"]) == 1

def test_dashboard_generator():
    mock_claude_response = {
        "title": "Team Health",
        "question_answered": "How is the team operating?",
        "summary": "It is doing okay.",
        "key_metrics": [],
        "charts": [],
        "top_finding": "None",
        "recommended_action": "None"
    }
    
    with patch("platform_core.intelligence.dashboard_generator.call_claude", return_value=json.dumps(mock_claude_response)):
        dg = DashboardGenerator()
        result = dg.generate("team_health", "test_tenant")
        
    assert result["status"] == "ready"
    assert "dashboard" in result
    assert result["dashboard"]["title"] == "Team Health"
    assert "generated_at" in result["dashboard"]
