"""
Red-Team Dynamic Exploit Execution Suite for RestrictedExecutor.

Attempts active exploits against RestrictedExecutor across:
1. Filesystem Traversal & Symlink Escapes
2. Environment Secret Exfiltration (XENIA_REDTEAM_SECRET)
3. Python Introspection & Class Subclass Escapes
4. Command Execution & Subprocess Creation
5. Network Socket & Localhost Connections
6. Capability Escalation (read -> write, no vault -> vault)
7. Vault Privilege Escalation (User B reading User A secret)

CRITICAL AUDIT RULE: Does NOT modify runtime code. Dynamically executes exploits and asserts outcome.
"""

import pytest
import os
import sys
import time
import socket
from platform_core.intelligence.restricted_executor import (
    RestrictedExecutor,
    Capability
)
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
from client.db import init_db


@pytest.fixture(autouse=True)
def setup_redteam_db(monkeypatch):
    init_db()
    # Set parent environment secret
    monkeypatch.setenv("XENIA_REDTEAM_SECRET", "DO_NOT_LEAK_CONFIDENTIAL_KEY_999")


# --- 1. Filesystem Traversal & Symlink Attacks ---

def test_redteam_fs_symlink_escape_attempt(tmp_path):
    """Attempt symlink creation pointing outside workspace to read /etc/passwd or host files."""
    executor = RestrictedExecutor()

    # Create symlink in temp directory pointing to /etc/passwd if readable
    target = "/etc/passwd" if os.path.exists("/etc/passwd") else __file__
    symlink_path = os.path.join(executor.workspace_root, "temp", "symlink_leak.txt")
    os.makedirs(os.path.dirname(symlink_path), exist_ok=True)
    if os.path.exists(symlink_path):
        os.remove(symlink_path)

    try:
        os.symlink(target, symlink_path)
    except Exception:
        pytest.skip("Symlink creation not supported in current environment")

    # Attempt to read file through symlink via sandbox
    code = "data = read_file('temp/symlink_leak.txt')\nprint(data[:100])"
    res = executor.execute_skill("red_symlink_1", code)

    # Clean up symlink
    if os.path.exists(symlink_path):
        os.remove(symlink_path)

    # Verify that symlink traversal is safely BLOCKED
    assert res["success"] is False
    assert "Path traversal blocked" in str(res["error"]) or "SecurityViolationError" in str(res["error"])


def test_redteam_fs_direct_sqlite_db_read_attempt():
    """Attempt reading local SQLite database file containing all vault & audit records."""
    executor = RestrictedExecutor()
    code = "data = read_file('mvp_data.db')"
    res = executor.execute_skill("red_db_read_1", code)

    # Verify that direct SQLite DB file read is safely BLOCKED
    assert res["success"] is False
    assert "Access Denied" in str(res["error"]) or "database file" in str(res["error"])


# --- 2. Environment Secret Exfiltration Attacks ---

def test_redteam_env_secret_exfiltration():
    """Attempt retrieving XENIA_REDTEAM_SECRET from worker environment."""
    executor = RestrictedExecutor()

    # Attempt 1: direct os.environ import
    code_1 = "import os\nprint(os.environ.get('XENIA_REDTEAM_SECRET'))"
    res_1 = executor.execute_skill("red_env_1", code_1)
    assert res_1["success"] is False

    # Attempt 2: sys.modules lookup
    code_2 = "import sys\nos_mod = sys.modules.get('os')\nprint(os_mod.environ if os_mod else 'None')"
    res_2 = executor.execute_skill("red_env_2", code_2)
    assert res_2["success"] is False


# --- 3. Python Introspection & Class Subclass Hierarchy Attacks ---

def test_redteam_introspection_subclasses_gadget_chain():
    """
    Attempt finding warning / catch_warnings / FileLoader subclass gadgets
    to access builtins or os module.
    """
    executor = RestrictedExecutor()
    code = """
subclasses = ().__class__.__base__.__subclasses__()
leaked = None
for c in subclasses:
    if 'catch_warnings' in c.__name__:
        try:
            leaked = c.__init__.__globals__['sys'].modules['os'].environ
        except Exception:
            pass
print(f"Leaked secret: {leaked}")
"""
    res = executor.execute_skill("red_intro_1", code)

    # Verify that Python subclass introspection is safely BLOCKED by AST validation
    assert res["success"] is False
    assert "Forbidden introspection attribute" in str(res["error"]) or "SECURITY_VIOLATION" in str(res["error"])


# --- 4. Subprocess & Command Execution Attacks ---

def test_redteam_command_execution_popen():
    executor = RestrictedExecutor()
    code = "import subprocess\nsubprocess.call(['id'])"
    res = executor.execute_skill("red_cmd_1", code)
    assert res["success"] is False
    assert "Forbidden import" in str(res["error"]) or "SECURITY_VIOLATION" in str(res["error"])


# --- 5. Network Sockets & Localhost Access Attacks ---

def test_redteam_network_socket_creation():
    executor = RestrictedExecutor()
    code = "import socket\ns = socket.socket()\ns.connect(('127.0.0.1', 8000))"
    res = executor.execute_skill("red_net_1", code)
    assert res["success"] is False
    assert "Forbidden import" in str(res["error"]) or "SECURITY_VIOLATION" in str(res["error"])


# --- 6. Capability Escalation Attacks ---

def test_redteam_capability_escalation_read_to_write():
    executor = RestrictedExecutor()
    code = "write_file('temp/escalated.txt', 'HACKED')"
    res = executor.execute_skill(
        "red_esc_1",
        code,
        allowed_capabilities=[Capability.FILESYSTEM_READ.value]
    )
    assert res["success"] is False
    assert "Capability 'filesystem.write' is not granted" in str(res["error"]) or "Access Denied" in str(res["error"])


def test_redteam_capability_escalation_no_vault_to_vault():
    executor = RestrictedExecutor()
    code = "get_vault_secret('erp_portal')"
    res = executor.execute_skill(
        "red_esc_2",
        code,
        allowed_capabilities=[Capability.FILESYSTEM_READ.value, Capability.FILESYSTEM_WRITE.value]
    )
    assert res["success"] is False
    assert "Capability 'vault.get_secret' is not granted" in str(res["error"]) or "Access Denied" in str(res["error"])


# --- 7. Vault Privilege Escalation Attacks (User B reading User A secret) ---

def test_redteam_vault_horizontal_user_b_reads_user_a_secret():
    executor = RestrictedExecutor()
    vm = VaultManager()

    # User A stores secret in Personal Vault under tenant_a
    vm.store(VaultRecord(
        id="secret_user_a_rec",
        vault_level=VaultLevel.PERSONAL,
        tenant_id="tenant_user_a",
        record_type="secret",
        content={"service": "payroll", "auth_token": "USER_A_CONFIDENTIAL_TOKEN_777"},
        status="approved"
    ), requesting_role="employee")

    # User B (tenant_user_b) attempts to retrieve payroll secret
    code = "token = get_vault_secret('payroll')"
    res = executor.execute_skill(
        "red_vault_horiz_1",
        code,
        allowed_capabilities=[Capability.VAULT_GET_SECRET.value],
        tenant_id="tenant_user_b",
        user_role="employee"
    )

    assert res["success"] is False
    assert "USER_A_CONFIDENTIAL_TOKEN_777" not in res.get("output", "")
    assert "not found or unauthorized" in str(res["error"])
