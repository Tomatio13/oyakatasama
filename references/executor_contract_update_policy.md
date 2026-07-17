# Executor contract update policy

This file defines how delegated executors interact with goal contracts. The Lead enforces this policy. Do not assume external executors will discover or apply it on their own.

Launch and process monitoring for the task executor are routed through a direct child **executor-runner** Subagent. See [executor_runner.md](executor_runner.md) for the wait boundary and return package. The runner is not a contract editor and is not an `executors.yaml` ID.

## Responsibility split

| Area | Lead responsibility | Executor-runner responsibility | Executor responsibility |
|---|---|---|---|
| contract creation | yes | no | no |
| backlog structure changes | yes | no | no |
| `project.constraints` changes | yes | no | no |
| `project.success_criteria` changes | yes | no | no |
| executor selection | yes | no | no |
| `executor_history` updates | yes | no | no |
| `delegation` updates | yes | no | no |
| spawn runner and wait for completion | yes | n/a | no |
| invoke approved executor command and monitor exit | no | yes | n/a |
| task status update | yes | no | yes, only assigned task |
| `learnings` append | yes | no | yes, concise line only |
| edit task `target_files` | no | no | yes, assigned only |
| final validation and review | yes | no | no |

## Fields executors may edit

Executors may edit only:

- their assigned task's `status`, using `scripts/todo_cli.py set-status`;
- `learnings`, by appending one concise project-specific line with `scripts/todo_cli.py add-learning`;
- the task `target_files` they were assigned to change.

Executors must not edit:

- `project.*`;
- any other task;
- `executor`;
- `executor_history`;
- `delegation`;
- contract YAML directly for status or learning updates;
- `references/.todo.yaml`.

## Fields the executor-runner may edit

None. The runner launches and monitors the approved executor only. It must not edit the contract, `target_files`, routing fields, or approvals. It must not mark verification passed for the Lead.

## Why Codex must enforce this

External executors such as `agy`, `grok`, or `opencode` operate only on the prompt they are given. They should not be trusted to infer the full contract-management policy from repository files.

The executor-runner Subagent likewise receives only the invocation package the Lead provides. It must not invent new approvals, re-route selection, or treat the executor self-report as final verification.

Therefore the Lead must:

1. choose the route;
2. record `assign` and `approve` changes before delegation;
3. pass a constrained executor prompt inside the runner invocation package;
4. spawn a direct-child executor-runner Subagent and wait for its completion (do not run the executor command in the Lead session);
5. run independent verification and `validate` after the runner returns;
6. keep Reviewer launch in the Lead session.

## Executor prompt requirements

When delegating, include contract-update limits explicitly. The prompt should tell the executor:

- read the active contract first;
- work only on the assigned task IDs and `target_files`;
- set the assigned task `in_progress` with `python3 <skill-dir>/scripts/todo_cli.py set-status <active-contract-path> <task-id> in_progress` before editing;
- run the task verification;
- set the assigned task `completed` with `python3 <skill-dir>/scripts/todo_cli.py set-status <active-contract-path> <task-id> completed` only after verification succeeds;
- append any project-specific lesson only with `python3 <skill-dir>/scripts/todo_cli.py add-learning <active-contract-path> "<entry>"`;
- leave failures as `in_progress` and report the exact blocker;
- do not update status or learnings by editing YAML directly;
- do not edit `executor`, `executor_history`, or `delegation`;
- do not change contract structure;
- do not touch `references/.todo.yaml`;
- do not review.

## Runner prompt requirements

When spawning the executor-runner, require it to:

- launch only the provided expanded command and args;
- wait for process completion;
- return only `exit_code`, `changed_files`, `executor_self_reported_verification`, and `unresolved_issues`;
- refuse new approvals, re-routing, `target_files` edits, final verification judgment, and review.

Full runner rules live in `references/executor_runner.md`.

## Minimal operating rule

Treat delegated executors as bounded implementers, not as contract orchestrators. Treat the executor-runner as a launch-and-monitor shell only. Contract orchestration, independent verification, and review remain with the Lead.
