#!/usr/bin/env python3
"""Helpers for reading and updating Oyakatasama goal contracts."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


VALID_STATUSES = {"pending", "in_progress", "completed"}


class TodoError(Exception):
    """Raised when a contract operation cannot be completed safely."""


def ensure_mutable_contract_path(path: Path) -> None:
    if path.name == ".todo.yaml" and path.parent.name == "references":
        raise TodoError("refusing to edit references/.todo.yaml; copy it to .oyakatasama/L-*.yaml first")


def load_contract(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text())
    except OSError as error:
        raise TodoError(f"cannot read {path}: {error}") from error
    except yaml.YAMLError as error:
        raise TodoError(f"invalid YAML in {path}: {error}") from error

    if not isinstance(data, dict):
        raise TodoError(f"{path} must contain a YAML mapping")
    return data


def write_contract(path: Path, contract: dict[str, Any]) -> None:
    ensure_mutable_contract_path(path)
    try:
        path.write_text(
            yaml.safe_dump(
                contract,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )
        )
    except OSError as error:
        raise TodoError(f"cannot write {path}: {error}") from error


def require_backlog(contract: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    backlog = contract.get("backlog")
    if not isinstance(backlog, list) or not backlog:
        raise TodoError(f"{path} backlog must be a non-empty list")
    typed_backlog: list[dict[str, Any]] = []
    for index, task in enumerate(backlog):
        if not isinstance(task, dict):
            raise TodoError(f"{path} backlog[{index}] must be a mapping")
        typed_backlog.append(task)
    return typed_backlog


def find_task(contract: dict[str, Any], path: Path, task_id: str) -> dict[str, Any]:
    for task in require_backlog(contract, path):
        if task.get("id") == task_id:
            return task
    raise TodoError(f"{path} does not contain task {task_id}")


def set_task_status(contract: dict[str, Any], path: Path, task_id: str, status: str) -> dict[str, str]:
    if status not in VALID_STATUSES:
        raise TodoError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")

    task = find_task(contract, path, task_id)
    current = task.get("status")
    if not isinstance(current, str):
        raise TodoError(f"{path} task {task_id} has invalid status")
    if current == status:
        return {"task_id": task_id, "old_status": current, "new_status": status}

    task["status"] = status
    return {"task_id": task_id, "old_status": current, "new_status": status}


def require_string_list(values: object, field_name: str) -> list[str]:
    if not isinstance(values, list) or not values or not all(isinstance(item, str) and item for item in values):
        raise TodoError(f"{field_name} must be a non-empty string list")
    return list(values)


def append_executor_history(task: dict[str, Any], executor: str, reason: str) -> None:
    history = task.get("executor_history")
    if not isinstance(history, list):
        raise TodoError("executor_history must be a list")
    history.append(
        {
            "executor": executor,
            "reason": reason,
            "changed_by": "lead",
        }
    )


def assign_task_executor(
    contract: dict[str, Any],
    path: Path,
    task_id: str,
    executor: str,
    reason: str,
) -> dict[str, str]:
    task = find_task(contract, path, task_id)
    current = task.get("executor")
    if not isinstance(current, str) or not current:
        raise TodoError(f"{path} task {task_id} has invalid executor")
    if not isinstance(executor, str) or not executor:
        raise TodoError("executor must be a non-empty string")
    if not isinstance(reason, str) or not reason.strip():
        raise TodoError("reason must be a non-empty string")

    task["executor"] = executor
    append_executor_history(task, executor, reason.strip())
    return {"task_id": task_id, "old_executor": current, "new_executor": executor}


def approve_task_delegation(
    contract: dict[str, Any],
    path: Path,
    task_id: str,
    executor: str,
    approved_target_files: list[str],
) -> dict[str, Any]:
    task = find_task(contract, path, task_id)
    target_files = require_string_list(task.get("target_files"), f"{path} task {task_id} target_files")
    if approved_target_files != target_files:
        raise TodoError("approved_target_files must exactly match task target_files")
    if task.get("executor") != executor:
        raise TodoError("approved executor must match task executor")

    delegation = task.get("delegation")
    if not isinstance(delegation, dict):
        raise TodoError(f"{path} task {task_id} requires delegation")

    previous_approval = delegation.get("approval")
    delegation["approval"] = "approved"
    delegation["approved_executor"] = executor
    delegation["approved_target_files"] = approved_target_files
    return {
        "task_id": task_id,
        "old_approval": previous_approval,
        "new_approval": "approved",
        "approved_executor": executor,
        "approved_target_files": approved_target_files,
    }


def add_learning(contract: dict[str, Any], path: Path, entry: str) -> dict[str, Any]:
    if not isinstance(entry, str) or not entry.strip():
        raise TodoError("learning entry must be a non-empty string")
    learnings = contract.get("learnings")
    if not isinstance(learnings, list):
        raise TodoError(f"{path} learnings must be a list")
    learnings.append(entry.strip())
    return {"learning": entry.strip(), "learnings_count": len(learnings)}


def slugify_goal(goal: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in goal)
    words = [word for word in normalized.split() if word]
    if not words:
        raise TodoError("goal slug requires at least one ASCII or numeric word")
    slug = "_".join(words[:5])
    return slug[:48].strip("_")


def next_contract_id(goal_dir: Path) -> str:
    max_number = 0
    for path in goal_dir.glob("L-*.yaml"):
        stem = path.stem
        prefix = stem.split("_", 1)[0]
        if not prefix.startswith("L-"):
            continue
        number = prefix[2:]
        if number.isdigit():
            max_number = max(max_number, int(number))
    return f"L-{max_number + 1:03d}"


def create_contract_from_template(template_path: Path, goal_dir: Path, goal: str) -> dict[str, str]:
    if not template_path.exists():
        raise TodoError(f"template not found: {template_path}")

    goal_dir.mkdir(parents=True, exist_ok=True)
    contract_id = next_contract_id(goal_dir)
    slug = slugify_goal(goal)
    contract_path = goal_dir / f"{contract_id}_{slug}.yaml"
    if contract_path.exists():
        raise TodoError(f"contract already exists: {contract_path}")

    template = load_contract(template_path)
    contract = deepcopy(template)
    project = contract.get("project")
    if not isinstance(project, dict):
        raise TodoError(f"{template_path} project must be a mapping")
    project["id"] = contract_id
    project["goal"] = goal

    write_contract(contract_path, contract)
    return {
        "path": str(contract_path),
        "project_id": contract_id,
        "goal": goal,
    }


def classify_contract_status(summary: dict[str, Any], validation_ok: bool) -> str:
    if not validation_ok:
        return "invalid"

    counts = summary["counts"]
    if counts["in_progress"] > 0 or counts["pending"] > 0:
        return "active"
    return "completed"


def extract_open_tasks(summary: dict[str, Any]) -> list[dict[str, Any]]:
    open_tasks: list[dict[str, Any]] = []
    for task in summary["tasks"]:
        if task["status"] in {"pending", "in_progress"}:
            open_tasks.append(
                {
                    "id": task["id"],
                    "title": task["title"],
                    "status": task["status"],
                    "executor": task["executor"],
                }
            )
    return open_tasks


def recommended_contract_reason(contract: dict[str, Any] | None) -> str | None:
    if contract is None:
        return None
    counts = contract["counts"]
    if counts["in_progress"] > 0:
        return "has in_progress tasks"
    if counts["pending"] > 0:
        return "has pending tasks and no in_progress tasks"
    return "no active tasks"


def classify_validation_issue(error: str | None) -> dict[str, str | bool | None]:
    if error is None:
        return {
            "rule": None,
            "category": None,
            "auto_migration_candidate": False,
            "summary": "valid",
        }

    if not error:
        return {
            "rule": "unknown",
            "category": "manual_review_required",
            "auto_migration_candidate": False,
            "summary": "validation failed",
        }

    if "executor must be delegable" in error:
        return {
            "rule": "non_delegable_executor",
            "category": "legacy_schema",
            "auto_migration_candidate": False,
            "summary": "task executor is not delegable under the current schema",
        }
    if "requires delegation" in error or "delegation" in error:
        return {
            "rule": "missing_or_invalid_delegation",
            "category": "missing_delegation",
            "auto_migration_candidate": True,
            "summary": "delegation fields are missing or inconsistent",
        }
    if "project.id must match the file prefix" in error:
        return {
            "rule": "project_id_mismatch",
            "category": "contract_metadata_mismatch",
            "auto_migration_candidate": True,
            "summary": "project.id does not match the contract file prefix",
        }
    if "executor_history" in error:
        return {
            "rule": "executor_history_invalid",
            "category": "legacy_schema",
            "auto_migration_candidate": True,
            "summary": "executor_history is missing or incomplete",
        }

    return {
        "rule": "unknown",
        "category": "manual_review_required",
        "auto_migration_candidate": False,
        "summary": error,
    }


def list_active_contracts(goal_dir: Path, validate_contract: Any) -> dict[str, Any]:
    contracts: list[dict[str, Any]] = []
    completed_contracts_count = 0

    for path in sorted(goal_dir.glob("L-*.yaml")):
        contract = load_contract(path)
        summary = summarize_contract(contract, path)
        validation_error: str | None = None
        try:
            validate_contract(path)
            validation_ok = True
        except TodoError as error:
            validation_ok = False
            validation_error = str(error)
        status = classify_contract_status(summary, validation_ok)
        validation_details = classify_validation_issue(validation_error)
        if status == "completed":
            completed_contracts_count += 1
        contracts.append(
            {
                "path": str(path),
                "project": summary["project"],
                "counts": summary["counts"],
                "open_tasks": extract_open_tasks(summary),
                "status": status,
                "validation": {
                    "ok": validation_ok,
                    "error": validation_error,
                    "rule": validation_details["rule"],
                    "category": validation_details["category"],
                    "auto_migration_candidate": validation_details["auto_migration_candidate"],
                    "summary": validation_details["summary"],
                },
            }
        )

    active_contracts = [contract for contract in contracts if contract["status"] == "active"]
    invalid_contracts = [contract for contract in contracts if contract["status"] == "invalid"]

    def sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
        counts = item["counts"]
        return (
            0 if counts["in_progress"] > 0 else 1,
            -(counts["pending"] + counts["in_progress"]),
            item["path"],
        )

    recommended_contract = sorted(active_contracts, key=sort_key)[0] if active_contracts else None

    return {
        "active_contracts": active_contracts,
        "invalid_contracts": invalid_contracts,
        "completed_contracts_count": completed_contracts_count,
        "recommended_contract": recommended_contract,
        "recommended_reason": recommended_contract_reason(recommended_contract),
    }


def summarize_contract(contract: dict[str, Any], path: Path) -> dict[str, Any]:
    project = contract.get("project")
    if not isinstance(project, dict):
        raise TodoError(f"{path} project must be a mapping")

    backlog = require_backlog(contract, path)
    counts = Counter()
    tasks: list[dict[str, Any]] = []
    for task in backlog:
        status = task.get("status", "unknown")
        counts[status] += 1
        tasks.append(
            {
                "id": task.get("id"),
                "title": task.get("title"),
                "status": status,
                "executor": task.get("executor"),
                "target_files": task.get("target_files"),
            }
        )

    return {
        "path": str(path),
        "project": {
            "id": project.get("id"),
            "goal": project.get("goal"),
        },
        "counts": {
            "total": len(backlog),
            "pending": counts.get("pending", 0),
            "in_progress": counts.get("in_progress", 0),
            "completed": counts.get("completed", 0),
        },
        "tasks": tasks,
        "learnings_count": len(contract.get("learnings", [])) if isinstance(contract.get("learnings"), list) else None,
    }
