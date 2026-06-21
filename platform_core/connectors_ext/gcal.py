from platform_core.connectors import Connector
from typing import Dict, Any

class GCalConnector(Connector):
    name = "GoogleCalendar"
    auth_method = "OAuth2"
    capabilities = ["READ", "WRITE", "STREAM"]
    
    def authenticate(self, credentials: Dict[str, Any]) -> str:
        return "gcal_oauth_token"
        
    def read(self, query: Dict[str, Any]) -> Dict[str, Any]:
        action = query.get("action")
        if action == "get_today":
            return {"events": [{"title": "Sync", "attendees": ["team@test.com"]}]}
        return {"events": []}
        
    def write(self, action: Dict[str, Any]) -> Dict[str, Any]:
        if action.get("action") == "create_event":
            return {"status": "success", "event_id": "123"}
        return {"status": "failed"}
        
    def stream(self, callback: Any) -> Any:
        pass
