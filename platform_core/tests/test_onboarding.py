import pytest
import time
import json
import uuid
from unittest.mock import patch, MagicMock

from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
from platform_core.onboarding.onboarding_agent import OnboardingAgent
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

def test_brief_returns_insufficient_data_when_empty():
    vault_manager = VaultManager()
    agent = OnboardingAgent()
    result = agent.generate_day_one_brief("empty_tenant")
    assert result["status"] == "insufficient_data"
    assert "message" in result
    assert result["brief"] is None

def test_brief_generates_when_role_vault_has_data():
    vm = VaultManager()
    vm.store(VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.ROLE,
        tenant_id="onboard_test",
        record_type="workflow",
        content={
            "name": "Invoice Processing",
            "description": "Process supplier invoices",
            "app_sequence": ["Excel", "Tally"],
            "frequency_per_week": 4,
            "avg_duration_seconds": 1800
        },
        created_at=int(time.time()),
        status="approved"
    ), requesting_role="manager")

    mock_brief = {
        "what_this_role_actually_does": "test",
        "tools_you_will_use": [],
        "processes_to_learn_first": [],
        "first_week_reality": "test",
        "questions_you_will_have": []
    }

    with patch(
        "platform_core.onboarding.onboarding_agent.call_claude",
        return_value=json.dumps(mock_brief)
    ):
        agent = OnboardingAgent()
        result = agent.generate_day_one_brief(
            "onboard_test"
        )

    assert result["status"] == "ready"
    assert result["brief"] is not None
    assert result["workflows_available"] >= 1

def test_90_day_report_generates():
    mock_report = {
        "headline": "Strong first quarter",
        "workflows_mastered": 5,
        "knowledge_contributed": 3,
        "team_contributions": 2,
        "strengths_observed": ["consistent"],
        "growth_areas": ["speed"],
        "impact_statement": "test impact"
    }
    with patch(
        "platform_core.onboarding.onboarding_agent.call_claude",
        return_value=json.dumps(mock_report)
    ):
        agent = OnboardingAgent()
        result = agent.generate_90_day_report("local")
    assert result["status"] == "ready"
    assert "report" in result
