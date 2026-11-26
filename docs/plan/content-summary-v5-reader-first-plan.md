# Implementation Plan - Content Summary v5.0 (Answer-First Pyramid & Low-Cognitive-Load Hierarchy)

Reorganize `content-summary`, `daily-distiller`, `ingest-website`, and worker sub-agent personas around **Answer First, Explain Later (Pyramid / BLUF)** and **ADHD-friendly working-memory limits** so every report delivers its 1-sentence conclusion on line 1, fits its core takeaways and comparison table on a single ~25-line screen, and isolates formulas/benchmarks into modular per-topic `<details>` accordions.

For the detailed technical architecture, design trade-offs, and decisions, please refer to the corresponding RFC/ADR: [Content Summary v5.0 — Answer-First Pyramid](../rfc/content-summary-v5-reader-first.md).

## User Review Required

> [!NOTE]
> Designed interactively with user guidance to freely reorganize the report format around **Answer First, Explain Later** (1-sentence conclusion first, minimal cognitive load, tables over prose, Just-in-Time inline analogies, and collapsible `<details>` hierarchy). Historical reports in `reports/` remain untouched unless explicitly requested.

## Open Questions

- None.

---

## Proposed Changes

### Shared Content Summary Library

#### [MODIFY] [SKILL.md](../../.agents/skills/content-summary/SKILL.md)
* Update reference table descriptions to reflect the v5.0 Answer-First Pyramid and per-topic `<details>` accordions.

#### [MODIFY] [output_template.md](../../.agents/skills/content-summary/references/output_template.md)
* Replace top metadata boilerplate and multi-summary layout with a 3-second top callout (`🎯 一句話結論` + `⭐ 推薦度 · 🔗 原文 · ⚡ 下一步`), 3–5 numbered 1-line `## 💡 核心重點`, conditional `## 📊 一張表看懂` comparison table (`≤5 rows`), per-topic `<details>` accordions under `## 🔍 深入解構` (`≤3 short bullets` each), and a collapsed `🧭 對我的意義與來源資訊` footer.

#### [MODIFY] [summarise.md](../../.agents/skills/content-summary/references/summarise.md)
* Define the 3s → 15s → 2m Inverted Pyramid hierarchy, Zone A+ Just-in-Time inline analogies (`≤10–12 chars`), and 6 cognitive-load guardrails (`≤5 items` cap, tables over prose, per-topic accordions with GFM blank lines, specific minute estimates, zero preamble).

#### [MODIFY] [README.md](../../.agents/skills/content-summary/README.md)
* Document `v5.0.0` in Changelog and `ADR-0009` through `ADR-0011` (Answer-First Pyramid, Just-in-Time Context Bridge, and Per-Topic Collapsible Accordions).

---

### Ingestion & Daily Distillation Skills

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-website/SKILL.md) & [README.md](../../.agents/skills/ingest-website/README.md)
* Route Website domain/date metadata into the collapsed `🧭 對我的意義與來源資訊` footer block so line 1 starts directly with `🎯 一句話結論`.

#### [MODIFY] [SKILL.md](../../.agents/skills/daily-distiller/SKILL.md), [output_template.md](../../.agents/skills/daily-distiller/assets/output_template.md), & [README.md](../../.agents/skills/daily-distiller/README.md)
* Upgrade `Knowledge_Distillation_YYYY_MM_DD.md` to the matching Answer-First Pyramid (`🎯 今日一句話結論` + `⚡ 本週唯一行動` → numbered `💡 今日核心重點` → `📊 跨來源主題速覽` table → per-pillar `<details>` accordions).

---

### Sub-Agent Personas & Automated Tests

#### [MODIFY] Sub-Agent Personas in `.agents/agents/`
* Update `website_worker.md`, `newsletter_worker.md`, `threads_worker.md`, `youtube_worker.md`, and `distiller_reviewer.md` to enforce the v5.0 Answer-First Pyramid, then propagate to `.claude/` and `.codex/` via `scripts/sync_subagents.py`.

#### [MODIFY] [test_output_template.py](../../tests/test_output_template.py)
* Assert v5.0 Inverted Pyramid section order, GFM blank lines inside `<details>`, Just-in-Time context & `≤5 items` rules in `summarise.md`, and `daily-distiller` Answer-First template invariants.

---

## Verification Plan

### Automated Tests
- **What to test**: v5.0 Answer-First Pyramid template order, GFM `<details>` blank lines, summarisation guardrails, and `daily-distiller` template
  - **How to test**: `pytest -p no:recording tests/test_output_template.py`
  - **Expected behavior**: All 4 tests pass with exit code 0.
- **What to test**: Full repository Python test suite regression check
  - **How to test**: `pytest -p no:recording --ignore=tests/test_compile_session_learnings.py`
  - **Expected behavior**: All 65 active tests pass with exit code 0.
- **What to test**: Skill frontmatter, language policy hooks, and multi-platform sub-agent sync
  - **How to test**: `python3 scripts/validate_skill.py .agents/skills/content-summary/SKILL.md .agents/skills/ingest-website/SKILL.md .agents/skills/daily-distiller/SKILL.md`, `python3 scripts/validate_language_config.py`, and `python3 scripts/sync_subagents.py`
  - **Expected behavior**: All commands succeed with exit code 0.
