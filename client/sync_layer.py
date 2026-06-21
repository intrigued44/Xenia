import json
import os
import hashlib

from . import db

EXPORT_PATH = "company_sync.json"

def hash_string(text):
    if not text:
        return ""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {}

def export_anonymized_data():
    config = load_config()
    if not config.get("company_sync_enabled", False):
        return None
        
    logs = db.get_recent_logs(days=7)
    anonymized_sequence = []
    combined_logs = []
    
    for w in logs['window_logs']:
        combined_logs.append({
            "timestamp": w[0],
            "type": "window_focus",
            "app": w[1],
            "context_hash": hash_string(w[2])
        })
        
    for f in logs['file_logs']:
        ext = os.path.splitext(f[2])[1] if f[2] else "unknown"
        combined_logs.append({
            "timestamp": f[0],
            "type": f"file_{f[1]}",
            "app": "filesystem",
            "context_hash": f"ext:{ext}"
        })
        
    combined_logs.sort(key=lambda x: x["timestamp"])
    
    export_data = {
        "user_id": "anon_user_1",
        "sequence": combined_logs
    }
    
    with open(EXPORT_PATH, 'w') as f:
        json.dump(export_data, f, indent=2)
        
    # HTTP Sync Upload if backend_url and api_key are set
    backend_url = config.get("backend_url")
    api_key = config.get("api_key")
    if backend_url and api_key:
        import requests
        try:
            url = f"{backend_url}/v1/sync"
            headers = {"x-api-key": api_key}
            
            sync_sequence = []
            for item in combined_logs:
                mapped_item = {
                    "timestamp": item["timestamp"],
                    "type": item["type"],
                    "app": item["app"]
                }
                if item["type"] == "window_focus":
                    mapped_item["content"] = item["context_hash"]
                else:
                    mapped_item["file_path"] = item["context_hash"]
                sync_sequence.append(mapped_item)
                
            payload = {
                "user_id": export_data["user_id"],
                "sequence": sync_sequence
            }
            
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                print(f"[Sync Layer] Successfully uploaded {len(sync_sequence)} events to server.")
            else:
                print(f"[Sync Layer] Failed to upload sync data: HTTP {resp.status_code}")
        except Exception as e:
            print(f"[Sync Layer] Error uploading sync data: {e}")
            
    return EXPORT_PATH

if __name__ == "__main__":
    path = export_anonymized_data()
    print(f"Exported to {path}")
