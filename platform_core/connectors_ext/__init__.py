class ConnectorRegistry:
    def __init__(self):
        self._connectors = {}
        
    def register(self, name, connector):
        self._connectors[name] = connector
        
    def get(self, name, tenant_id=None):
        return self._connectors.get(name)

registry = ConnectorRegistry()

try:
    from .gmail import GmailConnector
    registry.register("gmail", GmailConnector())
except Exception as e:
    import logging
    logging.error(f"context: {e}", exc_info=True)
