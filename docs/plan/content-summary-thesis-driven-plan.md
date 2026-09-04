# Content Summary v4.0.0 — Implementation Plan

**RFC**: [content-summary-thesis-driven-analysis.md](../rfc/content-summary-thesis-driven-analysis.md)
**Task Checklist**: [content-summary-thesis-driven-task.md](content-summary-thesis-driven-task.md)
**Status**: Approved, awaiting execution

---

## Scope

Modify 3 files in the `content-summary` skill to implement the thesis-driven analysis framework:

| File | Change Type |
|---|---|
| `references/output_template.md` | Rewrite — new report structure |
| `references/summarise.md` | Rewrite — new quality rules |
| `README.md` | Update — overview + changelog |

All other files (ai_analysis.md, suggestion_log.md, filename_rules.md, SKILL.md) and all consumer skills (ingest-*, daily-distiller, rubric-grader) remain untouched.

---

## Implementation Details

### 1. output_template.md — New Report Structure

Replace the entire report body. The new template has 6 content sections:

```
📝 TL;DR                → 3-5 sentences (topic + problem + conclusion)
🎯 Core Thesis           → One-sentence conclusion + bullet list of supporting arguments
🗺️ Reasoning Map         → 3 templates (Linear Chain / Parallel Arguments / Minimal)
                           with inline evidence tags (📊📖🏢💬👤🧠)
⭐ Reading Decision       → Personalized star rating (goals.md) + judgment bullets
                           + 💡 真正的新資訊 sub-section
🗺️ Visual Map            → Mermaid flowchart (conditional: ★★★★☆+ only)
🤖 AI Analysis           → 4 sub-sections (個人相關性, 可行動性, 靈感觸發, 反思與預測)
                           No layer numbering
```

Preserved unchanged: 來源 header, 🔖 來源 Metadata, ⚠️ 資訊免責聲明, 📄 原始內容.

Star Rating Rubric (labels follow configured output language):

| Rating | Criteria |
|---|---|
| ★★★★★ | Novel framework directly applicable to current goals |
| ★★★★☆ | Strong new info relevant to goals. Worth full read |
| ★★★☆☆ | Useful context, no breakthrough. TL;DR sufficient |
| ★★☆☆☆ | Tangential or repackaged. Skip |
| ★☆☆☆☆ | No new info. Content farm or redundant |

### 2. summarise.md — New Quality Rules

Replace the 7 Layers guidance with thesis-driven analysis rules:

| Section | Content |
|---|---|
| Language | Preserved unchanged |
| Two-Zone Rule (revised) | Zone A (Extraction): TL;DR, Core Thesis, Reasoning Map, Visual Map — zero hallucination. Zone B (Judgement): Reading Decision, AI Analysis — grounded inference via goals.md |
| Thesis Extraction Guidance | NEW — How to identify core thesis vs. topic description |
| Reasoning Map Templates | NEW — Selection criteria for Linear Chain / Parallel Arguments / Minimal; evidence tag definitions |
| Reading Decision Rubric | NEW — Star rating criteria anchored to goals.md |
| Visual Map Rules | NEW — Conditional generation (★★★★☆+), Mermaid flowchart format |
| AI Analysis Guidance | PRESERVED — Layers 4-7 guiding questions, without layer numbering |
| Comprehensiveness & Objectivity | Preserved unchanged |
| Self-Verification | UPDATED — 5 checks targeting new structure risks |
| Teaser Detection | Preserved unchanged |

### 3. README.md — Documentation Update

- Update overview to describe thesis-driven analysis approach
- Add v4.0.0 changelog entry with date and change summary
- Remove references to "7 Layers of Learning" as the active framework

---

## Verification Strategy

### Automated

1. **Structural validation**: Confirm output_template.md contains all 6 required section headings
2. **Consumer compatibility**: Grep all ingest skills for `📄 Read` directives → confirm all point to valid files (no broken references after rename)
3. **End-to-end smoke test**: Run `ingest-website` on a known article URL → verify output report follows the new template

### Manual

- Review generated report: does it answer the 3 core questions?
- Verify Mermaid diagram renders for ★★★★☆+ articles
- Confirm AI Analysis reads naturally without layer numbering

---

## Rollback Plan

If the new template produces significantly worse reports:
1. Revert output_template.md and summarise.md via git
2. Reports generated during the experiment remain in `reports/` (they're still valid documents)
3. No consumer skills need rollback (they use `📄 Read` directives)
