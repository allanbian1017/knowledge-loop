# Plan: Parallel Content Processing

Rewrite the `daily-workflow` orchestrator from sequential processing to parallel subagent dispatch, giving each content item (newsletter, Threads, website, YouTube) its own isolated full-lifecycle subagent.

> RFC: [parallel-content-processing.md](../rfc/parallel-content-processing.md)

---

## Proposed Changes

### 1. content-summary (Shared Skill)

#### [MODIFY] [suggestion_log.md](../../.agents/skills/content-summary/references/suggestion_log.md)

Add an optional `SuggestionOutputPath` parameter:
- When provided, write the suggestion JSON to the specified path instead of the default location
- When omitted, behavior is unchanged (backward compatible)
- This enables per-subagent suggestion files (`data/suggestions_pending/suggestion_<type>_<id>.json`)

---

### 2. ingest-newsletter

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-newsletter/SKILL.md)

Add single-email mode:
- When a `MESSAGE_ID` is provided, skip Step 1 (batch discovery via `gws gmail users messages list`)
- Go directly to Step 2 (read email → summarise → write report → AI analysis → suggestion → mark read + archive)
- The existing batch-loop mode remains unchanged for standalone invocations (e.g., user says "幫我整理電子報")
- Accept optional `SuggestionOutputPath` parameter — pass through to `suggestion_log.md`

---

### 3. ingest-threads

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-threads/SKILL.md)

Accept optional `SuggestionOutputPath` parameter — pass through to `suggestion_log.md`.
No other changes to processing logic.

---

### 4. ingest-website

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-website/SKILL.md)

Accept optional `SuggestionOutputPath` parameter — pass through to `suggestion_log.md`.
No other changes to processing logic.

---

### 5. ingest-youtube

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-youtube/SKILL.md)

Accept optional `SuggestionOutputPath` parameter — pass through to `suggestion_log.md`.
No other changes to processing logic.

---

### 6. daily-workflow

#### [MODIFY] [SKILL.md](../../.agents/skills/daily-workflow/SKILL.md)

Replace Steps 2–5 with the parallel dispatch-and-collect flow:

**Step 2 — Pre-create report directories:**
- Create date-stamped report directories only for content types with items
- Create `data/suggestions_pending/` staging area

**Step 3 — Dispatch all content items in parallel:**

- **3a (Newsletters):** Fetch unread email IDs in batches of 10 via `gws gmail users messages list`. For each `MESSAGE_ID`, spawn a focused subagent scoped to `ingest-newsletter` (single-email mode). Fire-and-forget — continue dispatching immediately.
- **3b (Threads):** For each Threads task, spawn a focused subagent scoped to `ingest-threads`. Pass URL, task ID, Delegate list ID, report directory, suggestion output path.
- **3c (Websites):** For each website task, spawn a focused subagent scoped to `ingest-website`. Same metadata pattern.
- **3d (YouTube):** For each YouTube task, spawn a focused subagent scoped to `ingest-youtube`. Same metadata pattern.

Each subagent:
- Loads ONLY the skill relevant to its content type (focused context)
- Executes the full lifecycle: fetch → summarise → report → suggestion → mark done
- Writes suggestion to `data/suggestions_pending/suggestion_<type>_<item_id>.json`

**Early exit:** If all queues are empty, skip Steps 3–7 and report "No content to process today."

**Step 4 — Collect all results:**
- Wait for all subagents with a **30-minute global timeout**
- After timeout, proceed with completed results; report timed-out items as failures
- Record per-subagent: success/failure, report path, error message

**Step 4M — Merge suggestions:**
- Read all files in `data/suggestions_pending/suggestion_*.json`
- Append each to the main suggestion log
- Delete pending files after successful merge

Steps 1 (bootstrap/discovery), 6 (distillation), 7 (suggestion review), 8 (final summary) remain unchanged.

---

### 7. Data Directory

#### [NEW] data/suggestions_pending/

Empty directory for per-subagent suggestion staging. Created by the orchestrator in Step 2.

---

## What Does NOT Change

- Core processing logic of `ingest-threads`, `ingest-website`, `ingest-youtube` — same skill steps, same behavior
- The website fallback chain (Jina → browser → search_web) — independent of this RFC
- `daily-distiller` and `review-suggestions` — they consume finished reports, unaffected
- The suggestion log schema or report output format
- `data/goals.md`, `data/user_preferences.md` — untouched
- Source-fetching logic within each skill (gws, agent-browser, yt2doc, Jina Reader)

---

## Verification Plan

### Automated Tests

- **What to test**: Single newsletter subagent in single-email mode
  - **How to test**: Invoke `ingest-newsletter` with a specific `MESSAGE_ID` and `SuggestionOutputPath`
  - **Expected behavior**: Report file exists in `reports/Newsletter_YYYY_MM_DD/`, suggestion written to the specified path (not the default location), email marked as read

- **What to test**: Parallel dispatch with mixed content types
  - **How to test**: Run `daily-workflow` with at least 1 newsletter + 1 Threads + 1 website task
  - **Expected behavior**: All subagents dispatch immediately (fire-and-forget). All reports written correctly. Suggestion files merged at Step 4M. Tasks/emails marked done.

- **What to test**: Suggestion merge correctness
  - **How to test**: After parallel run, verify `data/suggestions_pending/` files are merged into the main log and deleted
  - **Expected behavior**: Main log contains all suggestions. No orphaned pending files for successful subagents.

- **What to test**: Timeout behavior
  - **How to test**: Dispatch a subagent with a known-slow URL. Verify orchestrator proceeds after 30 minutes.
  - **Expected behavior**: Completed items are distilled. Timed-out items reported as failures.

- **What to test**: Zero items fast exit
  - **How to test**: Run `daily-workflow` with no unread newsletters and empty Delegate list
  - **Expected behavior**: Orchestrator reports "No content to process today" and exits without creating directories or dispatching subagents.

- **What to test**: Error isolation
  - **How to test**: Process items where one is known to fail (e.g., Cloudflare-blocked website) alongside a healthy newsletter
  - **Expected behavior**: Failed subagent logged as failure. Healthy newsletter processed successfully. Final summary includes both.

- **What to test**: Orchestrator context cleanliness
  - **How to test**: Process 5+ items in a single `daily-workflow` run. Inspect the orchestrator's conversation context.
  - **Expected behavior**: Orchestrator context contains only metadata (IDs, URLs, subagent IDs, completion status). Never contains raw article content.

### Manual Verification

- Verify wall-clock time reduction compared to sequential baseline
- Verify each subagent loads only its relevant skill (not all 30+ skills)
