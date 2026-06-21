import json
from dataclasses import dataclass
from typing import List, Dict, Any
from client.db import get_connection, dict_factory
import time

@dataclass
class RetrievalResult:
    intent: str
    data: dict
    summary_stats: dict
    data_density: float
    time_range_days: int
    source_tables: List[str]

class DataRetriever:
    INTENT_KEYWORDS = {
        "app_usage": ["app", "tool", "software", "using", "time", "spent", "hours", "productive", "focus", "distracted", "switching"],
        "workflows": ["workflow", "process", "task", "recurring", "routine", "pattern", "repeat", "sequence", "doing", "doing every", "always"],
        "automation": ["automate", "automation", "save time", "inefficient", "manual", "repetitive", "script", "optimize", "candidate"],
        "alerts": ["alert", "issue", "problem", "anomaly", "unusual", "warning", "spike", "drop", "wrong", "broken", "attention"],
        "proposals": ["proposal", "suggestion", "recommend", "pending", "review", "waiting", "decide", "approve", "action"],
        "health": ["health", "score", "performance", "team", "department", "function", "overall", "how are we", "how is the team"],
        "profile": ["my", "me", "personal", "own", "mine", "profile", "contribution", "what have i", "what did i"],
        "graph": ["connected", "dependency", "bottleneck", "central", "who", "which tool", "relationship", "network", "hub", "most used"]
    }

    def _classify_intent(self, query: str) -> str:
        q = query.lower()
        scores = {intent: 0 for intent in self.INTENT_KEYWORDS.keys()}
        import re
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for kw in keywords:
                if len(kw) <= 2:
                    if re.search(r'\b' + re.escape(kw) + r'\b', q):
                        scores[intent] += 1
                else:
                    if kw in q:
                        scores[intent] += 2  # longer keywords carry more weight
        
        best_intent = max(scores, key=scores.get)
        if scores[best_intent] == 0:
            return "general"
        
        # Tie breaker rules or more precise check if needed, 
        # actually 'me', 'my', 'i' causes 'profile' to trigger often.
        # Let's fix 'i' matching within words by padding with spaces.
        return best_intent

    def _calculate_density(self, row_count: int) -> float:
        if row_count == 0: return 0.0
        if row_count < 5: return 0.2
        if row_count < 20: return 0.5
        if row_count < 100: return 0.8
        return 1.0

    def retrieve(self, query: str, tenant_id: str) -> RetrievalResult:
        intent = self._classify_intent(query)
        conn = get_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        data = {}
        stats = {}
        source_tables = []
        row_count = 0
        time_range = 7
        
        try:
            if intent == "app_usage":
                cursor.execute("""
                    SELECT app_name, COUNT(*) as appearances,
                    SUM(CASE WHEN typeof(window_title) = 'text' THEN length(window_title) ELSE 0 END) as title_changes
                    FROM window_logs WHERE tenant_id=? AND timestamp >= datetime('now','-7 days')
                    GROUP BY app_name ORDER BY appearances DESC LIMIT 15
                """, (tenant_id,))
                rows = cursor.fetchall()
                data["app_usage"] = rows
                row_count = len(rows)
                source_tables.append("window_logs")
                
                stats = {
                    "total_observations": sum(r["appearances"] for r in rows),
                    "unique_apps": len(rows),
                    "top_app": rows[0]["app_name"] if rows else None,
                    "date_range": "7 days"
                }

            elif intent == "workflows":
                cursor.execute("SELECT * FROM workflows WHERE tenant_id=? ORDER BY frequency_per_week DESC", (tenant_id,))
                rows = cursor.fetchall()
                data["workflows"] = rows
                row_count = len(rows)
                source_tables.append("workflows")
                
                stats = {
                    "total_workflows": len(rows),
                    "high_automation_count": sum(1 for r in rows if r.get("automation_potential", 0) > 0.7),
                    "total_weekly_hours": round(sum(r.get("frequency_per_week", 0) * r.get("avg_duration_seconds", 0) / 3600 for r in rows), 1),
                    "most_frequent_workflow": rows[0]["name"] if rows else None
                }

            elif intent == "automation":
                cursor.execute("SELECT * FROM workflows WHERE tenant_id=? AND automation_potential > 0.5 ORDER BY automation_potential DESC", (tenant_id,))
                wf_rows = cursor.fetchall()
                cursor.execute("SELECT * FROM proposals WHERE tenant_id=? AND type='automation' AND status='pending'", (tenant_id,))
                prop_rows = cursor.fetchall()
                data["automation_candidates"] = wf_rows
                data["pending_automation_proposals"] = prop_rows
                row_count = len(wf_rows) + len(prop_rows)
                source_tables.extend(["workflows", "proposals"])
                
                stats = {
                    "automation_candidates_count": len(wf_rows),
                    "total_hours_recoverable_per_week": round(sum(r.get("frequency_per_week", 0) * r.get("avg_duration_seconds", 0) / 3600 for r in wf_rows), 1),
                    "top_candidate_name": wf_rows[0]["name"] if wf_rows else None,
                    "top_candidate_potential": wf_rows[0]["automation_potential"] if wf_rows else None
                }

            elif intent == "alerts":
                cursor.execute("SELECT * FROM alerts WHERE tenant_id=? AND status != 'resolved' ORDER BY created_at DESC LIMIT 20", (tenant_id,))
                rows = cursor.fetchall()
                data["alerts"] = rows
                row_count = len(rows)
                source_tables.append("alerts")
                
                stats = {
                    "unresolved_count": len(rows),
                    "critical_count": sum(1 for r in rows if r.get("severity") == "critical"),
                    "latest_alert_title": rows[0]["title"] if rows else None
                }

            elif intent == "proposals":
                cursor.execute("SELECT * FROM proposals WHERE tenant_id=? AND status='pending' ORDER BY created_at DESC", (tenant_id,))
                rows = cursor.fetchall()
                data["proposals"] = rows
                row_count = len(rows)
                source_tables.append("proposals")
                
                now = int(time.time())
                stats = {
                    "pending_count": len(rows),
                    "total_value_minutes_pending": sum(r.get("estimated_value_minutes", 0) for r in rows),
                    "oldest_pending_days": round((now - rows[-1]["created_at"]) / 86400) if rows else 0
                }

            elif intent == "health":
                time_range = 30
                cursor.execute("SELECT automation_score, workflow_label FROM sessions WHERE tenant_id=? AND started_at >= strftime('%s','now','-30 days')", (tenant_id,))
                session_rows = cursor.fetchall()
                cursor.execute("SELECT count(*) as c FROM workflows WHERE tenant_id=?", (tenant_id,))
                wf_count = cursor.fetchone()["c"]
                cursor.execute("SELECT count(*) as c FROM alerts WHERE tenant_id=? AND status != 'resolved'", (tenant_id,))
                alert_count = cursor.fetchone()["c"]
                cursor.execute("SELECT count(*) as c FROM proposals WHERE tenant_id=? AND status='pending'", (tenant_id,))
                prop_count = cursor.fetchone()["c"]
                
                row_count = len(session_rows)
                source_tables.extend(["sessions", "workflows", "alerts", "proposals"])
                data["sessions_summary"] = {"count": len(session_rows)}
                
                auto_scores = [r["automation_score"] for r in session_rows if r.get("automation_score") is not None]
                if auto_scores:
                    hs = sum(auto_scores) / len(auto_scores) * 100
                else:
                    hs = min(len(session_rows) / 100, 100)
                    
                stats = {
                    "health_score": round(hs, 1),
                    "session_count_30d": len(session_rows),
                    "workflow_count": wf_count,
                    "active_alerts": alert_count,
                    "pending_proposals": prop_count
                }

            elif intent == "profile":
                time_range = 30
                now_str = str(int(time.time()))
                thirty_days_ago_str = str(int(time.time()) - 30 * 86400)
                seven_days_ago_str = str(int(time.time()) - 7 * 86400)

                cursor.execute("SELECT count(*) as c FROM sessions WHERE tenant_id=? AND started_at >= ?", (tenant_id, thirty_days_ago_str))
                month_sessions = cursor.fetchone()["c"]
                cursor.execute("SELECT count(*) as c FROM sessions WHERE tenant_id=? AND started_at >= ?", (tenant_id, seven_days_ago_str))
                week_sessions = cursor.fetchone()["c"]
                
                cursor.execute("SELECT app_name, count(*) as c FROM window_logs WHERE tenant_id=? AND timestamp >= datetime('now','-30 days') GROUP BY app_name ORDER BY c DESC LIMIT 3", (tenant_id,))
                top_apps = [r["app_name"] for r in cursor.fetchall()]
                
                cursor.execute("SELECT count(*) as c FROM workflows WHERE tenant_id=?", (tenant_id,))
                wf_count = cursor.fetchone()["c"]
                
                cursor.execute("SELECT count(*) as c FROM clipboard_logs WHERE tenant_id=? AND timestamp >= datetime('now','-30 days')", (tenant_id,))
                clip_count = cursor.fetchone()["c"]
                
                cursor.execute("SELECT count(*) as c FROM file_logs WHERE tenant_id=? AND timestamp >= datetime('now','-30 days')", (tenant_id,))
                file_count = cursor.fetchone()["c"]
                
                row_count = month_sessions + clip_count + file_count
                source_tables.extend(["sessions", "window_logs", "workflows", "clipboard_logs", "file_logs"])
                
                stats = {
                    "sessions_this_week": week_sessions,
                    "sessions_this_month": month_sessions,
                    "top_3_apps": top_apps,
                    "workflows_detected": wf_count,
                    "clipboard_events_30d": clip_count,
                    "file_events_30d": file_count
                }

            elif intent == "graph":
                from platform_core.intelligence.graph import get_graph_data
                graph_data = get_graph_data(tenant_id)
                data["graph"] = graph_data
                row_count = graph_data["summary"]["nodes"] + graph_data["summary"]["edges"]
                source_tables.extend(["graph_nodes", "graph_edges"])
                stats = {
                    "node_count": graph_data["summary"]["nodes"],
                    "edge_count": graph_data["summary"]["edges"],
                    "most_connected_node": graph_data.get("most_connected", {}).get("label") if graph_data.get("most_connected") else None,
                    "most_connected_count": graph_data.get("most_connected", {}).get("connections", 0) if graph_data.get("most_connected") else 0
                }

            else: # general
                cursor.execute("SELECT count(*) as c FROM sessions WHERE tenant_id=? AND started_at >= ?", (tenant_id, str(int(time.time()) - 7*86400)))
                sess_count = cursor.fetchone()["c"]
                cursor.execute("SELECT app_name, count(*) as c FROM window_logs WHERE tenant_id=? AND timestamp >= datetime('now','-7 days') GROUP BY app_name ORDER BY c DESC LIMIT 5", (tenant_id,))
                top_apps = [r["app_name"] for r in cursor.fetchall()]
                cursor.execute("SELECT count(*) as c FROM alerts WHERE tenant_id=? AND status != 'resolved'", (tenant_id,))
                alert_count = cursor.fetchone()["c"]
                cursor.execute("SELECT count(*) as c FROM proposals WHERE tenant_id=? AND status='pending'", (tenant_id,))
                prop_count = cursor.fetchone()["c"]
                cursor.execute("SELECT count(*) as c FROM workflows WHERE tenant_id=?", (tenant_id,))
                wf_count = cursor.fetchone()["c"]
                cursor.execute("SELECT count(*) as c FROM vault_records WHERE tenant_id=?", (tenant_id,))
                vault_count = cursor.fetchone()["c"]
                
                row_count = sess_count + alert_count + prop_count + wf_count + vault_count
                source_tables.extend(["sessions", "window_logs", "alerts", "proposals", "workflows", "vault_records"])
                stats = {
                    "session_count_7d": sess_count,
                    "top_5_apps": top_apps,
                    "unresolved_alerts": alert_count,
                    "pending_proposals": prop_count,
                    "workflow_count": wf_count,
                    "vault_record_count": vault_count
                }
                
        except Exception as e:
            print(f"Error in DataRetriever: {e}")
            stats["error"] = str(e)
        finally:
            conn.close()

        density = self._calculate_density(row_count)
        
        return RetrievalResult(
            intent=intent,
            data=data,
            summary_stats=stats,
            data_density=density,
            time_range_days=time_range,
            source_tables=list(set(source_tables))
        )
