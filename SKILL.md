---
name: oyakata
description: Orchestrate software work with a user-editable executors.yaml, one .oyakata/L-NNN_short_goal.yaml local task contract per goal, task-level executor assignment, and CodexBar quota-aware routing. Use for non-trivial implementation, review, refactoring, testing, research, or documentation tasks that benefit from role separation and configurable commands and models.
---

# Oyakata

Separate judgment, implementation, and documentation. Keep the configured Lead in control of scope and quality; delegate bounded production work to task-assigned executors.

## Runtime definitions

Before creating a goal contract or delegating work, read [executors.yaml](executors.yaml) from this skill directory. It is the only source of truth for the Lead, Reviewer, executor IDs, commands, arguments, models, quota-provider mappings, research routing, and quota-selection candidates.

Run the configuration check before creating or assigning a task. It must exit 0:

```bash
python3 <skill-dir>/scripts/validate_executors.py <skill-dir>/executors.yaml <skill-dir>/references/.todo.yaml
```

Use only an executor ID defined under `executors`, except for a selector ID defined under `selection`. A task executor MUST have `delegable: true`; the configured Lead and Reviewer MUST NOT implement task `target_files`. Expand `{repo}`, `{model}`, and `{prompt}` in its `args` before invoking its `command`; do not add unlisted flags or silently substitute a model. Keep architecture, security decisions, acceptance decisions, and final sign-off in the configured Lead session.

## Workflow

### 1. Initialize the goal-specific task contract

Before delegation or any code edit, select exactly one active contract under project-root `.oyakata/`.

1. For a new user-visible goal, create `.oyakata/` if needed and copy [references/.todo.yaml](references/.todo.yaml) from this skill to `.oyakata/L-<next-number>_<short-goal>.yaml`. Never overwrite or reuse an existing contract.
2. Determine `<next-number>` from the greatest existing `L-NNN_*.yaml` number plus one, zero-padded to at least three digits. Start at `001` when none exists.
3. Use a concise lowercase ASCII `<short-goal>` of two to five words joined by underscores, for example `auth_refactor` or `payment_api`.
4. For a follow-up to an existing goal, reuse only that goal's contract. Identify its exact path before delegating; do not create a second contract for the same goal.
5. Read the active contract's `project.goal`, `project.constraints`, `project.success_criteria`, and every `backlog` item.
6. Replace template placeholders with the user-visible goal, constraints, success criteria, and bounded tasks before assigning work. Give every task a stable ID, exact `target_files`, a local `verification` command or objective manual procedure, a delegable `executor`, and a `delegation` record.

Set each task's `executor` to a delegable `executors` or `selection` key in `executors.yaml`. Never assign the configured Lead or Reviewer as a task executor. Use a selector only when the Lead intentionally delegates the implementation choice to that selector's quota rule.

The active `.oyakata/L-NNN_<short-goal>.yaml` is the single source of truth for that goal's scope and progress. Completed contracts remain in `.oyakata/` as immutable goal history, except for a later Lead-created remediation task for the same goal. The Lead owns contract selection, task creation, task assignment, review decisions, and the project contract. Executors may update only the status of their assigned task and append a concise project-specific item to `learnings` after a verified completion. Only the Lead may change a task's `executor`, `delegation`, or `executor_history`; append each assignment or reassignment to `executor_history` without overwriting earlier entries.

### 2. Follow the four-part operating protocol

Before changing even one line of implementation or documentation, the Lead and every executor must:

1. **Fix the context:** Read the active goal contract, confirm `project.goal` and `project.constraints`, change the assigned task from `pending` to `in_progress`, and save it.
2. **Respect the edit boundary:** Edit only paths in that task's `target_files`. The only exception is the active goal contract, which executors may update solely for the assigned task's status and `learnings`; the Lead may additionally update `executor`, `delegation`, and `executor_history` before execution. Do not add unrequested code or files.
3. **Verify objectively:** Run the task's `verification` locally after implementation. Do not start another task unless it exits successfully (`exit 0`) or its stated manual check passes completely.
4. **Synchronize progress and learning:** After successful verification, change the task status to `completed`. If a project-specific bug pattern or specification trap was found, append it as one concise line to `learnings` before handing off.

If verification fails, keep the task `in_progress`, record no completion, and report the exact command and failure to the Lead. Do not weaken, skip, or replace the specified verification without the Lead's explicit task-contract update.

### 3. Classify the work

- Keep planning, architecture, investigation conclusions, risk decisions, and review in the configured Lead session.
- Assign every task an explicit `executor` in the active goal contract; honor it instead of inferring from the task title or file type.
- Use a `selection` key only for code changes, tests, mechanical refactors, and implementation-focused debugging that the Lead wants CodexBar to route.
- Use the `research` executor IDs from `executors.yaml` for web and X research.
- For a mixed task, split code and documentation into separate tasks. Review both in the configured Reviewer session.
- The Lead may create contracts, select executors, verify, and review. It MUST NOT edit implementation or documentation `target_files`, including trivial one-file tasks.

### 4. Confirm external delegation

Before invoking an executor whose `data_boundary` is `external_service`, or running a quota selector's CodexBar lookup, inspect `project.constraints`. If any constraint prohibits external APIs, external servers, or data transmission, do not run the lookup or delegate externally; leave the task `pending` and report the conflict to the user.

Otherwise, request explicit approval before any external executor command, including a runtime check. State the executor ID and model, the exact task IDs, the exact `target_files`, and that the task contract and relevant file contents may be sent to the external service. Do not treat a request to "delegate" as approval of a specific external provider and file scope.

After approval, set `delegation.approval` to `approved`, set `approved_executor` to the selected executor, and set `approved_target_files` to the exact task file list. The selected executor and files MUST exactly match this record. A different fallback executor requires a new approval.

### 5. Select an implementation executor

For a task assigned to a `selection` key, immediately before delegation, use the user-installed official CodexBar CLI. Never download, install, update, or configure CodexBar during an Oyakata run.

```bash
codexbar usage --provider <candidate quota_provider> --format json --pretty --no-color
```

For a selector, read every executor ID from `selection.<selector>.candidates`, resolve each `quota_provider`, then run and parse one command per candidate. If `codexbar` is not on `PATH`, a command returns a non-zero exit status, or a response cannot be parsed, set the task's `executor` to `selection.<selector>.fallback_executor` and append the reason to `executor_history`. Do not invoke the fallback until its exact external-delegation approval has been recorded.

If CodexBar succeeds, read each candidate's configured `quota_windows` only. For each candidate:

1. Reject an entry that is disabled, stale without usable quota data, or reports an error.
2. Read only `usage.<window>` for every window listed in that candidate's `quota_windows`. Ignore every unlisted usage window, even if it is exhausted.
3. Calculate `safe_remaining` as the minimum `remainingPercent` across the configured windows. If only `usedPercent` exists, use `100 - usedPercent`.
4. Calculate `next_reset` as the earliest future reset among the configured windows that determine `safe_remaining`.
5. Never infer unlimited capacity from a missing configured window or missing percentage.

For a selector, choose among its configured candidates with this order:

1. Discard candidates without valid quota data.
2. Find the highest `safe_remaining` among the remaining candidates.
3. Keep every remaining candidate within 5 percentage points of that highest value, then choose the earliest `next_reset` among them.
4. If candidates remain tied, choose `selection.<selector>.tie_breaker` when it is tied; otherwise choose the first tied candidate in `candidates` order.
5. If no candidate has valid data, set `executor` to `selection.<selector>.fallback_executor` and append the unavailable quota data to `executor_history`. Do not invoke it until its exact external-delegation approval has been recorded.

Do not use reset proximity to justify sending work to a provider with materially less remaining quota. Re-run the command before every new executor task; do not reuse an old result across phases.

Record the actual executor in the task's `executor` and append a decision to `executor_history`:

```text
executor: <selected executor ID>
executor_history:
  - executor: <selected executor ID>
    reason: "Quota: <candidate>=<safe_remaining>; Reset: <candidate>=<next_reset>; <reason>"
    changed_by: lead
```

### 6. Delegate implementation

Use non-interactive commands so the Lead can capture and review the result. Preserve repository instructions and least-privilege permissions.

Read each task's `executor` before delegation. Refuse a non-delegable executor. For an external executor, require the exact approved `delegation` record before invoking its configured command. If `requires_unsandboxed_runtime` is true, request the already-approved least-privilege runtime escalation before invocation; do not first run it in a sandbox that cannot write its logs or bind required loopback sockets. Build every executor prompt with the active goal-contract absolute path, its assigned task IDs, each assigned task's `target_files`, and the following mandatory instructions:

```text
Read <active-contract-path>. Assigned task IDs: <IDs>. Work only on those tasks and their target_files. Set each task in_progress before editing. Run its verification. Set completed only after success. Leave failures in_progress and report the exact blocker. Do not review.
```

1. Read `project` and its assigned `pending` task IDs before editing.
2. Change each assigned task to `in_progress` before editing and work only on its `target_files`.
3. Run each task's verification command.
4. Set a task to `completed` only after its verification passes, and append any project-specific learning.
5. Keep a failed task `in_progress` and return the exact blocker.
6. Stop after all assigned tasks complete or one is blocked; do not perform Codex review.

Run the executor in an isolated branch or worktree for non-trivial changes when the active harness supports it. Do not grant bypass permissions by default. If the executor cannot start because of sandbox filesystem, log-path, socket, or permission errors, leave the task `pending`, append the exact error to `executor_history`, and stop. Do not automatically retry, switch providers, or send the project to another external executor. Tell the executor to return only files changed, verification results, and unresolved issues.

### 7. Delegate documentation

Give the configured documentation executor only task IDs assigned to its executor ID. Require it to inspect implemented behavior and relevant tests, use only its configured command and model, and follow the same status, file-boundary, verification, and learning rules as an implementation executor.

### 8. Review in the configured Reviewer session

Do not start review until every assigned backlog task is `completed`. If any task remains `pending` or `in_progress`, resolve its route before review rather than pretending the phase is complete.

The configured Reviewer must inspect the actual diff and independently run appropriate verification. Reject work when:

- acceptance criteria are missing;
- tests fail or relevant error cases lack coverage;
- unrelated files changed;
- secrets, credentials, or unsafe permissions appear;
- documentation disagrees with code or runtime behavior;
- the executor made an architecture or risk decision reserved for the Lead.

Never accept an executor's self-report as verification.

Record review findings in the Lead's handoff with a stable ID such as `R1-01`, severity, affected file, required correction, and verification command. On changes requested, add a new `pending` remediation task such as `R1-01` to the active goal contract; do not reopen a completed original task. Keep remediation `target_files` exact and use a real verification command.

### 9. Rework loop

For `changes_requested`:

1. Refresh CodexBar usage instead of automatically reusing the previous executor.
2. Keep the remediation task's explicit `executor`; use the normal quota rule only when it names a `selection` key.
3. Obtain a new exact external-delegation approval for any external executor and remediation file scope.
4. Delegate only the `pending` remediation task IDs and their review findings.
5. Require the executor to correct, verify, set the remediation task to `completed`, and append any relevant learning.
6. Return to the configured Reviewer and perform a new full review of the resulting diff, not only the latest patch.
7. Repeat until the configured Reviewer approves or an escalation condition is met.

Do not let an executor mark review findings resolved, change review status, or approve its own work. The configured Reviewer alone closes findings through the next review result.

## Escalation

Return implementation to the configured Lead when:

- security, authentication, payments, privacy, data loss, or production incidents are involved;
- the task requires a non-obvious architecture or product tradeoff;
- the selected executor fails the same acceptance check twice;
- two review rounds reject the same underlying issue;
- every quota-selector candidate is unavailable or unsafe;
- the generated diff is too broad to review reliably.

After one executor fails for a provider-specific reason, refresh CodexBar usage before trying the selector's next eligible candidate. Do not alternate indefinitely.

## Completion report

End with:

```text
Result: <completed or blocked>
Lead/Reviewer: <executors.yaml lead and reviewer IDs plus models>
Task contract: <.oyakata/L-NNN_short_goal.yaml path and task statuses>
Implementation route: <executor IDs plus models from executors.yaml>
Documentation route: <executor ID plus model from executors.yaml | none>
Routing evidence: <remaining quota and reset comparison>
Review rounds: <count and final decision>
Verification: <commands and results>
Unresolved: <none or concise list>
```
