import re

PATTERNS = {
    'EMAIL': r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
    'CARD': r'\b(?:\d[ -]*?){13,19}\b',
    'API_KEY': r'\b(?:sk-|pk-|ghp_|xoxb-|Bearer )[a-zA-Z0-9_\-]+\b',
    'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
    'PASSWORD': r'(?i)(?:password:\s*|pwd=)(\S+)'
}

def sanitize(text: str) -> str:
    if not text:
        return text
        
    sanitized = text
    sanitized = re.sub(PATTERNS['EMAIL'], '[REDACTED_EMAIL]', sanitized)
    sanitized = re.sub(PATTERNS['SSN'], '[REDACTED_SSN]', sanitized)
    sanitized = re.sub(PATTERNS['API_KEY'], '[REDACTED_API_KEY]', sanitized)
    
    def pass_replacer(match):
        return match.group(0).replace(match.group(1), '[REDACTED_PASSWORD]')
    sanitized = re.sub(PATTERNS['PASSWORD'], pass_replacer, sanitized)
    
    def card_replacer(match):
        digits = re.sub(r'[^0-9]', '', match.group(0))
        if 13 <= len(digits) <= 19:
            return '[REDACTED_CARD]'
        return match.group(0)
    sanitized = re.sub(PATTERNS['CARD'], card_replacer, sanitized)
    
    return sanitized

def is_sensitive(text: str) -> bool:
    if not text:
        return False
        
    for key, pattern in PATTERNS.items():
        if key == 'CARD':
            matches = re.finditer(pattern, text)
            for m in matches:
                digits = re.sub(r'[^0-9]', '', m.group(0))
                if 13 <= len(digits) <= 19:
                    return True
        else:
            if re.search(pattern, text):
                return True
                
    return False
