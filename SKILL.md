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

Use only an executor ID defined under `executors`, except for a selector ID defined under `selection`. Expand `{repo}`, `{model}`, and `{prompt}` in its `args` before invoking its `command`; do not add unlisted flags or silently substitute a model. Keep architecture, security decisions, acceptance decisions, and final sign-off in the configured Lead session.

## Workflow

### 1. Initialize the goal-specific task contract

Before delegation or any code edit, select exactly one active contract under project-root `.oyakata/`.

1. For a new user-visible goal, create `.oyakata/` if needed and copy [references/.todo.yaml](references/.todo.yaml) from this skill to `.oyakata/L-<next-number>_<short-goal>.yaml`. Never overwrite or reuse an existing contract.
2. Determine `<next-number>` from the greatest existing `L-NNN_*.yaml` number plus one, zero-padded to at least three digits. Start at `001` when none exists.
3. Use a concise lowercase ASCII `<short-goal>` of two to five words joined by underscores, for example `auth_refactor` or `payment_api`.
4. For a follow-up to an existing goal, reuse only that goal's contract. Identify its exact path before delegating; do not create a second contract for the same goal.
5. Read the active contract's `project.goal`, `project.constraints`, `project.success_criteria`, and every `backlog` item.
6. Replace template placeholders with the user-visible goal, constraints, success criteria, and bounded tasks before assigning work. Give every task a stable ID, exact `target_files`, a local `verification` command or objective manual procedure, and an `executor`.

Set each task's `executor` to an `executors` or `selection` key in `executors.yaml`. Use a selector only when the Lead intentionally delegates the implementation choice to that selector's quota rule.

The active `.oyakata/L-NNN_<short-goal>.yaml` is the single source of truth for that goal's scope and progress. Completed contracts remain in `.oyakata/` as immutable goal history, except for a later Lead-created remediation task for the same goal. The Lead owns contract selection, task creation, task assignment, review decisions, and the project contract. Executors may update only the status of their assigned task and append a concise project-specific item to `learnings` after a verified completion. Only the Lead may change a task's `executor`; append each assignment or reassignment to `executor_history` without overwriting earlier entries.

### 2. Follow the four-part operating protocol

Before changing even one line of implementation or documentation, the Lead and every executor must:

1. **Fix the context:** Read the active goal contract, confirm `project.goal` and `project.constraints`, change the assigned task from `pending` to `in_progress`, and save it.
2. **Respect the edit boundary:** Edit only paths in that task's `target_files`. The only exception is the active goal contract, which executors may update solely for the assigned task's status and `learnings`; the Lead may additionally update `executor` and append an `executor_history` entry before execution. Do not add unrequested code or files.
3. **Verify objectively:** Run the task's `verification` locally after implementation. Do not start another task unless it exits successfully (`exit 0`) or its stated manual check passes completely.
4. **Synchronize progress and learning:** After successful verification, change the task status to `completed`. If a project-specific bug pattern or specification trap was found, append it as one concise line to `learnings` before handing off.

If verification fails, keep the task `in_progress`, record no completion, and report the exact command and failure to the Lead. Do not weaken, skip, or replace the specified verification without the Lead's explicit task-contract update.

### 3. Classify the work

- Keep planning, architecture, investigation conclusions, risk decisions, and review in the configured Lead session.
- Assign every task an explicit `executor` in the active goal contract; honor it instead of inferring from the task title or file type.
- Use a `selection` key only for code changes, tests, mechanical refactors, and implementation-focused debugging that the Lead wants CodexBar to route.
- Use the `research` executor IDs from `executors.yaml` for web and X research.
- For a mixed task, split code and documentation into separate tasks. Review both in the configured Reviewer session.
- Handle a trivial one-file edit directly only when delegation overhead is larger than the work.

### 4. Select an implementation executor

For a task assigned to a `selection` key, immediately before delegation, use the user-installed official CodexBar CLI. Never download, install, update, or configure CodexBar during an Oyakata run.

```bash
codexbar usage --provider <candidate quota_provider> --format json --pretty --no-color
```

For a selector, read every executor ID from `selection.<selector>.candidates`, resolve each `quota_provider`, then run and parse one command per candidate. If `codexbar` is not on `PATH`, a command returns a non-zero exit status, or a response cannot be parsed, set the task's `executor` to `selection.<selector>.fallback_executor`, append the reason to `executor_history`, and delegate with that configured executor.

If CodexBar succeeds, read the configured quota-provider entries. For each provider:

1. Reject an entry that is disabled, stale without usable quota data, or reports an error.
2. Inspect every applicable rate-limit window, including primary, secondary, tertiary, and extra windows.
3. Calculate `safe_remaining` as the minimum available `remainingPercent`. If only `usedPercent` exists, use `100 - usedPercent`.
4. Calculate `next_reset` as the earliest future reset among the windows that determine `safe_remaining`.
5. Never infer unlimited capacity from a missing window or missing percentage.

For a selector, choose among its configured candidates with this order:

1. Discard candidates without valid quota data.
2. Find the highest `safe_remaining` among the remaining candidates.
3. Keep every remaining candidate within 5 percentage points of that highest value, then choose the earliest `next_reset` among them.
4. If candidates remain tied, choose `selection.<selector>.tie_breaker` when it is tied; otherwise choose the first tied candidate in `candidates` order.
5. If no candidate has valid data, set `executor` to `selection.<selector>.fallback_executor`, append the unavailable quota data to `executor_history`, and use that configured executor.

Do not use reset proximity to justify sending work to a provider with materially less remaining quota. Re-run the command before every new executor task; do not reuse an old result across phases.

Record the actual executor in the task's `executor` and append a decision to `executor_history`:

```text
executor: <selected executor ID>
executor_history:
  - executor: <selected executor ID>
    reason: "Quota: <candidate>=<safe_remaining>; Reset: <candidate>=<next_reset>; <reason>"
    changed_by: lead
```

### 5. Delegate implementation

Use non-interactive commands so the Lead can capture and review the result. Preserve repository instructions and least-privilege permissions.

Read each task's `executor` before delegation. Run the corresponding command, arguments, and model from `executors.yaml`; run the configured Lead executor in the current Lead session. Build every executor prompt with the active goal-contract absolute path, its assigned task IDs, each assigned task's `target_files`, and the following mandatory instructions:

```text
Read <active-contract-path>. Assigned task IDs: <IDs>. Work only on those tasks and their target_files. Set each task in_progress before editing. Run its verification. Set completed only after success. Leave failures in_progress and report the exact blocker. Do not review.
```

1. Read `project` and its assigned `pending` task IDs before editing.
2. Change each assigned task to `in_progress` before editing and work only on its `target_files`.
3. Run each task's verification command.
4. Set a task to `completed` only after its verification passes, and append any project-specific learning.
5. Keep a failed task `in_progress` and return the exact blocker.
6. Stop after all assigned tasks complete or one is blocked; do not perform Codex review.

Run the executor in an isolated branch or worktree for non-trivial changes when the active harness supports it. Do not grant bypass permissions by default. Tell the executor to return only files changed, verification results, and unresolved issues.

### 6. Delegate documentation

Give the configured documentation executor only task IDs assigned to its executor ID. Require it to inspect implemented behavior and relevant tests, use only its configured command and model, and follow the same status, file-boundary, verification, and learning rules as an implementation executor.

### 7. Review in the configured Reviewer session

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

### 8. Rework loop

For `changes_requested`:

1. Refresh CodexBar usage instead of automatically reusing the previous executor.
2. Keep the remediation task's explicit `executor`; use the normal quota rule only when it names a `selection` key.
3. Delegate only the `pending` remediation task IDs and their review findings.
4. Require the executor to correct, verify, set the remediation task to `completed`, and append any relevant learning.
5. Return to Codex and perform a new full review of the resulting diff, not only the latest patch.
6. Repeat until Codex approves or an escalation condition is met.

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
