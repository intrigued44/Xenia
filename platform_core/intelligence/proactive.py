import time
import uuid
import client.db as db
from platform_core.tools.core_tools import registry

class ProactiveEngine:
    def __init__(self):
        self.gmail_connector = None
        self.gcal_connector = None

    def run(self, tenant_id: str) -> list[dict]:
        from platform_core.intelligence.graph import build_from_sessions
        build_from_sessions("local")
        
        proposals = []
        proposals.extend(self._check_missing_recurring_tasks(tenant_id))
        proposals.extend(self._check_behavioral_anomalies(tenant_id))
        if self.gcal_connector:
            proposals.extend(self._check_calendar_preparation(tenant_id))
        if self.gmail_connector:
            proposals.extend(self._check_overdue_followups(tenant_id))
        
        for p in proposals:
            p["id"] = str(uuid.uuid4())
            p["tenant_id"] = tenant_id
            p["created_at"] = int(time.time())
            p["status"] = "pending"
            db.insert_proposal(p)
            try:
                tool = registry.get("notification_tool.toast")
                if tool:
                    tool.execute({"title": "Nous Insight", "message": p["title"]}, tenant_id)
            except Exception as e:
                import logging
                logging.error(f"context: {e}", exc_info=True)
        return proposals

    def _check_missing_recurring_tasks(self, tenant_id: str) -> list[dict]:
        workflows = db.get_workflows(tenant_id=tenant_id)
        sessions_today = db.get_sessions(days=1, tenant_id=tenant_id)
        apps_used_today = {s["primary_app"] for s in sessions_today if s.get("primary_app")}
        
        proposals = []
        for wf in workflows:
            if not wf.get("frequency_per_week") or wf["frequency_per_week"] < 1:
                continue
            app_seq = wf.get("app_sequence", "")
            first_app = app_seq.split(",")[0].strip() if app_seq else ""
            
            from datetime import datetime
            is_weekday = datetime.now().weekday() < 5
            if is_weekday and first_app and first_app not in apps_used_today:
                proposals.append({
                    "type": "reminder",
                    "title": f"Recurring task not started: {wf.get('name', 'Unknown')}",
                    "description": f"This workflow usually runs {wf.get('frequency_per_week'):.1f}x per week but hasn't started today.",
                    "proposed_action": f"Start {wf.get('name', 'Workflow')}",
                    "permission_tier": "auto",
                    "estimated_value_minutes": int(wf.get("avg_duration_seconds", 0) / 60)
                })
        return proposals

    def _check_behavioral_anomalies(self, tenant_id: str) -> list[dict]:
        from platform_core.intelligence.preprocessor import build_analysis_context
        
        this_week = build_analysis_context(days=7)
        last_week_sessions = db.get_sessions(days=14, tenant_id=tenant_id)
        
        this_week_apps = this_week.get("app_usage_minutes", {})
        
        last_week_apps = {}
        for s in last_week_sessions:
            if not s.get("ended_at") or not s.get("primary_app"):
                continue
            started = s["started_at"]
            now = int(time.time())
            if started < (now - 7 * 86400):
                duration_min = (s["ended_at"] - started) / 60
                app = s["primary_app"]
                last_week_apps[app] = last_week_apps.get(app, 0) + duration_min
        
        proposals = []
        for app, this_mins in this_week_apps.items():
            last_mins = last_week_apps.get(app, 0)
            if last_mins > 30 and this_mins > 30:
                change = abs(this_mins - last_mins) / last_mins
                if change > 0.5:
                    direction = "increased" if this_mins > last_mins else "decreased"
                    proposals.append({
                        "type": "anomaly",
                        "title": f"Unusual activity: {app} usage {direction} by {int(change*100)}%",
                        "description": f"{app}: {int(last_mins)}min last week vs {int(this_mins)}min this week.",
                        "proposed_action": "Review activity",
                        "permission_tier": "auto",
                        "estimated_value_minutes": 5
                    })
        return proposals

    def _check_calendar_preparation(self, tenant_id: str) -> list[dict]:
        if not self.gcal_connector:
            return []
        events = self.gcal_connector.get_upcoming(days=1)
        proposals = []
        for event in events:
            if len(event.get("attendees", [])) > 1:
                proposals.append({
                    "type": "meeting_prep",
                    "title": f"Prepare for: {event['title']}",
                    "description": f"Meeting at {event['start']} with {len(event['attendees'])} attendees.",
                    "proposed_action": "Generate meeting brief with attendee research",
                    "permission_tier": "confirm",
                    "estimated_value_minutes": 15
                })
        return proposals

    def _check_overdue_followups(self, tenant_id: str) -> list[dict]:
        if not self.gmail_connector:
            return []
        unanswered = self.gmail_connector.get_unanswered(days=3)
        proposals = []
        for email in unanswered:
            proposals.append({
                "type": "followup",
                "title": f"No reply from: {email.get('sent_to', 'unknown')}",
                "description": f"Subject: {email.get('subject', '')} — sent {email.get('days_since_sent', '?')} days ago.",
                "proposed_action": "Draft follow-up email",
                "permission_tier": "confirm",
                "estimated_value_minutes": 10
            })
        return proposals
