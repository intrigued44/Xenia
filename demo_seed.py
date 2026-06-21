import os
import sys
import uuid
import time
import random
import json
from datetime import datetime, timedelta

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client.db import get_connection, init_db

PHARMACY_WORKFLOWS = [
    {
        "name": "Daily Sales Entry",
        "description": "Entering daily register sales into accounting systems.",
        "app_sequence": "Excel, Marg, Chrome",
        "freq": 3,
        "duration": 45,
        "potential": 0.6
    },
    {
        "name": "Supplier Invoice Processing",
        "description": "Downloading invoices and feeding them to accounting.",
        "app_sequence": "Chrome, Excel, Tally",
        "freq": 4,
        "duration": 35,
        "potential": 0.9
    },
    {
        "name": "Stock Reorder Check",
        "description": "Checking low stock and messaging suppliers.",
        "app_sequence": "Marg, Excel, WhatsApp Web",
        "freq": 2,
        "duration": 25,
        "potential": 0.75
    },
    {
        "name": "Cash Reconciliation",
        "description": "Matching cash drawer against Tally entries.",
        "app_sequence": "Tally, Excel",
        "freq": 5,
        "duration": 20,
        "potential": 0.85
    },
    {
        "name": "Prescription Processing",
        "description": "Checking doctor prescriptions against inventory.",
        "app_sequence": "Marg, Chrome",
        "freq": 8,
        "duration": 15,
        "potential": 0.3
    },
    {
        "name": "Monthly Report",
        "description": "Generating the month-end tax and sales report.",
        "app_sequence": "Excel, Chrome, Gmail",
        "freq": 1,
        "duration": 60,
        "potential": 0.5
    }
]

def clear_all():
    conn = get_connection()
    cursor = conn.cursor()
    tables = [
        "sessions", "events", "workflows", "proposals", 
        "alerts", "window_logs", "clipboard_logs", "file_logs", 
        "pending_approvals"
    ]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except Exception as e:
            import logging
            logging.error(f"context: {e}", exc_info=True)
    conn.commit()
    conn.close()
    
    # Remove files
    import shutil
    for d in ["briefings", "digests", "reports"]:
        if os.path.exists(d):
            shutil.rmtree(d)

def seed_data():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    # 1. WORKFLOWS
    workflow_ids = []
    for wf in PHARMACY_WORKFLOWS:
        wf_id = str(uuid.uuid4())
        workflow_ids.append(wf_id)
        cursor.execute('''
            INSERT INTO workflows 
            (id, name, description, app_sequence, avg_duration_seconds, frequency_per_week, automation_potential, first_detected, last_seen, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'local')
        ''', (
            wf_id, wf["name"], wf["description"], wf["app_sequence"], 
            wf["duration"] * 60, wf["freq"], wf["potential"], 
            int(thirty_days_ago.timestamp()), int(now.timestamp())
        ))
    
    # 2. SESSIONS (45 spread across 30 days)
    # Generate exactly 45 sessions
    total_sessions = 45
    for i in range(total_sessions):
        # Pick a random day in the last 30 days
        day_offset = random.randint(0, 29)
        # Pick a random hour between 9 AM and 7 PM (19)
        hour = random.randint(9, 18)
        minute = random.randint(0, 59)
        
        start_time = thirty_days_ago + timedelta(days=day_offset, hours=hour, minutes=minute)
        
        # Pick a random workflow based roughly on frequencies
        wf = random.choices(PHARMACY_WORKFLOWS, weights=[w["freq"] for w in PHARMACY_WORKFLOWS])[0]
        
        # Add variation to duration (±20%)
        duration_variance = wf["duration"] * random.uniform(0.8, 1.2)
        end_time = start_time + timedelta(minutes=duration_variance)
        
        session_id = str(uuid.uuid4())
        primary_app = wf["app_sequence"].split(",")[0].strip()
        
        cursor.execute('''
            INSERT INTO sessions (id, started_at, ended_at, primary_app, workflow_label, automation_score, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, 'local')
        ''', (session_id, int(start_time.timestamp()), int(end_time.timestamp()), primary_app, wf["name"], wf["potential"]))
        
        # Insert sequence events
        apps = [a.strip() for a in wf["app_sequence"].split(",")]
        event_time = start_time
        time_step = duration_variance / max(1, len(apps))
        
        for idx, app in enumerate(apps):
            event_ts = int((event_time + timedelta(minutes=time_step * idx)).timestamp())
            try:
                cursor.execute('''
                    INSERT INTO events (session_id, timestamp, event_type, app_name, metadata, tenant_id)
                    VALUES (?, ?, ?, ?, ?, 'local')
                ''', (session_id, event_ts, "window_focus", app, json.dumps({"title": f"{app} - {wf['name']}"})))
            except Exception as e:
                import logging
                logging.error(f"context: {e}", exc_info=True) # skip if schema mismatch for mock data
    
    # 3. PROPOSALS
    proposals = [
        {"type": "followup", "title": "Supplier Ravi Pharma hasn't responded in 4 days", "desc": "Follow up on invoice #4002", "action": "Draft email", "tier": "confirm"},
        {"type": "reminder", "title": "Stock reorder workflow not started today", "desc": "Usually runs by 10 AM.", "action": "Start workflow", "tier": "auto"},
        {"type": "automation_opportunity", "title": "Invoice processing takes 2.3 hrs/week", "desc": "High automation potential detected.", "action": "Review script", "tier": "confirm"},
        {"type": "process_improvement", "title": "Cash reconciliation has 3 variants", "desc": "Standardize the process to save time.", "action": "Generate SOP", "tier": "auto"},
        {"type": "scout_finding", "title": "New GST filing deadline announced", "desc": "Affects pharma distributors. Read more.", "action": "Review alert", "tier": "auto"},
        {"type": "scout_finding", "title": "Competitor opening nearby", "desc": "News article mentions Apollo Pharmacy 2 miles away.", "action": "Read summary", "tier": "auto"},
        {"type": "automation_opportunity", "title": "Daily Sales Entry can be automated", "desc": "Saves 1.5 hrs/week.", "action": "Review script", "tier": "confirm"},
        {"type": "meeting_prep", "title": "Prep: Supplier Sync", "desc": "Meeting at 4PM.", "action": "Generate brief", "tier": "confirm"}
    ]
    
    for p in proposals:
        cursor.execute('''
            INSERT INTO proposals (id, tenant_id, type, title, description, proposed_action, permission_tier, estimated_value_minutes, status, created_at)
            VALUES (?, 'local', ?, ?, ?, ?, ?, ?, 'pending', ?)
        ''', (str(uuid.uuid4()), p["type"], p["title"], p["desc"], p["action"], p["tier"], random.randint(5, 30), int(now.timestamp())))

    # 4. ALERTS
    alerts = [
        {"severity": "high", "title": "End-of-day reconciliation not detected", "desc": "Cash drawer might not match."},
        {"severity": "medium", "title": "3 workflows have no documentation", "desc": "Missing SOPs for critical paths."},
        {"severity": "low", "title": "Unusual spike in Chrome usage this week", "desc": "Up 45% compared to last week."}
    ]
    for a in alerts:
        cursor.execute('''
            INSERT INTO alerts (id, tenant_id, severity, title, description, created_at, status)
            VALUES (?, 'local', ?, ?, ?, ?, 'unread')
        ''', (str(uuid.uuid4()), a["severity"], a["title"], a["desc"], int(now.timestamp())))
    
    conn.commit()
    conn.close()
    
    # 5. FILES
    os.makedirs("briefings", exist_ok=True)
    os.makedirs("digests", exist_ok=True)
    
    date_str = now.strftime("%Y-%m-%d")
    
    with open(f"briefings/{date_str}_morning.md", "w") as f:
        f.write(f"# Morning Briefing — {date_str}\n\n- GST deadline extended by 15 days.\n- Marg ERP rolled out a new update.\n- Consider following up with Ravi Pharma today.\n")
        
    with open(f"digests/{date_str}_strategic.md", "w") as f:
        f.write(f"# Strategic Digest — {date_str}\n\nThe pharmacy is operating with 6 stable workflows. The biggest opportunity is automating the Supplier Invoice Processing, which consumes 2.3 hours weekly. Risk detected: Cash reconciliation process varies widely between shifts.")

    print(f"Demo data loaded successfully.\n 45 sessions | 6 workflows | 8 proposals | 3 alerts\n Start Nous and everything will be populated.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_all()
        print("All data cleared.")
    else:
        seed_data()
