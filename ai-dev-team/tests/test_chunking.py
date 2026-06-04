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
