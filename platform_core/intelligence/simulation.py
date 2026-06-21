import json
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from client.db import get_connection, dict_factory

@dataclass
class SimulationScenario:
    scenario_type: str
    target: str
    change_percent: int
    direction: str
    context: str = ""

@dataclass
class SimulationResult:
    id: str
    scenario: SimulationScenario
    before_state: dict
    after_state: dict
    delta: dict
    narrative: str
    risks: List[str]
    opportunities: List[str]
    confidence: str
    confidence_rationale: str
    affected_workflows: List[str]
    hours_saved_per_week: float
    monthly_value_hours: float
    health_score_before: float
    health_score_after: float
    data_observations: int
    created_at: int
    
class SimulationError(Exception):
    pass

class SimulationEngine:
    def __init__(self):
        pass
        
    def _call_claude(self, prompt: str) -> str:
        import os
        from anthropic import Anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY", "your_key_here")
        if api_key == "your_key_here":
            return json.dumps({
                "narrative": "Simulation narrative placeholder since no API key.",
                "risks": ["Risk 1", "Risk 2", "Risk 3"],
                "opportunities": ["Opportunity 1", "Opportunity 2"]
            })
            
        client = Anthropic(api_key=api_key)
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return json.dumps({
                "narrative": f"Simulation ran but Claude narrative failed: {str(e)}",
                "risks": [],
                "opportunities": []
            })

    def _get_health_score(self, tenant_id: str) -> float:
        conn = get_connection()
        conn.row_factory = dict_factory
        c = conn.cursor()
        c.execute("SELECT automation_score FROM sessions WHERE tenant_id=? AND started_at >= strftime('%s','now','-30 days')", (tenant_id,))
        rows = c.fetchall()
        conn.close()
        
        scores = [r["automation_score"] for r in rows if r.get("automation_score") is not None]
        if scores:
            return sum(scores) / len(scores) * 100
        return min(len(rows) / 100, 100)

    def simulate(self, scenario: SimulationScenario, tenant_id: str) -> SimulationResult:
        conn = get_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        before_state = {}
        after_state = {}
        delta = {}
        confidence = "low"
        confidence_rationale = ""
        affected_workflows = []
        hours_saved_per_week = 0.0
        health_score_before = self._get_health_score(tenant_id)
        health_score_after = health_score_before
        data_observations = 0
        
        try:
            if scenario.scenario_type == "automate_workflow":
                cursor.execute("SELECT * FROM workflows WHERE tenant_id=? AND lower(name) LIKE ?", (tenant_id, f"%{scenario.target.lower()}%"))
                wf = cursor.fetchone()
                if not wf:
                    cursor.execute("SELECT name FROM workflows WHERE tenant_id=?", (tenant_id,))
                    names = [r["name"] for r in cursor.fetchall()]
                    raise SimulationError(f"No workflow found matching '{scenario.target}'. Available: {names}")
                
                app_seq = wf.get("app_sequence", "[]")
                if isinstance(app_seq, str):
                    try:
                        app_seq = json.loads(app_seq)
                    except:
                        app_seq = []
                        
                first_app = app_seq[0] if app_seq else ""
                
                cursor.execute("SELECT count(*) as c FROM sessions WHERE tenant_id=? AND primary_app=?", (tenant_id, first_app))
                obs_count = cursor.fetchone()["c"]
                data_observations = obs_count
                
                freq = wf.get("frequency_per_week", 0)
                dur = wf.get("avg_duration_seconds", 0)
                weekly_hours = freq * dur / 3600
                auto_potential = wf.get("automation_potential", 0)
                
                before_state = {
                    "weekly_hours": round(weekly_hours, 2),
                    "annual_hours": round(weekly_hours * 52, 2),
                    "automation_potential": auto_potential,
                    "observation_count": obs_count
                }
                
                if scenario.direction == "eliminate":
                    hours_saved_per_week = weekly_hours
                else:
                    hours_saved_per_week = weekly_hours * (scenario.change_percent / 100)
                    
                remaining_hours = weekly_hours - hours_saved_per_week
                
                after_state = {
                    "remaining_hours": round(remaining_hours, 2),
                    "hours_saved_per_week": round(hours_saved_per_week, 2)
                }
                
                base_delta = hours_saved_per_week * 0.6
                adjusted_delta = base_delta * auto_potential
                health_score_after = min(health_score_before + adjusted_delta, 100.0)
                
                cursor.execute("SELECT name, app_sequence FROM workflows WHERE tenant_id=? AND id != ?", (tenant_id, wf["id"]))
                other_wfs = cursor.fetchall()
                for owf in other_wfs:
                    other_seq = owf.get("app_sequence", "[]")
                    if isinstance(other_seq, str):
                        try:
                            other_seq = json.loads(other_seq)
                        except:
                            other_seq = []
                    if any(app in other_seq for app in app_seq):
                        affected_workflows.append(owf["name"])
                        
                if obs_count > 20 and auto_potential > 0.7:
                    confidence = "high"
                    confidence_rationale = "Strong pattern repetition and high automation potential score."
                elif obs_count > 5 and auto_potential > 0.4:
                    confidence = "medium"
                    confidence_rationale = "Moderate pattern repetition observed."
                else:
                    confidence = "low"
                    confidence_rationale = "Infrequent observation or low automation potential."

            elif scenario.scenario_type == "reduce_meetings":
                meeting_apps = ["zoom", "teams", "meet", "calendar", "outlook", "google meet", "webex", "skype"]
                
                cursor.execute("SELECT * FROM workflows WHERE tenant_id=?", (tenant_id,))
                all_wfs = cursor.fetchall()
                
                meeting_wfs = []
                total_all_hrs = 0.0
                
                for wf in all_wfs:
                    freq = wf.get("frequency_per_week", 0)
                    dur = wf.get("avg_duration_seconds", 0)
                    hrs = freq * dur / 3600
                    total_all_hrs += hrs
                    
                    app_seq = wf.get("app_sequence", "[]")
                    if isinstance(app_seq, str):
                        try:
                            app_seq = json.loads(app_seq)
                        except:
                            app_seq = []
                    
                    is_meeting = any(any(m in a.lower() for m in meeting_apps) for a in app_seq)
                    if is_meeting:
                        if not scenario.target or (scenario.target and scenario.target.lower() in str(wf.get("description", "")).lower() or scenario.target.lower() in wf.get("name", "").lower()):
                            meeting_wfs.append((wf, hrs))
                
                total_meeting_wfs = len(meeting_wfs)
                total_weekly_meeting_hours = sum(h for _, h in meeting_wfs)
                meeting_percentage = (total_weekly_meeting_hours / total_all_hrs) if total_all_hrs > 0 else 0
                data_observations = total_meeting_wfs
                
                before_state = {
                    "total_meeting_workflows": total_meeting_wfs,
                    "total_weekly_meeting_hours": round(total_weekly_meeting_hours, 2),
                    "meeting_percentage": round(meeting_percentage * 100, 1)
                }
                
                hours_saved_per_week = total_weekly_meeting_hours * (scenario.change_percent / 100)
                after_state = {
                    "remaining_meeting_hours": round(total_weekly_meeting_hours - hours_saved_per_week, 2),
                    "hours_saved_per_week": round(hours_saved_per_week, 2)
                }
                
                health_delta = hours_saved_per_week * 0.4
                health_score_after = min(health_score_before + health_delta, 100.0)
                
                affected_workflows = [wf["name"] for wf, _ in meeting_wfs]
                
                if total_meeting_wfs >= 3:
                    confidence = "high"
                    confidence_rationale = "Multiple meeting workflows detected consistently."
                elif total_meeting_wfs >= 1:
                    confidence = "medium"
                    confidence_rationale = "Some meeting workflows detected."
                else:
                    confidence = "low"
                    confidence_rationale = "No specific meeting workflows matched."

            elif scenario.scenario_type == "add_headcount":
                cursor.execute("SELECT * FROM workflows WHERE tenant_id=?", (tenant_id,))
                all_wfs = cursor.fetchall()
                target_wfs = []
                for wf in all_wfs:
                    if not scenario.target or (scenario.target.lower() in str(wf.get("description", "")).lower() or scenario.target.lower() in wf.get("name", "").lower()):
                        target_wfs.append(wf)
                        
                total_weekly_hours = sum(w.get("frequency_per_week", 0) * w.get("avg_duration_seconds", 0) / 3600 for w in target_wfs)
                
                cursor.execute("SELECT count(DISTINCT primary_app) as c FROM sessions WHERE tenant_id=? AND started_at >= strftime('%s','now','-30 days')", (tenant_id,))
                distinct_apps = cursor.fetchone()["c"]
                est_headcount = max(1, distinct_apps // 3) # Very rough proxy
                if est_headcount < 1: est_headcount = 1
                
                data_observations = len(target_wfs)
                load_per_person = total_weekly_hours / est_headcount if est_headcount > 0 else 0
                
                before_state = {
                    "total_weekly_hours": round(total_weekly_hours, 2),
                    "estimated_headcount": est_headcount,
                    "load_per_person": round(load_per_person, 2),
                    "overload_signal": load_per_person > 40
                }
                
                new_headcount = est_headcount * (1 + scenario.change_percent / 100)
                new_load_per_person = total_weekly_hours / new_headcount if new_headcount > 0 else 0
                hours_saved_per_week = (load_per_person - new_load_per_person) * est_headcount
                
                after_state = {
                    "new_headcount": round(new_headcount, 1),
                    "new_load_per_person": round(new_load_per_person, 2),
                    "load_reduction_per_person": round(load_per_person - new_load_per_person, 2)
                }
                
                load_reduction_percent = ((load_per_person - new_load_per_person) / load_per_person * 100) if load_per_person > 0 else 0
                health_delta = (load_reduction_percent / 100) * 15
                health_score_after = min(health_score_before + health_delta, 100.0)
                
                confidence = "medium"
                confidence_rationale = "Headcount estimation is approximate based on distinct behavioral patterns."

            elif scenario.scenario_type == "remove_bottleneck":
                from platform_core.intelligence.graph import get_graph_data
                graph = get_graph_data(tenant_id)
                nodes = graph.get("nodes", [])
                
                if scenario.target:
                    target_node = next((n for n in nodes if n["label"].lower() == scenario.target.lower()), None)
                    if not target_node:
                        raise SimulationError(f"No node found matching '{scenario.target}' in graph.")
                else:
                    target_node = graph.get("most_connected")
                    if not target_node:
                        raise SimulationError("No bottleneck node could be identified automatically.")
                        
                bottleneck_name = target_node["label"]
                conn_count = target_node.get("connections", 0)
                max_conns = max([n.get("connections", 0) for n in nodes]) if nodes else 1
                if max_conns == 0: max_conns = 1
                
                cursor.execute("SELECT * FROM workflows WHERE tenant_id=?", (tenant_id,))
                all_wfs = cursor.fetchall()
                dep_wfs = []
                for wf in all_wfs:
                    app_seq = wf.get("app_sequence", "[]")
                    if isinstance(app_seq, str):
                        try:
                            app_seq = json.loads(app_seq)
                        except:
                            app_seq = []
                    if any(bottleneck_name.lower() in a.lower() for a in app_seq):
                        dep_wfs.append(wf)
                        
                total_dep_hours = sum(w.get("frequency_per_week", 0) * w.get("avg_duration_seconds", 0) / 3600 for w in dep_wfs)
                data_observations = len(nodes)
                
                before_state = {
                    "bottleneck_node": bottleneck_name,
                    "connection_count": conn_count,
                    "dependent_workflows": [w["name"] for w in dep_wfs],
                    "total_dependent_hours": round(total_dep_hours, 2)
                }
                
                if scenario.direction == "eliminate":
                    hours_saved_per_week = total_dep_hours * 0.30
                else:
                    hours_saved_per_week = total_dep_hours * (scenario.change_percent / 100) * 0.20
                    
                after_state = {
                    "hours_saved_per_week": round(hours_saved_per_week, 2),
                    "remaining_dependent_hours": round(total_dep_hours - hours_saved_per_week, 2)
                }
                
                health_delta = (conn_count / max_conns) * 25
                health_score_after = min(health_score_before + health_delta, 100.0)
                affected_workflows = [w["name"] for w in dep_wfs]
                
                if len(nodes) > 10 and conn_count > 3:
                    confidence = "high"
                    confidence_rationale = "Graph is well-populated and node is clearly a central hub."
                elif len(nodes) >= 5:
                    confidence = "medium"
                    confidence_rationale = "Graph has moderate population."
                else:
                    confidence = "low"
                    confidence_rationale = "Graph has very few nodes, relationships may not be fully observed."

            else:
                raise SimulationError(f"Unknown scenario type: {scenario.scenario_type}")
                
            delta = {
                "hours_saved_per_week": round(hours_saved_per_week, 2),
                "health_score_change": round(health_score_after - health_score_before, 2)
            }
            
            prompt = f"""
System: You are an operations consultant analyzing the projected impact of an organizational change. Be specific, use the numbers provided, and think about second-order effects. Do not give generic change management advice. Respond ONLY as JSON with no preamble.

User: Simulation: {scenario.scenario_type} on '{scenario.target}', {scenario.direction} by {scenario.change_percent}%.
Context provided: {scenario.context if scenario.context else 'None'}

Before: {json.dumps(before_state)}
After: {json.dumps(after_state)}
Delta: {json.dumps(delta)}
Confidence: {confidence} — {confidence_rationale}
Based on {data_observations} observed data points.

Return JSON:
{{
  "narrative": "2-3 sentence explanation of what this change means operationally. Use the specific numbers. Mention what the data quality means for certainty of this projection.",
  "risks": ["risk 1", "risk 2", "risk 3"],
  "opportunities": ["opportunity 1", "opportunity 2"]
}}
"""
            llm_text = self._call_claude(prompt)
            try:
                # Basic json extraction if model includes markdown
                if "```json" in llm_text:
                    llm_text = llm_text.split("```json")[1].split("```")[0].strip()
                elif "```" in llm_text:
                    llm_text = llm_text.split("```")[1].split("```")[0].strip()
                llm_res = json.loads(llm_text)
                narrative = llm_res.get("narrative", llm_text)
                risks = llm_res.get("risks", [])[:3]
                opportunities = llm_res.get("opportunities", [])[:2]
            except Exception:
                narrative = llm_text
                risks = []
                opportunities = []
                
        except SimulationError as se:
            raise se
        except Exception as e:
            # Fallback
            narrative = f"Simulation math completed but narrative failed: {e}"
            risks = []
            opportunities = []
        finally:
            conn.close()

        res = SimulationResult(
            id=str(uuid.uuid4()),
            scenario=scenario,
            before_state=before_state,
            after_state=after_state,
            delta=delta,
            narrative=narrative,
            risks=risks,
            opportunities=opportunities,
            confidence=confidence,
            confidence_rationale=confidence_rationale,
            affected_workflows=affected_workflows,
            hours_saved_per_week=round(hours_saved_per_week, 2),
            monthly_value_hours=round(hours_saved_per_week * 4.33, 2),
            health_score_before=round(health_score_before, 2),
            health_score_after=round(health_score_after, 2),
            data_observations=data_observations,
            created_at=int(time.time())
        )
        return res
