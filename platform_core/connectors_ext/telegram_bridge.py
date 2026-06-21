import os
import time
import threading
import requests

class TelegramBridge:
    def __init__(self, bot_token: str, backend_url: str = "http://localhost:8000", api_key: str = "sk-test-key-123"):
        self.bot_token = bot_token
        self.backend_url = backend_url
        self.api_key = api_key
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.running = False
        self.thread = None

    def start(self):
        if not self.bot_token:
            print("[Telegram Bridge] No Bot Token provided. Not starting.")
            return False
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
        print("[Telegram Bridge] Polling bot listener started successfully.")
        return True

    def stop(self):
        self.running = False
        print("[Telegram Bridge] Bot listener stopped.")

    def _poll_loop(self):
        offset = 0
        while self.running:
            try:
                # Poll updates from Telegram
                url = f"{self.base_url}/getUpdates"
                params = {"offset": offset, "timeout": 10}
                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    time.sleep(5)
                    continue
                
                updates = resp.json().get("result", [])
                for update in updates:
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if not message:
                        continue
                    
                    chat_id = message["chat"]["id"]
                    text = message.get("text")
                    if not text:
                        continue
                        
                    print(f"[Telegram Bridge] Received message from chat {chat_id}: {text}")
                    
                    # Forward request to /v1/query
                    query_url = f"{self.backend_url}/v1/query"
                    headers = {"x-api-key": self.api_key}
                    query_params = {
                        "q": text,
                        "session_id": f"telegram_{chat_id}"
                    }
                    
                    try:
                        q_resp = requests.get(query_url, params=query_params, headers=headers, timeout=30)
                        if q_resp.status_code == 200:
                            answer = q_resp.json().get("answer", "No answer returned.")
                        else:
                            answer = f"Error from backend (HTTP {q_resp.status_code}): {q_resp.text}"
                    except Exception as e:
                        answer = f"Failed to contact Xenia backend: {str(e)}"
                        
                    # Send response back to Telegram chat
                    send_url = f"{self.base_url}/sendMessage"
                    send_payload = {
                        "chat_id": chat_id,
                        "text": answer
                    }
                    requests.post(send_url, json=send_payload, timeout=10)
                    
            except Exception as e:
                print(f"[Telegram Bridge] Exception in poll loop: {e}")
                time.sleep(5)
