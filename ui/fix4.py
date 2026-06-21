import re

filepath = r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Unhide labels so user can read what each tab does
html = html.replace('width: 60px;', 'width: 140px;')
old_css = '''.tab-label {
            font-size: 10px;
            display: none; /* Icon-only in sidebar as requested */
        }'''
new_css = '''.tab-label {
            font-size: 11px;
            font-weight: 500;
            margin-top: 4px;
        }'''
if old_css in html:
    html = html.replace(old_css, new_css)
else:
    # Just aggressively remove display:none from tab-label if the formatting was slightly different
    html = re.sub(r'\.tab-label\s*\{[^}]*display:\s*none;[^}]*\}', new_css, html)

# 2. Rename the tabs exactly to match what they represent
html = html.replace('<span class="tab-label">Ask</span>', '<span class="tab-label">Chat</span>')
html = html.replace('<span class="tab-label">Dashboards</span>', '<span class="tab-label">Dashboard Creator</span>')
html = html.replace('<span class="tab-label">Me</span>', '<span class="tab-label">Profile</span>')
html = html.replace('<span class="tab-label">Company</span>', '<span class="tab-label">Org Intel</span>')

# 3. Add Vault System tab linking to graph.html
vault_tab = '''
        <button class="tab-btn" onclick="window.location.href='graph.html'">
            <span class="tab-icon">🛡️</span>
            <span class="tab-label">Vault System</span>
        </button>
'''
if 'Vault System' not in html:
    html = html.replace('<button class="tab-btn" data-tab="company">', vault_tab + '        <button class="tab-btn" data-tab="company">')

# 4. Bring back emojis because text looks bad with display labels anyway.
html = re.sub(r'<span class="tab-icon"[^>]*>OVW</span>', '<span class="tab-icon">📊</span>', html)
html = re.sub(r'<span class="tab-icon"[^>]*>WRK</span>', '<span class="tab-icon">⚡</span>', html)
html = re.sub(r'<span class="tab-icon"[^>]*>AUT</span>', '<span class="tab-icon">🤖</span>', html)
html = re.sub(r'<span class="tab-icon"[^>]*>APP</span>', '<span class="tab-icon">✅</span>', html)
html = re.sub(r'<span class="tab-icon"[^>]*>ASK</span>', '<span class="tab-icon">💬</span>', html)
html = re.sub(r'<span class="tab-icon"[^>]*>INS</span>', '<span class="tab-icon">💡</span>', html)
html = re.sub(r'<span class="tab-icon"[^>]*>PRO</span>', '<span class="tab-icon">👤</span>', html)
html = re.sub(r'<span class="tab-icon"[^>]*>ORG</span>', '<span class="tab-icon">🏢</span>', html)
html = re.sub(r'<span class="tab-icon"[^>]*>DSH</span>', '<span class="tab-icon">📈</span>', html)
html = re.sub(r'<span class="tab-icon"[^>]*>ENT</span>', '<span class="tab-icon">⚙️</span>', html)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(html)
