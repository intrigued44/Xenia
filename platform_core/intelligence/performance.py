from platform_core.vaults.vault_manager import VaultManager
from platform_core.vaults.models import VaultLevel

class PerformanceDashboard:

    def get_team_dashboard(self,
                           tenant_id: str) -> dict:
        # Aggregate metrics across all vault records
        vault_manager = VaultManager()
        
        team_records = vault_manager.retrieve_as_agent(
            VaultLevel.TEAM, tenant_id,
            agent_name="architect"
        )
        
        org_records = vault_manager.retrieve_as_agent(
            VaultLevel.ORGANIZATION, tenant_id,
            agent_name="strategist"
        )
        
        # Process health metrics
        total_processes = len(team_records)
        
        improvement_records = [
            r for r in team_records
            if r.get("record_type") == "improvement"
        ]
        
        alert_records = [
            r for r in team_records
            if r.get("record_type") == "operational_alert"
        ]
        
        intel_records = [
            r for r in org_records
            if r.get("record_type") == "intelligence"
        ]
        
        return {
            "status": "ready",
            "team_metrics": {
                "total_processes_tracked": total_processes,
                "improvement_opportunities": 
                    len(improvement_records),
                "active_alerts": len(alert_records),
                "external_intelligence_items": 
                    len(intel_records)
            },
            "recent_improvements": [
                {
                    "description": r["content"].get(
                        "description",""
                    ),
                    "type": r["content"].get("type",""),
                    "time_recovery": r["content"].get(
                        "estimated_time_recovery_minutes",0
                    )
                }
                for r in improvement_records[:5]
            ],
            "active_alerts": [
                {
                    "message": r["content"].get(
                        "message",""
                    ),
                    "timestamp": r.get("created_at",0)
                }
                for r in alert_records[:5]
            ]
        }
