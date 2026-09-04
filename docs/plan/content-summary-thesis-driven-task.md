# Content Summary v4.0.0 — Execution Tasks

**RFC**: [content-summary-thesis-driven-analysis.md](../rfc/content-summary-thesis-driven-analysis.md)
**Plan**: [content-summary-thesis-driven-plan.md](content-summary-thesis-driven-plan.md)

---

## Phase 1: Implementation

- [x] **1.1** Rewrite `content-summary/references/output_template.md`
  - New report structure: TL;DR → Core Thesis → Reasoning Map → Reading Decision → Visual Map → AI Analysis
  - Include 3 Reasoning Map templates (Linear Chain, Parallel Arguments, Minimal)
  - Include evidence tag definitions (6 emoji labels)
  - Include star rating rubric (5 levels, personalized via goals.md)
  - Include Reading Decision format (judgment bullets + 💡 Novel Insight sub-section)
  - Visual Map conditional note (★★★★☆+ only)
  - AI Analysis with 4 sub-sections (no layer numbering)

- [x] **1.2** Rewrite `content-summary/references/summarise.md`
  - Replace 7 Layers framework with thesis-driven analysis guidance
  - New Two-Zone rule (A: Extraction, B: Judgement)
  - Thesis extraction guidance
  - Reasoning Map template selection criteria
  - Evidence tag usage rules
  - Reading Decision rubric with goals.md anchoring
  - Updated Self-Verification (5 checks)
  - Preserve: Language config, Teaser Detection, Comprehensiveness, Objectivity

- [x] **1.3** Update `content-summary/README.md`
  - Update overview description
  - Add v4.0.0 changelog entry
  - Remove "7 Layers of Learning" references

## Phase 2: Verification

- [x] **2.1** Structural validation: confirm output_template.md contains all required section headings
- [x] **2.2** Consumer compatibility: grep all ingest skills for `📄 Read` directives, confirm all point to valid files
- [x] **2.3** End-to-end smoke test: run `ingest-website` on a known URL, verify output follows new template

## Phase 3: Wrap-up

- [x] **3.1** Update session decision log outcomes
- [x] **3.2** Create walkthrough.md summarizing changes
