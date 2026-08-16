"""
Quantifiable Verification & Proof Generator for Xenia.

Executes:
1. Full backend pytest test suite
2. Vertical slice pilot pipeline (Primary & Secondary scenarios)
3. UI feature & html integrity check
4. Writes verifiable evidence, latency logs, and audit summary to verification_evidence_report.json
"""

import sys
import os
import json
import time
import subprocess

from platform_core.pilot_pipeline import PilotPipelineRunner


def run_backend_pytest():
    print("[Verification] Running full backend pytest suite...")
    t0 = time.time()
    res = subprocess.run(["python3", "-m", "pytest", "--tb=short"], capture_output=True, text=True)
    latency_ms = int((time.time() - t0) * 1000)
    passed = (res.returncode == 0) and ("passed" in res.stdout) and ("FAILED" not in res.stdout)
    print(f"  Pytest result: {'PASSED' if passed else 'FAILED'} ({latency_ms}ms)")
    return {
        "passed": passed,
        "latency_ms": latency_ms,
        "output_summary": res.stdout.splitlines()[-2] if res.stdout else ""
    }


def run_pilot_closed_loop_proofs():
    print("[Verification] Running Pilot Closed-Loop Pipeline Proofs...")
    runner = PilotPipelineRunner(tenant_id="verification_tenant")

    # Primary Scenario
    t0 = time.time()
    primary_res = runner.run_full_closed_loop("invoice_processing")
    primary_ms = int((time.time() - t0) * 1000)

    # Secondary Scenario
    t0 = time.time()
    secondary_res = runner.run_full_closed_loop("weekly_report")
    secondary_ms = int((time.time() - t0) * 1000)

    print(f"  Primary Scenario (Invoice Processing): {'PASSED' if primary_res['success'] else 'FAILED'} in {primary_ms}ms")
    print(f"  Secondary Scenario (Weekly Report): {'PASSED' if secondary_res['success'] else 'FAILED'} in {secondary_ms}ms")

    return {
        "primary_scenario": primary_res,
        "secondary_scenario": secondary_res
    }


def run_ui_integrity_proofs():
    print("[Verification] Running UI HTML & JS integrity verification...")
    features = [
        'startVoiceCapture', 'handleCanvasDrop', 'handleSidebarDragStart',
        'nodes_json', 'voice-modal', 'drag-over', 'voice-pulse',
        'loadAutoIntoCanvas', 'deleteAuto', 'confirmDeleteAuto',
        'loadMyAutomations', 'saveAndRunFlow', 'generateFlowScript',
        'buildFlowFromVoice', 'renderFlowCanvas',
        'openNodeConfig', 'saveNodeConfig', 'insertConditionNode',
        'removeNode', 'clearFlowCanvas', 'addTriggerNode', 'addActionNode'
    ]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, 'ui', 'index.html')

    with open(index_path, encoding='utf-8') as f:
        html = f.read()

    found = []
    missing = []
    for feat in features:
        if feat in html:
            found.append(feat)
        else:
            missing.append(feat)

    all_ok = len(missing) == 0
    print(f"  UI Integrity: {len(found)}/{len(features)} features verified in index.html (Total HTML size: {len(html):,} chars)")

    return {
        "passed": all_ok,
        "total_html_chars": len(html),
        "verified_features_count": len(found),
        "missing_features": missing
    }


def generate_proof_report():
    print("==================================================")
    print("XENIA OFFICIAL BUILD & VERIFICATION PROOF SUITE")
    print("==================================================")

    pytest_proof = run_backend_pytest()
    pipeline_proof = run_pilot_closed_loop_proofs()
    ui_proof = run_ui_integrity_proofs()

    overall_passed = pytest_proof["passed"] and pipeline_proof["primary_scenario"]["success"] and pipeline_proof["secondary_scenario"]["success"] and ui_proof["passed"]

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "overall_status": "VERIFIED_PRODUCTION_READY" if overall_passed else "FAILED",
        "quantifiable_proofs": {
            "backend_pytest": pytest_proof,
            "pilot_pipeline_primary_invoice": pipeline_proof["primary_scenario"],
            "pilot_pipeline_secondary_report": pipeline_proof["secondary_scenario"],
            "ui_frontend_integrity": ui_proof
        }
    }

    report_path = "verification_evidence_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n==================================================")
    print(f"VERIFICATION STATUS: {report['overall_status']}")
    print(f"Evidence Report written to: {report_path}")
    print("==================================================")

    return overall_passed


if __name__ == "__main__":
    success = generate_proof_report()
    sys.exit(0 if success else 1)
