import pytest
from platform_core.connectors import MockConnector
from platform_core.agents import MockAgent
from platform_core.api import receive_event, get_events, clear_events
from client.db import get_connection, init_db


@pytest.fixture(autouse=True)
def setup_teardown():
    init_db()
    clear_events()
    yield
    clear_events()


def test_connector_interface():
    connector = MockConnector()
    assert connector.name == "MockSystem"
    assert connector.auth_method == "APIKey"
    assert "READ" in connector.capabilities

    auth_token = connector.authenticate({"api_key": "test_token"})
    assert auth_token == "mock_token"

    read_data = connector.read({"query": "invoices"})
    assert read_data == {"data": "mock_read"}

    write_data = connector.write({"record_id": "123", "value": 450})
    assert write_data == {"status": "success"}


def test_agent_interface():
    agent = MockAgent()
    assert agent.name == "MockAgent"
    assert agent.perceive({"state": "active"}) == {"observed": True}
    assert agent.plan({"observed": True}) == {"action": "do_nothing"}
    assert agent.execute({"action": "do_nothing"}, {}) == {"success": True}


def test_receive_event():
    event_id = receive_event(
        event_type="web_click",
        source_system="salesforce",
        context={"button": "save_invoice"},
        user_id="user_123",
        tenant_id="tenant_sec_01"
    )

    assert event_id is not None
    events = get_events()
    assert len(events) >= 1

    event = next(e for e in events if e["event_id"] == event_id)
    assert event["event_type"] == "web_click"
    assert event["source_system"] == "salesforce"
    assert event["context"]["button"] == "save_invoice"

    # Verify real database side-effect persistence
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM audit_logs WHERE id = ?", (event_id,))
    row = c.fetchone()
    conn.close()

    assert row is not None
    assert row[3] == "web_click"  # action column
    assert row[1] == "tenant_sec_01"
