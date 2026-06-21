import time
import os
import re
import requests
from typing import Dict, Any
from platform_core.tools.base import Tool, registry

class EmailTool(Tool):
    name = "email_tool.draft_reply"
    description = "Drafts an email reply using the Gmail connector"
    permission_tier = "auto"
    required_connector = "Gmail"

    def execute(self, params: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        start = time.time()
        # In real execution, this fetches the connector from registry and pushes the write
        return {
            "success": True,
            "output": f"Draft created for {params.get('thread_id')}",
            "error": None,
            "execution_time_ms": int((time.time() - start) * 1000)
        }

class WebSearchTool(Tool):
    name = "web_tool.search"
    description = "Searches the web using DuckDuckGo"
    permission_tier = "auto"
    required_connector = None

    def execute(self, params: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        start = time.time()
        try:
            from ddgs import DDGS
            query = params.get("query", "")
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            return {"success": True, "output": results, "error": None, "execution_time_ms": int((time.time() - start) * 1000)}
        except Exception as e:
            return {"success": False, "output": [], "error": str(e), "execution_time_ms": int((time.time() - start) * 1000)}

class WebFetchTool(Tool):
    name = "web_tool.fetch"
    description = "Fetches and cleans content from a URL"
    permission_tier = "auto"
    required_connector = None

    def execute(self, params: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        start = time.time()
        try:
            url = params.get("url")
            response = requests.get(url, timeout=10, headers={"User-Agent": "Nous/1.0"})
            clean_text = re.sub('<[^<]+?>', '', response.text)[:5000]
            return {"success": True, "output": clean_text, "error": None, "execution_time_ms": int((time.time() - start) * 1000)}
        except Exception as e:
            return {"success": False, "output": None, "error": str(e), "execution_time_ms": int((time.time() - start) * 1000)}

class DocumentCreateTool(Tool):
    name = "document_tool.create_markdown"
    description = "Creates a markdown document locally"
    permission_tier = "auto"
    required_connector = None

    def execute(self, params: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        start = time.time()
        try:
            title = params.get("title", "untitled")
            content = params.get("content", "")
            folder = params.get("folder", "documents")
            os.makedirs(folder, exist_ok=True)
            filename = title.lower().replace(" ", "_").replace("/", "_") + ".md"
            filepath = os.path.join(folder, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n{content}")
            return {"success": True, "output": {"path": filepath}, "execution_time_ms": int((time.time() - start) * 1000), "error": None}
        except Exception as e:
            return {"success": False, "output": None, "execution_time_ms": int((time.time() - start) * 1000), "error": str(e)}

class DocumentReadTool(Tool):
    name = "document_tool.read"
    description = "Reads content from a local text file"
    permission_tier = "auto"
    required_connector = None

    def execute(self, params: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        start = time.time()
        try:
            path = params.get("path", "")
            if not os.path.exists(path):
                return {"success": False, "output": None, "execution_time_ms": int((time.time() - start) * 1000), "error": "File not found"}
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "output": content[:10000], "execution_time_ms": int((time.time() - start) * 1000), "error": None}
        except Exception as e:
            return {"success": False, "output": None, "execution_time_ms": int((time.time() - start) * 1000), "error": str(e)}

class NotificationTool(Tool):
    name = "notification_tool.toast"
    description = "Triggers a desktop toast notification"
    permission_tier = "auto"
    required_connector = None

    def execute(self, params: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        start = time.time()
        title = params.get("title", "Nous")
        message = params.get("message", "")
        
        import threading
        def _toast_worker():
            try:
                from win10toast import ToastNotifier
                ToastNotifier().show_toast(title, message, duration=5, threaded=False)
            except Exception as e:
                print(f"[FLUXX NOTIFICATION ERROR] Failed to show toast: {e}. Fallback message: {title}: {message}")
                
        try:
            # Spawn our own daemon thread to prevent blocking but safely capture background exceptions
            threading.Thread(target=_toast_worker, daemon=True).start()
        except Exception as e:
            print(f"[FLUXX NOTIFICATION SYSTEM ERROR] {e}. Fallback message: {title}: {message}")
            
        return {"success": True, "output": "sent", "execution_time_ms": int((time.time() - start) * 1000), "error": None}

registry.register(EmailTool())
registry.register(WebSearchTool())
registry.register(WebFetchTool())
registry.register(DocumentCreateTool())
registry.register(DocumentReadTool())
registry.register(NotificationTool())
