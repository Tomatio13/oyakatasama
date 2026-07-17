# Executor-runner subagent policy

This file defines how the Lead launches and monitors delegated executors through a direct child **executor-runner** Subagent. The Lead enforces this policy. Do not assume any harness will invent the wait boundary on its own.

The runner is a **workflow role**, not an `executors.yaml` executor ID. It does not appear under `executors` or `selection`.

## Architecture

```text
Lead (parent session)
  └─ executor-runner Subagent  (direct child only)
        └─ task executor command  (from executors.yaml)
```

- The Lead **must not** invoke a task executor `command` directly in the Lead session.
- The Lead **must** spawn exactly one direct-child executor-runner Subagent per delegated task batch, pass the already-approved invocation, and **wait** for that runner to finish before continuing Step 5.
- The runner **must not** spawn further routing Subagents, re-select executors, or open a Reviewer session.
- Prefer a skill-local runner prompt/contract over project-specific agent config (for example `.codex/agents`). The wait flow must work from any install path of this skill.

## Responsibility split

| Area | Lead | executor-runner | Task executor |
|---|---|---|---|
| contract creation / backlog structure | yes | no | no |
| `executor` / `executor_history` / `delegation` | yes | no | no |
| external transmission and runtime-escalation approval | yes | no | no |
| spawn runner and wait for completion | yes | n/a | no |
| expand `{skill_dir}`, `{repo}`, `{model}`, `{prompt}` and run executor `command` | no | yes | n/a |
| monitor executor process (exit code, timeout, failure logs) | no | yes | n/a |
| edit task `target_files` | no | no | yes, assigned only |
| task `status` / `learnings` via `todo_cli.py` | yes | no | yes, assigned only |
| treat self-report as final verification | no | no | may self-run checks only |
| independent local verification and `validate` | yes | no | no |
| Reviewer launch and review decisions | yes | no | no |

## What the Lead must do

Before spawning the runner:

1. Finish Steps 0–4 for the tasks being delegated (contract filled, external approval recorded when required, selection resolved when required).
2. Confirm the task `executor` is delegable and, if external, exactly matches `delegation.approved_executor` and `delegation.approved_target_files`.
3. Read this file and `references/executor_contract_update_policy.md`.
4. Build the constrained executor prompt (active contract path, task IDs, `target_files`, `todo_cli.py` status rules, and contract-update limits).
5. Expand the executor `command` and `args` placeholders to absolute values the runner can execute without relying on the caller's working directory.

When spawning the runner:

1. Use a **direct child** Subagent only (Lead → runner). Do not insert intermediate orchestrators.
2. Pass only the already-approved invocation package: executor ID, expanded command and args, model, task IDs, `target_files`, active contract path, skill directory, and the constrained executor prompt.
3. Do not grant the runner authority to change routing, approval, contract structure, or verification outcome.
4. **Wait** until the runner reports completion. Do not attach to or stream-monitor the executor process from the Lead session while the runner is active.
5. After the runner returns, independently run each task's `verification` (and contract validation when needed). Never accept the executor's or runner's self-report as proof of completion.
6. Keep Reviewer launch (Step 6) in the Lead session.

## What the runner may do

- Invoke the exact expanded executor `command` + `args` non-interactively.
- Wait for the process to exit; collect exit code, retained failure log paths when the quiet wrapper reports them, and the executor's stdout/stderr summary when available.
- Observe which files changed relative to the pre-invocation baseline when the harness allows it.
- Relay the executor's self-reported verification text without elevating it to a final pass/fail judgment.
- Return a compact result package to the Lead (see below).

## What the runner must not do

- Request or record new external-delegation approvals.
- Re-run CodexBar, re-resolve `selection`, switch fallback executors, or rewrite `executor` / `executor_history` / `delegation`.
- Edit any task `target_files` or any other repository file except by launching the already-approved executor.
- Edit the goal contract YAML (including status, learnings, project fields, or backlog structure).
- Decide that verification has passed for the goal, mark tasks `completed` on behalf of policy, or skip Lead verification.
- Launch the Reviewer, close review findings, or approve work.
- Spawn nested runners or re-route to a different provider when the approved executor fails to start.

## Runner return package

The runner returns **only** these fields to the Lead:

```text
exit_code: <process exit code, or start-failure code>
changed_files: <paths observed after the run, or unknown>
executor_self_reported_verification: <executor's claimed check results, or none>
unresolved_issues: <start failures, timeouts, non-zero exits, missing outputs, or none>
```

Optional diagnostic lines (failure log paths, brief stderr excerpts) may appear under `unresolved_issues` when they help the Lead decide the next action. The runner must not claim `verification: passed` as a Lead-level decision.

## Failure handling

| Condition | Runner action | Lead action after wait |
|---|---|---|
| Executor starts and exits 0 | Return exit code and reports | Run independent verification; set status via normal rules only if verification passes |
| Executor exits non-zero | Return exit code, log paths, unresolved issues | Keep or leave task `in_progress` / record blocker; no automatic provider switch |
| Executor cannot start (sandbox, log path, socket, permission) | Return start failure; do not retry other providers | Leave task `pending`, append exact error to `executor_history`, stop |
| Timeout or harness kill | Return unresolved timeout | Treat as failure; Lead decides retry or escalation |

## Runner prompt requirements

When the Lead spawns the runner, the runner prompt must state:

- you are an executor-runner Subagent, not the Lead and not the task executor;
- launch only the provided expanded command and args;
- wait for the process to finish;
- do not edit `target_files`, the contract, routing, or approvals;
- do not run final verification or review;
- return only `exit_code`, `changed_files`, `executor_self_reported_verification`, and `unresolved_issues`.

Include the already-built executor prompt as payload for the executor command's `{prompt}` expansion. The runner must not rewrite that payload to broaden scope.

## Minimal operating rule

Treat the executor-runner as a **launch-and-monitor shell** around one approved executor invocation. Judgment, contract orchestration, independent verification, and review remain with the Lead.
