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
