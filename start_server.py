import os
import sys
import time
import threading
import logging

# ── Path setup ─────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    sys.path.insert(0, BASE_DIR)
    internal = os.path.join(BASE_DIR, '_internal')
    if os.path.exists(internal):
        sys.path.insert(0, internal)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)
logging.basicConfig(level=logging.ERROR)

print(f"[Xenia] Starting from {BASE_DIR}", flush=True)

# ── Database init ────────────────────────────────────────────────────────────
try:
    from client.db import init_db
    init_db()
    print("[Xenia] Database initialized", flush=True)
except Exception as e:
    print(f"[Xenia] DB init warning: {e}", flush=True)

# ── Screen Observer ──────────────────────────────────────────────────────────
def start_observer():
    """Start the screen/window/clipboard observer in the background."""
    try:
        from client.observer import start_observing
        print("[Xenia] Starting screen observer...", flush=True)
        start_observing(private=False)
        print("[Xenia] Screen observer running", flush=True)
    except Exception as e:
        print(f"[Xenia] Observer could not start: {e}", flush=True)

# Start observer in background thread after 3s (give server time to start)
threading.Timer(3.0, start_observer).start()

# ── Proactive Engine ─────────────────────────────────────────────────────────
def start_proactive_engine():
    """Run the proactive intelligence engine periodically."""
    import time as _time
    _time.sleep(30)  # Wait 30s after startup before first run
    while True:
        try:
            from platform_core.intelligence.proactive import ProactiveEngine
            ProactiveEngine().run('tenant-local')
        except Exception as e:
            print(f"[Xenia] Proactive engine error: {e}", flush=True)
        _time.sleep(300)  # Run every 5 minutes

threading.Thread(target=start_proactive_engine, daemon=True).start()

# ── Scheduler (workflow analysis, etc.) ─────────────────────────────────────
def run_analysis():
    """Run weekly digest and workflow analysis."""
    import time as _time
    _time.sleep(60)  # Wait 60s after startup
    while True:
        try:
            from client.analyser import generate_weekly_digest
            generate_weekly_digest()
            print("[Xenia] Analysis complete", flush=True)
        except Exception as e:
            print(f"[Xenia] Analysis error: {e}", flush=True)
        _time.sleep(3600)  # Run every hour

threading.Thread(target=run_analysis, daemon=True).start()

# ── Ready signal ─────────────────────────────────────────────────────────────
READY_FILE = os.path.join(BASE_DIR, '.nous_ready')
if os.path.exists(READY_FILE):
    try:
        os.remove(READY_FILE)
    except Exception:
        pass

def write_ready():
    time.sleep(1.5)
    try:
        with open(READY_FILE, 'w') as f:
            f.write('ready')
        print("[Xenia] Server ready", flush=True)
    except Exception as e:
        print(f"[Xenia] Ready file error: {e}", flush=True)

# ── Start FastAPI server ──────────────────────────────────────────────────────
import uvicorn
from platform_core.server import app as fastapi_app

if __name__ == '__main__':
    threading.Timer(1.5, write_ready).start()
    uvicorn.run(
        fastapi_app,
        host='127.0.0.1',
        port=8000,
        log_level='error',
        access_log=False
    )
