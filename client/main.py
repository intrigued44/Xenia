import os
import threading
import time
import schedule
import json
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item

from . import observer
from . import db
from . import analyser as analyzer
from . import sync_layer
from . import query_ui

def create_image(color):
    image = Image.new('RGB', (64, 64), color='white')
    dc = ImageDraw.Draw(image)
    dc.ellipse((16, 16, 48, 48), fill=color)
    return image

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

class DesktopAIApp:
    def __init__(self, silent=False):
        self.silent = silent
        self.is_paused = False
        self.is_private = False
        self.icon = None
        db.init_db()
        if not self.silent:
            self.check_consent()

    def check_consent(self):
        config = load_config()
        if not config.get("consent_given"):
            self.show_consent_dialog()
            config = load_config()
            if not config.get("consent_given"):
                import sys
                sys.exit(0)
            self.show_exclusion_dialog()

    def show_consent_dialog(self):
        root = tk.Tk()
        root.title("Welcome to Nous")
        root.geometry("400x300")
        root.attributes("-topmost", True)
        
        msg = (
            "Nous watches which apps you use and for how long\n"
            "It never reads the content of your documents or messages\n"
            "Everything stays on this device unless you choose to share it\n"
            "You can pause or delete everything at any time"
        )
        
        tk.Label(root, text=msg, justify=tk.LEFT, wraplength=350, pady=20).pack()
        
        def on_accept():
            config = load_config()
            config["consent_given"] = True
            config["consent_date"] = datetime.now().isoformat()
            save_config(config)
            root.destroy()
            
        def on_exit():
            root.destroy()
            
        tk.Button(root, text="I understand, get started", command=on_accept, bg="green", fg="white", pady=10).pack(fill=tk.X, padx=50, pady=5)
        tk.Button(root, text="Exit", command=on_exit, pady=10).pack(fill=tk.X, padx=50, pady=5)
        
        root.mainloop()

    def show_exclusion_dialog(self):
        root = tk.Tk()
        root.title("Privacy Exclusions")
        root.geometry("300x350")
        root.attributes("-topmost", True)
        
        tk.Label(root, text="Select categories to never track:", pady=10).pack()
        
        categories = {
            "Personal email (Gmail, Outlook personal)": tk.BooleanVar(value=True),
            "Banking and finance apps": tk.BooleanVar(value=True),
            "Entertainment (Netflix, YouTube, Spotify, Steam)": tk.BooleanVar(value=True),
            "Health apps": tk.BooleanVar(value=True),
            "Personal messaging (WhatsApp, Telegram personal)": tk.BooleanVar(value=True)
        }
        
        for text, var in categories.items():
            tk.Checkbutton(root, text=text, variable=var, wraplength=250, justify=tk.LEFT).pack(anchor=tk.W, padx=20)
            
        def on_save():
            config = load_config()
            config["excluded_categories"] = [name for name, var in categories.items() if var.get()]
            save_config(config)
            root.destroy()
            
        tk.Button(root, text="Save Exclusions", command=on_save, pady=10).pack(pady=20)
        root.mainloop()

    def set_icon_color(self, color):
        if self.icon:
            self.icon.icon = create_image(color)

    def toggle_pause(self, icon, item):
        self.is_paused = not self.is_paused
        if self.is_paused:
            observer.stop_observing()
            self.set_icon_color('gray')
        elif self.is_private:
            observer.start_observing(private=True)
            self.set_icon_color('purple')
        else:
            observer.start_observing(private=False)
            self.set_icon_color('green')
            
    def toggle_private_session(self, icon, item):
        self.is_private = not self.is_private
        if self.is_private:
            observer.stop_observing()
            observer.start_observing(private=True)
            self.set_icon_color('purple')
        else:
            observer.stop_observing()
            observer.start_observing(private=False)
            self.set_icon_color('green')
            
    def toggle_company_sync(self, icon, item):
        config = load_config()
        if not config.get("company_sync_enabled"):
            root = tk.Tk()
            root.title("Company Sync")
            root.geometry("300x200")
            root.attributes("-topmost", True)
            msg = (
                "This will share anonymized workflow patterns — no personal "
                "data — with your organization's shared knowledge base. "
                "You can turn this off at any time."
            )
            tk.Label(root, text=msg, wraplength=250, pady=20).pack()
            def on_enable():
                config["company_sync_enabled"] = True
                save_config(config)
                root.destroy()
                self.update_menu()
            def on_cancel():
                root.destroy()
            tk.Button(root, text="Enable", command=on_enable, bg="blue", fg="white").pack(side=tk.LEFT, padx=30)
            tk.Button(root, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=30)
            root.mainloop()
        else:
            config["company_sync_enabled"] = False
            save_config(config)
            self.update_menu()

    def open_query_ui(self, icon, item):
        threading.Thread(target=query_ui.launch_ui, daemon=True).start()

    def generate_digest(self, icon=None, item=None):
        self.set_icon_color('yellow')
        try:
            digest = analyzer.generate_weekly_digest()
            with open("weekly_digest.md", "w") as f:
                f.write(digest)
            print("Weekly digest generated and saved to weekly_digest.md")
        except Exception as e:
            print(f"Error generating digest: {e}")
        
        sync_layer.export_anonymized_data()
        
        if not self.is_paused:
            self.set_icon_color('green')

    def update_menu(self):
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM pending_approvals WHERE status = 'pending'")
            approvals_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 0")
            alerts_count = cursor.fetchone()[0]
            conn.close()
        except:
            approvals_count = 0
            alerts_count = 0

        config = load_config()
        sync_enabled = config.get("company_sync_enabled", False)
        
        menu_items = [
            item('Private', lambda: None, enabled=False) if self.is_private else None,
            item(f'Approvals Pending: {approvals_count}', lambda: None, enabled=False) if approvals_count > 0 else item('No Pending Approvals', lambda: None, enabled=False),
            item(f'Unresolved Alerts: {alerts_count}', lambda: None, enabled=False) if alerts_count > 0 else item('No New Alerts', lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            item(lambda text: 'End Private Session' if self.is_private else 'Start Private Session', self.toggle_private_session),
            item(lambda text: 'Resume' if self.is_paused else 'Pause', self.toggle_pause),
            item(lambda text: 'Disable Company Sync' if sync_enabled else 'Share anonymized patterns with company brain', self.toggle_company_sync),
            item('Ask AI', self.open_query_ui),
            item('Generate Digest Now', self.generate_digest),
            item('Run Proactive Engine', self.run_proactive_engine),
            item('Quit', self.quit_app)
        ]
        
        self.icon.menu = pystray.Menu(*[m for m in menu_items if m is not None])
        self.icon.update_menu()

    def run_proactive_engine(self):
        self.set_icon_color('yellow')
        from platform_core.intelligence.proactive import ProactiveEngine
        try:
            ProactiveEngine().run("local")
        except Exception as e:
            print(f"Error running proactive engine: {e}")
        self.update_menu()
        if not self.is_paused:
            self.set_icon_color('green')

    def poll_and_execute_automations(self):
        config = load_config()
        backend_url = config.get("backend_url")
        api_key = config.get("api_key")
        if not backend_url or not api_key:
            return
            
        import requests
        try:
            url = f"{backend_url}/v1/automations/pending"
            headers = {"x-api-key": api_key}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return
                
            pending = resp.json().get("pending_automations", [])
            for aut in pending:
                name = aut["name"]
                code = aut["code_content"]
                print(f"[Client Automation] Found pending automation '{name}'. Running locally...")
                
                import sys
                import io
                import traceback
                
                stdout = io.StringIO()
                stderr = io.StringIO()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = stdout
                sys.stderr = stderr
                
                success = True
                error_msg = None
                try:
                    local_env = {"os": os, "time": time, "sys": sys, "__name__": "__main__"}
                    exec(code, local_env, local_env)
                except Exception as e:
                    success = False
                    tb = traceback.format_exc()
                    error_msg = f"{str(e)}\nTraceback:\n{tb}"
                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr
                    
                output_str = stdout.getvalue()
                err_str = stderr.getvalue()
                if err_str:
                    output_str += f"\nStderr:\n{err_str}"
                    
                result_url = f"{backend_url}/v1/automations/{name}/result"
                result_payload = {
                    "success": success,
                    "output": output_str,
                    "error": error_msg
                }
                requests.post(result_url, json=result_payload, headers=headers, timeout=10)
                print(f"[Client Automation] Executed '{name}'. Success: {success}")
        except Exception as e:
            print(f"[Client Automation] Error polling/executing automations: {e}")

    def run_scheduler(self):
        schedule.every().sunday.at("00:00").do(self.generate_digest)
        schedule.every(6).hours.do(self.run_proactive_engine)
        
        while True:
            schedule.run_pending()
            
            try:
                self.poll_and_execute_automations()
            except Exception as pe:
                import logging
                logging.error(f"Error in automation poller: {pe}")
                
            # Try updating menu every 60 seconds
            try:
                if self.icon:
                    self.update_menu()
            except Exception as e:
                import logging
                logging.error(f"context: {e}", exc_info=True)
            time.sleep(60)

    def run(self):
        observer.start_observing()
        
        if self.silent:
            print("[Client App] Running in headless/silent mode. Starting scheduler...")
            self.run_scheduler()
            return
            
        threading.Thread(target=self.run_scheduler, daemon=True).start()

        menu = pystray.Menu(
            item('Loading...', lambda: None, enabled=False)
        )
        
        self.icon = pystray.Icon("DesktopAI", create_image('green'), "Desktop AI Observer", menu)
        self.icon.visible = True
        
        # Give icon a moment to start before updating menu
        threading.Thread(target=lambda: (time.sleep(1), self.update_menu()), daemon=True).start()
        
        self.icon.run()

    def quit_app(self, icon, item):
        observer.stop_observing()
        self.icon.stop()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Nous Desktop AI App")
    parser.add_argument("--silent", action="store_true", help="Run headlessly, bypassing Tkinter dialogues")
    args = parser.parse_args()
    
    if args.silent:
        config = load_config()
        config["consent_given"] = True
        config["consent_date"] = datetime.now().isoformat()
        if "excluded_categories" not in config:
            config["excluded_categories"] = [
                "Personal email (Gmail, Outlook personal)",
                "Banking and finance apps",
                "Personal messaging (WhatsApp, Telegram personal)"
            ]
        save_config(config)
        
    app = DesktopAIApp(silent=args.silent)
    app.run()
