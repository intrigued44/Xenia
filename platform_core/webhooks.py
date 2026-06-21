from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.post("/v1/webhooks/receive")
async def receive_webhook(request: Request, format: str = "generic"):
    """
    Ingest webhooks from external systems and normalize them.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    from .api import receive_event
    
    if format == "github":
        event_type = f"github_{payload.get('action', 'event')}"
        source = "github"
    elif format == "slack":
        event_type = f"slack_{payload.get('type', 'event')}"
        source = "slack"
    elif format == "stripe":
        event_type = f"stripe_{payload.get('type', 'event')}"
        source = "stripe"
    else:
        event_type = payload.get("event_type", "webhook_event")
        source = payload.get("source", "generic_webhook")
        
    event_id = receive_event(
        event_type=event_type,
        source_system=source,
        context=payload,
        user_id="webhook_user",
        tenant_id="local"
    )
    
    return {"event_id": event_id, "status": "accepted"}
