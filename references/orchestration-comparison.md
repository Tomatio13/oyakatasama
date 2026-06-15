---
name: beastmode-orchestration-comparison
description: Evolution of the beastmode orchestration pattern from early prototypes to the current harness-agnostic framework.
title: Beastmode orchestration evolution
created: 2026-06-14
---

# Beastmode Orchestration Evolution

## Early Prototype (Video Production)

The original beastmode pattern emerged from a video production workflow that needed cost-efficient multi-agent orchestration:

**Strengths:**
- Clear cost hierarchy: expensive creative director, watcher/reviewer, cheap executor
- Strong acceptance gates and checkpoint names
- Explicit warning against using expensive models for mechanical implementation
- Domain-specific acceptance contracts for rendered assets
- Explicit paid-credit / credential escalation rules

**Weaknesses:**
- It was a project folder, not a portable skill
- The orchestration was described as a north-star design, not fully wired
- Checkpoints were not implemented as commands
- It mixed project-specific facts with reusable orchestration guidance
- Self-improvement was implied but not formalized as a required loop

## First Portable Skill (v1.0)

The pattern was generalized into portable `SKILL.md` files for use across multiple agent runtimes:

**Strengths:**
- Portable skill format available to multiple agents
- Generalized beyond video production to feature implementation
- Clear cheap/default vs expensive/escalation routing

**Weaknesses:**
- Too abstract: described patterns but did not enforce concrete defaults
- Did not enforce worktree isolation strongly enough
- Did not include acceptance contracts as a hard precondition
- Did not require a self-improving loop after each phase
- Token/cost reporting was described but not central

## Current Unified Skill (v2.0)

The unified beastmode skill consolidates all variants into one harness-agnostic framework:

**Improvements:**
- Harness-agnostic: works with any orchestration tool (Ultraswarm, GSD, delegate_task, Claude Code subagents, or manual git workflow)
- Worktree isolation is a hard rule
- Acceptance contract required before delegation
- Adversarial review required before merge
- Self-improvement entry required after every phase
- Repeated routing/QA/tool failures must promote into skill or config changes
- No local path assumptions — fully portable
- Clear harness selection guide with comparison table
- Both Opus-led and Codex-led variants in one document

## Key Principles (Unchanged)

Throughout all versions, these principles have remained constant:

1. **Expensive models decide, cheap models build** — never burn expensive tokens on routine implementation
2. **Isolation is non-negotiable** — executors work in branches/worktrees, never directly in main
3. **Acceptance contracts before delegation** — no vague tasks
4. **Adversarial review before merge** — executor self-report is never enough
5. **Self-improvement is mandatory** — every phase records lessons, repeated patterns get promoted
