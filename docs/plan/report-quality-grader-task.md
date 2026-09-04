# Report Quality Grader — Task Checklist

**RFC**: [report-quality-grader.md](../rfc/report-quality-grader.md)
**Plan**: [report-quality-grader-plan.md](report-quality-grader-plan.md)

---

## Phase 1: Core Rubric Infrastructure

- [ ] Create `references/report_rubric.md` in rubric-grader skill
  - Define 3 dimensions (Depth, Adoptability, Standalone Clarity) with 0/1/2 scoring
  - Add quality bar examples (good vs bad) from the 7-layers RFC
  - Add thin-source calibration instruction
- [ ] Add Mode 4 (Report Quality) to `rubric-grader/SKILL.md`
  - Document grading flow: read report → read rubric → score D/Ad/S → return scores + per-dimension feedback
  - Specify that this mode is invoked as a subagent by ingest skills

## Phase 2: Quality Gate Integration

- [ ] Create `references/quality_gate.md` in content-summary
  - Document the subagent grading flow (spawn → wait → pass/retry)
  - Specify feedback injection format for retry
  - Specify max 1 retry, no re-grade after retry
  - Specify quality badge format for report metadata
- [ ] Update `content-summary/SKILL.md` reference table
  - Add quality_gate.md entry with description
- [ ] Add quality gate step to `ingest-newsletter/SKILL.md`
  - Insert `📄 Read quality_gate.md` between Step 2-4 (write report) and Step 2-4b (AI analysis)
- [ ] Add quality gate step to `ingest-threads/SKILL.md`
  - Insert at equivalent position
- [ ] Add quality gate step to `ingest-youtube/SKILL.md`
  - Insert between Step 5 (write report) and Step 6 (append suggestion)
- [ ] Add quality gate step to `ingest-website/SKILL.md`
  - Insert at equivalent position

## Phase 3: Verification

- [ ] Grade 3 recent high-quality reports — expect scores ≥ 4
- [ ] Grade the "Before" example from 7-layers RFC (shallow Zhu Qi report) — expect score < 4
- [ ] Run one full ingest with quality gate active — confirm badge appears in metadata
- [ ] Verify retry flow: artificially constrain prompt to produce shallow output, confirm retry triggers and improves score

## Phase 4: Calibration (after ~20 graded reports)

- [ ] Collect score distribution data via `grep "Report Quality" reports/**/*.md`
- [ ] Evaluate whether threshold 4 is appropriate or should be raised to 5
- [ ] Document calibration results
