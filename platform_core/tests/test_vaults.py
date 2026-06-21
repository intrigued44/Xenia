import pytest
import time
import uuid
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultRecord, VaultLevel
from platform_core.vaults.access_control import VaultAccessError, check_agent_access
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

def test_store_and_retrieve_personal_vault():
    vm = VaultManager()
    record = VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.PERSONAL,
        tenant_id="test",
        record_type="workflow",
        content={"name": "test workflow"},
        created_at=int(time.time())
    )
    vm.store(record, requesting_role="employee")
    results = vm.retrieve(VaultLevel.PERSONAL,
                          "test", requesting_role="employee")
    assert any(r["id"] == record.id for r in results)

def test_personal_vault_blocked_from_manager():
    vm = VaultManager()
    with pytest.raises(VaultAccessError):
        vm.retrieve(VaultLevel.PERSONAL, "test",
                   requesting_role="manager")

def test_agent_access_enforced():
    vm = VaultManager()
    record = VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.PERSONAL,
        tenant_id="test",
        record_type="workflow",
        content={"name": "test"},
        created_at=int(time.time())
    )
    with pytest.raises(VaultAccessError):
        vm.store_as_agent(record, agent_name="scout")

def test_contribution_flow_anonymizes():
    vm = VaultManager()
    original_hash = "user_identity_123"

    record = VaultRecord(
        id=str(uuid.uuid4()),
        vault_level=VaultLevel.PERSONAL,
        tenant_id="test",
        record_type="workflow",
        contributor_hash=original_hash,
        content={"name": "Invoice Processing",
                 "user_id": "should_be_removed"},
        created_at=int(time.time())
    )
    vm.store(record, requesting_role="employee")

    request_id = vm.request_contribution(
        record_id=record.id,
        from_vault=VaultLevel.PERSONAL,
        to_vault=VaultLevel.ROLE,
        summary="Contribute this workflow?",
        tenant_id="test",
        contributor_hash=original_hash
    )

    vm.approve_contribution(request_id)

    role_records = vm.retrieve(
        VaultLevel.ROLE, "test",
        requesting_role="manager"
    )

    promoted = next(
        (r for r in role_records
         if r.get("record_type") == "workflow"),
        None
    )

    assert promoted is not None
    assert promoted["contributor_hash"] != original_hash
    assert "user_id" not in promoted.get("content", {})

def test_check_agent_access_rules():
    check_agent_access("closer", VaultLevel.PERSONAL)
    with pytest.raises(VaultAccessError):
        check_agent_access("scout", VaultLevel.PERSONAL)
    with pytest.raises(VaultAccessError):
        check_agent_access("operator",
                          VaultLevel.ORGANIZATION)

def test_vault_summary_returns_counts():
    vm = VaultManager()
    summary = vm.get_vault_summary("test")
    assert "personal" in summary
    assert "role" in summary
    assert "team" in summary
    assert "organization" in summary
    assert "pending_contributions" in summary
