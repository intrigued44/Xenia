import os
import json
from platform_core.connectors import Connector

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "gmail_credentials.json"
TOKEN_FILE = "gmail_token.json"

class GmailConnector(Connector):
    name = "gmail"
    auth_method = "oauth2"
    capabilities = ["READ", "STREAM"]

    def is_authenticated(self) -> bool:
        return os.path.exists(TOKEN_FILE)

    def authenticate(self, credentials: dict) -> str:
        # credentials = path to downloaded credentials.json
        # OR dict with client_id and client_secret
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        if isinstance(credentials, str):
            # Path to credentials file
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials, SCOPES
            )
        else:
            flow = InstalledAppFlow.from_client_config(
                {"installed": credentials}, SCOPES
            )
        
        creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        
        return "authenticated"

    def _get_service(self):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        
        if not os.path.exists(TOKEN_FILE):
            raise ValueError("Gmail not authenticated. "
                           "Call authenticate() first.")
        
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE, SCOPES
        )
        
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        
        return build("gmail", "v1", credentials=creds,
                    cache_discovery=False)

    def read(self, query: dict) -> dict:
        method = query.get("method", "read_inbox")
        if method == "read_inbox":
            return {"emails": self.read_inbox(
                days=query.get("days", 7),
                limit=query.get("limit", 20)
            )}
        elif method == "get_unanswered":
            return {"emails": self.get_unanswered(
                days=query.get("days", 3)
            )}
        return {"emails": []}

    def read_inbox(self, days=7, limit=20) -> list:
        from googleapiclient.errors import HttpError
        import base64
        from datetime import datetime, timedelta
        
        service = self._get_service()
        
        after_date = (datetime.now() - 
                     timedelta(days=days)).strftime("%Y/%m/%d")
        
        try:
            results = service.users().messages().list(
                userId="me",
                q=f"after:{after_date}",
                maxResults=limit
            ).execute()
        except HttpError as e:
            return []
        
        messages = results.get("messages", [])
        emails = []
        
        for msg in messages[:limit]:
            try:
                full = service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From","Subject","Date"]
                ).execute()
                
                headers = {
                    h["name"]: h["value"] 
                    for h in full["payload"]["headers"]
                }
                
                # Sanitize through PII filter
                from client.pii_filter import sanitize
                subject = sanitize(
                    headers.get("Subject", "(no subject)")
                )
                
                emails.append({
                    "id": msg["id"],
                    "thread_id": full["threadId"],
                    "subject": subject,
                    "sender": headers.get("From",""),
                    "date": headers.get("Date",""),
                    "snippet": sanitize(
                        full.get("snippet","")[:200]
                    )
                })
            except Exception:
                continue
        
        return emails

    def get_unanswered(self, days=3) -> list:
        from googleapiclient.errors import HttpError
        from datetime import datetime, timedelta
        
        service = self._get_service()
        after_date = (datetime.now() - 
                     timedelta(days=days)).strftime("%Y/%m/%d")
        
        try:
            # Get emails sent by the user
            sent = service.users().messages().list(
                userId="me",
                q=f"in:sent after:{after_date}",
                maxResults=20
            ).execute()
        except HttpError:
            return []
        
        sent_messages = sent.get("messages", [])
        unanswered = []
        
        for msg in sent_messages[:20]:
            try:
                full = service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["To","Subject","Date"]
                ).execute()
                
                thread_id = full["threadId"]
                
                # Check if thread has reply
                thread = service.users().threads().get(
                    userId="me",
                    id=thread_id
                ).execute()
                
                thread_messages = thread.get("messages", [])
                
                # If only one message in thread = no reply
                if len(thread_messages) == 1:
                    headers = {
                        h["name"]: h["value"]
                        for h in full["payload"]["headers"]
                    }
                    
                    from client.pii_filter import sanitize
                    sent_date = headers.get("Date","")
                    
                    unanswered.append({
                        "thread_id": thread_id,
                        "subject": sanitize(
                            headers.get("Subject","")
                        ),
                        "sent_to": headers.get("To",""),
                        "sent_date": sent_date,
                        "days_since_sent": days
                    })
            except Exception:
                continue
        
        return unanswered

    def stream(self, callback) -> str:
        # Polling-based stream
        import threading
        
        def poll():
            import time
            last_check = int(time.time())
            while True:
                try:
                    emails = self.read_inbox(days=1, limit=5)
                    for email in emails:
                        callback(email)
                except Exception as e:
                    import logging
                    logging.error(f"context: {e}", exc_info=True)
                time.sleep(300)  # every 5 min
        
        t = threading.Thread(target=poll, daemon=True)
        t.start()
        return "streaming"

    def write(self, action: dict) -> dict:
        # Read-only for now
        return {"status": "read_only_connector"}
