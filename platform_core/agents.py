from typing import Any, Dict
from abc import ABC, abstractmethod

class Agent(ABC):
    name: str

    @abstractmethod
    def perceive(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def plan(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute(self, plan: Dict[str, Any], tools: Any) -> Dict[str, Any]:
        pass

    @abstractmethod
    def learn(self, result: Dict[str, Any], feedback: Dict[str, Any]) -> None:
        pass

class MockAgent(Agent):
    name = "MockAgent"
    
    def perceive(self, context):
        return {"observed": True}
        
    def plan(self, observation):
        return {"action": "do_nothing"}
        
    def execute(self, plan, tools):
        return {"success": True}
        
    def learn(self, result, feedback):
        pass
