import re

filepath = r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

process_mining_ui = """
                <!-- WORKFLOWS TAB / PROCESS MINING STUDIO -->
                <div id="tab-workflows" class="tab-content" style="padding: 0; display: flex; height: 100%;">
                    <!-- Left Sidebar Filters -->
                    <div style="width: 280px; border-right: 1px solid var(--border); background: var(--bg-card); padding: 20px; overflow-y: auto;">
                        <h2 style="font-size: 16px; margin-bottom: 24px; color: var(--accent);">Process Mining Studio</h2>
                        
                        <h3 class="text-muted" style="font-size: 12px; margin-bottom: 8px;">DATA CONNECTIONS</h3>
                        <select style="width: 100%; padding: 8px; background: var(--bg-primary); color: white; border: 1px solid var(--border); border-radius: 4px; margin-bottom: 16px;">
                            <option>All Systems (Live)</option>
                            <option>SAP ERP (Production)</option>
                            <option>Salesforce CRM</option>
                            <option>Jira Service Desk</option>
                        </select>

                        <h3 class="text-muted" style="font-size: 12px; margin-bottom: 8px;">PROCESS VARIANT</h3>
                        <select style="width: 100%; padding: 8px; background: var(--bg-primary); color: white; border: 1px solid var(--border); border-radius: 4px; margin-bottom: 16px;">
                            <option>Happy Path (72% of cases)</option>
                            <option>Deviation A (14% of cases)</option>
                            <option>Deviation B (8% of cases)</option>
                        </select>

                        <h3 class="text-muted" style="font-size: 12px; margin-bottom: 8px;">DATE RANGE</h3>
                        <input type="date" style="width: 100%; padding: 8px; background: var(--bg-primary); color: white; border: 1px solid var(--border); border-radius: 4px; margin-bottom: 24px;" value="2026-06-01">

                        <button class="btn btn-primary" style="width: 100%; margin-bottom: 24px;">Run Deep Analysis</button>

                        <h3 class="text-muted" style="font-size: 12px; margin-bottom: 8px;">BOTTLENECK INSIGHTS</h3>
                        <div style="background: var(--bg-primary); border: 1px solid var(--accent-red); padding: 12px; border-radius: 6px; font-size: 12px;">
                            <strong style="color: var(--accent-red);">Critical Friction Detected</strong><br>
                            Approval step taking 48hrs longer than SLA. Root cause: Missing vendor PO data in SAP.
                        </div>
                    </div>
                    
                    <!-- Main Graph Area -->
                    <div style="flex: 1; padding: 24px; background: var(--bg-primary); position: relative; overflow: hidden; display: flex; flex-direction: column;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <div>
                                <h1 style="margin: 0; font-size: 20px;">Procure-to-Pay Process Graph</h1>
                                <span class="text-muted" style="font-size: 12px;">Analyzed 142,000 events in real-time.</span>
                            </div>
                            <div>
                                <button class="btn btn-ghost btn-sm">Export Graph</button>
                                <button class="btn btn-primary btn-sm">Build Action Flow</button>
                            </div>
                        </div>

                        <!-- FAKE PROCESS GRAPH -->
                        <div style="flex: 1; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; position: relative; display: flex; align-items: center; justify-content: center; background-image: radial-gradient(var(--border) 1px, transparent 1px); background-size: 20px 20px;">
                            <!-- Node 1 -->
                            <div style="position: absolute; top: 10%; left: 40%; background: var(--bg-card); border: 2px solid var(--accent); padding: 12px 24px; border-radius: 8px; text-align: center;">
                                <div style="font-weight: bold;">Create Purchase Requisition</div>
                                <div style="font-size: 10px; color: var(--text-muted);">SAP GUI • 12,400 cases</div>
                            </div>
                            <!-- Edge -->
                            <div style="position: absolute; top: 20%; left: 45%; width: 2px; height: 100px; background: var(--accent-yellow);">
                                <div style="position: absolute; top: 40%; left: 10px; font-size: 10px; color: var(--accent-yellow); white-space: nowrap;">Avg. 2.4 days ⚠️</div>
                            </div>
                            <!-- Node 2 -->
                            <div style="position: absolute; top: 35%; left: 40%; background: var(--bg-card); border: 2px solid var(--accent); padding: 12px 24px; border-radius: 8px; text-align: center;">
                                <div style="font-weight: bold;">Manager Approval</div>
                                <div style="font-size: 10px; color: var(--text-muted);">Outlook / Teams • 12,000 cases</div>
                            </div>
                            <!-- Edge Split -->
                            <div style="position: absolute; top: 45%; left: 45%; width: 2px; height: 100px; background: var(--accent-green);">
                                <div style="position: absolute; top: 40%; left: 10px; font-size: 10px; color: var(--accent-green); white-space: nowrap;">Approved (80%)</div>
                            </div>
                            <div style="position: absolute; top: 45%; left: 55%; width: 2px; height: 100px; background: var(--accent-red); transform: rotate(-45deg); transform-origin: top left;">
                                <div style="position: absolute; top: 40%; left: 10px; font-size: 10px; color: var(--accent-red); white-space: nowrap;">Rejected (20%)</div>
                            </div>
                            <!-- Node 3 -->
                            <div style="position: absolute; top: 60%; left: 40%; background: var(--bg-card); border: 2px solid var(--accent); padding: 12px 24px; border-radius: 8px; text-align: center;">
                                <div style="font-weight: bold;">Generate PO</div>
                                <div style="font-size: 10px; color: var(--text-muted);">NetSuite • 9,600 cases</div>
                            </div>
                        </div>
                    </div>
                </div>
"""

custom_canvas_ui = """
        <!-- DASHBOARDS TAB / CUSTOM CANVAS -->
        <div id="dashboards" class="tab-content" style="padding: 0; display: flex; height: 100%;">
            <!-- Left Sidebar -->
            <div style="width: 250px; border-right: 1px solid var(--border); background: var(--bg-card); padding: 20px;">
                <h2 style="font-size: 16px; margin-bottom: 24px; color: var(--accent);">Canvas Elements</h2>
                
                <h3 class="text-muted" style="font-size: 12px; margin-bottom: 8px;">VISUALIZATIONS</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 24px;">
                    <div style="border: 1px dashed var(--border); padding: 12px; text-align: center; border-radius: 4px; cursor: grab;">📊<br><span style="font-size:10px;">Bar Chart</span></div>
                    <div style="border: 1px dashed var(--border); padding: 12px; text-align: center; border-radius: 4px; cursor: grab;">📈<br><span style="font-size:10px;">Line Graph</span></div>
                    <div style="border: 1px dashed var(--border); padding: 12px; text-align: center; border-radius: 4px; cursor: grab;">🍩<br><span style="font-size:10px;">Donut</span></div>
                    <div style="border: 1px dashed var(--border); padding: 12px; text-align: center; border-radius: 4px; cursor: grab;">🔢<br><span style="font-size:10px;">KPI Card</span></div>
                </div>

                <h3 class="text-muted" style="font-size: 12px; margin-bottom: 8px;">AUTONOMY LOGIC</h3>
                <div style="border: 1px dashed var(--accent-purple); padding: 12px; text-align: center; border-radius: 4px; margin-bottom: 8px; cursor: grab; color: var(--accent-purple);">
                    ⚡ Action Button
                </div>
                <div style="border: 1px dashed var(--accent-green); padding: 12px; text-align: center; border-radius: 4px; margin-bottom: 8px; cursor: grab; color: var(--accent-green);">
                    🔄 Data Sync Trigger
                </div>
                <div style="border: 1px dashed var(--accent-yellow); padding: 12px; text-align: center; border-radius: 4px; margin-bottom: 24px; cursor: grab; color: var(--accent-yellow);">
                    🧠 AI Prompt Block
                </div>

                <button class="btn btn-primary" style="width: 100%;">Save Dashboard</button>
            </div>

            <!-- Canvas Workspace -->
            <div style="flex: 1; padding: 24px; background: var(--bg-primary); overflow-y: auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                    <h1 style="margin: 0; font-size: 24px;" contenteditable="true">Executive Performance Overview ✏️</h1>
                    <button class="btn btn-ghost btn-sm">Share Dashboard</button>
                </div>

                <!-- Canvas Grid -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
                    <!-- KPI Card -->
                    <div class="card" style="position: relative; padding: 20px;">
                        <div style="position: absolute; top: 8px; right: 8px; color: var(--text-muted); cursor: pointer;">⚙️</div>
                        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">Total Active Automations</div>
                        <div style="font-size: 28px; font-weight: bold; color: var(--accent);">142</div>
                        <div style="font-size: 12px; color: var(--accent-green); margin-top: 8px;">↑ 12% vs last month</div>
                    </div>
                    <!-- KPI Card -->
                    <div class="card" style="position: relative; padding: 20px;">
                        <div style="position: absolute; top: 8px; right: 8px; color: var(--text-muted); cursor: pointer;">⚙️</div>
                        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">Hours Saved (YTD)</div>
                        <div style="font-size: 28px; font-weight: bold; color: var(--accent);">4,200</div>
                        <div style="font-size: 12px; color: var(--accent-green); margin-top: 8px;">↑ 34% vs last month</div>
                    </div>
                    <!-- AI Insight Block -->
                    <div class="card" style="grid-column: span 2; position: relative; padding: 20px; border-color: var(--accent-purple);">
                        <div style="position: absolute; top: 8px; right: 8px; color: var(--text-muted); cursor: pointer;">⚙️</div>
                        <div style="font-size: 12px; color: var(--accent-purple); margin-bottom: 8px; font-weight: bold;">🧠 AI Simulation Insight</div>
                        <div style="font-size: 14px; line-height: 1.5;">If we deploy the "Invoice Parsing" automation to the EMEA team, predictive models show a potential <strong style="color:var(--accent-green);">14% cycle time reduction</strong> across the entire Q3 period.</div>
                        <button class="btn btn-primary btn-sm" style="margin-top: 12px; background: var(--accent-purple); border:none;">Deploy Now</button>
                    </div>
                </div>

                <!-- Custom Table -->
                <div class="card" style="position: relative; padding: 20px; height: 300px;">
                    <div style="position: absolute; top: 8px; right: 8px; color: var(--text-muted); cursor: pointer;">⚙️</div>
                    <div style="font-size: 16px; font-weight: bold; margin-bottom: 16px;">Cross-Department Data Aggregation</div>
                    <table style="width: 100%; text-align: left; border-collapse: collapse; font-size: 14px;">
                        <tr style="border-bottom: 1px solid var(--border); color: var(--text-muted);">
                            <th style="padding: 8px 0;">Department</th>
                            <th>Active Agents</th>
                            <th>Critical Bottlenecks</th>
                            <th>Data Sources</th>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 12px 0;">Finance</td>
                            <td>45</td>
                            <td style="color: var(--accent-red);">Invoice Approval</td>
                            <td>SAP, Outlook</td>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 12px 0;">HR</td>
                            <td>12</td>
                            <td style="color: var(--accent-yellow);">Onboarding</td>
                            <td>Workday, Slack</td>
                        </tr>
                    </table>
                </div>

            </div>
        </div>
"""

workflows_regex = r'<!-- WORKFLOWS TAB -->.*?<!-- AUTOMATIONS TAB -->'
html = re.sub(workflows_regex, process_mining_ui + '\n                <!-- AUTOMATIONS TAB -->', html, flags=re.DOTALL)

dashboards_regex = r'<!-- DASHBOARDS TAB -->.*?<!-- ENTERPRISE TAB -->'
html = re.sub(dashboards_regex, custom_canvas_ui + '\n        <!-- ENTERPRISE TAB -->', html, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(html)
