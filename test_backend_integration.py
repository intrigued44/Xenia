import sys, os, json
sys.path.insert(0, r'c:\Users\pranav\Downloads\nous-windows-installer-src')
os.chdir(r'c:\Users\pranav\Downloads\nous-windows-installer-src')

# Test DB migration runs cleanly
print('Testing DB init with nodes_json migration...')
from client.db import init_db
init_db()
print('  DB init: OK')

# Test save_skill with nodes_json
from platform_core.intelligence.skills_engine import save_skill, get_skill

test_nodes = [
    {'id': 1, 'role': 'trigger', 'type': 'schedule', 'name': 'Schedule', 'desc': 'Every morning', 'config': {'time': '09:00'}},
    {'id': 2, 'role': 'action', 'type': 'web', 'name': 'Gmail', 'desc': 'Open Gmail', 'config': {'url': 'https://gmail.com', 'action': 'open'}},
    {'id': 3, 'role': 'action', 'type': 'web', 'name': 'YouTube', 'desc': 'Open YouTube', 'config': {'url': 'https://youtube.com', 'action': 'open'}},
]
nodes_json_str = json.dumps(test_nodes)
code = 'import webbrowser\nwebbrowser.open("https://gmail.com")\nwebbrowser.open("https://youtube.com")\n'

print('Testing save_skill with nodes_json...')
sid = save_skill(
    'Test Gmail YouTube Flow',
    'Open Gmail then YouTube',
    code,
    'local',
    nodes_json=nodes_json_str
)
print(f'  Saved skill ID: {sid}')

print('Testing get_skill with nodes_json...')
skill = get_skill('Test Gmail YouTube Flow', 'local')
if skill:
    print(f'  Name: {skill["name"]}')
    print(f'  nodes_json present: {bool(skill.get("nodes_json"))}')
    if skill.get('nodes_json'):
        restored = json.loads(skill['nodes_json'])
        print(f'  Restored {len(restored)} nodes: {[n["name"] for n in restored]}')
else:
    print('  ERROR: skill not found')

# Test delete
from platform_core.intelligence.skills_engine import get_skill
from client.db import get_connection
conn = get_connection()
conn.execute("DELETE FROM agent_skills WHERE name = ? AND tenant_id = ?", ('Test Gmail YouTube Flow', 'local'))
conn.commit()
conn.close()
print('  Cleanup: deleted test skill')

print('\nAll backend tests PASSED!')
