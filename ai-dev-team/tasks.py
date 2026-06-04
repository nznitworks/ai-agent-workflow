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

from crewai import Task
from agents import planner, executor, analyzer

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


def detect_chunk_template(feature_request: str) -> dict | None:
    """
    Check if a feature request matches a chunk template for multi-pass execution.

    Scans the feature request for trigger keywords from each template.
    When multiple templates match (e.g. both share a generic keyword like
    "scaffold"), the template with the most keyword hits wins.
    Returns the matching template dict, or None if the task is small enough
    for single-pass execution.

    Args:
        feature_request: The user's feature description

    Returns:
        The matching CHUNK_TEMPLATES entry, or None
    """
    feature_lower = feature_request.lower()

    best_match = None
    best_score = 0

    for template in CHUNK_TEMPLATES.values():
        score = sum(1 for kw in template["trigger_keywords"] if kw in feature_lower)
        if score > best_score:
            best_score = score
            best_match = template

    return best_match


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


def detect_template(feature_request: str) -> str:
    """
    Auto-detect which Copilot agent template is relevant
    based on keywords in the feature request.

    React triggers:
        react, frontend, ui, component, page, dashboard, vite,
        next.js, nextjs, typescript tsx, tailwind, zustand, redux,
        vitest, jest (frontend context), spa, pwa, routing

    FastAPI triggers (default):
        fastapi, backend, api, endpoint, route, service, schema,
        pydantic, async, httpx, pytest, helm, kubernetes, check,
        health, dns, tcp, http, egress, network
    """
    feature_lower = feature_request.lower()

    react_keywords = [
        "react", "frontend", "ui", "component", "page", "dashboard",
        "vite", "next.js", "nextjs", "tsx", "tailwind", "zustand",
        "redux", "spa", "pwa", "navbar", "sidebar", "modal", "table",
        "form", "chart", "widget", "layout", "styled", "css module",
    ]

    if any(k in feature_lower for k in react_keywords):
        return "react-app-generator"

    # Default to FastAPI for all backend/network checker work
    return "fastapi-app-generator"


def create_tasks(feature_request: str, project_path: str) -> list[Task]:
    """
    Create planning and execution tasks for a feature request.

    Args:
        feature_request: Description of the feature to implement
        project_path: Absolute path to the project root

    Returns:
        [planning_task, execution_task]
    """

    template_name = detect_template(feature_request)

    planning_task = Task(
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
            {"Use the ReactUIContext tool with input 'all' to read the existing React project structure, components, pages, hooks, and config." if template_name == "react-app-generator" else "Use the NetworkCheckerContext tool with input 'all' to read the existing services, schemas, routes, and config."}

            STEP 4 — Produce the implementation plan for:
            ---
            {feature_request}
            ---

            {"React-specific rules to follow:" if template_name == "react-app-generator" else "FastAPI-specific rules to follow (AMIPDH):"}
            {"1. Use functional components and hooks exclusively — no class components" if template_name == "react-app-generator" else "1. Route handlers stay thin — all logic goes in services/"}
            {"2. TypeScript-first: define interfaces for all props, state, and API responses" if template_name == "react-app-generator" else "2. Service functions must be async def using httpx.AsyncClient"}
            {"3. Follow naming: PascalCase for components, camelCase for functions/variables" if template_name == "react-app-generator" else "3. All inputs/outputs must use Pydantic v2 models with validators"}
            {"4. Separate concerns: components/, hooks/, services/, utils/, pages/" if template_name == "react-app-generator" else "4. Catch exceptions in services, return ok=False — never raise to route handlers"}
            {"5. Use environment variables for API base URLs and config" if template_name == "react-app-generator" else "5. Tests must use TestClient, no live internet calls"}
            {"6. Tests with Vitest or Jest — cover rendering, user interactions, and API calls" if template_name == "react-app-generator" else "6. Python version: 3.11"}
            {"7. Use ESLint + Prettier for code quality" if template_name == "react-app-generator" else "7. Port stays 8080, base image stays ING RHEL9"}
            {"8. Implement error boundaries for error handling" if template_name == "react-app-generator" else "8. Flag if README.md or AGENTS.md need updating"}

            Your plan must include:
            1. Summary of the approach
            2. Files to create or modify (full paths)
            {"3. TypeScript interfaces and component prop types" if template_name == "react-app-generator" else "3. Exact Pydantic v2 schema definitions (request + response)"}
            {"4. Component hierarchy and data flow" if template_name == "react-app-generator" else "4. Async service function signatures"}
            {"5. Custom hooks to create (if any)" if template_name == "react-app-generator" else "5. Route handler structure"}
            {"6. API service calls and state management approach" if template_name == "react-app-generator" else "6. Test cases (happy path + edge cases + 422 validation errors)"}
            {"7. Test cases (rendering + interaction + API mocking)" if template_name == "react-app-generator" else "7. Any Helm or pipeline changes required"}
            8. Documentation files to update
        """,
        agent=planner,
        expected_output=(
            f"A detailed, numbered implementation plan following "
            f"{'React/TypeScript' if template_name == 'react-app-generator' else 'AMIPDH FastAPI'} "
            f"conventions, with file paths, "
            f"{'TypeScript interfaces, component hierarchy, and test cases.' if template_name == 'react-app-generator' else 'async service signatures, Pydantic v2 schema definitions, and explicit test cases.'}"
        ),
    )

    execution_task = Task(
        description=f"""
            You are the senior developer implementing a feature for:
            {project_path}

            STEP 1 — Load the Copilot agent template:
            Use the CopilotAgentTemplate tool with input '{template_name}'
            to load the scaffolding patterns and use them as your reference.

            STEP 2 — Read existing code for each file you will modify:
            {"Use the ReactUIContext tool to read existing components, pages, hooks, and config before making changes." if template_name == "react-app-generator" else "Use the NetworkCheckerContext tool or FileRead tool to read existing files before modifying them."}

            STEP 3 — Implement all files from the plan:
            {"React implementation rules:" if template_name == "react-app-generator" else "FastAPI implementation rules:"}
            {"- Use functional components with TypeScript — no class components" if template_name == "react-app-generator" else "- Match the existing code style, indentation, and naming"}
            {"- Define TypeScript interfaces for all props, state, and API types" if template_name == "react-app-generator" else "- Use async def for all service functions"}
            {"- Use hooks for state and side effects (useState, useEffect, custom hooks)" if template_name == "react-app-generator" else "- Use Pydantic v2 models (model_config, field validators)"}
            {"- Keep components small and composable" if template_name == "react-app-generator" else "- Handle exceptions with try/except, return ok=False responses"}
            {"- Put API calls in src/services/, not inside components" if template_name == "react-app-generator" else "- Add clear docstrings to all functions and classes"}
            {"- Use environment variables for API URLs (.env)" if template_name == "react-app-generator" else "- Follow import order: stdlib → third-party → local"}
            {"- Add JSDoc comments to complex components and hooks" if template_name == "react-app-generator" else ""}

            STEP 4 — Write tests:
            {"- Use Vitest or Jest with React Testing Library" if template_name == "react-app-generator" else "- Use TestClient (synchronous)"}
            {"- Test rendering, user interactions, and API calls (mock fetch/axios)" if template_name == "react-app-generator" else "- Cover happy path, edge cases, and 422 validation errors"}
            {"- No real API calls in tests — mock all external services" if template_name == "react-app-generator" else "- No live internet calls — mock external dependencies"}

            CRITICAL OUTPUT FORMAT — you MUST follow this exactly:
            For every file you create or modify, output it like this:

            ### relative/path/to/file.ext
            ```language
            ...full file contents here...
            ```

            Example:
            ### frontend/src/types/api.ts
            ```typescript
            export interface HttpCheckRequest {{
              url: string
            }}
            ```

            ### frontend/package.json
            ```json
            {{
              "name": "frontend"
            }}
            ```

            Output ALL files this way. Do not summarize or skip any file.
            Do not say "I would create..." — actually output the full contents.
        """,
        agent=executor,
        expected_output=(
            f"Every file listed in the plan, each formatted as:\n"
            f"### path/to/file.ext\n"
            f"```language\n"
            f"...full file contents...\n"
            f"```\n"
            f"All files complete with no placeholders or summaries."
        ),
        context=[planning_task],
    )

    return [planning_task, execution_task]


def create_gsoc_tasks(project_path: str) -> list[Task]:
    """
    Create a GSOC security scan analysis task.

    Args:
        project_path: Absolute path to the project root

    Returns:
        [gsoc_analysis_task]
    """

    gsoc_task = Task(
        description=f"""
            You are a security analyst for the AMIPDH Network Tools project at:
            {project_path}

            STEP 1 — Load the gsoc-scan-analyzer agent instructions:
            Use the CopilotAgentTemplate tool with input 'gsoc-scan-analyzer'
            to load the analysis rules and output format requirements.

            STEP 2 — Check for existing analyzer script:
            Check if this file exists:
            network-health-checker-ui/backend/gsoc_scan/analyze_gsoc_scan.py
            If it exists, note it in your report.

            STEP 3 — Read all scan files:
            Use the GSocScanReader tool with input 'read' to load all
            *_VULNERABILITIES.csv and *_COMPLIANCES.csv files.

            STEP 4 — Analyze findings:
            - Include only HIGH and MEDIUM severity findings
            - Normalize severity to uppercase
            - De-duplicate by CVE + package
            - Prioritize mitigations:
                1. Upgrade to fixed version
                2. Apply vendor advisory
                3. Compensating controls if no fix available

            STEP 5 — Write the report:
            Write the markdown report to:
            network-health-checker-ui/backend/gsoc_scan/gsoc_scan_analysis.md

            Report must include:
            1. Executive summary (counts of high/medium findings)
            2. Vulnerability findings (high first, then medium)
            3. Compliance findings (high first, then medium)
            4. Recommended mitigation per finding
            5. Resource impact per finding (package + Kubernetes impact)
            6. Prioritized remediation plan
            7. Source files processed and assumptions made
        """,
        agent=analyzer,
        expected_output=(
            "A complete markdown security report written to "
            "gsoc_scan/gsoc_scan_analysis.md covering all HIGH and MEDIUM "
            "findings with mitigations and a prioritized remediation plan."
        ),
    )

    return [gsoc_task]
