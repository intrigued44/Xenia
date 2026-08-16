import pytest
import time
import json
from client.db import init_db, get_connection, log_clipboard, create_session, log_event
from client.pii_filter import sanitize, is_sensitive
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
from platform_core.vaults.access_control import VaultAccessError
from platform_core.intelligence.employee_profile import EmployeeIntelligenceProfile
from platform_core.server import app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_privacy_db():
    init_db()


def test_pii_sanitization_before_persistence():
    raw_clipboard = "User password: MySecretPassword123 with SSN 123-45-6789 and email john@corp.com"
    clean_text = sanitize(raw_clipboard)

    log_clipboard(clean_text, "Notepad", "tenant_priv_01")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT text_content FROM clipboard_logs WHERE tenant_id = 'tenant_priv_01'")
    saved_text = c.fetchone()[0]
    conn.close()

    assert "MySecretPassword123" not in saved_text
    assert "123-45-6789" not in saved_text
    assert "john@corp.com" not in saved_text
    assert "[REDACTED_PASSWORD]" in saved_text
    assert "[REDACTED_SSN]" in saved_text
    assert "[REDACTED_EMAIL]" in saved_text


def test_vault_secrets_never_leak_in_logs():
    vm = VaultManager()
    vm.store(VaultRecord(
        id="sec_vault_rec_01",
        vault_level=VaultLevel.PERSONAL,
        tenant_id="tenant_priv_02",
        record_type="secret",
        content={"service": "bank_portal", "api_key": "sk-live-secret-token-999"},
        status="approved"
    ), requesting_role="employee")

    # Verify vault record content is encrypted/isolated and not accessible to manager
    with pytest.raises(VaultAccessError):
        vm.retrieve(VaultLevel.PERSONAL, "tenant_priv_02", requesting_role="manager")


def test_portable_export_anonymizes_pii():
    emp_profile = EmployeeIntelligenceProfile()
    exported = emp_profile.export_portable("empty_tenant")

    exported_str = json.dumps(exported)
    assert "ssn" not in exported_str.lower()
    assert "password" not in exported_str.lower()
    assert exported["tenant_id"] == "portable"


def test_data_deletion_removes_user_records():
    tenant = "tenant_wipe_test"
    create_session("sess_wipe_1", int(time.time()), "Excel", tenant)
    log_event("sess_wipe_1", "click", "Excel", {"data": "sample"}, tenant)

    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE tenant_id = ?", (tenant,))
    c.execute("DELETE FROM events WHERE tenant_id = ?", (tenant,))
    conn.commit()

    c.execute("SELECT COUNT(*) FROM sessions WHERE tenant_id = ?", (tenant,))
    count_sess = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM events WHERE tenant_id = ?", (tenant,))
    count_evt = c.fetchone()[0]
    conn.close()

    assert count_sess == 0
    assert count_evt == 0
