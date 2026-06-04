"""
main.py — Entry point for the AI Dev Team workflow

Usage:
    python main.py "add user authentication with JWT"
    python main.py "add shopping cart" --project /path/to/project
    python main.py  (interactive mode)
"""

import sys
import os
import argparse
from crewai import Crew, Process
from dotenv import load_dotenv

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Dev Team — Claude plans, Qwen executes"
    )
    parser.add_argument(
        "feature",
        nargs="?",
        help="Feature request to implement (omit for interactive mode)",
    )
    parser.add_argument(
        "--project",
        "-p",
        default=None,
        help="Path to the project directory (default: current directory)",
    )
    return parser.parse_args()


def get_project_path(project_arg: str | None) -> str:
    """Resolve project path from argument or environment variable."""
    if project_arg:
        path = os.path.abspath(project_arg)
    elif os.getenv("PROJECT_PATH"):
        path = os.path.abspath(os.getenv("PROJECT_PATH"))
    else:
        path = os.getcwd()

    if not os.path.isdir(path):
        print(f"❌ Project path does not exist: {path}")
        sys.exit(1)

    return path


def get_feature_request(feature_arg: str | None) -> str:
    """Get feature request from argument or prompt interactively."""
    if feature_arg:
        return feature_arg.strip()

    print("\n🦙 AI Dev Team — Interactive Mode")
    print("─" * 40)
    print("Describe the feature you want to implement.")
    print("Be as specific as possible for best results.\n")

    lines = []
    print("Feature request (press Enter twice when done):")
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)

    return "\n".join(lines).strip()


def run(feature_request: str, project_path: str):
    """Run the full planner → executor workflow."""

    # Import here to avoid circular imports
    from agents import planner, executor
    from tasks import create_tasks

    print(f"\n🚀 Starting AI Dev Team")
    print(f"   Project: {project_path}")
    print(f"   Feature: {feature_request[:80]}{'...' if len(feature_request) > 80 else ''}")
    print(f"\n{'─' * 50}")
    print("📋 Phase 1: Claude is planning the implementation...")
    print(f"{'─' * 50}\n")

    tasks = create_tasks(feature_request, project_path)

    crew = Crew(
        agents=[planner, executor],
        tasks=tasks,
        process=Process.sequential,  # plan first, then execute
        verbose=True,
    )

    result = crew.kickoff()

    print(f"\n{'─' * 50}")
    print("✅ Done! Review the changes in VS Code.")
    print("   → Open changed files")
    print("   → Ask Copilot Chat to review for bugs")
    print("   → Run your tests before committing")
    print(f"{'─' * 50}\n")

    return result


def main():
    args = parse_args()

    # Validate environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set. Add it to your .env file.")
        print("   Get your key at: https://console.anthropic.com")
        sys.exit(1)

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    print(f"🔌 Ollama server: {ollama_url}")

    project_path = get_project_path(args.project)
    feature_request = get_feature_request(args.feature)

    if not feature_request:
        print("❌ No feature request provided.")
        sys.exit(1)

    run(feature_request, project_path)


if __name__ == "__main__":
    main()
