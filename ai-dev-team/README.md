# AI Dev Team — Local Agent Workflow

A multi-agent AI workflow using Claude (Planner), Ollama/Qwen (Executor), and GitHub Copilot (Reviewer) to automate feature development inside your projects.

---

## Overview

```
You describe a feature
        ↓
Claude (Planner)     → breaks it into a step-by-step implementation plan
        ↓
Qwen 14B (Executor)  → implements the code based on the plan
        ↓
Copilot (Reviewer)   → reviews the output inline in VS Code
```

---

## Architecture

```
ai-dev-team/
├── README.md
├── .env                  ← API keys and config
├── requirements.txt      ← Python dependencies
├── main.py               ← Entry point, run this
├── agents.py             ← Agent definitions (Planner + Executor + Analyzer)
├── tasks.py              ← Task definitions + chunk templates
├── tools.py              ← Custom tools (template reader, context readers, GSOC)
├── parse_output.py       ← Fallback file extractor from markdown output
└── tests/
    └── test_chunking.py  ← Tests for chunked execution logic
```

---

## Prerequisites

### Mac Mini (Server)
- macOS with M-series chip (M4 recommended)
- Ollama installed via official app from [ollama.com](https://ollama.com)
- `qwen2.5-coder:14b` model pulled
- Ollama exposed to local network (`OLLAMA_HOST=0.0.0.0`)

### Client Mac
- VS Code with Continue.dev extension installed
- Python 3.10+
- Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

---

## Setup

### 1. Clone or copy this folder into your project

```bash
cp -r ai-dev-team/ your-project/ai-dev-team/
cd your-project/ai-dev-team/
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
OLLAMA_BASE_URL=http://192.168.x.x:11434
OLLAMA_MODEL=qwen2.5-coder:14b
PROJECT_PATH=/Users/you/your-project
```

> If running on the Mac Mini itself, use `http://localhost:11434`
> If running on a client Mac on the same network, use your Mac Mini's local IP
> If running remotely via Tailscale, use your Tailscale IP (`100.x.x.x`)

### 4. Start Ollama on Mac Mini

```bash
# Using the ollama-serve script
./ollama-serve.sh start

# Or manually
OLLAMA_HOST=0.0.0.0 ollama serve
```

### 5. Pre-load the model (optional but recommended)

```bash
ollama run qwen2.5-coder:14b --keepalive 60m
```

---

## Usage

### FastAPI Backend Feature
```bash
python main.py "add a UDP check endpoint to the network health checker"
```

### React Frontend Feature
```bash
python main.py "add a dashboard to display network check results"
```

### With explicit project path
```bash
python main.py "add a shopping cart feature" --project /Users/you/my-app
```

### GSOC Security Scan Analysis
```bash
python main.py --gsoc
# Reads CSV files from network-health-checker-ui/backend/gsoc_scan/
# Writes report to gsoc_scan/gsoc_scan_analysis.md
```

### Chunked Scaffold (full greenfield creation)
```bash
# Auto-detected — large scaffold requests are chunked automatically
python main.py "create the full frontend for Network Health Checker"

# Force chunking on any task
python main.py --chunked "add all CRUD endpoints"

# Disable chunking (single-pass, old behavior)
python main.py --no-chunk "create the full frontend"
```

Chunked mode solves a Qwen 14B limitation: when asked to generate many files in one shot, it exhausts its output budget and starts producing stubs (`// TODO`, `continue similarly...`). Chunked mode splits the work into focused passes of 2-7 files each.

**How it works:**
```
python main.py "create the full frontend scaffold"
        │
        ▼  Auto-detects "react-scaffold" chunk template
        │
  Phase 1: Claude plans EVERYTHING (1 API call)
        │  Plan structured into 5 sections
        │
  Phase 2: Qwen executes each section independently
        │
    Chunk 1/5: Types & Services  (2 files)  ✅
    Chunk 2/5: Hooks             (5 files)  ✅
    Chunk 3/5: Components        (5 files)  ✅
    Chunk 4/5: Pages             (6 files)  ✅
    Chunk 5/5: Config & Entry    (7 files)  ✅
        │
  Summary + Copilot review reminder
```

Each chunk gets a focused prompt with only its plan section and a list of files already written (so imports resolve correctly).

### Interactive mode
```bash
python main.py
# then type your feature request when prompted
```

---

## Template Auto-Detection

The workflow automatically selects the right Copilot agent template based on your feature request keywords:

| Keywords in request | Template loaded |
|---|---|
| `react`, `ui`, `dashboard`, `component`, `page`, `vite`, `tsx`, `tailwind`, `navbar`, `modal` | `react-app-generator` |
| `fastapi`, `endpoint`, `service`, `schema`, `check`, `dns`, `tcp`, `http`, `egress`, `network` | `fastapi-app-generator` |
| `--gsoc` flag | `gsoc-scan-analyzer` |

You can override by being explicit in your request:
```bash
python main.py "create a React dashboard for the TCP check results"  # → React
python main.py "add a new async TCP proxy check endpoint"            # → FastAPI
```

---

## VS Code + Continue.dev Setup

Install the Continue extension and configure `~/.continue/config.yaml`:

### On Mac Mini (localhost)

```yaml
models:
  - title: Claude Sonnet (Planner)
    provider: anthropic
    model: claude-sonnet-4-5
    apiKey: your-anthropic-api-key

  - title: Qwen Coder 14B (Executor)
    provider: ollama
    model: qwen2.5-coder:14b
    apiBase: http://localhost:11434

tabAutocompleteModel:
  title: Autocomplete
  provider: ollama
  model: qwen2.5-coder:7b
  apiBase: http://localhost:11434

customCommands:
  - name: plan
    description: Plan a feature implementation
    prompt: >
      Act as a tech lead. Break down this feature request
      into a clear step-by-step implementation plan with
      file names and what to implement in each.

  - name: review
    description: Review selected code
    prompt: >
      Review this code for bugs, edge cases, security issues,
      and improvements. Be specific and actionable.

  - name: test
    description: Write unit tests
    prompt: >
      Write comprehensive unit tests for this code.
      Cover happy path, edge cases, and error cases.

  - name: explain
    description: Explain selected code
    prompt: >
      Explain this code clearly. What does it do,
      how does it work, and are there any concerns?
```

### On Client Mac (network)

Same config but change `apiBase`:
```yaml
apiBase: http://192.168.x.x:11434   # local network
# or
apiBase: http://100.x.x.x:11434    # via Tailscale
```

---

## Continue.dev Shortcuts

| Shortcut | Action |
|---|---|
| `Cmd+L` | Open Continue chat |
| `Cmd+I` | Inline edit on selected code |
| `Cmd+Shift+L` | Add selected code to chat |
| `/plan` | Plan a feature |
| `/review` | Review selected code |
| `/test` | Write unit tests |
| `/explain` | Explain selected code |

---

## Day-to-Day Workflow

### FastAPI Backend Feature
```
1. python main.py "add a UDP check endpoint"

2. Claude reads conventions + fastapi-app-generator template + existing code

3. Claude plans: schemas → service → route → tests

4. Qwen implements directly into your project files

5. Open changed files in VS Code → Copilot reviews

6. Run: pytest -q && helm lint helm/

7. Commit if passing
```

### React Frontend Feature (single feature)
```
1. python main.py "add a results dashboard with charts"

2. Claude reads conventions + react-app-generator template + existing UI

3. Claude plans: TypeScript interfaces → components → hooks → services → tests

4. Qwen implements React components directly into your project

5. Open changed files in VS Code → Copilot reviews

6. Run: npm test && npm run lint

7. Commit if passing
```

### Full Frontend Scaffold (chunked)
```
1. python main.py "create the full frontend for Network Health Checker"

2. Auto-detects react-scaffold template → chunked mode activates

3. Claude plans ALL sections in one pass (types, hooks, components, pages, config)

4. Qwen executes chunk 1/5: Types & Services (2 files)
   Qwen executes chunk 2/5: Hooks (5 files)
   Qwen executes chunk 3/5: Components (5 files)
   Qwen executes chunk 4/5: Pages (6 files)
   Qwen executes chunk 5/5: Config & Entry (7 files)

5. Full plan saved to ai-dev-team-plan.md for reference

6. Open changed files in VS Code → Copilot reviews

7. Run: npm install && npm run dev && npm test

8. Commit if passing
```

### GSOC Security Scan
```
1. Drop CSV files into network-health-checker-ui/backend/gsoc_scan/

2. python main.py --gsoc

3. Claude reads gsoc-scan-analyzer template + CSV files

4. Claude writes gsoc_scan_analysis.md with findings and mitigations

5. Review report, start with HIGH severity items
```

---

## Tool Roles

| Tool | Role | Best For |
|---|---|---|
| **claude.ai** | Consultant | Architecture decisions, long discussions |
| **Claude (Continue)** | Senior Architect | Planning, complex reasoning |
| **Qwen 14B (Continue/Ollama)** | Developer | Writing and editing code |
| **Copilot (autocomplete)** | Junior Dev | Inline suggestions while typing |
| **Copilot Chat** | Codebase Expert | Questions about existing code |
| **CrewAI — Feature mode** | Autonomous Worker | Full feature implementation (FastAPI or React) |
| **CrewAI — GSOC mode** | Security Analyst | Vulnerability and compliance scan reports |

---

## Copilot Agents Used as Templates

Your `.github/agents/` templates are automatically loaded as context before planning and execution:

| Agent | Loaded when |
|---|---|
| `fastapi-app-generator` | Backend feature requests (default) |
| `react-app-generator` | Frontend/UI feature requests |
| `gsoc-scan-analyzer` | `--gsoc` flag is passed |

This ensures generated code always follows your established project conventions — structure, naming, patterns, and quality standards — without needing to repeat them in every prompt.

---

## Custom Tools (tools.py)

| Tool | Purpose |
|---|---|
| `CopilotAgentTemplate` | Reads `.github/agents/` templates into agent context |
| `ProjectConventions` | Reads `copilot-instructions.md`, `AGENTS.md`, `README.md` |
| `NetworkCheckerContext` | Reads existing FastAPI services, schemas, routes, config |
| `ReactUIContext` | Reads existing React components, pages, hooks, config |
| `GSocScanReader` | Reads GSOC vulnerability and compliance CSV files |

---

## Query Routing Guide

| Task | Use |
|---|---|
| Autocomplete while typing | Copilot |
| Questions about existing code | Copilot Chat |
| Plan a new FastAPI feature | Continue → Claude Sonnet |
| Plan a new React feature | Continue → Claude Sonnet |
| Write or edit backend code | Continue → Qwen 14B (`Cmd+I`) |
| Write or edit frontend code | Continue → Qwen 14B (`Cmd+I`) |
| Review code | Copilot Chat or Continue → Claude |
| Write tests | Continue → `/test` → Qwen 14B |
| Full FastAPI feature end-to-end | `python main.py "backend feature"` |
| Full React feature end-to-end | `python main.py "ui/react feature"` |
| GSOC security scan report | `python main.py --gsoc` |
| Architecture decisions | claude.ai (consultant) |
| Private/sensitive code | Continue → Qwen (stays local) |

---

## GitHub Copilot — Review Step (Manual)

Copilot cannot be automated via script — it lives inside VS Code and has no external API. It is intentionally the **human checkpoint** in the workflow, which is good practice: you should always review AI-generated code before committing.

### Automation Status

| Tool | Automated? |
|---|---|
| Claude (Planner) | ✅ Yes — runs via script |
| Qwen/Ollama (Executor) | ✅ Yes — runs via script |
| GitHub Copilot (Reviewer) | ❌ No — manual step in VS Code |

### How to Do the Copilot Review

After `main.py` finishes, the script will remind you with this prompt:

```
✅ Implementation complete!

📋 Next Step — Copilot Review (manual):
   1. Open VS Code
   2. Select the changed files
   3. Open Copilot Chat (Ctrl+Shift+I)
   4. Paste this prompt:

   "Review the recently generated code for bugs,
    edge cases, security issues, and improvements.
    Be specific and actionable."

   5. Accept/reject suggestions
   6. Run your tests
   7. Commit if passing
```

### Copilot Chat Review Prompts

Use these inside Copilot Chat after the agent run:

**General review:**
```
Review the recently generated code for bugs, edge cases,
security issues, and improvements. Be specific and actionable.
```

**Security focused:**
```
Review this code specifically for security vulnerabilities,
input validation issues, and authentication weaknesses.
```

**Performance focused:**
```
Review this code for performance issues, unnecessary loops,
missing indexes, or inefficient queries.
```

**Test coverage:**
```
What test cases are missing from this implementation?
List edge cases that are not currently handled.
```

### Copilot Shortcuts for Review

| Shortcut | Action |
|---|---|
| `Ctrl+Shift+I` | Open Copilot Chat |
| Select code → Copilot Chat | Review selected block |
| `Cmd+I` | Inline fix suggestion |
| `/explain` | Explain selected code |
| `/fix` | Fix selected code |
| `/tests` | Generate tests for selection |

---

## Troubleshooting

### "Unable to connect to local Ollama"
```bash
# Check Ollama is running and exposed
curl http://192.168.x.x:11434
# Should return: Ollama is running

# If not, start it with network exposure
OLLAMA_HOST=0.0.0.0 ollama serve
```

### Model not loading
```bash
# Check model is pulled
ollama list

# Pull if missing
ollama pull qwen2.5-coder:14b
```

### Slow first response
Normal — Ollama loads the model on first request (~10-30 seconds for 14B). Pre-load it:
```bash
ollama run qwen2.5-coder:14b --keepalive 60m
```

### llama-server binary not found
Reinstall Ollama using the official Mac app from [ollama.com](https://ollama.com) instead of Homebrew.

### GSOC scan folder not found
Make sure your CSV files are in:
```
network-health-checker-ui/backend/gsoc_scan/
```
Files must end in `_VULNERABILITIES.csv` or `_COMPLIANCES.csv`.

### React UI project not found
If `ReactUIContext` reports the UI folder missing, it means the React project hasn't been scaffolded yet. Run:
```bash
python main.py "create the full frontend for Network Health Checker"
```
This auto-detects the `react-scaffold` chunk template and generates the full frontend in 5 focused passes (types → hooks → components → pages → config).

### Qwen produces stubs or "continue similarly..."
This happens when the task is too large for a single pass. Use chunked mode:
```bash
python main.py --chunked "your large feature request"
```
If auto-detection didn't trigger, add scaffold keywords like "full frontend" or "complete backend" to your request. If a chunk still produces stubs, its raw output is saved to `ai-dev-team-chunk-{N}-output.md` — you can use `parse_output.py` to extract files manually.

---

## Network Configuration

| Location | Ollama URL |
|---|---|
| On Mac Mini | `http://localhost:11434` |
| Same WiFi/LAN | `http://192.168.x.x:11434` |
| Via Tailscale | `http://100.x.x.x:11434` |

---

## Cost Estimate

| Component | Cost |
|---|---|
| Ollama (Qwen) | Free — runs locally |
| Claude API (Planner) | ~$0.01–0.05 per feature (pay-as-you-go) |
| GitHub Copilot | Covered by your Office license |
| Claude Pro (claude.ai) | Covered by your Pro subscription |

Claude API is only used for planning and review — Qwen handles all code generation locally at zero cost.
