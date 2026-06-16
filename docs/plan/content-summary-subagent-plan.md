# Plan: Dedicated Summary Subagent for content-summary

Introduce a `content-summariser` subagent to isolate summarisation into clean contexts, preventing context rot as daily content volume grows.

> RFC: [content-summary-subagent.md](docs/rfc/content-summary-subagent.md)

---

## Proposed Changes

### 1. content-summary (Shared Skill)

#### [NEW] [subagent_prompt.md](.agents/skills/content-summary/references/subagent_prompt.md)

Contract-only file containing the `content-summariser` subagent's system prompt:
- Role description: content summariser for the pipeline
- File list: 7 files to read (5 references + `data/goals.md` + `data/user_preferences.md`)
- Input contract: expected prompt fields (Source Type, URL, Title, Author, Task ID, Source Metadata, Date, Raw Content)
- Output behavior: write report to `reports/{SourceType}_YYYY_MM_DD/`, append suggestion to `data/suggestions_pending.md`, return confirmation with file path

#### [MODIFY] [SKILL.md](.agents/skills/content-summary/SKILL.md)

- Add `subagent_prompt.md` to the reference table:

| File | When to read | What it provides |
|---|---|---|
| `references/subagent_prompt.md` | Before spawning the content-summariser subagent | System prompt and I/O contract for `define_subagent` |

#### [MODIFY] [README.md](.agents/skills/content-summary/README.md)

- Add architecture section explaining the subagent pattern with before/after diagram
- Add `subagent_prompt.md` to file structure and reference table
- Add `daily-workflow` Step 5 as a consumer
- Add changelog entry for v3.0.0

---

### 2. ingest-newsletter

#### [MODIFY] [SKILL.md](.agents/skills/ingest-newsletter/SKILL.md)

Replace Steps 2-2 through 2-4b with:

**Step 2-2 (Pre-flight, once per batch):**
> If `content-summariser` subagent has not been defined in this conversation, read `../content-summary/references/subagent_prompt.md` and call `define_subagent` with its content as the `system_prompt`, `enable_write_tools: true`.

**Step 2-3 (Per email):**
> Invoke `content-summariser` subagent with: Source Type = Newsletter, Source URL, Title (Subject), Author (From), Date, Source Metadata (sender email, subject line), Raw Content (email body).

**Step 2-4 (Post-subagent):**
> Verify report file exists. If not, log warning and skip to next email.

Steps 2-1 (read email), 2-5 (mark read), 2-6 (next batch) remain unchanged.

---

### 3. ingest-threads

#### [MODIFY] [SKILL.md](.agents/skills/ingest-threads/SKILL.md)

Replace Steps 2–4 with:

**Step 2 (Pre-flight):**
> If `content-summariser` not defined, read subagent prompt and `define_subagent`.

**Step 3 (Invoke subagent):**
> Invoke `content-summariser` with: Source Type = Threads, Source URL, Title, Author (@handle), Task ID, Date, Source Metadata (engagement metrics), Raw Content (verbatim extracted post).

**Step 4 (Post-subagent):**
> Verify report file exists.

Steps 1 (fetch via agent-browser), 5 (mark task done) remain unchanged.

---

### 4. ingest-youtube

#### [MODIFY] [SKILL.md](.agents/skills/ingest-youtube/SKILL.md)

Replace Steps 4–6 with:

**Step 4 (Pre-flight):**
> If `content-summariser` not defined, read subagent prompt and `define_subagent`.

**Step 5 (Invoke subagent):**
> Invoke `content-summariser` with: Source Type = YouTube, Source URL, Title (first `#` heading), Task ID, Date, Source Metadata (Whisper model, video duration), Raw Content (verbatim yt2doc transcript).

**Step 6 (Post-subagent):**
> Verify report file exists.

Steps 1–3 (model selection, launch, poll) and Step 7 (mark done + cleanup) remain unchanged.

---

### 5. ingest-website

#### [MODIFY] [SKILL.md](.agents/skills/ingest-website/SKILL.md)

Replace Steps 2–4 with:

**Step 2 (Pre-flight):**
> If `content-summariser` not defined, read subagent prompt and `define_subagent`.

**Step 3 (Invoke subagent):**
> Invoke `content-summariser` with: Source Type = Website, Source URL, Title (page title), Task ID, Date, Source Metadata (Domain/Host, scraped date), Raw Content (Jina Reader markdown — NOT included in the report per output_template rules).

**Step 4 (Post-subagent):**
> Verify report file exists.

Steps 1 (fetch via Jina Reader), 5 (mark task done) remain unchanged.

---

### 6. daily-workflow

#### [MODIFY] [SKILL.md](.agents/skills/daily-workflow/SKILL.md)

Update **Step 5** (YouTube post-processing) to use the subagent pattern:

Replace the current inline summary references (lines reading `summarise.md`, `output_template.md`, `ai_analysis.md`, `suggestion_log.md`, `filename_rules.md`) with:

**Step 5.3 (Pre-flight):**
> If `content-summariser` not defined, read subagent prompt and `define_subagent`.

**Step 5.4 (Per video):**
> Invoke `content-summariser` with: Source Type = YouTube, Source URL, Title, Task ID, Date, Source Metadata (Whisper model, video duration), Raw Content (transcript).

**Step 5.5 (Post-subagent):**
> Verify report file exists before marking task done.

Steps 5.1 (poll for completion), 5.2 (error handling), 5.6 (mark done + cleanup) remain unchanged.

---

## What Does NOT Change

- The 5 existing reference files (`summarise.md`, `output_template.md`, `ai_analysis.md`, `suggestion_log.md`, `filename_rules.md`) — content stays identical
- `data/goals.md`, `data/user_preferences.md` — format untouched
- `data/suggestions_pending.md` — append format untouched
- Source-fetching logic (gws gmail, agent-browser, yt2doc, Jina Reader)
- Google Tasks lifecycle (mark done, cleanup)
- `daily-distiller` and `review-suggestions` — they consume finished reports, unaffected
- Execution order and pipeline sequencing — no parallelism introduced

---

## Verification Plan

### Automated Tests

- **What to test**: Single newsletter ingest with subagent.
  - **How to test**: Run `ingest-newsletter` with 1 unread email in `label:newsletter is:unread`.
  - **Expected behavior**: Report file exists in `reports/Newsletter_YYYY_MM_DD/`, follows the 7-layer template with all headings present. `data/suggestions_pending.md` has a new entry appended at the bottom with `SourceType = Newsletter`. Email is marked as read.

- **What to test**: Single website ingest with subagent.
  - **How to test**: Run `ingest-website` with one URL from the Delegate task list.
  - **Expected behavior**: Report file exists in `reports/Website_YYYY_MM_DD/`, follows template, `📄 原始內容` section is omitted. Suggestion appended. Task marked completed.

- **What to test**: Verify-before-mark invariant.
  - **How to test**: Inspect orchestrator behavior when subagent completes. Confirm `view_file` or `list_dir` check occurs before `gws tasks tasks patch`.
  - **Expected behavior**: Report file existence is verified before task is marked done.

- **What to test**: Orchestrator context cleanliness.
  - **How to test**: Process 3+ items in a single `daily-workflow` run. Inspect the orchestrator's conversation context.
  - **Expected behavior**: Orchestrator context contains only metadata + subagent confirmations, never raw content from processed items.
