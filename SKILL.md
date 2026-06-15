---
name: beastmode
description: >
  Multi-agent orchestration framework for high-intensity feature implementation.
  Combines expensive high-judgment models (Opus/Codex) for planning and review
  with cheap models (Qwen/Gwen) for routine execution in isolated worktrees,
  with a self-improving learning loop that promotes lessons back into skills.
  Harness-agnostic: works with Ultraswarm, GSD, delegate_task, or manual orchestration.
version: 2.0.0
author: Luis Calderon
tags: [beastmode, orchestration, multi-agent, cost-optimization, self-improving, worktrees]
related_skills: [ultraswarm, gsd, subagent-driven-development, self-improvement]
agents: [hermes, codex, openclaw, claude-code]
---

# Beastmode: Multi-Agent Orchestration Framework

Beastmode is a structured approach to multi-agent software development that separates high-judgment work (planning, architecture, review) from routine execution (implementation, tests, docs) across different model tiers, with strict cost discipline and a self-improving learning loop.

**Harness-agnostic:** Works with Ultraswarm, GSD, `delegate_task`, Claude Code subagents, or manual orchestration. No specific tool required.

## Core Principle

**Expensive models decide. Cheap models build. The loop learns.**

- **Director/Lead:** High-judgment model (Opus, Claude Code, or Codex) owns intent, architecture, creative judgment, and final sign-off.
- **Watcher/Reviewer:** Adversarial reviewer (Codex/GSD) challenges plans, gates merges, catches scope creep.
- **Executor:** Cheap model (Qwen 3.7 Plus / Gwen) handles routine implementation in isolated worktrees.
- **Harness:** Any orchestration tool (Ultraswarm, GSD, `delegate_task`, Claude Code subagents, or manual git workflow).
- **Memory:** Self-improvement loop records lessons and promotes repeated patterns into skills/config.

## When to Use Beastmode

Use beastmode for complex tasks that need:
- Multi-phase workflows with planning and review gates
- Multiple workstreams or files
- High-stakes architecture/product/creative judgment
- Cost-efficient execution under an expensive lead model
- Strong QA and merge gates
- A reusable learning loop

**Do not use beastmode for:**
- Trivial one-file edits (use the cheap executor directly)
- Simple questions or information retrieval
- Tasks that don't benefit from role separation

## Two Beastmode Variants

### Variant A: Opus-Led Beastmode

**Use when:** You have Claude Code / Opus available as the lead and need maximum judgment for product/creative/architecture decisions.

**Role split:**
- **Director (Opus/Claude Code):** Intent, architecture, creative judgment, final sign-off
- **Watcher (Codex/GSD):** Adversarial planning, scope/cost review, merge gating
- **Executor (Qwen/Gwen):** Implementation, tests, docs, scripts, mechanical refactors

**Key rule:** Opus must aggressively avoid spending tokens on routine implementation. Delegate file edits, test writing, docs, refactors, and command execution to Qwen.

### Variant B: Codex-Led Beastmode

**Use when:** You don't have Opus, or the task doesn't require Opus-level judgment. Codex/GSD leads, with Qwen executing routine work.

**Role split:**
- **Director/Reviewer (Codex/GSD or current session):** Planning, review, merge decisions
- **Executor (Qwen/Gwen):** Implementation, tests, docs, scripts
- **Escalation:** Codex handles security, auth, payments, data-loss, production incidents, or failed Qwen attempts

**Key rule:** Delegate routine work to Qwen, but don't merge until the lead verifies acceptance.

## Hard Rules

1. **Main tree stays clean.** Executors work in isolated worktrees/branches. Never let cheap executors directly mutate the main working tree unless the task is tiny and explicitly approved by the lead.
2. **Lead reviews, executor implements.** The lead can plan, inspect, test, and merge. Routine work goes to the executor.
3. **Every phase has an acceptance contract.** Define goal, non-goals, verification commands, and escalation triggers before delegation.
4. **Every phase improves the loop.** Record learnings, errors, routing mistakes, and token/cost surprises. Promote repeated lessons into skills/config.
5. **Escalation doesn't skip self-improvement.** Record why the cheap route failed and whether routing rules should change.

## Choosing Your Harness

Beastmode works with any orchestration harness. Choose based on your environment:

### Harness 1: Ultraswarm (Preferred for Git Repos)

**Use when:** You have Ultraswarm installed and want worktree isolation, adaptive QA, merge gates, and cost reporting.

**Commands:**
```bash
ultraswarm run "<task + acceptance contract>" --repo . --provider auto --mode direct
ultraswarm qa <task-id>
ultraswarm merge <task-id> --repo . --approved
ultraswarm report
```

**For multi-phase work:**
```bash
ultraswarm plan "<goal>" --repo . --mode gsd
ultraswarm run "<goal or phase>" --repo . --provider auto --mode gsd
```

### Harness 2: GSD (Get Shit Done)

**Use when:** The repo already uses GSD for planning/phase management.

**Commands:**
```bash
gsd-plan-phase "<phase goal>"
gsd-execute-phase "<phase>"
gsd-verify-work
gsd-ship
```

Let GSD handle planning/phase gates, and delegate routine implementation units to Qwen via Ultraswarm or `delegate_task`.

### Harness 3: delegate_task (Hermes/OpenClaw)

**Use when:** You're in Hermes or OpenClaw and need subagent orchestration without worktrees.

**Example:**
```python
delegate_task(
    goal="<tight task with acceptance contract>",
    context="Repo, acceptance contract, files, verification commands, commit requirement",
    toolsets=['terminal', 'file']
)
```

**Note:** `delegate_task` doesn't provide worktree isolation. Use for small parallel tasks or when worktrees aren't needed.

### Harness 4: Claude Code Subagents

**Use when:** You're in Claude Code and want to spawn subagents for routine work.

**Example:**
```bash
# In Claude Code, use the Task tool or subagent spawning
Task("<tight task with acceptance contract>")
```

**Note:** Claude Code subagents don't provide worktree isolation by default. Use git branches manually if needed.

### Harness 5: Manual Git Workflow

**Use when:** No orchestration tool is available, but you still want isolation.

**Workflow:**
```bash
# Create isolated branch
git checkout -b beastmode/<task-id>

# Executor works in the branch (manually or via cheap model)
# ...

# Lead reviews
git diff main...beastmode/<task-id>

# Merge after approval
git checkout main
git merge beastmode/<task-id>
```

**Note:** Manual workflow requires discipline. Don't skip the review step.

### Harness Selection Guide

| Harness | Worktree Isolation | QA Gates | Cost Reporting | Best For |
|---------|-------------------|----------|----------------|----------|
| Ultraswarm | ✅ Yes | ✅ Adaptive | ✅ Yes | Git repos, multi-phase work |
| GSD | ❌ No (uses branches) | ✅ Phase gates | ❌ No | Repos already using GSD |
| delegate_task | ❌ No | ❌ No | ❌ No | Small parallel tasks, no repo |
| Claude Code subagents | ❌ No | ❌ No | ❌ No | Claude Code environments |
| Manual git | ✅ Yes (branches) | ❌ Manual | ❌ No | No orchestration tool available |

**Default recommendation:** Use Ultraswarm if available. Fall back to GSD if the repo uses it. Use `delegate_task` or Claude Code subagents for small tasks. Use manual git workflow as last resort.

## The Beastmode Loop

### Step 0: Preflight

```bash
cd "$REPO"
git status --short
# If using Ultraswarm:
ultraswarm doctor
ultraswarm report || true
```

If your harness is unavailable, fall back to a simpler harness (e.g., `delegate_task` or manual git), then record the failure in the self-improvement log.

### Step 1: Define Acceptance Contract

Before any delegation, write:

```markdown
Goal: <user-visible outcome>
Non-goals: <scope boundaries>
User-visible acceptance: <what the user will see/test>
Files/areas likely touched: <paths>
Verification commands: <unit/integration/e2e commands>
Manual QA: <visual/security checks>
Escalation triggers: <auth/security/payments/data-loss/architecture-uncertainty>
Self-improvement log path: <.learnings/BEASTMODE.md or project-local path>
```

### Step 2: Plan (With Challenge for Opus-Led)

**For Opus-led:**
- Opus drafts intent and constraints
- Codex/GSD turns it into phases and tries to find gaps
- Opus resolves tradeoffs and approves the phase map

**For Codex-led:**
- Lead writes the plan directly, or uses harness planning commands

**Planning commands by harness:**
- Ultraswarm: `ultraswarm plan "<goal>" --repo . --mode gsd`
- GSD: `gsd-plan-phase "<phase goal>"`
- Manual: Write plan in markdown, commit to `.planning/` or similar

### Step 3: Delegate Routine Work

Use tight task specs. One task should be reviewable in a single diff.

**Delegation by harness:**
- **Ultraswarm:** `ultraswarm run "<task>" --repo . --provider auto --mode auto`
- **delegate_task:** `delegate_task(goal="<task>", context="...", toolsets=['terminal', 'file'])`
- **Claude Code:** `Task("<task>")`
- **Manual:** Executor works in branch, commits changes

### Step 4: Adversarial Review

The lead or Codex reviews the branch diff against the contract.

**Review commands:**
```bash
# If using Ultraswarm:
ultraswarm qa <task-id>

# Manual review:
git diff --stat main...<branch>
git diff main...<branch>
```

**Reject if:**
- Tests fail
- Diff includes unrelated files
- Scope expanded beyond the acceptance contract
- Code uses nondeterminism or network calls where not allowed
- Secrets/credentials were exposed
- The executor made decisions reserved for the lead

### Step 5: Merge Gate

**Merge commands by harness:**
- **Ultraswarm:** `ultraswarm merge <task-id> --repo . --approved`
- **GSD:** `gsd-ship` (after verification)
- **Manual:** `git checkout main && git merge <branch>`

Never merge on executor self-report alone. The lead or Codex watcher must verify.

### Step 6: Self-Improving Checkpoint

After every phase, append a learning entry before continuing.

**Preferred locations (in order):**
1. Project-local `.learnings/BEASTMODE.md`
2. `.planning/LEARNINGS.md`
3. Relevant skill patch if the lesson is immediately reusable

**Template:**

```markdown
## BM-YYYYMMDD-HHMM <phase/task-id>
- Director/Lead: <model/agent>
- Watcher/Reviewer: <model/agent>
- Executor: <model/agent>
- Harness: <ultraswarm/gsd/delegate_task/claude-code/manual>
- Acceptance checks: <commands run>
- Result: pass | fail | partial
- Token/cost note: <estimate or harness report>
- What worked: <specific observations>
- What failed / drifted: <specific observations>
- Routing rule to change: <if applicable>
- Skill/config update needed: yes | no
- Promoted to: <skill/config/file or none>
```

**Promotion rules:**

The self-improvement loop writes **notes only** during a beastmode run. Any lasting change to agent behavior belongs in a separate user-approved maintenance task after the run is complete.

- Same routing mistake twice → record a proposed routing-rule change
- Same QA gap twice → record a proposed addition to the acceptance contract checklist
- Same tool failure twice → record a proposed troubleshooting entry
- Reusable workflow discovered → draft reusable procedure notes for later review
- User correction → record immediately and flag whether a lead-approved future update is needed

## Cost Discipline

### Opus-Led Cost Rules

**Keep Opus for:**
- Interpreting user intent
- Product/creative judgment
- Architecture tradeoffs
- Final review
- Escalation decisions

**Move to Qwen/Gwen:**
- Code generation
- Tests
- Docs
- Data transformations
- Scripts
- Asset assembly
- Repetitive refactors
- Command execution

**Use Codex for:**
- GSD planning
- Adversarial scope/cost review
- Merge gating
- High-risk analysis
- Debugging failed Qwen attempts

### Codex-Led Cost Rules

**Keep Codex for:**
- Planning and architecture
- Adversarial review
- Security/auth/payments/data-loss risk
- Production incidents
- Failed Qwen attempts

**Move to Qwen/Gwen:**
- Everything else (implementation, tests, docs, refactors, scripts, commands)

## Required Final Report

End every beastmode run with:

```text
✅ Beastmode complete: <goal>
Variant: opus-led | codex-led
Harness: <ultraswarm/gsd/delegate_task/claude-code/manual>
Phases completed: <n>
Director / watcher / executor split: <summary>
Models: Opus <x%>, Codex/GPT <y%>, Gwen/Qwen <z%>
Token/cost report: <harness report or estimate>
Verification: <commands and results>
Self-improvement: <learning entry path + promoted updates, if any>
Merge status: <merged/branch ready/blocked>
```

## Choosing Your Variant

**Use Opus-led when:**
- You have Claude Code / Opus available
- The task requires maximum product/creative/architecture judgment
- You're willing to pay for Opus-level decisions but want to minimize Opus implementation spend

**Use Codex-led when:**
- You don't have Opus, or the task doesn't require Opus-level judgment
- Codex/GSD is sufficient for planning and review
- You want the cheapest possible lead with strong gates

**Both variants share:**
- The same worktree isolation, QA, merge, cost-report, and self-improvement gates
- The same acceptance contract requirements
- The same escalation rules
- The same final report format

## Escalation Rules

Escalate from Qwen/Gwen to Codex/Opus when:
- Security, auth, payments, data-loss, legal/financial data, or production incident risk appears
- The work requires non-obvious architecture tradeoffs
- Qwen fails the same acceptance check twice
- The diff is too broad to review cheaply
- The user explicitly asks for frontier reasoning

Escalation does not skip self-improvement. Record why the cheap route failed and whether the routing rule should change.

## Implementation Notes

**Worktree isolation is non-negotiable.** Executors must work in branches/worktrees, never directly in the main tree (unless the task is tiny and explicitly approved by the lead).

**If your preferred harness is unavailable:**
- Fall back to a simpler harness (e.g., `delegate_task` or manual git)
- Record the harness failure in the self-improvement log
- Don't skip isolation — use git branches manually if needed

**The goal is portability.** Beastmode should work in any agent environment (Claude Code, Hermes, OpenClaw, Codex) with any available harness. The principles (role separation, acceptance contracts, self-improvement) are constant; the harness is flexible.

## Self-Improvement Philosophy

Beastmode is not just an execution framework—it's a learning system. Every run should make the next run better.

**During a run:**
- Record observations, errors, and routing mistakes
- Note token/cost surprises
- Flag acceptance gaps

**After a run (in a separate maintenance task):**
- Review learning entries
- Promote repeated patterns into skills/config
- Update routing rules
- Improve acceptance contract checklists
- Draft reusable procedures

**The goal:** Beastmode should get cheaper, faster, and more reliable over time as the learning loop promotes lessons into permanent improvements.

## Context Management (Critical)

Beastmode runs accumulate context fast — subagent outputs, tool results, file diffs, planning docs. Without active management, you'll hit 300-500KB in 10-15 minutes, causing compression timeouts and /compact failures.

**Hard rules:**

1. **Compact every 5-10 minutes** — don't wait for context to break. Run `/compact` after each major phase (planning, execution, QA, merge).
2. **Limit sessions to 30 minutes** — save state (commit work, write learnings), start fresh, resume from saved state.
3. **Subagent output summarization** — instruct subagents to return only final results (files changed, tests passed/failed, issues), not intermediate tool outputs. One subagent task should add <10KB to context, not 100KB.
4. **Break large tasks into small units** — one subagent = one small, bounded task. "Implement auth system" = 200KB output. "Create User model" + "Implement /login" + "Add password hashing" = 3x 20KB outputs.
5. **Enable headroom fail-open mode** — set `HEADROOM_WS_FAIL_OPEN_ON_COMPRESSION_FAILURE=1` in headroom launchd plist. Makes headroom pass through uncompressed instead of returning 413 errors.
6. **Use layered compression** — squeez (CLI output, 60-95%) + headroom (API layer, 60-95%) = 70-80% total savings. Watch for compression tax (agent asking more follow-ups = compression too aggressive).
7. **Compact after 3+ subagent delegations** — rule of thumb. If you've delegated 3 tasks, compact before continuing.

**Alert thresholds:**
- Context size > 200KB → compact now
- Compression failures > 3/hour → enable fail-open or increase timeout
- Session duration > 30 minutes → save state and restart

**What NOT to compress:**
- Error messages and stack traces (need full context for debugging)
- Small files (< 100 lines) — compression overhead > savings
- Structured data the agent needs to parse exactly (JSON APIs, CSV)

See `references/context-rot-mitigation.md` for full details on architectural fixes and monitoring.

## References

- **Context rot mitigation:** See `references/context-rot-mitigation.md` for detailed analysis of context accumulation, architectural fixes, and monitoring strategies.
- **Orchestration comparison:** See `references/orchestration-comparison.md` for the evolution from early prototypes to the current harness-agnostic beastmode.
- **Public sharing checklist:** See `references/public-sharing-checklist.md` for sanitization guidelines when publishing beastmode skills publicly.
