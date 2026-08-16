import sqlite3
import os
from datetime import datetime
import json

DB_PATH = 'mvp_data.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_vault_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vault_records (
            id TEXT PRIMARY KEY,
            vault_level TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            contributor_hash TEXT DEFAULT '',
            record_type TEXT,
            content TEXT,
            metadata TEXT DEFAULT '{}',
            created_at INTEGER,
            approved_by TEXT,
            approved_at INTEGER,
            status TEXT DEFAULT 'approved'
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_vault_level_tenant
        ON vault_records(vault_level, tenant_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_vault_record_type
        ON vault_records(record_type, tenant_id)
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contribution_requests (
            id TEXT PRIMARY KEY,
            from_vault TEXT NOT NULL,
            to_vault TEXT NOT NULL,
            record_id TEXT NOT NULL,
            contributor_hash TEXT DEFAULT '',
            summary TEXT,
            tenant_id TEXT NOT NULL,
            created_at INTEGER,
            status TEXT DEFAULT 'pending',
            resolved_at INTEGER
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_contrib_tenant
        ON contribution_requests(tenant_id, status)
    ''')
    conn.commit()
    conn.close()

def init_db():
    init_vault_tables()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS window_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            app_name TEXT,
            window_title TEXT,
            tenant_id TEXT DEFAULT 'local'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screen_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            window_title TEXT,
            image_path TEXT,
            tenant_id TEXT DEFAULT 'local',
            extracted_text TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            user_id TEXT,
            action TEXT,
            resource TEXT,
            details TEXT,
            timestamp INTEGER,
            event_type TEXT,
            source_system TEXT,
            actor TEXT,
            context TEXT,
            ip_address TEXT,
            target TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clipboard_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            text_content TEXT,
            app_context TEXT,
            tenant_id TEXT DEFAULT 'local'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT,
            file_path TEXT,
            tenant_id TEXT DEFAULT 'local'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            started_at INTEGER NOT NULL,
            ended_at INTEGER,
            primary_app TEXT,
            workflow_label TEXT,
            automation_score REAL,
            tenant_id TEXT DEFAULT 'local'
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_time ON sessions(started_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON sessions(tenant_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT REFERENCES sessions(id),
            timestamp INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            app_name TEXT,
            metadata TEXT,
            tenant_id TEXT DEFAULT 'local'
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_time ON events(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_tenant ON events(tenant_id)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflows (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            app_sequence TEXT,
            avg_duration_seconds INTEGER,
            frequency_per_week REAL,
            automation_potential REAL,
            first_detected INTEGER,
            last_seen INTEGER,
            tenant_id TEXT DEFAULT 'local'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            goal TEXT,
            status TEXT,
            created_at INTEGER,
            completed_at INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_steps (
            id TEXT PRIMARY KEY,
            plan_id TEXT REFERENCES plans(id),
            tool_name TEXT,
            params TEXT,
            depends_on TEXT,
            permission_tier TEXT,
            success_criteria TEXT,
            status TEXT,
            result TEXT,
            executed_at INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_approvals (
            id TEXT PRIMARY KEY,
            plan_id TEXT,
            step_id TEXT,
            tool_name TEXT,
            params_summary TEXT,
            status TEXT,
            tenant_id TEXT,
            created_at INTEGER,
            resolved_at INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_execution_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id TEXT,
            step_id TEXT,
            tool_name TEXT,
            status TEXT,
            result_summary TEXT,
            execution_time_ms INTEGER,
            timestamp INTEGER,
            tenant_id TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_automations (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            workflow_name TEXT,
            script_path TEXT,
            estimated_hours_saved_per_week REAL,
            status TEXT,
            created_at INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            severity TEXT,
            title TEXT,
            description TEXT,
            created_at INTEGER,
            status TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            type TEXT,
            title TEXT,
            description TEXT,
            proposed_action TEXT,
            permission_tier TEXT,
            estimated_value_minutes INTEGER,
            status TEXT,
            created_at INTEGER,
            resolved_at INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_skills (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            code_content TEXT,
            nodes_json TEXT,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            version INTEGER DEFAULT 1,
            tenant_id TEXT DEFAULT 'local',
            created_at INTEGER
        )
    ''')
    # Migration: add nodes_json if not present
    try:
        cursor.execute("ALTER TABLE agent_skills ADD COLUMN nodes_json TEXT")
    except Exception:
        pass  # Column already exists

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_memories (
            id TEXT PRIMARY KEY,
            agent_name TEXT,
            key TEXT,
            value TEXT,
            confidence REAL,
            tenant_id TEXT DEFAULT 'local',
            updated_at INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_conversations (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            message TEXT,
            tenant_id TEXT DEFAULT 'local',
            timestamp INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS installed_apps (
            name TEXT PRIMARY KEY,
            source TEXT DEFAULT 'installed',
            freq INTEGER DEFAULT 0,
            category TEXT DEFAULT 'other',
            path TEXT DEFAULT '',
            tenant_id TEXT DEFAULT 'local'
        )
    ''')

    # Simple migration logic for existing tables
    tables = ['window_logs', 'screen_logs', 'clipboard_logs', 'file_logs', 'sessions', 'events', 'workflows', 'plans', 'plan_steps', 'pending_approvals', 'plan_execution_log', 'pending_automations', 'alerts', 'proposals', 'agent_skills', 'agent_memories', 'agent_conversations', 'installed_apps']
    for table in tables:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            if 'tenant_id' not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN tenant_id TEXT DEFAULT 'local'")
        except Exception as e:
            import logging
            logging.error(f"context: {e}", exc_info=True)

    try:
        cursor.execute("ALTER TABLE screen_logs ADD COLUMN extracted_text TEXT")
    except Exception:
        pass

    # Create tenants table and seed API key safely without hardcoded production defaults
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT,
            api_key TEXT UNIQUE,
            plan TEXT DEFAULT 'enterprise',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    env = os.environ.get("ENV", "development").lower()
    test_mode = os.environ.get("XENIA_TEST_MODE", "1")
    custom_api_key = os.environ.get("XENIA_API_KEY") or os.environ.get("DEV_API_KEY")

    if custom_api_key:
        initial_key = custom_api_key
    elif env == "development" or test_mode == "1":
        initial_key = "sk-test-key-123"
    else:
        import secrets
        initial_key = f"sk-xenia-{secrets.token_hex(16)}"

    cursor.execute('''
        INSERT OR IGNORE INTO tenants (id, name, api_key, plan)
        VALUES ('tenant-local', 'Xenia Local', ?, 'enterprise')
    ''', (initial_key,))

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS execution_telemetry (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            success INTEGER NOT NULL,
            output TEXT,
            executed_at INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roi_logs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            time_saved_minutes REAL,
            cost_saved_cents INTEGER,
            token_cost_cents INTEGER,
            timestamp INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS llm_profiles (
            name TEXT PRIMARY KEY,
            latency_ms REAL,
            error_rate REAL,
            token_burn INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_runs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            workflow_name TEXT,
            status TEXT,
            logs TEXT,
            start_time INTEGER,
            end_time INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            id TEXT PRIMARY KEY,
            service_name TEXT,
            encrypted_token TEXT,
            tenant_id TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skill_script_versions (
            id TEXT PRIMARY KEY,
            skill_name TEXT,
            version INTEGER,
            diff TEXT,
            code_content TEXT,
            created_at INTEGER,
            tenant_id TEXT
        )
    ''')

    conn.commit()

    conn.close()

def log_window(app_name, window_title, tenant_id="local"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO window_logs (app_name, window_title, tenant_id) VALUES (?, ?, ?)', (app_name, window_title, tenant_id))
    conn.commit()
    conn.close()

def log_screen(window_title, image_path, tenant_id="local", extracted_text=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO screen_logs (window_title, image_path, tenant_id, extracted_text) VALUES (?, ?, ?, ?)', (window_title, image_path, tenant_id, extracted_text))
    conn.commit()
    conn.close()

def prune_old_screens(hours=1):
    conn = get_connection()
    cursor = conn.cursor()
    # Find records older than X hours
    cursor.execute("SELECT image_path FROM screen_logs WHERE timestamp < datetime('now', '-{} hours')".format(hours))
    old_screens = cursor.fetchall()
    
    for row in old_screens:
        path = row[0]
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    cursor.execute("DELETE FROM screen_logs WHERE timestamp < datetime('now', '-{} hours')".format(hours))
    conn.commit()
    conn.close()

def log_clipboard(text_content, app_context="", tenant_id="local"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO clipboard_logs (text_content, app_context, tenant_id) VALUES (?, ?, ?)', (text_content, app_context, tenant_id))
    conn.commit()

    conn.close()

def log_file_event(event_type, file_path, tenant_id="local"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO file_logs (event_type, file_path, tenant_id) VALUES (?, ?, ?)', (event_type, file_path, tenant_id))
    conn.commit()

    conn.close()

def create_session(session_id, started_at, primary_app, tenant_id="local"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sessions (id, started_at, primary_app, tenant_id) VALUES (?, ?, ?, ?)',
                   (session_id, started_at, primary_app, tenant_id))
    conn.commit()

    conn.close()

def close_session(session_id, ended_at, tenant_id="local"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE sessions SET ended_at = ? WHERE id = ? AND tenant_id = ?',
                   (ended_at, session_id, tenant_id))
    conn.commit()

    conn.close()

def log_event(session_id, event_type, app_name, metadata_dict, tenant_id="local"):
    conn = get_connection()
    cursor = conn.cursor()
    metadata = json.dumps(metadata_dict) if metadata_dict else None
    timestamp = int(datetime.now().timestamp())
    cursor.execute('INSERT INTO events (session_id, timestamp, event_type, app_name, metadata, tenant_id) VALUES (?, ?, ?, ?, ?, ?)',
                   (session_id, timestamp, event_type, app_name, metadata, tenant_id))
    conn.commit()

    conn.close()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_sessions(days=7, tenant_id="local"):
    conn = get_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    threshold = int(datetime.now().timestamp()) - (days * 86400)
    cursor.execute('SELECT * FROM sessions WHERE started_at >= ? AND tenant_id = ? ORDER BY started_at DESC', (threshold, tenant_id))
    sessions = cursor.fetchall()

    conn.close()
    return sessions

def get_events_for_session(session_id, tenant_id="local"):
    conn = get_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events WHERE session_id = ? AND tenant_id = ? ORDER BY timestamp ASC', (session_id, tenant_id))
    events = cursor.fetchall()

    conn.close()
    for e in events:
        if e['metadata']:
            try:
                e['metadata'] = json.loads(e['metadata'])
            except Exception as e:
                import logging
                logging.error(f"context: {e}", exc_info=True)
    return events

def upsert_workflow(workflow_dict, tenant_id="local"):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM workflows WHERE id = ? AND tenant_id = ?', (workflow_dict['id'], tenant_id))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute('''
            UPDATE workflows SET 
                name = ?, description = ?, app_sequence = ?, avg_duration_seconds = ?, 
                frequency_per_week = ?, automation_potential = ?, last_seen = ?
            WHERE id = ? AND tenant_id = ?
        ''', (
            workflow_dict.get('name'), workflow_dict.get('description'), workflow_dict.get('app_sequence'),
            workflow_dict.get('avg_duration_seconds'), workflow_dict.get('frequency_per_week'),
            workflow_dict.get('automation_potential'), workflow_dict.get('last_seen'),
            workflow_dict['id'], tenant_id
        ))
    else:
        cursor.execute('''
            INSERT INTO workflows (
                id, name, description, app_sequence, avg_duration_seconds, 
                frequency_per_week, automation_potential, first_detected, last_seen, tenant_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            workflow_dict['id'], workflow_dict.get('name'), workflow_dict.get('description'),
            workflow_dict.get('app_sequence'), workflow_dict.get('avg_duration_seconds'),
            workflow_dict.get('frequency_per_week'), workflow_dict.get('automation_potential'),
            workflow_dict.get('first_detected'), workflow_dict.get('last_seen'), tenant_id
        ))
        
    conn.commit()

    conn.close()

def get_workflows(tenant_id="local"):
    conn = get_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workflows WHERE tenant_id = ? ORDER BY last_seen DESC', (tenant_id,))
    workflows = cursor.fetchall()

    conn.close()
    return workflows

import uuid
import time

def insert_alert(alert: dict):
    conn = get_connection()
    cursor = conn.cursor()
    _id = alert.get("id", str(uuid.uuid4()))
    _time = alert.get("timestamp", int(time.time()))
    cursor.execute('''
        INSERT INTO alerts (id, tenant_id, severity, title, description, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, 'unread')
    ''', (_id, alert.get("tenant_id", "local"), alert.get("severity", "medium"), alert.get("title", ""), alert.get("description", ""), _time))
    conn.commit()

    conn.close()

def insert_proposal(proposal: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            type TEXT,
            title TEXT,
            description TEXT,
            proposed_action TEXT,
            permission_tier TEXT,
            estimated_value_minutes INTEGER,
            status TEXT DEFAULT 'pending',
            created_at INTEGER,
            resolved_at INTEGER
        )
    ''')
    cursor.execute('''
        INSERT OR REPLACE INTO proposals 
        (id, tenant_id, type, title, description, proposed_action, 
         permission_tier, estimated_value_minutes, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        proposal.get("id", str(uuid.uuid4())), proposal.get("tenant_id", "local"), proposal.get("type", "unknown"),
        proposal.get("title", ""), proposal.get("description", ""),
        proposal.get("proposed_action", ""), proposal.get("permission_tier", "confirm"),
        proposal.get("estimated_value_minutes", 0), proposal.get("status", "pending"),
        proposal.get("created_at", int(time.time()))
    ))
    conn.commit()

    conn.close()

def get_proposals(tenant_id: str, status: str = "pending") -> list:
    conn = get_connection()
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM proposals WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC",
            (tenant_id, status)
        )
        results = cursor.fetchall()
    except:
        results = []

    conn.close()
    return results

def get_unread_alerts(tenant_id: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE (status = 'unread' OR status IS NULL) AND tenant_id = ?", (tenant_id,))
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return results

def get_pending_approvals(tenant_id: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pending_approvals WHERE status = 'pending' AND tenant_id = ?", (tenant_id,))
    columns = [col[0] for col in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return results

def get_recent_logs(days=7, tenant_id="local"):
    conn = get_connection()
    cursor = conn.cursor()
    
    window_logs = cursor.execute(
        "SELECT timestamp, app_name, window_title FROM window_logs WHERE timestamp >= date('now', '-' || ? || ' days') AND tenant_id = ? ORDER BY timestamp DESC LIMIT 500", (days, tenant_id)
    ).fetchall()
    clipboard_logs = cursor.execute(
        "SELECT timestamp, text_content FROM clipboard_logs WHERE timestamp >= date('now', '-' || ? || ' days') AND tenant_id = ? ORDER BY timestamp DESC LIMIT 100", (days, tenant_id)
    ).fetchall()
    file_logs = cursor.execute(
        "SELECT timestamp, event_type, file_path FROM file_logs WHERE timestamp >= date('now', '-' || ? || ' days') AND tenant_id = ? ORDER BY timestamp DESC LIMIT 200", (days, tenant_id)
    ).fetchall()
    

    conn.close()
    
    return {
        "window_logs": window_logs,
        "clipboard_logs": clipboard_logs,
        "file_logs": file_logs
    }

def clear_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM window_logs')
    cursor.execute('DELETE FROM clipboard_logs')
    cursor.execute('DELETE FROM file_logs')
    conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
