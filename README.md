<h1 align="center">Oyakatasama</h1>

<p align="center">
  <img src="assets/oyakatasama-crest.jpg" width="260" alt="Oyakatasama heraldic crest with a samurai helmet and banners" />
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README_JP.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Lead-Codex-412991?style=flat-square" alt="Configurable Lead" />
  <img src="https://img.shields.io/badge/Routing-CodexBar-1f6feb?style=flat-square" alt="CodexBar routing" />
  <img src="https://img.shields.io/badge/Contracts-YAML-cb171e?style=flat-square" alt="YAML contracts" />
</p>

Oyakatasama is a configurable workflow for non-trivial software work. Its name evokes **Oyakatasama** (specifically inspired by the Sengoku-period warlord Sanada Masayuki)—a feudal lord in Japan's warrior society—not a modern construction foreman. The Lead plans and reviews; every goal has an independent local task contract; individual tasks retain their assigned executor; CodexBar quota data can select an implementation executor.

## ⚙️ Executor definitions

[`executors.yaml`](./executors.yaml) is the only place that defines the Lead, Reviewer, executors, commands, arguments, models, quota-provider mappings, research routing, and quota-selection candidates. Edit it to choose the command and model combinations used by this skill.

The default definitions use Codex as Lead and Reviewer, with Grok, OpenCode, and Antigravity as executors. The Lead and Reviewer are not delegable and never edit task `target_files`. Keep architecture, security, acceptance, and final approval in the configured Lead session. Do not store API keys, cookies, tokens, passwords, or `.env` values in `executors.yaml`.

## 🚀 Use

Start Codex in the target Git repository and request Oyakatasama explicitly:

```text
$oyakatasama

Implement user registration with duplicate-email protection and tests.
Update the README to match the implemented behavior.
```

## 🔧 CodexBar CLI setup

Install the official CodexBar CLI yourself before using a `selection` task. Oyakatasama never downloads, installs, updates, or configures it, and it only reads quota when a new goal contract or remediation task introduces a selector-backed decision.

1. Download the matching Linux or macOS CLI archive from the [CodexBar releases](https://github.com/steipete/CodexBar/releases).
2. Extract `CodexBarCLI` and its `codexbar` symlink into a user-managed directory such as `$HOME/.local/bin`, then add that directory to `PATH`.
3. Confirm that the intended binary is selected and that the required providers are configured.

```bash
command -v codexbar
codexbar --version
codexbar usage --provider <quota_provider> --format json --pretty --no-color
python3 <skill-dir>/scripts/validate_executors.py <skill-dir>/executors.yaml
```

After the goal contract exists, rerun the validator with `.oyakatasama/L-001_auth_refactor.yaml` or the current `L-NNN_*.yaml` file as the second argument.

The official CLI supports `--provider` and JSON output. Keep its provider credentials and configuration under your own control.

## 🗂️ Minimal goal contract

```yaml
# .oyakatasama/L-001_auth_refactor.yaml
backlog:
  - id: T001
    title: Update authentication documentation
    status: pending
    executor: agy
    executor_history:
      - executor: agy
        reason: Documentation task
        changed_by: lead
    delegation:
      approval: not_requested
      approved_executor: null
      approved_target_files: []
    target_files: [README.md]
    verification: git diff --check
```

Use an executor or selector key defined in `executors.yaml`.

## 🔁 Execution loop

1. The Lead creates one contract per goal: `.oyakatasama/L-NNN_short_goal.yaml`.
2. The contract records the goal, constraints, bounded tasks, exact editable files, verification, task status, and `executor`.
3. Each executor changes only its assigned task from `pending` to `in_progress`, edits only `target_files`, verifies locally, then marks it `completed`.
4. `executor` must name an `executors.yaml` executor or selector key.
5. The Lead never implements a task. Every task must use an executor with `delegable: true`.
6. Before an external executor or CodexBar selector runs, the Lead confirms that project constraints permit external transmission and obtains approval for the exact executor and `target_files`.
7. For an approved selector, the Lead runs the official `codexbar` CLI with the relevant `quota_provider` values from `executors.yaml` and compares their JSON results.
8. If a fallback executor is selected, the Lead obtains new approval for that executor before invoking it.
9. After all assigned tasks are done, the configured Reviewer independently reviews the diff and runs verification. Review remediation becomes a new task in the same goal contract.
10. The configured Reviewer alone approves the result.

Executors cannot approve their own work or close review findings.

## 🧭 Stop points and next action

Oyakatasama should not end a run with only a status line. At every stopping point, return:

1. the current position
2. a concise completion or blocker summary
3. the next action as options, a recommendation, and a copy-paste prompt

Use this after:

- task completion
- review completion
- verification failure
- quota-routing failure
- external delegation approval conflicts

Before ending a run, the skill also checks whether any pending or in-progress task remains, whether a remediation or retry is needed, and whether a natural next goal should be proposed.

If there are still pending tasks or the goal naturally continues, propose the next task or stage instead of stopping silently.

When the user comes back later to resume the same goal, Oyakatasama first reads the active contract and reports the current position, what is already done, what is still pending or blocked, and the next concrete action.

## 📊 Routing rule

For any approved selector, use only each candidate's configured `quota_windows`. Prefer the larger `safe_remaining`. When the difference is within five percentage points, prefer the earlier reset. If the result is still tied, use the selector's `tie_breaker`. Read quota only when creating a new selector-backed goal contract or remediation task; do not refresh it for later tasks in the same contract. If the CLI or quota result is unusable, select its `fallback_executor`, then obtain approval before invoking it. Sandbox log, socket, or permission failures leave the task pending; they do not trigger an automatic provider change.

## 📁 Files

- `SKILL.md` — the complete workflow and command templates
- `executors.yaml` — user-editable executor commands and models
- `README.md` — this overview
- `README_JP.md` — Japanese overview
- `assets/oyakatasama-crest.jpg` — Oyakatasama-inspired heraldic logo
- `references/.todo.yaml` — template copied to each goal contract
- `references/contract_cli.md` — when to use the contract CLI versus direct editing
- `references/executor_contract_update_policy.md` — Lead-enforced executor limits for contract updates
- `references/legacy_contract_migration.md` — how to decide whether an invalid old contract should be migrated
- `scripts/todo_cli.py` — compact contract summary and task-status updater
- `scripts/validate_executors.py` — executor and goal-contract validator

## 🧰 Contract CLI

Use the local helper when you want small, deterministic contract updates instead of opening the whole YAML in an LLM context. Keep the detailed operating rules in `references/contract_cli.md`; this README only summarizes the available commands.

```bash
python3 scripts/todo_cli.py create "Implement duplicate-email-safe registration"
python3 scripts/todo_cli.py list-active
python3 scripts/todo_cli.py list-active --format text
python3 scripts/todo_cli.py summary .oyakatasama/L-001_auth_refactor.yaml
python3 scripts/todo_cli.py set-status .oyakatasama/L-001_auth_refactor.yaml T001 in_progress
python3 scripts/todo_cli.py assign .oyakatasama/L-001_auth_refactor.yaml T001 grok "Quota winner"
python3 scripts/todo_cli.py approve .oyakatasama/L-001_auth_refactor.yaml T001 grok README.md
python3 scripts/todo_cli.py add-learning .oyakatasama/L-001_auth_refactor.yaml "Fallback executor required fresh approval"
python3 scripts/todo_cli.py validate executors.yaml .oyakatasama/L-001_auth_refactor.yaml
```

Current scope:

- `create` copies `references/.todo.yaml` into the next `.oyakatasama/L-*.yaml` contract and fills `project.id` plus `project.goal`.
- `list-active` returns active, invalid, and completed contract state plus `recommended_contract`.
- `list-active --format text` prints a compact resume-oriented summary for humans.
- invalid entries include validation category, rule, and auto-migration hint for Next Action decisions.
- `summary` prints compact JSON for the project, task counts, and task metadata.
- `set-status` updates one task status and writes the contract back.
- `assign` updates one task executor and appends `executor_history`.
- `approve` records exact delegation approval for one task.
- `add-learning` appends one concise entry to `learnings`.
- `validate` reuses `scripts/validate_executors.py`.

The active goal contract is treated as machine-managed YAML. The template under `references/.todo.yaml` keeps the rich inline guidance; copied contracts may be normalized when the CLI writes them back.

Guardrail:

- write commands reject `references/.todo.yaml`; update only active contracts under `.oyakatasama/`.

## 🧭 Contract policy references

Use the reference files, not this README, as the detailed operating policy:

- `references/contract_cli.md` — use-case split between direct editing and deterministic CLI updates
- `references/executor_contract_update_policy.md` — responsibility split between the Lead and delegated executors
- `references/legacy_contract_migration.md` — decision rules for invalid or historical contracts

External executors such as `agy`, `grok`, and `opencode` should not be expected to infer the full contract-management policy from repository files alone. Codex, acting as the Lead, is responsible for:

- choosing the route;
- recording `assign` and `approve` changes;
- constraining the delegated prompt;
- validating the returned contract state.

When the current goal is not explicit, use `list-active` before writing the next recommendation. This keeps Next Action tied to one chosen contract instead of an ambiguous repository-wide status.

## 📄 License

MIT
