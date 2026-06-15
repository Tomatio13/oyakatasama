# Beastmode: Multi-Agent Orchestration Framework

A structured approach to multi-agent software development that separates high-judgment work (planning, architecture, review) from routine execution (implementation, tests, docs) across different model tiers, with strict cost discipline and a self-improving learning loop.

## What is Beastmode?

Beastmode is an orchestration pattern for AI-assisted development that:

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
