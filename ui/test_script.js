
        const API_BASE = 'http://127.0.0.1:8000/v1';
        const HEADERS = { 'X-API-Key': 'sk-test-key-123', 'Content-Type': 'application/json' };
        
        let allWorkflows = [];
        let allApprovals = [];
        let currentActivePlanId = null;

        // UI Helpers
        function showToast(msg, type='success') {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.className = `toast ${type}`;
            toast.style.opacity = 1;
            setTimeout(() => toast.style.opacity = 0, 4000);
        }

        function closeModal(id) { document.getElementById(id).style.display = 'none'; }
        function openModal(id) { document.getElementById(id).style.display = 'flex'; }

        function formatCode(code) {
            let escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            escaped = escaped.replace(/(import|from|def|class|return|if|else|elif|try|except|for|in|while)\b/g, '<span class="kw">$1</span>');
            escaped = escaped.replace(/("[^"]*"|'[^']*')/g, '<span class="str">$1</span>');
            escaped = escaped.replace(/(#.*)/g, '<span class="cmt">$1</span>');
            return escaped;
        }

        function getGreeting() {
            const hr = new Date().getHours();
            if (hr < 12) return "Good morning";
            if (hr < 18) return "Good afternoon";
            return "Good evening";
        }
        document.getElementById('greeting').textContent = getGreeting();

        // API Calls
        async function fetchAPI(endpoint, options = {}) {
            console.log("Mocking API:", endpoint);
            
            // Artificial delay
            await new Promise(r => setTimeout(r, 400));
            
            if (endpoint.startsWith('/health')) {
                return { status: "ok" };
            }
            if (endpoint.startsWith('/mydata')) {
                return {
                    sessions_this_week: 42,
                    workflows_detected: 14,
                    clipboard_entries: 1204,
                    file_events: 539,
                    data_size_kb: 45000,
                    apps_tracked: ["Chrome", "VS Code", "Slack", "SAP GUI", "Outlook"]
                };
            }
            if (endpoint.startsWith('/proposals')) {
                return {
                    proposals: [
                        {id: "p1", type: "meeting_prep", title: "Upcoming Board Meeting", description: "You have a meeting with the board in 2 hours.", proposed_action: "Draft meeting notes from past Q2 data"},
                        {id: "p2", type: "anomaly", title: "SAP Invoice Anomaly", description: "3 invoices from Acme Corp lack PO numbers.", proposed_action: "Send automated email to vendor"}
                    ]
                };
            }
            if (endpoint.startsWith('/workflows')) {
                return [
                    {name: "Procure to Pay", app_sequence: "Outlook, SAP GUI, NetSuite", frequency_per_week: 45, avg_duration_seconds: 1400, automation_potential: 0.85},
                    {name: "Employee Onboarding", app_sequence: "Workday, Slack, Gmail", frequency_per_week: 12, avg_duration_seconds: 2400, automation_potential: 0.45},
                    {name: "Weekly Reporting", app_sequence: "Excel, PowerPoint, Outlook", frequency_per_week: 1, avg_duration_seconds: 3600, automation_potential: 0.95}
                ];
            }
            if (endpoint.startsWith('/approvals')) {
                if (options.method === 'POST') return { status: 'success' };
                return {
                    approvals: [
                        {id: "a1", tool_name: "Action Flow: Automate AP", plan_goal: "Automate Accounts Payable email parsing", parameters: "content': 'def parse_invoice():\n    # Extract PDF\n    # Send to SAP\n    pass'"},
                        {id: "a2", tool_name: "Slack Action", plan_goal: "Message EMEA team", parameters: "{channel: '#emea-ap', message: 'Please review Q3 variances'}"}
                    ]
                };
            }
            if (endpoint.startsWith('/intelligence/patterns')) {
                return {
                    app_usage_minutes: {"SAP GUI": 420, "Outlook": 310, "Chrome": 240, "Slack": 180, "Excel": 90}
                };
            }
            if (endpoint.startsWith('/intelligence/classifier')) {
                return {
                    classified_patterns: [
                        {app_sequence: ["Outlook", "SAP GUI"], overall_score: 0.92, recommended_action: "AUTOMATE"},
                        {app_sequence: ["Chrome", "Excel"], overall_score: 0.65, recommended_action: "DOCUMENT"}
                    ]
                };
            }
            if (endpoint.startsWith('/analyze')) {
                return {
                    digest: "## Weekly Intelligence Digest\n**High Impact:** You spent 7 hours in SAP GUI copying invoices. We recommend activating the *Invoice Parser* shadow automation.\n- 45 Procure-to-pay cycles completed\n- 12% rework rate on vendor Acme Corp."
                };
            }
            if (endpoint.startsWith('/mobile/query')) {
                return {
                    answer: "Based on the enterprise graph, Sarah from Finance usually approves these invoices within 4 hours. Would you like me to ping her on Slack?"
                };
            }

            return null;
        }

        // Health Check
        async function checkHealth() {
            const dot = document.getElementById('health-dot');
            try {
                const res = await fetch(`${API_BASE}/health`, { headers: HEADERS });
                if (res.ok) {
                    dot.style.backgroundColor = 'var(--accent-green)';
                    dot.title = 'Connected';
                } else throw new Error();
            } catch (e) {
                dot.style.backgroundColor = 'var(--accent-red)';
                dot.title = 'Disconnected';
            }
        }

        // --- Tabs Logic ---
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const target = e.currentTarget.dataset.tab;
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                
                document.querySelectorAll('.tab-content').forEach(tc => {
                    tc.classList.remove('active');
                    // Reset opacity for transition
                    tc.style.opacity = 0; 
                });
                
                // If the element doesn't have the tab- prefix (which they don't in the new tabs)
                const activeTab = document.getElementById(target) || document.getElementById(`tab-${target}`);
                if (activeTab) {
                    activeTab.classList.add('active');
                    setTimeout(() => activeTab.style.opacity = 1, 50);
                }
                
                loadTabData(target);
            });
        });

        // --- Loaders ---
        async function loadTabData(tab) {
            if (tab === 'today') await loadToday();
            else if (tab === 'workflows') await loadWorkflows();
            else if (tab === 'automations') await loadAutomations();
            else if (tab === 'approvals') await loadApprovals();
            else if (tab === 'insights') await loadInsights();
            else if (tab === 'onboarding') await loadOnboarding();
            else if (tab === 'me') await loadMeProfile();
            else if (tab === 'enterprise') { /* nothing to load initially */ }
            else if (tab === 'company') {
                await loadCompanyIntelligence('general');
                await loadTeamPerformance();
            }
            else if (tab === 'dashboards') await loadDashboardTypes();
        }

        const iconsMap = { 'meeting_prep': '📅', 'followup': '📧', 'reminder': '⏰', 'anomaly': '' };

        async function loadToday() {
            // Load status bar
            const mydata = await fetchAPI('/mydata');
            if (mydata) {
                document.getElementById('metric-sessions').textContent = mydata.sessions_this_week;
                document.getElementById('metric-workflows').textContent = mydata.workflows_detected;
                const hrs = (mydata.sessions_this_week * 0.5).toFixed(1); // placeholder calc
                document.getElementById('metric-hours').textContent = hrs;
            }

            // Load proposals
            const data = await fetchAPI('/proposals');
            const container = document.getElementById('proposals-container');
            container.innerHTML = '';
            
            if (!data || !data.proposals || data.proposals.length === 0) {
                container.innerHTML = '<div class="empty-state">No insights yet. Xenia is observing your workflows.</div>';
                return;
            }

            data.proposals.forEach(p => {
                const icon = iconsMap[p.type] || '💡';
                const el = document.createElement('div');
                el.className = 'card';
                el.id = `prop-${p.id}`;
                el.innerHTML = `
                    <div style="display:flex; gap: 16px;">
                        <div style="font-size: 32px;">${icon}</div>
                        <div style="flex: 1;">
                            <div class="text-bold" style="font-size: 16px;">${p.title}</div>
                            <div class="text-muted" style="font-size: 14px; margin: 4px 0;">${p.description}</div>
                            <div class="text-italic" style="font-size: 14px; color: var(--accent);">${p.proposed_action}</div>
                        </div>
                        <div style="display:flex; flex-direction:column; gap: 8px;">
                            <button class="btn btn-primary" onclick="handleProposal('${p.id}', 'approve', this)">Approve</button>
                            <button class="btn btn-ghost" onclick="handleProposal('${p.id}', 'dismiss', this)">Dismiss</button>
                        </div>
                    </div>
                `;
                container.appendChild(el);
            });
        }

        window.handleProposal = async (id, action, btn) => {
            // Fake API call as we don't have endpoints for these specifically yet, just visually dismiss
            if (action === 'approve') {
                btn.style.backgroundColor = 'var(--accent-green)';
                btn.innerHTML = '✓';
                showToast('Action approved');
            } else {
                document.getElementById(`prop-${id}`).style.opacity = 0;
                setTimeout(() => document.getElementById(`prop-${id}`).remove(), 200);
            }
        };

        async function loadWorkflows() {
            const data = await fetchAPI('/workflows');
            if (data) {
                allWorkflows = data;
                renderWorkflows('freq');
            }
        }

        window.renderWorkflows = (sortBy) => {
            let sorted = [...allWorkflows];
            if (sortBy === 'freq') sorted.sort((a,b) => (b.frequency_per_week||0) - (a.frequency_per_week||0));
            if (sortBy === 'time') sorted.sort((a,b) => (b.avg_duration_seconds||0) - (a.avg_duration_seconds||0));
            if (sortBy === 'auto') sorted.sort((a,b) => (b.automation_potential||0) - (a.automation_potential||0));

            const container = document.getElementById('workflows-container');
            container.innerHTML = '';

            if (sorted.length === 0) {
                container.innerHTML = '<div class="empty-state" style="grid-column: span 2;">No workflows detected yet. Keep working and Xenia will learn your patterns.</div>';
                return;
            }

            sorted.forEach(w => {
                const seq = (w.app_sequence || "").split(",").slice(0,3);
                const pills = seq.map((s, i) => `<span class="pill">${s.trim()}</span>${i<seq.length-1?'<span class="arrow">→</span>':''}`).join('');
                
                const freq = (w.frequency_per_week||0).toFixed(1);
                const mins = Math.round((w.avg_duration_seconds||0)/60);
                const autoPot = Math.round((w.automation_potential||0)*100);
                
                let barColor = 'var(--accent-green)';
                if (autoPot > 70) barColor = 'var(--accent-red)';
                else if (autoPot >= 40) barColor = 'var(--accent-yellow)';

                const el = document.createElement('div');
                el.className = 'card';
                el.innerHTML = `
                    <div class="text-bold" style="font-size: 18px; margin-bottom: 12px;">${w.name}</div>
                    <div style="margin-bottom: 12px;">${pills}</div>
                    <div class="metrics-row">
                        <span>🔁 ${freq}x/week</span>
                        <span>⏱ ${mins}min avg</span>
                        <span> ${autoPot}% automatable</span>
                    </div>
                    <div class="auto-bar-bg">
                        <div class="auto-bar-fill" style="width: ${autoPot}%; background-color: ${barColor};"></div>
                    </div>
                `;
                container.appendChild(el);
            });
        };

        async function loadAutomations() {
            const data = await fetchAPI('/approvals');
            const pendingContainer = document.getElementById('automations-pending-container');
            pendingContainer.innerHTML = '';
            
            if (data && data.approvals) {
                const autos = data.approvals.filter(a => (a.tool_name||"").includes("automation") || (a.plan_goal||"").toLowerCase().includes("automat"));
                
                if (autos.length === 0) {
                    pendingContainer.innerHTML = '<div class="empty-state">No pending automations.</div>';
                } else {
                    autos.forEach(a => {
                        const scriptMatch = (a.parameters||"").match(/content': '([^']+)'/);
                        const script = scriptMatch ? scriptMatch[1].replace(/\\n/g, '\n') : "# Python script";
                        const preview = script.split('\n').slice(0,8).join('\n');
                        
                        const el = document.createElement('div');
                        el.className = 'card';
                        el.id = `auto-${a.id}`;
                        el.innerHTML = `
                            <div style="display:flex; justify-content: space-between;">
                                <div>
                                    <div class="text-bold" style="font-size: 16px;">${a.plan_goal || "Workflow Automation"}</div>
                                    <div class="text-muted" style="font-size: 12px; margin-top: 4px;">Estimated time saved: 2 hours/week</div>
                                </div>
                                <div style="display:flex; gap: 8px; height: 32px;">
                                    <button class="btn btn-primary" onclick="reviewAutomation('${a.id}', \`${encodeURIComponent(script)}\`)">Review & Activate</button>
                                    <button class="btn btn-ghost" onclick="handleApprove('${a.id}', 'reject')">Reject</button>
                                </div>
                            </div>
                            <pre>${formatCode(preview)}</pre>
                        `;
                        pendingContainer.appendChild(el);
                    });
                }
            } else {
                pendingContainer.innerHTML = '<div class="empty-state">No pending automations.</div>';
            }
        }

        window.reviewAutomation = (id, encodedScript) => {
            const script = decodeURIComponent(encodedScript);
            document.getElementById('am-code').innerHTML = formatCode(script);
            const activateBtn = document.getElementById('am-activate-btn');
            activateBtn.onclick = () => {
                handleApprove(id, 'approve');
                closeModal('automation-modal');
                document.getElementById(`auto-${id}`).remove();
            };
            openModal('automation-modal');
        };

        async function updateApprovalsBadge() {
            const data = await fetchAPI('/approvals');
            if (data && data.approvals) {
                allApprovals = data.approvals;
                const badge = document.getElementById('approvals-badge');
                if (allApprovals.length > 0) {
                    badge.textContent = allApprovals.length;
                    badge.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                }
            }
        }

        async function loadApprovals() {
            await updateApprovalsBadge();
            const container = document.getElementById('approvals-container');
            container.innerHTML = '';

            if (allApprovals.length === 0) {
                container.innerHTML = '<div class="empty-state">No pending approvals.<br>Xenia will ask for your approval before taking any action.</div>';
                return;
            }

            allApprovals.forEach(a => {
                const el = document.createElement('div');
                el.className = 'card';
                el.id = `appr-${a.id}`;
                const timeStr = new Date(a.created_at * 1000).toLocaleString();
                el.innerHTML = `
                    <div style="display:flex; justify-content: space-between;">
                        <div>
                            <div class="text-bold" style="font-size: 16px;">${a.tool_name}</div>
                            <div class="text-muted" style="font-size: 12px; margin-top: 4px;">Goal: ${a.plan_goal || 'Unknown'}</div>
                            <div style="font-size: 12px; margin-top: 8px; color: var(--text-primary); font-family: monospace; background: var(--bg-primary); padding: 8px; border-radius: 4px; word-break: break-all;">
                                ${a.parameters}
                            </div>
                            <div class="text-muted" style="font-size: 10px; margin-top: 8px;">Created: ${timeStr}</div>
                        </div>
                        <div style="display:flex; flex-direction:column; gap: 8px;">
                            <button class="btn btn-primary" onclick="handleApprove('${a.id}', 'approve')">Approve</button>
                            <button class="btn btn-ghost" onclick="handleApprove('${a.id}', 'reject')">Reject</button>
                        </div>
                    </div>
                `;
                container.appendChild(el);
            });
        }

        window.handleApprove = async (id, action) => {
            let reason = "";
            if (action === 'reject') {
                reason = prompt("Reason (optional):") || "";
            }
            const res = await fetchAPI(`/approvals/${id}?action=${action}&reason=${encodeURIComponent(reason)}`, { method: 'POST' });
            if (res && res.status === 'success') {
                showToast(`Approval ${action}ed`);
                const card = document.getElementById(`appr-${id}`) || document.getElementById(`auto-${id}`);
                if (card) {
                    card.style.opacity = 0;
                    setTimeout(() => card.remove(), 200);
                }
                updateApprovalsBadge();
            }
        };

        // --- ASK TAB ---
        document.getElementById('mode-chat-btn').onclick = () => {
            document.getElementById('mode-chat-btn').className = 'btn btn-primary';
            document.getElementById('mode-plan-btn').className = 'btn btn-ghost';
            document.getElementById('ask-chat-view').style.display = 'flex';
            document.getElementById('ask-plan-view').style.display = 'none';
        };

        document.getElementById('mode-plan-btn').onclick = () => {
            document.getElementById('mode-plan-btn').className = 'btn btn-primary';
            document.getElementById('mode-chat-btn').className = 'btn btn-ghost';
            document.getElementById('ask-plan-view').style.display = 'block';
            document.getElementById('ask-chat-view').style.display = 'none';
        };

        const chatInput = document.getElementById('chat-input');
        const chatSend = document.getElementById('chat-send-btn');
        const chatHistory = document.getElementById('chat-history');

        async function sendChat() {
            const q = chatInput.value.trim();
            if (!q) return;
            chatInput.value = '';
            
            chatHistory.innerHTML += `<div class="msg user">${q}</div>`;
            const dotsId = 'typing-' + Date.now();
            chatHistory.innerHTML += `<div id="${dotsId}" class="msg ai">...</div>`;
            chatHistory.scrollTop = chatHistory.scrollHeight;

            const res = await fetchAPI(`/mobile/query?q=${encodeURIComponent(q)}`, { method: 'POST' });
            document.getElementById(dotsId).remove();
            
            if (res && res.answer) {
                chatHistory.innerHTML += `<div class="msg ai">${res.answer}</div>`;
            } else {
                chatHistory.innerHTML += `<div class="msg ai" style="color:var(--accent-red)">Error getting response.</div>`;
            }
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }

        chatSend.onclick = sendChat;
        chatInput.onkeypress = (e) => { if (e.key === 'Enter') sendChat(); };

        document.getElementById('plan-create-btn').onclick = async () => {
            const goal = document.getElementById('plan-input').value.trim();
            if (!goal) return;
            const container = document.getElementById('plan-result-container');
            container.innerHTML = '<div class="loader"></div>';
            
            const res = await fetchAPI(`/plans?goal=${encodeURIComponent(goal)}`, { method: 'POST' });
            if (res && res.plan_id) {
                currentActivePlanId = res.plan_id;
                let stepsHtml = res.steps.map((s, i) => {
                    let badgeClass = 'tier-auto';
                    let tierText = 'AUTO';
                    if (s.permission_tier === 'confirm') { badgeClass = 'tier-confirm'; tierText = 'CONFIRM'; }
                    if (s.permission_tier === 'review') { badgeClass = 'tier-review'; tierText = 'REVIEW'; }
                    
                    return `
                    <div class="plan-step" id="step-${i}">
                        <div style="width: 20px; height: 20px; border-radius: 50%; border: 2px solid var(--border); display:flex; align-items:center; justify-content:center; font-size:10px;" class="step-check"></div>
                        <div style="flex:1">
                            <div class="text-bold">${s.tool_name}</div>
                            <div class="text-muted" style="font-size: 12px;">${s.description || JSON.stringify(s.parameters)}</div>
                        </div>
                        <div class="tier-badge ${badgeClass}">${tierText}</div>
                    </div>`;
                }).join('');
                
                container.innerHTML = `
                    <div class="card">
                        <h3 style="margin-bottom:16px;">Plan Generated</h3>
                        ${stepsHtml}
                        <button class="btn btn-primary" style="margin-top: 20px; width: 100%;" onclick="executePlan()">Execute Plan</button>
                    </div>
                `;
            } else {
                container.innerHTML = '<div class="empty-state">Failed to create plan</div>';
            }
        };

        window.executePlan = async () => {
            if (!currentActivePlanId) return;
            showToast('Executing plan...', 'success');
            const res = await fetchAPI(`/plans/${currentActivePlanId}/execute`, { method: 'POST' });
            if (res) {
                // Fake visual execution for UI
                const checks = document.querySelectorAll('.step-check');
                checks.forEach((c, i) => {
                    setTimeout(() => {
                        c.style.borderColor = 'var(--accent-green)';
                        c.style.backgroundColor = 'var(--accent-green)';
                        c.style.color = 'black';
                        c.innerHTML = '✓';
                    }, (i+1)*1000);
                });
            }
        };

        // --- INSIGHTS TAB ---
        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'];
        
        async function loadOnboarding() {
            const container = document.getElementById('onboarding-container');
            container.innerHTML = '<div class="loader"></div>';
            
            const res = await fetchAPI('/onboarding/brief');
            if (!res) {
                container.innerHTML = '<div class="empty-state">Failed to load onboarding data.</div>';
                return;
            }
            
            if (res.status === 'insufficient_data') {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="icon">🎓</div>
                        <h2>Onboarding Intelligence</h2>
                        <p>${res.message}</p>
                        <p style="font-size:12px; color:var(--text-muted); margin-top:16px;">
                            Onboarding briefs generate automatically as team members contribute workflow patterns to the Role Vault.
                        </p>
                    </div>
                `;
                return;
            }
            
            if (res.status === 'ready' && res.brief) {
                const b = res.brief;
                let toolsHtml = (b.tools_you_will_use || []).map(t => 
                    `<div style="margin-bottom:8px"><strong>${t.tool}</strong>: ${t.how_used}</div>`
                ).join('');
                
                let processesHtml = (b.processes_to_learn_first || []).map(p => `
                    <div class="card" style="margin-bottom:12px; background:var(--background);">
                        <div class="text-bold" style="font-size:16px;">${p.name}</div>
                        <div style="font-style:italic; color:var(--text-muted); font-size:13px; margin:4px 0 8px 0;">${p.why_important}</div>
                        <div style="font-size:10px; font-weight:bold; background:#e2e8f0; color:#475569; display:inline-block; padding:2px 8px; border-radius:4px; margin-bottom:12px;">${p.frequency}</div>
                        <ol style="margin-left:20px; font-size:14px; color:var(--text);">
                            ${(p.rough_steps || []).map(s => `<li style="margin-bottom:4px;">${s}</li>`).join('')}
                        </ol>
                    </div>
                `).join('');
                
                let questionsHtml = (b.questions_you_will_have || []).map(q => 
                    `<li style="margin-bottom:8px;">${q}</li>`
                ).join('');
                
                container.innerHTML = `
                    <h2 style="margin-bottom:8px;">Day One Brief</h2>
                    <p style="color:var(--text-muted); font-size:14px; margin-bottom:24px;">Generated from ${res.generated_from}</p>
                    
                    <div class="card" style="margin-bottom:24px;">
                        <h3 style="margin-bottom:12px; color:var(--accent);">1. What This Role Actually Does</h3>
                        <p style="line-height:1.6; font-size:15px;">${b.what_this_role_actually_does}</p>
                    </div>
                    
                    <div class="card" style="margin-bottom:24px;">
                        <h3 style="margin-bottom:12px; color:var(--accent);">2. Tools You Will Use</h3>
                        <div style="font-size:14px;">${toolsHtml}</div>
                    </div>
                    
                    <h3 style="margin:32px 0 16px 0; color:var(--accent);">3. Processes To Learn First</h3>
                    ${processesHtml}
                    
                    <div class="card" style="margin-bottom:24px; margin-top:24px;">
                        <h3 style="margin-bottom:12px; color:var(--accent);">4. Your First Week</h3>
                        <p style="line-height:1.6; font-size:15px;">${b.first_week_reality}</p>
                    </div>
                    
                    <div class="card" style="margin-bottom:24px;">
                        <h3 style="margin-bottom:12px; color:var(--accent);">5. Questions You Will Have</h3>
                        <ul style="margin-left:20px; font-size:14px;">${questionsHtml}</ul>
                    </div>
                    
                    <button class="btn btn-primary" style="width:100%; margin-top:16px; padding:16px; font-size:16px;" onclick="generate90DayReport()">Generate 90-Day Report</button>
                `;
            }
        }
        
        window.generate90DayReport = async () => {
            showToast("Generating report...", "success");
            const res = await fetchAPI('/onboarding/90-day-report');
            if (res && res.status === 'ready' && res.report) {
                const r = res.report;
                const modal = document.getElementById('settings-modal');
                modal.querySelector('.modal-content').innerHTML = `
                    <div class="modal-header">
                        <h2>90-Day Contribution Report</h2>
                        <button class="icon-btn" onclick="closeModal('settings-modal')">✕</button>
                    </div>
                    <div style="padding:24px;">
                        <h1 style="text-align:center; font-size:24px; margin-bottom:32px; color:var(--accent);">${r.headline}</h1>
                        
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:24px;">
                            <div class="card" style="text-align:center; background:#f8fafc;">
                                <div style="font-size:32px; font-weight:800; color:#0f172a;">${r.workflows_mastered}</div>
                                <div style="font-size:12px; color:#64748b; text-transform:uppercase; font-weight:600; letter-spacing:0.05em;">Workflows Mastered</div>
                            </div>
                            <div class="card" style="text-align:center; background:#f8fafc;">
                                <div style="font-size:32px; font-weight:800; color:#0f172a;">${r.knowledge_contributed}</div>
                                <div style="font-size:12px; color:#64748b; text-transform:uppercase; font-weight:600; letter-spacing:0.05em;">Knowledge Cards</div>
                            </div>
                            <div class="card" style="text-align:center; background:#f8fafc; grid-column:span 2;">
                                <div style="font-size:32px; font-weight:800; color:#0f172a;">${r.team_contributions}</div>
                                <div style="font-size:12px; color:#64748b; text-transform:uppercase; font-weight:600; letter-spacing:0.05em;">Team Contributions</div>
                            </div>
                        </div>
                        
                        <div class="card" style="margin-bottom:24px; background:#eff6ff; border:1px solid #bfdbfe;">
                            <div style="font-size:11px; color:#1d4ed8; text-transform:uppercase; font-weight:700; margin-bottom:8px;">Impact Statement</div>
                            <div style="font-size:15px; color:#1e3a8a; line-height:1.5;">${r.impact_statement}</div>
                        </div>
                        
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:24px;">
                            <div>
                                <h3 style="font-size:14px; margin-bottom:12px; color:var(--accent-green);">Strengths Observed</h3>
                                <ul style="margin-left:20px; font-size:13px; color:var(--text);">
                                    ${(r.strengths_observed || []).map(s => `<li style="margin-bottom:6px;">${s}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 style="font-size:14px; margin-bottom:12px; color:var(--accent-red);">Growth Areas</h3>
                                <ul style="margin-left:20px; font-size:13px; color:var(--text);">
                                    ${(r.growth_areas || []).map(g => `<li style="margin-bottom:6px;">${g}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                `;
                openModal('settings-modal');
            } else {
                showToast("Failed to generate report");
            }
        };

        async function loadInsights() {
            const mydata = await fetchAPI('/mydata');
            if (mydata) {
                document.getElementById('is-sessions').textContent = mydata.sessions_this_week;
                document.getElementById('is-hours').textContent = (mydata.sessions_this_week * 0.5).toFixed(1);
                document.getElementById('is-apps').textContent = mydata.apps_tracked.length;
                document.getElementById('is-workflows').textContent = mydata.workflows_detected;
            }

            const patternsRes = await fetchAPI('/intelligence/patterns');
            if (patternsRes && patternsRes.app_usage_minutes) {
                const chart = document.getElementById('insights-app-chart');
                chart.innerHTML = '';
                let entries = Object.entries(patternsRes.app_usage_minutes).sort((a,b)=>b[1]-a[1]).slice(0,8);
                const max = Math.max(...entries.map(e=>e[1]), 1);
                
                entries.forEach((e, i) => {
                    const w = (e[1] / max) * 100;
                    const c = colors[i % colors.length];
                    chart.innerHTML += `
                        <div class="bar-row">
                            <div class="bar-lbl" title="${e[0]}">${e[0]}</div>
                            <div class="bar-track">
                                <div class="bar-fill" style="width: ${w}%; background: ${c};"></div>
                            </div>
                            <div class="bar-val">${Math.round(e[1])}m</div>
                        </div>
                    `;
                });
                if(entries.length === 0) chart.innerHTML = '<div class="empty-state">No app usage data</div>';
            }

            const classifier = await fetchAPI('/intelligence/classifier');
            if (classifier && classifier.classified_patterns) {
                const cont = document.getElementById('insights-patterns');
                cont.innerHTML = '';
                classifier.classified_patterns.forEach(p => {
                    let badgeColor = 'gray';
                    if (p.recommended_action === 'AUTOMATE') badgeColor = 'var(--accent-red)';
                    if (p.recommended_action === 'DOCUMENT') badgeColor = 'var(--accent)';
                    
                    cont.innerHTML += `
                        <div style="display:flex; justify-content: space-between; align-items:center; padding: 12px 0; border-bottom: 1px solid var(--border);">
                            <div style="flex:1;">
                                <div class="text-bold" style="font-size:14px;">${p.app_sequence.join(' → ')}</div>
                                <div class="text-muted" style="font-size:12px;">Score: ${p.overall_score}</div>
                            </div>
                            <div style="background:${badgeColor}; padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight:bold; color:white;">
                                ${p.recommended_action}
                            </div>
                        </div>
                    `;
                });
                if(classifier.classified_patterns.length === 0) cont.innerHTML = '<div class="empty-state">No classified patterns</div>';
            }
        }

        document.getElementById('generate-digest-btn').onclick = async () => {
            const cont = document.getElementById('digest-content');
            cont.innerHTML = '<div class="loader"></div>';
            const res = await fetchAPI('/analyze', {method: 'POST'});
            if (res && res.digest) {
                let md = res.digest;
                md = md.replace(/## (.*)/g, '<h2>$1</h2>');
                md = md.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                md = md.replace(/- (.*)/g, '<li>$1</li>');
                cont.innerHTML = `<div style="line-height:1.6; font-size:14px;">${md}</div>`;
            } else {
                cont.innerHTML = '<div class="empty-state">Digest generation failed.</div>';
            }
        };

        
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

        // --- Settings Modal ---
        document.getElementById('settings-btn').onclick = async () => {
            openModal('settings-modal');
            checkGmailStatus();
        };
        
        async function checkGmailStatus() {
            const dot = document.getElementById('gmail-status-dot');
            const text = document.getElementById('gmail-status-text');
            const btn = document.getElementById('gmail-connect-btn');
            
            const res = await fetchAPI('/connectors/gmail/inbox');
            if (res && res.emails) {
                dot.style.backgroundColor = 'var(--accent-green)';
                text.textContent = 'Gmail connected';
                btn.textContent = 'Disconnect';
                btn.onclick = () => { /* mock disconnect logic */ 
                    showToast('Disconnected from Gmail'); 
                    dot.style.backgroundColor = 'var(--text-muted)';
                    text.textContent = 'Gmail unconnected';
                    btn.textContent = 'Connect Gmail';
                    btn.onclick = connectGmail;
                };
            } else {
                dot.style.backgroundColor = 'var(--text-muted)';
                text.textContent = 'Gmail unconnected';
                btn.textContent = 'Connect Gmail';
                btn.onclick = connectGmail;
            }
        }
        
        window.connectGmail = async () => {
            document.getElementById('gmail-status-text').textContent = 'Opening browser for authorization...';
            // Trigger oauth route
            const res = await fetchAPI('/connectors/gmail/auth', {
                method: 'POST',
                body: JSON.stringify({ "credentials_path": "gmail_credentials.json" })
            });
            if (res && res.status === "authenticated") {
                document.getElementById('gmail-status-dot').style.backgroundColor = 'var(--accent-green)';
                document.getElementById('gmail-status-text').textContent = 'Gmail connected';
                document.getElementById('gmail-connect-btn').textContent = 'Disconnect';
                showToast("Gmail connected successfully", "success");
            } else {
                document.getElementById('gmail-status-text').textContent = 'Authentication failed';
            }
        };
        
        window.viewMyData = async () => {
            const data = await fetchAPI('/mydata');
            if(data) alert(`Your Data:\n\nSessions this week: ${data.sessions_this_week}\nWorkflows: ${data.workflows_detected}\nClipboard logs: ${data.clipboard_entries}\nFile events: ${data.file_events}\nDB Size: ${data.data_size_kb} KB`);
        };

        window.deleteAllData = async () => {
            if(confirm("Are you sure? This will wipe all local logs and patterns. Cannot be undone.")) {
                const res = await fetchAPI('/mydata', {method: 'DELETE'});
                if(res) showToast("All data wiped");
            }
        };

        // Boot
        setInterval(checkHealth, 10000);
        setInterval(() => { if(document.getElementById('tab-today').classList.contains('active')) loadToday(); }, 60000);
        setInterval(updateApprovalsBadge, 30000);
        
        checkHealth();
        loadToday();

    