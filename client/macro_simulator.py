import json
import os

def run_simulation(inr_depreciation_percent):
    """
    Simulates the impact of INR depreciation on key Indian stock sectors.
    inr_depreciation_percent: Positive float (e.g., 5.0 for a 5% drop in INR value vs USD)
    """
    
    # Baseline data (mocked baseline valuations or index values)
    sectors = {
        "IT Services": {"baseline": 100, "export_exposure": 0.8, "import_exposure": 0.1, "beta": 1.2, "stocks": ["TCS", "Infosys", "Wipro", "HCL Tech"]},
        "Pharmaceuticals": {"baseline": 100, "export_exposure": 0.6, "import_exposure": 0.2, "beta": 0.9, "stocks": ["Sun Pharma", "Dr Reddy's", "Cipla"]},
        "Oil & Gas": {"baseline": 100, "export_exposure": 0.1, "import_exposure": 0.85, "beta": -1.5, "stocks": ["Reliance", "BPCL", "ONGC"]},
        "FMCG": {"baseline": 100, "export_exposure": 0.05, "import_exposure": 0.4, "beta": -0.8, "stocks": ["HUL", "Britannia", "Nestle India"]},
        "Automobiles": {"baseline": 100, "export_exposure": 0.2, "import_exposure": 0.5, "beta": -0.5, "stocks": ["Tata Motors", "Maruti Suzuki", "M&M"]},
        "Banking": {"baseline": 100, "export_exposure": 0.0, "import_exposure": 0.0, "beta": -0.3, "stocks": ["HDFC Bank", "ICICI Bank", "SBI"]}
    }

    results = []
    
    for sector_name, data in sectors.items():
        # Margin expansion/contraction formula based on currency exposure
        # If INR falls, exports earn more INR, imports cost more INR.
        export_gain = data["export_exposure"] * inr_depreciation_percent * 1.5 # Multiplier for margin leverage
        import_loss = data["import_exposure"] * inr_depreciation_percent * 1.2
        
        net_impact_percent = export_gain - import_loss + (data["beta"] * (inr_depreciation_percent * 0.2)) # Macro sentiment beta
        
        new_value = data["baseline"] * (1 + net_impact_percent / 100)
        
        results.append({
            "sector": sector_name,
            "baseline": data["baseline"],
            "simulated": round(new_value, 2),
            "impact_percent": round(net_impact_percent, 2),
            "top_stocks": data["stocks"]
        })
        
    return results

def generate_html_dashboard(results, depreciation_percent):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Macro Simulation: INR Depreciation Impact</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }}
            .glass {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }}
        </style>
    </head>
    <body class="p-8">
        <div class="max-w-6xl mx-auto">
            <header class="mb-8 text-center">
                <h1 class="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">Elite AI Business Simulation Engine</h1>
                <p class="text-slate-400 mt-2 text-lg">Scenario: Impact of a {depreciation_percent}% Depreciation in the Indian Rupee (INR)</p>
            </header>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="glass p-6 rounded-2xl">
                    <h3 class="text-sm text-slate-400 uppercase tracking-wider">Top Boom Sector</h3>
                    <div class="text-3xl font-bold text-emerald-400 mt-2">IT Services</div>
                    <p class="text-sm mt-1 text-slate-300">TCS, Infosys, Wipro</p>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <h3 class="text-sm text-slate-400 uppercase tracking-wider">Top Risk Sector</h3>
                    <div class="text-3xl font-bold text-rose-400 mt-2">Oil & Gas</div>
                    <p class="text-sm mt-1 text-slate-300">Reliance, BPCL, ONGC</p>
                </div>
                <div class="glass p-6 rounded-2xl">
                    <h3 class="text-sm text-slate-400 uppercase tracking-wider">Secondary Effect</h3>
                    <div class="text-3xl font-bold text-amber-400 mt-2">Inflation Risk</div>
                    <p class="text-sm mt-1 text-slate-300">RBI Rate Hike Probability: High</p>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div class="glass p-6 rounded-2xl">
                    <h2 class="text-xl font-semibold mb-4">Sector Impact Analysis</h2>
                    <canvas id="impactChart"></canvas>
                </div>
                
                <div class="glass p-6 rounded-2xl overflow-y-auto" style="max-height: 400px;">
                    <h2 class="text-xl font-semibold mb-4">Detailed Stock Matrix</h2>
                    <div class="space-y-4">
    """
    
    # Sort results by impact
    results = sorted(results, key=lambda x: x["impact_percent"], reverse=True)
    
    labels = []
    data_points = []
    colors = []
    
    for r in results:
        labels.append(r["sector"])
        data_points.append(r["impact_percent"])
        
        if r["impact_percent"] > 0:
            colors.append('rgba(52, 211, 153, 0.8)') # emerald
            text_color = "text-emerald-400"
            sign = "+"
        else:
            colors.append('rgba(251, 113, 133, 0.8)') # rose
            text_color = "text-rose-400"
            sign = ""
            
        html_content += f"""
                        <div class="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                            <div class="flex justify-between items-center mb-2">
                                <span class="font-semibold text-lg">{r["sector"]}</span>
                                <span class="font-bold {text_color}">{sign}{r["impact_percent"]}%</span>
                            </div>
                            <p class="text-sm text-slate-400">Key Beneficiaries/Risks: <span class="text-slate-200">{", ".join(r["top_stocks"])}</span></p>
                        </div>
        """

    html_content += f"""
                    </div>
                </div>
            </div>
            
            <div class="mt-8 glass p-6 rounded-2xl">
                <h2 class="text-xl font-semibold mb-2">Simulation Mechanics & Assumptions</h2>
                <ul class="list-disc pl-5 text-slate-300 space-y-2 text-sm">
                    <li><strong>Mechanism:</strong> INR depreciation increases INR realizations for export-heavy businesses while dramatically inflating input costs for import-dependent sectors.</li>
                    <li><strong>Second Order Effects:</strong> Banking and Autos suffer slight negative beta due to imported inflation forcing the RBI to potentially hike interest rates, lowering credit demand.</li>
                    <li><strong>Confidence Level:</strong> HIGH for directional moves in IT and Pharma. MEDIUM for Banking.</li>
                </ul>
            </div>
        </div>

        <script>
            const ctx = document.getElementById('impactChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Projected Sector Impact (%)',
                        data: {json.dumps(data_points)},
                        backgroundColor: {json.dumps(colors)},
                        borderWidth: 0,
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            grid: {{ color: 'rgba(255,255,255,0.05)' }},
                            ticks: {{ color: '#94a3b8' }}
                        }},
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{ color: '#94a3b8' }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Save to disk
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macro_dashboard.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return output_path

if __name__ == "__main__":
    import sys
    # Default to 5% depreciation if not provided
    depreciation = 5.0
    if len(sys.argv) > 1:
        try:
            depreciation = float(sys.argv[1])
        except ValueError:
            pass
            
    res = run_simulation(depreciation)
    path = generate_html_dashboard(res, depreciation)
    print(f"Dashboard successfully generated at: {path}")
