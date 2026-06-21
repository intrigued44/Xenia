import sys
import os
import uuid
import time
import threading
from collections import Counter

from platform_core import api as platform_api
from . import db

class SessionManager:
    def __init__(self):
        self.current_session_id = None
        self.last_event_time = 0
        self.app_counts = Counter()
        self.lock = threading.Lock()
        self.gap_threshold_seconds = 10 * 60

    def handle_event(self, event_type, app_name, metadata_dict):
        current_time = int(time.time())
        
        with self.lock:
            if not self.current_session_id or (current_time - self.last_event_time) > self.gap_threshold_seconds:
                self._start_new_session(current_time, app_name)
            
            self.last_event_time = current_time
            if app_name:
                self.app_counts[app_name] += 1
                
            db.log_event(self.current_session_id, event_type, app_name, metadata_dict)
            
            platform_api.receive_event(
                event_type=event_type,
                source_system=app_name if app_name else "unknown",
                context=metadata_dict if metadata_dict else {}
            )

    def _start_new_session(self, current_time, first_app):
        if self.current_session_id:
            self._close_current_session(self.last_event_time)
            
        self.current_session_id = str(uuid.uuid4())
        self.app_counts.clear()
        if first_app:
            self.app_counts[first_app] += 1
            
        db.create_session(self.current_session_id, current_time, first_app)

    def _close_current_session(self, ended_at):
        if self.current_session_id:
            db.close_session(self.current_session_id, ended_at)
            
            if self.app_counts:
                primary_app = self.app_counts.most_common(1)[0][0]
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE sessions SET primary_app = ? WHERE id = ?',
                               (primary_app, self.current_session_id))
                conn.commit()
                conn.close()
                
            self.current_session_id = None

    def end_current_session(self):
        with self.lock:
            self._close_current_session(self.last_event_time)
