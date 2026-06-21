import sqlite3
import time
import os
import uuid
import json
from client.db import get_connection

def save_skill(name: str, description: str, code_content: str, tenant_id: str = "local", nodes_json: str = None) -> str:
    """Saves or updates a skill in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if skill exists
    cursor.execute("SELECT id, version FROM agent_skills WHERE name = ? AND tenant_id = ?", (name, tenant_id))
    row = cursor.fetchone()
    
    if row:
        skill_id = row[0]
        version = row[1] + 1
        cursor.execute("""
            UPDATE agent_skills 
            SET description = ?, code_content = ?, nodes_json = ?, version = ?, created_at = ? 
            WHERE id = ?
        """, (description, code_content, nodes_json, version, int(time.time()), skill_id))
    else:
        skill_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO agent_skills (id, name, description, code_content, nodes_json, success_count, failure_count, version, tenant_id, created_at)
            VALUES (?, ?, ?, ?, ?, 0, 0, 1, ?, ?)
        """, (skill_id, name, description, code_content, nodes_json, tenant_id, int(time.time())))
        
    conn.commit()
    conn.close()
    return skill_id

def get_skill(name: str, tenant_id: str = "local") -> dict:
    """Retrieves a skill by name."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, description, code_content, success_count, failure_count, version, nodes_json
        FROM agent_skills 
        WHERE name = ? AND tenant_id = ?
    """, (name, tenant_id))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "code_content": row[3],
            "success_count": row[4],
            "failure_count": row[5],
            "version": row[6],
            "nodes_json": row[7]
        }
    return None

def log_skill_run(name: str, success: bool, error_message: str = None, tenant_id: str = "local"):
    """Increments the success or failure count for a skill."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if success:
        cursor.execute("""
            UPDATE agent_skills 
            SET success_count = success_count + 1 
            WHERE name = ? AND tenant_id = ?
        """, (name, tenant_id))
    else:
        cursor.execute("""
            UPDATE agent_skills 
            SET failure_count = failure_count + 1 
            WHERE name = ? AND tenant_id = ?
        """, (name, tenant_id))
        
        # If there's an error message and a script path is known, log it
        if error_message:
            print(f"[Skills Engine] Logging error for skill '{name}': {error_message}")
            
    conn.commit()
    conn.close()

def self_heal_skill(name: str, error_message: str, tenant_id: str = "local") -> str:
    """Uses LLM to correct the skill's code based on the error message."""
    skill = get_skill(name, tenant_id)
    if not skill:
        return None
        
    original_code = skill["code_content"]
    description = skill["description"]
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[Skills Engine] No API key available for self-healing.")
        return original_code
        
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    
    sys_prompt = (
        "You are the self-healing module of the Hermes Agent in Xenia.\n"
        "You fix failing automation scripts. Analyze the error traceback and edit the code to fix the issue.\n"
        "Keep the script runnable on Windows using stdlib, pyperclip, or pygetwindow.\n"
        "Return ONLY the corrected Python script code inside a code block (no introductory text)."
    )
    
    prompt = (
        f"Goal: {description}\n\n"
        f"Original Code:\n```python\n{original_code}\n```\n\n"
        f"Error Output / Traceback:\n{error_message}\n\n"
        f"Corrected Code:"
    )
    
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2500,
            system=sys_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        healed_code = response.content[0].text
        
        # Clean formatting
        if "```python" in healed_code:
            healed_code = healed_code.split("```python")[1].split("```")[0]
        elif "```" in healed_code:
            healed_code = healed_code.split("```")[1].split("```")[0]
            
        healed_code = healed_code.strip()
        
        # Save healed code to database
        save_skill(name, description, healed_code, tenant_id)
        print(f"[Skills Engine] Successfully self-healed skill '{name}' to version {skill['version'] + 1}")
        return healed_code
    except Exception as e:
        print(f"[Skills Engine] Failed to self-heal skill: {e}")
        return original_code

def run_and_heal_skill(name: str, code_content: str, tenant_id: str = "local") -> dict:
    """
    Executes the Python code using exec(), catches any traceback/exception,
    logs the run to log_skill_run(), and triggers self_heal_skill() if it fails.
    """
    import sys
    import io
    import traceback
    
    # Capture stdout/stderr
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout
    sys.stderr = stderr
    
    success = True
    error_msg = None
    
    try:
        # Create a local environment
        local_env = {"os": os, "time": time, "sys": sys, "__name__": "__main__"}
        exec(code_content, local_env, local_env)
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
        
    log_skill_run(name, success, error_msg or output_str, tenant_id)
    
    if not success:
        print(f"[Skills Engine] Skill '{name}' failed. Triggering self-healing...")
        healed_code = self_heal_skill(name, error_msg or output_str, tenant_id)
        return {"success": False, "error": error_msg, "output": output_str, "healed_code": healed_code}
        
    return {"success": True, "output": output_str}

