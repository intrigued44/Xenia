import pytest
import time
import json
import uuid
import sys
from unittest.mock import patch, MagicMock

from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel
from platform_core.vaults.access_control import VaultAccessError
from platform_core.agents_ext.workflow_agent import WorkflowAgent
from platform_core.agents_ext.scout_agent import ScoutAgent
from client.db import init_db, get_connection

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vault_records")
    cursor.execute("DELETE FROM contribution_requests")
    cursor.execute("DELETE FROM proposals")
    conn.commit()
    conn.close()

@patch('platform_core.agents_ext.workflow_agent.os.makedirs')
@patch('platform_core.agents_ext.workflow_agent.open')
#@patch('platform_core.agents_ext.workflow_agent.Anthropic')
def test_workflow_agent_stores_in_personal_vault(mock_open, mock_makedirs):


    # Setup Plan
    plan = {
        "tenant_id": "local",
        "actions": [{
            "pattern": ["Excel", "Chrome"],
            "action": "DOCUMENT",
            "rationale": "High repetition",
            "confidence": 0.9,
            "workflow_name": "Test Workflow",
            "workflow_description": "A test workflow description"
        }]
    }
    
    agent = WorkflowAgent()
    agent.execute(plan, {})

    vm = VaultManager()
    personal = vm.retrieve(VaultLevel.PERSONAL, "local", requesting_role="employee")
    
    assert len(personal) > 0
    assert any(r["record_type"] == "workflow" for r in personal)
    
    record = next(r for r in personal if r["record_type"] == "workflow")
    assert record["content"]["name"] == "Test Workflow"
    assert "doc_path" in record["content"]

@patch('platform_core.agents_ext.workflow_agent.os.makedirs')
@patch('platform_core.agents_ext.workflow_agent.open')
#@patch('platform_core.agents_ext.workflow_agent.Anthropic')
def test_workflow_agent_creates_contribution_request(mock_open, mock_makedirs):


    plan = {
        "tenant_id": "local",
        "actions": [{
            "pattern": ["Notepad"],
            "action": "DOCUMENT",
            "workflow_name": "Role Workflow"
        }]
    }
    
    agent = WorkflowAgent()
    agent.execute(plan, {})

    vm = VaultManager()
    pending = vm.get_pending_contributions("local")
    
    assert len(pending) > 0
    assert pending[0]["to_vault"] == "role"
    assert pending[0]["from_vault"] == "personal"

@patch('platform_core.agents_ext.scout_agent.call_claude')
@patch('platform_core.agents_ext.scout_agent.WebSearchTool')
def test_scout_stores_in_org_vault(mock_search_tool_cls, mock_call_claude):
    mock_searcher = MagicMock()
    mock_searcher.execute.return_value = {
        "success": True, 
        "output": [{"title": "Result", "snippet": "Text", "url": "http"}]
    }
    mock_search_tool_cls.return_value = mock_searcher
    
    # Mock Claude responses - first for queries, second for finding summary, third for briefing
    mock_call_claude.side_effect = [
        '{"finding": "Test finding", "urgency": "high", "category": "Test"}',
        '{"briefing": "Test briefing"}'
    ]
    
    plan = {
        "tenant_id": "local",
        "queries": ["query1"],
        "industry": "retail"
    }
    
    agent = ScoutAgent()
    agent.execute(plan)

    vm = VaultManager()
    org = vm.retrieve_as_agent(VaultLevel.ORGANIZATION, "local", "scout")
    
    assert len(org) > 0
    assert any(r["record_type"] == "intelligence" for r in org)
    
    record = next(r for r in org if r["record_type"] == "intelligence")
    assert record["content"]["finding"] == "Test finding"
    assert record["content"]["urgency"] == "high"

def test_manager_cannot_read_personal_vault():
    vm = VaultManager()
    record = __import__('platform_core').vaults.models.VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.PERSONAL,
        tenant_id="local",
        record_type="workflow",
        content={"name": "private"},
        created_at=int(time.time())
    )
    vm.store(record, requesting_role="employee")
    
    with pytest.raises(VaultAccessError):
        vm.retrieve(
            VaultLevel.PERSONAL, "local",
            requesting_role="manager"
        )
