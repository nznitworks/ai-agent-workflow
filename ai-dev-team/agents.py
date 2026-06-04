"""
agents.py — Agent definitions for the AI Dev Team workflow

Agents:
  - planner  : Claude Sonnet — breaks down feature requests into implementation plans
  - executor : Qwen 14B (Ollama) — implements code based on the plan
"""

import os
from crewai import Agent
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama
from crewai_tools import FileReadTool, FileWriterTool
from dotenv import load_dotenv

load_dotenv()

# ─── Model Setup ──────────────────────────────────────────────────────────────

claude = ChatAnthropic(
    model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
)

ollama_llm = Ollama(
    model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b"),
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
)

# ─── Tools ────────────────────────────────────────────────────────────────────

file_reader = FileReadTool()
file_writer = FileWriterTool()

# ─── Agents ───────────────────────────────────────────────────────────────────

planner = Agent(
    role="Tech Lead",
    goal=(
        "Analyze feature requests and produce clear, detailed implementation plans. "
        "Read existing project files to understand structure, patterns, and conventions "
        "before producing the plan so it fits naturally into the codebase."
    ),
    backstory=(
        "You are a senior tech lead with 15 years of experience across many stacks. "
        "You excel at breaking down complex features into actionable steps that junior "
        "developers can follow without ambiguity. You always read the existing code first "
        "to ensure your plan respects the architecture already in place."
    ),
    llm=claude,
    tools=[file_reader],
    verbose=True,
    allow_delegation=False,
)

executor = Agent(
    role="Senior Developer",
    goal=(
        "Implement features by following the implementation plan exactly. "
        "Read existing files for context, then write clean, well-commented, working code. "
        "Write files directly into the project directory."
    ),
    backstory=(
        "You are a senior developer who writes clean, efficient, production-ready code. "
        "You follow the plan provided by the tech lead precisely, match the existing code "
        "style, and always handle edge cases. You never leave placeholder code or TODOs "
        "without explaining them."
    ),
    llm=ollama_llm,
    tools=[file_reader, file_writer],
    verbose=True,
    allow_delegation=False,
)
