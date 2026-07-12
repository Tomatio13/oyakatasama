#!/usr/bin/env python3
"""CLI for compact Oyakatasama goal-contract updates."""

from __future__ import annotations

import argparse
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from todo_lib import (
    TodoError,
    add_learning,
    approve_task_delegation,
    assign_task_executor,
    create_contract_from_template,
    list_active_contracts,
    load_contract,
    set_task_status,
    summarize_contract,
    write_contract,
)
from validate_executors import main as validate_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Oyakatasama goal contracts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Print a compact JSON summary.")
    summary_parser.add_argument("contract", type=Path, help="Path to .todo.yaml or goal contract")

    create_parser = subparsers.add_parser("create", help="Create a new active contract from the template.")
    create_parser.add_argument("goal", help="Concrete goal text written into project.goal")
    create_parser.add_argument("--template", type=Path, default=Path("references/.todo.yaml"), help="Template path")
    create_parser.add_argument("--goal-dir", type=Path, default=Path(".oyakatasama"), help="Active contract directory")

    list_parser = subparsers.add_parser("list-active", help="List active, invalid, and completed contracts.")
    list_parser.add_argument("--goal-dir", type=Path, default=Path(".oyakatasama"), help="Active contract directory")
    list_parser.add_argument("--executors", type=Path, default=Path("executors.yaml"), help="Path to executors.yaml")
    list_parser.add_argument("--format", choices=("json", "text"), default="json", help="Output format")

    status_parser = subparsers.add_parser("set-status", help="Update one task status.")
    status_parser.add_argument("contract", type=Path, help="Path to goal contract")
    status_parser.add_argument("task_id", help="Task ID such as T001")
    status_parser.add_argument("status", help="New status")

    approve_parser = subparsers.add_parser("approve", help="Approve delegation for one task.")
    approve_parser.add_argument("contract", type=Path, help="Path to goal contract")
    approve_parser.add_argument("task_id", help="Task ID such as T001")
    approve_parser.add_argument("executor", help="Approved executor ID")
    approve_parser.add_argument("approved_target_files", nargs="+", help="Approved target files in exact order")

    assign_parser = subparsers.add_parser("assign", help="Assign one task executor and append history.")
    assign_parser.add_argument("contract", type=Path, help="Path to goal contract")
    assign_parser.add_argument("task_id", help="Task ID such as T001")
    assign_parser.add_argument("executor", help="New executor or selector ID")
    assign_parser.add_argument("reason", help="Reason recorded in executor_history")

    learning_parser = subparsers.add_parser("add-learning", help="Append one learning entry.")
    learning_parser.add_argument("contract", type=Path, help="Path to goal contract")
    learning_parser.add_argument("entry", help="One concise learning line")

    validate_parser = subparsers.add_parser("validate", help="Validate executors and a goal contract.")
    validate_parser.add_argument("executors", type=Path, help="Path to executors.yaml")
    validate_parser.add_argument("contract", type=Path, nargs="?", help="Optional goal contract path")

    return parser


def command_summary(contract_path: Path) -> int:
    summary = summarize_contract(load_contract(contract_path), contract_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def command_create(template_path: Path, goal_dir: Path, goal: str) -> int:
    result = create_contract_from_template(template_path, goal_dir, goal)
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


def format_list_active_text(result: dict) -> str:
    lines: list[str] = []
    lines.append(f"recommended_contract: {result['recommended_contract']['path']}" if result["recommended_contract"] else "recommended_contract: none")
    lines.append(f"recommended_reason: {result['recommended_reason'] or 'none'}")
    lines.append(f"active_contracts: {len(result['active_contracts'])}")
    for contract in result["active_contracts"]:
        counts = contract["counts"]
        lines.append(
            f"- active {contract['project']['id']} {contract['path']} pending={counts['pending']} in_progress={counts['in_progress']} completed={counts['completed']}"
        )
        for task in contract["open_tasks"]:
            lines.append(f"  - {task['status']} {task['id']} {task['title']}")
    lines.append(f"invalid_contracts: {len(result['invalid_contracts'])}")
    for contract in result["invalid_contracts"]:
        validation = contract["validation"]
        lines.append(
            f"- invalid {contract['project']['id']} {contract['path']} category={validation['category']} auto_migration_candidate={validation['auto_migration_candidate']}"
        )
        lines.append(f"  - rule={validation['rule']}")
        lines.append(f"  - summary={validation['summary']}")
    lines.append(f"completed_contracts_count: {result['completed_contracts_count']}")
    return "\n".join(lines)


def command_list_active(goal_dir: Path, executors_path: Path, output_format: str) -> int:
    def validate_one(contract_path: Path) -> None:
        argv = [str(executors_path), str(contract_path)]
        original_argv = sys.argv[:]
        try:
            sys.argv = ["validate_executors.py", *argv]
            stderr_buffer = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr_buffer):
                validate_main()
        except SystemExit as error:
            code = error.code if isinstance(error.code, int) else 1
            if code != 0:
                stderr_text = stderr_buffer.getvalue().strip()
                if stderr_text:
                    raise TodoError(stderr_text)
                raise TodoError(f"validation failed for {contract_path}")
        finally:
            sys.argv = original_argv

    result = list_active_contracts(goal_dir, validate_one)
    if output_format == "text":
        print(format_list_active_text(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_set_status(contract_path: Path, task_id: str, status: str) -> int:
    contract = load_contract(contract_path)
    result = set_task_status(contract, contract_path, task_id, status)
    write_contract(contract_path, contract)
    print(json.dumps({"ok": True, **result, "path": str(contract_path)}, ensure_ascii=False, indent=2))
    return 0


def command_approve(contract_path: Path, task_id: str, executor: str, approved_target_files: list[str]) -> int:
    contract = load_contract(contract_path)
    result = approve_task_delegation(contract, contract_path, task_id, executor, approved_target_files)
    write_contract(contract_path, contract)
    print(json.dumps({"ok": True, **result, "path": str(contract_path)}, ensure_ascii=False, indent=2))
    return 0


def command_assign(contract_path: Path, task_id: str, executor: str, reason: str) -> int:
    contract = load_contract(contract_path)
    result = assign_task_executor(contract, contract_path, task_id, executor, reason)
    write_contract(contract_path, contract)
    print(json.dumps({"ok": True, **result, "reason": reason, "path": str(contract_path)}, ensure_ascii=False, indent=2))
    return 0


def command_add_learning(contract_path: Path, entry: str) -> int:
    contract = load_contract(contract_path)
    result = add_learning(contract, contract_path, entry)
    write_contract(contract_path, contract)
    print(json.dumps({"ok": True, **result, "path": str(contract_path)}, ensure_ascii=False, indent=2))
    return 0


def command_validate(executors_path: Path, contract_path: Path | None) -> int:
    argv = [str(executors_path)]
    if contract_path is not None:
        argv.append(str(contract_path))
    original_argv = sys.argv[:]
    try:
        sys.argv = ["validate_executors.py", *argv]
        validate_main()
    finally:
        sys.argv = original_argv
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "summary":
            return command_summary(args.contract)
        if args.command == "create":
            return command_create(args.template, args.goal_dir, args.goal)
        if args.command == "list-active":
            return command_list_active(args.goal_dir, args.executors, args.format)
        if args.command == "set-status":
            return command_set_status(args.contract, args.task_id, args.status)
        if args.command == "approve":
            return command_approve(args.contract, args.task_id, args.executor, args.approved_target_files)
        if args.command == "assign":
            return command_assign(args.contract, args.task_id, args.executor, args.reason)
        if args.command == "add-learning":
            return command_add_learning(args.contract, args.entry)
        if args.command == "validate":
            return command_validate(args.executors, args.contract)
    except TodoError as error:
        print(f"todo_cli error: {error}", file=sys.stderr)
        return 1
    except SystemExit as error:
        code = error.code if isinstance(error.code, int) else 1
        return code

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
