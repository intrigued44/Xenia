import pytest
from platform_core.connectors import MockConnector
from platform_core.agents import MockAgent
from platform_core.api import receive_event, get_events, clear_events

@pytest.fixture(autouse=True)
def setup_teardown():
    clear_events()
    yield
    clear_events()

def test_connector_interface():
    connector = MockConnector()
    assert connector.name == "MockSystem"
    assert connector.auth_method == "APIKey"
    assert "READ" in connector.capabilities
    
    assert connector.authenticate({}) == "mock_token"
    assert connector.read({}) == {"data": "mock_read"}
    assert connector.write({}) == {"status": "success"}

def test_agent_interface():
    agent = MockAgent()
    assert agent.name == "MockAgent"
    assert agent.perceive({}) == {"observed": True}
    assert agent.plan({}) == {"action": "do_nothing"}
    assert agent.execute({}, {}) == {"success": True}

def test_receive_event():
    event_id = receive_event(
        event_type="web_click",
        source_system="salesforce",
        context={"button": "save"},
        user_id="user_123"
    )
    
    assert event_id is not None
    events = get_events()
    assert len(events) == 1
    
    event = events[0]
    assert event["event_id"] == event_id
    assert event["event_type"] == "web_click"
    assert event["source_system"] == "salesforce"
