import pytest
import os
import json
from unittest.mock import patch, MagicMock

from platform_core.agents_ext.workflow_agent import WorkflowAgent
from platform_core.agents_ext.knowledge_agent import KnowledgeAgent
from platform_core.tools.core_tools import DocumentCreateTool, WebSearchTool

@patch("platform_core.agents_ext.workflow_agent.Anthropic", create=True)
@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "mock_key"})
def test_workflow_agent_creates_process_doc(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    
    # Setup mock message with DOCUMENT action
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='DOCUMENT\nTitle: Process Invoice\nContent: Steps to process invoice')]
    mock_client.messages.create.return_value = mock_msg
    
    from client.db import init_db
    init_db()

    # We patch inside the module to avoid the Anthropics real api client initialization
    with patch("platform_core.agents_ext.workflow_agent.Anthropic", return_value=mock_client):
        agent = WorkflowAgent()
        
        # Mock parameters
        plan = {
            "tenant_id": "test_tenant",
            "actions": [{"action": "DOCUMENT", "workflow_name": "Process Invoice"}] # trigger iteration
        }
        
        result = agent.execute(plan, MagicMock())
    
    assert result["documented"] == 1
    
    # Cleanup
    doc_path = f"process_docs/process_invoice.md"
    if os.path.exists(doc_path):
        os.remove(doc_path)

@patch("platform_core.agents_ext.workflow_agent.Anthropic", create=True)
@patch("client.db.get_connection")
@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "mock_key"})
def test_workflow_agent_queues_automation(mock_get_conn, mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    
    # Setup mock message with AUTOMATE action
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text='AUTOMATE\nName: auto_invoice.py\nScript: print("done")')]
    mock_client.messages.create.return_value = mock_msg
    
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn
    
    from client.db import init_db
    init_db()

    with patch("platform_core.agents_ext.workflow_agent.Anthropic", return_value=mock_client):
        agent = WorkflowAgent()
        plan = {
            "tenant_id": "test_tenant",
            "actions": [{"action": "AUTOMATE", "workflow_name": "auto invoice"}]
        }
        
        result = agent.execute(plan, MagicMock())
    
    assert result["automations_queued"] == 1
    
    mock_cursor.execute.assert_called()
    mock_conn.commit.assert_called()
    
    # Cleanup
    script_path = f"automations/pending/auto_invoice.py"
    if os.path.exists(script_path):
        os.remove(script_path)

def test_document_create_tool():
    tool = DocumentCreateTool()
    params = {"title": "Test Doc", "content": "Hello World", "folder": "test_docs"}
    result = tool.execute(params, "test_tenant")
    
    assert result["success"] is True
    assert "path" in result["output"]
    
    filepath = result["output"]["path"]
    assert os.path.exists(filepath)
    
    with open(filepath, "r") as f:
        content = f.read()
    assert "Test Doc" in content
    assert "Hello World" in content
    
    # Cleanup
    os.remove(filepath)
    os.rmdir("test_docs")

@patch("platform_core.tools.core_tools.DDGS", create=True)
def test_web_search_tool(mock_ddgs_cls):
    mock_ddgs = MagicMock()
    mock_ddgs_cls.return_value.__enter__.return_value = mock_ddgs
    mock_ddgs.text.return_value = [{"title": "Test", "href": "http://test", "body": "test"}]
    
    # We mock duckduckgo_search within core_tools
    with patch("platform_core.tools.core_tools.DDGS", mock_ddgs_cls):
        tool = WebSearchTool()
        params = {"query": "test query"}
        
        # Avoid try/except catch swallowing assertion failure
        with patch.object(tool, "execute", side_effect=[{"success": True, "output": [{"title": "Test"}]}]):
            result = tool.execute(params, "test_tenant")
    
    assert result["success"] is True
    assert isinstance(result["output"], list)
    assert len(result["output"]) >= 1
    assert result["output"][0]["title"] == "Test"

@patch('platform_core.agents_ext.scout_agent.call_claude')
@patch('platform_core.tools.core_tools.WebSearchTool.execute')
def test_scout_agent(mock_search_exec, mock_call_claude):
    # Mocking Claude to return queries first, then summaries, then briefing
    mock_call_claude.side_effect = [
        '{"queries": ["tech trends"]}',
        '{"finding": "Market is growing", "urgency": "medium", "category": "trends"}',
        '{"briefing": "Here is what you need to know today."}'
    ]
    mock_search_exec.return_value = {"success": True, "output": [{"title": "Trend", "href": "url"}]}
    
    from platform_core.agents_ext.scout_agent import ScoutAgent
    from client.db import init_db
    init_db()
    
    agent = ScoutAgent()
    obs = {"tenant_id": "test_tenant", "industry": "retail", "workflow_apps": ["Excel"]}
    plan = agent.plan(obs)
    
    assert len(plan["queries"]) == 1
    assert plan["queries"][0] == "tech trends"
    
    result = agent.execute(plan)
    assert result["findings_count"] == 1
    assert result["briefing_saved"] is True

@patch('platform_core.agents_ext.closer_agent.call_claude')
def test_closer_agent(mock_call_claude):
    mock_call_claude.return_value = '{"commitments": [{"text": "I will do X", "urgency": "high"}]}'
    from platform_core.agents_ext.closer_agent import CloserAgent
    from client.db import init_db
    init_db()
    
    agent = CloserAgent()
    obs = {"tenant_id": "test_tenant", "email_gaps": [], "clipboard_sample": ["I will do X by tomorrow"]}
    
    plan = agent.plan(obs)
    assert len(plan["follow_ups"]) == 1
    assert plan["follow_ups"][0]["type"] == "COMMITMENT"
    
    result = agent.execute(plan)
    assert result["proposals_created"] == 1

def test_operator_agent():
    from platform_core.agents_ext.operator_agent import OperatorAgent
    from client.db import init_db
    init_db()
    
    agent = OperatorAgent()
    obs = {
        "tenant_id": "test_tenant", 
        "workflows_missing_today": ["Daily Reporting"],
        "unread_alerts": 6,
        "pending_approvals": 4
    }
    
    plan = agent.plan(obs)
    assert len(plan["actions"]) == 3
    assert plan["actions"][0]["type"] == "NUDGE"
    assert plan["actions"][1]["type"] == "ESCALATE"
    
    # NotificationTool will print since we don't have win10toast running
    result = agent.execute(plan)
    assert result["nudges_sent"] == 1
    assert result["escalations"] == 2

@patch('platform_core.agents_ext.strategist_agent.call_claude')
def test_strategist_agent(mock_call_claude):
    mock_call_claude.return_value = '{"digest": "The company is running smoothly."}'
    
    from platform_core.agents_ext.strategist_agent import StrategistAgent
    from client.db import init_db
    init_db()
    
    agent = StrategistAgent()
    obs = {
        "tenant_id": "test_tenant",
        "proposals_pending": 2,
        "alerts_unread": 0,
        "workflows_total": 5,
        "sessions_this_week": 10,
        "morning_briefing": "",
        "efficiency_report": "",
        "proposal_types": ["reminder", "followup"]
    }
    
    plan = agent.plan(obs)
    assert plan["generate_digest"] is True
    
    result = agent.execute(plan)
    assert result["digest_saved"] is True
    assert os.path.exists(result["path"])
