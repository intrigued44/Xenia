# Xenia — Enterprise Automation & Organizational Intelligence Platform

Xenia is a local-first enterprise automation and productivity intelligence engine. It combines background activity observation, process mining, capability-bounded RPA automation, and grounded decision intelligence to eliminate manual workflow overhead while preserving organizational data privacy.

> **Status Notice**: Xenia's local-first architecture supports enterprise data residency and privacy compliance requirements (GDPR, SOC 2, HIPAA data control principles), but formal third-party compliance certifications have not been performed.

---

## 🏗️ Technical Architecture & Capability Status Matrix

| Subsystem / Capability | Verification Status | Implementation & Platform Notes |
| :--- | :---: | :--- |
| **Connected Closed-Loop Pilot Pipeline** | **VERIFIED** | 12-stage connected pipeline (`platform_core/pilot_pipeline.py` & `pilot_harness.py`) |
| **Capability-Bounded Sandbox Executor** | **VERIFIED** | Isolated subprocess sandbox (`platform_core/intelligence/restricted_executor.py`) |
| **LLM Provider Abstraction** | **VERIFIED** | Supports Anthropic, OpenAI, Local Ollama, and `MockLLMProvider` (`llm_provider.py`) |
| **Multi-Tier Credential Vault** | **VERIFIED** | Personal, Role, Team, and Org vault storage with RBAC (`vault_manager.py`) |
| **PII Sanitizer & Data Filter** | **VERIFIED** | Automatic regex redaction for SSNs, credit cards, emails, passwords (`pii_filter.py`) |
| **FastAPI Service API** | **VERIFIED** | REST API server with authenticated headers and environment CORS (`server.py`) |
| **Process Mining & Discovery** | **VERIFIED** | Sequence grouping and pattern classification (`preprocessor.py`, `classifier.py`) |
| **Active Window & Clipboard Observer** | **WINDOWS-ONLY / UNVERIFIED** | Background thread monitoring window titles (`pygetwindow`) and clipboard (`pyperclip`) |
| **Native Windows Media OCR** | **WINDOWS-ONLY / UNVERIFIED** | Windows Media OCR API (`winsdk.windows.media.ocr`) for local screen text extraction |
| **Electron UI Desktop Client** | **EXPERIMENTAL** | Glassmorphic Electron UI (`ui/index.html` + `ui/main.js`) |
| **Stealth Browser Orchestrator** | **EXPERIMENTAL** | Anti-fingerprinting browser automation wrappers (`platform_core/tools/browser.py`) |
| **Multi-Agent Orchestration & Research** | **PLANNED** | Multi-agent autonomous research capabilities |

---

## 🛡️ Six Layers of Enterprise Intelligence

### Layer 1: Communication Intelligence
* **Priority Triage**: Triages unread emails, scoring items by urgency, keywords, and sender role mapping. [VERIFIED]
* **Writing Style Copywriter**: Drafts contextual email replies using learned tone profiles. [EXPERIMENTAL]
* **Telegram Connector Bridge**: Zero-dependency polling bridge forwarding query sessions (`telegram_bridge.py`). [VERIFIED]

### Layer 2: Pipeline and Ops Intelligence
* **Alert Feed**: Parses status reports and logs into daily operational digests. [VERIFIED]
* **Archive Syncing**: Logs notes from clipboard or local files into organized workspace directories. [VERIFIED]

### Layer 3: Data and Reporting Automation
* **Clean & Merge Excel Wrangling**: Python scripts running `pandas` and `openpyxl` inside the restricted RPA sandbox. [VERIFIED]
* **Anomaly Outlier Detector**: Flags values exceeding standard deviation thresholds before final report export. [VERIFIED]

### Layer 4: Meeting Intelligence
* **Pre-Meeting Prep dossiers**: Auto-assembles brief dossiers for scheduled attendees. [EXPERIMENTAL]
* **Live Call Screen OCR**: Captures Zoom/Teams screenshots and extracts decisions via native OCR. [WINDOWS-ONLY]

### Layer 5: Executive Decision Intelligence
* **Executive Command Center**: Glassmorphic dashboard showing KPI metrics, task statuses, and proposals. [VERIFIED]
* **What-If Scenario Simulations**: Quantitative process impact simulations (`simulation.py`). [VERIFIED]

### Layer 6: Knowledge & Compliance Layer
* **Grounded Operational Q&A**: Answers queries grounded strictly in observable telemetry evidence. [VERIFIED]
* **Cryptographic Audit Trail**: Stores signed, immutable action logs inside local SQLite database. [VERIFIED]

---

## 🚀 Installation & Developer Setup

### Prerequisites
* Windows 10/11 or Linux / Docker
* Python 3.9+
* Node.js 18+

### 1. Install Dependencies
Install Python package requirements from the workspace root:
```bash
pip install -r requirements.txt
```
*(On Linux/Docker environments, dependencies without Windows-native packages are installed automatically via `requirements_linux.txt`).*

### 2. Launching Backend & Tests
Run the FastAPI backend server:
```bash
python start_server.py
```
Run the automated test suite:
```bash
python3 -m pytest -v
```
Run the full verification proof suite:
```bash
python3 generate_verification_proofs.py
```

### 3. Packaging & Building (Windows Target)
Compile backend into executable and bundle Electron installer:
```bash
build.bat
```
*(See `WINDOWS_VALIDATION.md` for native Windows QA testing checklist).*
