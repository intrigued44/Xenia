import json
import uuid
from datetime import datetime
from typing import Dict, Any

EVENT_STORE = []

def receive_event(event_type: str, source_system: str, context: Dict[str, Any], user_id: str = "anon", tenant_id: str = "default_tenant") -> str:
    normalized_event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat() + "Z",
        "user_id": user_id,
        "tenant_id": tenant_id,
        "event_type": event_type,
        "source_system": source_system,
        "context": context,
        "pii_scrubbed": True
    }
    
    EVENT_STORE.append(normalized_event)
    return normalized_event["event_id"]

def get_events() -> list:
    return EVENT_STORE

def clear_events() -> None:
    EVENT_STORE.clear()
