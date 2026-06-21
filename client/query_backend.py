import os
from anthropic import Anthropic
from client import db
from client import preprocessor

class ChatSession:
    def __init__(self):
        self.history = []

chat_session = ChatSession()

def ask_nous(query, session_id="default_session", tenant_id="local"):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Please set ANTHROPIC_API_KEY environment variable to use the query interface."
        
    # Import memory engine functions
    from platform_core.intelligence.memory_engine import save_message, get_all_memories, nudge_memory
    
    # Save the user query to conversation history database
    save_message(session_id, "user", query, tenant_id)
    
    client = Anthropic(api_key=api_key)
    context_dict = preprocessor.build_analysis_context(days=7)
    workflows = db.get_workflows()
    
    # Ground the assistant with user profiling memories retrieved from the database
    memories = get_all_memories("nous", tenant_id)
    memory_str = ""
    if memories:
        memory_str += "Known Facts about the User / Profile:\n"
        for mem in memories:
            memory_str += f"- {mem['key']}: {mem['value']} (Confidence: {mem['confidence']})\n"
            
    context_str = f"Total Work Hours: {context_dict['total_work_hours']}\n"
    context_str += f"Total Sessions: {context_dict['total_sessions']}\n\n"
    context_str += f"Most Used Apps: {', '.join(context_dict['most_used_apps'])}\n\n"
    context_str += "Detected Patterns (App Sequences):\n"
    
    for p in context_dict['detected_patterns']:
        seq = " -> ".join(p['app_sequence'])
        context_str += f"- {seq} (Occurred {p['session_count']} times)\n"
        
    workflow_str = ""
    for w in workflows:
        workflow_str += f"- {w.get('name', 'Unknown')}: {w.get('app_sequence', [])}\n"

    system_prompt = f"""You are an operational intelligence assistant for Xenia. 
You have access to this person's actual work behavior data. 
Answer only from the provided context. 
If the data does not support an answer, say so clearly.
Never invent workflows or processes that are not in the context.

{memory_str}

Context: {context_str}
Known Workflows: {workflow_str}"""

    # Retrieve recent chat history from the DB for this session
    import sqlite3
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, message 
        FROM agent_conversations 
        WHERE session_id = ? AND tenant_id = ? 
        ORDER BY timestamp ASC 
        LIMIT 20
    """, (session_id, tenant_id))
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for r_role, r_msg in rows:
        # Avoid duplicating the user query if it's already there
        if r_role == "user" and r_msg == query and len(messages) == len(rows) - 1:
            continue
        messages.append({"role": r_role, "content": r_msg})
        
    messages.append({"role": "user", "content": query})

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            system=system_prompt,
            max_tokens=800,
            messages=messages
        )
        answer = response.content[0].text
        
        # Save the assistant response to conversation history database
        save_message(session_id, "assistant", answer, tenant_id)
        
        # Run a memory nudge to update user facts & profile
        nudge_memory(session_id, tenant_id)
        
        return answer
    except Exception as e:
        return f"Error: {str(e)}"

