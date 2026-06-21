import re

with open(r'C:\Users\pranav\Downloads\nous-temp-extract\ui\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace Nous -> Xenia
html = html.replace('Nous', 'Xenia').replace('nous', 'xenia')

# Radix theme replacements
html = html.replace('--bg-primary: #0f172a;', '--bg-primary: #0f0f11;')
html = html.replace('--bg-secondary: #1e293b;', '--bg-secondary: #1a1a1e;')
html = html.replace('--bg-card: #1e293b;', '--bg-card: #26262b;')
html = html.replace('--border: #334155;', '--border: #2a2a30;')
html = html.replace('--accent: #3b82f6;', '--accent: #5e6ad2;')

# Remove Emojis
html = re.sub(r'👁️|💬|📊|🧠|👤|⚙️|📈|🔮|✅|🛡️|🏢|👥|⚠️', '', html)

# Inject Enterprise Tab button
btn_html = '''
        <button class="tab-btn" onclick="switchTab('enterprise')" id="nav-enterprise">
            <div style="font-size:18px; margin-bottom:4px;"></div>
            <div style="font-size:10px;">Enterprise</div>
        </button>
'''
html = html.replace('<!-- nav buttons -->', '<!-- nav buttons -->' + btn_html)
html = html.replace('</button>\n        </div>\n\n        <button class="tab-btn"', '</button>\n' + btn_html + '\n        </div>\n\n        <button class="tab-btn"')

# Inject Enterprise View Layer
enterprise_layer = '''
        <!-- Enterprise Layer -->
        <div id="tab-enterprise" class="view-layer">
            <div style="margin-bottom: 24px;">
                <h2 style="margin-bottom: 8px;">Enterprise Features</h2>
                <div class="text-muted">Advanced business intelligence and shadow automation.</div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
                <div class="card">
                    <div style="font-weight:bold; margin-bottom: 8px;">SOP Generator</div>
                    <div class="text-muted" style="margin-bottom: 12px; font-size:13px;">Automatically drafts an SOP document from recorded workflows.</div>
                    <button class="btn btn-primary" onclick="generateSOP()">Generate SOP</button>
                    <div id="sop-result" style="margin-top:16px; font-family:monospace; font-size:12px; max-height:150px; overflow-y:auto; background:var(--bg-primary); padding:8px; border-radius:4px; display:none;"></div>
                </div>

                <div class="card">
                    <div style="font-weight:bold; margin-bottom: 8px;">Shadow Automator</div>
                    <div class="text-muted" style="margin-bottom: 12px; font-size:13px;">Generates RPA Python scripts for repetitive tasks.</div>
                    <button class="btn btn-primary" onclick="runShadowAuto()">Generate Script</button>
                    <div id="shadow-result" style="margin-top:16px; font-family:monospace; font-size:12px; max-height:150px; overflow-y:auto; background:var(--bg-primary); padding:8px; border-radius:4px; display:none;"></div>
                </div>

                <div class="card">
                    <div style="font-weight:bold; margin-bottom: 8px;">Simulation Engine</div>
                    <div class="text-muted" style="margin-bottom: 12px; font-size:13px;">Run business shock simulations.</div>
                    <button class="btn" onclick="runSimulation()">Run Shock</button>
                    <div id="sim-result" style="margin-top:16px; font-family:monospace; font-size:12px; max-height:150px; overflow-y:auto; background:var(--bg-primary); padding:8px; border-radius:4px; display:none;"></div>
                </div>

                <div class="card">
                    <div style="font-weight:bold; margin-bottom: 8px;">Compliance Scanner</div>
                    <div class="text-muted" style="margin-bottom: 12px; font-size:13px;">Scan operational logs for DLP violations.</div>
                    <button class="btn" onclick="runCompliance()">Scan Logs</button>
                    <div id="compliance-result" style="margin-top:16px; font-family:monospace; font-size:12px; max-height:150px; overflow-y:auto; background:var(--bg-primary); padding:8px; border-radius:4px; display:none;"></div>
                </div>
            </div>
        </div>
'''

html = html.replace('<!-- View Layers -->', '<!-- View Layers -->' + enterprise_layer)

# Inject JS for Enterprise logic
enterprise_js = '''
    // Enterprise logic
    async function generateSOP() {
        const out = document.getElementById('sop-result');
        out.style.display = 'block'; out.innerText = 'Generating...';
        const res = await fetchAPI('/v1/enterprise/sop/generate', {method: 'POST', body: JSON.stringify({})});
        out.innerText = res ? res.sop : 'Error';
    }
    async function runShadowAuto() {
        const out = document.getElementById('shadow-result');
        out.style.display = 'block'; out.innerText = 'Generating script...';
        const res = await fetchAPI('/v1/enterprise/shadow-auto', {method: 'POST', body: JSON.stringify({})});
        out.innerText = res ? res.script : 'Error';
    }
    async function runSimulation() {
        const out = document.getElementById('sim-result');
        out.style.display = 'block'; out.innerText = 'Simulating...';
        const res = await fetchAPI('/v1/enterprise/simulate', {method: 'POST', body: JSON.stringify({})});
        out.innerText = res ? JSON.stringify(res.results, null, 2) : 'Error';
    }
    async function runCompliance() {
        const out = document.getElementById('compliance-result');
        out.style.display = 'block'; out.innerText = 'Scanning...';
        const res = await fetchAPI('/v1/enterprise/compliance');
        out.innerText = res ? JSON.stringify(res.violations, null, 2) : 'Error';
    }
'''

html = html.replace('// --- Settings Modal ---', enterprise_js + '\n        // --- Settings Modal ---')

# More Radix styling improvements (font, etc)
html = html.replace('<style>', '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">\n    <style>')
html = html.replace('font-family: system-ui, -apple-system, sans-serif;', 'font-family: "Inter", sans-serif;')

# Remove font-size:24px wrapper from icons since we removed emojis to prevent huge empty blocks
html = html.replace('font-size: 24px;', 'font-size: 14px; margin-bottom: 2px;')

with open(r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
