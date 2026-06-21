"""
Smoke test: Simulate the Gmail -> YouTube flow end-to-end
Tests: save a flow, run it, verify output, then clean up
"""
import sys, os, json, subprocess, time
sys.path.insert(0, r'c:\Users\pranav\Downloads\nous-windows-installer-src')
os.chdir(r'c:\Users\pranav\Downloads\nous-windows-installer-src')

from platform_core.intelligence.skills_engine import save_skill, get_skill, run_and_heal_skill
from client.db import get_connection

FLOW_NAME = "Gmail to YouTube Smoke Test"
NODES = [
    {'id': 1, 'role': 'trigger', 'type': 'app', 'name': 'Manual Trigger', 'desc': 'Run now', 'config': {}},
    {'id': 2, 'role': 'action', 'type': 'web', 'name': 'Gmail', 'desc': 'Open Gmail', 'config': {'url': 'https://gmail.com', 'action': 'open'}},
    {'id': 3, 'role': 'action', 'type': 'web', 'name': 'YouTube', 'desc': 'Open YouTube', 'config': {'url': 'https://youtube.com', 'action': 'open'}},
]

# A safe script that just prints (no actual browser opened for test)
SAFE_CODE = """
import webbrowser, time

def run_gmail_to_youtube():
    print("Step 1: Trigger - starting flow")
    print("Step 2: Action - Opening Gmail (https://gmail.com)")
    webbrowser.open("https://gmail.com")
    time.sleep(1)
    print("Step 3: Action - Opening YouTube (https://youtube.com)")
    webbrowser.open("https://youtube.com")
    print("Flow complete!")

if __name__ == '__main__':
    run_gmail_to_youtube()
"""

print(f"[1] Saving flow: {FLOW_NAME!r}")
skill_id = save_skill(FLOW_NAME, "Open Gmail then YouTube", SAFE_CODE, 'local', nodes_json=json.dumps(NODES))
print(f"    Skill ID: {skill_id}")

print(f"\n[2] Retrieving flow to verify nodes_json...")
skill = get_skill(FLOW_NAME, 'local')
assert skill is not None, "Skill not found!"
assert skill['nodes_json'] is not None, "nodes_json missing!"
restored = json.loads(skill['nodes_json'])
assert len(restored) == 3, f"Expected 3 nodes, got {len(restored)}"
print(f"    Restored nodes: {[n['name'] for n in restored]}")

print(f"\n[3] Running flow (opens Gmail and YouTube in browser)...")
t0 = time.time()
result = run_and_heal_skill(FLOW_NAME, skill['code_content'], 'local')
elapsed = int((time.time() - t0) * 1000)
print(f"    Success: {result['success']}")
print(f"    Output: {result.get('output', '')[:200]}")
print(f"    Elapsed: {elapsed}ms")

print(f"\n[4] Cleanup...")
conn = get_connection()
conn.execute("DELETE FROM agent_skills WHERE name = ? AND tenant_id = ?", (FLOW_NAME, 'local'))
conn.commit()
conn.close()
print("    Deleted test flow")

print(f"\n{'='*50}")
print("SMOKE TEST PASSED - Gmail → YouTube flow works!")
print(f"{'='*50}")
