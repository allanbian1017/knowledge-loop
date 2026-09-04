# RFC: Introduce Report Quality Grader to Content-Summary Pipeline

## Summary

Introduce a report quality grading step that evaluates the report body (Core Idea, Key Insight, 7 Layers) against a 3-dimension rubric (Depth, Adoptability, Standalone Clarity), automatically detecting shallow summaries and regenerating them with targeted feedback — raising the floor on report quality without manual re-reading.

## Status

**Proposed** — 2026-07-17

## Motivation

The 7-layer report template ([content-summary-7-layers-of-learning.md](content-summary-7-layers-of-learning.md)) and Key Insight section ([content-summary-key-insight.md](content-summary-key-insight.md)) define *what* a good report contains. But there is no enforcement mechanism — the pipeline generates reports and moves on, regardless of quality. The existing `rubric-grader` skill ([rubric-grader.md](rubric-grader.md)) grades AI-generated *suggestions*, not the report body itself.

Concrete example from the 7-layers RFC Before/After:

**Shallow report (D=0, Ad=0):**
```markdown
## 📝 核心總結（Core Idea）
- 朱騏介紹一魚多吃內容策略，將長文提取金句製作圖卡。

## 🚀 行動呼籲 / 延伸思考
- 考慮在目前的 AI 工作流中增加「內容再生」環節。
```

This passes every structural check — headings present, content exists — but the Core Idea is surface-level description and the action item is vague. The user reads this and gains nothing lasting.

**Deep report (D=2, Ad=2):**
```markdown
## 📝 核心總結（Core Idea）
- 同一份內容的價值不在於內容本身，而在於它被多少不同受眾消費。
  將長文拆解為獨立圖卡，以零邊際成本觸及完全不同的讀者群。

### 5️⃣ 可行動性（Actionability）
- 本週可嘗試：在 daily-distiller 輸出中加入
  「📌 今日金句（Top 3 Quotes）」區塊，自動從各報告提取最具分享性的句子。
```

The difference is not structural — it's analytical depth. A quality gate must evaluate *content quality*, not just format compliance.

## Detailed Design

### Architecture Overview

The report quality grader runs as a **subagent** (separate context window) spawned by the main ingest agent after report generation. This avoids self-grading bias — the grader evaluates the report without the generator's context polluting its judgment.

```
Main Agent (ingest skill)
  │
  ├─ 1. Generate report → write to file
  ├─ 2. Spawn grader subagent → "Grade report at {path}"
  ├─ 3. Wait for subagent response (score + per-dimension feedback)
  ├─ 4. If score ≥ 4 → append quality badge to report metadata → done
  └─ 5. If score < 4 → regenerate with feedback → append badge with ♻️ → done (no re-grade)
```

Key architectural difference from suggestion `rubric-grader`: this uses a **subagent** (separate context window), not inline self-grading. The suggestion grader chose inline self-grading for zero token cost; the report grader justifies the extra cost because:
- Reports are the primary user-facing artefact (not intermediate suggestions)
- The generator has a long context from source processing that biases self-evaluation
- Subagent grading enables retry without gaming risk

### Rubric Definition

**3 dimensions**, each scored 0 / 1 / 2. Maximum composite score: 6.

#### Dimension 1: Depth (D) — "Can I understand what this is actually about?"

| Score | Label | Criteria |
|---|---|---|
| 0 | Shallow | Core Idea is surface-level description. Key Insight 📌 is generic restatement. Layers 2–3 state conclusions without causality. |
| 1 | Adequate | Core Idea identifies thesis/principle. Key Insight 📌 cites specific non-obvious fact. Layers 2–3 explain at least one mechanism. |
| 2 | Deep | Core Idea articulates principle + why it matters. Key Insight 💡 formulates genuinely transferable principle. Layers 2–3 explain causality, constraints, what breaks model. |

**Examples:**
- ❌ D=0: "朱騏介紹一魚多吃內容策略，將長文提取金句製作圖卡。"
- ✅ D=2: "同一份內容的價值不在於內容本身，而在於它被多少不同受眾消費。將長文拆解為獨立圖卡，以零邊際成本觸及完全不同的讀者群。"

#### Dimension 2: Adoptability (Ad) — "Can I do something concrete with this?"

| Score | Label | Criteria |
|---|---|---|
| 0 | Vague | Layer 5 uses banned phrases ("研究看看"). Layer 4 is generic ("與目標相關"). |
| 1 | Actionable | Layer 5 names specific action + target. Layer 4 connects to specific goal. |
| 2 | Ready-to-Execute | Layer 5 has action + target + time estimate. Layer 4 identifies exact goal + intersection. Layer 6 proposes concrete new idea. |

**Examples:**
- ❌ Ad=0: "考慮在目前的 AI 工作流中增加「內容再生」環節。"
- ✅ Ad=2: "本週可嘗試：在 daily-distiller 輸出中加入「📌 今日金句（Top 3 Quotes）」區塊（30 分鐘內）。"

#### Dimension 3: Standalone Clarity (S) — "Can I understand this without reading the original?"

| Score | Label | Criteria |
|---|---|---|
| 0 | Opaque | Unexplained jargon, unnamed concepts, requires source context. |
| 1 | Clear | Core Idea + Key Highlights cover main argument. Technical terms contextualised. |
| 2 | Self-Contained | Full narrative arc (What → So What → Details → Why → What To Do). Reader with no context can understand, evaluate, and act. |

### Thin Source Handling

Sources with limited content (short Threads posts, teaser newsletters) should not be penalised for brevity. The grader judges **source richness** — no arbitrary character thresholds. A report that faithfully extracts all available signal from a thin source scores D≥1. The quality gate catches shallow *analysis*, not shallow *sources*.

### Grading Target

The grader evaluates the **whole report as a unit**, not per-section. Sections interact — a strong Key Insight can compensate for terse Layers. Per-section scoring would miss these cross-section dependencies and add complexity without proportional benefit.

### Feedback Format

The grader returns:
- Per-dimension score (0–2) with reason
- Composite score (0–6)
- No example rewrite — reasons are sufficient for the generator to improve

Example grader response:
```
D: 0 — Core Idea restates the title. No principle identified.
Ad: 1 — Layer 5 names action but no time estimate.
S: 1 — Technical terms explained, but Layer 4 is too vague to evaluate without source.
Total: 2/6 — FAIL
```

### Quality Gate Flow

The quality gate logic is documented in a shared reference file (`quality_gate.md`) that all ingest skills read. Each ingest skill adds a single `📄 Read` line pointing to this reference, keeping the gate definition in one place.

**Pass flow (score ≥ 4):**
1. Grader returns score + feedback
2. Main agent appends quality badge to report's `🔖 來源 Metadata` section:
   ```
   - 📊 Quality: 5/6 (D:2 Ad:1 S:2)
   ```
3. Done — proceed to AI analysis

**Fail flow (score < 4):**
1. Grader returns score + per-dimension feedback
2. Main agent regenerates the **full report** with feedback injected into prompt
3. Main agent appends quality badge with retry marker:
   ```
   - 📊 Quality: 5/6 (D:2 Ad:2 S:1) ♻️ retried
   ```
4. Done — no re-grade after retry (max 1 retry)

### Pass/Fail Threshold

Start at **≥ 4/6**. Calibrate after 20 graded reports using the same data-driven approach as the suggestion rubric. If ≥80% of reports pass on first attempt, the threshold is well-set. If pass rate is too low or too high, adjust.

### Score Persistence

The quality badge is appended to the report's `🔖 來源 Metadata` section — the natural home for report-level metadata. Format:

```markdown
## 🔖 來源 Metadata
- 📊 Quality: {total}/6 (D:{n} Ad:{n} S:{n})
```

If retried:
```markdown
- 📊 Quality: {total}/6 (D:{n} Ad:{n} S:{n}) ♻️ retried
```

### File Changes

| File | Action | What changes |
|---|---|---|
| `.agents/skills/rubric-grader/references/report_rubric.md` | **NEW** | 3 dimension definitions with scoring criteria and examples |
| `.agents/skills/content-summary/references/quality_gate.md` | **NEW** | Subagent grading flow instructions |
| `.agents/skills/rubric-grader/SKILL.md` | MODIFY | Add Mode 4: Report Quality |
| `.agents/skills/content-summary/SKILL.md` | MODIFY | Add `quality_gate.md` to reference table |
| `.agents/skills/ingest-newsletter/SKILL.md` | MODIFY | Add quality gate step between report writing and AI analysis |
| `.agents/skills/ingest-threads/SKILL.md` | MODIFY | Same |
| `.agents/skills/ingest-youtube/SKILL.md` | MODIFY | Same |
| `.agents/skills/ingest-website/SKILL.md` | MODIFY | Same |

### Downstream Compatibility

| Consumer | Impact | Action |
|---|---|---|
| `daily-distiller` | No impact. Reads full reports; quality badge in metadata doesn't affect synthesis. | None. |
| `review-suggestions` | No impact. Reads `suggestions_pending.md`, not report body. | None. |
| `rubric-grader` Modes 1–3 | No impact. Existing suggestion grading is unchanged. | None. |
| Old reports | No quality badge. Mixed format in `reports/`. | None. No backfill. |

## Drawbacks

- **Token cost per report increases**: Spawning a subagent grader adds a full LLM call per report. On failure, a second generation call follows. Estimated: ~50% more tokens for passing reports, ~150% more for failed reports. Mitigated: reports are the primary user artefact — quality justifies cost.

- **Pipeline latency increases**: Sequential grading adds wait time. ~9 reports/day × subagent call = noticeable delay. Mitigated: grading is faster than generation (shorter prompt, no source processing).

- **Max 1 retry may not fix deep quality issues**: Some failures stem from thin sources or inherently shallow content. A single retry with feedback may not help. Mitigated: the grader judges source richness, so thin-source reports that extract all signal still pass.

- **No batch audit mode**: Cannot retroactively grade old reports or run calibration across a corpus. Accepted: the quality gate catches issues at generation time, which is the highest-leverage point.

## Alternatives Considered

### Alternative 1: On-Demand Only (No Auto-Grading)

User manually invokes grading when they suspect a report is shallow.

**Rejected**: User reads ~9 reports/day. Manual invocation adds friction and is easily forgotten. The goal is to raise the quality floor automatically, not add a manual review step.

### Alternative 2: Post-Generation Badge, No Retry

Grade every report and append a quality badge, but never retry — just inform the user of the score.

**Rejected**: A badge without corrective action is observability without improvement. If the pipeline can detect a shallow report, it should fix it. The retry mechanism is cheap (one regeneration) and high-impact (transforms a shallow report into a useful one).

### Alternative 3: Self-Grading Retry (No Subagent)

The same LLM call that generates the report also grades it and retries inline.

**Rejected**: Self-grading bias is well-documented in the existing rubric-grader RFC. The generator has a long context from source processing that anchors its judgment. A separate context window (subagent) provides independent evaluation. The suggestion rubric chose inline grading for zero cost; reports justify the extra cost because they are the primary user artefact.

### Alternative 4: Per-Section Scoring

Score each report section independently (Core Idea: 0–2, Layer 2: 0–2, etc.) instead of whole-report scoring.

**Rejected**: Sections interact. A strong Key Insight can compensate for terse Layer 3. Per-section scoring misses these cross-dependencies, inflates the rubric to 10+ dimensions, and makes the composite score harder to interpret. Three whole-report dimensions (Depth, Adoptability, Clarity) capture the user's actual quality concerns.

### Alternative 5: Batch Audit Mode

Add a mode to retroactively grade all reports in `reports/` for calibration and quality tracking.

**Rejected**: The highest-leverage quality intervention is at generation time. Batch auditing old reports provides calibration data but doesn't improve the reports themselves (no retroactive regeneration). The 20-report calibration window provides sufficient data for threshold tuning without a dedicated batch mode.

## Unresolved Questions

None. All 9 design decisions resolved during grilling session (see ADRs below).

## Implementation Plan

1. Create `references/report_rubric.md` — 3 dimension definitions with scoring criteria and examples.
2. Create `references/quality_gate.md` — subagent grading flow instructions.
3. Modify `rubric-grader/SKILL.md` — add Mode 4: Report Quality.
4. Modify `content-summary/SKILL.md` — add `quality_gate.md` to reference table.
5. Modify all 4 ingest skill `SKILL.md` files — add quality gate step.
6. Verify: process one newsletter with quality gate enabled, confirm grader subagent runs and badge appears in report metadata.
7. Verify: process a known-shallow source, confirm retry triggers and `♻️ retried` marker appears.
8. Calibrate: after 20 graded reports, review pass/fail distribution and adjust threshold if needed.

## References

- [7 Layers RFC](content-summary-7-layers-of-learning.md) — report template that this grader evaluates
- [Key Insight RFC](content-summary-key-insight.md) — Key Insight section evaluated by Depth dimension
- [Rubric Grader RFC](rubric-grader.md) — existing suggestion grading; Mode 4 extends this skill

---

# ADR-001: Grading Target (Whole Report vs Per-Section)

## Status

Proposed — 2026-07-17

## Context

The report contains multiple sections (Core Idea, Key Insight, Key Highlights, Layers 2–7). The grader needs to decide its unit of evaluation: should it score each section independently or evaluate the whole report holistically?

## Decision Drivers

- Sections are interdependent — a strong Key Insight can compensate for terse Layer 3
- The user's quality concern is "is this report useful?" not "is Layer 5 adequate?"
- More scoring dimensions = more noise in LLM-based evaluation

## Considered Options

| Option | Unit | Dimensions | Composite |
|---|---|---|---|
| Whole report | 1 report = 1 evaluation | 3 (D, Ad, S) | 0–6 |
| Per-section | Each section scored independently | 10+ (one per section) | 0–20+ |
| Hybrid | Score clusters (extraction zone, synthesis zone) | 6 (3 per zone) | 0–12 |

## Decision

**Whole report as a unit** — 3 dimensions (Depth, Adoptability, Standalone Clarity) evaluated holistically across all sections.

## Rationale

- Cross-section dependencies are real: Key Insight depth informs Layer 2–3 quality; Layer 4–5 concreteness depends on Layer 1 clarity.
- Three dimensions map directly to the user's reading experience: "Do I understand it?", "Can I act on it?", "Does it stand alone?"
- Simpler rubrics produce more consistent LLM evaluations (fewer dimensions = less noise).

## Consequences

### Positive
- Clean, interpretable composite score (0–6)
- Grader prompt is concise — reads one report, returns 3 scores + reasons
- Same 0–6 scale as suggestion rubric — familiar mental model

### Negative
- Cannot pinpoint exactly which section caused a low score (mitigated by per-dimension reasons citing specific sections)
- A report with one excellent section and several poor ones may score "adequate" overall

---

# ADR-002: Architecture (Subagent Grader with Max 1 Retry)

## Status

Proposed — 2026-07-17

## Context

The existing suggestion `rubric-grader` uses inline self-grading (same LLM call generates and grades) because it was optimised for zero additional token cost. For report quality grading, the architecture choice is more consequential:

- Reports are the primary user-facing artefact (~9/day, directly read)
- The generator's context is long (full source content) and anchors its self-evaluation
- The [rubric-grader RFC](rubric-grader.md) explicitly documented subagent grading as a future upgrade path

## Decision Drivers

- Avoid self-grading bias (generator evaluating its own work)
- Enable retry without gaming risk (separate evaluator can't be gamed by the generator)
- Acceptable token cost for the primary user artefact

## Considered Options

| Option | Architecture | Token cost | Bias risk |
|---|---|---|---|
| Inline self-grading | Same LLM call | Zero | High — generator biased by its own context |
| Subagent grader, no retry | Separate context window | +1 call/report | Low |
| Subagent grader, max 1 retry | Separate context window | +1–2 calls/report | Low |
| Subagent grader, unlimited retry | Separate context window | +N calls/report | Low but wasteful |

## Decision

**Subagent grader (separate context window) with max 1 retry if score < threshold.**

## Rationale

- Separate context window eliminates self-grading bias — the grader reads only the report file, not the source
- Max 1 retry balances improvement opportunity with cost control — diminishing returns after first retry
- The retry injects per-dimension feedback into the regeneration prompt, giving the generator specific guidance

## Consequences

### Positive
- Independent evaluation free from generator context bias
- Retry mechanism can recover shallow reports — most quality issues are fixable with targeted feedback
- Max 1 retry bounds worst-case cost at 2× (generation + retry)

### Negative
- Token cost: +50% per report (pass) to +150% (fail + retry)
- Pipeline latency: sequential subagent call adds wait time
- No re-grade after retry — must trust that feedback-informed regeneration improves quality

---

# ADR-003: Thin Source Handling (Grader Judges Source Richness)

## Status

Proposed — 2026-07-17

## Context

Some sources are inherently thin — short Threads posts, teaser newsletters, brief announcements. A rigid quality threshold would fail reports that faithfully extract all available signal from thin content. Two approaches:

1. Pre-filter by source length (e.g., skip grading for sources < 500 characters)
2. Let the grader assess source richness as part of its evaluation

## Decision Drivers

- Source length is a poor proxy for content richness (a 200-character insight can be deep)
- The user does not want arbitrary character thresholds
- The grader already reads the full report — it can assess whether the analysis matches the source's depth

## Considered Options

| Option | Mechanism | Risk |
|---|---|---|
| Character threshold | Skip grading if source < N chars | Misses short-but-deep sources; arbitrary cutoff |
| Source type whitelist | Only grade newsletters/YouTube, skip Threads | Misses shallow long-form; penalises good Threads |
| Grader judges richness | Grader evaluates whether report depth matches source depth | Relies on grader's judgment |

## Decision

**Grader judges source richness** — no arbitrary character thresholds. Reports that faithfully extract all signal from thin sources score D≥1.

## Rationale

- Character count and source type are poor proxies for content richness. A 3-sentence Threads post can contain a transferable principle worth D=2.
- The grader reads the full report and can assess whether the analysis is shallow *relative to the available source material*.
- D=0 is reserved for reports that are shallow despite having rich source material.

## Consequences

### Positive
- No arbitrary thresholds to maintain or calibrate
- Thin-source reports are not penalised for brevity — only for missing available signal
- Consistent grading logic regardless of source type

### Negative
- Relies on grader's subjective assessment of "source richness" — may be inconsistent
- No deterministic shortcut — every report goes through the full grading flow

---

# ADR-004: Regeneration Scope (Full Report with Per-Dimension Feedback)

## Status

Proposed — 2026-07-17

## Context

When a report fails the quality gate, the pipeline must decide how to regenerate it. Options range from patching specific sections to full regeneration.

## Decision Drivers

- Report sections are interdependent — a deeper Core Idea changes the tone of all downstream layers
- Per-dimension feedback identifies specific weaknesses (e.g., "Layer 5 lacks time estimate")
- Partial regeneration requires complex diffing and merging logic

## Considered Options

| Option | Scope | Complexity |
|---|---|---|
| Patch specific sections | Only rewrite sections cited in feedback | High — requires section-level diffing |
| Full regeneration, no feedback | Regenerate entire report from scratch | Low — but may repeat same mistakes |
| Full regeneration with feedback | Regenerate entire report, inject grader feedback | Medium — feedback guides improvement |

## Decision

**Full report regeneration with grader's per-dimension feedback injected into prompt.**

## Rationale

- Full regeneration avoids section-level diffing complexity — the generator produces a complete replacement
- Injected feedback provides specific, actionable guidance (e.g., "D:0 — Core Idea restates title, identify the underlying principle")
- Sections are coupled: a deeper Core Idea naturally improves downstream layers — partial patching would miss these cascading improvements

## Consequences

### Positive
- Simple implementation — regenerate with additional prompt context
- Feedback-guided regeneration addresses specific weaknesses, not just "try again"
- Cross-section improvements cascade naturally

### Negative
- Full regeneration is more expensive than section patching (~2× tokens)
- Good sections may change — but the goal is a coherent whole, not preserving individual sections

---

# ADR-005: Pass/Fail Threshold (Start at ≥4/6, Data-Driven Calibration)

## Status

Proposed — 2026-07-17

## Context

The composite score ranges 0–6. A threshold must be set to determine pass/fail. Too low: shallow reports slip through. Too high: most reports fail and retry, wasting tokens.

## Decision Drivers

- Same scale (0–6) as suggestion rubric — threshold should be comparable
- No historical data for report quality scores — must calibrate empirically
- The suggestion rubric started at ≥4/6 and proved well-calibrated

## Considered Options

| Option | Threshold | Expected pass rate |
|---|---|---|
| ≥3/6 (lenient) | Each dimension averages 1 | Very high — almost everything passes |
| ≥4/6 (moderate) | At least one dimension at 2, or all at ≥1 with one at 2 | Moderate — matches suggestion rubric |
| ≥5/6 (strict) | Most dimensions at 2 | Low — frequent retries |

## Decision

**Start at ≥4/6. Calibrate after 20 graded reports** using the same data-driven approach as the suggestion rubric.

## Rationale

- ≥4/6 means each dimension must average ≥1.33 — no dimension can be 0 if the others aren't both at 2. This effectively bans "Shallow" (D=0), "Vague" (Ad=0), and "Opaque" (S=0) from passing unless other dimensions are exceptional.
- The suggestion rubric's ≥4/6 threshold proved well-calibrated — same logic applies.
- 20 reports provides sufficient data for initial calibration (~2 days at 9 reports/day).

## Consequences

### Positive
- Consistent with suggestion rubric — same mental model for the user
- Data-driven calibration avoids premature commitment to an arbitrary threshold
- 20-report window is short enough to adjust quickly

### Negative
- First 20 reports use an unvalidated threshold — some may be incorrectly passed or failed
- Calibration requires manual review of pass/fail decisions

---

# ADR-006: Integration Point (Shared quality_gate.md with Per-Skill Read Line)

## Status

Proposed — 2026-07-17

## Context

Four ingest skills (newsletter, threads, youtube, website) need to invoke the quality gate. The gate logic (subagent spawning, score parsing, badge appending, retry flow) must be defined once and referenced consistently.

## Decision Drivers

- DRY: gate logic defined once, not copied into 4 skill files
- Consistency: all ingest skills use identical grading flow
- Minimal coupling: ingest skills should not need to understand rubric internals

## Considered Options

| Option | Where gate logic lives | Ingest skill change |
|---|---|---|
| Inline in each SKILL.md | Duplicated in 4 files | 15+ lines each |
| Shared reference file | `content-summary/references/quality_gate.md` | 1 `📄 Read` line each |
| In rubric-grader SKILL.md only | Ingest skill says "use rubric-grader" | 1 line, but gate flow unclear |

## Decision

**Shared `quality_gate.md`** in `content-summary/references/`, with one `📄 Read` line per ingest skill.

## Rationale

- Single source of truth for the grading flow — update one file, all skills follow
- The `📄 Read` pattern is already established in the project (e.g., `ai_analysis.md`, `summarise.md`)
- Ingest skills remain lean — they delegate gate details to the reference file
- Distinct from `rubric-grader/SKILL.md` which defines *how to grade*; `quality_gate.md` defines *when and how to invoke grading*

## Consequences

### Positive
- Gate logic changes require editing one file, not four
- Consistent behaviour across all source types
- Ingest skills stay focused on their source-specific processing

### Negative
- One more reference file to read per ingestion — marginal token cost
- Indirection: debugging requires following the `📄 Read` chain to `quality_gate.md`

---

# ADR-007: Feedback Format (Scores + Per-Dimension Reason, No Example Rewrite)

## Status

Proposed — 2026-07-17

## Context

When the grader returns feedback for a failing report, the format determines how effectively the generator can improve on retry. Three levels of detail were considered.

## Decision Drivers

- The generator needs actionable guidance, not just a number
- Example rewrites risk the grader imposing its own style on the report
- Token cost of feedback affects the retry prompt length

## Considered Options

| Option | Content | Token cost |
|---|---|---|
| Score only | `2/6` | Minimal — but no actionable guidance |
| Score + per-dimension reason | `D:0 — Core Idea restates title` | Moderate — specific and actionable |
| Score + reason + example rewrite | `D:0 — … Example: "The principle is…"` | High — grader writes partial report |

## Decision

**Scores + per-dimension reason (no example rewrite).**

## Rationale

- Per-dimension reasons give the generator specific, targeted feedback (e.g., "Layer 5 lacks time estimate") without constraining its creative approach
- Example rewrites risk the grader imposing its phrasing on the generator — the generator should find its own expression
- Moderate token cost keeps the retry prompt concise — the generator already has the source context

## Consequences

### Positive
- Actionable feedback without over-constraining the generator
- Concise format keeps retry prompt manageable
- Reasons are human-readable — user can inspect badge + reason in reports

### Negative
- Generator may misinterpret abstract feedback (e.g., "add causality") — but per-dimension specificity reduces this risk
- No concrete example to anchor improvement — the generator must infer what "deeper" means from the criteria

---

# ADR-008: Batch Audit Mode (Rejected)

## Status

Proposed — 2026-07-17

## Context

A batch audit mode would allow retroactive grading of all reports in `reports/` for calibration, quality tracking, and identifying historical patterns. The suggestion rubric-grader has a backtest mode that samples historical suggestions for threshold validation.

## Considered Options

| Option | Capability | Cost |
|---|---|---|
| Batch audit mode | Grade all historical reports, output quality distribution | High — N × subagent calls for N reports |
| No batch mode | Auto-grade only during pipeline | Zero additional cost |

## Decision

**No batch mode** — auto-grade only during pipeline execution.

## Rationale

- The highest-leverage quality intervention is at generation time — catching and fixing a shallow report before the user reads it
- Batch auditing old reports provides calibration data but doesn't improve the reports themselves (no retroactive regeneration without re-reading the source)
- The 20-report calibration window from live pipeline grading provides sufficient data for threshold tuning
- If batch auditing becomes necessary later, it can be added as a separate mode without changing the core grading flow

## Consequences

### Positive
- Simpler implementation — no batch orchestration logic
- No cost for historical reports that have already been read
- Focus on forward-looking quality improvement

### Negative
- No retroactive quality data for ~200+ existing reports
- Calibration relies on live pipeline data only — initial threshold is unvalidated
- Cannot compare quality trends over time without manual sampling

---

# ADR-009: Score Persistence (Badge in Report Metadata)

## Status

Proposed — 2026-07-17

## Context

The quality score must be persisted somewhere visible. Options include: a separate log file, inline in the report, or in the report's metadata section.

## Decision Drivers

- The score is a property of the report — it should live with the report
- The `🔖 來源 Metadata` section already contains report-level metadata (author, date, source type)
- Downstream consumers (daily-distiller) should not be affected by the badge

## Considered Options

| Option | Location | Visibility | Downstream impact |
|---|---|---|---|
| Separate log file | `data/report_scores.md` | Low — requires opening a separate file | None |
| Inline at top of report | Before `## 來源` | High — always visible | May confuse distiller |
| In metadata section | `## 🔖 來源 Metadata` | Medium — visible when reading metadata | None — distiller ignores metadata fields |

## Decision

**Badge in the report's `🔖 來源 Metadata` section.** Format: `- 📊 Quality: {total}/6 (D:{n} Ad:{n} S:{n})`. If retried: append `♻️ retried`.

## Rationale

- The metadata section is the natural home for report-level properties — quality score fits alongside source URL, author, and date
- Daily distiller reads full reports but does not parse metadata fields — no downstream impact
- The `♻️ retried` marker provides transparency: the user knows this report was regenerated
- A separate log file would require cross-referencing to find a report's score — colocation is simpler

## Consequences

### Positive
- Score is colocated with the report — no cross-referencing needed
- `♻️ retried` marker provides full transparency
- No downstream impact on distiller or review-suggestions

### Negative
- Slightly increases metadata section length (1 line)
- Old reports won't have the badge — mixed format in `reports/` (accepted: no backfill)
