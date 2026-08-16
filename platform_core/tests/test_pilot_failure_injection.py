import pytest
import time
import json
from fastapi.testclient import TestClient
from platform_core.server import app
from client.db import init_db, get_connection
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel
from platform_core.vaults.access_control import VaultAccessError
from platform_core.intelligence.restricted_executor import RestrictedExecutor, Capability
from platform_core.intelligence.skills_engine import run_and_heal_skill
from platform_core.llm_provider import call_llm
from platform_core.pilot_harness import PilotHarness

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_fail_db():
    init_db()


# 1. Authentication Failure Injection
def test_fail_auth_invalid_api_key():
    resp = client.get("/v1/mydata", headers={"x-api-key": "invalid-token-000"})
    assert resp.status_code == 401
    assert "Invalid API Key" in resp.json()["detail"]


# 2. Vault Failure Injection
def test_fail_vault_missing_credential():
    vm = VaultManager()
    results = vm.retrieve(VaultLevel.PERSONAL, "fail_tenant", record_type="secret", requesting_role="employee")
    assert len(results) == 0


def test_fail_vault_unauthorized_role_access():
    vm = VaultManager()
    with pytest.raises(VaultAccessError):
        vm.retrieve(VaultLevel.PERSONAL, "fail_tenant", requesting_role="manager")


# 3. Sandbox Capability Failure Injection
def test_fail_sandbox_capability_violation():
    executor = RestrictedExecutor()
    code = "write_file('temp/forbidden.txt', 'test')"
    res = executor.execute_skill("fail_cap_test", code, allowed_capabilities=[Capability.FILESYSTEM_READ.value])
    assert res["success"] is False
    assert "Access Denied" in res["error"]


def test_fail_sandbox_timeout_recovery():
    executor = RestrictedExecutor(timeout_seconds=0.5)
    infinite_code = "while True: pass"
    res = executor.execute_skill("fail_timeout_test", infinite_code)
    assert res["success"] is False
    assert "EXECUTION_TIMEOUT" in res["error"]


def test_fail_sandbox_runtime_exception():
    res = run_and_heal_skill("fail_runtime_test", "x = 1 / 0")
    assert res["success"] is False
    assert "ZeroDivisionError" in res["error"]


# 4. LLM Provider Fallback Injection
def test_fail_llm_provider_fallback(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "invalid_api_key_for_test")

    # On invalid key/network failure, call_llm falls back gracefully to MockLLMProvider
    text = call_llm("Generate workflow script", max_tokens=100)
    assert len(text) > 0


# 5. Connected Pilot Harness Execution
def test_connected_pilot_harness_success():
    harness = PilotHarness(tenant_id="harness_tenant_01")
    res = harness.run_connected_harness("Invoice Ingestion Harness Flow")

    assert res["status"] == "COMPLETED_CONNECTED_HARNESS"
    assert res["overall_success"] is True
    assert res["telemetry"]["stage_1_2_events"]["event_count"] == 3
    assert res["telemetry"]["stage_9_10_execution"]["success"] is True
