# Quota selection algorithm (CodexBar)

Detailed procedure for SKILL.md Step 4. Run it once per fresh selection decision — that is, only when a new goal contract or a new Lead-created remediation task contains a task assigned to a `selection` key.

## 1. Lookup

For the selector, read every executor ID from `selection.<selector>.candidates` in `executors.yaml`, resolve each candidate's `quota_provider`, then run and parse one command per candidate:

```bash
codexbar usage --provider <candidate quota_provider> --format json --pretty --no-color
```

If `codexbar` is not on `PATH`, a command returns a non-zero exit status, or a response cannot be parsed: set the task's `executor` to `selection.<selector>.fallback_executor` and append the reason to `executor_history`. Do not invoke the fallback until its exact external-delegation approval has been recorded.

## 2. Score each candidate

Read each candidate's configured `quota_windows` only:

1. Reject an entry that is disabled, stale without usable quota data, or reports an error.
1. Read only `usage.<window>` for every window listed in that candidate's `quota_windows`. Ignore every unlisted usage window, even if it is exhausted.
1. `safe_remaining` = the minimum `remainingPercent` across the configured windows. If only `usedPercent` exists, use `100 - usedPercent`.
1. `next_reset` = the earliest future reset among the configured windows that determine `safe_remaining`.
1. Never infer unlimited capacity from a missing configured window or missing percentage.

## 3. Choose

Apply in order:

1. Discard candidates without valid quota data.
1. Find the highest `safe_remaining` among the remaining candidates.
1. Keep every remaining candidate within 5 percentage points of that highest value, then choose the earliest `next_reset` among them.
1. If candidates remain tied, choose `selection.<selector>.tie_breaker` when it is tied; otherwise choose the first tied candidate in `candidates` order.
1. If no candidate has valid data, set `executor` to `selection.<selector>.fallback_executor` and append the unavailable quota data to `executor_history`. Do not invoke it until its exact external-delegation approval has been recorded.

Do not use reset proximity to justify sending work to a provider with materially less remaining quota.

## 4. Record

Write the result back to the task as shown in SKILL.md Step 4: set `executor` to the selected ID and append an `executor_history` entry whose `reason` cites each candidate's `safe_remaining` and `next_reset`.
