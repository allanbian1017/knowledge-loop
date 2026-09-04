# RFC: Content Summary v4.0.0 — Thesis-Driven Analysis

## Summary

Replace the 7 Layers of Learning framework with a thesis-driven analysis structure that directly answers three questions: "Should I read this?", "What's the core argument?", and "How does the author prove it?" — while preserving the AI Analysis sections (Personal Relevance, Actionability, Idea Generation, Reflection & Prediction).

## Status

**Accepted** — 2026-07-22 (Grill Session)

**Supersedes**: [content-summary-7-layers-of-learning.md](content-summary-7-layers-of-learning.md) (v2.0.0), [content-summary-key-insight.md](content-summary-key-insight.md) (v2.2.0)

**Conversation**: `7d70880f-74d2-478b-9cef-bcb08eaa9739`

## Motivation

Current reports (v3.1.0) have 9 sections across 7 learning layers. While comprehensive, this design doesn't match the user's actual reading workflow:

| User's Real Question | Current System Answer |
|---|---|
| Should I spend time reading this? | ❌ No direct answer — must read 核心總結 + 關鍵洞察 + 關鍵重點 and infer |
| What is the author actually arguing? | ⚠️ 核心總結 captures *topic* but not *thesis* |
| How does the author prove it? | ❌ 關鍵重點 lists facts by paragraph, not by reasoning flow |

The system is optimized for "learning extraction" but the user's workflow is: **scan → triage → deep-read selectively**. The report structure should mirror this.

### Concrete Example

From a current report:
```
## 📝 核心總結（Core Idea）
- 本影片由前 Tesla AI 總監 Andrej Karpathy 分享，探討軟體開發從 1.0 到 3.0 的演進...
```

This tells me *what the video covers* but not:
- Whether I should watch the full 40-minute video (Reading Decision)
- What Karpathy is *arguing* vs. *describing* (Core Thesis)
- How his argument builds step by step (Reasoning Map)

## Decision Drivers

- **Must directly answer** "should I read this?" in < 30 seconds
- **Must distinguish** between the author's thesis and supporting evidence
- **Must track reasoning flow**, not paragraph order
- **Must preserve** AI Analysis (Layers 4-7) which the user actively reads
- **Should reduce** total sections vs. current 9 (avoid repeating the bloat problem)
- **Should support** different article types (research, opinion, news)

## Considered Options

### Option 1: Incremental — Add Reading Decision to existing structure

- **Pros**: Minimal change, no risk of breaking existing consumers
- **Cons**: Doesn't fix the core problem (thesis vs. summary confusion); adds yet another section to an already bloated structure

### Option 2: Thesis-Driven Redesign (chosen)

- **Pros**: Directly answers the 3 core questions; reduces section count; supports multiple article types via Reasoning Map templates
- **Cons**: Significant template rewrite; loses the "7 Layers" naming (though the valuable layers 4-7 are preserved)

### Option 3: Full Minimalist — Only 3 sections (TL;DR + Thesis + Decision)

- **Pros**: Extremely scannable
- **Cons**: Loses the Reasoning Map (how the author proves it) and AI Analysis sections the user actively uses

## Detailed Design

### New Report Structure

```
# {title}

## 來源                          ← unchanged
## 🔖 來源 Metadata              ← unchanged

## 📝 TL;DR                      ← NEW (3-5 sentences: topic + problem + conclusion)
## 🎯 Core Thesis                ← NEW (one-sentence conclusion + supporting arguments)
## 🗺️ Reasoning Map              ← NEW (3 templates, inline evidence tags)
## ⭐ Reading Decision            ← NEW (personalized star rating + Novel Insight)
## 🗺️ Visual Map                 ← NEW (Mermaid diagram, ★★★★☆+ only)

## 🤖 AI Analysis                ← RESTRUCTURED (Layers 4-7, no numbering)
  ### 個人相關性（Personal Relevance）
  ### 可行動性（Actionability）
  ### 靈感觸發（Idea Generation）
  ### 反思與預測（Reflection & Prediction）

## ⚠️ 資訊免責聲明               ← unchanged
## 📄 原始內容                    ← unchanged
```

### Removed Sections

| Old Section | Disposition |
|---|---|
| 📝 核心總結 (Core Idea) | → Replaced by TL;DR + Core Thesis |
| 💡 關鍵洞察 (Key Insight) | → Absorbed into Reading Decision's 💡 Novel Insight |
| 📌 關鍵重點 (Key Highlights) | → Absorbed into Reasoning Map |
| 2️⃣ 訊號判斷 (Signal vs Noise) | → Absorbed into Reading Decision |
| 3️⃣ 機制理解 (Mechanism) | → Absorbed into Reasoning Map |

### Key Design Decisions

#### 1. Core Thesis Format

```markdown
## 🎯 Core Thesis

> 一句話核心結論：[The single claim the author is trying to convince the reader to accept]

支撐論點：
- [Supporting argument 1]
- [Supporting argument 2]
- [Supporting argument 3 (if applicable)]
```

No primary/secondary distinction — bullet order implies weight. Detailed reasoning left to the Reasoning Map.

#### 2. Reasoning Map: 3 Templates

Agent auto-selects based on content type:

| Template | When | Format |
|---|---|---|
| **Linear Chain** | Research, argumentative articles | Step 1 → Step 2 → ... → Conclusion |
| **Parallel Arguments** | Opinion, commentary | Core Thesis ← Arg A + Arg B + Arg C |
| **Minimal** | News, informational | "No argument chain; factual content" + bullet list |

#### 3. Inline Evidence Tags

6 fixed emoji tags annotated inline within Reasoning Map steps:

`📊 Data` · `📖 Research` · `🏢 Case Study` · `💬 Quote` · `👤 Personal Experience` · `🧠 Reasoning`

Example:
```
Step 1：Author argues LLM context windows are the core bottleneck
[📊 Data] OpenAI internal tests show 40% performance degradation at 128k tokens
↓
Step 2：Proposes RAG as solution
[📖 Research] Lewis et al. 2020
[🏢 Case] Notion AI production deployment
```

#### 4. Reading Decision: Personalized Star Rating

Anchored to `data/goals.md`. Answers "should **I** read this?", not "is this objectively good?"

| Rating | Criteria |
|---|---|
| ★★★★★ | Novel framework directly applicable to current goals |
| ★★★★☆ | Strong new info relevant to goals. Worth full read |
| ★★★☆☆ | Useful context, no breakthrough. TL;DR sufficient |
| ★★☆☆☆ | Tangential or repackaged. Skip |
| ★☆☆☆☆ | No new info. Content farm or redundant |

Star labels follow configured output language (`data/user_preferences.md`).

Includes a structured sub-section:
```markdown
**判斷依據**：
- [Reason 1]
- [Reason 2]

**💡 真正的新資訊**：
[Most valuable new concept, or "主要重新整理已知觀念"]
```

#### 5. Conditional Visual Map

Mermaid flowchart only generated for ★★★★☆+ articles. Saves tokens and avoids Mermaid syntax errors on low-value content.

#### 6. Two-Zone Quality Rule

| Zone | Sections | Rule |
|---|---|---|
| **A: Extraction** | TL;DR, Core Thesis, Reasoning Map, Visual Map | Zero hallucination. Source-faithful only. |
| **B: Judgement** | Reading Decision (incl. Novel Insight), AI Analysis | Grounded inference. Calibrated by `data/goals.md`. |

#### 7. Self-Verification (5 Checks)

1. Core Thesis 是否真的是「一句話」？如果超過兩句，重寫。
2. Reasoning Map 是否追蹤作者的邏輯流程而非段落順序？
3. Reading Decision 的星級是否有錨定 goals.md？
4. Zone A sections 是否包含任何原文沒有的推論？如有，移除。
5. 若原文模糊，是否誠實標示（如「原文未詳細說明」）？

## Files Modified

| File | Change |
|---|---|
| `content-summary/references/output_template.md` | New report structure |
| `content-summary/references/summarise.md` | New quality rules, templates, self-verification |
| `content-summary/README.md` | Updated overview, v4.0.0 changelog |

## Files Unchanged

| File | Reason |
|---|---|
| `ai_analysis.md` | Suggestion pipeline is independent of report body |
| `suggestion_log.md` | Format references title/URL/category/score only |
| `filename_rules.md` | Path conventions unchanged |
| `SKILL.md` | Reference table unchanged (same files, same read timing) |
| All ingest skills | `📄 Read` directives auto-pick up new templates |
| `daily-distiller` | Synthesizes by theme, not section heading |
| `rubric-grader` | Scores based on `ai_analysis.md` fields |

## Consequences

### Positive

- Reports directly answer the 3 core triage questions
- Reasoning Map tracks logical flow, not paragraph order — reveals argument strength
- Personalized Reading Decision enables 30-second skip-or-read decisions
- Evidence tags make data vs. opinion immediately visible
- Reduced section count (6 vs. 9) without losing substance
- AI Analysis preserved — no workflow disruption

### Negative

- Breaking change in report format — old and new reports coexist in `reports/`
- Agent may initially struggle with thesis extraction vs. topic summarization (requires prompt iteration)
- Reasoning Map template selection adds complexity — agent may default to Linear Chain

### Risks

- **Reasoning Map quality**: Agent may fall back to paragraph-by-paragraph summary instead of logical flow. **Mitigation**: Self-Verification check #2.
- **Core Thesis overwriting**: Agent may write 2+ sentences. **Mitigation**: Self-Verification check #1.
- **Star rating calibration**: Without historical data, initial ratings may be inconsistent. Will stabilize over time.

## Migration

No backward migration. Old reports retain their format. New format applies to all reports generated after deployment. `daily-distiller` processes by date and synthesizes by theme — not affected.

## Lessons Learned from v2.0.0 (7 Layers)

From [content-summary-7-layers-of-learning.md](content-summary-7-layers-of-learning.md):

- **7 Layers was good at depth, bad at triage** — comprehensive analysis doesn't help if the user can't quickly decide whether to read
- **Section count matters** — 9 sections caused scan fatigue; the most valuable content got buried
- **Layers 4-7 proved their value** — user actively reads them; they're worth preserving even in a redesign

## Related Decisions

- [content-summary-7-layers-of-learning.md](content-summary-7-layers-of-learning.md) — Superseded by this RFC (Layers 1-3 replaced, 4-7 preserved)
- [content-summary-key-insight.md](content-summary-key-insight.md) — Key Insight section absorbed into Reading Decision's Novel Insight
- [content-summary-subagent.md](content-summary-subagent.md) — Subagent architecture unchanged; new templates flow through automatically
- [rubric-grader.md](rubric-grader.md) — Rubric grading pipeline unchanged

## References

- Grill Session Decision Log: `docs/decision_logs/session_7d70880f-74d2-478b-9cef-bcb08eaa9739.md`
- Implementation Plan: `docs/plan/content-summary-thesis-driven-plan.md`
- Task Checklist: `docs/plan/content-summary-thesis-driven-task.md`
