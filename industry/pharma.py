from . import IndustryModule

class PharmaModule(IndustryModule):
    def get_alert_triggers(self):
        return [
            {"trigger": "approval_step_skipped", "severity": "critical"},
            {"trigger": "non_standard_access_sequence", "severity": "high"},
            {"trigger": "document_access_outside_hours", "severity": "medium"}
        ]
        
    def get_compliance_rules(self):
        # Generates 21 CFR Part 11 compatible audit rules
        return ["log_all_document_reads", "require_mfa_for_approval_steps"]
