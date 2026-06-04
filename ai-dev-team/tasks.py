"""
tasks.py — Task definitions for the AI Dev Team workflow

Tasks:
  - planning_task   : Claude reads the project and produces an implementation plan
  - execution_task  : Qwen reads the plan and implements the code
"""

from crewai import Task
from agents import planner, executor


def create_tasks(feature_request: str, project_path: str) -> list[Task]:
    """
    Create the planning and execution tasks for a given feature request.

    Args:
        feature_request: Description of the feature to implement
        project_path: Absolute path to the project directory

    Returns:
        List of [planning_task, execution_task] in sequential order
    """

    planning_task = Task(
        description=f"""
            You are the tech lead for the project located at: {project_path}

            First, read the project structure and key files to understand:
            - The tech stack and frameworks used
            - Existing patterns and conventions
            - File and folder structure
            - Any relevant existing code related to the feature

            Then, produce a detailed implementation plan for this feature request:
            ---
            {feature_request}
            ---

            Your plan must include:
            1. A brief summary of the approach
            2. A list of files to create or modify (with full paths)
            3. For each file: what exactly needs to be added or changed
            4. Any dependencies or imports required
            5. Edge cases and error handling to consider
            6. Any environment variables or config changes needed

            Be specific enough that a developer can implement each step without guessing.
        """,
        agent=planner,
        expected_output=(
            "A structured, numbered implementation plan with file paths, "
            "step-by-step instructions, and notes on edge cases."
        ),
    )

    execution_task = Task(
        description=f"""
            You are the senior developer implementing a feature for the project at: {project_path}

            Follow the implementation plan from the tech lead exactly.

            For each file in the plan:
            1. Read the existing file first (if it exists) to understand the current code
            2. Write or update the file with the required changes
            3. Match the existing code style, indentation, and naming conventions
            4. Add clear comments explaining non-obvious logic
            5. Handle all edge cases mentioned in the plan

            Write all files directly to the project directory.

            Do NOT:
            - Skip any step from the plan
            - Leave placeholder code without explanation
            - Change files not mentioned in the plan
            - Introduce dependencies not in the plan
        """,
        agent=executor,
        expected_output=(
            "All files from the implementation plan written to disk, "
            "with clean, working, well-commented code."
        ),
        context=[planning_task],  # executor receives planner's output
    )

    return [planning_task, execution_task]
