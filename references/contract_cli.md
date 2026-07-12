# Contract CLI policy

Use the contract file as the single source of truth, but do not open and rewrite the whole YAML for every small update.

## Scope

This policy applies to active goal contracts under `.oyakatasama/L-*.yaml`.

- `references/.todo.yaml` is a template only.
- Active contracts are machine-managed YAML.
- Deterministic field updates should use `scripts/todo_cli.py`.
- Structural contract changes still require direct editing by the Lead.

## Use cases

| Use case | Primary actor | Update target | Preferred operation |
|---|---|---|---|
| Create a new goal contract | Lead | new contract file | `create` |
| Resume an existing goal | Lead | goal selection + read-only summary | `list-active`, then `summary` |
| Replace template placeholders | Lead | `project.*`, backlog structure | direct edit |
| Start a delegated task | Lead or executor | task `status` | `set-status ... in_progress` |
| Complete a delegated task | Lead or executor | task `status` | `set-status ... completed` |
| Record executor selection | Lead | `executor`, `executor_history` | `assign` |
| Record exact external approval | Lead | `delegation.*` | `approve` |
| Record one concise lesson | Lead or executor | `learnings` | `add-learning` |
| Check contract validity | Lead | full contract | `validate` |
| Inspect a legacy contract | Lead | read-only summary and schema fit | `summary`, `validate` |

## Command rules

Use the CLI for deterministic updates:

```bash
python3 <skill-dir>/scripts/todo_cli.py create "Implement duplicate-email-safe registration"
python3 <skill-dir>/scripts/todo_cli.py list-active
python3 <skill-dir>/scripts/todo_cli.py summary .oyakatasama/L-001_auth_refactor.yaml
python3 <skill-dir>/scripts/todo_cli.py set-status .oyakatasama/L-001_auth_refactor.yaml T001 in_progress
python3 <skill-dir>/scripts/todo_cli.py assign .oyakatasama/L-001_auth_refactor.yaml T001 grok "Quota winner"
python3 <skill-dir>/scripts/todo_cli.py approve .oyakatasama/L-001_auth_refactor.yaml T001 grok README.md
python3 <skill-dir>/scripts/todo_cli.py add-learning .oyakatasama/L-001_auth_refactor.yaml "Fallback executor required fresh approval"
python3 <skill-dir>/scripts/todo_cli.py validate <skill-dir>/executors.yaml .oyakatasama/L-001_auth_refactor.yaml
```

Do not use the CLI as a replacement for contract design. Use direct editing for:

- replacing template placeholders;
- adding, removing, or splitting backlog tasks;
- changing `project.constraints`;
- changing `project.success_criteria`;
- migrating a legacy contract to the current schema.

## Recommended flow

### New goal

1. Run `create`.
2. Fill placeholders and backlog structure by direct editing.
3. Run `validate`.

### Resume existing goal

1. Run `list-active`.
2. Choose the goal from `recommended_contract` when available; otherwise inspect `invalid_contracts` or completed contracts explicitly.
3. Run `summary` for the chosen contract.
4. Identify pending or `in_progress` tasks.
5. Re-enter the pipeline at the earliest incomplete gate.

### Goal selection before Next Action

Before returning a Next Action Protocol, determine which goal the recommendation is about.

- If `recommended_contract` exists, use it as the default resume target.
- If `active_contracts` is empty and `invalid_contracts` is non-empty, use each invalid entry's `category`, `rule`, and `auto_migration_candidate` fields to decide whether to recommend migration first or ask for manual review.
- If all contracts are completed, recommend the next goal rather than pretending there is active work.
- If the user already named a specific contract or task, that explicit instruction overrides `recommended_contract`.

When the invalid contract appears to be historical or pre-schema, read `references/legacy_contract_migration.md` before recommending mutation, migration, or replacement.

### Before executor work

1. Set the assigned task to `in_progress`.
2. If the Lead changed the route, record it with `assign`.
3. If external execution is approved, record it with `approve`.
4. Run `validate` before delegation when contract routing changed.

### After executor work

1. Run local verification.
2. Set the assigned task to `completed` only after verification passes.
3. Append one concise project-specific lesson with `add-learning` when useful.

## Guardrails

- Never write to `references/.todo.yaml`.
- Do not use write commands against a template or a legacy contract that has not been reviewed for schema fit.
- If `validate` fails on an older contract, treat it as a migration case rather than forcing field updates blindly.
