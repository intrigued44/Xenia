import sqlite3
import time
import os
import uuid
import json
from client.db import get_connection

def save_memory(agent_name: str, key: str, value: str, confidence: float = 1.0, tenant_id: str = "local") -> str:
    """Saves or updates a memory key-value pair in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if memory key already exists for this agent and tenant
    cursor.execute("""
        SELECT id FROM agent_memories 
        WHERE agent_name = ? AND key = ? AND tenant_id = ?
    """, (agent_name, key, tenant_id))
    row = cursor.fetchone()
    
    current_time = int(time.time())
    if row:
        memory_id = row[0]
        cursor.execute("""
            UPDATE agent_memories 
            SET value = ?, confidence = ?, updated_at = ? 
            WHERE id = ?
        """, (value, confidence, current_time, memory_id))
    else:
        memory_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO agent_memories (id, agent_name, key, value, confidence, tenant_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (memory_id, agent_name, key, value, confidence, tenant_id, current_time))
        
    conn.commit()
    conn.close()
    return memory_id

def get_memory(agent_name: str, key: str, tenant_id: str = "local") -> dict:
    """Retrieves a specific memory for an agent."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, value, confidence, updated_at 
        FROM agent_memories 
        WHERE agent_name = ? AND key = ? AND tenant_id = ?
    """, (agent_name, key, tenant_id))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "agent_name": agent_name,
            "key": key,
            "value": row[1],
            "confidence": row[2],
            "updated_at": row[3]
        }
    return None

def get_all_memories(agent_name: str, tenant_id: str = "local") -> list:
    """Retrieves all memories for an agent."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT key, value, confidence, updated_at 
        FROM agent_memories 
        WHERE agent_name = ? AND tenant_id = ?
    """, (agent_name, tenant_id))
    rows = cursor.fetchall()
    conn.close()
    
    memories = []
    for r in rows:
        memories.append({
            "key": r[0],
            "value": r[1],
            "confidence": r[2],
            "updated_at": r[3]
        })
    return memories

def save_message(session_id: str, role: str, message: str, tenant_id: str = "local") -> str:
    """Saves a message in the conversation history."""
    conn = get_connection()
    cursor = conn.cursor()
    message_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO agent_conversations (id, session_id, role, message, tenant_id, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (message_id, session_id, role, message, tenant_id, int(time.time())))
    conn.commit()
    conn.close()
    return message_id

def search_conversations(query_str: str, tenant_id: str = "local") -> list:
    """Searches agent conversations using keyword match (LIKE)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT session_id, role, message, timestamp 
        FROM agent_conversations 
        WHERE tenant_id = ? AND message LIKE ?
        ORDER BY timestamp DESC 
        LIMIT 50
    """, (tenant_id, f"%{query_str}%"))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        results.append({
            "session_id": r[0],
            "role": r[1],
            "message": r[2],
            "timestamp": r[3]
        })
    return results

def nudge_memory(session_id: str, tenant_id: str = "local") -> list:
    """
    Analyses recent conversation messages to identify and extract 
    important facts, preferences, user habits or rules, and saves them
    into agent_memories.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[Memory Engine] No API key available for dynamic memory nudge.")
        return []
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, message 
        FROM agent_conversations 
        WHERE session_id = ? AND tenant_id = ?
        ORDER BY timestamp ASC
    """, (session_id, tenant_id))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return []
        
    conversation_text = ""
    for role, msg in rows:
        conversation_text += f"{role.upper()}: {msg}\n"
        
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    
    sys_prompt = (
        "You are the memory engine of the Hermes Agent in Xenia.\n"
        "Your task is to analyze the user conversation and extract persistent memory facts about the user.\n"
        "Focus on: User habits, work schedule, software preferences, team member names/roles, credentials/systems used, and communication style.\n"
        "Format your answer as a JSON array of objects, each containing 'key', 'value', and 'confidence' (0.0 to 1.0).\n"
        "Return ONLY the raw JSON array, without any markdown formatting, backticks, or comments."
    )
    
    prompt = (
        f"Analyze this conversation:\n\n{conversation_text}\n\n"
        "Extract new facts, habits, or updates to the user profile."
    )
    
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=sys_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.content[0].text.strip()
        
        # Clean markdown code block wraps if LLM still wraps it
        if content.startswith("```"):
            if "json" in content:
                content = content.split("json")[1].split("```")[0]
            else:
                content = content.split("```")[1].split("```")[0]
        content = content.strip()
        
        updates = json.loads(content)
        saved_keys = []
        for update in updates:
            key = update.get("key")
            value = update.get("value")
            confidence = update.get("confidence", 0.8)
            if key and value:
                save_memory(agent_name="nous", key=key, value=str(value), confidence=confidence, tenant_id=tenant_id)
                saved_keys.append(key)
                print(f"[Memory Engine] Saved profile fact: {key} -> {value}")
        return saved_keys
    except Exception as e:
        print(f"[Memory Engine] Failed to nudge memory: {e}")
        return []
