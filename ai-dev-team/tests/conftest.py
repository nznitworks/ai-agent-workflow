"""
conftest.py — Mock heavy dependencies so pure-Python functions in tasks.py
can be tested without installing CrewAI, Ollama, or having API keys.

This runs before any test collection, stubbing out crewai, crewai_tools,
agents, tools, and dotenv so that `from tasks import ...` succeeds.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock

# ── Stub modules that tasks.py (and its transitive imports) need ──────────

_stubs = {
    "crewai": MagicMock(Task=MagicMock, Agent=MagicMock, LLM=MagicMock),
    "crewai_tools": MagicMock(FileReadTool=MagicMock, FileWriterTool=MagicMock),
    "dotenv": MagicMock(load_dotenv=MagicMock()),
}

# Create a proper stub for the agents module with the three expected names
_agents_mod = ModuleType("agents")
_agents_mod.planner = MagicMock(name="planner")
_agents_mod.executor = MagicMock(name="executor")
_agents_mod.analyzer = MagicMock(name="analyzer")
_stubs["agents"] = _agents_mod

# Create a proper stub for the tools module
_tools_mod = ModuleType("tools")
_tools_mod.CopilotAgentTemplateTool = MagicMock()
_tools_mod.ProjectConventionsTool = MagicMock()
_tools_mod.NetworkCheckerContextTool = MagicMock()
_tools_mod.ReactUIContextTool = MagicMock()
_tools_mod.GSocScanTool = MagicMock()
_stubs["tools"] = _tools_mod

for name, mod in _stubs.items():
    sys.modules[name] = mod
