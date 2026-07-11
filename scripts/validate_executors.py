#!/usr/bin/env python3
"""Validate Oyakata executor definitions and the goal-contract template."""

from pathlib import Path
import re
import sys

import yaml


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


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: validate_executors.py <executors.yaml> <todo-template.yaml>")

    config = load_yaml(Path(sys.argv[1]))
    template = load_yaml(Path(sys.argv[2]))
    executors = config.get("executors")
    if not isinstance(executors, dict) or not executors:
        fail("executors must be a non-empty mapping")

    for name, definition in executors.items():
        if not isinstance(name, str) or not isinstance(definition, dict):
            fail("each executor must be a named mapping")
        for field in ("command", "model"):
            if not isinstance(definition.get(field), str) or not definition[field]:
                fail(f"executor {name} requires {field}")
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
                if any(item not in {"{repo}", "{model}", "{prompt}"} for item in placeholders):
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

    backlog = template.get("backlog")
    if not isinstance(backlog, list):
        fail("template backlog must be a list")
    for task in backlog:
        if not isinstance(task, dict):
            fail("each template task must be a mapping")
        executor = task.get("executor")
        if executor not in executors and executor not in selectors:
            fail("each template task executor must reference an executor or selector")
        if executor in executors and not executors[executor]["delegable"]:
            fail("template task executor must be delegable")
        delegation = task.get("delegation")
        if not isinstance(delegation, dict):
            fail("each template task requires delegation")
        if delegation.get("approval") not in {"not_requested", "approved"}:
            fail("task delegation approval must be not_requested or approved")
        files = delegation.get("approved_target_files")
        if not isinstance(files, list) or not all(isinstance(path, str) for path in files):
            fail("task delegation approved_target_files must be a string list")
        approved_executor = delegation.get("approved_executor")
        if delegation["approval"] == "not_requested":
            if approved_executor is not None or files:
                fail("unapproved delegation must not declare executor or files")
        elif approved_executor not in executors:
            fail("approved delegation must reference an executor")
        elif approved_executor != executor:
            fail("approved delegation executor must match task executor")
        elif files != task.get("target_files"):
            fail("approved delegation files must match task target_files")

    print("Executor configuration is valid.")


if __name__ == "__main__":
    main()
