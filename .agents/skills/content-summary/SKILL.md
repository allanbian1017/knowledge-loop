---
name: content-summary
description: "Shared content summarisation and AI analysis pipeline. Provides reusable references for thesis-driven analysis quality rules, AI analysis with user-preference calibration, and suggestion logging. Referenced by ingest skills (ingest-newsletter, ingest-threads, ingest-youtube, ingest-website). Do not invoke this skill directly."
---

# content-summary

Shared reference library for the content intelligence pipeline. **Do not invoke directly** — ingest skills reference these files during their execution.

This skill follows the same pattern as `gws-shared`: it provides reusable rules and templates that multiple skills need.

## Reference Files

| File | When to read | What it provides |
|---|---|---|
| `references/output_template.md` | Before structuring the report | Standard v5.0 Answer-First Pyramid template: Top 1-sentence conclusion + triage/action callout, 3–5 numbered `核心重點`, conditional `一張表看懂`, and per-topic `<details>` accordions (`深入解構` + `對我的意義與來源資訊`) |
| `references/summarise.md` | Before generating any summary | Configurable output language rules, Inverted Pyramid (3s → 15s → 2m) hierarchy, Three-Zone rule with Just-in-Time inline analogies, and 6 low-cognitive-load guardrails |
| `references/ai_analysis.md` | Before generating the AI analysis | Field definitions, `$DATA_REPO/data/goals.md` + `$DATA_REPO/data/user_preferences.md` calibration instructions |
| `references/suggestion_log.md` | After generating the AI analysis | Append format and rules for `$DATA_REPO/data/suggestions_pending.md` |
| `references/filename_rules.md` | Before writing any report file | Path sanitisation and directory naming convention |
