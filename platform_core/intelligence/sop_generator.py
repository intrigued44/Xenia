import sqlite3
import json
import os
import time

def generate_sop_from_logs(db_path, start_time_str, end_time_str, task_name="Automated Task"):
    """
    Scans the observer database for a given time window, extracts OCR text,
    and generates a step-by-step Standard Operating Procedure (SOP).
    """
    if not os.path.exists(db_path):
        return "Database not found."

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # We query window_title and extracted_text within the timeframe
    c.execute("""
        SELECT timestamp, window_title, extracted_text
        FROM screen_logs
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    """, (start_time_str, end_time_str))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return "No activity logs found for the given time window."
        
    # Collate data
    timeline = []
    last_title = ""
    for r in rows:
        ts, title, text = r
        if not title: title = "Unknown Window"
        if not text: text = ""
        
        # Only add a timeline step if the window changed or significant text appeared
        if title != last_title or len(text.split()) > 10:
            timeline.append(f"[{ts}] Window: {title} | On-Screen Text Snippet: {text[:100]}...")
            last_title = title

    # Build prompt for LLM
    prompt = f"""
    System: You are an Elite Operations Manager. Your job is to convert raw background observer logs into a beautiful, step-by-step Standard Operating Procedure (SOP) training manual.
    
    Task: {task_name}
    Raw Activity Logs:
    {chr(10).join(timeline[:50])} # limit to 50 for token constraints
    
    Please output a Markdown formatted SOP with:
    1. Objective
    2. Applications Used
    3. Step-by-Step Instructions (infer the logical steps from the timeline)
    """
    
    return _call_llm(prompt)

def _call_llm(prompt: str) -> str:
    # Use Anthropic if key exists, otherwise mock
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your_key_here":
        return """
# Standard Operating Procedure: Automated Task

## 1. Objective
To document and standardize the workflow captured by the Xenia Observer based on on-screen OCR and window activity.

## 2. Applications Used
- Microsoft Excel
- Google Chrome

## 3. Step-by-Step Instructions
**Step 1: Data Initialization**
- Open Microsoft Excel.
- Locate the "Find and Replace" dialog box.

**Step 2: Processing**
- Execute bulk text replacement across the active worksheet based on the rules observed in the OCR buffer.
- Save the document.

*(Note: This is a mocked SOP because no Anthropic API Key was detected in the environment. Add your key to generate real dynamic SOPs.)*
        """
        
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error generating SOP: {str(e)}"

if __name__ == "__main__":
    # Example usage
    # get timestamps from 1 hour ago
    t_now = time.time()
    # Mock some ISO times
    print(generate_sop_from_logs("../../mvp_data.db", "2026-06-05 10:00:00", "2026-06-08 23:59:59"))
