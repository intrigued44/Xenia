from . import IndustryModule
from datetime import datetime
import time

class RetailModule(IndustryModule):
    def get_alert_triggers(self):
        return [
            {"trigger": "end_of_day_reconciliation_missed", "severity": "high"},
            {"trigger": "supplier_followup_overdue", "severity": "medium"},
            {"trigger": "high_return_sku_pattern", "severity": "low"},
            {"trigger": "inventory_reorder_pattern_missed", "severity": "medium"},
            {"trigger": "billing_discrepancy_pattern", "severity": "high"}
        ]

    def get_compliance_rules(self):
        return [
            {"rule": "daily_reconciliation_required", "check_time": "18:00", "severity": "high"},
            {"rule": "supplier_invoice_workflow_documented", "severity": "medium"},
            {"rule": "cash_handling_session_logged", "frequency": "daily", "severity": "high"}
        ]

    def on_workflow_detected(self, workflow):
        name = workflow.get("name", "").lower()
        if "inventory" in name or "reorder" in name:
            if workflow.get("automation_potential", 0) > 0.7:
                return {"alert": True, "message": f"Inventory workflow '{workflow['name']}' has high automation potential"}
        if "reconciliation" in name or "cash" in name:
            return {"tag": "compliance_relevant"}
        return {}

    def on_session_end(self, session):
        current_hour = datetime.now().hour
        billing_apps = ["tally", "marg", "busy", "excel"]
        primary = (session.get("primary_app") or "").lower()
        if current_hour >= 18 and any(app in primary for app in billing_apps):
            return {"check": "reconciliation_required", "session_id": session.get("id")}
        return {}

    def on_event(self, event):
        return {}
