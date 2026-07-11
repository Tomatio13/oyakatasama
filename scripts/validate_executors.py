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
            if not isinstance(executors[candidate].get("quota_provider"), str):
                fail(f"selector {name} candidate {candidate} requires quota_provider")
        tie_breaker = selector.get("tie_breaker")
        if tie_breaker not in candidates:
            fail(f"selector {name}.tie_breaker must be a candidate")
        require_executor(selector.get("fallback_executor"), executors, f"selector {name}.fallback_executor")

    backlog = template.get("backlog")
    if not isinstance(backlog, list):
        fail("template backlog must be a list")
    for task in backlog:
        if not isinstance(task, dict):
            fail("each template task must be a mapping")
        executor = task.get("executor")
        if executor not in executors and executor not in selectors:
            fail("each template task executor must reference an executor or selector")

    print("Executor configuration is valid.")


if __name__ == "__main__":
    main()
