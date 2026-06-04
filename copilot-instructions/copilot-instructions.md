# Copilot Instructions - AMIPDH Network Tools

## Repository Overview

This is a monorepo containing network tooling and AI development utilities:

- **network-health-checker/** - FastAPI backend for Kubernetes/OpenShift network diagnostics
- **ai-dev-team/** - Multi-agent AI workflow tool (Claude + Qwen + Copilot)
- **ansible-local-testing/** - Ansible playbooks for local testing
- **.github/agents/** - Custom Copilot agents (FastAPI/React generators, GSOC scanner)
- **.github/skills/** - MCP client and SCS documentation skills

## Session Startup

**CRITICAL:** Always load the `mcp-client` skill at the start of each session. This discovers MCP server tools and loads documentation catalogs into your context.

```bash
# This is handled automatically by AGENTS.md
bash .github/skills/mcp-client/scripts/discover.sh
```

## Network Health Checker (Primary Project)

### Purpose

FastAPI backend that validates outbound connectivity from Kubernetes/OpenShift namespaces to internal or external targets. Used for network policy validation and debugging.

### Architecture

```
app/
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

**Design principle:** Keep route handlers thin. All network logic lives in `services/network_checks.py` using async I/O patterns.

### API Contract (Base: /api/v1)

Health endpoints:
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe

Check endpoints (all POST):
- `/checks/http` - Single HTTP/HTTPS endpoint check
- `/checks/egress` - Multi-URL egress validation with aggregate status
- `/checks/dns` - DNS A/AAAA record resolution
- `/checks/tcp` - TCP socket connectivity test

**Important behaviors:**
- HTTP/egress checks compare actual status code to `expected_status`
- Egress returns per-URL results + aggregate pass/fail counts
- DNS only supports A and AAAA record types
- Validation errors must return 422

### Running the App

```bash
cd network-health-checker

# Setup (first time)
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run locally
python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Or via Docker
docker build -t network-check-backend:local .
docker run --rm -p 8080:8080 network-check-backend:local
```

### Testing

```bash
cd network-health-checker

# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest -q

# Run specific test file
pytest tests/test_network_checks.py -v

# Run single test
pytest tests/test_network_checks.py::test_dns_validation_error_for_invalid_record_type -v
```

**Test design:** Tests use `TestClient` for synchronous API calls and favor deterministic checks over live internet dependencies.

### Configuration

Settings in `app/core/config.py` loaded from environment variables or `.env`:

```bash
APP_NAME="Network Health Checker API"
APP_VERSION="1.0.0"
API_PREFIX="/api/v1"
ENVIRONMENT="dev"
DEFAULT_TIMEOUT_SECONDS=5.0
```

### Deployment

**Helm:**
```bash
cd network-health-checker

# Validate chart
helm lint helm/
helm template network-check-backend helm/

# Deploy
helm upgrade --install network-check-backend helm/
```

**Azure Pipelines:** Uses Autobahn templates in `azure-pipelines/`. Primary files:
- `build.yml` - Docker image + Helm artifact build
- `deploy-backend.yml` - Helm deployment
- `shared-variables.yml` - Cross-pipeline variables

### Code Change Rules

When modifying the network-health-checker:

1. **Route handlers** - Keep thin. Move logic to `services/`
2. **Service functions** - Preserve async I/O patterns
3. **Schemas** - Keep strict Pydantic validation
4. **Response models** - Do not break compatibility unless versioning
5. **Tests** - Favor deterministic tests over live internet calls
6. **Port changes** - If changing from 8080, update:
   - `Dockerfile` CMD
   - `helm/values.yaml` applicationPort
   - `azure-pipelines/shared-variables.yml`

### Container Requirements

- **User:** Non-root (UID 1000)
- **Port:** 8080 (must match Helm and Dockerfile)
- **Base image:** ING RHEL9 base from p15915baseimagesde.azurecr.io
- **Dependencies:** Pinned via `requirements.txt`

### Pre-Merge Checklist

Before merging changes to network-health-checker:

1. `pytest` passes
2. App starts with uvicorn
3. `helm lint helm/` passes
4. `helm template network-check-backend helm/` renders valid manifests
5. If API behavior changed, update both `README.md` and `AGENTS.md`

### Documentation Sync

When changing API routes, schemas, runtime behavior, or deployment config:
- Update `network-health-checker/README.md` (user-facing)
- Update `network-health-checker/AGENTS.md` (AI agent instructions)

## AI Dev Team

Multi-agent workflow tool using:
- **Claude (Planner)** - Feature planning and architecture
- **Qwen 14B via Ollama (Executor)** - Code implementation
- **GitHub Copilot (Reviewer)** - Manual review step

### Usage

```bash
cd ai-dev-team

# Setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with ANTHROPIC_API_KEY, OLLAMA_BASE_URL, etc.

# Run
python main.py "add user authentication with JWT"
```

**Note:** This is a standalone tool, not part of the network-health-checker deployment.

## Custom Copilot Agents

Located in `.github/agents/`:

- **fastapi-app-generator** - Scaffold new FastAPI projects
- **react-app-generator** - Scaffold new React projects  
- **gsoc-scan-analyzer** - Analyze GSOC security scan results

Invoke via the Task tool when users request relevant scaffolding or analysis.

## MCP Skills

Located in `.github/skills/`:

- **mcp-client** - MCP server discovery and tool catalog loading (auto-loaded)
- **comprehensive_search** - Hybrid search across ING SCS docs
- **ing-specific-topics** - Retrieve ING SCS topic documentation
- **list_file_types** - Discover available file types for search

## Key Conventions

### Python Version

All Python projects use **Python 3.11** explicitly.

### Async Patterns

The network-health-checker uses async throughout:
- Service functions are `async def`
- HTTP calls use `httpx.AsyncClient`
- Tests use `pytest-asyncio` where needed (but `TestClient` is sync)

### Import Order

Follow standard Python convention:
1. Standard library
2. Third-party packages
3. Local app imports

### Error Handling in Services

Network check services catch specific exceptions and return structured response models with `ok=False` rather than raising exceptions to route handlers.

Example:
```python
try:
    async with httpx.AsyncClient(...) as client:
        response = await client.get(url)
except httpx.HTTPError as exc:
    return HttpCheckResponse(ok=False, detail=f"Check failed: {exc}")
```

### Validation

Use Pydantic validators for:
- Port ranges (1-65535)
- DNS record types (only A and AAAA)
- Timeout bounds (0.5-30.0 seconds)
- URL schemes

Return 422 for validation errors automatically via FastAPI.

## Common Tasks

### Add a new check endpoint

1. Define request/response models in `app/schemas/checks.py`
2. Implement async check logic in `app/services/network_checks.py`
3. Add route handler in `app/api/routes/network_checks.py`
4. Add tests in `tests/test_network_checks.py`
5. Update `network-health-checker/README.md` with endpoint docs
6. Update `network-health-checker/AGENTS.md` with behavior notes

### Modify existing check behavior

1. Update service function in `app/services/network_checks.py`
2. Update tests to cover new behavior
3. If schema changes, update `app/schemas/checks.py`
4. Update documentation if behavior is externally visible

### Add new configuration setting

1. Add field to `Settings` class in `app/core/config.py`
2. Update `.env.example` with example value
3. Document in README if user-facing
4. Update Helm values if needed for deployment

## Azure Pipeline Integration

The network-health-checker uses ING Autobahn templates. If modifying:

**Image name/tag:**
- Update `azure-pipelines/shared-variables.yml`
- Update `helm/values.yaml` imageName

**Release name:**
- Update all references to `network-check-backend`
- Update `azure-pipelines/deploy-backend.yml`

**Build process:**
- Dockerfile changes auto-picked up by `azure-pipelines/build.yml`
- Helm changes auto-packaged as artifact
