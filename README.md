# Oyakata

Oyakata is a Codex-centered workflow for non-trivial software work. Codex plans and reviews; the implementation executor is chosen from live CodexBar quota data; Antigravity handles web research and bounded documentation tasks; Grok handles X research.

## Role map

- **Lead / Reviewer:** Codex with `gpt-5.6-medium`
- **Implementation:** `grok` with `grok-4.5`, or `opencode` with `zai-coding-plan/glm-5.2`
- **Documentation:** `agy` with `Gemini 3.5 Flash (Medium)`
- **Web research:** `agy`
- **X research:** `grok`

Codex retains architecture, security, acceptance, and final-approval decisions.

## Use

Start Codex in the target Git repository and request Oyakata explicitly:

```text
$oyakata

Implement user registration with duplicate-email protection and tests.
Update the README to match the implemented behavior.
```

## Execution loop

1. Codex creates a shared task ledger in `TODO.md`. If an unrelated `TODO.md` already exists, it uses `.oyakata/TODO.md`.
2. Codex records the goal, non-goals, bounded tasks, acceptance checks, and escalation conditions.
3. For every implementation delegation, Codex runs `~/Workspace/CodexBar/Scripts/codexbar-fast.sh usage --pretty`.
4. Codex compares the safe remaining quota and reset time for the `grok` and `zai` providers, then routes the task to `grok` or `opencode`.
5. The executor completes only its assigned task IDs, runs their checks, and updates its task checkboxes and execution notes.
6. After all assigned tasks are done, Codex independently reviews the diff and runs verification.
7. If review finds issues, Codex writes remediation task IDs into the same ledger, refreshes quota data, and delegates the fixes again.
8. Codex alone approves the result and closes the task ledger.

Executors cannot approve their own work or close review findings.

## Routing rule

For each provider, use the smallest remaining percentage among all applicable quota windows. Prefer the larger value. When the difference is within five percentage points, prefer the earlier reset. If the result is still tied, prefer Grok. If neither quota result is usable, Codex keeps the work instead of guessing.

## Files

- `SKILL.md` — the complete workflow and command templates
- `README.md` — this overview

## License

MIT
