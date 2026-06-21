import time
import threading
import pyperclip
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

from . import db
from . import pii_filter
from .session_manager import SessionManager

try:
    import pygetwindow as gw
    WINDOWS_OS = True
except Exception:
    WINDOWS_OS = False

session_manager = SessionManager()

class FileEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            db.log_file_event("created", event.src_path)
            session_manager.handle_event('file_created', 'filesystem', {'path': event.src_path})

    def on_modified(self, event):
        if not event.is_directory:
            db.log_file_event("modified", event.src_path)
            session_manager.handle_event('file_modified', 'filesystem', {'path': event.src_path})

    def on_moved(self, event):
        if not event.is_directory:
            db.log_file_event("moved", event.dest_path)
            session_manager.handle_event('file_moved', 'filesystem', {'path': event.dest_path})

class SystemObserver:
    def __init__(self):
        self.running = False
        self.threads = []
        self.file_observer = None

    def start(self, private=False):
        if self.running:
            return
            
        self.running = True
        self.private = private
        
        if not self.private:
            clip_thread = threading.Thread(target=self._observe_clipboard, daemon=True)
            self.threads.append(clip_thread)
            clip_thread.start()
            
            win_thread = threading.Thread(target=self._observe_windows, daemon=True)
            self.threads.append(win_thread)
            win_thread.start()
            
            self._start_file_observer()

    def stop(self):
        self.running = False
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()

    def _observe_clipboard(self):
        last_clip = ""
        while self.running:
            try:
                current_clip = pyperclip.paste()
                if current_clip and current_clip != last_clip:
                    if len(current_clip) < 30 and pii_filter.is_sensitive(current_clip):
                        pass
                    else:
                        sanitized_clip = pii_filter.sanitize(current_clip)
                        if not (len(sanitized_clip) < 20 and " " not in sanitized_clip):
                            db.log_clipboard(sanitized_clip)
                            session_manager.handle_event('clipboard_copy', 'unknown_app', {'content': sanitized_clip})
                    last_clip = current_clip
            except Exception as e:
                import logging
                logging.error(f"context: {e}", exc_info=True)
            time.sleep(2)

    def _observe_windows(self):
        import json
        from PIL import ImageGrab
        import datetime
        
        os.makedirs("screenshots", exist_ok=True)
        
        last_title = ""
        while self.running:
            try:
                if WINDOWS_OS:
                    active_window = gw.getActiveWindow()
                    if active_window is not None:
                        title = active_window.title
                        app_name = title.split(" - ")[-1] if " - " in title else title
                        
                        if title.strip():
                            # Privacy layer check
                            config = {}
                            if os.path.exists("config.json"):
                                with open("config.json", "r") as f:
                                    config = json.load(f)
                            exclusions = config.get("excluded_categories", [])
                            skip = False
                            for exc in exclusions:
                                if "email" in exc.lower() and ("gmail" in title.lower() or "outlook" in title.lower()): skip = True
                                if "banking" in exc.lower() and any(b in title.lower() for b in ["bank", "chase", "wells", "citi", "amex", "finance"]): skip = True
                                if "entertainment" in exc.lower() and any(e in title.lower() for e in ["netflix", "youtube", "spotify", "steam", "prime"]): skip = True
                                if "health" in exc.lower() and any(h in title.lower() for h in ["health", "medical", "mychart"]): skip = True
                                if "messaging" in exc.lower() and any(m in title.lower() for m in ["whatsapp", "telegram", "messenger", "signal"]): skip = True
                            
                            if not skip:
                                # Log window change
                                if title != last_title:
                                    db.log_window(app_name, title)
                                    session_manager.handle_event('window_focus', app_name, {'title': title})
                                    last_title = title
                                
                                # Take screenshot every 1 second
                                timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                filepath = os.path.join("screenshots", f"screen_{timestamp_str}.jpg")
                                
                                img = ImageGrab.grab()
                                # Compress heavily for zero CPU / low I/O
                                img.thumbnail((1280, 720))
                                img.save(filepath, "JPEG", quality=50)
                                
                                db.log_screen(title, filepath)
                                
                                # Auto prune old screens
                                db.prune_old_screens(hours=1)
                else:
                    pass
            except Exception as e:
                import logging
                logging.error(f"context: {e}", exc_info=True)
            time.sleep(1)

    def _start_file_observer(self):
        path_to_watch = os.path.expanduser("~/Documents")
        if not os.path.exists(path_to_watch):
            path_to_watch = "."
            
        event_handler = FileEventHandler()
        self.file_observer = Observer()
        self.file_observer.schedule(event_handler, path_to_watch, recursive=True)
        self.file_observer.start()

observer_instance = SystemObserver()

def start_observing(private=False):
    observer_instance.start(private)

def stop_observing():
    observer_instance.stop()
    session_manager.end_current_session()
