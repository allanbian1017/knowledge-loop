# Task: Parallel Content Processing

> Plan: [parallel-content-processing-plan.md](parallel-content-processing-plan.md)
> RFC: [parallel-content-processing.md](../rfc/parallel-content-processing.md)

---

## Phase 1 — Skill Changes

- [x] Add `SuggestionOutputPath` parameter to `content-summary/references/suggestion_log.md`
  - When provided, write suggestion JSON to the specified path
  - When omitted, use default location (backward compatible)
- [x] Add single-email mode to `ingest-newsletter/SKILL.md`
  - When `MESSAGE_ID` is provided, skip Step 1 (batch discovery)
  - Go directly to Step 2 (process that single email)
  - Accept optional `SuggestionOutputPath`
- [x] Add `SuggestionOutputPath` parameter to `ingest-threads/SKILL.md`
- [x] Add `SuggestionOutputPath` parameter to `ingest-website/SKILL.md`
- [x] Add `SuggestionOutputPath` parameter to `ingest-youtube/SKILL.md`
- [x] Create `data/suggestions_pending/` directory with `.gitkeep`
- [ ] Verify: standalone `ingest-newsletter` batch mode still works unchanged
- [ ] Verify: standalone `ingest-threads` / `ingest-website` / `ingest-youtube` still work unchanged

## Phase 2 — Orchestrator Rewrite

- [x] Rewrite `daily-workflow/SKILL.md` Steps 2–5:
  - [x] Step 2: Conditional directory pre-creation (only for non-empty queues)
  - [x] Step 3: Parallel subagent dispatch
    - [x] 3a: Newsletter — batch-of-10 email ID discovery + per-email subagent dispatch
    - [x] 3b: Threads — per-task subagent dispatch
    - [x] 3c: Website — per-task subagent dispatch
    - [x] 3d: YouTube — per-task subagent dispatch
  - [x] Early exit: skip Steps 3–7 if all queues are empty
  - [x] Step 4: Sync barrier with 30-minute global timeout
  - [x] Step 4M: Suggestion merge (read pending files → append to main log → delete pending)
- [x] Ensure focused subagent context (each subagent loads only its relevant skill)
- [x] Update Final Summary template to include: dispatched count, success count, failed count, timed-out count

## Phase 3 — Verification

- [ ] Test: single newsletter in single-email mode with `SuggestionOutputPath`
- [ ] Test: parallel dispatch with mixed content (newsletter + Threads + website)
- [ ] Test: suggestion merge correctness (pending files → main log → cleanup)
- [ ] Test: zero items fast exit
- [ ] Test: error isolation (one failed subagent doesn't block others)
- [ ] Test: orchestrator context cleanliness (no raw content in main agent)
- [ ] Measure: wall-clock time vs. sequential baseline
