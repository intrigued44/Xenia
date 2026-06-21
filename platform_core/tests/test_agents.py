import pytest
from platform_core.intelligence.classifier import PatternClassifier

def test_classifier_scores_patterns():
    classifier = PatternClassifier()
    patterns = [
        {"app_sequence": ["Excel", "Chrome"], "session_count": 10, "total_time_minutes": 120},
        {"app_sequence": ["Notepad", "Word"], "session_count": 2, "total_time_minutes": 50}
    ]
    
    results = classifier.classify_all_patterns(patterns)
    assert len(results) == 2
    
    # Excel + Web should score high
    high_score = next(r for r in results if r["app_sequence"] == ["Excel", "Chrome"])
    assert high_score["automation_potential"] == 0.9
    assert high_score["recommended_action"] in ["AUTOMATE", "DOCUMENT"]
    
    # Notepad + Word should score lower but not be ignored
    low_score = next(r for r in results if r["app_sequence"] == ["Notepad", "Word"])
    assert low_score["automation_potential"] == 0.5
    assert low_score["overall_score"] < high_score["overall_score"]
