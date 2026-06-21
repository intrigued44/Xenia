import subprocess
import os
import signal

def kill_process(name_pattern):
    try:
        # Find PIDs
        result = subprocess.run(["pgrep", "-f", name_pattern], capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        
        for pid in pids:
            if pid:
                print(f"Killing process {pid} matching '{name_pattern}'")
                os.kill(int(pid), signal.SIGTERM)
    except Exception as e:
        import logging
        logging.error(f"context: {e}", exc_info=True)

def main():
    print("Stopping Nous processes...")
    kill_process("uvicorn platform_core.server:app")
    kill_process("electron .")
    print("Done.")

if __name__ == "__main__":
    main()
