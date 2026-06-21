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

def test_department_analysis_insufficient_data():
    result = DepartmentIntelligence().analyze(
        "empty_tenant", "sales"
    )
    assert result["status"] == "insufficient_data"

def test_department_analysis_with_vault_data():
    vm = VaultManager()
    vm.store_as_agent(VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.TEAM,
        tenant_id="dept_test",
        record_type="workflow",
        content={
            "name": "Sales Workflow",
            "frequency_per_week": 5,
            "avg_duration_seconds": 1800,
            "automation_potential": 0.8
        },
        created_at=int(time.time())
    ), agent_name="architect")

    with patch(
        "platform_core.intelligence"
        ".departments.call_claude",
        return_value=json.dumps({
            "health_score": 75,
            "health_label": "Strong",
            "biggest_opportunity": "Automate",
            "biggest_risk": "Knowledge risk",
            "top_insights": [],
            "recommended_actions": [],
            "summary": "Test summary"
        })
    ):
        result = DepartmentIntelligence().analyze(
            "dept_test", "sales"
        )
    assert result["status"] == "ready"
    assert result["metrics"]["total_workflows"] >= 1

def test_employee_profile_building_state():
    result = EmployeeIntelligenceProfile().generate(
        "empty_employee"
    )
    assert result["status"] == "building"

def test_employee_profile_generates():
    vm = VaultManager()
    vm.store_as_agent(VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.PERSONAL,
        tenant_id="emp_test",
        record_type="workflow",
        content={
            "name": "Daily Reporting",
            "frequency_per_week": 5,
            "avg_duration_seconds": 2400,
            "automation_potential": 0.6
        },
        created_at=int(time.time())
    ), agent_name="workflow")

    mock_profile = {
        "capability_summary": "Test summary",
        "top_skills": [],
        "workflow_mastery": [],
        "contribution_score": 72,
        "contribution_breakdown": {},
        "growth_opportunities": [],
        "promotion_case": "Strong contributor",
        "career_trajectory": "Growing analyst"
    }

    with patch(
        "platform_core.intelligence"
        ".employee_profile.call_claude",
        return_value=json.dumps(mock_profile)
    ):
        result = EmployeeIntelligenceProfile().generate(
            "emp_test"
        )
    assert result["status"] == "ready"
    assert result["profile"]["contribution_score"] == 72

def test_portable_export_structure():
    result = EmployeeIntelligenceProfile()\
        .export_portable("empty_employee")
    assert "nous_profile_version" in result
    assert result["tenant_id"] == "portable"
    assert "portable_note" in result

def test_dashboard_generation():
    with patch(
        "platform_core.intelligence"
        ".dashboard_generator.call_claude",
        return_value=json.dumps({
            "title": "Team Health",
            "question_answered": "How is the team?",
            "summary": "Team is performing well",
            "key_metrics": [],
            "charts": [],
            "top_finding": "Strong execution",
            "recommended_action": "Keep it up"
        })
    ):
        result = DashboardGenerator().generate(
            "team_health", "local"
        )
    assert result["status"] == "ready"
    assert "dashboard" in result

def test_dashboard_types_complete():
    types = DashboardGenerator.DASHBOARD_TYPES
    assert "team_health" in types
    assert "process_efficiency" in types
    assert "knowledge_map" in types
    assert len(types) >= 7
