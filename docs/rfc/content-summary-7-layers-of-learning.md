# RFC: Adopt "7 Layers of Learning From Information" in content-summary

## Summary

Replace the shallow extraction template (Executive Summary → Key Highlights → Action Items) with a structured 7-layer deep-learning framework that transforms reports from information summaries into reusable knowledge artefacts.

## Status

**Proposed** — 2026-05-15

## Motivation

Current reports capture *what* a source says but not *why it matters*. Concrete example from today's pipeline:

```
## 🚀 行動呼籲 / 延伸思考
- 行動: 考慮在目前的 AI 工作流中增加「內容再生」環節。
```

This is vague, unactionable, and indistinguishable from the summary itself. The reader gains no lasting insight.

The "7 Layers of Learning From Information" framework structures reading into escalating depth:

| Layer | Question | Current coverage |
|---|---|---|
| 1. Core Idea | What is this really saying? | ✅ 核心總結 (shallow) |
| 2. Signal vs Noise | Why is this important? | ❌ Not captured |
| 3. Mechanism Understanding | How does it actually work? | ⚠️ Partially in Key Highlights |
| 4. Personal Relevance | Why should I care? | ❌ Not captured |
| 5. Actionability | What can I do now? | ⚠️ 行動呼籲 (vague) |
| 6. Idea Generation | What new combinations does this create? | ❌ Not captured |
| 7. Reflection & Prediction | What happens next? | ❌ Not captured |

Only 1.5 of 7 layers are currently addressed. The most valuable layers (4–7: personal synthesis) are entirely absent.

## Detailed Design

### New Report Structure

```
## 來源                                           ← unchanged
## 🔖 來源 Metadata                               ← unchanged
## 📝 核心總結（Core Idea）                        ← renamed, deeper (Layer 1)
## 📌 關鍵重點（Key Highlights）                   ← unchanged
## 🔍 深度分析（Deep Analysis）                    ← NEW (Layers 2–7)
  ### 2️⃣ 訊號判斷（Signal vs Noise）
  ### 3️⃣ 機制理解（Mechanism Understanding）
  ### 4️⃣ 個人相關性（Personal Relevance）
  ### 5️⃣ 可行動性（Actionability）
  ### 6️⃣ 靈感觸發（Idea Generation）
  ### 7️⃣ 反思與預測（Reflection & Prediction）
## ⚠️ 資訊免責聲明（Disclaimers）                  ← unchanged
---
## 📄 原始內容（Raw Content）                      ← unchanged
```

**Removed sections:**
- `📝 核心總結（Executive Summary）` → merged into `📝 核心總結（Core Idea）` (same heading position, deeper content)
- `🚀 行動呼籲 / 延伸思考` → absorbed by Layers 4–5

### Two-Zone Quality Rule

The existing Zero Hallucination rule ("嚴禁引入任何外部知識") conflicts with layers 4–7 which are inherently inferential. Resolution: explicit two-zone system.

| Zone | Sections | Rule |
|---|---|---|
| **Zone 1: Extraction** | 核心總結, 關鍵重點, Layers 2–3 | Strict Zero Hallucination. Only source-faithful facts. |
| **Zone 2: Synthesis** | Layers 4–7 | Grounded inference allowed. Must be based on facts extracted in Zone 1. No external knowledge. |

Zone 2 reads `data/goals.md` to ground Layer 4 (Personal Relevance) in the user's actual priorities. This is not "external knowledge" — it is user context, analogous to how `ai_analysis.md` already reads `data/goals.md` for suggestion scoring.

### Layer Content: Guiding Questions, Not Rigid Fields

Each layer heading is fixed (`### 2️⃣ 訊號判斷（Signal vs Noise）`) but the content beneath is free-form. The `summarise.md` reference provides guiding questions per layer, not mandatory sub-fields:

**Layer 1 — Core Idea** (in `📝 核心總結`):
- What's the central claim? Why does this matter? What's the underlying principle?
- Quality bar: thesis-level, not surface description.
  - ❌ "AI agents are trending."
  - ✅ "LLMs become dramatically more useful when combined with memory + tools + feedback loops."

**Layer 2 — Signal vs Noise**:
- Durable or hype? Apply the 3-year test. Paradigm shift or local optimization?
- Does this change economics, workflows, or incentives?

**Layer 3 — Mechanism Understanding**:
- Why does this happen? What are the inputs, outputs, constraints?
- What tradeoffs exist? What breaks this model?
- Quality bar: causality, not conclusions.
  - ❌ "RAG improves performance."
  - ✅ "RAG offloads knowledge retrieval from transformer attention into external retrieval systems, reducing context pressure and improving freshness."

**Layer 4 — Personal Relevance** (Zone 2):
- Read `data/goals.md`. Where does this intersect with current work?
- Does this solve a current pain point? Reveal a new opportunity?

**Layer 5 — Actionability** (Zone 2):
- What experiment can I run? What should I try this week?
- Must be concrete and time-bounded. No "研究看看" allowed.

**Layer 6 — Idea Generation** (Zone 2):
- What does this remind me of? What can this combine with?
- What industries are still not using this? New project ideas triggered?

**Layer 7 — Reflection & Prediction** (Zone 2):
- Second-order effects? Who benefits, who loses?
- What becomes more valuable? What becomes obsolete?

All 7 layers always present. Low-signal sources produce terse layers (1–2 lines each), not empty ones.

### Example: Zhu Qi Report (Before vs After)

**Before (current):**
```markdown
## 📝 核心總結（Executive Summary）
- 朱騏介紹一魚多吃內容策略，將長文提取金句製作圖卡。

## 📌 關鍵重點（Key Highlights）
- **平台拓展策略**: FB 長文 → IG 圖卡，觸及不同讀者群。
- **實踐方式**: 從長文提取 5-7 句金句，獨立製作成圖卡。

## 🚀 行動呼籲 / 延伸思考
- 考慮在目前的 AI 工作流中增加「內容再生」環節。
```

**After (7 layers):**
```markdown
## 📝 核心總結（Core Idea）
- 同一份內容的價值不在於內容本身，而在於它被多少不同受眾消費。
  將長文拆解為獨立圖卡，以零邊際成本觸及完全不同的讀者群。

## 📌 關鍵重點（Key Highlights）
- **平台拓展策略**: FB 長文 → IG 圖卡，觸及不同讀者群。
- **實踐方式**: 從長文提取 5-7 句金句，獨立製作成圖卡。
- **成本結構**: 一次創作，多次分發，邊際成本趨近於零。

## 🔍 深度分析（Deep Analysis）

### 2️⃣ 訊號判斷（Signal vs Noise）
- 內容再利用本身是成熟策略，非新典範。但在 AI 自動化脈絡下，
  圖卡生成可完全自動化，使此策略的執行成本從「低」降至「接近零」。
  持久性中等，3 年內仍有效。

### 3️⃣ 機制理解（Mechanism Understanding）
- 核心機制：不同平台有不同的內容消費模式（長文 vs 圖卡）。
  同一份知識以不同格式呈現 → 觸及不同受眾 → 擴大影響力。
  限制：圖卡需要視覺設計能力，且金句脫離上下文可能失去精確性。

### 4️⃣ 個人相關性（Personal Relevance）
- 目前 AI 工作流已有 ingest pipeline 產出 Markdown 報告。
  報告本身即可作為「長文」來源，從中提取金句。
  與「優化個人工作流程與生產力」目標直接相關。

### 5️⃣ 可行動性（Actionability）
- 本週可嘗試：在 daily-distiller 輸出中加入
  「📌 今日金句（Top 3 Quotes）」區塊，自動從各報告提取最具分享性的句子。

### 6️⃣ 靈感觸發（Idea Generation）
- 結合 generate_image 工具，可建立「報告 → 金句 → 圖卡」的全自動 pipeline。
  類似 content-summary 的 skill 架構，但輸出為圖片而非 Markdown。

### 7️⃣ 反思與預測（Reflection & Prediction）
- 當圖卡生成完全自動化，內容分發的瓶頸從「製作」轉移到「品味」——
  選擇哪些金句值得分享成為核心判斷力。
```

### Suggestion Log: No Change

The `ai_analysis.md` fields (分類 / 價值評分 / 可行動性 / 建議下一步 / 決策建議) remain independent from report layers 4–5. Different audiences:
- Report layers = learning artefact for the reader
- Suggestion log = action queue for `review-suggestions` skill

Minor addition to `ai_analysis.md`: a note acknowledging the overlap and confirming separation.

### File Changes

```
content-summary/
├── SKILL.md                                [MODIFY] update output_template.md description
├── README.md                               [MODIFY] add v2.0.0 changelog entry
└── references/
    ├── output_template.md                  [MODIFY] new report structure
    ├── summarise.md                        [MODIFY] add two-zone rule + 7-layer guiding questions
    └── ai_analysis.md                      [MODIFY] add separation note (1 line)
```

No changes to:
- `suggestion_log.md` — format unchanged
- `filename_rules.md` — unrelated
- `ingest-newsletter/` — reads shared references, no local changes needed
- `ingest-threads/` — same
- `ingest-youtube/` — same
- `daily-distiller/` — reads reports freely; richer input improves output

### Downstream Compatibility

| Consumer | Impact | Action |
|---|---|---|
| `daily-distiller` | Richer input (layers 2–7 give structured themes). `📝 核心總結` heading preserved. | None. Observe quality 2–3 days, then optionally tune. |
| `review-suggestions` | No change. Reads `suggestions_pending.md` which is format-unchanged. | None. |
| Old reports | Mixed format in `reports/`. Distiller already handles mixed formats. | None. No retroactive reformatting. |

## Drawbacks

- **Report length increases ~1.8x** — 9 reports/day × ~70 lines = ~630 lines vs ~360 lines today. Mitigated: low-signal sources produce terse layers. The additional reading provides proportionally more value (synthesis, not repetition).

- **Token cost increases** — Each report generation uses more LLM tokens for layers 4–7. Estimated ~30-50% more per report. Acceptable for the quality improvement.

- **Two-zone rule adds cognitive load for the agent** — Must track which zone it's in. Mitigated: explicit boundary (`## 🔍 深度分析` heading) makes the transition unambiguous.

## Alternatives Considered

### Alternative 1: Signal-gated depth (Layer 2 as gatekeeper)

If Layer 2 judges signal as low, skip layers 3–7. Reduces output for low-signal sources.

**Rejected**: User reads all reports directly. Even low-signal content benefits from terse synthesis layers. Forcing an early gate loses potential cross-domain connections (Layer 6).

### Alternative 2: 7 layers in distiller only, not per-report

Keep individual reports shallow. Run 7-layer analysis only during daily distillation across all sources.

**Rejected**: User reads individual reports as standalone artefacts. Each must provide complete learning value independently.

### Alternative 3: Rigid sub-fields per layer

Each layer has mandatory named fields (e.g., Layer 2 always has `持久性`, `影響層級`, `影響領域`).

**Rejected**: Produces robotic, form-filling output. Some sources don't have meaningful answers for all sub-fields. The 7-layer framework is a thinking tool, not a form. Layer headings provide structure; content within must be natural.

### Alternative 4: Merge suggestion log with report layers 4–5

Derive `ai_analysis.md` suggestion fields directly from layers 4–5 in the report.

**Rejected**: Creates fragile coupling. Report layers = free-form prose for human reading. Suggestion log = structured fields for programmatic review. Different audiences, different formats. Small redundancy in agent thinking is acceptable.

### Alternative 5: Keep Executive Summary as separate section above Layer 1

Preserve the 1–2 sentence quick-scan anchor before the deeper Core Idea analysis.

**Rejected**: Redundant. Layer 1 (Core Idea) opens with thesis-level summary that serves the same quick-scan purpose while going deeper. Merging eliminates a duplicative section.

## Unresolved Questions

None. All design decisions resolved during planning session (9 decisions, see ADR below).

## Implementation Plan

1. Modify `references/output_template.md` — new report structure.
2. Modify `references/summarise.md` — add two-zone rule and 7-layer guiding questions.
3. Modify `references/ai_analysis.md` — add separation note.
4. Modify `SKILL.md` — update reference table description.
5. Modify `README.md` — add v2.0.0 changelog entry.
6. Verify: process one newsletter with updated template, confirm output structure.
7. Verify: run `daily-distiller` on mixed old+new reports, confirm graceful handling.

---

# ADR: Report Template Structure for 7 Layers of Learning

## Status

Proposed — 2026-05-15

## Context

The content-summary output template produces shallow reports. The `📝 核心總結` restates the source title. The `🚀 行動呼籲` offers vague suggestions. Layers 2–7 of the "7 Layers of Learning From Information" framework (Signal, Mechanism, Relevance, Actionability, Ideas, Prediction) are entirely absent. Reports capture information but do not transform it into knowledge.

## Decision Drivers

- **Learning depth**: Reports are read directly by the user as standalone learning artefacts.
- **Downstream quality**: `daily-distiller` synthesizes reports; richer per-report analysis produces better cross-source connections.
- **Zero Hallucination compatibility**: Existing quality rules must coexist with inherently inferential layers (4–7).
- **Consistency**: All ingest skills share `content-summary/references/output_template.md`.

## Decisions Made

Nine design decisions were resolved during the planning session:

### Decision 1: Primary Consumer

**Context**: Reports serve two consumers — user reading directly and daily-distiller synthesizing.

**Decision**: Optimize for both. Full 7-layer depth per report.

**Rationale**: User reads reports first, then distiller. Each report must stand alone. Distiller benefits from richer structured input.

---

### Decision 2: Layer Presence

**Context**: Some sources are low-signal (e.g., marketing newsletters). Should layers be conditional?

**Decision**: All 7 layers always present. Low-signal sources produce terse layers (1–2 lines).

**Rationale**: User reads all reports. Even low-signal content benefits from brief synthesis. Terse layers have negligible reading cost.

---

### Decision 3: Zero Hallucination vs Inference

**Context**: Layers 4–7 require inference (personal relevance, predictions). The existing Zero Hallucination rule forbids any external knowledge.

**Decision**: Two-zone rule. Zone 1 (核心總結 + 關鍵重點 + Layers 2–3) = strict Zero Hallucination. Zone 2 (Layers 4–7) = grounded inference, must cite Zone 1 facts.

**Rationale**: Clean separation mirrors the framework's natural structure: extraction (objective) then synthesis (subjective). The `## 🔍 深度分析` heading marks the boundary unambiguously.

---

### Decision 4: Executive Summary Handling

**Context**: Old `📝 核心總結（Executive Summary）` and Layer 1 (Core Idea) cover the same ground.

**Decision**: Merge. Rename to `📝 核心總結（Core Idea）`. Same heading position, deeper content (thesis + principle + problem).

**Rationale**: Eliminates redundancy. Distiller still finds the heading at the expected position. Content upgrades from surface description to first-principles insight.

---

### Decision 5: Heading Hierarchy

**Context**: Should layers 2–7 each be `##` top-level or grouped under a parent?

**Decision**: Grouped under `## 🔍 深度分析（Deep Analysis）` as `###` sub-headings.

**Rationale**: Clean TOC (6 top-level sections, not 10). Visually separates "what this says" (核心總結 + 關鍵重點) from "what this means" (深度分析). Matches two-zone rule boundary.

---

### Decision 6: Key Highlights Preservation

**Context**: `📌 關鍵重點` contains concrete factual bullet points. Where do they live in the 7-layer model?

**Decision**: Keep as separate `##` section between 核心總結 and 深度分析.

**Rationale**: Key Highlights = factual extraction (Zone 1). Layers = interpretation. Reader flow: "what happened" → "what it means." Some sources have 5-8 distinct facts that don't map to a single mechanism.

---

### Decision 7: Sub-field Format

**Context**: Should each layer have mandatory named sub-fields (e.g., Layer 2: 持久性 / 影響層級 / 影響領域)?

**Decision**: Guiding questions in `summarise.md`, not rigid template fields. Layer headings fixed; content free-form.

**Rationale**: The 7-layer framework is a thinking tool, not a form. Forcing sub-fields produces robotic output. Agent picks relevant questions per source.

---

### Decision 8: Suggestion Log Relationship

**Context**: Layers 4 (Personal Relevance) and 5 (Actionability) overlap with `ai_analysis.md` suggestion fields.

**Decision**: Keep separate. Report layers = learning artefact. Suggestion log = action queue. No coupling.

**Rationale**: Different audiences, different formats. Suggestion log is consumed programmatically by `review-suggestions`. Report layers are free-form prose for human reading. Small redundancy is acceptable.

---

### Decision 9: Distiller Changes

**Context**: `daily-distiller` reads all reports. New structure changes headings.

**Decision**: No distiller changes. Observe quality with new format for 2–3 days before deciding.

**Rationale**: Distiller reads reports narratively ("Read every report file in full"), not by rigid heading parsing. `📝 核心總結` heading is preserved. Richer layer content gives distiller better raw material automatically.

## Consequences

### Positive

- Reports transform from information summaries into reusable knowledge artefacts.
- Layers 4–5 provide concrete, goal-calibrated action items instead of vague suggestions.
- Layer 2 (Signal vs Noise) explicitly labels content durability — helps the user allocate attention.
- Layer 6–7 trigger cross-domain connections and predictions that don't emerge from shallow extraction.
- `daily-distiller` gets structured analytical input per layer, improving synthesis quality.

### Negative

- Report length increases ~1.8x. Accepted: additional content is analysis, not repetition.
- Token cost per report increases ~30-50%. Accepted: quality improvement is proportional.
- Two-zone rule adds one more concept for the agent to track. Mitigated by unambiguous heading boundary.

### Risks

- **Agent quality variance**: Layer 4–7 content quality depends on the LLM's ability to make meaningful connections. Low-quality inference is worse than no inference.
  - **Mitigation**: Quality examples (good vs bad) in `summarise.md` set the bar explicitly. Terse-but-honest beats verbose-but-shallow.
- **Template drift**: Future edits to `output_template.md` must maintain the two-zone boundary. No risk today, but worth noting for future maintainers.

## References

- 7 Layers of Learning From Information — original framework
- content-summary SKILL.md — current skill index
- Unified Output Format RFC — prior RFC that created the unified template being modified
