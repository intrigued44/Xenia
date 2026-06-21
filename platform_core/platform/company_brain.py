from client.db import get_workflows
from platform_core.intelligence.graph import get_most_connected

def get_brain_summary(tenant_id: str) -> dict:
    """
    Aggregates behavioral patterns across all users in a tenant.
    Raw events are never queried here, only anonymized graphs and tracked workflows.
    """
    workflows = get_workflows(tenant_id=tenant_id)
    bottlenecks = get_most_connected(tenant_id=tenant_id, limit=5)
    
    # Analyze cross-tenant overlap
    frequent_tools = {}
    total_time_saved = 0
    
    for wf in workflows:
        total_time_saved += wf.get("avg_duration_seconds", 0) * wf.get("frequency_per_week", 1)
        
    return {
        "tenant_id": tenant_id,
        "total_workflows_tracked": len(workflows),
        "total_estimated_time_saved_hours": round(total_time_saved / 3600, 2),
        "key_bottlenecks": bottlenecks,
        "shared_knowledge_cards": [wf["name"] for wf in workflows if wf.get("description")]
    }

def query_brain(query: str, tenant_id: str) -> str:
    """
    Simulates a natural language query over the aggregate company brain.
    """
    summary = get_brain_summary(tenant_id)
    # Real implementation uses Claude on the graph DB
    if "tally" in query.lower():
        return "Based on organizational aggregate data, Tally is most frequently used in conjunction with Excel and the local File Explorer."
    elif "finance" in query.lower():
        return f"The most time-consuming process tracked is {summary['shared_knowledge_cards'][0] if summary['shared_knowledge_cards'] else 'unknown'}."
    return f"Company brain context retrieved. Total automated workflows: {summary['total_workflows_tracked']}"
