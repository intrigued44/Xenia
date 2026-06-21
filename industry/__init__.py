from abc import ABC

class IndustryModule(ABC):
    def on_event(self, event):
        pass
        
    def on_workflow_detected(self, workflow):
        pass
        
    def on_session_end(self, session):
        pass
        
    def get_compliance_rules(self):
        return []
        
    def get_alert_triggers(self):
        return []

def load_module(name: str) -> IndustryModule:
    if name == "retail":
        from .retail import RetailModule
        return RetailModule()
    elif name == "pharma":
        from .pharma import PharmaModule
        return PharmaModule()
    elif name == "banking":
        from .banking import BankingModule
        return BankingModule()
    return IndustryModule()
