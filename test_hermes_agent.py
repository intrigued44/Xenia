import os
import pytest
import sqlite3
import time
from client.db import init_db, get_connection
from platform_core.intelligence.skills_engine import (
    save_skill,
    get_skill,
    log_skill_run,
    run_and_heal_skill
)
from platform_core.intelligence.memory_engine import (
    save_memory,
    get_memory,
    get_all_memories,
    save_message,
    search_conversations,
    nudge_memory
)
from platform_core.connectors_ext.telegram_bridge import TelegramBridge

def test_hermes_skills():
    """Verify that skills can be saved, read, logged, and executed/healed."""
    init_db()
    
    skill_name = "test_math_skill"
    description = "Divides 10 by 2"
    code_content = "result = 10 / 2\nprint(f'Math result: {result}')"
    
    # Clean up previous runs
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agent_skills WHERE name = ? AND tenant_id = ?", (skill_name, "test_tenant"))
    conn.commit()
    conn.close()
    
    # 1. Save skill
    skill_id = save_skill(skill_name, description, code_content, tenant_id="test_tenant")
    assert skill_id is not None
    
    # 2. Get skill
    skill = get_skill(skill_name, tenant_id="test_tenant")
    assert skill is not None
    assert skill["name"] == skill_name
    assert skill["code_content"] == code_content
    
    # 3. Log runs
    log_skill_run(skill_name, success=True, tenant_id="test_tenant")
    skill = get_skill(skill_name, tenant_id="test_tenant")
    assert skill["success_count"] == 1
    assert skill["failure_count"] == 0
    
    log_skill_run(skill_name, success=False, error_message="ZeroDivisionError: division by zero", tenant_id="test_tenant")
    skill = get_skill(skill_name, tenant_id="test_tenant")
    assert skill["success_count"] == 1
    assert skill["failure_count"] == 1
    
    # 4. Run and heal skill (successful script)
    run_res = run_and_heal_skill(skill_name, code_content, tenant_id="test_tenant")
    assert run_res["success"] is True
    assert "Math result: 5.0" in run_res["output"]
    
    # 5. Run and heal skill (failing script)
    failing_code = "result = 10 / 0"
    # Even if API key is not present, it should log the failure and return gracefully
    run_res = run_and_heal_skill(skill_name, failing_code, tenant_id="test_tenant")
    assert run_res["success"] is False
    assert "ZeroDivisionError" in run_res["error"]

def test_hermes_memory():
    """Verify that memory persistence, conversation logging, search, and nudging work."""
    init_db()
    
    tenant_id = "test_tenant"
    
    # Clean up previous runs
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agent_memories WHERE tenant_id = ?", (tenant_id,))
    cursor.execute("DELETE FROM agent_conversations WHERE tenant_id = ?", (tenant_id,))
    conn.commit()
    conn.close()
    
    # 1. Save & get memories
    mem_id = save_memory(agent_name="nous", key="work_hours", value="9am - 5pm", confidence=0.9, tenant_id=tenant_id)
    assert mem_id is not None
    
    mem = get_memory(agent_name="nous", key="work_hours", tenant_id=tenant_id)
    assert mem is not None
    assert mem["value"] == "9am - 5pm"
    assert mem["confidence"] == 0.9
    
    all_mems = get_all_memories(agent_name="nous", tenant_id=tenant_id)
    assert len(all_mems) >= 1
    assert any(m["key"] == "work_hours" for m in all_mems)
    
    # 2. Save & search conversation messages
    session_id = "test_session_123"
    msg_id = save_message(session_id, "user", "Hello, my target automation is generating the weekly finance reports.", tenant_id)
    assert msg_id is not None
    
    search_res = search_conversations("finance reports", tenant_id)
    assert len(search_res) >= 1
    assert search_res[0]["role"] == "user"
    assert "weekly finance reports" in search_res[0]["message"]
    
    # 3. Memory nudge (mock/graceful test)
    # If ANTHROPIC_API_KEY is not set, nudge_memory returns []
    nudge_res = nudge_memory(session_id, tenant_id)
    assert isinstance(nudge_res, list)

def test_telegram_bridge():
    """Verify initialization and attributes of TelegramBridge."""
    bridge = TelegramBridge(bot_token="mock_token_123", backend_url="http://localhost:8000")
    assert bridge.bot_token == "mock_token_123"
    assert bridge.backend_url == "http://localhost:8000"
    assert bridge.running is False
    
    # Stop should work even if not running
    bridge.stop()

if __name__ == "__main__":
    print("Running Hermes Agent tests...")
    test_hermes_skills()
    test_hermes_memory()
    test_telegram_bridge()
    print("All tests passed successfully!")
