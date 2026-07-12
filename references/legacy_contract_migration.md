# Legacy contract migration policy

Use this file when `validate` or `list-active` reports an invalid contract that appears to predate the current schema.

## Purpose

The goal is not to normalize every old contract automatically. The goal is to decide whether:

1. the contract can be migrated safely;
2. the contract needs manual review first; or
3. the contract should remain historical and untouched.

## Decision order

Evaluate in this order.

### 1. Is the contract active?

- If any task is `pending` or `in_progress`, treat it as an active migration case.
- If all tasks are `completed`, prefer preserving it as history unless the user explicitly wants it reusable under the current schema.

### 2. What kind of validation issue is present?

Use `list-active` or `validate` output to identify:

- `legacy_schema`
- `missing_delegation`
- `contract_metadata_mismatch`
- `manual_review_required`

### 3. Can the migration be mechanical?

Safe mechanical migration candidates usually include:

- adding missing `delegation` keys with empty approval state;
- filling missing `executor_history` structure when the intended executor is already unambiguous;
- fixing `project.id` to match the file prefix when the filename is clearly canonical.

Manual review is required when:

- a task executor is non-delegable under the current schema;
- the historical contract assigned Lead-only work directly into backlog tasks;
- executor intent is ambiguous;
- multiple fields conflict and the original workflow meaning may be lost.

## Migration categories

| Category | Typical examples | Default action |
|---|---|---|
| `missing_delegation` | missing `delegation`, incomplete approval fields | mechanical migration candidate |
| `contract_metadata_mismatch` | `project.id` does not match filename | mechanical migration candidate |
| `legacy_schema` | non-delegable task executor, old backlog semantics | manual review first |
| `manual_review_required` | unknown rule or multiple conflicting issues | manual review first |

## Codex behavior

When a legacy contract is detected, Codex should:

1. identify whether it is active or historical;
2. explain the detected validation category in user-facing language;
3. say whether migration looks mechanical or requires manual review;
4. avoid mutating the contract unless the next step is clearly authorized and low-risk.

## Next Action guidance

Use these recommendation patterns:

- `missing_delegation`
  - Recommend schema completion first.
- `contract_metadata_mismatch`
  - Recommend metadata alignment first.
- `legacy_schema`
  - Recommend manual review of executor semantics first.
- `manual_review_required`
  - Recommend inspection before mutation.

If the repository has no active contracts and only invalid historical ones, recommend either:

- migrating the specific invalid contract for reuse; or
- leaving history untouched and starting a new contract.

## Non-goals

This policy does not define an automatic migrator. It only defines the decision boundary for whether migration should happen and how Codex should explain the choice.
