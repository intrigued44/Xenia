def calculate_automation_potential(app_sequence: list[str]) -> float:
    seq_lower = [str(app).lower() for app in app_sequence]
    
    # Check for two or more target apps
    target_apps = {"excel", "chrome", "firefox", "edge", "opera"}
    match_count = sum(1 for app in seq_lower if any(t in app for t in target_apps))
    if match_count >= 2:
        return 0.9
        
    # Check for billing apps
    billing_apps = {"tally", "marg", "busy", "quickbooks", "zoho"}
    if any(any(b in app for b in billing_apps) for app in seq_lower):
        return 0.85
        
    # Check for file utilities
    file_utils = {"file explorer", "winrar", "7-zip"}
    if any(any(f in app for f in file_utils) for app in seq_lower):
        return 0.7
        
    # Check sequence length
    if len(app_sequence) == 1:
        return 0.2
    if len(app_sequence) >= 5:
        return 0.8
        
    return 0.5

class PatternClassifier:
    def classify_all_patterns(self, patterns: list[dict]) -> list[dict]:
        results = []
        for pattern in patterns:
            rep_score = min(pattern.get("session_count", 0) / 10.0, 1.0)
            time_score = min(pattern.get("total_time_minutes", 0) / 120.0, 1.0)
            auto_potential = calculate_automation_potential(pattern.get("app_sequence", []))
            
            overall = (rep_score * 0.3) + (time_score * 0.4) + (auto_potential * 0.3)
            
            action = "IGNORE"
            if overall >= 0.7:
                action = "AUTOMATE"
            elif overall >= 0.4:
                action = "DOCUMENT"
            elif overall >= 0.2:
                action = "MONITOR"
                
            if action != "IGNORE":
                results.append({
                    "app_sequence": pattern.get("app_sequence"),
                    "repetition_score": round(rep_score, 2),
                    "time_cost_score": round(time_score, 2),
                    "automation_potential": round(auto_potential, 2),
                    "overall_score": round(overall, 2),
                    "recommended_action": action
                })
            
        return sorted(results, key=lambda x: x["overall_score"], reverse=True)

def classify_all_patterns(patterns: list[dict]) -> list[dict]:
    return PatternClassifier().classify_all_patterns(patterns)
