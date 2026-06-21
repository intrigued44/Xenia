import uuid
import time
import json
import sqlite3
from client.db import get_connection

def create_tenant(name: str, plan: str, admin_email: str) -> dict:
    tenant_id = str(uuid.uuid4())
    api_key = f"sk_{tenant_id}_{str(uuid.uuid4()).replace('-', '')}"
    
    feature_flags = {
        "max_users": 100 if plan == "enterprise" else 1 if plan == "individual" else 10,
        "connectors_allowed": ["desktop_observer", "gmail", "gcal"] if plan in ["business", "enterprise"] else ["desktop_observer"],
        "agents_enabled": ["workflow", "knowledge"] if plan in ["team", "business", "enterprise"] else ["workflow"],
        "company_brain": plan in ["team", "business", "enterprise"],
        "api_access": plan in ["business", "enterprise"],
        "on_premise": plan == "enterprise"
    }
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plan TEXT NOT NULL,
            admin_email TEXT NOT NULL,
            feature_flags TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            api_key TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        INSERT INTO tenants (id, name, plan, admin_email, feature_flags, created_at, api_key)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tenant_id, name, plan, admin_email, json.dumps(feature_flags), int(time.time()), api_key))
    
    conn.commit()
    conn.close()
    
    return {"tenant_id": tenant_id, "api_key": api_key, "plan": plan, "features": feature_flags}

def get_tenant(tenant_id: str) -> dict:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    except Exception as e:
        import logging
        logging.error(f"context: {e}", exc_info=True) # Table doesn't exist
    finally:
        conn.close()
    return None

def update_tenant(tenant_id: str, config: dict) -> bool:
    # MVP update logic
    return True
    
def add_user(tenant_id: str, user_email: str, role: str) -> dict:
    user_id = str(uuid.uuid4())
    user_api_key = f"sk_{tenant_id}_{str(uuid.uuid4()).replace('-', '')}"
    return {"user_id": user_id, "email": user_email, "role": role, "api_key": user_api_key}

def list_users(tenant_id: str) -> list:
    return [{"user_id": "anon", "email": "admin@local", "role": "admin"}]
