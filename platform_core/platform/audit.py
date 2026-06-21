import sqlite3
import time
import json
import hashlib
from client.db import get_connection

def _hash_params(params: dict) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()

def log_action(tenant_id: str, user_id: str, action_type: str, resource_type: str, resource_id: str, params: dict, result_status: str, ip_address: str = "127.0.0.1"):
    """
    Append-only audit log for compliance. Immutable.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            params_hash TEXT NOT NULL,
            result_status TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log(tenant_id)')
    
    cursor.execute('''
        INSERT INTO audit_log (tenant_id, user_id, action_type, resource_type, resource_id, params_hash, result_status, ip_address, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tenant_id, user_id, action_type, resource_type, resource_id, _hash_params(params), result_status, ip_address, int(time.time())))
    
    conn.commit()
    conn.close()

def get_audit_log(tenant_id: str, from_ts: int = 0, to_ts: int = None) -> list:
    if to_ts is None:
        to_ts = int(time.time())
        
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT * FROM audit_log 
            WHERE tenant_id = ? AND timestamp >= ? AND timestamp <= ? 
            ORDER BY timestamp DESC
        ''', (tenant_id, from_ts, to_ts))
        results = [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        results = [] # Table not created yet
    conn.close()
    return results
