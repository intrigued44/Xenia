import re

filepath = r'C:\Users\pranav\Downloads\nous-windows-installer-src\ui\index.html'
with open(filepath, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the fetchAPI function with a mock version
old_fetch = r'''async function fetchAPI\(endpoint, options = \{\}\) \{
            console.log\("Mocking API:", endpoint\);.*?return null;
        \}'''

new_fetch = r"""async function fetchAPI(endpoint, options = {}) {
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
                        {id: "a1", tool_name: "Action Flow: Automate AP", plan_goal: "Automate Accounts Payable email parsing", parameters: "content': 'def parse_invoice():\\n    # Extract PDF\\n    # Send to SAP\\n    pass'"},
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
                    digest: "## Weekly Intelligence Digest\\n**High Impact:** You spent 7 hours in SAP GUI copying invoices. We recommend activating the *Invoice Parser* shadow automation.\\n- 45 Procure-to-pay cycles completed\\n- 12% rework rate on vendor Acme Corp."
                };
            }
            if (endpoint.startsWith('/mobile/query')) {
                return {
                    answer: "Based on the enterprise graph, Sarah from Finance usually approves these invoices within 4 hours. Would you like me to ping her on Slack?"
                };
            }

            return null;
        }"""

html = re.sub(old_fetch, new_fetch, html, flags=re.DOTALL)

# Let's fix it manually if the regex didn't work. We can just replace the literal string causing the issue.
bad_str1 = """{id: "a1", tool_name: "Action Flow: Automate AP", plan_goal: "Automate Accounts Payable email parsing", parameters: "content': 'def parse_invoice():
    # Extract PDF
    # Send to SAP
    pass'"},"""
good_str1 = """{id: "a1", tool_name: "Action Flow: Automate AP", plan_goal: "Automate Accounts Payable email parsing", parameters: "content': 'def parse_invoice():\\\\n    # Extract PDF\\\\n    # Send to SAP\\\\n    pass'"},"""

html = html.replace(bad_str1, good_str1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(html)
