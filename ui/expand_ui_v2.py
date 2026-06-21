import re

filepath = r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

# ==========================================
# 1. PROCESS MINING STUDIO (Replaces tab-workflows)
# ==========================================
process_mining_ui = """
                <!-- WORKFLOWS TAB / PROCESS MINING STUDIO -->
                <div id="tab-workflows" class="tab-content" style="padding: 0; display: flex; height: 100%; flex-direction: column;">
                    
                    <!-- Top Status Bar (Process Health Score) -->
                    <div style="padding: 20px 24px; border-bottom: 1px solid var(--border); background: var(--bg-secondary); display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <div class="text-muted" style="font-size: 11px; letter-spacing: 1px; margin-bottom: 4px;">PROCESS HEALTH SCORE</div>
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="font-size: 28px; font-weight: bold; color: var(--text-primary);">78/100</div>
                                <div style="color: var(--accent-green); font-size: 12px; display: flex; align-items: center;">▲ +4 pts this month</div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 24px;">
                            <div class="card" style="margin: 0; padding: 12px 20px; background: var(--bg-card); border-color: var(--border);">
                                <div class="text-muted" style="font-size: 11px;">Conformance</div>
                                <div style="font-size: 16px; font-weight: bold;">82%</div>
                            </div>
                            <div class="card" style="margin: 0; padding: 12px 20px; background: var(--bg-card); border-color: var(--border);">
                                <div class="text-muted" style="font-size: 11px;">Throughput</div>
                                <div style="font-size: 16px; font-weight: bold;">4.2d avg</div>
                            </div>
                            <div class="card" style="margin: 0; padding: 12px 20px; background: var(--bg-card); border-color: var(--border);">
                                <div class="text-muted" style="font-size: 11px;">Rework Rate</div>
                                <div style="font-size: 16px; font-weight: bold; color: var(--accent-red);">12%</div>
                            </div>
                        </div>
                    </div>

                    <div style="flex: 1; display: flex; overflow: hidden;">
                        
                        <!-- Left Sidebar: Variants & Bottlenecks -->
                        <div style="width: 320px; border-right: 1px solid var(--border); background: var(--bg-card); padding: 0; display: flex; flex-direction: column; overflow-y: auto;">
                            
                            <!-- Variant Explorer -->
                            <div style="padding: 20px; border-bottom: 1px solid var(--border);">
                                <h3 class="text-muted" style="font-size: 12px; margin-bottom: 16px;">PROCESS VARIANTS</h3>
                                
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 13px; font-weight: bold; color: var(--accent);">● Happy Path</span>
                                    <span style="font-size: 13px;">67%</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: var(--bg-primary); border-radius: 3px; margin-bottom: 16px;"><div style="width: 67%; height: 100%; background: var(--accent); border-radius: 3px;"></div></div>

                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 13px; color: var(--text-primary);">○ Variant B</span>
                                    <span style="font-size: 13px;">18%</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: var(--bg-primary); border-radius: 3px; margin-bottom: 16px;"><div style="width: 18%; height: 100%; background: var(--text-muted); border-radius: 3px;"></div></div>

                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 13px; color: var(--text-primary);">○ Variant C</span>
                                    <span style="font-size: 13px;">9%</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: var(--bg-primary); border-radius: 3px; margin-bottom: 16px;"><div style="width: 9%; height: 100%; background: var(--text-muted); border-radius: 3px;"></div></div>

                                <button class="btn btn-ghost btn-sm" style="width: 100%;">Explore All Variants</button>
                            </div>

                            <!-- Friction Heatmap -->
                            <div style="padding: 20px; border-bottom: 1px solid var(--border);">
                                <h3 class="text-muted" style="font-size: 12px; margin-bottom: 16px;">FRICTION HEATMAP</h3>
                                <table style="width: 100%; text-align: left; font-size: 12px; border-collapse: collapse;">
                                    <tr style="color: var(--text-muted); border-bottom: 1px solid var(--border);">
                                        <th style="padding-bottom: 8px;">Step</th>
                                        <th style="padding-bottom: 8px;">Wait</th>
                                        <th style="padding-bottom: 8px;">Impact</th>
                                    </tr>
                                    <tr style="border-bottom: 1px solid var(--border);">
                                        <td style="padding: 8px 0; color: var(--accent-red);">🔴 Invoice Appr.</td>
                                        <td>3.2d</td>
                                        <td>$89k</td>
                                    </tr>
                                    <tr style="border-bottom: 1px solid var(--border);">
                                        <td style="padding: 8px 0; color: var(--accent-yellow);">🟠 PO Creation</td>
                                        <td>1.1d</td>
                                        <td>$31k</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: var(--accent-green);">🟢 Payment Run</td>
                                        <td>0.2d</td>
                                        <td>$4k</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Root Cause ML -->
                            <div style="padding: 20px; flex: 1;">
                                <h3 class="text-muted" style="font-size: 12px; margin-bottom: 12px;">🧠 ROOT CAUSE ANALYZER</h3>
                                <p style="font-size: 12px; color: var(--text-primary); margin-bottom: 12px;">
                                    "Why are 23% of invoices taking > 5 days?"
                                </p>
                                <div style="background: var(--bg-primary); border: 1px solid var(--border); padding: 12px; border-radius: 6px; font-size: 11px; line-height: 1.5; color: var(--text-muted); margin-bottom: 12px;">
                                    <strong style="color: var(--accent);">ML INSIGHT:</strong> 51% of delayed invoices are missing a PO number. Concentrated in 3 vendors (Acme, TechParts, Global Supply) onboarded before March 2023.
                                </div>
                                <button class="btn btn-primary btn-sm" style="width: 100%;">Draft Vendor Email Fix</button>
                            </div>

                        </div>

                        <!-- Main Live Map -->
                        <div style="flex: 1; padding: 24px; background: var(--bg-primary); display: flex; flex-direction: column; position: relative;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                                <div>
                                    <h1 style="margin: 0; font-size: 20px;">Live Process Map</h1>
                                    <span class="text-muted" style="font-size: 12px;">Comparing: Happy Path vs. Variant B</span>
                                </div>
                                <div style="display: flex; gap: 8px;">
                                    <select class="btn btn-ghost btn-sm" style="outline: none;">
                                        <option>Department: All</option>
                                    </select>
                                    <select class="btn btn-ghost btn-sm" style="outline: none;">
                                        <option>Time Period: Q3</option>
                                    </select>
                                </div>
                            </div>

                            <div style="flex: 1; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; position: relative; overflow: auto; padding: 40px;">
                                
                                <!-- Diagram Path 1 -->
                                <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">HAPPY PATH (67% of cases) • AVG: 1.8 days</div>
                                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 40px;">
                                    <div style="padding: 12px 24px; border: 2px solid var(--accent); border-radius: 6px; background: var(--bg-card); font-size: 13px;">[Receive]</div>
                                    <div style="flex: 1; height: 2px; background: var(--text-muted); position: relative;"><div style="position: absolute; top: -18px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--text-muted);">2h</div></div>
                                    <div style="padding: 12px 24px; border: 2px solid var(--accent); border-radius: 6px; background: var(--bg-card); font-size: 13px;">[Validate]</div>
                                    <div style="flex: 1; height: 2px; background: var(--text-muted); position: relative;"><div style="position: absolute; top: -18px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--text-muted);">4h</div></div>
                                    <div style="padding: 12px 24px; border: 2px solid var(--accent); border-radius: 6px; background: var(--bg-card); font-size: 13px;">[Approve]</div>
                                    <div style="flex: 1; height: 2px; background: var(--text-muted); position: relative;"><div style="position: absolute; top: -18px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--text-muted);">6h</div></div>
                                    <div style="padding: 12px 24px; border: 2px solid var(--accent); border-radius: 6px; background: var(--bg-card); font-size: 13px;">[Ship]</div>
                                </div>

                                <!-- Diagram Path 2 -->
                                <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">VARIANT B (18% of cases) • AVG: 7.4 days</div>
                                <div style="display: flex; align-items: center; gap: 16px;">
                                    <div style="padding: 12px 24px; border: 2px solid var(--text-muted); border-radius: 6px; background: var(--bg-card); font-size: 13px;">[Receive]</div>
                                    <div style="width: 60px; height: 2px; background: var(--text-muted); position: relative;"><div style="position: absolute; top: -18px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--text-muted);">2h</div></div>
                                    <div style="padding: 12px 24px; border: 2px solid var(--text-muted); border-radius: 6px; background: var(--bg-card); font-size: 13px;">[Validate]</div>
                                    <div style="width: 60px; height: 2px; background: var(--text-muted); position: relative;"><div style="position: absolute; top: -18px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--text-muted);">2h</div></div>
                                    <div style="padding: 12px 24px; border: 2px solid var(--accent-red); border-radius: 6px; background: var(--bg-card); font-size: 13px; color: var(--accent-red);">[REJECTED]</div>
                                    
                                    <div style="width: 60px; height: 2px; background: var(--accent-red); position: relative;"><div style="position: absolute; top: -18px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--accent-red);">12h</div></div>
                                    <div style="padding: 12px 24px; border: 2px dashed var(--accent-yellow); border-radius: 6px; background: var(--bg-card); font-size: 13px;">[Manual Review]</div>
                                    
                                    <div style="width: 60px; height: 2px; background: var(--accent-yellow); position: relative;"><div style="position: absolute; top: -18px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--accent-yellow);">3d</div></div>
                                    <div style="padding: 12px 24px; border: 2px solid var(--text-muted); border-radius: 6px; background: var(--bg-card); font-size: 13px;">[Ship]</div>
                                </div>
                                
                                <div style="position: absolute; bottom: 20px; right: 20px; background: var(--bg-card); border: 1px solid var(--accent-red); padding: 16px; border-radius: 8px;">
                                    <div style="font-size: 12px; color: var(--text-muted);">TIME LOST TO VARIANT B THIS QUARTER</div>
                                    <div style="font-size: 20px; font-weight: bold; color: var(--text-primary); margin: 4px 0;">2,847 hours • $142,350 cost</div>
                                    <div style="display: flex; gap: 8px; margin-top: 12px;">
                                        <button class="btn btn-primary btn-sm" style="background: var(--accent-red);">Fix Automatically</button>
                                        <button class="btn btn-ghost btn-sm">Set Alert</button>
                                    </div>
                                </div>

                            </div>
                        </div>
                    </div>
                </div>
"""

# ==========================================
# 2. CUSTOM CANVAS (Replaces dashboards)
# ==========================================
custom_canvas_ui = """
        <!-- DASHBOARDS TAB / CUSTOM CANVAS -->
        <div id="dashboards" class="tab-content" style="padding: 0; display: flex; height: 100%;">
            <!-- Left Sidebar -->
            <div style="width: 280px; border-right: 1px solid var(--border); background: var(--bg-card); display: flex; flex-direction: column;">
                <div style="padding: 20px; border-bottom: 1px solid var(--border);">
                    <h2 style="font-size: 16px; color: var(--accent);">Xenia Canvas</h2>
                </div>
                <div style="padding: 20px; overflow-y: auto; flex: 1;">
                    <h3 class="text-muted" style="font-size: 12px; margin-bottom: 12px;">MY APPS</h3>
                    <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 24px;">
                        <div class="card" style="padding: 12px; margin: 0; cursor: pointer; border-color: var(--accent);">
                            <div style="font-weight: bold; font-size: 14px;">📊 CFO Dashboard</div>
                            <div class="text-muted" style="font-size: 10px; margin-top: 4px;">Built by: You • Last edit: Today</div>
                        </div>
                        <div class="card" style="padding: 12px; margin: 0; cursor: pointer;">
                            <div style="font-weight: bold; font-size: 14px;">⚡ AP Tracker</div>
                            <div class="text-muted" style="font-size: 10px; margin-top: 4px;">Built by: Team • Last edit: 3d</div>
                        </div>
                        <div class="card" style="padding: 12px; margin: 0; cursor: pointer; border-style: dashed; text-align: center; color: var(--text-muted);">
                            ＋ Create New
                        </div>
                    </div>

                    <h3 class="text-muted" style="font-size: 12px; margin-bottom: 12px;">BUILD WITH AI</h3>
                    <div class="card" style="padding: 12px; margin: 0; border-color: var(--accent-purple);">
                        <textarea style="width: 100%; height: 60px; background: transparent; border: none; color: white; resize: none; outline: none; font-family: inherit; font-size: 12px;" placeholder='"Build me a dashboard that shows invoice cycle time by vendor..."'></textarea>
                        <div style="display: flex; justify-content: flex-end;">
                            <button class="btn btn-primary btn-sm" style="background: var(--accent-purple); border-radius: 4px; padding: 4px 12px;">▶</button>
                        </div>
                    </div>
                </div>
                <div style="padding: 20px; border-top: 1px solid var(--border);">
                    <button class="btn btn-primary" style="width: 100%;" onclick="alert('Opening KPI Builder...')">Open Custom KPI Engine</button>
                </div>
            </div>

            <!-- Canvas Workspace -->
            <div style="flex: 1; padding: 32px; background: var(--bg-primary); overflow-y: auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;">
                    <h1 style="margin: 0; font-size: 28px;" contenteditable="true">CFO Dashboard ✏️</h1>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-ghost">Preview</button>
                        <button class="btn btn-primary">Share</button>
                    </div>
                </div>

                <!-- Canvas Grid -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px;">
                    <!-- KPI Card -->
                    <div class="card" style="position: relative; padding: 24px; margin: 0;">
                        <div style="position: absolute; top: 12px; right: 12px; color: var(--text-muted); cursor: pointer;">⚙️</div>
                        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">Total Active Automations</div>
                        <div style="font-size: 32px; font-weight: bold; color: var(--accent);">142</div>
                        <div style="font-size: 12px; color: var(--accent-green); margin-top: 8px;">↑ 12% vs last month</div>
                    </div>
                    <!-- KPI Card -->
                    <div class="card" style="position: relative; padding: 24px; margin: 0;">
                        <div style="position: absolute; top: 12px; right: 12px; color: var(--text-muted); cursor: pointer;">⚙️</div>
                        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 8px;">Avg Cycle Time</div>
                        <div style="font-size: 32px; font-weight: bold; color: var(--text-primary);">4.2 days</div>
                        <div style="font-size: 12px; color: var(--accent-red); margin-top: 8px;">↓ 2% vs last month</div>
                    </div>
                    <!-- AI Insight Block -->
                    <div class="card" style="grid-column: span 2; position: relative; padding: 24px; border-color: var(--accent-purple); margin: 0; background: rgba(139, 92, 246, 0.05);">
                        <div style="position: absolute; top: 12px; right: 12px; color: var(--text-muted); cursor: pointer;">⚙️</div>
                        <div style="font-size: 12px; color: var(--accent-purple); margin-bottom: 12px; font-weight: bold;">🧠 AI Simulation Insight</div>
                        <div style="font-size: 15px; line-height: 1.5; color: var(--text-primary);">If we deploy the "Invoice Parsing" automation to the EMEA team, predictive models show a potential <strong style="color:var(--accent-green);">14% cycle time reduction</strong> across the entire Q3 period.</div>
                        <button class="btn btn-primary btn-sm" style="margin-top: 16px; background: var(--accent-purple); border:none;">Deploy Automation Now</button>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                    <!-- Line Chart Placeholder -->
                    <div class="card" style="position: relative; padding: 24px; height: 350px; margin: 0; display: flex; flex-direction: column;">
                        <div style="position: absolute; top: 12px; right: 12px; color: var(--text-muted); cursor: pointer;">⚙️</div>
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">Cycle Time Trend (90 days)</div>
                        <div style="flex: 1; border: 1px dashed var(--border); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); margin-top: 16px;">
                            [ Line Chart Canvas Rendering ]
                        </div>
                    </div>
                    <!-- Embedded Process Map -->
                    <div class="card" style="position: relative; padding: 24px; height: 350px; margin: 0; display: flex; flex-direction: column;">
                        <div style="position: absolute; top: 12px; right: 12px; color: var(--text-muted); cursor: pointer;">⚙️</div>
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">Live Process Map Embed</div>
                        <div style="flex: 1; border: 1px solid var(--border); background: var(--bg-secondary); border-radius: 8px; margin-top: 16px; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden;">
                             <div style="padding: 8px 16px; border: 1px solid var(--accent); border-radius: 4px; background: var(--bg-card); font-size: 11px;">[Mini Map View]</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
"""

# ==========================================
# 3. DEEP ENTERPRISE CONNECTORS (Replaces company)
# ==========================================
enterprise_connectors_ui = """
        <!-- COMPANY TAB / DEEP ENTERPRISE CONNECTORS -->
        <div id="company" class="tab-content" style="padding: 0; display: flex; height: 100%;">
            <div style="width: 250px; border-right: 1px solid var(--border); background: var(--bg-card); padding: 20px;">
                <h2 style="font-size: 16px; margin-bottom: 24px; color: var(--accent);">Connector Hub</h2>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <button class="btn btn-ghost" style="text-align: left; background: var(--bg-primary);">🔌 Connected Systems</button>
                    <button class="btn btn-ghost" style="text-align: left;">♊ Digital Twin Builder</button>
                    <button class="btn btn-ghost" style="text-align: left;">🔄 Data Transformations</button>
                </div>
            </div>
            <div style="flex: 1; padding: 32px; background: var(--bg-primary); overflow-y: auto;">
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;">
                    <h1 style="margin: 0; font-size: 24px;">Digital Twin Data Fusion</h1>
                    <button class="btn btn-primary">+ Add Connector</button>
                </div>

                <div class="card" style="padding: 24px; margin-bottom: 24px;">
                    <h3 style="font-size: 16px; margin-bottom: 16px;">DATA SOURCES FUSED INTO TWIN: "Procure-to-Pay"</h3>
                    <div style="display: flex; flex-direction: column; gap: 12px; font-size: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 8px;">
                            <div><span style="color:var(--accent-green);">✅</span> <strong>Xenia Screen Events</strong> <span class="text-muted">(UI actions, clicks)</span></div>
                            <div class="text-muted" style="font-size: 12px;">1.4M events</div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 8px;">
                            <div><span style="color:var(--accent-green);">✅</span> <strong>SAP: MM Module</strong> <span class="text-muted">(PO creation)</span></div>
                            <div class="text-muted" style="font-size: 12px;">847k events</div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 8px;">
                            <div><span style="color:var(--accent-green);">✅</span> <strong>Email (Outlook)</strong> <span class="text-muted">(Vendor threads)</span></div>
                            <div class="text-muted" style="font-size: 12px;">189k events</div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px;">
                            <div><span style="color:var(--text-muted);">❌</span> <strong style="color:var(--text-muted);">Coupa</strong> <span class="text-muted">(Not connected)</span></div>
                            <button class="btn btn-ghost btn-sm">Add Now</button>
                        </div>
                    </div>
                </div>

                <div class="card" style="padding: 24px; border-color: var(--accent);">
                    <h3 style="font-size: 16px; margin-bottom: 16px;">TWIN ALIGNMENT VISUALIZATION</h3>
                    <table style="width: 100%; text-align: left; font-size: 14px; border-collapse: collapse;">
                        <tr style="color: var(--text-muted); border-bottom: 1px solid var(--border);">
                            <th style="padding-bottom: 12px; width: 25%;">DIGITAL RECORD</th>
                            <th style="padding-bottom: 12px; width: 25%;">PHYSICAL REALITY</th>
                            <th style="padding-bottom: 12px; width: 50%;">MATCH SCORE</th>
                        </tr>
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 16px 0;">PO Created in SAP</td>
                            <td style="padding: 16px 0;">Screen: PO form filled</td>
                            <td style="padding: 16px 0;">
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <div style="flex:1; height:8px; background:var(--bg-secondary); border-radius:4px;"><div style="width:94%; height:100%; background:var(--accent-green); border-radius:4px;"></div></div>
                                    <span style="font-weight:bold;">94%</span>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 16px 0;">Invoice Approved</td>
                            <td style="padding: 16px 0;">Screen: Email approval</td>
                            <td style="padding: 16px 0;">
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <div style="flex:1; height:8px; background:var(--bg-secondary); border-radius:4px;"><div style="width:72%; height:100%; background:var(--accent-yellow); border-radius:4px;"></div></div>
                                    <span style="font-weight:bold;">72%</span>
                                </div>
                            </td>
                        </tr>
                    </table>
                    <div style="margin-top: 16px; padding: 16px; background: rgba(245, 158, 11, 0.1); border-left: 3px solid var(--accent-yellow); font-size: 13px;">
                        <strong style="color: var(--accent-yellow);">GAP INSIGHT:</strong> 28% of approvals happen via email, not SAP. This means no audit trail and higher compliance risk.
                        <div style="margin-top: 8px;"><button class="btn btn-primary btn-sm" style="background: var(--accent-yellow); color: black;">Build Enforcement Rule</button></div>
                    </div>
                </div>

            </div>
        </div>
"""

# ==========================================
# 4. ACTION FLOWS (Replaces tab-enterprise)
# ==========================================
action_flows_ui = """
        <!-- ENTERPRISE TAB / ACTION FLOWS -->
        <div id="tab-enterprise" class="tab-content" style="padding: 0; display: flex; height: 100%;">
            <!-- Node Library -->
            <div style="width: 250px; border-right: 1px solid var(--border); background: var(--bg-card); padding: 20px; overflow-y: auto;">
                <h2 style="font-size: 16px; margin-bottom: 24px; color: var(--accent);">Node Library</h2>
                
                <h3 class="text-muted" style="font-size: 11px; margin-bottom: 8px;">🟣 TRIGGERS</h3>
                <div style="display:flex; flex-direction:column; gap:6px; margin-bottom: 20px;">
                    <div style="padding:8px 12px; border:1px solid var(--border); border-radius:4px; font-size:12px; cursor:grab;">Xenia Event</div>
                    <div style="padding:8px 12px; border:1px solid var(--border); border-radius:4px; font-size:12px; cursor:grab;">Schedule</div>
                    <div style="padding:8px 12px; border:1px solid var(--border); border-radius:4px; font-size:12px; cursor:grab;">SAP Event</div>
                </div>

                <h3 class="text-muted" style="font-size: 11px; margin-bottom: 8px;">🔵 LOGIC</h3>
                <div style="display:flex; flex-direction:column; gap:6px; margin-bottom: 20px;">
                    <div style="padding:8px 12px; border:1px solid var(--border); border-radius:4px; font-size:12px; cursor:grab;">IF / ELSE</div>
                    <div style="padding:8px 12px; border:1px solid var(--border); border-radius:4px; font-size:12px; cursor:grab;">Loop</div>
                </div>

                <h3 class="text-muted" style="font-size: 11px; margin-bottom: 8px;">🟢 ACTIONS</h3>
                <div style="display:flex; flex-direction:column; gap:6px; margin-bottom: 20px;">
                    <div style="padding:8px 12px; border:1px solid var(--border); border-radius:4px; font-size:12px; cursor:grab;">Send Slack</div>
                    <div style="padding:8px 12px; border:1px solid var(--border); border-radius:4px; font-size:12px; cursor:grab;">Update SAP</div>
                    <div style="padding:8px 12px; border:1px solid var(--border); border-radius:4px; font-size:12px; cursor:grab;">Run Script</div>
                </div>

                <h3 class="text-muted" style="font-size: 11px; margin-bottom: 8px;">🟡 HUMAN IN THE LOOP</h3>
                <div style="display:flex; flex-direction:column; gap:6px; margin-bottom: 20px;">
                    <div style="padding:8px 12px; border:1px dashed var(--accent-yellow); color: var(--accent-yellow); border-radius:4px; font-size:12px; cursor:grab;">Approval</div>
                    <div style="padding:8px 12px; border:1px dashed var(--accent-yellow); color: var(--accent-yellow); border-radius:4px; font-size:12px; cursor:grab;">Input Form</div>
                </div>
            </div>

            <!-- Flow Canvas Workspace -->
            <div style="flex: 1; padding: 24px; background: var(--bg-primary); position: relative; overflow: hidden;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h1 style="margin: 0; font-size: 20px;">Action Flow: "Invoice Escalation"</h1>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn btn-ghost btn-sm">Test Run ▶</button>
                        <button class="btn btn-primary btn-sm">Publish Flow</button>
                    </div>
                </div>

                <!-- Mock Canvas Grid -->
                <div style="position: absolute; top: 70px; left: 24px; right: 24px; bottom: 24px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; background-image: radial-gradient(var(--border) 1px, transparent 1px); background-size: 20px 20px; display: flex; align-items: center; justify-content: center; flex-direction: column;">
                    
                    <!-- Nodes -->
                    <div style="padding: 12px 24px; background: var(--bg-card); border-top: 3px solid #a855f7; border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; width: 200px;">
                        <div style="font-size: 10px; color: #a855f7; font-weight: bold; margin-bottom: 4px;">🟣 TRIGGER</div>
                        <div style="font-size: 13px;">Invoice pending > 24hrs</div>
                    </div>

                    <div style="width: 2px; height: 30px; background: var(--text-muted);"></div>

                    <div style="padding: 12px 24px; background: var(--bg-card); border-top: 3px solid #3b82f6; border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; width: 200px;">
                        <div style="font-size: 10px; color: #3b82f6; font-weight: bold; margin-bottom: 4px;">🔵 CHECK LOGIC</div>
                        <div style="font-size: 13px;">Amount > $10k?</div>
                    </div>

                    <div style="display: flex; width: 300px; justify-content: space-between;">
                        <div style="width: 2px; height: 30px; background: var(--text-muted); margin-left: 50px;"></div>
                        <div style="width: 2px; height: 30px; background: var(--text-muted); margin-right: 50px;"></div>
                    </div>

                    <div style="display: flex; width: 400px; justify-content: space-between; align-items: flex-start;">
                        <div style="padding: 12px 24px; background: var(--bg-card); border-top: 3px solid var(--accent-yellow); border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; width: 160px; cursor: pointer;">
                            <div style="font-size: 10px; color: var(--accent-yellow); font-weight: bold; margin-bottom: 4px;">🟡 HUMAN LOOP</div>
                            <div style="font-size: 13px;">CFO Approval</div>
                        </div>
                        <div style="padding: 12px 24px; background: var(--bg-card); border-top: 3px solid var(--accent-green); border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center; width: 160px;">
                            <div style="font-size: 10px; color: var(--accent-green); font-weight: bold; margin-bottom: 4px;">🟢 ACTION</div>
                            <div style="font-size: 13px;">Slack #AP-team</div>
                        </div>
                    </div>

                </div>

                <!-- Floating Human-in-Loop Config Panel Mock -->
                <div style="position: absolute; top: 100px; right: 40px; width: 320px; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 10; display: flex; flex-direction: column;">
                    <div style="padding: 12px 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: var(--bg-card); border-radius: 8px 8px 0 0;">
                        <div style="font-size: 13px; font-weight: bold;">Human Approval Config</div>
                        <div style="cursor: pointer; color: var(--text-muted);">✕</div>
                    </div>
                    <div style="padding: 16px; flex: 1; overflow-y: auto;">
                        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">SEND TO</div>
                        <select style="width: 100%; padding: 8px; background: var(--bg-secondary); color: white; border: 1px solid var(--border); border-radius: 4px; margin-bottom: 16px;">
                            <option>Sarah Chen - CFO</option>
                        </select>
                        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">VIA CHANNEL</div>
                        <div style="display: flex; gap: 8px; margin-bottom: 16px;">
                            <button class="btn btn-primary btn-sm" style="flex:1;">Slack</button>
                            <button class="btn btn-ghost btn-sm" style="flex:1;">Email</button>
                        </div>
                        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">MESSAGE TEMPLATE</div>
                        <textarea style="width: 100%; height: 100px; background: var(--bg-secondary); color: var(--text-muted); border: 1px solid var(--border); border-radius: 4px; padding: 8px; font-family: monospace; font-size: 11px; resize: none; margin-bottom: 16px;">Hi {{approver.first_name}},\n\nInvoice #{{invoice.id}} from {{vendor.name}} requires your approval.\nAmount: {{invoice.amount}}</textarea>
                        
                        <div style="padding: 12px; background: rgba(16, 185, 129, 0.1); border-left: 2px solid var(--accent-green); font-size: 11px; color: var(--text-primary);">
                            <span style="color: var(--accent-green);">✓</span> Written back to SAP upon approval
                        </div>
                    </div>
                </div>

            </div>
        </div>
"""

# Replace workloads tab
workflows_regex = r'<!-- WORKFLOWS TAB.*?<div id="tab-automations" class="tab-content">'
html = re.sub(workflows_regex, process_mining_ui + '\n                <!-- AUTOMATIONS TAB -->\n                <div id="tab-automations" class="tab-content">', html, flags=re.DOTALL)

# Replace dashboards tab
dashboards_regex = r'<!-- DASHBOARDS TAB.*?<!-- ENTERPRISE TAB -->'
html = re.sub(dashboards_regex, custom_canvas_ui + '\n        <!-- ENTERPRISE TAB -->', html, flags=re.DOTALL)

# Replace company tab
company_regex = r'<!-- COMPANY TAB.*?<!-- DASHBOARDS TAB -->'
html = re.sub(company_regex, enterprise_connectors_ui + '\n        <!-- DASHBOARDS TAB -->', html, flags=re.DOTALL)

# Replace enterprise tab
enterprise_regex = r'<!-- ENTERPRISE TAB.*?<!-- Modals -->'
html = re.sub(enterprise_regex, action_flows_ui + '\n    <!-- Modals -->', html, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(html)
