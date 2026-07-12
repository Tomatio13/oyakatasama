---
name: oyakatasama
description: Orchestrate software work with a user-editable executors.yaml, one .oyakatasama/L-NNN_short_goal.yaml local task contract per goal, task-level executor assignment, and CodexBar quota-aware routing. Use for non-trivial implementation, review, refactoring, testing, research, or documentation tasks that benefit from role separation and configurable commands and models.
---

# oyakatasama

Separate judgment, implementation, and documentation. The configured Lead controls scope, quality, and sign-off; bounded production work goes to task-assigned executors.

`<skill-dir>` below means the directory that contains this SKILL.md. Resolve it to an absolute path once, at the start of the run.

## Hard rules — apply at every step

- The configured Lead and Reviewer MUST NOT edit any task `target_files`, even for trivial one-file tasks. Architecture, security decisions, acceptance decisions, and final sign-off stay in the Lead session.
- [executors.yaml](executors.yaml) in `<skill-dir>` is the only source of truth for the Lead, Reviewer, executor IDs, commands, args, models, quota-provider mappings, research routing, and selectors. Use only IDs defined under `executors` or `selection`. A task executor MUST have `delegable: true`.
- Expand `{repo}`, `{model}`, and `{prompt}` in an executor's `args` before invoking its `command`. Expand `{skill_dir}` to the absolute path of the skill directory (the directory containing executors.yaml) in both `command` and `args`, so a path-like command such as `{skill_dir}/scripts/executor_quiet.sh` resolves the same way regardless of the caller's working directory. Never add unlisted flags, silently substitute a model, or leave a `{skill_dir}` command relative to the caller's cwd.
- The active `.oyakatasama/L-NNN_<short-goal>.yaml` contract is the single source of truth for that goal's scope and progress. Executors may change only their assigned task's `status` and append to `learnings`. Only the Lead changes `executor`, `delegation`, and `executor_history`; `executor_history` is append-only.
- A task becomes `completed` only after its `verification` passes locally (exit 0, or the stated manual check passes completely). Never weaken, skip, or replace a verification without the Lead's explicit task-contract update. Never accept an executor's self-report as verification.
- Any executor with `data_boundary: external_service` requires the recorded approval of Step 3 before any invocation, including runtime checks and quota lookups.
- Write user-facing prose in the user's language. Keep contract YAML keys, the executor prompt block, and report field labels exactly as written in this file.

## Pipeline — execute in this exact order

Work through the steps strictly in order. Each step ends with a GATE; do not start the next step until the gate is met. Never skip, reorder, or merge steps.

| # | Step | GATE — do not advance until |
|---|------|-----------------------------|
| 0 | Load runtime config | validator exits 0 |
| 1 | Select or create the goal contract | exactly one active contract identified |
| 2 | Fill the contract and assign executors | every task has ID, `target_files`, `verification`, delegable `executor`, `delegation` record |
| 3 | Approve external delegation *(conditional)* | approval recorded for every external executor and quota lookup, or the task left `pending` with the conflict reported |
| 4 | Resolve `selection` executors *(conditional)* | every selection task has a concrete executor and an `executor_history` entry |
| 5 | Delegate and verify | all assigned tasks `completed`, or a blocker reported to the Lead |
| 6 | Review in the Reviewer session | approved, or remediation tasks created |
| 7 | Rework loop *(conditional)* | Reviewer approves, or an escalation condition triggers |
| 8 | Report and next action | Completion report + Next Action Protocol returned |

Steps 3, 4, and 7 apply only when there is an external executor, a `selection` task, or a changes-requested review, respectively. Every other step is unconditional.

**Resume rule:** when the user returns to existing work, do not restart blindly. First identify which goal contract should be resumed. Use `list-active` when more than one contract may exist, or when the current goal is not explicit. Prefer its `recommended_contract`; if it is null, inspect `invalid_contracts` or completed contracts before deciding the next action. After choosing the goal contract, identify task statuses, the last completed or blocked step, and any pending verification, review, delegation, or routing decision. Enter the pipeline at the earliest step whose gate is not yet met, and open your reply with a compact resume summary: current position, what is done, what is blocked or pending, and the next concrete action. If the goal is already complete, go directly to Step 8.

### Step 0 — Load runtime config

1. Read `<skill-dir>/executors.yaml`.
1. Run the configuration check and require exit 0:

```bash
python3 <skill-dir>/scripts/validate_executors.py <skill-dir>/executors.yaml
```

3. If it fails, stop and report the exact error to the user. Do not create or assign tasks.

### Step 1 — Select or create the goal contract

Exactly one contract under project-root `.oyakatasama/` is active per goal.

Before using any contract helper CLI command, you MUST read `<skill-dir>/references/contract_cli.md` ([references/contract_cli.md](references/contract_cli.md)) and follow its use-case split between direct editing and deterministic CLI updates exactly.

- **New user-visible goal:** create `.oyakatasama/` if needed and copy `<skill-dir>/references/.todo.yaml` to `.oyakatasama/L-<next-number>_<short-goal>.yaml`. `<next-number>` is the greatest existing `L-NNN_*.yaml` number plus one, zero-padded to at least three digits (`001` when none exists). `<short-goal>` is two to five lowercase ASCII words joined by underscores, for example `auth_refactor` or `payment_api`. Never overwrite or reuse an existing contract. After the copy, validate the active contract path, not the template path.
- **Follow-up to an existing goal:** reuse only that goal's contract. Identify its exact path before delegating; never create a second contract for the same goal.
- Completed contracts stay in `.oyakatasama/` as immutable history, except for a later Lead-created remediation task for the same goal.

### Step 2 — Fill the contract and assign executors

1. Replace every template placeholder: `project.goal`, `project.constraints`, `project.success_criteria`, and bounded `backlog` tasks.
1. Give every task a stable ID, exact `target_files`, a local `verification` command or objective manual procedure, an `executor` set to a delegable `executors` or `selection` key, and a `delegation` record.
1. After the active `.oyakatasama/L-NNN_<short-goal>.yaml` file is created and filled, re-run `python3 <skill-dir>/scripts/validate_executors.py <skill-dir>/executors.yaml <active-contract-path>` so the concrete contract, not the template, is checked before delegation.
1. Classify the work:
   - Planning, architecture, investigation conclusions, risk decisions, and review stay in the Lead session — never as delegated tasks.
   - Code changes, tests, mechanical refactors, and implementation-focused debugging → a `selection` key **by default**. Assign a fixed executor ID only when the user or a `project.constraints` entry explicitly requires a specific provider; record that reason in `executor_history`.
   - Web research → `research.web_executor`; X research → `research.x_executor` from `executors.yaml`.
   - A mixed code+documentation task → split into separate tasks; both are reviewed in Step 6.
1. Honor each task's `executor` field; never infer the route from the task title or file type. Use a selector only when the Lead intentionally delegates the implementation choice to that selector's quota rule.

### Step 3 — Approve external delegation (conditional)

Before invoking any executor whose `data_boundary` is `external_service`, or running a quota selector's CodexBar lookup:

1. Inspect `project.constraints`. If any constraint prohibits external APIs, external servers, or data transmission: do not run the lookup or delegate; leave the task `pending` and report the conflict to the user.
1. Otherwise request explicit user approval stating: the executor ID and model, the exact task IDs, the exact `target_files`, and that the task contract and relevant file contents may be sent to the external service. A request to "delegate" is NOT approval of a specific provider and file scope.
1. After approval, set `delegation.approval` to `approved`, `approved_executor` to the selected executor, and `approved_target_files` to the exact task file list. The invoked executor and files MUST exactly match this record. A different fallback executor requires a new approval.

### Step 4 — Resolve selection executors (conditional)

Run only when a new goal contract, or a later Lead-created remediation task, contains a task assigned to a `selection` key. Use the user-installed official CodexBar CLI; never download, install, update, or configure CodexBar. Never re-run it for fixed-executor tasks or for later phases of the same contract.

Before resolving any `selection` task, you MUST read `<skill-dir>/references/quota_selection.md` ([references/quota_selection.md](references/quota_selection.md)) and follow it exactly for the lookup command, per-candidate scoring, choice order, tie-breaking, and fallback rules. Writing a concrete executor into a `selection` task without a successful CodexBar lookup — or, on lookup failure, without applying that file's fallback rule — is forbidden; never resolve a selection from memory. Then record the decision in the task:

```text
executor: <selected executor ID>
executor_history:
  - executor: <selected executor ID>
    reason: "Quota: <candidate>=<safe_remaining>; Reset: <candidate>=<next_reset>; <reason>"
    changed_by: lead
```

### Step 5 — Delegate and verify

For each task or task batch, in this order:

Before delegating to any executor, you MUST read `<skill-dir>/references/executor_contract_update_policy.md` ([references/executor_contract_update_policy.md](references/executor_contract_update_policy.md)) and apply its responsibility split and prompt constraints. The Lead, not the executor, is responsible for enforcing that policy.

1. Confirm the task's `executor` is delegable and, if external, exactly matches its approved `delegation` record. Refuse a non-delegable executor.
1. If `requires_unsandboxed_runtime` is true, request the already-approved least-privilege runtime escalation before invocation; do not first run it in a sandbox that cannot write its logs or bind required loopback sockets.
1. Invoke the configured `command` — expanding `{skill_dir}` in it to the absolute skill directory so the resolved command is independent of the caller's working directory — with expanded `args`, non-interactively so the Lead can capture and review the result. Run in an isolated branch or worktree for non-trivial changes when the active harness supports it. Do not grant bypass permissions by default. Preserve repository instructions and least-privilege permissions.
1. Build the executor prompt from the active contract's absolute path, the assigned task IDs, each task's `target_files`, and exactly this instruction block:

```text
Read <active-contract-path>. Assigned task IDs: <IDs>. Work only on those tasks and their target_files. When contract discovery or creation is needed, use `--repo <repo>` or `--goal-dir <repo>/.oyakatasama` explicitly; do not rely on the script caller's working directory. Use `python3 <skill-dir>/scripts/todo_cli.py set-status <active-contract-path> <task-id> in_progress` before editing. Run the task verification. Use `python3 <skill-dir>/scripts/todo_cli.py set-status <active-contract-path> <task-id> completed` only after verification succeeds. If you need to append one concise lesson, use `python3 <skill-dir>/scripts/todo_cli.py add-learning <active-contract-path> "<entry>"`. Do not update status or learnings by editing YAML directly. Leave failures in_progress and report the exact blocker. Do not review.
```

Add the executor-update restrictions from `references/executor_contract_update_policy.md` to the delegated prompt. Never assume an external executor will infer those restrictions from repository files alone.

5. Tell the executor to return only: files changed, verification results, and unresolved issues.
1. If the executor cannot start because of sandbox filesystem, log-path, socket, or permission errors: leave the task `pending`, append the exact error to `executor_history`, and stop. Do not automatically retry, switch providers, or send the project to another external executor.
1. Documentation tasks follow the same rules: give the documentation executor only task IDs assigned to its executor ID, and require it to inspect implemented behavior and relevant tests using only its configured command and model.

**Operating protocol** — the Lead and every executor, before changing even one line:

1. **Fix the context:** read the active contract, confirm `project.goal` and `project.constraints`, set the assigned task from `pending` to `in_progress`, and save it.
1. **Respect the edit boundary:** edit only that task's `target_files`, plus the contract fields each role may edit (Hard rules). Do not add unrequested code or files.
1. **Verify objectively:** run the task's `verification` locally after implementation. Do not start another task until it passes.
1. **Synchronize:** use `scripts/todo_cli.py` for deterministic contract updates. On success set the task `completed` with `set-status`; if a project-specific bug pattern or specification trap was found, append it as one concise line to `learnings` with `add-learning`. On failure keep the task `in_progress`, record no completion, and report the exact command and failure to the Lead.

### Step 6 — Review in the Reviewer session

Entry gate: every assigned backlog task is `completed`. If any task is `pending` or `in_progress`, resolve its route first; never pretend the phase is complete.

The configured Reviewer must inspect the actual diff and independently run appropriate verification. Reject when:

- acceptance criteria are missing;
- tests fail or relevant error cases lack coverage;
- unrelated files changed;
- secrets, credentials, or unsafe permissions appear;
- documentation disagrees with code or runtime behavior;
- the executor made an architecture or risk decision reserved for the Lead.

Record each finding in the Lead's handoff with a stable ID such as `R1-01`, severity, affected file, required correction, and verification command. On changes requested, add a new `pending` remediation task (for example `R1-01`) to the active contract with exact `target_files` and a real verification command; do not reopen a completed original task.

### Step 7 — Rework loop (conditional)

For `changes_requested`:

1. Refresh CodexBar usage instead of automatically reusing the previous executor. Keep the remediation task's explicit `executor`; apply the quota rule only when it names a `selection` key.
1. Obtain a new exact external-delegation approval (Step 3) for any external executor and remediation file scope.
1. Delegate only the `pending` remediation task IDs together with their review findings, following Step 5.
1. Return to the Reviewer for a new full review of the resulting diff, not only the latest patch. Repeat until the Reviewer approves or an escalation condition is met.
1. Only the Reviewer closes findings through the next review result. An executor never marks findings resolved, changes review status, or approves its own work.

### Step 8 — Report and next action

Produce the two Output contract blocks below. Before ending, confirm none of these is left implicit:

1. `pending` or `in_progress` tasks remaining in the active contract;
1. remediation, blockers, or failed verifications needing a concrete follow-up;
1. a completed goal that naturally leads to the next task, goal, or documentation update;
1. an external-delegation or quota-routing failure needing a precise retry path.

When the current goal is not explicit, or when several contracts may compete for attention, determine the goal first from `list-active` before writing the Next Action Protocol.
If the chosen contract is invalid and appears historical or pre-schema, you MUST read `<skill-dir>/references/legacy_contract_migration.md` ([references/legacy_contract_migration.md](references/legacy_contract_migration.md)) before recommending migration, repair, or replacement.

## Output contract

At every stopping point — goal complete, task blocked, approval needed, or session end — the reply MUST end with the Completion report followed by the Next Action Protocol, in that order. Never end with a bare status, and never end without a copy-paste prompt.

Write the report in the user's language. Put the decision-relevant information first: status, the immediate blocker or completed outcome, and the exact next user action. Keep routes, models, quota comparisons, and full verification commands in `Details`; do not make the user infer the blocker from those fields. Use short bullets, not dense semicolon-separated lines.

### Completion report

```text
Completion report
Status: <COMPLETED or BLOCKED>
Outcome or blocker:
- <what completed, or the one immediate reason work cannot continue>
Required action:
- <exact user action needed now, or none>
Progress:
- Contract: <path>
- Tasks: <completed count/total; pending or in-progress task IDs, if any>
Checks:
- <passed verification summary, or not run>
Review: <not started | round count and final decision>
Details:
- Lead/Reviewer: <executor IDs plus models>
- Routes: <implementation and documentation executor IDs plus models, or unresolved candidates>
- Routing evidence: <quota and reset comparison, or none>
- Unresolved: <remaining items, or none>
```

For a blocked run, `Outcome or blocker` MUST name the incomplete pipeline gate (for example, `Step 3: external delegation approval is not recorded`). `Required action` MUST state the exact approval or decision and its task/file scope. Do not describe unresolved routes as if they were selected.

Example — blocked before routing:

```text
Completion report
Status: BLOCKED
Outcome or blocker:
- Step 3: External delegation approval is not recorded, so T001-T003 cannot be sent.
Required action:
- Approve sending the contract and each task's target_files to grok or opencode for T001-T003.
- Approve the CodexBar quota lookup for grok and opencode; the result will select the executor.
Progress:
- Contract: .oyakatasama/L-010_ui_smoke_verification_for_existing.yaml
- Tasks: 0/3 completed; pending T001, T002, T003.
Checks:
- Executor configuration, contract validation, and active-contract lookup passed.
Review: not started.
Details:
- Lead/Reviewer: codex gpt-5.6-medium / codex gpt-5.6-medium
- Routes: unresolved between grok grok-4.5 and opencode zai-coding-plan/glm-5.2.
- Routing evidence: none; quota lookup has not run.
- Unresolved: Step 3 approval and Step 4 quota lookup.
```

### Next Action Protocol

```text
Next actions:
1. Options:
   - [recommended] <option drawn from the current state>
   - <at least one alternative when another valid path exists>
2. Recommendation reason: <one or two sentences>
3. Copy-paste prompt:
   <a prompt the user can paste as-is to continue>
```

Rules: make the recommended option explicit and list it first; draw options from the current state (continue the next pending task, start the next stage, revise the contract or backlog, re-run review or verification, stop and hand off); never auto-run the next step just because it is recommended.

## Escalation

Return implementation to the configured Lead when:

- security, authentication, payments, privacy, data loss, or production incidents are involved;
- the task requires a non-obvious architecture or product tradeoff;
- the selected executor fails the same acceptance check twice;
- two review rounds reject the same underlying issue;
- every quota-selector candidate is unavailable or unsafe;
- the generated diff is too broad to review reliably.

After one executor fails for a provider-specific reason, refresh CodexBar usage before trying the selector's next eligible candidate. Do not alternate indefinitely.
