---
name: oyakata
description: Orchestrate software work by keeping Codex with GPT-5.6 medium as Lead and Reviewer, routing implementation to Grok or OpenCode according to live CodexBar quota and reset data, routing web search and documentation to Antigravity, and routing X search to Grok. Use for non-trivial implementation, review, refactoring, testing, research, or documentation tasks that benefit from role separation and quota-aware provider selection.
---

# Oyakata

Separate judgment, implementation, and documentation. Keep Codex in control of scope and quality; delegate bounded production work to the configured command whose provider currently has the safer quota.

## Fixed role map

- Lead: run in the current Codex session with `gpt-5.6-medium`.
- Reviewer: run in the current Codex session with `gpt-5.6-medium`.
- Grok executor: run `grok` with `grok-4.5`.
- Z.ai executor: run `opencode` with `zai-coding-plan/glm-5.2`.
- Documentation executor: run `agy` with `Gemini 3.5 Flash (Medium)`.
- Web search: use `agy`.
- X search: use `grok`.
- Do not route architecture, security decisions, acceptance decisions, or final sign-off away from Codex.

Treat the model strings above as the intended logical models. Before the first delegation, use the CLI's model-list or help command if the installed CLI requires a different exact model identifier. Do not silently substitute a different model family.

## Workflow

### 1. Create the shared task ledger

Before delegation, create or replace a project-root `TODO.md` for the current Oyakata run. Preserve an unrelated existing `TODO.md`; if one exists, use `.oyakata/TODO.md` instead and tell every participant the chosen path.

Use this structure:

```markdown
# Oyakata Task Ledger

## Contract

- Goal: <user-visible outcome>
- Non-goals: <scope boundaries>
- Likely files: <paths>
- Verification: <commands and manual checks>
- Escalation: <conditions reserved for Lead>

## Plan

- [ ] T01 <bounded implementation task>
  - Owner: executor
  - Acceptance: <observable result>
  - Verify: `<command>`
- [ ] T02 <bounded documentation task>
  - Owner: documentation
  - Acceptance: <observable result>
  - Verify: <inspection or command>

## Executor notes

- <task ID>: <files changed, verification result, unresolved issue>

## Codex review

- Status: pending
- Round: 0
- Findings: none

## Final status

- Status: in_progress
- Approved by: pending
```

Codex owns the Contract, Plan, Codex review, and Final status sections. Executors may check only tasks they completed and append concise Executor notes. Keep task IDs stable across review rounds. Never treat a checked box as proof; it only means the executor claims completion.

### 2. Classify the work

- Keep planning, architecture, investigation conclusions, risk decisions, and review in Codex.
- Route code changes, tests, mechanical refactors, and implementation-focused debugging through the implementation selector.
- Route prose documentation, README updates, migration guides, release notes, and user-facing explanations to `agy`.
- Route web research to `agy`; route X research to `grok`.
- For a mixed task, split code and documentation into separate tasks. Review both in Codex.
- Handle a trivial one-file edit directly only when delegation overhead is larger than the work.

### 3. Select an implementation executor

Immediately before each implementation delegation, run:

```bash
~/Workspace/CodexBar/Scripts/codexbar-fast.sh usage --pretty
```

Read the `grok` and `zai` provider entries. For each provider:

1. Reject an entry that is disabled, stale without usable quota data, or reports an error.
2. Inspect every applicable rate-limit window, including primary, secondary, tertiary, and extra windows.
3. Calculate `safe_remaining` as the minimum available `remainingPercent`. If only `usedPercent` exists, use `100 - usedPercent`.
4. Calculate `next_reset` as the earliest future reset among the windows that determine `safe_remaining`.
5. Never infer unlimited capacity from a missing window or missing percentage.

Choose with this order:

1. Prefer the provider with the larger `safe_remaining`.
2. If the difference is at most 5 percentage points, prefer the provider with the earlier `next_reset`.
3. If still tied, prefer `grok` to avoid arbitrary route flapping.
4. If one provider has valid data and the other does not, use the valid provider.
5. If neither provider has valid data, do not guess. Report the quota lookup failure and ask the Lead to choose or execute the task.

Do not use reset proximity to justify sending work to a provider with materially less remaining quota. Re-run the command before every new executor task; do not reuse an old result across phases.

Record the decision briefly:

```text
Route: grok | zai
Quota: grok=<safe_remaining>, zai=<safe_remaining>
Reset: grok=<next_reset>, zai=<next_reset>
Reason: <one sentence>
```

### 4. Delegate implementation

Use non-interactive commands so the Lead can capture and review the result. Preserve repository instructions and least-privilege permissions.

Include the ledger path in every executor prompt. Tell the executor to:

1. Read the Contract and its assigned unchecked task IDs before editing.
2. Work only on those task IDs.
3. Run each task's verification command.
4. Check a task only after its acceptance criteria pass.
5. Leave a failed task unchecked and record the exact blocker in Executor notes.
6. Stop after all assigned tasks are checked or explicitly blocked; do not perform Codex review.

Grok route:

```bash
grok --single "Read <ledger path>. Complete the assigned unchecked task IDs, verify them, update their checkboxes and Executor notes, then stop." \
  --model grok-4.5 \
  --cwd "$REPO" \
  --permission-mode acceptEdits \
  --check
```

Z.ai route:

```bash
opencode run \
  --model zai-coding-plan/glm-5.2 \
  --agent build \
  --dir "$REPO" \
  "Read <ledger path>. Complete the assigned unchecked task IDs, verify them, update their checkboxes and Executor notes, then stop."
```

Run the executor in an isolated branch or worktree for non-trivial changes when the active harness supports it. Do not grant bypass permissions by default. Tell the executor to return only files changed, verification results, and unresolved issues.

### 5. Delegate documentation

Use Antigravity independently of the implementation quota comparison:

```bash
agy --print \
  --model "Gemini 3.5 Flash (Medium)" \
  --mode accept-edits \
  "<documentation acceptance contract and source-of-truth paths>"
```

Require the documentation executor to inspect the implemented behavior and relevant tests. Do not let it invent commands, configuration, or runtime behavior. If the exact installed model identifier differs, resolve it with `agy models` first.

Give `agy` only documentation-owned task IDs from the ledger. Require it to update the corresponding checkboxes and Executor notes under the same rules as an implementation executor.

### 6. Review in Codex

Do not start Codex review until every Plan task is checked or carries an explicit blocker. If a task is blocked, resolve its route before review rather than pretending the phase is complete.

The Codex Reviewer must return to the current Codex session, inspect the actual diff, and independently run appropriate verification. Reject work when:

- acceptance criteria are missing;
- tests fail or relevant error cases lack coverage;
- unrelated files changed;
- secrets, credentials, or unsafe permissions appear;
- documentation disagrees with code or runtime behavior;
- the executor made an architecture or risk decision reserved for the Lead.

Never accept an executor's self-report as verification.

Update the ledger after every review:

- Increment `Round`.
- Set review `Status` to `approved`, `changes_requested`, or `blocked`.
- Record each finding with a stable ID such as `R1-01`, its severity, affected file, required correction, and verification command.
- On approval, set Final status to `approved` and name Codex as approver.
- On changes requested, add new unchecked remediation tasks such as `R1-01` to Plan. Do not reopen completed original tasks.

### 7. Rework loop

For `changes_requested`:

1. Refresh CodexBar usage instead of automatically reusing the previous executor.
2. Select `grok` or `zai` with the normal quota rule.
3. Delegate only the unchecked remediation task IDs and their review findings.
4. Require the executor to correct, verify, check the remediation tasks, and append Executor notes.
5. Return to Codex and perform a new full review of the resulting diff, not only the latest patch.
6. Repeat until Codex approves or an escalation condition is met.

Do not let an executor mark review findings resolved, change review status, or approve its own work. Codex alone closes findings through the next review result.

## Escalation

Return implementation to Codex when:

- security, authentication, payments, privacy, data loss, or production incidents are involved;
- the task requires a non-obvious architecture or product tradeoff;
- the selected executor fails the same acceptance check twice;
- two review rounds reject the same underlying issue;
- both implementation quotas are unavailable or unsafe;
- the generated diff is too broad to review reliably.

After one executor fails for a provider-specific reason, refresh CodexBar usage before trying the alternate executor. Do not alternate indefinitely.

## Completion report

End with:

```text
Result: <completed or blocked>
Lead/Reviewer: Codex + gpt-5.6-medium
Task ledger: <TODO.md path and final status>
Implementation route: <grok + grok-4.5 | opencode + zai-coding-plan/glm-5.2 | Codex>
Documentation route: <agy + Gemini 3.5 Flash (Medium) | none>
Routing evidence: <remaining quota and reset comparison>
Review rounds: <count and final decision>
Verification: <commands and results>
Unresolved: <none or concise list>
```
