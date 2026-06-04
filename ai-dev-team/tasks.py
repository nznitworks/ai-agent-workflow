"""
tasks.py — Task definitions for the AI Dev Team workflow

Tasks:
  - create_tasks      : planning + execution for feature development
  - create_gsoc_tasks : GSOC security scan analysis
"""

from crewai import Task
from agents import planner, executor, analyzer


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

            Write all files directly to the project directory.
        """,
        agent=executor,
        expected_output=(
            f"All files from the implementation plan written to disk with "
            f"{'clean TypeScript React components, hooks, services, and Vitest/Jest tests.' if template_name == 'react-app-generator' else 'clean async code, Pydantic v2 models, and pytest test cases.'}"
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
