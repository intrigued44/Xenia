from typing import Dict, Any, Literal
from abc import ABC, abstractmethod

class Tool(ABC):
    name: str
    description: str
    permission_tier: Literal["auto", "confirm", "review"]
    required_connector: str | None = None

    @abstractmethod
    def execute(self, params: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """
        Execute the tool and return a ToolResult dict:
        {"success": bool, "output": any, "error": str | None, "execution_time_ms": int}
        """
        pass

class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Tool]:
        return self._tools
        
registry = ToolRegistry()
