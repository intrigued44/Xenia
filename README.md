# Xenia — Enterprise Automation & Organizational Intelligence Platform

Xenia is a local-first enterprise automation and productivity intelligence engine. It combines high-performance desktop window logs, lightweight native screen OCR, and stealth browser orchestration to automate tasks, eliminate corporate meeting overhead, and generate real-time executive ROI analytics.

---

## 🏗️ Technical Architecture & Core Systems

Xenia operates locally to ensure strict corporate data residency (complying with GDPR, HIPAA, and SOC2 guidelines). It coordinates three primary engines:

```
                  ┌──────────────────────────────┐
                  │      Xenia UI (Electron)     │
                  └──────────────┬───────────────┘
                                 │ HTTP / JSON
                  ┌──────────────▼───────────────┐
                  │    Xenia Server (FastAPI)    │
                  └──────────────┬───────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌────────▼────────┐     ┌────────▼────────┐     ┌────────▼────────┐
│  RPA Sandbox    │     │  Local Watcher  │     │   Local Vault   │
│ (skills_engine) │     │  (observer.py)  │     │ (vault_manager) │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
 ┌───────┼───────┐       ┌───────┼───────┐               │
 │       │       │       │       │       │               │
┌▼┐     ┌▼┐     ┌▼┐     ┌▼┐     ┌▼┐     ┌▼┐              │
│py│    │Se│    │Ca│    │Win│   │OCR│   │PII│              │
│au│    │le│    │mo│    │Log│   │SDK│   │Fil│              │
│to│    │ni│    │fo│    │   │   │   │   │ter│              │
└─┘     └─┘     └─┘     └───┘   └───┘   └───┘              │
  ▲                                                        │
  └─────────────────── Authenticates ──────────────────────┘
```

1. **Activity Observer & Event Watcher (`client/observer.py`)**:
   Runs background monitoring threads checking active window titles (using `pygetwindow`), tracking clipboard changes (`pyperclip`), and observing filesystem creations or modifications in workspace directories (`watchdog`).
2. **Native Windows OCR (`client/ocr_engine.py`)**:
   Uses the Windows-native Media OCR API (`winsdk.windows.media.ocr`) to perform fast, lightweight text recognition from captured screen thumbnails, removing any external dependencies on Tesseract.
3. **Data Sanitization & Privacy Filter (`client/pii_filter.py`)**:
   Analyzes extracted text or clipboard content locally to redact sensitive info (SSNs, credit cards, passwords, API keys) before data is stored or passed to LLM orchestration layers.
4. **Skills & Automation Sandbox (`platform_core/intelligence/skills_engine.py`)**:
   Executes auto-generated automation workflows using a local Python `exec()` environment. Implements self-healing error analysis powered by LLMs (Claude & OpenAI GPT-4o) to automatically correct and re-run failing automation scripts.
5. **Stealth Browser Orchestrator (Camofox)**:
   Launches and commands browsers using anti-fingerprinting configurations and persistent profile cookies to bypass browser CAPTCHAs and session security flags on target corporate portals.
6. **Secure Credential Vault (`platform_core/vaults/vault_manager.py`)**:
   Manages encrypted local keystores to authorize automated logins to webmails, reporting dashboards, and intranet portals.

---

## 🛡️ Six Layers of Enterprise Intelligence

### Layer 1: Communication Intelligence
* **Priority Triage**: Triages unread emails, scoring items by urgency, keywords, and sender role mapping.
* **Writing Style Copywriter**: Drafts contextual email replies using tone profiles learned from user's sent folders.
* **Slack / Teams notification aggregator**: Checks enterprise communication channels for action items and aggregates mentions.
* **Meeting Agenda Analyzer**: Evaluates calendar invites against current task priorities to suggest acceptances, declines, or delegations.

### Layer 2: Pipeline and Ops Intelligence
* **Alert Feed**: Parses incoming status reports, deal sheets, and logs, compiling them into a daily digest.
* **Archive Syncing**: Automatically logs notes from the clipboard or local files directly into organized folders.
* **Pipeline Gap Alerter**: Cross-references sales spreadsheets against target metrics to highlight pipeline risks.

### Layer 3: Data and Reporting Automation
* **Clean & Merge Excel Wrangling**: standard Python scripts running `pandas` and `openpyxl` inside the RPA sandbox. Automatically drops duplicates, joins datasets on matching ID columns, and formats table styles.
* **BI Refresh & PDF Export**: Automates cloud dashboard refreshing, downloads PDF snapshots, and exports reports.
* **Anomaly Outlier Detector**: Flags values exceeding 3 standard deviations in dataset columns before final export.

### Layer 4: Meeting Intelligence
* **Pre-Meeting Prep dossiers**: Auto-assembles brief dossiers for scheduled attendees (scraped via LinkedIn/local directory), previous mail threads, and project notes.
* **Live Call Screen OCR**: Captures Zoom/Teams window screenshots, runs native OCR, extracts decisions, and compiles an instant meeting timeline.
* **Meeting ROI Calculator**: Calculates the financial burn rate of meetings based on duration, attendee count, and corporate seniority pay grades.

### Layer 5: Executive Decision Intelligence
* **Executive command center**: Glassmorphic, modern dashboard showing priority email summaries, KPI metrics, and task statuses.
* **Competitor Signal Tracker**: Daily scans of competitor blog posts, news articles, and press announcements.
* **Board Pack Generator**: Compiles multi-department spreadsheets and text summaries into a formatted PDF slide brief.

### Layer 6: Knowledge & Compliance Layer
* **SharePoint / Confluence Q&A**: Explores internal documents to answer policy questions with cited source pages.
* **Contract Renewal watchdog**: Watches folder directories for contract PDFs, highlights upcoming renewals, and flags high-risk clauses.
* **Cryptographic Audit Trail**: Stores signed, immutable action logs inside the local SQLite database for compliance audits.

---

## 🚀 Installation & Developer Setup

### Prerequisites
* Windows 10/11
* Python 3.9+
* Node.js 18+

### 1. Install Dependencies
Install Python package requirements from the workspace root:
```bash
pip install -r requirements.txt
```
Install frontend dependencies inside the `ui` folder:
```bash
cd ui
npm install
cd ..
```

### 2. Launching in Development
Run the FastAPI backend server:
```bash
python start_server.py
```
Run the Electron frontend client in another window:
```bash
cd ui
npm run dev
```

### 3. Packaging & Building
Compile the Python backend into a single executable and bundle the Electron client into a Windows installer:
```bash
build.bat
```
*Compiled artifacts are saved in: `ui/dist/win-unpacked/`*

---

## 🧪 Verification & Testing
Xenia includes a suite to verify web scraping, pandas wrangling, and sandbox execution:
```bash
python test_phase1_flow.py
```
*Verify that the scraper extracts mock HTML table data, the wrangler merges CSV/Excel rosters and flags revenue anomalies, and the skills sandbox successfully runs code.*
