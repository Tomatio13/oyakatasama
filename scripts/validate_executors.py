#!/usr/bin/env python3
"""Validate Oyakatasama executor definitions and goal contracts."""

from pathlib import Path
import re
import sys

import yaml


# Supported runtime placeholders. {skill_dir} expands to the absolute path of the
# directory that contains executors.yaml (the skill directory); the others are
# per-invocation values expanded by the Lead at runtime.
ARG_PLACEHOLDERS = {"{repo}", "{model}", "{prompt}", "{skill_dir}"}
COMMAND_PLACEHOLDERS = {"{skill_dir}"}


def expand_skill_dir(value: str, skill_dir: Path) -> str:
    """Expand the {skill_dir} placeholder to the absolute skill directory path.

    This makes path-like values resolvable at runtime independent of the caller's
    working directory. ``skill_dir`` is the resolved directory containing
    executors.yaml.
    """
    return value.replace("{skill_dir}", str(skill_dir))


def fail(message: str) -> None:
    print(f"Invalid executor configuration: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as error:
        fail(f"cannot read {path}: {error}")
    if not isinstance(data, dict):
        fail(f"{path} must contain a YAML mapping")
    return data


def require_executor(name: object, executors: dict, field: str) -> None:
    if not isinstance(name, str) or name not in executors:
        fail(f"{field} must reference an executor ID")


def validate_task(task: object, executors: dict, selectors: dict, path: Path) -> None:
    if not isinstance(task, dict):
        fail(f"{path} each backlog task must be a mapping")

    for field in ("id", "title", "status", "verification"):
        if not isinstance(task.get(field), str) or not task[field]:
            fail(f"{path} backlog task requires {field}")

    if task["status"] not in {"pending", "in_progress", "completed"}:
        fail(f"{path} backlog task status is invalid")

    target_files = task.get("target_files")
    if not isinstance(target_files, list) or not target_files:
        fail(f"{path} backlog task target_files must be a non-empty list")
    if not all(isinstance(file_path, str) and file_path for file_path in target_files):
        fail(f"{path} backlog task target_files must contain strings")

    executor = task.get("executor")
    if executor not in executors and executor not in selectors:
        fail(f"{path} backlog task executor must reference an executor or selector")
    if executor in executors and not executors[executor]["delegable"]:
        fail(f"{path} backlog task executor must be delegable")

    history = task.get("executor_history")
    if not isinstance(history, list) or not history:
        fail(f"{path} backlog task executor_history must be a non-empty list")
    for entry in history:
        if not isinstance(entry, dict):
            fail(f"{path} backlog task executor_history entries must be mappings")
        for field in ("executor", "reason", "changed_by"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                fail(f"{path} backlog task executor_history requires {field}")

    delegation = task.get("delegation")
    if not isinstance(delegation, dict):
        fail(f"{path} backlog task requires delegation")
    if delegation.get("approval") not in {"not_requested", "approved"}:
        fail(f"{path} task delegation approval must be not_requested or approved")
    files = delegation.get("approved_target_files")
    if not isinstance(files, list) or not all(isinstance(file_path, str) for file_path in files):
        fail(f"{path} task delegation approved_target_files must be a string list")
    approved_executor = delegation.get("approved_executor")
    if delegation["approval"] == "not_requested":
        if approved_executor is not None or files:
            fail(f"{path} unapproved delegation must not declare executor or files")
    elif approved_executor not in executors:
        fail(f"{path} approved delegation must reference an executor")
    elif approved_executor != executor:
        fail(f"{path} approved delegation executor must match task executor")
    elif files != target_files:
        fail(f"{path} approved delegation files must match task target_files")


def validate_contract(path: Path, executors: dict, selectors: dict) -> None:
    contract = load_yaml(path)
    project = contract.get("project")
    if not isinstance(project, dict):
        fail(f"{path} project must be a mapping")
    for field in ("id", "goal", "constraints", "success_criteria"):
        if field not in project:
            fail(f"{path} project requires {field}")
    if not isinstance(project["id"], str) or not project["id"]:
        fail(f"{path} project.id must be a string")
    if not isinstance(project["goal"], str) or not project["goal"]:
        fail(f"{path} project.goal must be a string")
    for field in ("constraints", "success_criteria"):
        values = project.get(field)
        if not isinstance(values, list) or not values or not all(isinstance(item, str) and item for item in values):
            fail(f"{path} project.{field} must be a non-empty string list")

    if path.stem.startswith("L-"):
        file_id = path.stem.split("_", 1)[0]
        if project["id"] != file_id:
            fail(f"{path} project.id must match the file prefix")

    backlog = contract.get("backlog")
    if not isinstance(backlog, list) or not backlog:
        fail(f"{path} backlog must be a non-empty list")
    for task in backlog:
        validate_task(task, executors, selectors, path)

    learnings = contract.get("learnings")
    if not isinstance(learnings, list):
        fail(f"{path} learnings must be a list")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: validate_executors.py <executors.yaml> [<goal-contract.yaml> ...]")

    config_path = Path(sys.argv[1])
    config = load_yaml(config_path)
    config_dir = config_path.resolve().parent
    executors = config.get("executors")
    if not isinstance(executors, dict) or not executors:
        fail("executors must be a non-empty mapping")

    for name, definition in executors.items():
        if not isinstance(name, str) or not isinstance(definition, dict):
            fail("each executor must be a named mapping")
        for field in ("command", "model"):
            if not isinstance(definition.get(field), str) or not definition[field]:
                fail(f"executor {name} requires {field}")
        command = definition["command"]
        if command != "current_codex_session":
            command_placeholders = set(re.findall(r"\{[^}]+\}", command))
            unsupported_command = command_placeholders - COMMAND_PLACEHOLDERS
            if unsupported_command:
                fail(
                    f"executor {name} command has unsupported placeholder: "
                    f"{sorted(unsupported_command)}"
                )
            expanded_command = expand_skill_dir(command, config_dir)
            if "/" in expanded_command:
                command_path = Path(expanded_command)
                resolved = command_path if command_path.is_absolute() else config_dir / command_path
                if not resolved.exists():
                    fail(f"executor {name} command does not exist: {resolved}")
        if not isinstance(definition.get("delegable"), bool):
            fail(f"executor {name} requires boolean delegable")
        if definition.get("data_boundary") not in {"current_session", "external_service"}:
            fail(f"executor {name} requires data_boundary")
        if not isinstance(definition.get("requires_unsandboxed_runtime"), bool):
            fail(f"executor {name} requires boolean requires_unsandboxed_runtime")
        if definition["command"] != "current_codex_session":
            args = definition.get("args")
            if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
                fail(f"executor {name} requires string args")
            for arg in args:
                placeholders = re.findall(r"\{[^}]+\}", arg)
                if any(item not in ARG_PLACEHOLDERS for item in placeholders):
                    fail(f"executor {name} has an unsupported placeholder")

    for role in ("lead", "reviewer"):
        definition = config.get(role)
        if not isinstance(definition, dict):
            fail(f"{role} must be a mapping")
        require_executor(definition.get("executor"), executors, f"{role}.executor")
        if executors[definition["executor"]]["delegable"]:
            fail(f"{role}.executor must not be delegable")

    research = config.get("research")
    if not isinstance(research, dict):
        fail("research must be a mapping")
    for field in ("web_executor", "x_executor"):
        require_executor(research.get(field), executors, f"research.{field}")

    selectors = config.get("selection")
    if not isinstance(selectors, dict) or not selectors:
        fail("selection must be a non-empty mapping")
    for name, selector in selectors.items():
        if not isinstance(name, str) or not isinstance(selector, dict):
            fail("each selector must be a named mapping")
        candidates = selector.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            fail(f"selector {name} requires non-empty candidates")
        for candidate in candidates:
            require_executor(candidate, executors, f"selector {name}.candidates")
            if not executors[candidate]["delegable"]:
                fail(f"selector {name} candidate {candidate} must be delegable")
            if not isinstance(executors[candidate].get("quota_provider"), str):
                fail(f"selector {name} candidate {candidate} requires quota_provider")
            windows = executors[candidate].get("quota_windows")
            if not isinstance(windows, list) or not windows:
                fail(f"selector {name} candidate {candidate} requires quota_windows")
            if any(window not in {"primary", "secondary", "tertiary", "extra"} for window in windows):
                fail(f"selector {name} candidate {candidate} has invalid quota_windows")
        tie_breaker = selector.get("tie_breaker")
        if tie_breaker not in candidates:
            fail(f"selector {name}.tie_breaker must be a candidate")
        fallback_executor = selector.get("fallback_executor")
        require_executor(fallback_executor, executors, f"selector {name}.fallback_executor")
        if not executors[fallback_executor]["delegable"]:
            fail(f"selector {name}.fallback_executor must be delegable")

    for path in map(Path, sys.argv[2:]):
        validate_contract(path, executors, selectors)

    print("Executor configuration is valid.")


if __name__ == "__main__":
    main()
