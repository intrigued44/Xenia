from . import IndustryModule

class BankingModule(IndustryModule):
    def get_alert_triggers(self):
        return [
            {"trigger": "unusual_data_access_patterns", "severity": "critical"}
        ]
        
    def get_compliance_rules(self):
        # KYC workflow compliance monitoring
        return ["track_kyc_document_origin"]
