import json

class ConnectorSDK:
    class Connector:
        name: str
        auth_method: str
        capabilities: list
        
        def authenticate(self, credentials: dict) -> str:
            raise NotImplementedError
            
        def read(self, query: dict) -> dict:
            raise NotImplementedError
            
        def write(self, action: dict) -> dict:
            raise NotImplementedError
            
        def stream(self, callback) -> None:
            raise NotImplementedError
            
        def emit_event(self, event_type: str, source: str, context: dict, tenant_id: str):
            """Helper to normalize and push directly to platform integration plane"""
            from platform_core.api import receive_event
            receive_event(
                event_type=event_type,
                source_system=source,
                context=context,
                tenant_id=tenant_id
            )
            return True
