# Skill Plan: Report Quality Grader for Content-Summary Pipeline

Introduce a report quality grading step that evaluates report body quality (Core Idea, Key Insight, 7 Layers) against a 3-dimension rubric (Depth, Adoptability, Standalone Clarity), automatically detecting and regenerating shallow summaries via a subagent grader with max 1 retry.

**RFC**: [report-quality-grader.md](../rfc/report-quality-grader.md)

---

## Proposed Changes

### 1. rubric-grader (Skill Extension + New Reference)

#### [NEW] [references/report_rubric.md](../../.agents/skills/rubric-grader/references/report_rubric.md)
- Define 3 rubric dimensions (Depth, Adoptability, Standalone Clarity) with 0/1/2 scoring criteria per dimension.
- Include concrete examples for each score level (D=0 vs D=2, Ad=0 vs Ad=2).
- Document thin source handling: grader judges source richness, no arbitrary character thresholds. Reports that faithfully extract all signal from thin sources score D≥1.
- Document composite score (0–6) and threshold (≥4, calibrate after 20 reports).
- Document feedback format: per-dimension score + reason, no example rewrite.

#### [MODIFY] [SKILL.md](../../.agents/skills/rubric-grader/SKILL.md)
- Add **Mode 4: Report Quality** to the mode table.
  - Trigger: invoked by ingest skills via `quality_gate.md` after report generation.
  - Behaviour: read report file at given path. Read `references/report_rubric.md`. Score 3 dimensions (D, Ad, S). Return composite score + per-dimension score + reason.
  - No file writes — the invoking agent handles badge appending and retry.
- Update skill description to mention report quality grading alongside suggestion grading.

---

### 2. content-summary (New Shared Reference)

#### [NEW] [references/quality_gate.md](../../.agents/skills/content-summary/references/quality_gate.md)
- Document the subagent grading flow:
  1. After writing the report file, spawn a grader subagent: "Grade report at {path}" using `rubric-grader` skill Mode 4.
  2. Wait for subagent response (composite score + per-dimension feedback).
  3. If score ≥ 4: append `- 📊 Quality: {total}/6 (D:{n} Ad:{n} S:{n})` to the report's `🔖 來源 Metadata` section. Proceed to AI analysis.
  4. If score < 4: regenerate the full report with grader's per-dimension feedback injected into the prompt. Append `- 📊 Quality: {total}/6 (D:{n} Ad:{n} S:{n}) ♻️ retried` to metadata. Proceed to AI analysis. No re-grade after retry.
- Document the quality badge format and `♻️ retried` marker.

#### [MODIFY] [SKILL.md](../../.agents/skills/content-summary/SKILL.md)
- Add `quality_gate.md` to the reference table with description: "Report quality grading flow — subagent grader with retry logic."

---

### 3. Ingest Skills (Quality Gate Step)

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-newsletter/SKILL.md)
- Add a quality gate step between report writing and AI analysis:
  - `📄 Read` reference to `content-summary/references/quality_gate.md`.
  - Position: after "Write report to file" step, before "Generate AI analysis" step.

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-threads/SKILL.md)
- Same change as ingest-newsletter: add `📄 Read` line for `quality_gate.md` between report writing and AI analysis.

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-youtube/SKILL.md)
- Same change as ingest-newsletter: add `📄 Read` line for `quality_gate.md` between report writing and AI analysis.

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-website/SKILL.md)
- Same change as ingest-newsletter: add `📄 Read` line for `quality_gate.md` between report writing and AI analysis.

---

## Verification Plan

### Automated Tests

- **What to test**: Quality gate triggers on report generation.
  - **How to test**: Process one newsletter with quality gate enabled. Check the report's `🔖 來源 Metadata` section.
  - **Expected behavior**: Report contains `- 📊 Quality: {n}/6 (D:{n} Ad:{n} S:{n})` line in metadata.

- **What to test**: Retry mechanism triggers on low-quality report.
  - **How to test**: Process a known thin/shallow source (e.g., a 2-sentence teaser newsletter). If grader scores < 4, verify retry occurs.
  - **Expected behavior**: Report metadata contains `♻️ retried` marker. Report content is qualitatively deeper than a non-retried version of the same source.

- **What to test**: Subagent grader returns valid rubric scores.
  - **How to test**: Invoke `rubric-grader` skill (Mode 4) directly on an existing report file. Verify response format.
  - **Expected behavior**: Response contains 3 dimension scores (D, Ad, S) each 0–2, composite score 0–6, and per-dimension reason text.

- **What to test**: Quality badge format compliance.
  - **How to test**: After first daily-workflow run post-launch, `grep "📊 Quality" reports/` across new reports.
  - **Expected behavior**: All new reports contain `📊 Quality:` line in metadata. Score format matches `{n}/6 (D:{n} Ad:{n} S:{n})`.

- **What to test**: Downstream compatibility with daily-distiller.
  - **How to test**: Run `daily-distiller` on a mix of old reports (no badge) and new reports (with badge).
  - **Expected behavior**: Distiller produces normal output. Quality badge in metadata does not affect synthesis.

### Live Validation (after 20 reports)

- Review pass/fail distribution: target ≥80% first-attempt pass rate.
- Review retried reports: confirm quality improvement between original and retried version.
- Adjust threshold if pass rate is too low (< 70%) or too high (> 95%).
