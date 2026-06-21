import re
import sqlite3

class ComplianceMonitor:
    """
    Monitors OCR text streams for Data Loss Prevention (DLP)
    and Shadow IT usage.
    """
    def __init__(self):
        # Regex for sensitive data (SSN, API Keys, etc.)
        self.sensitive_patterns = {
            "Social Security Number": r"\b\d{3}-\d{2}-\d{4}\b",
            "Credit Card": r"\b(?:\d{4}[ -]?){3}\d{4}\b",
            "AWS Access Key": r"\bAKIA[0-9A-Z]{16}\b",
            "Generic API Key": r"(?i)(api[_-]?key|secret|token)[\s:=]+([a-zA-Z0-9_\-]{20,})"
        }
        
        # Domains or App Titles that are flagged
        self.unapproved_apps = ["chatgpt", "claude", "personal email", "whatsapp"]

    def analyze_frame(self, window_title, ocr_text):
        """
        Analyzes a single screenshot frame's data for violations.
        Returns a list of violations (if any).
        """
        violations = []
        text = ocr_text if ocr_text else ""
        title = window_title.lower() if window_title else ""
        
        # 1. Shadow IT Check
        for app in self.unapproved_apps:
            if app in title:
                violations.append(f"Shadow IT Alert: Unauthorized application '{app}' in use.")
                
        # 2. DLP Check
        for name, pattern in self.sensitive_patterns.items():
            if re.search(pattern, text):
                violations.append(f"DLP Alert: Potential {name} exposed on screen.")
                
        return violations

def test_monitor():
    monitor = ComplianceMonitor()
    
    # Test DLP
    ocr = "Here is my key: AKIA1234567890ABCDEF do not share it."
    title = "Notepad"
    print("Testing DLP:")
    print(monitor.analyze_frame(title, ocr))
    
    # Test Shadow IT
    ocr2 = "Drafting quarterly earnings."
    title2 = "ChatGPT - Google Chrome"
    print("\nTesting Shadow IT:")
    print(monitor.analyze_frame(title2, ocr2))

if __name__ == "__main__":
    test_monitor()
