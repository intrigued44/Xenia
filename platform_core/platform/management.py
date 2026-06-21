from .company_brain import get_brain_summary

def get_insights(tenant_id: str) -> dict:
    """
    Aggregate organizational intelligence for managers and executives.
    Individual data never surfaces. Only patterns.
    """
    brain = get_brain_summary(tenant_id)
    
    return {
        "process_variance_score": 0.35, # Mock: High variance = training gap
        "automation_opportunity_hours": brain["total_estimated_time_saved_hours"],
        "knowledge_concentration_risk": ["Invoice Approval", "End of Month Reconciliation"], 
        "tool_adoption_map": {
            "licensed": ["Slack", "Salesforce", "Tally"],
            "actually_used": ["WhatsApp", "Excel", "Tally"]
        },
        "workflow_bottleneck_map": brain["key_bottlenecks"]
    }
