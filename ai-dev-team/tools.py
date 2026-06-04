"""
tools.py — Custom CrewAI tools for the AI Dev Team workflow

Tools:
  - CopilotAgentTemplateTool : reads .github/agents/ templates as context
  - ProjectConventionsTool   : reads copilot-instructions.md conventions
  - GSocScanTool             : reads GSOC scan CSV files for analysis
"""

import os
from crewai.tools import BaseTool
from typing import Optional


# ─── Helper ───────────────────────────────────────────────────────────────────

def get_project_path() -> str:
    return os.getenv("PROJECT_PATH", os.getcwd())


def read_file_safe(path: str) -> str:
    """Read a file safely, returning an error string if not found."""
    if not os.path.isfile(path):
        return f"[File not found: {path}]"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ─── Tool 1: Copilot Agent Template Reader ────────────────────────────────────

class CopilotAgentTemplateTool(BaseTool):
    name: str = "CopilotAgentTemplate"
    description: str = """
        Reads a Copilot agent template from .github/agents/ in the project.
        Use this BEFORE planning or implementing to load the scaffolding
        conventions for the relevant technology.

        Available agents:
        - fastapi-app-generator  : FastAPI project structure, async patterns,
                                   Pydantic v2, pytest conventions, dependency
                                   injection, SQLAlchemy, JWT auth patterns
        - react-app-generator    : React project structure, Vite/Next.js/CRA
                                   tooling, TypeScript, functional components,
                                   hooks, routing, state management (Zustand,
                                   Redux, Context), Tailwind/CSS modules,
                                   Vitest/Jest testing, ESLint/Prettier setup
        - gsoc-scan-analyzer     : GSOC security scan analysis instructions,
                                   vulnerability/compliance CSV parsing,
                                   markdown report generation

        Input: the agent name (e.g. 'fastapi-app-generator')
        Output: full agent instructions including patterns and conventions
    """

    def _run(self, agent_name: str) -> str:
        project_path = get_project_path()

        # Try both naming conventions (with and without .agent.md)
        candidates = [
            os.path.join(project_path, ".github", "agents", agent_name),
            os.path.join(project_path, ".github", "agents", f"{agent_name}.agent.md"),
            os.path.join(project_path, ".github", "agents", f"{agent_name}_agent.md"),
        ]

        # Check if it's a directory (folder-based agent)
        for path in candidates:
            if os.path.isdir(path):
                contents = []
                for fname in sorted(os.listdir(path)):
                    fpath = os.path.join(path, fname)
                    if os.path.isfile(fpath):
                        contents.append(f"### {fname}\n{read_file_safe(fpath)}")
                if contents:
                    return f"# Copilot Agent: {agent_name}\n\n" + "\n\n".join(contents)

            # Check if it's a single file
            if os.path.isfile(path):
                return f"# Copilot Agent: {agent_name}\n\n{read_file_safe(path)}"

        return (
            f"[Agent template '{agent_name}' not found. "
            f"Checked: {', '.join(candidates)}. "
            f"Available agents: fastapi-app-generator, react-app-generator, gsoc-scan-analyzer]"
        )


# ─── Tool 2: Project Conventions Reader ───────────────────────────────────────

class ProjectConventionsTool(BaseTool):
    name: str = "ProjectConventions"
    description: str = """
        Reads the project's copilot-instructions.md and AGENTS.md files
        to understand the full project conventions, architecture rules,
        and coding standards before planning or implementing.

        Always use this at the start of any planning task to ensure
        your output follows the project's established patterns.

        Input: 'all' to read everything, or a specific file name
               like 'copilot-instructions' or 'AGENTS'
    """

    def _run(self, target: str = "all") -> str:
        project_path = get_project_path()

        files_to_read = {
            "copilot-instructions": os.path.join(
                project_path, ".github", "copilot-instructions.md"
            ),
            "AGENTS": os.path.join(
                project_path, "network-health-checker", "AGENTS.md"
            ),
            "README": os.path.join(
                project_path, "network-health-checker", "README.md"
            ),
        }

        if target == "all":
            results = []
            for name, path in files_to_read.items():
                content = read_file_safe(path)
                results.append(f"## {name}\n\n{content}")
            return "\n\n---\n\n".join(results)

        # Read specific file
        for name, path in files_to_read.items():
            if target.lower() in name.lower():
                return read_file_safe(path)

        return f"[Convention file '{target}' not found.]"


# ─── Tool 3: GSOC Scan Reader ─────────────────────────────────────────────────

class GSocScanTool(BaseTool):
    name: str = "GSocScanReader"
    description: str = """
        Reads GSOC security scan CSV files from the project's gsoc_scan folder.
        Use this when analyzing security vulnerabilities and compliance findings.

        Reads files matching:
        - *_VULNERABILITIES.csv
        - *_COMPLIANCES.csv

        Input: 'list' to see available scan files, or 'read' to read all CSV files
        Output: contents of the scan files for analysis
    """

    def _run(self, action: str = "read") -> str:
        project_path = get_project_path()
        scan_folder = os.path.join(
            project_path,
            "network-health-checker-ui", "backend", "gsoc_scan"
        )

        if not os.path.isdir(scan_folder):
            return f"[GSOC scan folder not found: {scan_folder}]"

        # List available files
        all_files = os.listdir(scan_folder)
        csv_files = [
            f for f in all_files
            if f.endswith("_VULNERABILITIES.csv") or f.endswith("_COMPLIANCES.csv")
        ]

        if not csv_files:
            return "[No GSOC scan CSV files found in gsoc_scan folder]"

        if action == "list":
            return "Available scan files:\n" + "\n".join(f"- {f}" for f in csv_files)

        # Read all CSV files
        results = []
        for fname in csv_files:
            fpath = os.path.join(scan_folder, fname)
            content = read_file_safe(fpath)
            results.append(f"### {fname}\n\n{content}")

        return "\n\n---\n\n".join(results)


# ─── Tool 4: Existing Code Reader ─────────────────────────────────────────────

class NetworkCheckerContextTool(BaseTool):
    name: str = "NetworkCheckerContext"
    description: str = """
        Reads key files from the network-health-checker project to understand
        the existing code structure before planning changes.

        Reads:
        - app/main.py
        - app/api/router.py
        - app/services/network_checks.py
        - app/schemas/checks.py
        - app/core/config.py

        Input: 'all' to read all files, or a specific file like 'services'
        Output: existing code for context
    """

    def _run(self, target: str = "all") -> str:
        project_path = get_project_path()
        base = os.path.join(project_path, "network-health-checker", "app")

        key_files = {
            "main":     os.path.join(project_path, "network-health-checker", "app", "main.py"),
            "router":   os.path.join(base, "api", "router.py"),
            "services": os.path.join(base, "services", "network_checks.py"),
            "schemas":  os.path.join(base, "schemas", "checks.py"),
            "config":   os.path.join(base, "core", "config.py"),
        }

        if target == "all":
            results = []
            for name, path in key_files.items():
                content = read_file_safe(path)
                results.append(f"## {name}.py\n\n```python\n{content}\n```")
            return "\n\n".join(results)

        for name, path in key_files.items():
            if target.lower() in name.lower():
                return read_file_safe(path)

        return f"[File '{target}' not found in network-health-checker/app/]"


# ─── Tool 5: React UI Context Reader ──────────────────────────────────────────

class ReactUIContextTool(BaseTool):
    name: str = "ReactUIContext"
    description: str = """
        Reads key files from the network-health-checker-ui React project
        to understand the existing frontend structure before planning changes.

        Reads:
        - package.json          (dependencies, scripts, tooling)
        - src/App.tsx           (routing structure)
        - src/main.tsx          (entry point)
        - vite.config.ts        (build config)
        - tsconfig.json         (TypeScript config)
        - src/components/       (existing components list)
        - src/pages/            (existing pages list)
        - src/hooks/            (existing hooks list)

        Input: 'all' to read all files, or a specific target like
               'package', 'app', 'components', 'pages', 'hooks'
        Output: existing frontend code and structure for context
    """

    def _run(self, target: str = "all") -> str:
        project_path = get_project_path()
        ui_base = os.path.join(project_path, "network-health-checker-ui")

        if not os.path.isdir(ui_base):
            return (
                f"[React UI project not found at: {ui_base}. "
                f"This may be a new UI project — use the react-app-generator "
                f"template to scaffold it from scratch.]"
            )

        key_files = {
            "package":  os.path.join(ui_base, "package.json"),
            "app":      os.path.join(ui_base, "src", "App.tsx"),
            "main":     os.path.join(ui_base, "src", "main.tsx"),
            "vite":     os.path.join(ui_base, "vite.config.ts"),
            "tsconfig": os.path.join(ui_base, "tsconfig.json"),
        }

        dir_targets = {
            "components": os.path.join(ui_base, "src", "components"),
            "pages":      os.path.join(ui_base, "src", "pages"),
            "hooks":      os.path.join(ui_base, "src", "hooks"),
            "services":   os.path.join(ui_base, "src", "services"),
            "utils":      os.path.join(ui_base, "src", "utils"),
        }

        def list_dir(path: str, name: str) -> str:
            if not os.path.isdir(path):
                return f"[{name}/ not found]"
            files = os.listdir(path)
            return f"## {name}/\n" + "\n".join(f"  - {f}" for f in sorted(files))

        if target == "all":
            results = []
            # Read key files
            for name, path in key_files.items():
                content = read_file_safe(path)
                ext = "json" if "json" in name else "tsx"
                results.append(f"## {name}\n\n```{ext}\n{content}\n```")
            # List directories
            for name, path in dir_targets.items():
                results.append(list_dir(path, name))
            return "\n\n".join(results)

        # Specific file target
        for name, path in key_files.items():
            if target.lower() in name.lower():
                return read_file_safe(path)

        # Specific directory target
        for name, path in dir_targets.items():
            if target.lower() in name.lower():
                return list_dir(path, name)

        return f"[Target '{target}' not found in React UI project.]"
