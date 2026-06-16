# RFC: Introduce Rubric Grader to Suggestion Pipeline

## Summary

Introduce a `rubric-grader` skill that scores every AI-generated suggestion against a 3-dimension rubric before it enters the pending review queue, automatically filtering low-quality suggestions to raise the user's acceptance rate from ~71% to ≥80%.

## Status

**Approved** — 2026-06-11

## Motivation

The content intelligence pipeline generates ~10–15 suggestions per day from newsletters, Threads, YouTube, and website ingestion. The user must manually review each suggestion in `review-suggestions`. Current data shows significant waste:

| Metric | Value |
|---|---|
| Total reviewed | 390 |
| Rejected | 113 (29.0%) |
| Top reject reason: ambiguous/vague | 18 (16% of rejects) |
| Top reject reason: not interested | 10 (9% of rejects) |
| Bare rejects (no explanation) | 73 — of which 71% were 💎 High value by AI's own scoring |

The AI's existing quality rules are poorly enforced. `ai_analysis.md` already bans abstract suggestions ("禁止抽象描述（例如：研究看看、了解一下）"), yet 18 rejections are exactly this pattern — the generator violates its own constraint ~16% of the time.

Additionally, the three removed suggestion fields (💎 價值評分, ⚡ 可行動性, 🎯 決策建議) provide low signal:

| Removed field | Why |
|---|---|
| 💎 價值評分 (High/Mid/Low) | Redundant with rubric's Goal Relevance dimension. 71% of bare rejects were scored "High" — poorly calibrated. |
| ⚡ 可行動性 (High/Mid/Low) | Redundant with rubric's Actionability dimension. |
| 🎯 決策建議 (Action/Store/Drop) | Applied "Action" to 63% of all suggestions (no discrimination). "Store" has 42.6% reject rate (worst accuracy). Only 4/390 reviews mentioned this field. |

A rubric-based quality gate can pre-filter ~29% of rejections before they reach the user, while the three legacy fields are replaced by a single, more informative rubric score.

## Detailed Design

### Architecture Overview

```
BEFORE:
Ingest → AI Analysis → append to suggestions_pending.md (no gate) → User reviews

AFTER:
Ingest → AI Analysis → rubric-grader skill (grade mode)
                              ↓ score ≥ 4        ↓ score < 4 or hard-veto
                    suggestions_pending.md    suggestions_filtered.md
                              ↓
                    User reviews (review-suggestions)
                              ↓
                    rubric-grader skill (maintain mode)
```

### New Skill: `rubric-grader`

A 3-mode skill that owns all rubric evaluation logic:

| Mode | Trigger | What it does |
|---|---|---|
| **Grade** | Invoked by `ai_analysis.md` after suggestion generation | Score a suggestion against the rubric, apply hard-veto blocklist, pass/fail gate |
| **Backtest** | Direct invocation: "backtest the rubric" | Sample N accepted + N rejected from `suggestions_reviewed.md`, score each, output accuracy report |
| **Maintain** | Invoked by `review-suggestions` after Step 6 | (a) Scan `suggestions_reviewed.md` for 3+ rejection patterns → update `data/rubric_blocklist.md`. (b) Compute rubric score calibration — requires ≥30 scored+reviewed suggestions, otherwise output "collecting more data" |

### Rubric Definition

**3 active dimensions**, each scored 0 / 1 / 2:

| # | Dimension | 0 (Fail) | 1 (Pass) | 2 (Strong) |
|---|---|---|---|---|
| 1 | **Actionability** | Abstract / vague (e.g. 研究看看, 了解一下) | Action + Object specified | Action + Object + Scope + time estimate |
| 2 | **Preference Alignment** | Matches low-interest topic or neutral | Matches medium-interest topic | Matches high-interest topic + preferred action type |
| 3 | **Goal Relevance** | No connection to any goal in `goals.md` | Indirect connection | Directly advances a specific goal |

**Composite score**: 0–6. **Threshold**: ≥ 4 to pass.

**Future dimensions** (documented, not implemented):

| # | Dimension | When to add |
|---|---|---|
| 4 | **Source Grounding** — Is the suggestion grounded in source content? | If post-launch data shows suggestions passing rubric but rejected for "content doesn't match" |
| 5 | **Novelty** — Does it offer insight beyond what user already knows? | If post-launch data shows suggestions passing rubric but rejected for "already done" |

### Two-Tier Gating Logic

The rubric-grader skill applies checks in this order:

1. **Hard-veto blocklist** (`data/rubric_blocklist.md`): If the suggestion matches any blocklist pattern → **auto-fail**, append to `suggestions_filtered.md`, skip rubric scoring entirely.

2. **Deterministic ambiguity check**: If `建議下一步` contains banned phrases (研究看看, 了解一下, 評估看看, etc.) → **auto-fail**.

3. **Rubric scoring**: Score 3 dimensions. If total < 4 → fail. If total ≥ 4 → pass.

Pass → append to `suggestions_pending.md`.
Fail → append to `suggestions_filtered.md` with score and reason.

### Blocklist

`data/rubric_blocklist.md` — seeded with known hard-veto patterns, auto-maintained by the skill's maintain mode:

```markdown
# Rubric Blocklist

> Hard-veto patterns. Suggestions matching any pattern are auto-filtered.
> Auto-maintained by rubric-grader skill (maintain mode).

## Topic Blocks
- Claude Code / Cursor (user does not use these tools)
- Token budget reduction / context compression mechanisms
- GPU K-Means clustering / GPU memory IO / GPU database clustering
- Blockchain / Web3 / Crypto / NFT

## Ambiguity Blocklist
- 研究看看
- 了解一下
- 評估看看
- 觀察看看
```

### Filtered Suggestion Audit Log

`data/suggestions_filtered.md` — persistent record of all filtered suggestions for threshold calibration and false-positive detection:

```markdown
# 🚫 Filtered Suggestions

---

### YYYY-MM-DD | {SourceType} | [{Title}]({source_url})
- 📊 Rubric: {total}/6 (A:{n} P:{n} G:{n})
- 📋 建議：{建議下一步}
- ❌ Filter: {reason — e.g. "Below threshold (3 < 4)" or "Hard-veto: Claude Code"}
- 📄 [報告](file:///absolute/path/to/report.md)
```

### Updated Suggestion Entry Format

```diff
 ### YYYY-MM-DD | {SourceType} | [{Title}]({source_url})
-- 🏷️ {分類} | 💎 {價值評分} | ⚡ {可行動性} | 🎯 {決策建議}
+- 🏷️ {分類} | 📊 {total}/6 (A:{n} P:{n} G:{n})
 - 📋 建議：{建議下一步}
 - 📄 [報告](file:///absolute/path/to/report.md)
```

### Future Improvement: Retry Mechanism

> Not implemented in MVP due to self-grading gaming risk. Add when upgrading to a separate grader pass.
>
> - Retry only on **Actionability failures** (score 0) — the only failure type where rephrasing can help
> - Max **1 retry** — diminishing returns after that
> - Pass failure reason back to generator as feedback for re-generation
> - Log both original and retry in `suggestions_filtered.md` for comparison
> - **Prerequisite**: Separate grader model/prompt (not inline self-grading) to prevent the generator from gaming the rubric by superficially inflating phrasing (e.g., appending "（10 分鐘內）" to pass Actionability)

## Drawbacks

- **Self-grading bias**: Inline grading (same LLM call generates and grades) risks the model gaming its own rubric. Mitigated by the deterministic blocklist catching the most common failure mode, and the filtered audit log providing visibility. Upgrade path: separate grader pass when cost is justified.

- **Cold start for calibration**: No historical suggestions have rubric scores. Calibration requires ≥30 post-launch scored+reviewed suggestions (~2–3 weeks). Mitigated by the 30-entry minimum gate.

- **Breaking change to suggestion format**: Removing 3 fields (💎, ⚡, 🎯) changes the entry schema in `suggestions_pending.md` and `suggestions_reviewed.md`. Old reviewed entries won't have rubric scores. Mitigated: `review-suggestions` already handles mixed formats; calibration only counts entries with `📊` scores.

## Alternatives Considered

### Alternative 1: Separate grader pass (dedicated LLM call)

A second LLM call grades the suggestion independently, per Anthropic's Outcomes pattern.

**Rejected for MVP**: Doubles token cost per suggestion (~3–15 extra calls/day). The project's Anthropic Outcomes report shows this is the ideal architecture, but inline grading + deterministic blocklist provides ~80% of the value at zero extra cost. Upgrade path documented as future improvement.

### Alternative 2: Rubric as reference file only (no separate skill)

`ai_analysis.md` reads `rubric.md` as a reference, embedding all grading logic inline.

**Rejected**: Creates drift risk between ingestion mode (reads `rubric.md` only) and backtest mode (reads full `SKILL.md`). Splits orchestration logic (threshold, blocklist, filter/log routing) across `ai_analysis.md` and the rubric file. The skill approach provides single source of truth and consistent behavior across modes.

### Alternative 3: Keep all 5 dimensions from the start

Implement Source Grounding and Novelty alongside the 3 core dimensions.

**Rejected**: Source Grounding and Novelty together account for only ~4 rejections out of 113 (3.5%). More dimensions = more noise in self-grading scores = less reliable threshold. Start lean, add when data justifies.

### Alternative 4: Keep legacy fields alongside rubric scores

Keep 💎, ⚡, 🎯 in the suggestion entry and add 📊 rubric score.

**Rejected**: No logic consumes these fields. User ignores 🎯 (1% mention rate). 💎 and ⚡ are redundant with rubric dimensions. Adding without removing increases visual clutter.

## File Changes

| File | Action | What changes |
|---|---|---|
| `.agents/skills/rubric-grader/SKILL.md` | **NEW** | 3-mode skill: Grade, Backtest, Maintain |
| `.agents/skills/rubric-grader/references/rubric.md` | **NEW** | Rubric definition: 3 active + 2 future dimensions |
| `data/rubric_blocklist.md` | **NEW** | Hard-veto patterns (topic blocks + ambiguity) |
| `data/suggestions_filtered.md` | **NEW** | Audit log for filtered suggestions |
| `content-summary/references/ai_analysis.md` | MODIFY | Remove 3 fields; add rubric-grader invocation |
| `content-summary/references/suggestion_log.md` | MODIFY | New entry format (remove 💎⚡🎯, add 📊) |
| `review-suggestions/SKILL.md` | MODIFY | Update display format; remove §6-4; add maintain mode invocation |
| `review-suggestions/README.md` | MODIFY | Update format examples |
| `content-summary/README.md` | MODIFY | Document rubric integration |
| `backlog.md` | MODIFY | Update #1 and #4 status |

## References

- [Anthropic Outcomes Grader Architecture](../../../reports/Threads_2026_05_26/therobertta_Anthropic_Outcomes_Grader_Architecture.md) — Generator-Grader separation pattern, 31-criteria eval, pass rates 62% → 89%
- [Gary Chen Evaluation 4 Schools Analysis](../../../reports/Newsletter_2026_05_25/Gary_Chen_Evaluation_4_Schools_Analysis.md) — Rubric scoring, criteria drift, grader strategies
- [Session Decision Log](../decision_logs/session_5541be06-9cbc-45e0-b265-29c4f4bc66e8.md) — 12 resolved decisions from grilling session
- [Backlog #1](../../backlog.md) — LLM-as-a-Judge Evaluation & Test Harness
- [Backlog #4](../../backlog.md) — Memory Consolidation, Rubric Filtering & Preference Steerability

---

# ADR-001: Grading Architecture (Inline Self-Grading + Deterministic Blocklist)

## Status

Accepted — 2026-06-11

## Context

The suggestion pipeline needs a quality gate. Two architectures were considered: (1) a separate LLM grader pass that evaluates each suggestion independently, and (2) inline self-grading where the same LLM call generates and grades the suggestion.

The project's ingested [Anthropic Outcomes report](../../../reports/Threads_2026_05_26/therobertta_Anthropic_Outcomes_Grader_Architecture.md) explicitly warns: "When the same model generates AND evaluates, it is grading its own homework. Bias is inevitable."

However, `ai_analysis.md` already bans abstract suggestions ("禁止抽象描述"), yet 18/113 rejections are exactly this pattern — the generator violates its own constraint 16% of the time.

## Decision Drivers

- Zero additional token cost for MVP
- The #1 failure mode (ambiguous phrasing) is deterministic — detectable by string matching
- Self-grading bias is a real risk, but quantifiable via the filtered audit log

## Decision

**Hybrid approach**: Inline self-grading for the soft rubric score, plus a deterministic blocklist for the most common failure mode (ambiguous phrases and hard-vetoed topics).

## Rationale

The deterministic blocklist catches failures that the generator already should avoid but doesn't — providing a zero-cost safety net. The soft rubric handles subtler dimensions. If inline self-grading proves unreliable (measured via acceptance rate delta), upgrade to a separate grader pass.

## Consequences

### Positive
- Zero additional token cost
- Deterministic checks for the highest-impact failure mode
- Filtered audit log enables bias detection

### Negative
- Self-grading bias risk for soft rubric dimensions
- Cannot use retry mechanism (gaming risk) until separate grader is implemented

---

# ADR-002: Rubric Dimensions (3 Active, 2 Deferred)

## Status

Accepted — 2026-06-11

## Context

Five candidate dimensions were identified from user rejection patterns:

| Dimension | Rejections it catches | % of 113 rejects |
|---|---|---|
| Actionability | 18 ambiguous | 15.9% |
| Preference Alignment | 10 not-interested + 2 wrong-tool | 10.6% |
| Goal Relevance | Overlaps with Pref. Alignment | — |
| Source Grounding | ~2 "content doesn't match" | 1.8% |
| Novelty | 2 "already done" | 1.8% |

## Decision

Implement **3 dimensions** (Actionability, Preference Alignment, Goal Relevance) on a 0–2 scale, giving a 0–6 composite with threshold ≥ 4. Document Source Grounding and Novelty for future addition.

## Rationale

Source Grounding and Novelty together account for only ~4 rejections (3.5%). More dimensions = more noise in self-grading scores = less reliable threshold. Research consensus: simpler rubrics are more consistent for LLM judges.

## Consequences

### Positive
- Tighter, more reliable rubric with fewer noise dimensions
- Covers ~27% of rejections — same practical coverage as 5 dimensions

### Negative
- Won't catch the ~3.5% of rejections caused by source mismatch or redundancy
- Must monitor for these failure patterns post-launch

---

# ADR-003: Preference Alignment Gating (Two-Tier: Hard Veto + Soft Score)

## Status

Accepted — 2026-06-11

## Context

[Backlog #4](../../backlog.md) specifies: "exclude categories explicitly rejected by the user." The user's explicit reject patterns fall into two categories:

1. **Topic-based hard blocks** — deterministic (Claude Code, token budget, GPU, blockchain)
2. **Conditional/nuanced rejects** — context-dependent ("reject if not clear enough to execute")

A pure soft score (0/1/2) allows a suggestion about Claude Code to pass if other dimensions compensate. A pure hard gate over-filters conditional patterns.

## Decision

**Two-tier gate**:
- **Hard veto**: Topic-based blocks auto-fail the entire suggestion regardless of total score
- **Soft score**: General preference alignment scored 0/1/2 within the rubric

## Rationale

Topic blocks are binary decisions that shouldn't be overridden. Conditional patterns are already handled by other rubric dimensions (Actionability, Goal Relevance).

## Consequences

### Positive
- Directly addresses backlog #4's "exclude" requirement
- No false positives from hard veto — these topics are definitively rejected

### Negative
- Blocklist must be maintained (auto-maintenance via maintain mode mitigates this)

---

# ADR-004: Rubric-Grader as Separate Skill with Explicit Invocation

## Status

Accepted — 2026-06-11

## Context

Two options for how `ai_analysis.md` connects to the rubric:

| Option | How | Risk |
|---|---|---|
| Reference | `ai_analysis.md` reads `rubric.md` file, embeds orchestration inline | Drift between ingestion mode and backtest mode |
| Explicit skill | `ai_analysis.md` says "use the rubric-grader skill" | More tokens read per ingestion |

## Decision

**Explicit skill invocation**. `ai_analysis.md` delegates to the `rubric-grader` skill.

## Rationale

- **Consistency**: Same `SKILL.md` instructions run in both ingestion and backtest modes — no drift risk
- **Single source of truth**: All rubric logic (criteria, threshold, blocklist, filter/log routing, calibration) in one place
- **Clean interface**: `ai_analysis.md` doesn't need to know rubric internals
- Token cost is marginal — one more skill read per ingestion

## Consequences

### Positive
- Any rubric change requires editing one file only
- Backtest and grade modes guaranteed to apply identical logic

### Negative
- Agent reads more instructions per ingestion (SKILL.md + references vs. rubric.md only)

---

# ADR-005: Remove Legacy Suggestion Fields (💎 價值評分, ⚡ 可行動性, 🎯 決策建議)

## Status

Accepted — 2026-06-11

## Context

The suggestion entry format has 4 metadata fields. After introducing the rubric, 3 become redundant:

| Field | Rubric overlap | Usage evidence |
|---|---|---|
| 💎 價值評分 | ≈ Goal Relevance | 71% of bare rejects scored "High" — poorly calibrated |
| ⚡ 可行動性 | ≈ Actionability | Redundant with rubric dimension |
| 🎯 決策建議 | Replaced by threshold filter | Applied "Action" to 63% of suggestions; "Store" has 42.6% reject rate; only 4/390 reviews mentioned it |

No programmatic logic consumes these fields — confirmed by `grep` across all skills.

## Decision

Remove all 3 fields. Replace with a single `📊 Rubric: {total}/6 (A:{n} P:{n} G:{n})` line.

## Rationale

- Net reduction: 3 fields removed, 1 added — cleaner entry format
- Rubric score provides more information (per-dimension breakdown) in less space
- Eliminates poorly calibrated signals that waste the user's attention

## Consequences

### Positive
- Leaner suggestion entries — less noise for the reviewer
- Generator produces fewer fields — less to get wrong
- `review-suggestions` Step 6 loses §6-4 Decision Calibration — reduced density

### Negative
- Breaking format change: old entries in `suggestions_reviewed.md` lack rubric scores
- Calibration (maintain mode) can only compute on post-launch entries

---

# ADR-006: Blocklist Ownership (rubric-grader skill, not review-suggestions)

## Status

Accepted — 2026-06-11

## Context

The hard-veto blocklist (`data/rubric_blocklist.md`) needs auto-maintenance — scanning `suggestions_reviewed.md` for 3+ rejection patterns and appending new entries. Three ownership options:

| Option | Owner | Impact on review-suggestions |
|---|---|---|
| A | `review-suggestions` Step 6 | Adds pattern detection logic to an already-dense step (6 subsections) |
| B | Dedicated maintenance script | New infrastructure to maintain |
| C | `rubric-grader` skill (maintain mode) | One invocation line in `review-suggestions` |

## Decision

**Option C**: The rubric-grader skill owns both reading (grade mode) and writing (maintain mode) the blocklist.

## Rationale

- Single ownership: the skill that reads the blocklist also maintains it
- `review-suggestions` adds one line ("use rubric-grader skill (maintain mode)") — no density increase
- Calibration logic (rubric score accuracy tracking) bundles naturally with blocklist maintenance

## Consequences

### Positive
- `review-suggestions` stays lean
- All rubric-related logic centralized in one skill
- Maintain mode is testable independently

### Negative
- `rubric-grader` is a 3-mode skill — more complex than a pure reference skill
- But consistent with project's existing multi-mode skill patterns

---

# ADR-007: Filtered Suggestion Audit Log

## Status

Accepted — 2026-06-11

## Context

When a suggestion is filtered (fails rubric or hard-veto), the "⏭️ Suggestion scored {score}/10 — below threshold, skipped" message only appears in ephemeral conversation output. After the daily-workflow finishes, there is no persistent record of what was filtered or why.

Without a log:
- Cannot verify if the rubric is filtering correctly vs. over-filtering
- Cannot calibrate the threshold without data
- The verification plan's "track via logs" step has no actual log to query

## Decision

Append filtered suggestions to `data/suggestions_filtered.md` with rubric scores and filter reason.

## Rationale

- Provides audit trail for threshold calibration and false-positive detection
- Negligible cost: one file write per filtered suggestion
- Reviewed periodically during calibration, not daily

## Consequences

### Positive
- Full observability of the rubric's filtering behavior
- Enables data-driven threshold adjustment

### Negative
- File grows indefinitely — may need periodic archival (acceptable for now)
