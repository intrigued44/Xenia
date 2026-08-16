import pytest
import time
import json
from client.db import init_db, get_connection
from platform_core.pilot_pipeline import PilotPipelineRunner
from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel
from platform_core.vaults.access_control import VaultAccessError


@pytest.fixture(autouse=True)
def setup_pipeline_db():
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions")
    c.execute("DELETE FROM window_logs")
    c.execute("DELETE FROM workflows")
    c.execute("DELETE FROM vault_records")
    c.execute("DELETE FROM pending_approvals")
    c.execute("DELETE FROM agent_skills")
    conn.commit()
    conn.close()


def test_invoice_processing_closed_loop():
    runner = PilotPipelineRunner(tenant_id="test_tenant")
    res = runner.run_full_closed_loop(scenario_name="invoice_processing")

    assert res["success"] is True
    assert res["total_latency_ms"] > 0
    telemetry = res["telemetry"]

    # Verify Stage 1: Observation
    assert telemetry["stage_1_observation"]["status"] == "completed"
    assert telemetry["stage_1_observation"]["session_id"].startswith("sess_pilot_")

    # Verify Stage 2: Mining
    assert telemetry["stage_2_process_mining"]["confidence"] == 0.92
    assert "Invoice Ingestion" in telemetry["stage_2_process_mining"]["discovered_workflow_name"]

    # Verify Stage 3: Generation
    assert telemetry["stage_3_workflow_generation"]["step_count"] == 4

    # Verify Stage 4: Approval & Vault
    assert telemetry["stage_4_approval_vault"]["status"] == "approved"
    assert telemetry["stage_4_approval_vault"]["vault_secret_retrieved"] is True

    # Verify Stage 5: Execution
    assert telemetry["stage_5_execution"]["success"] is True
    assert "Posted invoice successfully" in telemetry["stage_5_execution"]["output"]

    # Verify Stage 6: Grounded Q&A
    assert len(telemetry["stage_6_grounded_qa"]["answer"]) > 0
    assert telemetry["stage_6_grounded_qa"]["evidence"]["workflow_record"] is not None


def test_weekly_report_closed_loop():
    runner = PilotPipelineRunner(tenant_id="test_tenant_2")
    res = runner.run_full_closed_loop(scenario_name="weekly_report")

    assert res["success"] is True
    assert res["scenario"] == "weekly_report"
    telemetry = res["telemetry"]

    assert telemetry["stage_1_observation"]["status"] == "completed"
    assert telemetry["stage_5_execution"]["success"] is True


def test_closed_loop_repeated_runs_determinism():
    runner = PilotPipelineRunner(tenant_id="repeat_tenant")
    res1 = runner.run_full_closed_loop(scenario_name="invoice_processing")
    res2 = runner.run_full_closed_loop(scenario_name="invoice_processing")

    assert res1["success"] is True
    assert res2["success"] is True
    assert res1["telemetry"]["stage_3_workflow_generation"]["step_count"] == res2["telemetry"]["stage_3_workflow_generation"]["step_count"]


def test_unauthorized_vault_access_in_pipeline():
    vm = VaultManager()
    with pytest.raises(VaultAccessError):
        vm.retrieve(VaultLevel.PERSONAL, "test_tenant", requesting_role="unauthorized_role")
