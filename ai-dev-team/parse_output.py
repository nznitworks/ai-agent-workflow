"""
parse_output.py — Extract files from ai-dev-team-output.md

Handles Qwen's output format where all code is in one block
with file paths as comments like:
    // path/to/file.tsx
    ...code...
    // path/to/next/file.tsx
    ...code...

Usage:
    python parse_output.py                          (uses ai-dev-team-output.md in cwd)
    python parse_output.py --output path/to/file.md
    python parse_output.py --project /path/to/project
"""

import os
import re
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract files from ai-dev-team-output.md"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Path to the output markdown file (default: ai-dev-team-output.md in PROJECT_PATH)"
    )
    parser.add_argument(
        "--project", "-p",
        default=None,
        help="Project root to write files into (default: PROJECT_PATH env or cwd)"
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Folder prefix to prepend to all extracted file paths (e.g. 'frontend')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without actually writing"
    )
    return parser.parse_args()


def get_project_path(project_arg):
    if project_arg:
        return os.path.abspath(project_arg)
    if os.getenv("PROJECT_PATH"):
        return os.path.abspath(os.getenv("PROJECT_PATH"))
    return os.getcwd()


def extract_files_from_comment_blocks(content: str) -> dict[str, str]:
    """
    Handles Qwen's format where files are delimited by comment headers:

        // index.tsx
        import React from 'react';
        ...

        // App.tsx
        import React from 'react';
        ...

    Also handles:
        # path/to/file.py
        # path/to/file.ts (with leading slash)
    """
    files = {}

    # Remove the outer code fence if present
    # Find content inside ```typescript ... ``` or ```tsx ... ```
    fence_match = re.search(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
    if fence_match:
        code_block = fence_match.group(1)
    else:
        code_block = content

    # Split on comment-style file headers
    # Matches: // filename.ext  or  // path/to/filename.ext
    # Also matches Python: # filename.py
    file_header_pattern = re.compile(
        r'^(?://|#)\s+'                                          # comment prefix
        r'((?:[\w\-]+/)*[\w\-]+\.'                              # optional path segments
        r'(?:ts|tsx|js|jsx|json|yaml|yml|md|py|css|html|sh|toml|env|lock))'  # extension
        r'\s*$',                                                 # end of line
        re.MULTILINE
    )

    matches = list(file_header_pattern.finditer(code_block))

    if not matches:
        return {}

    for i, match in enumerate(matches):
        file_path = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(code_block)

        file_content = code_block[start:end].strip()

        # Skip empty files or placeholder-only files
        if not file_content:
            continue
        if file_content.startswith("(") and "exercise" in file_content.lower():
            print(f"   ⚠️  Skipping placeholder: {file_path}")
            continue

        files[file_path] = file_content

    return files


def extract_files_from_separate_blocks(content: str) -> dict[str, str]:
    """
    Handles format where each file has its own code block:

        ### frontend/src/types/api.ts
        ```typescript
        ...
        ```
    """
    files = {}

    pattern = re.compile(
        r'(?:#{1,3}\s+|File:\s*|\*\*)'
        r'((?:[\w\-]+/)*[\w\-]+\.(?:ts|tsx|js|jsx|json|yaml|yml|md|py|css|html|sh|toml))'
        r'(?:\*\*)?\s*\n+'
        r'```(?:\w+)?\n'
        r'(.*?)'
        r'```',
        re.DOTALL
    )

    for match in pattern.finditer(content):
        file_path = match.group(1).strip()
        file_content = match.group(2).strip()
        if file_content:
            files[file_path] = file_content

    return files


def write_files(files: dict[str, str], project_path: str, prefix: str = None, dry_run: bool = False) -> list[str]:
    written = []

    for file_path, content in files.items():
        # Skip files that already have the prefix
        if prefix and not file_path.startswith(prefix + "/"):
            file_path = os.path.join(prefix, file_path)

        if file_path.startswith("/"):
            full_path = file_path
        else:
            full_path = os.path.join(project_path, file_path)

        if dry_run:
            print(f"   [DRY RUN] Would write: {file_path} ({len(content)} chars)")
            written.append(full_path)
            continue

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"   📄 Written: {file_path}")
        written.append(full_path)

    return written


def main():
    args = parse_args()
    project_path = get_project_path(args.project)

    # Find the output file
    if args.output:
        output_file = args.output
    else:
        output_file = os.path.join(project_path, "ai-dev-team-output.md")

    if not os.path.isfile(output_file):
        print(f"❌ Output file not found: {output_file}")
        return

    prefix = args.prefix or "frontend"  # default to frontend/

    print(f"📖 Reading: {output_file}")
    print(f"📁 Project: {project_path}")
    print(f"📂 Prefix:  {prefix}/")
    print(f"{'─' * 50}")

    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Try comment-block format first (Qwen's typical output)
    print("🔍 Trying comment-block format (// filename.ext)...")
    files = extract_files_from_comment_blocks(content)

    if not files:
        # Try separate code block format
        print("🔍 Trying separate code block format (### filename)...")
        files = extract_files_from_separate_blocks(content)

    if not files:
        print("❌ No files could be extracted.")
        print("   The output format is not recognized.")
        print("   Please check ai-dev-team-output.md manually.")
        return

    print(f"✅ Found {len(files)} files to write:\n")
    for path in files:
        display = os.path.join(prefix, path) if not path.startswith(prefix) else path
        print(f"   - {display}")

    print(f"\n{'─' * 50}")
    print("📝 Writing files...")
    print(f"{'─' * 50}")

    written = write_files(files, project_path, prefix=prefix, dry_run=args.dry_run)

    print(f"\n{'─' * 50}")
    if args.dry_run:
        print(f"✅ Dry run complete — {len(written)} files would be written.")
    else:
        print(f"✅ Done — {len(written)} files written.")
    print(f"{'─' * 50}\n")

    if not args.dry_run:
        print("Next steps:")
        print(f"   1. cd {prefix}/")
        print(f"   2. npm install")
        print(f"   3. npm run dev")
        print(f"   4. Open http://localhost:5173")


if __name__ == "__main__":
    main()
