import re

with open(r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove remaining emojis
html = html.replace('⚡', '')
html = html.replace('🔄', '')
html = html.replace('🤖', '')
html = html.replace('⚙️', '')

# We need to inject the Enterprise tab button into the sidebar.
# The sidebar looks like:
# <div id="sidebar"> ... <button class="tab-btn" onclick="switchTab('today')" ... </button>
# Let's find the last button in the sidebar (which is Settings) and insert our Enterprise button before it.
btn_html = '''
        <button class="tab-btn" onclick="switchTab('enterprise')" id="nav-enterprise">
            <div class="tab-icon">🏢</div>
            <div style="font-size:10px;">Enterprise</div>
        </button>
'''
# Wait, I promised NO emojis. So I'll use text.
btn_html = '''
        <button class="tab-btn" onclick="switchTab('enterprise')" id="nav-enterprise">
            <div style="font-size:14px; margin-bottom:4px; font-weight:bold;">ENT</div>
            <div style="font-size:10px;">Enterprise</div>
        </button>
'''
# Let's replace the other icons with text so they don't look broken
html = html.replace('<div class="tab-icon"></div>\n            <div style="font-size:10px;">Overview</div>', '<div style="font-size:14px; margin-bottom:4px; font-weight:bold;">OVW</div>\n            <div style="font-size:10px;">Overview</div>')
html = html.replace('<div class="tab-icon"></div>\n            <div style="font-size:10px;">Intelligence</div>', '<div style="font-size:14px; margin-bottom:4px; font-weight:bold;">INT</div>\n            <div style="font-size:10px;">Intelligence</div>')
html = html.replace('<div class="tab-icon"></div>\n            <div style="font-size:10px;">Ask Xenia</div>', '<div style="font-size:14px; margin-bottom:4px; font-weight:bold;">ASK</div>\n            <div style="font-size:10px;">Ask Xenia</div>')
html = html.replace('<div class="tab-icon"></div>\n            <div style="font-size:10px;">Settings</div>', '<div style="font-size:14px; margin-bottom:4px; font-weight:bold;">SET</div>\n            <div style="font-size:10px;">Settings</div>')

# In case they were already matched or had the `?` due to powershell
html = re.sub(r'<div class=\"tab-icon\">.*?</div>', '<div style="font-size:14px; margin-bottom:4px; font-weight:bold;">*</div>', html)

if 'switchTab(\'enterprise\')' not in html:
    # Insert enterprise button before the settings button
    # Find settings button
    parts = html.split('<button class="tab-btn" onclick="document.getElementById(\'settings-btn\').click()"')
    if len(parts) == 2:
        html = parts[0] + btn_html + '\n        <button class="tab-btn" onclick="document.getElementById(\'settings-btn\').click()"' + parts[1]

# Inject Enterprise View Layer if it's not already there
enterprise_layer = '''
        <!-- Enterprise Layer -->
        <div id="tab-enterprise" class="view-layer" style="display:none; padding:24px; overflow-y:auto;">
            <div style="margin-bottom: 24px;">
                <h2 style="margin-bottom: 8px;">Enterprise Features</h2>
                <div class="text-muted">Advanced business intelligence and shadow automation.</div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
                <div class="card" style="padding:16px; background:var(--bg-card); border-radius:8px;">
                    <div style="font-weight:bold; margin-bottom: 8px;">SOP Generator</div>
                    <div class="text-muted" style="margin-bottom: 12px; font-size:13px;">Automatically drafts an SOP document from recorded workflows.</div>
                    <button class="btn btn-primary" style="background:var(--accent); color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer;" onclick="generateSOP()">Generate SOP</button>
                    <div id="sop-result" style="margin-top:16px; font-family:monospace; font-size:12px; max-height:150px; overflow-y:auto; background:var(--bg-primary); padding:8px; border-radius:4px; display:none;"></div>
                </div>

                <div class="card" style="padding:16px; background:var(--bg-card); border-radius:8px;">
                    <div style="font-weight:bold; margin-bottom: 8px;">Shadow Automator</div>
                    <div class="text-muted" style="margin-bottom: 12px; font-size:13px;">Generates RPA Python scripts for repetitive tasks.</div>
                    <button class="btn btn-primary" style="background:var(--accent); color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer;" onclick="runShadowAuto()">Generate Script</button>
                    <div id="shadow-result" style="margin-top:16px; font-family:monospace; font-size:12px; max-height:150px; overflow-y:auto; background:var(--bg-primary); padding:8px; border-radius:4px; display:none;"></div>
                </div>

                <div class="card" style="padding:16px; background:var(--bg-card); border-radius:8px;">
                    <div style="font-weight:bold; margin-bottom: 8px;">Simulation Engine</div>
                    <div class="text-muted" style="margin-bottom: 12px; font-size:13px;">Run business shock simulations.</div>
                    <button class="btn" style="background:var(--border); color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer;" onclick="runSimulation()">Run Shock</button>
                    <div id="sim-result" style="margin-top:16px; font-family:monospace; font-size:12px; max-height:150px; overflow-y:auto; background:var(--bg-primary); padding:8px; border-radius:4px; display:none;"></div>
                </div>

                <div class="card" style="padding:16px; background:var(--bg-card); border-radius:8px;">
                    <div style="font-weight:bold; margin-bottom: 8px;">Compliance Scanner</div>
                    <div class="text-muted" style="margin-bottom: 12px; font-size:13px;">Scan operational logs for DLP violations.</div>
                    <button class="btn" style="background:var(--border); color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer;" onclick="runCompliance()">Scan Logs</button>
                    <div id="compliance-result" style="margin-top:16px; font-family:monospace; font-size:12px; max-height:150px; overflow-y:auto; background:var(--bg-primary); padding:8px; border-radius:4px; display:none;"></div>
                </div>
            </div>
        </div>
'''

if 'id="tab-enterprise"' not in html:
    parts = html.split('<!-- Settings Modal -->')
    if len(parts) == 2:
        html = parts[0] + enterprise_layer + '\n<!-- Settings Modal -->' + parts[1]

# Add enterprise switchTab handling
if "else if (tab === 'enterprise')" not in html:
    html = html.replace("else if (tab === 'me') await loadMeProfile();", "else if (tab === 'me') await loadMeProfile();\n            else if (tab === 'enterprise') { /* nothing to load initially */ }")

with open(r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
