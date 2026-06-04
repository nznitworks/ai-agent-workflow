"""
main.py — Entry point for the AI Dev Team workflow

Usage:
    python main.py "add a TCP proxy check endpoint"
    python main.py "add shopping cart" --project /path/to/project
    python main.py --gsoc                        (run GSOC scan analysis)
    python main.py                               (interactive mode)
"""

import sys
import os
import re
import argparse
from crewai import Crew, Process
from dotenv import load_dotenv

load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Dev Team — Claude plans, Qwen executes, Copilot reviews"
    )
    parser.add_argument(
        "feature",
        nargs="?",
        help="Feature request to implement (omit for interactive mode)",
    )
    parser.add_argument(
        "--project", "-p",
        default=None,
        help="Path to the project root (default: PROJECT_PATH env or cwd)",
    )
    parser.add_argument(
        "--gsoc",
        action="store_true",
        help="Run GSOC security scan analysis instead of feature development",
    )
    return parser.parse_args()


def get_project_path(project_arg: str | None) -> str:
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


def extract_and_write_files(output: str, project_path: str) -> list[str]:
    """
    Parse the agent output and write any code blocks to disk.

    Catches multiple formats:
        ### path/to/file.ext          (preferred)
        **path/to/file.ext**          (bold markdown)
        File: path/to/file.ext        (explicit label)
        # path/to/file.ext            (heading)
        `path/to/file.ext`            (inline code)
    """
    written = []

    # Broad pattern — catches most LLM output styles
    pattern = re.compile(
        r'(?:'
        r'#{1,3}\s+'           # ### or ## or #
        r'|File:\s*'           # File:
        r'|\*{1,2}'            # ** bold
        r'|`'                  # backtick
        r')?'
        r'((?:[\w\-]+/)*[\w\-]+\.(?:ts|tsx|js|jsx|json|yaml|yml|md|py|css|html|env|sh|toml|lock))'
        r'(?:\*{1,2}|`)?'     # closing bold/backtick
        r'\s*\n+'              # newlines
        r'```(?:\w+)?\n'       # opening fence
        r'(.*?)'               # file contents
        r'```',                # closing fence
        re.DOTALL
    )

    matches = pattern.findall(output)

    if not matches:
        # Try looser pattern — just find any code blocks with a path nearby
        loose_pattern = re.compile(
            r'([\w./\-]+\.(?:ts|tsx|js|jsx|json|yaml|yml|md|py|css|html|sh|toml))'
            r'[^\n]*\n'
            r'```(?:\w+)?\n'
            r'(.*?)'
            r'```',
            re.DOTALL
        )
        matches = loose_pattern.findall(output)

    if not matches:
        # Save raw output so nothing is lost
        raw_path = os.path.join(project_path, "ai-dev-team-output.md")
        with open(raw_path, "w") as f:
            f.write(f"# AI Dev Team Output\n\n{output}")
        print(f"\n⚠️  Could not parse files from output.")
        print(f"   Raw output saved to: {raw_path}")
        print(f"   Check the file — code may be there but in unexpected format.")
        return []

    for file_path, content in matches:
        # Skip if path looks wrong
        if len(file_path) > 200 or " " in file_path:
            continue

        # Resolve relative paths against project root
        if not file_path.startswith("/"):
            full_path = os.path.join(project_path, file_path)
        else:
            full_path = file_path

        # Create parent directories
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        written.append(full_path)
        print(f"   📄 Written: {file_path}")

    return written


def print_copilot_review_reminder(written_files: list[str] = None):
    print(f"\n{'─' * 50}")
    print("✅ Implementation complete!")
    print()
    if written_files:
        print("📁 Files written:")
        for f in written_files:
            print(f"   {f}")
        print()
    print("📋 Next Step — Copilot Review (manual):")
    print("   1. Open VS Code")
    print("   2. Select the changed files")
    print("   3. Open Copilot Chat (Ctrl+Shift+I)")
    print("   4. Paste this prompt:\n")
    print('   "Review the recently generated code for bugs,')
    print('    edge cases, security issues, and improvements.')
    print('    Be specific and actionable."')
    print()
    print("   5. Accept/reject suggestions")
    print("   6. Run your tests")
    print("   7. Commit if passing")
    print(f"{'─' * 50}\n")


def run_feature(feature_request: str, project_path: str):
    """Run the planner → executor workflow for a feature request."""
    from agents import planner, executor
    from tasks import create_tasks

    print(f"\n🚀 AI Dev Team — Feature Mode")
    print(f"   Project : {project_path}")
    print(f"   Feature : {feature_request[:80]}{'...' if len(feature_request) > 80 else ''}")
    print(f"\n{'─' * 50}")
    print("📋 Phase 1: Claude is reading conventions and planning...")
    print(f"{'─' * 50}\n")

    tasks = create_tasks(feature_request, project_path)

    crew = Crew(
        agents=[planner, executor],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    # Extract output string from CrewAI result
    output = str(result.raw) if hasattr(result, "raw") else str(result)

    # DEBUG — print raw output to see what the executor returned
    print(f"\n{'─' * 50}")
    print("🔍 DEBUG — Raw executor output:")
    print(f"{'─' * 50}")
    print(output[:3000])  # first 3000 chars
    print(f"{'─' * 50}\n")

    print(f"\n{'─' * 50}")
    print("📝 Extracting and writing files...")
    print(f"{'─' * 50}")

    written = extract_and_write_files(output, project_path)
    print_copilot_review_reminder(written)

    return result


def run_gsoc(project_path: str):
    """Run the GSOC security scan analysis workflow."""
    from agents import analyzer
    from tasks import create_gsoc_tasks

    print(f"\n🔐 AI Dev Team — GSOC Scan Analysis")
    print(f"   Project : {project_path}")
    print(f"\n{'─' * 50}")
    print("🔍 Analyzing GSOC scan files...")
    print(f"{'─' * 50}\n")

    tasks = create_gsoc_tasks(project_path)

    crew = Crew(
        agents=[analyzer],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    # Extract and write files from output
    output = str(result.raw) if hasattr(result, "raw") else str(result)
    written = extract_and_write_files(output, project_path)

    print(f"\n{'─' * 50}")
    print("✅ GSOC analysis complete!")
    if written:
        print("   Report written to:")
        for f in written:
            print(f"   {f}")
    else:
        print("   Check ai-dev-team-output.md for the raw report.")
    print("   Review findings — start with HIGH severity items first.")
    print(f"{'─' * 50}\n")

    return result


def main():
    args = parse_args()

    # Validate API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set. Add it to your .env file.")
        print("   Get your key at: https://console.anthropic.com")
        sys.exit(1)

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    project_path = get_project_path(args.project)

    print(f"🔌 Ollama : {ollama_url}")
    print(f"📁 Project: {project_path}")

    if args.gsoc:
        run_gsoc(project_path)
    else:
        feature_request = get_feature_request(args.feature)
        if not feature_request:
            print("❌ No feature request provided.")
            sys.exit(1)
        run_feature(feature_request, project_path)


if __name__ == "__main__":
    main()
