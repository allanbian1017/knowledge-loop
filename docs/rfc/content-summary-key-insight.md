# RFC: Add「關鍵洞察（Key Insight）」Section to content-summary Reports

## Summary

Add a new `## 💡 關鍵洞察（Key Insight）` section between 核心總結 and 關鍵重點 that distils the content's most transferable principles with transparent provenance — splitting each insight into 📌 原文洞察 (extraction) and 💡 延伸洞察 (synthesis).

## Status

**Proposed** — 2026-06-05

## Motivation

The current report template has a gap between "What this content covers" and "Why it matters":

| Existing Section | What it answers | Gap |
|---|---|---|
| 📝 核心總結（Core Idea） | What is this content about? (descriptive) | ✅ covered |
| 📌 關鍵重點（Key Highlights） | What are the major facts? (factual extraction) | ✅ covered |
| 🔍 深度分析（Layers 2–7） | Why does it matter? How to apply it? | ✅ covered |
| **❓ Key Insight** | **What's the single transferable principle to remember?** | **❌ missing** |

Core Idea tells you *what*; the reader still has to work to extract the *so what*. Deep Analysis covers this at length but is 6 layers deep. There is no quick-access "elevator pitch" of the distilled principle.

**Concrete example** — from the Ara Khan report ([Dont_Build_Slop](../reports/YouTube_2026_05_27/Dont_Build_Slop_4_Levels_of_AI_Agent_Maturity_Ara_Khan_Cline.md)):

```markdown
## 📝 核心總結（Core Idea）
- 在當前大眾對 AI Agent 盲目追求與集體焦慮（Mass Psychosis）的背景下，
  開發者應理性回歸，將 Agent 熟度分為四個層級…
```

This is accurate but *descriptive*. The reader remembers "there are 4 levels" but not the deeper principle. A Key Insight would capture:

```markdown
## 💡 關鍵洞察（Key Insight）
- 📌 原文洞察: 所有 Agent 本質上都是一個帶終止條件的 while loop；
  官方將 GPT-5 到 GPT-5.3 的 System Prompt 縮減了三分之二，
  因為過度指令使 Frontier model 表現變差。
- 💡 延伸洞察: 工程師對 Agent 架構的深度思考比 token throughput 更重要——
  在狀態機設計上花的時間，比在 System Prompt 上堆規則更有價值。
```

The `📌` line is directly from the source (Zone 1). The `💡` line is a transferable principle sharpened from the source's argument (Hybrid zone).

## Detailed Design

### New Section Placement

```
## 來源                                           ← unchanged
## 🔖 來源 Metadata                               ← unchanged
## 📝 核心總結（Core Idea）                        ← unchanged
## 💡 關鍵洞察（Key Insight）                      ← NEW
## 📌 關鍵重點（Key Highlights）                   ← unchanged
## 🔍 深度分析（Deep Analysis）                    ← unchanged
  ### 2️⃣ ~ 7️⃣                                    ← unchanged
## ⚠️ 資訊免責聲明（Disclaimers）                  ← unchanged
---
## 📄 原始內容（Raw Content）                      ← unchanged
```

Reading flow: What → So What → Details → Analysis — a natural funnel from broad to deep.

### Section Format

Each insight is a pair of sub-bullets:

```markdown
## 💡 關鍵洞察（Key Insight）
- 📌 原文洞察: [directly from source — Zone 1, zero hallucination]
- 💡 延伸洞察: [transferable principle sharpened from the source — Hybrid zone]
```

For content-rich sources with multiple distinct insights, multiple pairs are allowed:

```markdown
## 💡 關鍵洞察（Key Insight）
- 📌 原文洞察: [insight 1 extraction]
- 💡 延伸洞察: [insight 1 synthesis]

- 📌 原文洞察: [insight 2 extraction]
- 💡 延伸洞察: [insight 2 synthesis]
```

### Zone Classification (Hybrid)

Key Insight introduces a new zone classification:

| Sub-bullet | Zone | Rule |
|---|---|---|
| 📌 原文洞察 | Zone 1 (Extraction) | Zero Hallucination. Must be directly stated or strongly implied in source. |
| 💡 延伸洞察 | Hybrid | Must originate from the source's argument. Agent may sharpen/reframe into a more universal, transferable principle. No external knowledge. |

The Hybrid zone is explicitly different from Zone 2 (Synthesis in Layers 4–7), which allows inference based on `data/goals.md` and personal context. 💡 延伸洞察 is source-bound — it reframes the source's own argument, not the reader's personal context.

### Low-Signal Source Handling

For short Threads posts, teaser newsletters, or content too thin to extract a distinct insight:

```markdown
## 💡 關鍵洞察（Key Insight）
- 同核心總結，原文資訊不足以提煉獨立洞察
```

The `💡` sub-bullet is skipped. The section heading remains present for grep-ability.

### Quality Rule Addition to summarise.md

Add the following to the 7 Layers of Learning section:

> **核心總結 vs 關鍵洞察的區分**：
> - 核心總結 = 「這篇在講什麼」（What）— 忠實於來源的主題概括
> - 關鍵洞察 = 「這篇最值得帶走的原則」（So What）— 可脫離原文獨立成立的、可遷移的觀點
> - 📌 原文洞察必須是 Zone 1（零幻覺），直接來自來源
> - 💡 延伸洞察可將原文的隱含論點提煉為顯性命題，但不引入外部知識或個人脈絡
> - 低訊號來源允許折疊：`同核心總結，原文資訊不足以提煉獨立洞察`

### File Changes

```
content-summary/
└── references/
    ├── output_template.md                  [MODIFY] insert Key Insight section (lines 19–20)
    └── summarise.md                        [MODIFY] add differentiation rule + zone classification
```

No changes to:
- `ai_analysis.md` — Key Insight is a report section, not a suggestion field
- `suggestion_log.md` — unrelated
- `filename_rules.md` — unrelated
- `SKILL.md` — reference table descriptions remain accurate
- Any ingest skill — all read the shared template dynamically
- `daily-distiller` — reads full reports; Key Insight section improves signal density automatically

### Downstream Compatibility

| Consumer | Impact | Action |
|---|---|---|
| `daily-distiller` | Richer input. Can scan `## 💡` headings for pre-distilled principles. | None now. Observe 2–3 runs, then optionally tune to prioritise Key Insight headings. |
| `review-suggestions` | No change. Reads `suggestions_pending.md`. | None. |
| Old reports | Won't have the section. Mixed format in `reports/`. | None. No backfill. |

## Drawbacks

- **Potential redundancy with Core Idea**: For simple content, the "So What" may feel like a rephrasing of the "What". Mitigated by the explicit differentiation rule and the low-signal collapse mechanism.

- **Uncapped cardinality**: Multiple insight pairs could make the section long for content-rich sources. Mitigated by the natural constraint that each pair must be genuinely distinct (not just a different framing of the same point).

- **Hybrid zone adds a third zone concept**: The existing two-zone rule (Extraction / Synthesis) now has a third classification (Hybrid). Mitigated by limiting it to a single section; the boundary is clear and does not affect other sections.

## Alternatives Considered

### Alternative 1: Embed Key Insight as a bullet inside Core Idea

```markdown
## 📝 核心總結（Core Idea）
- [1–3 句話精準概括主旨]
- 💡 **關鍵洞察**: [一句話]
```

**Rejected**: Easily overlooked. Not grep-able by heading. Blurs the What/So-What boundary. Daily distiller cannot selectively extract it.

### Alternative 2: Callout box (TL;DR style)

```markdown
> [!TIP]
> 💡 **Key Insight**: [一句話]
```

**Rejected**: Breaks the existing `##` heading hierarchy. Not a proper section — harder to parse programmatically. Visually disconnected from the report body.

### Alternative 3: Single pair only (hard cap at 1)

Force the agent to pick the single most important insight per report.

**Rejected by user**: Key Highlights captures categorised facts; Key Insight captures distilled principles. They serve different purposes even when there are multiple insights. The constraint of selectivity is already enforced by the "must be genuinely distinct" quality rule.

### Alternative 4: Soft cap at 3 pairs

Allow up to 3 pairs to balance selectivity with richness.

**Rejected by user**: Artificial caps force the agent to make arbitrary cuts. The natural quality bar ("must be a genuinely distinct, transferable principle") provides sufficient selectivity without a numeric limit.

### Alternative 5: Pure extraction only (Zone 1)

Key Insight must be a verbatim or near-verbatim quote from the source.

**Rejected**: Too narrow. The value of Key Insight is precisely in sharpening the source's implicit argument into an explicit, transferable principle. A pure quote often lacks the reframing that makes it memorable.

### Alternative 6: Pure synthesis only (Zone 2)

Key Insight is fully the agent's inference, like Layers 4–7.

**Rejected**: Loses transparency. The user wants to see which part is from the source and which is the agent's interpretation. The Hybrid approach with provenance markers achieves this.

## Unresolved Questions

None. All design decisions resolved during grilling session (6 decisions, see ADRs below).

## Implementation Plan

1. Modify `references/output_template.md` — insert `## 💡 關鍵洞察（Key Insight）` section with format template.
2. Modify `references/summarise.md` — add differentiation rule, zone classification, and low-signal handling.
3. Verify: process one existing content URL with updated template, confirm output contains `## 💡 關鍵洞察` with both sub-bullets.
4. Verify: confirm the insight's `📌` line is source-faithful and `💡` line is a transferable principle.

---

# ADR-001: Key Insight Zone Classification (Hybrid)

## Status

Proposed — 2026-06-05

## Context

The content-summary pipeline uses a two-zone quality rule:
- **Zone 1 (Extraction)**: Zero hallucination. Core Idea, Key Highlights, Layers 2–3.
- **Zone 2 (Synthesis)**: Grounded inference using `data/goals.md`. Layers 4–7.

Key Insight doesn't fit neatly into either zone. The 📌 原文洞察 sub-bullet is pure extraction (Zone 1), but the 💡 延伸洞察 sub-bullet needs to sharpen the source's argument into a transferable principle — which is inference, but *source-bound* inference without personal context.

## Decision Drivers

- User wants to see transparent provenance: what's from the source vs what's the agent's reframing.
- 💡 延伸洞察 must not introduce external knowledge or personal goals (unlike Zone 2).
- The reframing must add value beyond verbatim extraction (unlike Zone 1).

## Decision

Introduce a **Hybrid** zone classification for 💡 延伸洞察 only:
- Must originate from the source's own argument
- Agent may sharpen, reframe, or universalise the argument
- No external knowledge, no `data/goals.md` context
- Provenance is transparent via the `📌`/`💡` sub-bullet split

## Consequences

### Positive
- Clean separation of source-fact from agent-interpretation within a single section
- Reader can evaluate the agent's reasoning by comparing `📌` (evidence) with `💡` (conclusion)
- Does not pollute the existing two-zone rule — Hybrid is scoped to one section only

### Negative
- A third zone classification adds complexity to `summarise.md`
- Agent must understand the distinction between Hybrid (source-bound reframing) and Zone 2 (goal-calibrated inference)

---

# ADR-002: Key Insight Format (Dual Sub-Bullet with Provenance Markers)

## Status

Proposed — 2026-06-05

## Context

The user wants Key Insight to surface both what the source says (extraction) and the deeper principle (synthesis), with clear visual marking of which is which.

## Considered Options

### Option 1: Single line with provenance tag at the end
```
- 所有 Agent 都是 while loop，架構思考比 throughput 更重要。（原文提及 while loop；「架構 > throughput」為綜合推論）
```

### Option 2: Two sub-bullets with emoji markers (selected)
```
- 📌 原文洞察: [extraction]
- 💡 延伸洞察: [synthesis]
```

### Option 3: Two sub-bullets, synthesis first
```
- 💡 [synthesis principle]
- 📌 來源依據: [supporting extraction]
```

## Decision

**Option 2**: Two sub-bullets, extraction first (`📌`), then synthesis (`💡`).

## Rationale

- Extraction-first grounds the reader in source facts before presenting the agent's reframing
- Emoji markers make provenance instantly scannable without reading the text
- Two separate lines enable grep/parsing (e.g., `grep "💡 延伸洞察"` extracts all synthesised principles)
- Clean separation avoids the visual clutter of inline parenthetical provenance tags (Option 1)

## Consequences

### Positive
- Each insight is self-documenting: evidence + conclusion in one visual unit
- Daily distiller can extract `💡` lines as a high-density principle feed

### Negative
- Two lines per insight instead of one — doubles the vertical space per insight
- For low-signal content, the extraction line may feel redundant with Core Idea

---

# ADR-003: Key Insight Placement (Standalone Section Between Core Idea and Key Highlights)

## Status

Proposed — 2026-06-05

## Context

Key Insight needs a home in the report template. Three structural options were evaluated.

## Considered Options

| Option | Location | Heading level |
|---|---|---|
| A: Standalone section | Between Core Idea and Key Highlights | `##` |
| B: Embedded in Core Idea | As a sub-bullet inside `📝 核心總結` | N/A (bullet) |
| C: Callout box | After metadata, before Core Idea | `> [!TIP]` |

## Decision

**Option A**: Standalone `## 💡 關鍵洞察（Key Insight）` between Core Idea and Key Highlights.

## Rationale

- `##` heading is grep-able — daily distiller can scan `## 💡` across all reports
- Natural reading flow: What (Core Idea) → So What (Key Insight) → Details (Key Highlights) → Analysis (Deep Analysis)
- Does not break existing heading hierarchy
- Consistent with the existing `##` pattern for all major report sections

## Consequences

### Positive
- Visually prominent — reader can spot it immediately when scanning
- Structurally consistent with existing report sections
- Grep-friendly for downstream consumers

### Negative
- Adds one more `##` section to the report (7 top-level sections instead of 6)
- For low-signal content that collapses to `同核心總結`, the section occupies space for minimal value

---

# ADR-004: Key Insight Cardinality (Uncapped)

## Status

Proposed — 2026-06-05

## Context

Content-rich sources (e.g., 60-minute YouTube videos, dense academic papers) may contain multiple genuinely distinct transferable principles. Should Key Insight be capped?

## Considered Options

| Option | Cap | Constraint mechanism |
|---|---|---|
| Hard cap at 1 | 1 pair | Forces selection of single most important insight |
| Soft cap at 3 | ≤3 pairs | Preserves selectivity while allowing rich content |
| Uncapped | No limit | Natural quality bar provides sufficient selectivity |

## Decision

**Uncapped** — as many `📌`/`💡` pairs as the content warrants.

## Rationale

- Key Insight captures *distilled principles*; Key Highlights captures *categorised facts*. These are structurally different even when both are numerous.
- The quality bar ("must be a genuinely distinct, transferable principle that can stand independent of the source") is a stronger filter than an arbitrary numeric cap.
- Artificial caps force the agent to make arbitrary cuts among equally important principles, reducing information value.

## Consequences

### Positive
- Content-rich sources get full principle extraction without arbitrary truncation
- No need for the agent to rank principles against each other (which is subjective and error-prone)

### Negative
- Risk of section bloat for very rich sources — but mitigated by the "genuinely distinct" quality bar
- May create visual overlap with Key Highlights for sources where facts and principles are closely coupled

---

# ADR-005: Low-Signal Source Handling (Collapsible Section)

## Status

Proposed — 2026-06-05

## Context

Some sources are too thin (2–3 sentence Threads posts, teaser newsletters) to extract a Key Insight that differs meaningfully from Core Idea. The agent should not be forced to hallucinate a distinction.

## Considered Options

| Option | Behaviour |
|---|---|
| Always require both sub-bullets | Force the agent to find something, even for thin content |
| Allow collapse | Write `同核心總結，原文資訊不足以提煉獨立洞察`, skip `💡` |
| Omit entire section | Remove `## 💡` heading entirely for low-signal content |

## Decision

**Allow collapse**: Keep the heading, write the collapse marker, skip the `💡` sub-bullet.

## Rationale

- Heading remains present → grep-able → daily distiller can still scan all reports uniformly
- Avoids forcing hallucination on thin content
- The collapse marker is honest and transparent: the reader knows the source was too thin, not that the agent failed

## Consequences

### Positive
- Zero hallucination risk for thin content
- Consistent section structure across all reports (heading always present)
- Clear signal to the reader about source depth

### Negative
- A collapsed section occupies 2 lines for minimal value — acceptable overhead

---

# ADR-006: Daily Distiller Changes (Deferred)

## Status

Proposed — 2026-06-05

## Context

The daily distiller reads all reports and synthesizes them into knowledge pillars. With Key Insight now in reports, the distiller has access to pre-distilled principles (`💡 延伸洞察`). Should the distiller be updated to explicitly prioritise these?

## Considered Options

| Option | Change |
|---|---|
| Update distiller | Modify distiller instructions to scan `## 💡` and use insights as primary pillar input |
| No change | Distiller reads full reports as before; richer content improves output naturally |
| Defer | Ship Key Insight first, observe 2–3 distillation runs, then decide |

## Decision

**Defer** — ship the template change first, observe quality over 2–3 daily runs, then decide if the distiller needs explicit tuning.

## Rationale

- The distiller's instruction is "Read every report file in full" — it will naturally ingest Key Insight sections
- Premature optimisation of the distiller risks coupling it to a section format that may evolve
- Observation-first approach lets us measure whether the distiller's synthesis quality improves passively before investing in explicit changes

## Consequences

### Positive
- Minimal blast radius — only content-summary template changes, no distiller risk
- Evidence-based tuning if/when distiller changes are needed

### Negative
- Distiller may underweight Key Insight initially since it's not explicitly told to prioritise it
- 2–3 day observation period before potential improvement
