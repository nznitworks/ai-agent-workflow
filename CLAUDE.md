# CLAUDE.md — AMIPDH Network Tools

This file is loaded automatically by Claude Code (CLI) at the start of every session.
It contains the full project context, architecture decisions, and AI workflow setup
built during our consultant sessions.

---

## Project Overview

**AMIPDH Network Tools** is a monorepo containing:

```
AMIPDH-Network-Tools/
├── backend/                    ← FastAPI network health checker (renamed from network-health-checker/)
├── frontend/                   ← React TypeScript UI (in progress)
├── ai-dev-team/                ← Multi-agent AI workflow (Claude + Qwen + Copilot)
├── ansible-local-testing/      ← Ansible playbooks for local testing
└── .github/
    ├── agents/                 ← Copilot agents (fastapi, react, gsoc)
    ├── skills/                 ← MCP client and SCS doc skills
    └── copilot-instructions.md ← Full project conventions
```

---

## Session Startup

**CRITICAL:** Always load the MCP client skill at the start of each session:

```bash
bash .github/skills/mcp-client/scripts/discover.sh
```

---

## Backend — Network Health Checker

### Purpose
FastAPI backend that validates outbound connectivity from Kubernetes/OpenShift
namespaces to internal or external targets. Used for network policy validation.

### Architecture
```
backend/app/
├── main.py              # FastAPI app initialization
├── core/config.py       # Pydantic settings from env vars
├── api/
│   ├── router.py        # API router wiring
│   └── routes/
│       ├── health.py            # /health/live, /health/ready
│       └── network_checks.py    # /checks/* endpoints
├── services/
│   └── network_checks.py        # Async network check logic
└── schemas/
    ├── health.py        # Health endpoint models
    └── checks.py        # Check request/response models
```

### API Contract (Base: /api/v1)

```
GET  /health/live          → liveness probe
GET  /health/ready         → readiness probe
POST /checks/http          → single HTTP/HTTPS check
POST /checks/egress        → multi-URL egress validation
POST /checks/dns           → DNS A/AAAA resolution
POST /checks/tcp           → TCP socket connectivity
```

### Pydantic Schemas (checks.py)

```python
class HttpCheckRequest(BaseModel):
    url: HttpUrl
    timeout_seconds: float = Field(default=5.0, ge=0.5, le=30.0)
    expected_status: int = Field(default=200, ge=100, le=599)

class HttpCheckResponse(BaseModel):
    ok: bool
    url: str
    status_code: int | None = None
    latency_ms: float | None = None
    detail: str

class EgressCheckRequest(BaseModel):
    urls: list[HttpUrl] = Field(min_length=1, max_length=50)
    timeout_seconds: float = Field(default=5.0, ge=0.5, le=30.0)
    expected_status: int = Field(default=200, ge=100, le=599)

class EgressCheckResponse(BaseModel):
    ok: bool
    total: int
    success_count: int
    failure_count: int
    results: list[EgressUrlResult]
    detail: str

class DnsCheckRequest(BaseModel):
    hostname: str = Field(min_length=1, max_length=253)
    record_type: str = Field(default="A", pattern="^(A|AAAA)$")

class DnsCheckResponse(BaseModel):
    ok: bool
    hostname: str
    record_type: str
    addresses: list[str] = Field(default_factory=list)
    detail: str

class TcpCheckRequest(BaseModel):
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(ge=1, le=65535)
    timeout_seconds: float = Field(default=5.0, ge=0.5, le=30.0)

class TcpCheckResponse(BaseModel):
    ok: bool
    host: str
    port: int
    latency_ms: float | None = None
    detail: str
```

### Backend Rules (MUST follow)
1. Route handlers stay thin — all logic goes in `services/`
2. Service functions must be `async def` using `httpx.AsyncClient`
3. All inputs/outputs use Pydantic v2 models with validators
4. Catch exceptions in services, return `ok=False` — never raise to route handlers
5. Tests use `TestClient` — no live internet calls
6. Python version: **3.11**
7. Port: **8080** — must match Dockerfile, helm/values.yaml, azure-pipelines/shared-variables.yml
8. Base image: ING RHEL9 from p15915baseimagesde.azurecr.io
9. Update `backend/README.md` and `backend/AGENTS.md` when API changes

### Running Backend
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Testing Backend
```bash
cd backend
pytest -q
helm lint helm/
helm template network-check-backend helm/
```

### Pre-Merge Checklist
- [ ] `pytest` passes
- [ ] App starts with uvicorn
- [ ] `helm lint helm/` passes
- [ ] `helm template` renders valid manifests
- [ ] README.md and AGENTS.md updated if API changed

---

## Frontend — React UI

### Status: In Progress
Scaffolded via AI agent workflow. Some components are stubs and need completion.

### Tech Stack
- Vite + React 18 + TypeScript
- Tailwind CSS
- React Router v6
- TanStack Query (React Query)
- Axios
- Vitest + React Testing Library
- ESLint + Prettier

### Structure
```
frontend/
├── src/
│   ├── types/
│   │   └── api.ts           ← TypeScript interfaces (matches Pydantic schemas)
│   ├── services/
│   │   └── api.ts           ← Axios instance + typed API calls
│   ├── hooks/
│   │   ├── useHttpCheck.ts  ← POST /checks/http
│   │   ├── useEgressCheck.ts← POST /checks/egress
│   │   ├── useDnsCheck.ts   ← POST /checks/dns
│   │   ├── useTcpCheck.ts   ← POST /checks/tcp
│   │   └── useHealth.ts     ← GET /health/live + /health/ready (30s refresh)
│   ├── components/
│   │   ├── CheckForm/       ← reusable form wrapper (STUB — needs completion)
│   │   ├── ResultCard/      ← ok/fail result display (STUB — needs completion)
│   │   ├── StatusBadge/     ← green/red ok indicator (STUB — needs completion)
│   │   ├── LatencyBadge/    ← latency_ms display (STUB — needs completion)
│   │   └── ErrorBoundary/   ← error boundary (STUB — needs completion)
│   ├── pages/
│   │   ├── Dashboard.tsx    ← tabbed view of all checks
│   │   ├── HttpCheck.tsx
│   │   ├── EgressCheck.tsx  ← multi-URL textarea, one per line, max 50
│   │   ├── DnsCheck.tsx     ← A/AAAA dropdown
│   │   ├── TcpCheck.tsx
│   │   └── Health.tsx       ← auto-refresh every 30s
│   ├── App.tsx
│   └── main.tsx
├── .env.example             ← VITE_API_BASE_URL=http://localhost:8080
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### TypeScript Interfaces (must match Pydantic schemas exactly)
```typescript
interface HttpCheckRequest { url: string; timeout_seconds?: number; expected_status?: number }
interface HttpCheckResponse { ok: boolean; url: string; status_code: number|null; latency_ms: number|null; detail: string }
interface EgressCheckRequest { urls: string[]; timeout_seconds?: number; expected_status?: number }
interface EgressUrlResult { url: string; ok: boolean; status_code: number|null; latency_ms: number|null; detail: string }
interface EgressCheckResponse { ok: boolean; total: number; success_count: number; failure_count: number; results: EgressUrlResult[]; detail: string }
interface DnsCheckRequest { hostname: string; record_type?: 'A' | 'AAAA' }
interface DnsCheckResponse { ok: boolean; hostname: string; record_type: string; addresses: string[]; detail: string }
interface TcpCheckRequest { host: string; port: number; timeout_seconds?: number }
interface TcpCheckResponse { ok: boolean; host: string; port: number; latency_ms: number|null; detail: string }
interface HealthResponse { status: string }
```

### Frontend Rules (MUST follow)
1. Functional components and hooks only — no class components
2. TypeScript interfaces for all props, state, and API types
3. PascalCase for components, camelCase for functions/variables
4. API calls in `src/services/` — not inside components
5. Environment variable for API URL: `VITE_API_BASE_URL`
6. Tests with Vitest + React Testing Library — mock all API calls
7. No real network calls in tests

### Form Validation Rules (match backend)
- `timeout_seconds`: 0.5 to 30.0
- `expected_status`: 100 to 599
- `port`: 1 to 65535
- `hostname/host`: max 253 characters
- `record_type`: only `A` or `AAAA` (dropdown)
- `urls` (egress): textarea, one URL per line, max 50

### Running Frontend
```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
npm run build
npm run test
```

### Outstanding Work
- [ ] Complete stub components (CheckForm, ResultCard, StatusBadge, LatencyBadge, ErrorBoundary)
- [ ] Add package.json, vite.config.ts, tsconfig.json, tailwind.config.ts
- [ ] Azure Pipelines for frontend build and deploy
- [ ] Helm chart for frontend deployment

---

## AI Dev Team Workflow

### Purpose
Multi-agent workflow that automates feature development:
```
Claude (Planner) → Qwen 14B via Ollama (Executor) → Copilot (Reviewer — manual)
```

### Infrastructure
- **Mac Mini M4** (16GB) — Ollama server
- **Ollama** — runs `qwen2.5-coder:14b` locally
- **Tailscale** — private network access from any device
- **Continue.dev** — VS Code extension connecting to both Claude API and Ollama

### Files
```
ai-dev-team/
├── main.py          ← entry point
├── agents.py        ← Claude (planner) + Qwen (executor) + Claude (analyzer)
├── tasks.py         ← task definitions, auto-detects FastAPI vs React template
├── tools.py         ← custom tools (template reader, context readers, GSOC)
├── parse_output.py  ← extracts files from ai-dev-team-output.md
├── .env             ← API keys and config
└── requirements.txt
```

### Environment Variables (.env)
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
OLLAMA_BASE_URL=http://192.168.x.x:11434   # Mac Mini IP (client mac)
OLLAMA_MODEL=qwen2.5-coder:14b
CLAUDE_MODEL=claude-sonnet-4-5
PROJECT_PATH=/path/to/AMIPDH-Network-Tools
OTEL_SDK_DISABLED=true
CREWAI_TRACING_ENABLED=false
```

### Running the Workflow
```bash
cd ai-dev-team

# FastAPI feature (auto-detects backend keywords)
python main.py "add a UDP check endpoint"

# React feature (auto-detects frontend keywords)
python main.py "create StatusBadge component showing ok as green checkmark"

# GSOC security scan
python main.py --gsoc

# Parse output if files weren't written
python parse_output.py --dry-run
python parse_output.py --prefix frontend
```

### Key Lessons Learned
- Qwen 14B cuts corners on large tasks — **use small focused prompts**
- Split frontend scaffold into: types → services → hooks → components → pages → config
- Always run `parse_output.py` if files aren't created after a run
- `OLLAMA_BASE_URL` must point to Mac Mini IP on client Mac (not localhost)
- Use `ollama_chat/` prefix (not `ollama/`) in CrewAI LLM config
- CrewAI requires Python `>=3.10, <3.14` — use **3.11**

### Template Auto-Detection
| Keywords in request | Template used |
|---|---|
| react, ui, dashboard, component, page, vite, tsx, tailwind, navbar, modal | `react-app-generator` |
| fastapi, endpoint, service, schema, check, dns, tcp, http, egress, network | `fastapi-app-generator` |
| `--gsoc` flag | `gsoc-scan-analyzer` |

### Copilot Agents (used as templates)
Located in `.github/agents/`:
- `fastapi-app-generator.agent.md` — FastAPI conventions, async patterns, Pydantic v2
- `react-app-generator.agent.md` — React/TypeScript, Vite, hooks, Vitest
- `gsoc-scan-analyzer.agent.md` — GSOC CSV analysis, markdown report generation

### Copilot Review (manual step after each run)
```
1. Open VS Code
2. Select changed files
3. Open Copilot Chat (Ctrl+Shift+I)
4. Prompt: "Review this generated code for bugs, edge cases,
            security issues, and improvements. Be specific."
5. Accept/reject suggestions
6. Run tests
7. Commit if passing
```

---

## Ollama Server Setup

### Mac Mini M4 (server)
```bash
# Start with network exposure
OLLAMA_HOST=0.0.0.0 ollama serve

# Or use the manage script
./ollama-serve.sh start|stop|restart|status|logs

# Pre-load model
ollama run qwen2.5-coder:14b --keepalive 60m

# Check if exposed
lsof -i :11434   # must show *:11434 not localhost:11434
```

### Client Mac
```bash
# Test connectivity
curl http://192.168.x.x:11434
# Expected: Ollama is running

# Test model
curl http://192.168.x.x:11434/api/chat \
  -d '{"model":"qwen2.5-coder:14b","messages":[{"role":"user","content":"hello"}],"stream":false}'
```

### Continue.dev Config (client mac — ~/.continue/config.yaml)
```yaml
models:
  - title: Claude Sonnet (Planner)
    provider: anthropic
    model: claude-sonnet-4-5
    apiKey: your-anthropic-api-key

  - title: Qwen Coder 14B (Executor)
    provider: ollama
    model: qwen2.5-coder:14b
    apiBase: http://192.168.x.x:11434

tabAutocompleteModel:
  title: Autocomplete
  provider: ollama
  model: qwen2.5-coder:7b
  apiBase: http://192.168.x.x:11434
```

---

## Tool Roles

| Tool | Role | Best For |
|---|---|---|
| **claude.ai** | Consultant | Architecture decisions, this session |
| **Claude (Continue)** | Senior Architect | Planning, complex reasoning |
| **Qwen 14B (Ollama)** | Developer | Writing code (small focused tasks) |
| **Copilot (autocomplete)** | Junior Dev | Inline suggestions while typing |
| **Copilot Chat** | Codebase Expert | Questions about existing code |
| **CrewAI** | Autonomous Worker | End-to-end feature runs |

## Query Routing

| Task | Use |
|---|---|
| Autocomplete while typing | Copilot |
| Questions about existing code | Copilot Chat |
| Plan a feature | Continue → Claude |
| Write/edit code | Continue → Qwen (`Cmd+I`) |
| Review code | Copilot Chat |
| Full feature end-to-end | `python main.py "..."` |
| GSOC scan | `python main.py --gsoc` |
| Architecture decisions | claude.ai (here) |
| Private/sensitive code | Continue → Qwen (local) |

---

## What's Not Done Yet

### Frontend
- [ ] Stub components need full implementation
- [ ] package.json, vite.config.ts, tsconfig.json missing
- [ ] No Azure Pipeline for frontend yet
- [ ] No Helm chart for frontend yet

### Infrastructure
- [ ] Azure Pipelines for frontend (build + deploy)
- [ ] Helm chart for frontend deployment
- [ ] SCS assets (ING-specific)
- [ ] GSOC scan workflow end-to-end test

### AI Dev Team
- [ ] Better handling of large scaffold tasks (chunked runs)
- [ ] Auto-detect when output has stubs and re-run missing parts

---

## Key Decisions Made

| Decision | Reason |
|---|---|
| Renamed `network-health-checker/` → `backend/` | Cleaner monorepo structure before frontend added |
| Qwen 14B for execution | Free, local, fast enough for focused tasks |
| Claude for planning | Best reasoning for architecture and complex decisions |
| Copilot for review | Already in VS Code, knows the codebase |
| `ollama_chat/` prefix in CrewAI | `ollama/` routes to OpenAI fallback — bug |
| Small focused prompts for Qwen | Large prompts cause Qwen to leave stubs |
| `parse_output.py` | CrewAI FileWriterTool unreliable with Qwen |
| Python 3.11 for ai-dev-team | Matches backend, CrewAI compatible |
