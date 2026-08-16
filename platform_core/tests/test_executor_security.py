import pytest
import os
import time
from platform_core.intelligence.restricted_executor import (
    RestrictedExecutor,
    Capability,
    SecurityViolationError
)
from platform_core.intelligence.skills_engine import run_and_heal_skill
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
from client.db import init_db


@pytest.fixture(autouse=True)
def setup_sec_db():
    init_db()


def test_executor_blocks_forbidden_import_os():
    executor = RestrictedExecutor()
    malicious_code = "import os\nos.system('echo HACKED')"
    res = executor.execute_skill("hack_test_1", malicious_code)

    assert res["success"] is False
    assert "SECURITY_VIOLATION" in res["error"] or "Forbidden import" in res["error"]


def test_executor_blocks_forbidden_import_subprocess():
    executor = RestrictedExecutor()
    malicious_code = "import subprocess\nsubprocess.run(['ls', '-la'])"
    res = executor.execute_skill("hack_test_2", malicious_code)

    assert res["success"] is False
    assert "SECURITY_VIOLATION" in res["error"]


def test_executor_blocks_path_traversal_reading():
    executor = RestrictedExecutor()
    malicious_code = "content = read_file('/etc/passwd')"
    res = executor.execute_skill("hack_test_3", malicious_code)

    assert res["success"] is False
    assert "Path traversal blocked" in str(res["error"]) or "Access Denied" in str(res["error"])


def test_executor_blocks_path_traversal_writing():
    executor = RestrictedExecutor()
    malicious_code = "write_file('../../../root_hacked.txt', 'data')"
    res = executor.execute_skill("hack_test_4", malicious_code)

    assert res["success"] is False
    assert "Path traversal blocked" in str(res["error"]) or "Access Denied" in str(res["error"])


def test_executor_blocks_unauthorized_vault_access():
    executor = RestrictedExecutor()
    # Executing without VAULT_GET_SECRET capability
    malicious_code = "token = get_vault_secret('erp_portal')"
    res = executor.execute_skill(
        "hack_test_5",
        malicious_code,
        allowed_capabilities=[Capability.FILESYSTEM_READ.value]
    )

    assert res["success"] is False
    assert "Access Denied" in str(res["error"])


def test_executor_enforces_execution_timeout():
    executor = RestrictedExecutor(timeout_seconds=1.0)
    infinite_loop_code = "while True:\n    time.sleep(0.1)"
    res = executor.execute_skill("timeout_test", infinite_loop_code)

    assert res["success"] is False
    assert "EXECUTION_TIMEOUT" in res["error"]
    assert res["duration_ms"] >= 900


def test_executor_allows_legitimate_approved_workflow():
    executor = RestrictedExecutor()

    # Create secret in vault
    vm = VaultManager()
    vm.store(VaultRecord(
        id="sec_test_vault_01",
        vault_level=VaultLevel.PERSONAL,
        tenant_id="local",
        record_type="secret",
        content={"service": "erp_portal", "auth_token": "token_legit_123"},
        status="approved"
    ), requesting_role="employee")

    legit_code = """
write_file('temp/output_test.txt', 'Processing invoice batch...')
data = read_file('temp/output_test.txt')
token = get_vault_secret('erp_portal')
print(f"Read data: {data}, Token length: {len(token)}")
"""

    res = executor.execute_skill(
        "legit_test",
        legit_code,
        allowed_capabilities=[
            Capability.FILESYSTEM_READ.value,
            Capability.FILESYSTEM_WRITE.value,
            Capability.VAULT_GET_SECRET.value
        ],
        user_role="employee"
    )

    assert res["success"] is True
    assert "Read data: Processing invoice batch..." in res["output"]
    assert "Token length: 15" in res["output"]


def test_skills_engine_uses_restricted_executor():
    res = run_and_heal_skill(
        name="test_skills_engine_sandbox",
        code_content="import subprocess"
    )
    assert res["success"] is False
    assert "SECURITY_VIOLATION" in res["error"]
