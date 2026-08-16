import pytest
import time
import json
from client.db import init_db, get_connection, create_session, log_event
from client.pii_filter import sanitize
from client.preprocessor import build_analysis_context
from platform_core.intelligence.classifier import PatternClassifier
from platform_core.intelligence.restricted_executor import RestrictedExecutor, Capability
from platform_core.pilot_pipeline import PilotPipelineRunner


@pytest.fixture(autouse=True)
def setup_perf_db():
    init_db()


def test_performance_baseline_metrics():
    baseline_results = {}

    # 1. DB Initialization & Connection Latency
    t0 = time.time()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1")
    c.fetchone()
    conn.close()
    baseline_results["db_query_ms"] = int((time.time() - t0) * 1000)

    # 2. PII Sanitization Latency
    t0 = time.time()
    for _ in range(100):
        sanitize("User email user@corp.com with SSN 123-45-6789 and card 4111-2222-3333-4444")
    baseline_results["pii_100_runs_ms"] = int((time.time() - t0) * 1000)

    # 3. Process Mining Latency
    t0 = time.time()
    context = build_analysis_context(days=7)
    classifier = PatternClassifier()
    classifier.classify_all_patterns(context.get("detected_patterns", []))
    baseline_results["process_mining_ms"] = int((time.time() - t0) * 1000)

    # 4. Restricted Executor Sandbox Latency
    t0 = time.time()
    executor = RestrictedExecutor()
    executor.execute_skill(
        "perf_skill",
        "write_file('temp/perf.txt', 'test'); data = read_file('temp/perf.txt'); print(data)",
        allowed_capabilities=[Capability.FILESYSTEM_READ.value, Capability.FILESYSTEM_WRITE.value]
    )
    baseline_results["sandbox_execution_ms"] = int((time.time() - t0) * 1000)

    # 5. Connected Pilot Pipeline Total Latency
    runner = PilotPipelineRunner(tenant_id="perf_tenant")
    pipeline_res = runner.run_full_closed_loop("invoice_processing")
    baseline_results["pipeline_total_ms"] = pipeline_res["total_latency_ms"]

    print("\n==================================================")
    print("XENIA PERFORMANCE BASELINE LATENCY MEASUREMENTS:")
    print("==================================================")
    for metric, latency in baseline_results.items():
        print(f"  - {metric}: {latency}ms")
    print("==================================================")

    assert baseline_results["db_query_ms"] < 100
    assert baseline_results["pipeline_total_ms"] < 5000
