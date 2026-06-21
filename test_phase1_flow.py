import os
import sys
import pandas as pd
import json
import time

# Ensure workspace root is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from platform_core.tools.scraper import WebScraper
from platform_core.tools.data_wrangler import DataWrangler
from platform_core.intelligence.skills_engine import run_and_heal_skill, save_skill

def run_test():
    print("=== STARTING PHASE 1 AUTOMATION INTEGRATION TESTS ===")
    
    # 1. Test Data Generation
    print("\n[Test Setup] Creating mock datasets...")
    os.makedirs("test_data", exist_ok=True)
    
    # Mock CRM CSV file
    crm_data = [
        {"Account_ID": "ACC100", "Company": "Global Tech Corp", "Revenue": 5000000, "Active": "Yes"},
        {"Account_ID": "ACC101", "Company": "Venture Builders", "Revenue": 1200000, "Active": "Yes"},
        {"Account_ID": "ACC102", "Company": "Quantum Dynamics", "Revenue": 95000000, "Active": "Yes"}, # Anomaly (very high)
        {"Account_ID": "ACC103", "Company": "Apex Retail", "Revenue": 450000, "Active": "No"},
        {"Account_ID": "ACC104", "Company": "Holo-Lenses Inc", "Revenue": 1500000, "Active": "Yes"},
        {"Account_ID": "ACC104", "Company": "Holo-Lenses Inc", "Revenue": 1500000, "Active": "Yes"}, # Duplicate row
    ]
    crm_df = pd.DataFrame(crm_data)
    crm_path = "test_data/raw_crm_deals.csv"
    crm_df.to_csv(crm_path, index=False)
    print(f"  - Saved mock CRM CSV to: {crm_path}")
    
    # Mock Roster Excel file
    roster_data = [
        {"Account_ID": "ACC100", "Region": "North America", "Manager": "Sarah Connor"},
        {"Account_ID": "ACC101", "Region": "EMEA", "Manager": "Tony Stark"},
        {"Account_ID": "ACC102", "Region": "APAC", "Manager": "Bruce Wayne"},
        {"Account_ID": "ACC103", "Region": "EMEA", "Manager": "Natasha Romanoff"},
        {"Account_ID": "ACC104", "Region": "North America", "Manager": "Steve Rogers"},
        {"Account_ID": "ACC105", "Region": "LATAM", "Manager": "Peter Parker"},
    ]
    roster_df = pd.DataFrame(roster_data)
    roster_path = "test_data/territory_roster.xlsx"
    roster_df.to_excel(roster_path, index=False)
    print(f"  - Saved mock Roster Excel to: {roster_path}")

    # Create mock HTML page for local scraping
    html_content = """
    <html>
    <head><title>Mock Web Report</title></head>
    <body>
        <h1>Company Employee Count Report</h1>
        <table id="emp-table">
            <thead>
                <tr>
                    <th>Company Name</th>
                    <th>Employee Count</th>
                    <th>Industry</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Global Tech Corp</td>
                    <td>14,500</td>
                    <td>Technology</td>
                </tr>
                <tr>
                    <td>Venture Builders</td>
                    <td>120</td>
                    <td>Financial Services</td>
                </tr>
                <tr>
                    <td>Quantum Dynamics</td>
                    <td>8,200</td>
                    <td>Energy</td>
                </tr>
                <tr>
                    <td>Holo-Lenses Inc</td>
                    <td>450</td>
                    <td>Hardware</td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    html_path = os.path.abspath("test_data/mock_webpage.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"  - Saved mock HTML page for scraping to: {html_path}")

    # 2. Test Scraper Utility
    print("\n[Test WebScraper] Scraping local html page...")
    file_url = f"file:///{html_path.replace(os.sep, '/')}"
    print(f"  - Loading page via Playwright: {file_url}")
    try:
        # requests can't fetch file:/// but Playwright can
        table_rows = WebScraper.scrape_table(file_url, table_selector="#emp-table", use_playwright=True)
        if table_rows:
            print(f"  - Successfully scraped {len(table_rows)} rows of data.")
            print(f"  - First row sample: {table_rows[0]}")
        else:
            print("  - FAILED: WebScraper returned empty table for local file.")
    except Exception as se:
        print(f"  - Scraper error: {se}")

    # 3. Test DataWrangler Utility
    print("\n[Test DataWrangler] Processing data files...")
    
    # Clean CSV
    print("  - Cleaning CRM CSV (removing duplicates and inactive rows)...")
    cleaned_crm = DataWrangler.clean_dataset(crm_path)
    # Filter inactive
    cleaned_crm = cleaned_crm[cleaned_crm['Active'] == 'Yes']
    print(f"    Cleaned rows: {len(cleaned_crm)} (Original: {len(crm_df)})")
    
    # Clean Excel Roster
    print("  - Cleaning Roster Excel...")
    cleaned_roster = DataWrangler.clean_dataset(roster_path)
    
    # Merge
    print("  - Merging datasets on 'Account_ID'...")
    merged_report = DataWrangler.merge_datasets(cleaned_crm, cleaned_roster, on_column="Account_ID", join_type="inner")
    print(f"    Merged columns: {list(merged_report.columns)}")
    print(f"    Merged row count: {len(merged_report)}")
    
    # Detect outliers/anomalies (e.g. huge deals)
    print("  - Detecting anomalies in Revenue column (> 1.0 standard deviations)...")
    anomalies = DataWrangler.detect_anomalies(merged_report, column="Revenue", threshold_std=1.0)
    print(f"    Detected {len(anomalies)} anomalies:")
    for _, row in anomalies.iterrows():
        print(f"      * {row['Company']}: ${row['Revenue']:,}")

    # Save to styled Excel
    output_path = "test_data/final_corporate_report.xlsx"
    print(f"  - Exporting styled final Excel report to: {output_path}")
    DataWrangler.export_to_excel(merged_report, output_path, sheet_name="Active Accounts Summary")
    print(f"    File generated: {os.path.exists(output_path)}")
    
    # 4. Test Sandbox Execution Compatibility
    print("\n[Test Sandbox Execution] Verifying skills engine compatibility...")
    automation_code = """
import sys
import os
sys.path.append(os.path.abspath("."))

from platform_core.tools.scraper import WebScraper
from platform_core.tools.data_wrangler import DataWrangler

def execute_pipeline():
    print("  -> Sandbox pipeline running successfully!")
    crm_clean = DataWrangler.clean_dataset("test_data/raw_crm_deals.csv")
    roster_clean = DataWrangler.clean_dataset("test_data/territory_roster.xlsx")
    merged = DataWrangler.merge_datasets(crm_clean, roster_clean, on_column="Account_ID", join_type="inner")
    out_path = "test_data/sandbox_report.xlsx"
    DataWrangler.export_to_excel(merged, out_path, sheet_name="Sandbox Merged")
    print(f"  -> Sandbox exported to: {out_path}")

if __name__ == "__main__":
    execute_pipeline()
"""
    # Save the skill to the database
    skill_name = "Phase_1_Test_Workflow"
    save_skill(skill_name, "Integration test for Phase 1", automation_code, "local")
    print(f"  - Skill '{skill_name}' saved to SQLite DB.")
    
    # Execute the saved skill inside the skills engine exec() environment
    print("  - Running skill inside the local execution sandbox...")
    res = run_and_heal_skill(skill_name, automation_code, "local")
    
    print("\n[Sandbox Output]")
    print(res.get("output", ""))
    
    if res.get("success"):
        print("  - SUCCESS: Skill executed successfully in sandbox!")
    else:
        print(f"  - FAILED: Sandbox execution error: {res.get('error')}")

    print("\n=== PHASE 1 INTEGRATION TESTS COMPLETED ===")

if __name__ == "__main__":
    run_test()
