import re
import os

filepath = r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace emojis using regex for anything in tab-icon
html = re.sub(r'<span class="tab-icon">.*?</span>\s*<span class="tab-label">Today</span>', '<span class="tab-icon" style="font-size:12px;font-weight:bold;">OVW</span>\n            <span class="tab-label">Today</span>', html, flags=re.DOTALL)
html = re.sub(r'<span class="tab-icon">.*?</span>\s*<span class="tab-label">Workflows</span>', '<span class="tab-icon" style="font-size:12px;font-weight:bold;">WRK</span>\n            <span class="tab-label">Workflows</span>', html, flags=re.DOTALL)
html = re.sub(r'<span class="tab-icon">.*?</span>\s*<span class="tab-label">Automations</span>', '<span class="tab-icon" style="font-size:12px;font-weight:bold;">AUT</span>\n            <span class="tab-label">Automations</span>', html, flags=re.DOTALL)
html = re.sub(r'<span class="tab-icon">.*?</span>\s*<span class="tab-label">Approvals</span>', '<span class="tab-icon" style="font-size:12px;font-weight:bold;">APP</span>\n            <span class="tab-label">Approvals</span>', html, flags=re.DOTALL)
html = re.sub(r'<span class="tab-icon">.*?</span>\s*<span class="tab-label">Ask</span>', '<span class="tab-icon" style="font-size:12px;font-weight:bold;">ASK</span>\n            <span class="tab-label">Ask</span>', html, flags=re.DOTALL)
html = re.sub(r'<span class="tab-icon">.*?</span>\s*<span class="tab-label">Insights</span>', '<span class="tab-icon" style="font-size:12px;font-weight:bold;">INS</span>\n            <span class="tab-label">Insights</span>', html, flags=re.DOTALL)
html = re.sub(r'<span class="tab-icon">.*?</span>\s*<span class="tab-label">Me</span>', '<span class="tab-icon" style="font-size:12px;font-weight:bold;">PRO</span>\n            <span class="tab-label">Me</span>', html, flags=re.DOTALL)
html = re.sub(r'<span class="tab-icon">.*?</span>\s*<span class="tab-label">Company</span>', '<span class="tab-icon" style="font-size:12px;font-weight:bold;">ORG</span>\n            <span class="tab-label">Company</span>', html, flags=re.DOTALL)
html = re.sub(r'<span class="tab-icon">.*?</span>\s*<span class="tab-label">Dashboards</span>', '<span class="tab-icon" style="font-size:12px;font-weight:bold;">DSH</span>\n            <span class="tab-label">Dashboards</span>', html, flags=re.DOTALL)

# Add Enterprise to sidebar if missing
if 'data-tab="enterprise"' not in html:
    html = html.replace('</div>\n\n    <!-- Main Wrapper -->', '''        <button class="tab-btn" data-tab="enterprise">
            <span class="tab-icon" style="font-size:12px;font-weight:bold;">ENT</span>
            <span class="tab-label">Enterprise</span>
        </button>
    </div>

    <!-- Main Wrapper -->''')

# Inject enterprise layer if missing
enterprise_layer = '''
        <!-- ENTERPRISE TAB -->
        <div id="tab-enterprise" class="tab-content" style="padding: 24px;">
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
    html = html.replace('<!-- Modals -->', enterprise_layer + '\n    <!-- Modals -->')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(html)

print("Done injecting fix3.py")
