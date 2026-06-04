"""
agents.py — Agent definitions for the AI Dev Team workflow

Agents:
  - planner  : Claude Sonnet — reads templates + conventions, plans features
  - executor : Qwen 14B (Ollama) — implements code using templates as reference
  - analyzer : Claude Sonnet — analyzes GSOC security scans
"""

import os
from crewai import Agent, LLM
from crewai_tools import FileReadTool, FileWriterTool
from tools import (
    CopilotAgentTemplateTool,
    ProjectConventionsTool,
    NetworkCheckerContextTool,
    ReactUIContextTool,
    GSocScanTool,
)
from dotenv import load_dotenv

load_dotenv()

# ─── Models ───────────────────────────────────────────────────────────────────

# CrewAI's native LLM wrapper — works with both Anthropic and Ollama
claude = LLM(
    model=f"anthropic/{os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5')}",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

ollama_llm = LLM(
    model=f"ollama/{os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:14b')}",
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
)

# ─── Tools ────────────────────────────────────────────────────────────────────

file_reader        = FileReadTool()
file_writer        = FileWriterTool()
template_tool      = CopilotAgentTemplateTool()
conventions_tool   = ProjectConventionsTool()
context_tool       = NetworkCheckerContextTool()
react_context_tool = ReactUIContextTool()
gsoc_tool          = GSocScanTool()

# ─── Agents ───────────────────────────────────────────────────────────────────

planner = Agent(
    role="Tech Lead",
    goal=(
        "Before planning anything, always: "
        "(1) read project conventions via ProjectConventions tool, "
        "(2) load the relevant Copilot agent template via CopilotAgentTemplate tool, "
        "(3) read the existing code via NetworkCheckerContext tool (backend) "
        "or ReactUIContext tool (frontend). "
        "Then produce a detailed implementation plan that strictly follows "
        "the AMIPDH conventions and the loaded template patterns."
    ),
    backstory=(
        "You are a senior tech lead specialized in FastAPI, async Python, "
        "React/TypeScript, and Kubernetes-deployed services. You always read "
        "the project conventions and existing code before planning so your "
        "output fits naturally into the existing architecture. You know the "
        "AMIPDH monorepo well: thin route handlers, async services, strict "
        "Pydantic validation, deterministic tests, functional React components "
        "with hooks, TypeScript-first, and Helm-based deployment on Azure."
    ),
    llm=claude,
    tools=[file_reader, template_tool, conventions_tool, context_tool, react_context_tool],
    verbose=True,
    allow_delegation=False,
)

executor = Agent(
    role="Senior Developer",
    goal=(
        "Implement features by following the plan exactly. "
        "Use the CopilotAgentTemplate tool to load the relevant template "
        "as your scaffolding reference. For backend features use "
        "NetworkCheckerContext; for frontend features use ReactUIContext. "
        "Write clean, well-commented code that matches the existing project "
        "style. Write all files directly into the project directory."
    ),
    backstory=(
        "You are a senior full-stack developer who specializes in FastAPI "
        "async patterns and modern React with TypeScript. You always use "
        "the provided Copilot agent templates as your starting reference. "
        "For backend: thin route handlers, async service functions, strict "
        "Pydantic v2 models, deterministic pytest tests. "
        "For frontend: functional components with hooks, TypeScript interfaces, "
        "proper routing, composable components, Vitest/Jest tests."
    ),
    llm=ollama_llm,
    tools=[file_reader, file_writer, template_tool, context_tool, react_context_tool],
    verbose=True,
    allow_delegation=False,
)

analyzer = Agent(
    role="Security Analyst",
    goal=(
        "Analyze GSOC security scan results from CSV files. "
        "Focus on HIGH and MEDIUM severity findings only. "
        "Produce a structured markdown risk report with mitigations, "
        "resource impact, and a prioritized remediation plan."
    ),
    backstory=(
        "You are a security analyst who specializes in Kubernetes workload "
        "security and vulnerability management. You analyze GSOC scan outputs "
        "and produce clear, actionable reports that help engineering teams "
        "understand and remediate security findings efficiently."
    ),
    llm=claude,
    tools=[file_reader, file_writer, gsoc_tool],
    verbose=True,
    allow_delegation=False,
)
