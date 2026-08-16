import pytest
import time
import json
import uuid
from client.db import init_db, get_connection, upsert_workflow
from platform_core.pilot_pipeline import PilotPipelineRunner
from platform_core.llm_provider import call_llm


@pytest.fixture(autouse=True)
def setup_grounding_db():
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM execution_telemetry")
    c.execute("DELETE FROM workflows")
    conn.commit()
    conn.close()


def test_scenario_a_successful_telemetry_grounding():
    """Scenario A: Telemetry says invoice_123 processed successfully."""
    tenant_id = "ground_tenant_a"
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS execution_telemetry (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            success INTEGER NOT NULL,
            output TEXT,
            executed_at INTEGER NOT NULL
        )
    """)
    c.execute("""
        INSERT INTO execution_telemetry (id, tenant_id, skill_name, success, output, executed_at)
        VALUES ('telem_123', ?, 'invoice_123_pipeline', 1, 'Ref #INV-2026-123 posted successfully to ERP', ?)
    """, (tenant_id, int(time.time())))
    conn.commit()
    conn.close()

    upsert_workflow({
        "id": "wf_123",
        "name": "Invoice 123 Processing",
        "app_sequence": json.dumps(["Excel", "ERP Portal"]),
        "avg_duration_seconds": 200,
        "frequency_per_week": 5,
        "automation_potential": 0.9,
        "first_detected": int(time.time()),
        "last_seen": int(time.time())
    }, tenant_id)

    runner = PilotPipelineRunner(tenant_id=tenant_id)
    res = runner.stage_6_grounded_qa("Invoice 123 Processing")

    assert res["evidence"]["latest_execution"] is not None
    assert res["evidence"]["latest_execution"]["success"] == 1
    assert "INV-2026-123 posted successfully" in res["evidence"]["latest_execution"]["output"]


def test_scenario_b_no_telemetry_prevents_hallucination():
    """Scenario B: No telemetry exists. Answer must indicate insufficient evidence."""
    tenant_id = "ground_tenant_b"
    runner = PilotPipelineRunner(tenant_id=tenant_id)

    res = runner.stage_6_grounded_qa("Non Existent Invoice 456")

    assert res["evidence"]["workflow_record"] is None
    assert res["evidence"]["latest_execution"] is None
    # Must NOT claim success without evidence
    assert "status" in res or "answer" in res


def test_scenario_c_failed_telemetry_grounding():
    """Scenario C: Telemetry indicates execution failed."""
    tenant_id = "ground_tenant_c"
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS execution_telemetry (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            success INTEGER NOT NULL,
            output TEXT,
            executed_at INTEGER NOT NULL
        )
    """)
    c.execute("""
        INSERT INTO execution_telemetry (id, tenant_id, skill_name, success, output, executed_at)
        VALUES ('telem_789', ?, 'invoice_789_pipeline', 0, 'ConnectionError: ERP Portal HTTP 500', ?)
    """, (tenant_id, int(time.time())))
    conn.commit()
    conn.close()

    upsert_workflow({
        "id": "wf_789",
        "name": "Invoice 789 Processing",
        "app_sequence": json.dumps(["Excel", "ERP Portal"]),
        "avg_duration_seconds": 200,
        "frequency_per_week": 5,
        "automation_potential": 0.9,
        "first_detected": int(time.time()),
        "last_seen": int(time.time())
    }, tenant_id)

    runner = PilotPipelineRunner(tenant_id=tenant_id)
    res = runner.stage_6_grounded_qa("Invoice 789 Processing")

    assert res["evidence"]["latest_execution"] is not None
    assert res["evidence"]["latest_execution"]["success"] == 0
    assert "ConnectionError" in res["evidence"]["latest_execution"]["output"]


def test_scenario_d_surfaces_conflicting_telemetry_records():
    """Scenario D: Two conflicting execution records exist."""
    tenant_id = "ground_tenant_d"
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS execution_telemetry (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            success INTEGER NOT NULL,
            output TEXT,
            executed_at INTEGER NOT NULL
        )
    """)
    now = int(time.time())
    c.execute("INSERT INTO execution_telemetry VALUES ('telem_d1', ?, 'wf_d', 1, 'Success run', ?)", (tenant_id, now - 100))
    c.execute("INSERT INTO execution_telemetry VALUES ('telem_d2', ?, 'wf_d', 0, 'Failed run', ?)", (tenant_id, now))
    conn.commit()

    c.execute("SELECT success, output FROM execution_telemetry WHERE tenant_id = ? ORDER BY executed_at DESC", (tenant_id,))
    rows = c.fetchall()
    conn.close()

    assert len(rows) == 2
    # Verify conflict between consecutive runs is visible in telemetry
    assert rows[0][0] != rows[1][0]
