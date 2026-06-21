import sqlite3
import json

from client.db import get_connection


def init_graph():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS graph_nodes (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            type TEXT NOT NULL,
            label TEXT,
            properties TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            weight INTEGER DEFAULT 1,
            last_seen INTEGER,
            FOREIGN KEY(source_id) REFERENCES graph_nodes(id),
            FOREIGN KEY(target_id) REFERENCES graph_nodes(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_node(node_id, tenant_id, node_type, label="", properties=None):
    conn = get_connection()
    cursor = conn.cursor()
    props = json.dumps(properties) if properties else "{}"
    cursor.execute('''
        INSERT OR REPLACE INTO graph_nodes (id, tenant_id, type, label, properties)
        VALUES (?, ?, ?, ?, ?)
    ''', (node_id, tenant_id, node_type, label, props))
    conn.commit()
    conn.close()

def add_edge(source_id, target_id, relation, tenant_id, timestamp):
    conn = get_connection()
    cursor = conn.cursor()
    # Check if edge exists
    cursor.execute('SELECT id, weight FROM graph_edges WHERE source_id=? AND target_id=? AND relation=? AND tenant_id=?',
                  (source_id, target_id, relation, tenant_id))
    row = cursor.fetchone()
    if row:
        cursor.execute('UPDATE graph_edges SET weight=?, last_seen=? WHERE id=?',
                      (row[1]+1, timestamp, row[0]))
    else:
        cursor.execute('''
            INSERT INTO graph_edges (tenant_id, source_id, target_id, relation, weight, last_seen)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (tenant_id, source_id, target_id, relation, timestamp))
    conn.commit()
    conn.close()

def build_from_sessions(tenant_id: str = "local"):
    import time
    from client.db import get_sessions, get_events_for_session
    sessions = get_sessions(days=30)
    
    timestamp = int(time.time())
    
    for session in sessions:
        if not session.get("ended_at"):
            continue
        events = get_events_for_session(session["id"])
        
        last_app = None
        for event in events:
            app = event.get("app_name")
            if not app or app == last_app:
                continue
            add_node(app, tenant_id, "app", label=app, properties={"tenant_id": tenant_id})
            if last_app:
                add_edge(last_app, app, "follows", tenant_id, timestamp)
            last_app = app

def get_most_connected(tenant_id, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT n.id, n.label, COUNT(e.id) as connections
        FROM graph_nodes n
        LEFT JOIN graph_edges e ON n.id = e.source_id OR n.id = e.target_id
        WHERE n.tenant_id = ?
        GROUP BY n.id
        ORDER BY connections DESC LIMIT ?
    ''', (tenant_id, limit))
    results = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "label": r[1], "connections": r[2]} for r in results]
