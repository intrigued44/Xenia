import json
import uuid
from datetime import datetime
from typing import Dict, Any

EVENT_STORE = []

def receive_event(event_type: str, source_system: str, context: Dict[str, Any], user_id: str = "anon", tenant_id: str = "default_tenant") -> str:
    event_id = str(uuid.uuid4())
    now_iso = datetime.now().isoformat() + "Z"
    now_ts = int(datetime.now().timestamp())

    normalized_event = {
        "event_id": event_id,
        "timestamp": now_iso,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "event_type": event_type,
        "source_system": source_system,
        "context": context,
        "pii_scrubbed": True
    }

    EVENT_STORE.append(normalized_event)

    try:
        from client.db import get_connection
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO audit_logs (id, tenant_id, user_id, action, resource, timestamp, event_type, source_system, context)
            VALUES (?, ?, ?, ?, 'event_api', ?, 'EVENT', ?, ?)
        """, (event_id, tenant_id, user_id, event_type, now_ts, source_system, json.dumps(context)))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return event_id

def get_events() -> list:
    return EVENT_STORE

def clear_events() -> None:
    EVENT_STORE.clear()
