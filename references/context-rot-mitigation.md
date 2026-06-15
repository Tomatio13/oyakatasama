# Context Rot in Multi-Agent Orchestration

## The Problem

Beastmode/ultraswarm orchestrates multiple subagents (Codex, Qwen, Gwen), each generating tool outputs, file reads, and intermediate results. When these outputs accumulate in the main orchestrator's context, the context grows rapidly:

- **10-15 minutes into a beastmode run:** 300-500KB of accumulated context
- **Sources:** Agent summaries, tool outputs, file contents, planning docs, QA results
- **Symptoms:** Headroom compression timeouts (413 errors), Codex /compact failures, "Bad Request" errors

## Root Cause

The orchestrator (Codex/Claude Code) receives the **full output** from each subagent, including:
- Intermediate tool calls and results
- File reads and diffs
- Planning documents
- QA/merge logs
- Self-improvement entries

This is **not** a beastmode skill length issue (the skill is 416 lines, within the 250-450 target). The issue is **context accumulation during execution**.

## Solutions

### Immediate Fixes

#### 1. Enable Headroom Fail-Open Mode

When headroom compression fails, make it pass through uncompressed instead of returning 413 errors.

**Fix:** Add to headroom launchd plist (`~/Library/LaunchAgents/com.headroom.proxy.plist`):

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>HEADROOM_WS_FAIL_OPEN_ON_COMPRESSION_FAILURE</key>
  <string>1</string>
</dict>
```

Then restart:
```bash
launchctl unload ~/Library/LaunchAgents/com.headroom.proxy.plist
sleep 2
launchctl load ~/Library/LaunchAgents/com.headroom.proxy.plist
```

**Tradeoff:** You lose compression on failed payloads, but gain reliability. Better to send uncompressed than to error out.

#### 2. Compact More Aggressively

Don't wait for context to break. Run `/compact` early and often:

- **Every 5-10 minutes** during beastmode runs
- **After each major phase** (planning, execution, QA, merge)
- **Before escalation** (when switching from Qwen to Codex)

**Rule of thumb:** If you've delegated 3+ subagent tasks, compact before continuing.

#### 3. Limit Beastmode Session Duration

Hard stop beastmode runs at **20-30 minutes**, then:
- Save state (commit work, write learnings)
- Start a fresh session
- Resume from the saved state

**Why:** Context grows non-linearly. A 30-minute run might have 200KB, but a 60-minute run might have 600KB+ (due to accumulated diffs, planning docs, etc.).

### Architectural Fixes

#### 4. Subagent Output Summarization

**Problem:** Subagents return full tool outputs, which accumulate in the orchestrator's context.

**Fix:** Subagents should return **only the final result**, not intermediate steps.

**Example:**
```python
# Bad: Subagent returns full execution log
delegate_task(
    goal="Implement feature X",
    # Returns: 50 tool calls, 20 file reads, 10 diffs = 100KB
)

# Good: Subagent returns summary
delegate_task(
    goal="Implement feature X. Return only: (1) files changed, (2) tests passed/failed, (3) any issues. Do not include intermediate tool outputs.",
    # Returns: 3-line summary = 1KB
)
```

**Implementation:** Update ultraswarm to instruct subagents to summarize their outputs.

#### 5. Context Boundaries

**Problem:** Beastmode runs accumulate context indefinitely.

**Fix:** Use explicit context boundaries:
- **Phase 1 (Planning):** Compact before starting execution
- **Phase 2 (Execution):** Compact after each subagent delegation
- **Phase 3 (QA/Merge):** Compact before final review
- **Phase 4 (Self-improvement):** Compact after writing learnings

**Implementation:** Add explicit "compact now" checkpoints to the beastmode loop.

#### 6. Limit Subagent Scope

**Problem:** Subagents tackle large tasks, generating lots of intermediate output.

**Fix:** Break tasks into smaller units. One subagent = one small, bounded task.

**Example:**
```python
# Bad: One subagent implements entire feature
delegate_task(goal="Implement user authentication system")
# Returns: 200KB of output

# Good: Multiple subagents, each with small scope
delegate_task(goal="Create User model with email/password fields")
delegate_task(goal="Implement /login endpoint")
delegate_task(goal="Add password hashing utility")
# Each returns: 10-20KB of output
```

**Tradeoff:** More subagent calls, but each call has smaller context impact.

### Compression Strategy

#### 7. Layered Compression

Use multiple compression layers for maximum savings:

| Layer | Tool | Savings | What It Compresses |
|-------|------|---------|-------------------|
| CLI output | squeez | 60-95% | Terminal commands, git output, test results |
| API layer | headroom | 60-95% | File contents, logs, conversation history |
| Combined | Both | 70-80% | Everything |

**Setup:**
```bash
# Install squeez
cargo install squeez

# Configure for Codex
# Add to ~/.codex/config.json:
{
  "hooks": {
    "PostToolUse": "~/.local/bin/squeez hook codex"
  }
}
```

**Warning:** Watch for "compression tax" — if compression is too aggressive, the agent compensates by asking follow-up questions or re-running commands, emitting MORE tokens than saved. Squeez has adaptive intensity to detect this; RTK does not.

#### 8. Avoid Compressing Critical Context

Some outputs should NOT be compressed:
- Error messages and stack traces (need full context for debugging)
- Small files (< 100 lines) — compression overhead > savings
- Structured data the agent needs to parse exactly (JSON APIs, CSV)
- Interactive prompts (password prompts, Y/N)

**Implementation:** Configure squeez/headroom to skip these patterns.

## Recommended Action Plan

### Phase 1: Immediate Relief (Today)

1. **Enable headroom fail-open mode** — eliminates 413 errors
2. **Add "compact every 5-10 minutes" rule** to beastmode skill
3. **Limit beastmode sessions to 30 minutes** — start fresh after

### Phase 2: Architectural Improvements (This Week)

4. **Update ultraswarm to summarize subagent outputs** — only return final results, not intermediate steps
5. **Add explicit compact checkpoints** to beastmode loop (after each phase)
6. **Install squeez** for CLI output compression (layered with headroom)

### Phase 3: Long-Term Optimization (Next Week)

7. **Break large tasks into smaller subagent units** — reduce per-subagent context
8. **Monitor compression tax** — if agent starts asking more follow-ups, back off compression intensity
9. **Consider context isolation** — run subagents in separate processes that don't share context with orchestrator

## Beastmode Skill Updates

Add a new section to the beastmode skill:

```markdown
## Context Management

Beastmode runs accumulate context fast. Follow these rules to avoid context rot:

1. **Compact every 5-10 minutes** — don't wait for context to break
2. **Limit sessions to 30 minutes** — save state, start fresh, resume
3. **Subagent output summarization** — instruct subagents to return only final results, not intermediate steps
4. **Compact after each phase** — planning, execution, QA, merge, self-improvement
5. **Enable headroom fail-open mode** — `HEADROOM_WS_FAIL_OPEN_ON_COMPRESSION_FAILURE=1`
6. **Use layered compression** — squeez (CLI) + headroom (API) = 70-80% savings
7. **Break large tasks into small units** — one subagent = one small, bounded task

**Rule of thumb:** If you've delegated 3+ subagent tasks, compact before continuing.
```

## Tradeoffs

| Solution | Benefit | Cost |
|----------|---------|------|
| Fail-open mode | Eliminates 413 errors | Lose compression on failed payloads |
| Aggressive compacting | Keeps context small | Lose some context (may need to re-read files) |
| Session limits | Prevents context bloat | Need to save/resume state |
| Subagent summarization | Reduces context accumulation | May lose debugging details |
| Layered compression | 70-80% savings | Setup overhead, potential compression tax |
| Smaller subagent tasks | Less context per task | More subagent calls |

## Monitoring

Track these metrics to detect context rot:

- **Context size:** `curl http://127.0.0.1:8787/stats` — watch for growing payload sizes
- **Compression failures:** Check headroom logs for timeouts/413s
- **Compact frequency:** How often are you running `/compact`?
- **Session duration:** Are beastmode runs exceeding 30 minutes?
- **Subagent output size:** Are subagents returning large outputs?

**Alert thresholds:**
- Context size > 200KB → compact now
- Compression failures > 3/hour → enable fail-open or increase timeout
- Session duration > 30 minutes → save state and restart
