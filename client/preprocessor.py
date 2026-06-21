from . import db
from collections import defaultdict, Counter

def build_analysis_context(days=7) -> dict:
    sessions = db.get_sessions(days=days)
    
    total_sessions = len(sessions)
    total_work_time_seconds = 0
    app_usage_seconds = defaultdict(float)
    
    longest_sessions = []
    
    sequence_counter = Counter()
    sequence_data = defaultdict(lambda: {"total_duration": 0, "session_count": 0})
    
    for session in sessions:
        if not session.get('ended_at'):
            continue
            
        duration = session['ended_at'] - session['started_at']
        total_work_time_seconds += duration
        
        longest_sessions.append({
            "session_id": session['id'],
            "primary_app": session.get('primary_app', 'Unknown'),
            "duration_minutes": round(duration / 60, 2)
        })
        
        events = db.get_events_for_session(session['id'])
        
        app_sequence = []
        last_app = None
        last_event_time = session['started_at']
        
        for event in events:
            event_duration = event['timestamp'] - last_event_time
            if last_app:
                app_usage_seconds[last_app] += event_duration
                
            last_event_time = event['timestamp']
            
            current_app = event.get('app_name')
            if current_app and current_app != last_app:
                app_sequence.append(current_app)
                last_app = current_app
                
        if last_app:
             app_usage_seconds[last_app] += session['ended_at'] - last_event_time
             
        if app_sequence:
            seq_tuple = tuple(app_sequence)
            sequence_counter[seq_tuple] += 1
            sequence_data[seq_tuple]["total_duration"] += duration
            sequence_data[seq_tuple]["session_count"] += 1

    total_work_hours = round(total_work_time_seconds / 3600, 2)
    
    app_usage_minutes = {
        app: round(time_sec / 60, 2)
        for app, time_sec in sorted(app_usage_seconds.items(), key=lambda item: item[1], reverse=True)
    }
    
    most_used_apps = list(app_usage_minutes.keys())[:5]
    
    longest_sessions.sort(key=lambda x: x['duration_minutes'], reverse=True)
    top_longest_sessions = longest_sessions[:3]
    
    detected_patterns = []
    for seq_tuple, count in sequence_counter.most_common(10):
        data = sequence_data[seq_tuple]
        detected_patterns.append({
            "app_sequence": list(seq_tuple),
            "session_count": count,
            "avg_duration_minutes": round((data["total_duration"] / count) / 60, 2),
            "total_time_minutes": round(data["total_duration"] / 60, 2)
        })
        
    return {
        "total_sessions": total_sessions,
        "total_work_hours": total_work_hours,
        "app_usage_minutes": app_usage_minutes,
        "detected_patterns": detected_patterns,
        "most_used_apps": most_used_apps,
        "longest_sessions": top_longest_sessions
    }
