import os
import pytest
import sqlite3
import json

os.environ["ANTHROPIC_API_KEY"] = "test_key"

from . import db
from . import sync_layer
from . import analyser

@pytest.fixture(autouse=True)
def setup_teardown():
    db.DB_PATH = 'test_data.db'
    db.init_db()
    db.clear_logs()
    
    yield
    
    if os.path.exists('test_data.db'):
        os.remove('test_data.db')
    if os.path.exists('company_sync.json'):
        os.remove('company_sync.json')

def test_db_operations():
    db.log_window("TestApp", "Test Window Title")
    db.log_clipboard("Test clipboard data")
    db.log_file_event("created", "/path/to/test.txt")
    
    logs = db.get_recent_logs()
    assert len(logs['window_logs']) == 1
    assert logs['window_logs'][0][1] == "TestApp"
    assert logs['window_logs'][0][2] == "Test Window Title"
    
    assert len(logs['clipboard_logs']) == 1
    assert logs['clipboard_logs'][0][1] == "Test clipboard data"
    
    assert len(logs['file_logs']) == 1
    assert logs['file_logs'][0][1] == "created"
    assert logs['file_logs'][0][2] == "/path/to/test.txt"

from unittest.mock import patch
@patch("client.sync_layer.load_config")
def test_sync_layer(mock_load_config):
    mock_load_config.return_value = {"company_sync_enabled": True}
    db.log_window("TestApp", "Test Window Title")
    db.log_file_event("created", "/path/to/test.txt")
    
    sync_layer.EXPORT_PATH = "company_sync.json"
    path = sync_layer.export_anonymized_data()
    
    assert os.path.exists(path)
    
    with open(path, 'r') as f:
        data = json.load(f)
        
    assert "user_id" in data
    assert "sequence" in data
    assert len(data["sequence"]) == 2
    
    seq1 = data["sequence"][0]
    assert seq1["app"] in ["TestApp", "filesystem"]
    assert "Test Window Title" not in str(seq1)

def test_analyzer_handles_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = analyser.generate_weekly_digest()
    assert "error" in result

import time
from .session_manager import SessionManager

def test_session_manager_creates_session():
    manager = SessionManager()
    manager.handle_event('window_focus', 'TestApp', {'title': 'Doc'})
    
    assert manager.current_session_id is not None
    sessions = db.get_sessions()
    assert len(sessions) == 1
    assert sessions[0]['primary_app'] == 'TestApp'
    
    events = db.get_events_for_session(sessions[0]['id'])
    assert len(events) == 1
    assert events[0]['event_type'] == 'window_focus'
    
def test_session_manager_closes_on_gap(monkeypatch):
    manager = SessionManager()
    
    current_time = int(time.time())
    def mock_time():
        return current_time
    monkeypatch.setattr(time, 'time', mock_time)
    
    manager.handle_event('window_focus', 'App1', {})
    first_session_id = manager.current_session_id
    
    current_time += 11 * 60
    manager.handle_event('window_focus', 'App2', {})
    second_session_id = manager.current_session_id
    
    assert first_session_id != second_session_id
    sessions = db.get_sessions()
    assert len(sessions) == 2
    
    first_session = next(s for s in sessions if s['id'] == first_session_id)
    assert first_session['ended_at'] is not None

from . import pii_filter

def test_pii_filter_redacts_email():
    text = "Contact me at test.user@example.com for info."
    sanitized = pii_filter.sanitize(text)
    assert "[REDACTED_EMAIL]" in sanitized
    assert "test.user@example.com" not in sanitized

def test_pii_filter_redacts_card():
    text = "My card is 1234-5678-9012-3456."
    sanitized = pii_filter.sanitize(text)
    assert "[REDACTED_CARD]" in sanitized
    assert "1234-5678-9012-3456" not in sanitized

def test_pii_filter_blocks_sensitive_clipboard():
    assert pii_filter.is_sensitive("sk-12345abcdef") == True
    assert pii_filter.is_sensitive("Just normal text") == False

from . import preprocessor
def test_preprocessor_builds_context():
    t = int(time.time())
    db.create_session("sess1", t - 3600, "AppA")
    db.log_event("sess1", "window", "AppA", {})
    db.log_event("sess1", "window", "AppB", {})
    db.close_session("sess1", t - 3000)
    
    db.create_session("sess2", t - 2000, "AppA")
    db.log_event("sess2", "window", "AppA", {})
    db.log_event("sess2", "window", "AppB", {})
    db.close_session("sess2", t - 1000)
    
    db.create_session("sess3", t - 500, "AppC")
    db.log_event("sess3", "window", "AppC", {})
    db.log_event("sess3", "window", "AppD", {})
    db.close_session("sess3", t - 100)
    
    ctx = preprocessor.build_analysis_context()
    assert ctx["total_sessions"] == 3
    assert len(ctx["detected_patterns"]) >= 2
    
    pattern = next((p for p in ctx["detected_patterns"] if p["app_sequence"] == ["AppA", "AppB"]), None)
    assert pattern is not None
    assert pattern["session_count"] == 2

def test_analyzer_uses_preprocessor(monkeypatch):
    mock_ctx = {
        "total_sessions": 5,
        "total_work_hours": 2.5,
        "app_usage_minutes": {"AppX": 60},
        "most_used_apps": ["AppX"],
        "detected_patterns": [{"app_sequence": ["AppX", "AppY"], "session_count": 5, "avg_duration_minutes": 10}],
        "longest_sessions": []
    }
    monkeypatch.setattr(preprocessor, 'build_analysis_context', lambda days: mock_ctx)
    
    class MockMessages:
        def create(self, **kwargs):
            self.prompt_sent = kwargs['messages'][0]['content']
            class MockResponse:
                content = [type('obj', (object,), {'text': '{"workflows": [], "summary": "mocked_response"}'})]
            return MockResponse()
            
    class MockClient:
        def __init__(self, **kwargs):
            self.messages = MockMessages()
            
    from . import analyser
    monkeypatch.setattr(analyser, 'Anthropic', MockClient)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    
    result = analyser.generate_weekly_digest()
    assert result["summary"] == "mocked_response"
