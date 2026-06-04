# Chunked Execution for AI Dev Team

**Date:** 2026-06-04
**Status:** Approved
**Problem:** Qwen 14B silently truncates output on large tasks, producing stubs instead of complete code.

---

## Problem

When the ai-dev-team workflow receives a broad request like "create the full frontend scaffold", the executor (Qwen 14B) hits its output budget and degrades:

```
Generates first few files fully
        |
Realizes output is getting long
        |
Shortcuts remaining files with "Continue similarly..." or stubs
        |
Reports done - but work is incomplete
```

## Solution

Break large tasks into focused chunks. One Claude planning call, then Qwen executes each chunk independently with a small, focused prompt.

## Architecture

```
python main.py "create full frontend scaffold"
        |
  detect_template() -> "react-app-generator"
        |
  detect_chunk_template() -> "react-scaffold" (matches keywords)
        |
  Claude plans the ENTIRE feature (1 API call)
  Plan is structured into predefined sections matching chunks
        |
  For each chunk:
    -> Feed Qwen: chunk description + relevant plan section + files written so far
    -> Extract files -> write to disk -> print summary
    -> Continue to next chunk
        |
  Print final summary + Copilot review reminder
```

## CLI Interface

```bash
# Auto-detects and chunks (default for broad tasks)
python main.py "create the full frontend for Network Health Checker"

# Force chunking on any task
python main.py --chunked "add all CRUD endpoints"

# Disable chunking (single-shot, old behavior)
python main.py --no-chunk "create the full frontend"

# Single-feature runs are unaffected
python main.py "add StatusBadge component"
```

## Chunk Templates

Defined in `tasks.py` as `CHUNK_TEMPLATES` dict.

### react-scaffold

Trigger keywords: scaffold, full frontend, create frontend, all components, complete frontend

| Chunk | Label | Target Files |
|-------|-------|-------------|
| 1 | Types & Services | src/types/api.ts, src/services/api.ts |
| 2 | Hooks | src/hooks/useHttpCheck.ts, useEgressCheck.ts, useDnsCheck.ts, useTcpCheck.ts, useHealth.ts |
| 3 | Components | src/components/CheckForm/, ResultCard/, StatusBadge/, LatencyBadge/, ErrorBoundary/ |
| 4 | Pages | src/pages/Dashboard.tsx, HttpCheck.tsx, EgressCheck.tsx, DnsCheck.tsx, TcpCheck.tsx, Health.tsx |
| 5 | Config | package.json, vite.config.ts, tsconfig.json, tailwind.config.ts, .env.example, App.tsx, main.tsx |

### fastapi-scaffold

Trigger keywords: scaffold, full backend, create backend, all endpoints, complete backend

| Chunk | Label | Target Files |
|-------|-------|-------------|
| 1 | Schemas | app/schemas/ |
| 2 | Services | app/services/ |
| 3 | Routes & Config | app/api/, app/core/, app/main.py |
| 4 | Tests & Docs | tests/, README.md, AGENTS.md |

## Planning Prompt Changes

When chunked mode is active, the planner's task includes an additional instruction:

```
IMPORTANT: Structure your plan into these exact sections,
in this order, because they will be implemented in separate passes:

Section 1 - Types & Services:
  Files: src/types/api.ts, src/services/api.ts
  Plan the TypeScript interfaces and Axios API layer.

Section 2 - Hooks:
  ...
```

This ensures Claude's plan output has clear section boundaries that can be extracted per-chunk.

## Execution Loop (run_chunked_feature)

```python
def run_chunked_feature(feature_request, project_path, chunk_template):
    # Phase 1: Claude plans everything (1 API call)
    planning_task = create_chunked_planning_task(feature_request, project_path, chunk_template)
    planning_crew = Crew(agents=[planner], tasks=[planning_task], ...)
    plan_result = planning_crew.kickoff()
    full_plan = str(plan_result.raw)

    # Phase 2: Qwen executes each chunk
    all_written = []
    for i, chunk in enumerate(chunk_template["chunks"]):
        section_plan = extract_plan_section(full_plan, i + 1, chunk["label"])

        exec_task = create_chunk_execution_task(
            chunk=chunk,
            section_plan=section_plan,
            written_so_far=all_written,
            project_path=project_path,
            template_name=template_name,
        )

        exec_crew = Crew(agents=[executor], tasks=[exec_task], ...)
        result = exec_crew.kickoff()

        output = str(result.raw)
        written = extract_and_write_files(output, project_path)
        all_written.extend(written)

        print(f"Chunk {i+1}/{total}: {chunk['label']} - wrote {len(written)} files")

    print_copilot_review_reminder(all_written)
```

## Per-Chunk Executor Prompt

Each chunk gets a focused prompt:

```
You are implementing Section {N}: {label}

Here is the plan for THIS section only:
{section_plan}

Files already created in previous sections:
{written_files_list}

You MUST produce exactly these files:
{target_files}

[Same output format rules: ### path + code fence]
```

## Files Changed

| File | Changes |
|------|---------|
| main.py | Add --chunked/--no-chunk flags, add run_chunked_feature(), update routing |
| tasks.py | Add CHUNK_TEMPLATES, detect_chunk_template(), create_chunked_planning_task(), create_chunk_execution_task() |
| agents.py | No changes |
| tools.py | No changes |

## What Stays the Same

- Single-feature runs (run_feature) - unchanged
- GSOC mode - unchanged
- parse_output.py - unchanged
- Agent definitions - unchanged
- Tool definitions - unchanged
