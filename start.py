import os
import sys
import subprocess
import time
import socket
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def check_python_version():
    if sys.version_info < (3, 9):
        print("Error: Python 3.9 or higher is required.")
        sys.exit(1)

def setup_env():
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("ANTHROPIC_API_KEY=your_key_here\nENV=development\nDEV_API_KEY=sk-test-key-123\n")
        print("Created .env file. Add your Anthropic API key before continuing.")
        sys.exit(0)
    
    # Load .env manually to avoid extra dependencies if possible
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val
                
    if os.environ.get("ANTHROPIC_API_KEY") in [None, "", "your_key_here"]:
        print("Warning: ANTHROPIC_API_KEY is not set or is using placeholder. Some features may fail.")

def check_requirements():
    missing = False
    try:
        import fastapi
        import anthropic
        import pystray
    except ImportError:
        missing = True
        
    try:
        npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
        subprocess.run([npx_cmd, "electron", "--version"], capture_output=True, check=True)
    except Exception as e:
        import logging
        logging.error(f"context: {e}", exc_info=True) # Handle NPM failures softly, just run install
        
    if missing:
        print("Missing requirements. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def check_db_and_seed():
    from client.db import init_db, get_connection
    init_db()
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sessions")
    count = c.fetchone()[0]
    conn.close()
    
    if count == 0:
        ans = input("No data found. Load demo data for first run? (y/n) ").strip().lower()
        if ans == 'y':
            subprocess.run([sys.executable, "demo_seed.py"])

def ping_health():
    for _ in range(5):
        try:
            with socket.create_connection(("127.0.0.1", 8000), timeout=1):
                return True
        except OSError:
            time.sleep(1)
    return False

def main():
    check_python_version()
    setup_env()
    check_requirements()
    
    # Needs to be below check_requirements so imports inside check_db_and_seed work
    # check_db_and_seed()
    
    # Start Backend
    print("Starting FastAPI server...")
    server_proc = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "platform_core.server:app", "--port", "8000", "--log-level", "warning"
    ])
    
    if ping_health():
        print("Platform server running on port 8000")
    else:
        print("Warning: Server didn't ping successfully on port 8000")
        
    # Start Observer
    print("Starting Desktop Observer...")
    client_proc = subprocess.Popen([sys.executable, "-m", "client.main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    # Start Frontend
    print("Nous UI launching...")
    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
    ui_proc = subprocess.Popen([npx_cmd, "electron", "."], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("""
    ======================================
    |   Nous is running                  |
    |   Platform: http://localhost:8000  |  
    |   UI: Electron app                 |
    ======================================
    Press Ctrl+C to stop everything.
    """)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        server_proc.terminate()
        ui_proc.terminate()
        client_proc.terminate()
        server_proc.wait()
        ui_proc.wait()
        client_proc.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
