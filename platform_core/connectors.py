from typing import Any, List, Dict
from abc import ABC, abstractmethod

class Connector(ABC):
    name: str
    auth_method: str
    capabilities: List[str]

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def read(self, query: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def write(self, action: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def stream(self, callback: Any) -> Any:
        pass

class MockConnector(Connector):
    name = "MockSystem"
    auth_method = "APIKey"
    capabilities = ["READ", "WRITE"]
    
    def authenticate(self, credentials):
        return "mock_token"
        
    def read(self, query):
        return {"data": "mock_read"}
        
    def write(self, action):
        return {"status": "success"}
        
    def stream(self, callback):
        return "mock_handle"
