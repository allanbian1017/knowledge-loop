# RFC: Content Summary — Prioritize Reading Decision for Fast Triage

## Summary

Move the `## ⭐ Reading Decision` section directly below `## 🔖 來源 Metadata` (before `## 📝 TL;DR`) in the standard report output template (`content-summary/references/output_template.md`). This enables split-second (<5-second) triage decisions without requiring the user to scroll or read through summary details first.

## Status

**Accepted** — 2026-07-30 (Grill Session)

**Conversation**: `21604227-b448-42d0-830e-9a8cd788773f`

**Affects**: `content-summary` reference library (`output_template.md`, `summarise.md`) and downstream ingest skills (`ingest-newsletter`, `ingest-threads`, `ingest-youtube`, `ingest-website`).

## Motivation

In Content Summary v4.0.0 (Thesis-Driven Analysis), `Reading Decision` was introduced to provide a personalized star rating (anchored to `data/goals.md`), judgment rationale, and a `💡 真正的新資訊` (Novel Insight) bullet.

However, in the v4.0.0 layout, `Reading Decision` was placed after `TL;DR`, `Core Thesis`, and `Reasoning Map`:

```
# {title}
## 來源
## 🔖 來源 Metadata
## 📝 TL;DR                      ← lines ~17-20
## 🎯 Core Thesis                ← lines ~20-27
## 🗺️ Reasoning Map              ← lines ~28-52
## ⭐ Reading Decision            ← lines ~53-66 (Requires scrolling / reading summary first)
```

### The Problem

The user's actual information consumption workflow operates in three distinct phases:

$$\text{1. Scan Header/Metadata} \longrightarrow \text{2. Triage (Read or Skip?)} \longrightarrow \text{3. Deep Read Selectively}$$

With `Reading Decision` situated at line 50+:
- To determine whether a report is worth reading, the user must either scroll down past 35+ lines of text or mentally process `TL;DR` and `Core Thesis` first.
- For low-rated content (★★☆☆☆ or ★☆☆☆☆), reading `TL;DR` before discovering it is low-value wastes cognitive energy.
- For 15+ daily reports, this added friction turns a 30-second daily scan into a 5-minute scrolling exercise.

## Decision Drivers

1. **<5-Second Triage**: The rating (★ stars) and reason to read/skip must be visible immediately on file open without scrolling.
2. **Zero Waste on Low-Value Content**: If an article is a rehash or irrelevant, the user should be able to abandon it in 2 seconds.
3. **Executive Teaser for High-Value Content**: For 4–5★ reports, seeing the rating and key novel insight upfront frames the reader's focus before reading the full summary.
4. **No LLM Generation Quality Regression**: Prompts must maintain rigorous zero-hallucination extraction CoT internally before generating output.

## Proposed Changes

### 1. Reordered Report Structure

Move `Reading Decision` to immediately follow `🔖 來源 Metadata`:

```markdown
# {title}

## 來源
- **來源類型**: {Newsletter | Threads | YouTube | Website}
- **作者 / 寄件者**: {author}
- **原文連結**: {url}
- **處理時間**: {timestamp}
- **任務 ID**: {task_id}

## 🔖 來源 Metadata
{source-specific metadata}

## ⭐ Reading Decision            ← NEW POSITION (Immediate Triage)
- **推薦指數**: {★★★★★ | ★★★★☆ | ★★★☆☆ | ★★☆☆☆ | ★☆☆☆☆} ({語言對應標籤})
- **判斷依據**:
  - [依據 1：錨定 data/goals.md 之相關性與價值]
  - [依據 2：內容深度 / 創新度 / 實用性]
- **💡 真正的新資訊**:
  - [最具有價值的全新觀念，或寫「主要重新整理已知觀念」]

## 📝 TL;DR
- [3-5 句話精準概括：主題背景 + 核心問題 + 主要結論]

## 🎯 Core Thesis
> 一句話核心結論：[作者試圖讓讀者接受的單一核心主張]

支撐論點：
- [支撐論點 1]
- [支撐論點 2]

## 🗺️ Reasoning Map
...

## 🗺️ Visual Map
...

## 🤖 AI Analysis
...
```

### 2. Prompt Instruction Calibration (`summarise.md`)

To ensure the LLM maintains reasoning accuracy despite the layout shift:
- **Internal CoT Ordering**: The LLM system instructions will explicitly require: *"Internally analyze the raw text to extract Zone A facts (TL;DR, Thesis, Reasoning Map) first, evaluate relevance against data/goals.md second, and then render the Markdown output starting with the Reading Decision section."*
- This decoupling guarantees that visual output layout optimization does not degrade internal reasoning quality.

## Considered Options

### Option 1: Move Reading Decision directly below Metadata (Proposed)

- **Pros**: Solves triage speed completely (<5s decision without scrolling); provides an upfront "executive teaser" for high-value reports.
- **Cons**: Reorders Zone B (Judgement) ahead of Zone A (Extraction) in visual document flow.
- **Verdict**: **Recommended.** Visual document flow should serve reader UX, while prompt CoT maintains factual integrity.

### Option 2: Status Quo (`TL;DR` → `Core Thesis` → `Reasoning Map` → `Reading Decision`)

- **Pros**: Zone A extraction precedes Zone B evaluation in strict academic reading order.
- **Cons**: High cognitive load during triage; requires scrolling 30-50 lines to find the rating.
- **Verdict**: Rejected. Fails the user's primary daily triage goal.

### Option 3: Dual Presentation (Rating Badge in Title + Full Section below)

Example title line: `# [★★★★☆] {title}` while keeping the full `Reading Decision` section at line 50.

- **Pros**: Gives star rating in title without reordering body sections.
- **Cons**: Title only has stars, missing the crucial `判斷依據` and `💡 真正的新資訊` needed to understand *why* it got that rating; creates duplicated state maintenance across template parsers.
- **Verdict**: Rejected. Star rating alone without context is insufficient for confident triage decisions.

## Impact & Trade-offs Analysis

| Metric | Before (v4.0.0) | Proposed (v4.3.0) | Net Effect |
|---|---|---|---|
| **First-screen visibility** | Metadata + TL;DR | Metadata + Reading Decision + TL;DR top | ⭐ **Major Gain**: Rating visible on page load |
| **Scroll required for triage** | Yes (30-50 lines) | No (0 lines) | ⭐ **Major Gain**: 5s decision time |
| **Reading sequence for 4-5★** | Facts → Rating | Rating → Facts | 💡 **Gain**: Rating & novel insight frame expectations |
| **Template changes** | None | `output_template.md`, `summarise.md` | 🛠️ Minor doc update, backward compatible |

## Verification Plan

### Automated Tests
- Verify all reference templates render valid Markdown.
- Test report generation across sample ingest tasks to ensure section headers are cleanly parsed.

### Manual Verification
- Review generated sample report on desktop and mobile viewports to confirm `Reading Decision` appears above the fold without scrolling.

## Architecture Decision Records (ADRs)

### ADR-0002: Upfront Reading Decision Placement for Immediate Triage

**Status**: Accepted · **Date**: 2026-07-30

**Context**:
In v4.0.0, `Reading Decision` was located after `Reasoning Map` (line 50+). To triage whether a report was worth reading, readers had to scroll past ~35 lines or read through `TL;DR` and `Core Thesis` first.

**Decision**:
Place `## ⭐ Reading Decision` immediately below `## 🔖 來源 Metadata` (before `## 📝 TL;DR`).

**Consequences**:
- Enables <5-second triage without scrolling.
- Low-rated reports (★★☆☆☆ or ★☆☆☆☆) can be abandoned immediately without reading summary text.
- High-rated reports (★★★★☆ or ★★★★★) provide an executive teaser that frames expectations for `TL;DR` and `Core Thesis`.

---

### ADR-0003: Decoupled Internal CoT Reasoning from Visual Output Order

**Status**: Accepted · **Date**: 2026-07-30

**Context**:
Changing visual output layout so that Zone B (`Reading Decision`) precedes Zone A (`TL;DR`, `Core Thesis`, `Reasoning Map`) might tempt the LLM to judge content relevance before extracting facts, risking biased ratings.

**Decision**:
Explicitly instruct the LLM in system prompts (`summarise.md`) to perform Zone A factual extraction first in internal Chain-of-Thought (CoT) reasoning, synthesize relevance second, and then render the Markdown output starting with `Reading Decision`.

**Consequences**:
- Maintains zero-hallucination factual extraction integrity.
- Incurs zero additional latency or extra API calls.

---

### ADR-0004: Forward-Only Report Template Migration Policy

**Status**: Accepted · **Date**: 2026-07-30

**Context**:
Over 70 historical report files exist in `./reports/` using the v4.0.0 section ordering.

**Decision**:
Apply the new top-placed `Reading Decision` structure only to newly generated reports. Leave existing historical files untouched.

**Consequences**:
- Eliminates git noise and churn on archived report files.
- Downstream summary distillers continue to parse both old and new reports safely.
