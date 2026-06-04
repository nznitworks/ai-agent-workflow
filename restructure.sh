#!/bin/bash

# ─────────────────────────────────────────────────────────────────
#  AMIPDH Network Tools — Monorepo Restructure Script
#  
#  What this does:
#    - Renames network-health-checker/ → backend/
#    - Creates frontend/ folder
#    - Updates all internal path references
#    - Updates copilot-instructions.md
#    - Updates ai-dev-team/ tools and tasks
#
#  Usage:
#    chmod +x restructure.sh
#    ./restructure.sh
#
#  Run from the ROOT of your monorepo (AMIPDH-network-tools/)
# ─────────────────────────────────────────────────────────────────

set -e  # exit on any error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# ─── Helpers ──────────────────────────────────────────────────────

log()     { echo -e "${GREEN}✅ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $1${NC}"; }
error()   { echo -e "${RED}❌ $1${NC}"; exit 1; }
section() { echo -e "\n${BLUE}── $1 ──────────────────────────────${NC}"; }

# ─── Pre-flight checks ────────────────────────────────────────────

section "Pre-flight checks"

# Must be run from repo root
if [ ! -d ".github" ]; then
    error "Run this script from the ROOT of your monorepo (where .github/ is)"
fi

# network-health-checker must exist
if [ ! -d "network-health-checker" ]; then
    error "network-health-checker/ folder not found. Are you in the right directory?"
fi

# backend/ must not already exist
if [ -d "backend" ]; then
    error "backend/ folder already exists. Rename or remove it first."
fi

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    warn "You have uncommitted changes. It's recommended to commit them first."
    read -p "   Continue anyway? (y/N): " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "Aborted."
        exit 0
    fi
fi

log "Pre-flight checks passed"

# ─── Step 1: Rename backend folder ────────────────────────────────

section "Step 1: Rename network-health-checker → backend"

git mv network-health-checker backend
log "Renamed network-health-checker/ → backend/"

# ─── Step 2: Create frontend folder ───────────────────────────────

section "Step 2: Create frontend/ folder"

mkdir -p frontend
# Add a placeholder so git tracks the folder
cat > frontend/.gitkeep << 'EOF'
# React frontend will be scaffolded here
# Run the ai-dev-team agent to scaffold the UI
EOF

git add frontend/.gitkeep
log "Created frontend/ folder"

# ─── Step 3: Update copilot-instructions.md ───────────────────────

section "Step 3: Update .github/copilot-instructions.md"

COPILOT_FILE=".github/copilot-instructions.md"

if [ -f "$COPILOT_FILE" ]; then
    # Replace all references
    sed -i '' \
        -e 's|network-health-checker/|backend/|g' \
        -e 's|network-health-checker-ui/|frontend/|g' \
        -e 's|network-health-checker\b|backend|g' \
        "$COPILOT_FILE"
    git add "$COPILOT_FILE"
    log "Updated $COPILOT_FILE"
else
    warn "$COPILOT_FILE not found — skipping"
fi

# ─── Step 4: Update backend AGENTS.md ─────────────────────────────

section "Step 4: Update backend/AGENTS.md"

AGENTS_FILE="backend/AGENTS.md"

if [ -f "$AGENTS_FILE" ]; then
    sed -i '' \
        -e 's|network-health-checker/|backend/|g' \
        -e 's|network-health-checker-ui/|frontend/|g' \
        -e 's|network-health-checker\b|backend|g' \
        "$AGENTS_FILE"
    git add "$AGENTS_FILE"
    log "Updated $AGENTS_FILE"
else
    warn "$AGENTS_FILE not found — skipping"
fi

# ─── Step 5: Update backend README.md ─────────────────────────────

section "Step 5: Update backend/README.md"

BACKEND_README="backend/README.md"

if [ -f "$BACKEND_README" ]; then
    sed -i '' \
        -e 's|network-health-checker/|backend/|g' \
        -e 's|network-health-checker\b|backend|g' \
        "$BACKEND_README"
    git add "$BACKEND_README"
    log "Updated $BACKEND_README"
else
    warn "$BACKEND_README not found — skipping"
fi

# ─── Step 6: Update Azure Pipelines ──────────────────────────────

section "Step 6: Update azure-pipelines/"

PIPELINES_DIR="backend/azure-pipelines"

if [ -d "$PIPELINES_DIR" ]; then
    find "$PIPELINES_DIR" -name "*.yml" -o -name "*.yaml" | while read -r file; do
        sed -i '' \
            -e 's|network-health-checker/|backend/|g' \
            -e 's|network-health-checker\b|backend|g' \
            "$file"
        git add "$file"
        log "Updated $file"
    done
else
    warn "$PIPELINES_DIR not found — skipping"
fi

# ─── Step 7: Update Helm values ───────────────────────────────────

section "Step 7: Update Helm chart"

HELM_DIR="backend/helm"

if [ -d "$HELM_DIR" ]; then
    find "$HELM_DIR" -name "*.yml" -o -name "*.yaml" | while read -r file; do
        sed -i '' \
            -e 's|network-health-checker/|backend/|g' \
            -e 's|network-health-checker\b|backend|g' \
            "$file"
        git add "$file"
        log "Updated $file"
    done
else
    warn "$HELM_DIR not found — skipping"
fi

# ─── Step 8: Update Dockerfile ────────────────────────────────────

section "Step 8: Update backend/Dockerfile"

DOCKERFILE="backend/Dockerfile"

if [ -f "$DOCKERFILE" ]; then
    sed -i '' \
        -e 's|network-health-checker/|backend/|g' \
        -e 's|network-health-checker\b|backend|g' \
        "$DOCKERFILE"
    git add "$DOCKERFILE"
    log "Updated $DOCKERFILE"
else
    warn "$DOCKERFILE not found — skipping"
fi

# ─── Step 9: Update ai-dev-team/tools.py ─────────────────────────

section "Step 9: Update ai-dev-team/tools.py"

TOOLS_FILE="ai-dev-team/tools.py"

if [ -f "$TOOLS_FILE" ]; then
    sed -i '' \
        -e 's|network-health-checker-ui|frontend|g' \
        -e 's|network-health-checker|backend|g' \
        "$TOOLS_FILE"
    git add "$TOOLS_FILE"
    log "Updated $TOOLS_FILE"
else
    warn "$TOOLS_FILE not found — skipping"
fi

# ─── Step 10: Update ai-dev-team/tasks.py ────────────────────────

section "Step 10: Update ai-dev-team/tasks.py"

TASKS_FILE="ai-dev-team/tasks.py"

if [ -f "$TASKS_FILE" ]; then
    sed -i '' \
        -e 's|network-health-checker-ui|frontend|g' \
        -e 's|network-health-checker|backend|g' \
        "$TASKS_FILE"
    git add "$TASKS_FILE"
    log "Updated $TASKS_FILE"
else
    warn "$TASKS_FILE not found — skipping"
fi

# ─── Step 11: Update ai-dev-team/README.md ───────────────────────

section "Step 11: Update ai-dev-team/README.md"

AI_README="ai-dev-team/README.md"

if [ -f "$AI_README" ]; then
    sed -i '' \
        -e 's|network-health-checker-ui|frontend|g' \
        -e 's|network-health-checker|backend|g' \
        "$AI_README"
    git add "$AI_README"
    log "Updated $AI_README"
else
    warn "$AI_README not found — skipping"
fi

# ─── Step 12: Update ai-dev-team/.env.example ────────────────────

section "Step 12: Update ai-dev-team/.env.example"

ENV_EXAMPLE="ai-dev-team/.env.example"

if [ -f "$ENV_EXAMPLE" ]; then
    sed -i '' \
        -e 's|network-health-checker|backend|g' \
        "$ENV_EXAMPLE"
    git add "$ENV_EXAMPLE"
    log "Updated $ENV_EXAMPLE"
else
    warn "$ENV_EXAMPLE not found — skipping"
fi

# ─── Step 13: Commit everything ──────────────────────────────────

section "Step 13: Git commit"

git add -A

git commit -m "refactor: restructure monorepo — rename network-health-checker to backend, add frontend folder

- network-health-checker/ → backend/
- Created frontend/ placeholder for React UI
- Updated all path references in:
  - .github/copilot-instructions.md
  - backend/AGENTS.md
  - backend/README.md
  - backend/azure-pipelines/
  - backend/helm/
  - backend/Dockerfile
  - ai-dev-team/tools.py
  - ai-dev-team/tasks.py
  - ai-dev-team/README.md
  - ai-dev-team/.env.example"

log "Committed all changes"

# ─── Done ─────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ Restructure complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  New structure:"
echo "  ├── backend/          ← was network-health-checker/"
echo "  ├── frontend/         ← ready for React scaffold"
echo "  ├── ai-dev-team/      ← updated paths"
echo "  ├── ansible-local-testing/"
echo "  └── .github/"
echo ""
echo "  Next steps:"
echo "  1. Verify backend still runs:"
echo "     cd backend && python3.11 -m uvicorn app.main:app --reload"
echo ""
echo "  2. Run backend tests:"
echo "     cd backend && pytest -q"
echo ""
echo "  3. Scaffold the React frontend:"
echo "     cd ai-dev-team && python main.py \"scaffold React UI for network health checker\""
echo ""
