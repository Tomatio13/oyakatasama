# Executor contract update policy

This file defines how delegated executors interact with goal contracts. The Lead enforces this policy. Do not assume external executors will discover or apply it on their own.

## Responsibility split

| Area | Lead responsibility | Executor responsibility |
|---|---|---|
| contract creation | yes | no |
| backlog structure changes | yes | no |
| `project.constraints` changes | yes | no |
| `project.success_criteria` changes | yes | no |
| executor selection | yes | no |
| `executor_history` updates | yes | no |
| `delegation` updates | yes | no |
| task status update | yes | yes, only assigned task |
| `learnings` append | yes | yes, concise line only |
| final validation and review | yes | no |

## Fields executors may edit

Executors may edit only:

- their assigned task's `status`;
- `learnings`, by appending one concise project-specific line;
- the task `target_files` they were assigned to change.

Executors must not edit:

- `project.*`;
- any other task;
- `executor`;
- `executor_history`;
- `delegation`;
- `references/.todo.yaml`.

## Why Codex must enforce this

External executors such as `agy`, `grok`, or `opencode` operate only on the prompt they are given. They should not be trusted to infer the full contract-management policy from repository files.

Therefore the Lead must:

1. choose the route;
2. record `assign` and `approve` changes before delegation;
3. pass a constrained executor prompt;
4. run verification and `validate` after the delegated work returns.

## Executor prompt requirements

When delegating, include contract-update limits explicitly. The prompt should tell the executor:

- read the active contract first;
- work only on the assigned task IDs and `target_files`;
- set the assigned task `in_progress` before editing;
- run the task verification;
- set the assigned task `completed` only after verification succeeds;
- leave failures as `in_progress` and report the exact blocker;
- do not edit `executor`, `executor_history`, or `delegation`;
- do not change contract structure;
- do not touch `references/.todo.yaml`;
- do not review.

## Minimal operating rule

Treat delegated executors as bounded implementers, not as contract orchestrators. Contract orchestration remains with the Lead.
