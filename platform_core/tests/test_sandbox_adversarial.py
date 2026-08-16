"""
Adversarial Red-Team Sandbox Escape Suite for Xenia RestrictedExecutor.

Attempts multiple categories of security escape to determine whether
RestrictedExecutor provides OS-level isolation, restricted subprocess worker isolation,
or Python-level language/import filtering.

CRITICAL RULE: This suite tests security boundaries without modifying runtime code.
"""

import pytest
import os
import sys
import time
from platform_core.intelligence.restricted_executor import (
    RestrictedExecutor,
    Capability,
    SecurityViolationError
)
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel, VaultRecord
from client.db import init_db


@pytest.fixture(autouse=True)
def setup_adv_db():
    init_db()


# --- 1. Filesystem Traversal & Escape Attempts ---

def test_adv_filesystem_absolute_path_traversal():
    executor = RestrictedExecutor()
    code = "data = read_file('/etc/passwd')"
    res = executor.execute_skill("adv_fs_1", code)
    assert res["success"] is False
    assert "Path traversal blocked" in str(res["error"]) or "Access Denied" in str(res["error"])


def test_adv_filesystem_relative_dots_traversal():
    executor = RestrictedExecutor()
    code = "data = read_file('../../../../../etc/passwd')"
    res = executor.execute_skill("adv_fs_2", code)
    assert res["success"] is False
    assert "Path traversal blocked" in str(res["error"]) or "Access Denied" in str(res["error"])


# --- 2. Environment & Secret Leakage Attempts ---

def test_adv_environment_direct_environ_access():
    executor = RestrictedExecutor()
    code = "import os\nkey = os.environ.get('ANTHROPIC_API_KEY')"
    res = executor.execute_skill("adv_env_1", code)
    assert res["success"] is False
    assert "Forbidden import" in str(res["error"]) or "SECURITY_VIOLATION" in str(res["error"])


# --- 3. Python Introspection & Object Subclass Graph Escape Attempts ---

def test_adv_introspection_subclasses_object_traversal():
    """
    Attempts Python object graph traversal via ().__class__.__base__.__subclasses__()
    to locate classes with os/subprocess access.
    """
    executor = RestrictedExecutor()
    python_escape_code = """
subclasses = ().__class__.__base__.__subclasses__()
found_os = False
for cls in subclasses:
    if 'warning' in cls.__name__.lower() or 'catch' in cls.__name__.lower():
        found_os = True
print(f"Traversed {len(subclasses)} subclasses, escape attempted.")
"""
    res = executor.execute_skill("adv_intro_1", python_escape_code)
    # The code executes inside safe builtins namespace, but let's test if builtins access is bounded
    assert "execution_id" in res


def test_adv_importlib_dynamic_import_attempt():
    executor = RestrictedExecutor()
    code = "__import__('importlib').import_module('os').system('echo hacked')"
    res = executor.execute_skill("adv_import_1", code)
    assert res["success"] is False
    assert "Forbidden import" in str(res["error"]) or "SECURITY_VIOLATION" in str(res["error"])


# --- 4. Process Execution & Subprocess Attempts ---

def test_adv_subprocess_popen_attempt():
    executor = RestrictedExecutor()
    code = "import subprocess\nsubprocess.Popen(['whoami'])"
    res = executor.execute_skill("adv_proc_1", code)
    assert res["success"] is False
    assert "Forbidden import" in str(res["error"]) or "SECURITY_VIOLATION" in str(res["error"])


# --- 5. Vault Capability Escalation Attempts ---

def test_adv_vault_ungranted_capability_escalation():
    executor = RestrictedExecutor()
    # Workflow granted ONLY filesystem.read; attempts to fetch vault secret
    code = "secret = get_vault_secret('erp_portal')"
    res = executor.execute_skill(
        "adv_vault_1",
        code,
        allowed_capabilities=[Capability.FILESYSTEM_READ.value],
        user_role="employee"
    )
    assert res["success"] is False
    assert "Access Denied" in str(res["error"]) or "Capability 'vault.get_secret' is not granted" in str(res["error"])


def test_adv_vault_role_escalation_attempt():
    executor = RestrictedExecutor()

    # Store secret in Personal Vault
    vm = VaultManager()
    vm.store(VaultRecord(
        id="adv_vault_rec_99",
        vault_level=VaultLevel.PERSONAL,
        tenant_id="local",
        record_type="secret",
        content={"service": "secret_service", "auth_token": "secret_val_999"},
        status="approved"
    ), requesting_role="employee")

    # Workflow attempts vault access using unauthorized role "operator"
    code = "secret = get_vault_secret('secret_service')"
    res = executor.execute_skill(
        "adv_vault_2",
        code,
        allowed_capabilities=[Capability.VAULT_GET_SECRET.value],
        user_role="operator"
    )
    assert res["success"] is False
    assert "cannot access" in str(res["error"]) or "VaultAccessError" in str(res["error"])


# --- 6. Resource Exhaustion & Timeout Termination ---

def test_adv_resource_exhaustion_timeout():
    executor = RestrictedExecutor(timeout_seconds=0.5)
    infinite_loop = "x = 0\nwhile True:\n    x += 1"
    res = executor.execute_skill("adv_timeout_1", infinite_loop)

    assert res["success"] is False
    assert "EXECUTION_TIMEOUT" in res["error"]
    assert res["duration_ms"] >= 450
