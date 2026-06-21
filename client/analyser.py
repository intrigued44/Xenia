import os
import json
from anthropic import Anthropic

from . import db
from . import preprocessor

def generate_weekly_digest():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set", "summary": "", "workflows": [], "automation_candidates": []}

    client = Anthropic(api_key=api_key)

    context_dict = preprocessor.build_analysis_context(days=7)
    
    context_str = f"Total Work Hours: {context_dict['total_work_hours']}\n"
    context_str += f"Total Sessions: {context_dict['total_sessions']}\n\n"
    context_str += f"Most Used Apps: {', '.join(context_dict['most_used_apps'])}\n\n"
    context_str += "Detected Patterns (App Sequences):\n"
    
    for p in context_dict['detected_patterns']:
        seq = " -> ".join(p['app_sequence'])
        context_str += f"- {seq} (Occurred {p['session_count']} times, Avg Duration: {p['avg_duration_minutes']} min)\n"

    prompt = f"""
    You are an AI assistant analyzing a user's work behavior based on passive logs.
    Your goal is to figure out their actual processes.
    
    Here is a structured summary of their recent activity:
    {context_str}
    
    You must respond ONLY with a valid JSON object matching this exact schema, with no markdown formatting around it:
    {{
      "workflows": [{{"id":"string","name":"string","description":"string","steps":["string"],"app_sequence":"string","avg_duration_seconds":0,"frequency_per_week":0.0,"automation_potential":0.0}}],
      "automation_candidates": [{{"workflow_name":"string","weekly_hours_lost":0.0,"automation_complexity":"low|medium|high","suggested_approach":"string"}}],
      "anomalies": ["string"],
      "summary": "string"
    }}
    """

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = response.content[0].text
        # Clean potential markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        digest_data = json.loads(response_text.strip())
        
        # Store each detected workflow in DB
        import uuid
        import time
        for wf in digest_data.get('workflows', []):
            db.upsert_workflow({
                "id": wf.get('id', str(uuid.uuid4())),
                "name": wf.get('name', 'Unknown Workflow'),
                "description": wf.get('description', ''),
                "app_sequence": json.dumps(wf.get('steps', [])),
                "avg_duration_seconds": wf.get('avg_duration_seconds', 0),
                "frequency_per_week": wf.get('frequency_per_week', 0.0),
                "automation_potential": wf.get('automation_potential', 0.0),
                "first_detected": int(time.time()),
                "last_seen": int(time.time())
            })
            
        return digest_data
    except Exception as e:
        print(f"Error communicating with Anthropic API: {str(e)}")
        return {"error": str(e), "summary": "", "workflows": [], "automation_candidates": []}

if __name__ == "__main__":
    print(generate_weekly_digest())
