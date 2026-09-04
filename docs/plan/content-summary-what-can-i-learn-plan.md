# Implementation Plan - Add "🧠 What Can I Learn From It" Report Section

Add a new `## 🧠 What Can I Learn From It` section to the shared content-summary template, positioned between `📝 TL;DR` and `🎯 Core Thesis`. This section distills 2–5 reader-centric learning points per report. Only 2 files change; all 4 ingest skills inherit automatically.

For the detailed technical architecture, design trade-offs, and decisions, please refer to the corresponding RFC/ADR: [content-summary-what-can-i-learn](../rfc/content-summary-what-can-i-learn.md).

## User Review Required

> [!IMPORTANT]
> All design decisions resolved via grill-me session (2026-08-19). No open questions remain.

## Open Questions

None — all resolved in grill session.

---

## Proposed Changes

### Content Summary Shared Skill

#### [MODIFY] [output_template.md](.agents/skills/content-summary/references/output_template.md)

* Insert new `## 🧠 What Can I Learn From It` section between `## 📝 TL;DR` and `## 🎯 Core Thesis`.
* Section template: 2–5 bullet points of concrete learnings (knowledge, skill, methodology, or insight).

#### [MODIFY] [summarise.md](.agents/skills/content-summary/references/summarise.md)

* **Two-Zone table**: Add `What Can I Learn From It` to Zone A row alongside TL;DR, Core Thesis, Reasoning Map, Visual Map.
* **Guidance section**: Insert new numbered section between TL;DR guidance and Core Thesis guidance, with quality rules (Zone A, 2–5 bullets, reader perspective, ❌/✅ examples).
* **Self-verification**: Add 6th check — "「What Can I Learn From It」是否為具體學習點而非主題描述？"
* **Section numbering**: Renumber subsequent sections after the insertion.

---

## Verification Plan

### Automated Tests

- **What to test**: New section exists in output_template.md in correct position
  - **How to test**: `awk '/TL;DR/,/Core Thesis/' .agents/skills/content-summary/references/output_template.md | grep "What Can I Learn From It"`
  - **Expected behavior**: Grep matches 1 line, confirming section is between TL;DR and Core Thesis

- **What to test**: Summarise.md contains all 3 additions (Zone table, guidance, self-verification)
  - **How to test**: `grep -c "What Can I Learn From It" .agents/skills/content-summary/references/summarise.md`
  - **Expected behavior**: Count ≥ 3

- **What to test**: Zone A classification is correct
  - **How to test**: `grep -A1 "Zone A" .agents/skills/content-summary/references/summarise.md | grep "What Can I Learn"`
  - **Expected behavior**: Match found in Zone A row

- **What to test**: Skill YAML frontmatter is valid
  - **How to test**: `python3 scripts/validate_skill.py .agents/skills/content-summary/SKILL.md`
  - **Expected behavior**: Validation passes (exit code 0)
