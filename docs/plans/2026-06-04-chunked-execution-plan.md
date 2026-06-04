# Chunked Execution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add chunked execution mode to the AI dev team workflow so Qwen 14B receives small, focused prompts instead of one massive task.

**Architecture:** One Claude planning call produces a full plan structured into predefined sections. Then Qwen executes each section independently as a separate CrewAI Crew run. Files written in earlier chunks are listed in later chunk prompts so imports resolve correctly.

**Tech Stack:** Python 3.11, CrewAI, existing agents.py/tools.py (unchanged)

---

### Task 1: Add CHUNK_TEMPLATES data structure to tasks.py

**Files:**
- Modify: `ai-dev-team/tasks.py:1-11` (add after imports, before `detect_template`)

**Step 1: Add the chunk templates dictionary**

Insert this block between line 10 (`from agents import planner, executor, analyzer`) and line 13 (`def detect_template`):

```python
# ─── Chunk Templates ─────────────────────────────────────────────────────────
# Predefined chunk sequences for large scaffold tasks.
# Each chunk is a focused sub-task that Qwen can complete without truncating.

CHUNK_TEMPLATES = {
    "react-scaffold": {
        "template_name": "react-app-generator",
        "trigger_keywords": [
            "scaffold", "full frontend", "create frontend",
            "all components", "complete frontend", "entire frontend",
            "frontend scaffold",
        ],
        "chunks": [
            {
                "label": "Types & Services",
                "description": "Create TypeScript interfaces matching Pydantic schemas and the Axios API service layer",
                "target_files": [
                    "frontend/src/types/api.ts",
                    "frontend/src/services/api.ts",
                ],
            },
            {
                "label": "Hooks",
                "description": "Create all React Query hooks for API calls",
                "target_files": [
                    "frontend/src/hooks/useHttpCheck.ts",
                    "frontend/src/hooks/useEgressCheck.ts",
                    "frontend/src/hooks/useDnsCheck.ts",
                    "frontend/src/hooks/useTcpCheck.ts",
                    "frontend/src/hooks/useHealth.ts",
                ],
            },
            {
                "label": "Components",
                "description": "Create reusable UI components",
                "target_files": [
                    "frontend/src/components/CheckForm/CheckForm.tsx",
                    "frontend/src/components/ResultCard/ResultCard.tsx",
                    "frontend/src/components/StatusBadge/StatusBadge.tsx",
                    "frontend/src/components/LatencyBadge/LatencyBadge.tsx",
                    "frontend/src/components/ErrorBoundary/ErrorBoundary.tsx",
                ],
            },
            {
                "label": "Pages",
                "description": "Create page components with routing",
                "target_files": [
                    "frontend/src/pages/Dashboard.tsx",
                    "frontend/src/pages/HttpCheck.tsx",
                    "frontend/src/pages/EgressCheck.tsx",
                    "frontend/src/pages/DnsCheck.tsx",
                    "frontend/src/pages/TcpCheck.tsx",
                    "frontend/src/pages/Health.tsx",
                ],
            },
            {
                "label": "Config & Entry",
                "description": "Create project configuration files and app entry point",
                "target_files": [
                    "frontend/package.json",
                    "frontend/vite.config.ts",
                    "frontend/tsconfig.json",
                    "frontend/tailwind.config.ts",
                    "frontend/.env.example",
                    "frontend/src/App.tsx",
                    "frontend/src/main.tsx",
                ],
            },
        ],
    },
    "fastapi-scaffold": {
        "template_name": "fastapi-app-generator",
        "trigger_keywords": [
            "scaffold", "full backend", "create backend",
            "all endpoints", "complete backend", "entire backend",
            "backend scaffold",
        ],
        "chunks": [
            {
                "label": "Schemas",
                "description": "Create Pydantic v2 request/response models",
                "target_files": [
                    "backend/app/schemas/checks.py",
                    "backend/app/schemas/health.py",
                ],
            },
            {
                "label": "Services",
                "description": "Create async service functions using httpx.AsyncClient",
                "target_files": [
                    "backend/app/services/network_checks.py",
                ],
            },
            {
                "label": "Routes & Config",
                "description": "Create route handlers, router wiring, config, and app entry",
                "target_files": [
                    "backend/app/api/routes/health.py",
                    "backend/app/api/routes/network_checks.py",
                    "backend/app/api/router.py",
                    "backend/app/core/config.py",
                    "backend/app/main.py",
                ],
            },
            {
                "label": "Tests & Docs",
                "description": "Create tests and update documentation",
                "target_files": [
                    "backend/tests/test_health.py",
                    "backend/tests/test_network_checks.py",
                    "backend/README.md",
                    "backend/AGENTS.md",
                ],
            },
        ],
    },
}
```

**Step 2: Verify no syntax errors**

Run: `cd /Users/zeus/Documents/ai-agent-workflow/ai-dev-team && python -c "from tasks import CHUNK_TEMPLATES; print(len(CHUNK_TEMPLATES))"`
Expected: `2`

**Step 3: Commit**

```bash
git add ai-dev-team/tasks.py
git commit -m "feat: add CHUNK_TEMPLATES for react and fastapi scaffolds"
```

---

### Task 2: Add detect_chunk_template() to tasks.py

**Files:**
- Modify: `ai-dev-team/tasks.py` (add new function after `CHUNK_TEMPLATES`, before `detect_template`)

**Step 1: Write the test**

Create file `ai-dev-team/tests/test_chunking.py`:

```python
"""Tests for chunked execution logic."""

import sys
import os

# Add parent dir to path so we can import from ai-dev-team/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_detect_chunk_template_react_scaffold():
    from tasks import detect_chunk_template
    result = detect_chunk_template("create the full frontend scaffold")
    assert result is not None
    assert result["template_name"] == "react-app-generator"
    assert len(result["chunks"]) == 5


def test_detect_chunk_template_fastapi_scaffold():
    from tasks import detect_chunk_template
    result = detect_chunk_template("scaffold the complete backend API")
    assert result is not None
    assert result["template_name"] == "fastapi-app-generator"
    assert len(result["chunks"]) == 4


def test_detect_chunk_template_returns_none_for_small_tasks():
    from tasks import detect_chunk_template
    result = detect_chunk_template("add StatusBadge component")
    assert result is None


def test_detect_chunk_template_returns_none_for_single_endpoint():
    from tasks import detect_chunk_template
    result = detect_chunk_template("add a UDP check endpoint")
    assert result is None
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zeus/Documents/ai-agent-workflow && python -m pytest ai-dev-team/tests/test_chunking.py -v`
Expected: FAIL with `ImportError` or `cannot import name 'detect_chunk_template'`

**Step 3: Write the implementation**

Add this function to `ai-dev-team/tasks.py` after `CHUNK_TEMPLATES`, before `detect_template`:

```python
def detect_chunk_template(feature_request: str) -> dict | None:
    """
    Check if a feature request matches a chunk template for multi-pass execution.

    Scans the feature request for trigger keywords from each template.
    Returns the matching template dict, or None if the task is small enough
    for single-pass execution.

    Args:
        feature_request: The user's feature description

    Returns:
        The matching CHUNK_TEMPLATES entry, or None
    """
    feature_lower = feature_request.lower()

    for template in CHUNK_TEMPLATES.values():
        if any(kw in feature_lower for kw in template["trigger_keywords"]):
            return template

    return None
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/zeus/Documents/ai-agent-workflow && python -m pytest ai-dev-team/tests/test_chunking.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add ai-dev-team/tasks.py ai-dev-team/tests/test_chunking.py
git commit -m "feat: add detect_chunk_template() with keyword matching"
```

---

### Task 3: Add extract_plan_section() to main.py

**Files:**
- Modify: `ai-dev-team/main.py` (add new function after `extract_and_write_files`, before `print_copilot_review_reminder`)

**Step 1: Write the test**

Append to `ai-dev-team/tests/test_chunking.py`:

```python
def test_extract_plan_section_finds_section():
    from main import extract_plan_section
    plan = """
## Section 1 — Types & Services
Create TypeScript interfaces for all API types.
Files: src/types/api.ts, src/services/api.ts

## Section 2 — Hooks
Create React Query hooks for each endpoint.
Files: src/hooks/useHttpCheck.ts

## Section 3 — Components
Create reusable UI components.
"""
    result = extract_plan_section(plan, 2, "Hooks")
    assert "React Query hooks" in result
    assert "useHttpCheck" in result
    # Should NOT contain other sections
    assert "TypeScript interfaces" not in result
    assert "reusable UI components" not in result


def test_extract_plan_section_finds_last_section():
    from main import extract_plan_section
    plan = """
## Section 1 — Types & Services
First section content.

## Section 2 — Hooks
Second section content.

## Section 3 — Components
Third and last section content.
"""
    result = extract_plan_section(plan, 3, "Components")
    assert "Third and last section" in result
    assert "First section" not in result


def test_extract_plan_section_falls_back_to_full_plan():
    from main import extract_plan_section
    plan = "This plan has no section headers at all. Just a blob of text."
    result = extract_plan_section(plan, 1, "Types & Services")
    # Should return the full plan when sections can't be parsed
    assert "blob of text" in result
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zeus/Documents/ai-agent-workflow && python -m pytest ai-dev-team/tests/test_chunking.py::test_extract_plan_section_finds_section -v`
Expected: FAIL with `ImportError` or `cannot import name 'extract_plan_section'`

**Step 3: Write the implementation**

Add this function to `ai-dev-team/main.py` after `extract_and_write_files` (after line 152), before `print_copilot_review_reminder`:

```python
def extract_plan_section(full_plan: str, section_num: int, label: str) -> str:
    """
    Extract a numbered section from Claude's structured plan.

    Looks for headers like "## Section 2 — Hooks" or "Section 2:" or just
    the label text. Returns everything between this section header and the
    next section header (or end of plan).

    Falls back to returning the full plan if sections can't be parsed.

    Args:
        full_plan: The complete plan text from Claude
        section_num: 1-based section number
        label: The section label (e.g. "Hooks")

    Returns:
        The extracted section text, or the full plan as fallback
    """
    # Try multiple header patterns Claude might use
    patterns = [
        # ## Section 2 — Hooks  or  ## Section 2 - Hooks
        rf'(?:^|\n)##?\s*Section\s+{section_num}\s*[—\-:]\s*{re.escape(label)}.*?\n(.*?)(?=\n##?\s*Section\s+\d|\Z)',
        # ## 2. Hooks  or  ## 2) Hooks
        rf'(?:^|\n)##?\s*{section_num}[.\)]\s*{re.escape(label)}.*?\n(.*?)(?=\n##?\s*\d[.\)]|\Z)',
        # Just look for the label as a heading
        rf'(?:^|\n)##?\s*{re.escape(label)}.*?\n(.*?)(?=\n##?\s|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, full_plan, re.DOTALL | re.IGNORECASE)
        if match:
            section = match.group(1).strip()
            if section:
                return section

    # Fallback — return full plan so the executor still has context
    return full_plan
```

**Step 4: Run all section tests to verify they pass**

Run: `cd /Users/zeus/Documents/ai-agent-workflow && python -m pytest ai-dev-team/tests/test_chunking.py -v -k "extract_plan_section"`
Expected: 3 passed

**Step 5: Commit**

```bash
git add ai-dev-team/main.py ai-dev-team/tests/test_chunking.py
git commit -m "feat: add extract_plan_section() for chunked plan parsing"
```

---

### Task 4: Add create_chunked_planning_task() to tasks.py

**Files:**
- Modify: `ai-dev-team/tasks.py` (add new function after `detect_chunk_template`, before `create_tasks`)

**Step 1: Write the implementation**

Add this function to `ai-dev-team/tasks.py`:

```python
def create_chunked_planning_task(
    feature_request: str,
    project_path: str,
    chunk_template: dict,
) -> Task:
    """
    Create a planning task that instructs Claude to structure its plan
    into predefined sections matching the chunk template.

    Args:
        feature_request: The user's feature description
        project_path: Absolute path to the project root
        chunk_template: A CHUNK_TEMPLATES entry with 'chunks' list

    Returns:
        A single planning Task for Claude
    """
    template_name = chunk_template["template_name"]
    is_react = template_name == "react-app-generator"

    # Build section instructions from chunks
    section_instructions = []
    for i, chunk in enumerate(chunk_template["chunks"], 1):
        files_list = "\n".join(f"      - {f}" for f in chunk["target_files"])
        section_instructions.append(
            f"    Section {i} — {chunk['label']}:\n"
            f"      {chunk['description']}\n"
            f"      Files:\n{files_list}"
        )
    sections_block = "\n\n".join(section_instructions)

    context_step = (
        "Use the ReactUIContext tool with input 'all' to read the existing "
        "React project structure, components, pages, hooks, and config."
        if is_react else
        "Use the NetworkCheckerContext tool with input 'all' to read the "
        "existing services, schemas, routes, and config."
    )

    rules = (
        "React-specific rules to follow:\n"
        "1. Use functional components and hooks exclusively — no class components\n"
        "2. TypeScript-first: define interfaces for all props, state, and API responses\n"
        "3. Follow naming: PascalCase for components, camelCase for functions/variables\n"
        "4. Separate concerns: components/, hooks/, services/, utils/, pages/\n"
        "5. Use environment variables for API base URLs and config\n"
        "6. Tests with Vitest or Jest — cover rendering, user interactions, and API calls\n"
        "7. Use ESLint + Prettier for code quality\n"
        "8. Implement error boundaries for error handling"
        if is_react else
        "FastAPI-specific rules to follow (AMIPDH):\n"
        "1. Route handlers stay thin — all logic goes in services/\n"
        "2. Service functions must be async def using httpx.AsyncClient\n"
        "3. All inputs/outputs must use Pydantic v2 models with validators\n"
        "4. Catch exceptions in services, return ok=False — never raise to route handlers\n"
        "5. Tests must use TestClient, no live internet calls\n"
        "6. Python version: 3.11\n"
        "7. Port stays 8080, base image stays ING RHEL9\n"
        "8. Flag if README.md or AGENTS.md need updating"
    )

    return Task(
        description=f"""
            You are the tech lead for the AMIPDH Network Tools monorepo at:
            {project_path}

            STEP 1 — Load project conventions:
            Use the ProjectConventions tool with input 'all' to read
            copilot-instructions.md, AGENTS.md, and README.md.

            STEP 2 — Load the Copilot agent template:
            Use the CopilotAgentTemplate tool with input '{template_name}'
            to load the scaffolding conventions and patterns.

            STEP 3 — Read existing code:
            {context_step}

            STEP 4 — Produce the implementation plan for:
            ---
            {feature_request}
            ---

            {rules}

            CRITICAL: Structure your plan into these EXACT sections, in this
            order. Use "## Section N — Label" as the heading for each.
            The executor will implement each section in a SEPARATE pass,
            so each section must be self-contained with enough detail to
            implement without seeing the other sections.

{sections_block}

            For each section, include:
            - Exact file paths to create
            - Complete type definitions / schemas / interfaces
            - Function signatures with parameter types and return types
            - Import statements needed (what to import from where)
            - Key implementation details (not pseudocode)
        """,
        agent=planner,
        expected_output=(
            f"A detailed implementation plan structured into exactly "
            f"{len(chunk_template['chunks'])} sections using "
            f"'## Section N — Label' headings, following "
            f"{'React/TypeScript' if is_react else 'AMIPDH FastAPI'} conventions."
        ),
    )
```

**Step 2: Verify it imports and runs without error**

Run: `cd /Users/zeus/Documents/ai-agent-workflow/ai-dev-team && python -c "from tasks import create_chunked_planning_task; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add ai-dev-team/tasks.py
git commit -m "feat: add create_chunked_planning_task() for sectioned plans"
```

---

### Task 5: Add create_chunk_execution_task() to tasks.py

**Files:**
- Modify: `ai-dev-team/tasks.py` (add new function after `create_chunked_planning_task`)

**Step 1: Write the implementation**

Add this function to `ai-dev-team/tasks.py`:

```python
def create_chunk_execution_task(
    chunk: dict,
    section_plan: str,
    written_so_far: list[str],
    project_path: str,
    template_name: str,
) -> Task:
    """
    Create a focused execution task for a single chunk.

    The prompt is kept small and specific — just the relevant plan section,
    the list of already-written files, and the target files for this chunk.

    Args:
        chunk: One entry from a CHUNK_TEMPLATES 'chunks' list
        section_plan: The extracted plan section for this chunk
        written_so_far: List of file paths already written in previous chunks
        project_path: Absolute path to the project root
        template_name: Which Copilot agent template to load

    Returns:
        A single execution Task for Qwen
    """
    is_react = template_name == "react-app-generator"

    target_files_list = "\n".join(f"  - {f}" for f in chunk["target_files"])

    if written_so_far:
        written_block = (
            "Files already created in previous chunks (you can import from these):\n"
            + "\n".join(f"  - {f}" for f in written_so_far)
        )
    else:
        written_block = "This is the first chunk — no files have been created yet."

    context_step = (
        "Use the ReactUIContext tool to read existing frontend code for reference."
        if is_react else
        "Use the NetworkCheckerContext tool to read existing backend code for reference."
    )

    rules = (
        "React implementation rules:\n"
        "- Use functional components with TypeScript — no class components\n"
        "- Define TypeScript interfaces for all props, state, and API types\n"
        "- Use hooks for state and side effects (useState, useEffect, custom hooks)\n"
        "- Keep components small and composable\n"
        "- Put API calls in src/services/, not inside components\n"
        "- Use environment variables for API URLs (.env)\n"
        "- Add JSDoc comments to complex components and hooks"
        if is_react else
        "FastAPI implementation rules:\n"
        "- Match the existing code style, indentation, and naming\n"
        "- Use async def for all service functions\n"
        "- Use Pydantic v2 models (model_config, field validators)\n"
        "- Handle exceptions with try/except, return ok=False responses\n"
        "- Add clear docstrings to all functions and classes\n"
        "- Follow import order: stdlib, third-party, local"
    )

    return Task(
        description=f"""
            You are implementing one focused section of a larger feature for:
            {project_path}

            SECTION: {chunk['label']}
            GOAL: {chunk['description']}

            STEP 1 — Load the Copilot agent template:
            Use the CopilotAgentTemplate tool with input '{template_name}'

            STEP 2 — Read existing code:
            {context_step}

            STEP 3 — Review the plan for this section:
            ---
            {section_plan}
            ---

            {written_block}

            {rules}

            STEP 4 — Implement EXACTLY these files:
{target_files_list}

            CRITICAL OUTPUT FORMAT — you MUST follow this exactly:
            For every file, output it like this:

            ### relative/path/to/file.ext
            ```language
            ...full file contents here...
            ```

            Output ALL files listed above. Do not summarize or skip any file.
            Do not say "I would create..." — actually output the full contents.
            Each file must be COMPLETE — no placeholders, no "// TODO", no
            "continue similarly". Every function body must be fully implemented.
        """,
        agent=executor,
        expected_output=(
            f"Complete implementation of: {', '.join(chunk['target_files'])}. "
            f"Each file formatted as ### path followed by a code fence with "
            f"full contents. No placeholders or stubs."
        ),
    )
```

**Step 2: Verify it imports and runs without error**

Run: `cd /Users/zeus/Documents/ai-agent-workflow/ai-dev-team && python -c "from tasks import create_chunk_execution_task; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add ai-dev-team/tasks.py
git commit -m "feat: add create_chunk_execution_task() for focused Qwen prompts"
```

---

### Task 6: Add --chunked and --no-chunk CLI flags to main.py

**Files:**
- Modify: `ai-dev-team/main.py:21-40` (the `parse_args` function)

**Step 1: Add the flags**

Add two new arguments to `parse_args()`, after the `--gsoc` argument (after line 39):

```python
    parser.add_argument(
        "--chunked",
        action="store_true",
        help="Force chunked execution (split into smaller passes for Qwen)",
    )
    parser.add_argument(
        "--no-chunk",
        action="store_true",
        help="Disable chunked execution (single-pass, even for large tasks)",
    )
```

**Step 2: Verify flags parse correctly**

Run: `cd /Users/zeus/Documents/ai-agent-workflow/ai-dev-team && python main.py --help`
Expected: Output includes `--chunked` and `--no-chunk` in the help text

**Step 3: Commit**

```bash
git add ai-dev-team/main.py
git commit -m "feat: add --chunked and --no-chunk CLI flags"
```

---

### Task 7: Add run_chunked_feature() to main.py

**Files:**
- Modify: `ai-dev-team/main.py` (add new function after `run_feature`, before `run_gsoc`)

**Step 1: Write the implementation**

Add this function to `ai-dev-team/main.py`:

```python
def run_chunked_feature(feature_request: str, project_path: str, chunk_template: dict):
    """Run the chunked planner → multi-pass executor workflow.

    Phase 1: Claude plans the entire feature in one call, structured into sections.
    Phase 2: Qwen executes each section independently with a focused prompt.
    """
    from agents import planner, executor
    from tasks import create_chunked_planning_task, create_chunk_execution_task

    template_name = chunk_template["template_name"]
    chunks = chunk_template["chunks"]
    total_chunks = len(chunks)

    print(f"\n🚀 AI Dev Team — Chunked Mode ({total_chunks} chunks)")
    print(f"   Project  : {project_path}")
    print(f"   Feature  : {feature_request[:80]}{'...' if len(feature_request) > 80 else ''}")
    print(f"   Template : {template_name}")
    print(f"   Chunks   :")
    for i, chunk in enumerate(chunks, 1):
        print(f"     {i}. {chunk['label']} ({len(chunk['target_files'])} files)")

    # ── Phase 1: Claude plans everything ─────────────────────────────────
    print(f"\n{'─' * 50}")
    print("📋 Phase 1: Claude is planning all sections...")
    print(f"{'─' * 50}\n")

    planning_task = create_chunked_planning_task(
        feature_request, project_path, chunk_template
    )

    planning_crew = Crew(
        agents=[planner],
        tasks=[planning_task],
        process=Process.sequential,
        verbose=True,
    )

    plan_result = planning_crew.kickoff()
    full_plan = str(plan_result.raw) if hasattr(plan_result, "raw") else str(plan_result)

    # Save the full plan for reference
    plan_path = os.path.join(project_path, "ai-dev-team-plan.md")
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(f"# AI Dev Team Plan\n\n{full_plan}")
    print(f"\n   📄 Full plan saved to: {plan_path}")

    # ── Phase 2: Qwen executes each chunk ────────────────────────────────
    all_written = []

    for i, chunk in enumerate(chunks, 1):
        print(f"\n{'─' * 50}")
        print(f"🔨 Phase 2 — Chunk {i}/{total_chunks}: {chunk['label']}")
        print(f"   Target files: {', '.join(chunk['target_files'])}")
        print(f"{'─' * 50}\n")

        section_plan = extract_plan_section(full_plan, i, chunk["label"])

        exec_task = create_chunk_execution_task(
            chunk=chunk,
            section_plan=section_plan,
            written_so_far=all_written,
            project_path=project_path,
            template_name=template_name,
        )

        exec_crew = Crew(
            agents=[executor],
            tasks=[exec_task],
            process=Process.sequential,
            verbose=True,
        )

        result = exec_crew.kickoff()
        output = str(result.raw) if hasattr(result, "raw") else str(result)

        written = extract_and_write_files(output, project_path)
        all_written.extend(written)

        print(f"\n   ✅ Chunk {i}/{total_chunks}: {chunk['label']} — wrote {len(written)} files")

        if not written:
            # Save raw output for this chunk so nothing is lost
            chunk_output_path = os.path.join(
                project_path, f"ai-dev-team-chunk-{i}-output.md"
            )
            with open(chunk_output_path, "w", encoding="utf-8") as f:
                f.write(f"# Chunk {i}: {chunk['label']}\n\n{output}")
            print(f"   ⚠️  No files extracted. Raw output saved to: {chunk_output_path}")

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'═' * 50}")
    print(f"🏁 Chunked execution complete: {len(all_written)} files written")
    print(f"{'═' * 50}")
    print_copilot_review_reminder(all_written)

    return all_written
```

**Step 2: Verify it imports without error**

Run: `cd /Users/zeus/Documents/ai-agent-workflow/ai-dev-team && python -c "from main import run_chunked_feature; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add ai-dev-team/main.py
git commit -m "feat: add run_chunked_feature() chunked execution loop"
```

---

### Task 8: Update main() routing to use chunked mode

**Files:**
- Modify: `ai-dev-team/main.py` (the `main` function — the routing logic at the end)

**Step 1: Update the main function**

Replace the feature-mode branch in `main()`. The current code (approximately lines 279-284) is:

```python
    else:
        feature_request = get_feature_request(args.feature)
        if not feature_request:
            print("❌ No feature request provided.")
            sys.exit(1)
        run_feature(feature_request, project_path)
```

Replace with:

```python
    else:
        feature_request = get_feature_request(args.feature)
        if not feature_request:
            print("❌ No feature request provided.")
            sys.exit(1)

        # Determine execution mode: chunked vs single-pass
        from tasks import detect_chunk_template

        if args.no_chunk:
            # User explicitly disabled chunking
            chunk_template = None
        elif args.chunked:
            # User forced chunking — detect which template
            chunk_template = detect_chunk_template(feature_request)
            if not chunk_template:
                print("⚠️  --chunked flag used but no matching chunk template found.")
                print("   Falling back to single-pass execution.")
        else:
            # Auto-detect: chunk only if the request matches a template
            chunk_template = detect_chunk_template(feature_request)

        if chunk_template:
            run_chunked_feature(feature_request, project_path, chunk_template)
        else:
            run_feature(feature_request, project_path)
```

**Step 2: Verify the full CLI works**

Run: `cd /Users/zeus/Documents/ai-agent-workflow/ai-dev-team && python main.py --help`
Expected: Help text shows all flags including `--chunked` and `--no-chunk`

Run: `cd /Users/zeus/Documents/ai-agent-workflow/ai-dev-team && python -c "from main import main; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add ai-dev-team/main.py
git commit -m "feat: wire chunked execution into main() routing"
```

---

### Task 9: Update module docstrings

**Files:**
- Modify: `ai-dev-team/main.py:1-9` (module docstring)
- Modify: `ai-dev-team/tasks.py:1-7` (module docstring)

**Step 1: Update main.py docstring**

Replace lines 1-9 with:

```python
"""
main.py — Entry point for the AI Dev Team workflow

Usage:
    python main.py "add a TCP proxy check endpoint"
    python main.py "add shopping cart" --project /path/to/project
    python main.py --gsoc                        (run GSOC scan analysis)
    python main.py --chunked "create full frontend scaffold"
    python main.py --no-chunk "create full frontend scaffold"
    python main.py                               (interactive mode)

Chunked mode splits large tasks into focused sub-tasks for Qwen 14B.
Auto-detected for scaffold tasks, or forced with --chunked/--no-chunk.
"""
```

**Step 2: Update tasks.py docstring**

Replace lines 1-7 with:

```python
"""
tasks.py — Task definitions for the AI Dev Team workflow

Tasks:
  - create_tasks                : planning + execution for single-pass features
  - create_chunked_planning_task: planning for multi-pass chunked execution
  - create_chunk_execution_task : execution for one chunk of a larger task
  - create_gsoc_tasks           : GSOC security scan analysis

Data:
  - CHUNK_TEMPLATES             : predefined chunk sequences for scaffold tasks
"""
```

**Step 3: Commit**

```bash
git add ai-dev-team/main.py ai-dev-team/tasks.py
git commit -m "docs: update module docstrings for chunked execution"
```

---

### Task 10: Run all tests and verify

**Files:**
- Test: `ai-dev-team/tests/test_chunking.py`

**Step 1: Run the full test suite**

Run: `cd /Users/zeus/Documents/ai-agent-workflow && python -m pytest ai-dev-team/tests/test_chunking.py -v`
Expected: All 7 tests pass (4 detect tests + 3 extract tests)

**Step 2: Verify CLI end-to-end (dry check, no API call)**

Run: `cd /Users/zeus/Documents/ai-agent-workflow/ai-dev-team && python -c "
from tasks import detect_chunk_template, CHUNK_TEMPLATES
# Verify react scaffold detection
t = detect_chunk_template('create the full frontend scaffold')
assert t is not None
assert t['template_name'] == 'react-app-generator'
assert len(t['chunks']) == 5
print('react-scaffold: OK')

# Verify fastapi scaffold detection
t = detect_chunk_template('scaffold the complete backend')
assert t is not None
assert len(t['chunks']) == 4
print('fastapi-scaffold: OK')

# Verify small tasks are NOT chunked
t = detect_chunk_template('add StatusBadge component')
assert t is None
print('small-task: OK (not chunked)')

print('All checks passed')
"`
Expected: All checks pass

**Step 3: Final commit**

```bash
git add -A
git commit -m "test: verify chunked execution integration"
```

---

## Summary of All Files Changed

| File | Action | What Changed |
|------|--------|-------------|
| `ai-dev-team/tasks.py` | Modified | Added CHUNK_TEMPLATES, detect_chunk_template(), create_chunked_planning_task(), create_chunk_execution_task(), updated docstring |
| `ai-dev-team/main.py` | Modified | Added --chunked/--no-chunk flags, extract_plan_section(), run_chunked_feature(), updated main() routing, updated docstring |
| `ai-dev-team/tests/test_chunking.py` | Created | 7 tests for detect_chunk_template and extract_plan_section |

## Files NOT Changed

| File | Reason |
|------|--------|
| `ai-dev-team/agents.py` | No changes needed — same planner/executor agents |
| `ai-dev-team/tools.py` | No changes needed — same tools |
| `ai-dev-team/parse_output.py` | No changes needed — still works as fallback |
