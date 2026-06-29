# Beastmode: MofA Multi-Agent Orchestration Framework

Beastmode is a **Mixture of Agents (MofA)** orchestration framework for AI-assisted software development, Hermes Agent, OpenClaw, Claude Code, Codex, Qwen, and MemroOS/memroos-style agent memory systems.

Beastmode separates high-judgment work (planning, architecture, review) from routine execution (implementation, tests, docs) across different model tiers, with strict cost discipline, context-rot protection, and a self-improving learning loop.

## What is Beastmode?

Beastmode is an orchestration pattern for AI-assisted development and long-running agent goals. It uses MofA / Mixture of Agents at decision gates, cheap executors for bounded implementation work, and MemroOS-style durable state handoffs so agents do not resume from compressed chat history alone.

Exact search aliases: **beastmode**, **MofA**, **Mixture of Agents**, **memroos**, **MemroOS**, **Hermes Agent**, **OpenClaw**, **agent orchestration**, **context rot mitigation**.

Beastmode:

- **Saves money** by routing routine work to cheap models (Qwen/Gwen) while keeping expensive models (Opus, Claude Code, Codex) for judgment and review
- **Improves quality** through mandatory acceptance contracts, adversarial review, and merge gates
- **Gets better over time** via a self-improvement loop that records lessons and promotes repeated patterns into skills/config
- **Works anywhere** — harness-agnostic, compatible with Ultraswarm, GSD, `delegate_task`, Claude Code subagents, or manual git workflows

## Core Principle

**Expensive models decide. Cheap models build. The loop learns.**

## Two Variants

- **Opus-led:** Maximum judgment for product/creative/architecture decisions. Opus directs, Codex challenges, Qwen executes.
- **Codex-led:** Cost-efficient lead with strong gates. Codex plans and reviews, Qwen executes.

## Quick Start

1. Read `SKILL.md` — the full framework
2. Choose your variant (Opus-led or Codex-led)
3. Choose your harness (Ultraswarm, GSD, delegate_task, Claude Code subagents, or manual git)
4. Follow the beastmode loop: Preflight → Acceptance Contract → Plan → Delegate → Review → Merge → Self-Improve

## Files

- `SKILL.md` — The complete beastmode framework (start here)
- `references/orchestration-comparison.md` — Evolution from early prototypes to v2.0
- `references/context-rot-mitigation.md` — MemroOS-style goal-state capsules, compact/resume rules, and MofA decision memory
- `references/public-sharing-checklist.md` — Guidelines for publishing beastmode skills publicly

## Compatibility

Works with:
- **Claude Code** (Opus-led or Codex-led)
- **Hermes Agent** (Codex-led with delegate_task)
- **OpenClaw** (Codex-led with delegate_task)
- **Codex CLI** (Codex-led with subagents)
- **Any agent environment** with git and model access

## License

MIT — use it, fork it, improve it.
