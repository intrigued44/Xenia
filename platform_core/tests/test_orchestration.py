import os
import pytest
from platform_core.orchestration.engine import OrchestrationEngine, Plan, PlanStep, PlanResult
from platform_core.orchestration.planner import NaturalLanguagePlanner
from platform_core.tools.base import ToolRegistry, Tool
from platform_core.orchestration.approvals import ApprovalManager

class MockSearchTool(Tool):
    name = "web_tool.search"
    description = "Searches web"
    permission_tier = "auto"
    required_connector = None
    def execute(self, params, tenant_id):
        return {"success": True, "output": ["mock_result"], "error": None}

class MockFailTool(Tool):
    name = "fail_tool"
    description = "Always fails"
    permission_tier = "auto"
    required_connector = None
    def execute(self, params, tenant_id):
        return {"success": False, "output": None, "error": "mock_error"}

class MockEmailTool(Tool):
    name = "email_tool.send"
    description = "Sends email"
    permission_tier = "confirm"
    required_connector = None
    def execute(self, params, tenant_id):
        return {"success": True, "output": "sent", "error": None}

@pytest.fixture
def mock_registry():
    r = ToolRegistry()
    r.register(MockSearchTool())
    r.register(MockFailTool())
    r.register(MockEmailTool())
    return r

def test_auto_execution(mock_registry):
    engine = OrchestrationEngine(mock_registry)
    plan = Plan(
        id="plan_1", goal="test", tenant_id="test_tenant",
        steps=[PlanStep(id="s1", tool_name="web_tool.search", params={}, depends_on=[], permission_tier="auto", success_criteria="")]
    )
    result = engine.execute(plan)
    assert result.overall_status == "completed"
    assert result.step_results["s1"]["success"] is True

def test_plan_failure(mock_registry):
    engine = OrchestrationEngine(mock_registry)
    plan = Plan(
        id="plan_2", goal="test", tenant_id="test_tenant",
        steps=[PlanStep(id="s1", tool_name="fail_tool", params={}, depends_on=[], permission_tier="auto", success_criteria="", retry_count=0)]
    )
    result = engine.execute(plan)
    assert result.overall_status == "failed"
    assert result.failed_step == "s1"

def test_approval_pause(mock_registry):
    engine = OrchestrationEngine(mock_registry)
    plan = Plan(
        id="plan_3", goal="test", tenant_id="test_tenant",
        steps=[PlanStep(id="s1", tool_name="email_tool.send", params={}, depends_on=[], permission_tier="confirm", success_criteria="")]
    )
    result = engine.execute(plan)
    assert result.overall_status == "paused"
    assert plan.steps[0].status == "paused_for_approval"

def test_dependency_ordering(mock_registry):
    engine = OrchestrationEngine(mock_registry)
    plan = Plan(
        id="plan_4", goal="test", tenant_id="test_tenant",
        steps=[
            PlanStep(id="s2", tool_name="web_tool.search", params={}, depends_on=["s1"], permission_tier="auto", success_criteria=""),
            PlanStep(id="s1", tool_name="web_tool.search", params={}, depends_on=[], permission_tier="auto", success_criteria="")
        ]
    )
    ordered = engine._topological_sort(plan.steps)
    assert ordered[0].id == "s1"
    assert ordered[1].id == "s2"

def test_plan_creation(monkeypatch, mock_registry):
    planner = NaturalLanguagePlanner(mock_registry)
    
    class MockMessages:
        def create(self, **kwargs):
            class MockResponse:
                content = [type('obj', (object,), {'text': '{"goal_interpreted": "test", "steps": [{"id": "s1", "tool_name": "web_tool.search", "params": {}, "depends_on": [], "permission_tier": "auto", "success_criteria": "done"}]}'})]
            return MockResponse()
            
    class MockClient:
        def __init__(self, **kwargs):
            self.messages = MockMessages()
            
    from platform_core.orchestration import planner as planner_module
    monkeypatch.setattr(planner_module, 'Anthropic', MockClient)
    
    plan = planner.create_plan("do something", "test_tenant")
    assert plan.goal == "do something"
    assert len(plan.steps) == 1
    assert plan.steps[0].id == "s1"
    assert plan.steps[0].tool_name == "web_tool.search"

@pytest.mark.integration
def test_real_web_search(monkeypatch):
    class MockDDGS:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def text(self, q, max_results=5):
            return iter([
                {"title":"Test","href":"https://test.com", "body":"Test result"}
            ])
            
    import platform_core.tools.core_tools
    
    # Also need to mock the import itself inside the execute method,
    # or just mock the entire execute method, but since the test wants to test WebSearchTool 
    # we can mock the ddgs module
    
    import sys
    from types import ModuleType
    mock_ddgs_module = ModuleType("ddgs")
    mock_ddgs_module.DDGS = MockDDGS
    sys.modules["ddgs"] = mock_ddgs_module
    
    from platform_core.tools.core_tools import WebSearchTool
    res = WebSearchTool().execute(
        {"query": "test"}, "local"
    )
    assert res["success"] is True
    assert len(res["output"]) > 0
