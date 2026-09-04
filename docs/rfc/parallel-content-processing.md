# RFC: Parallel Content Processing for Newsletter, Threads, Website & YouTube

## Summary

Extend the `daily-workflow` orchestrator to dispatch each content item as an independent, full-lifecycle subagent. The main agent becomes a pure metadata dispatcher that never touches content — it only discovers item IDs/URLs and spawns subagents. Each subagent independently fetches, summarises, writes a report, appends a suggestion, and marks the source as done. This eliminates both the sequential bottleneck and the context pollution problem.

## Status

**Proposed** — 2026-06-25  
**Revised** — 2026-07-07 (post grill-me session)

## Motivation

### The sequential bottleneck

The current [daily-workflow/SKILL.md](../../.agents/skills/daily-workflow/SKILL.md) processes content types in strict sequence:

```
Step 2: Fire YouTube background commands (async)
Step 3: Process newsletters     ← sequential, one-by-one
Step 4: Process Threads tasks   ← sequential, one-by-one
Step 4W: Process Website tasks  ← sequential, one-by-one (with 4-step fallback chain each)
Step 5: Poll YouTube results    ← summarise in main agent
```

When there are 5 newsletters + 3 Threads posts + 2 website articles, each taking 3–8 minutes, the sequential pipeline takes **30–80 minutes**. With parallelism, the wall-clock time drops to the duration of the single slowest item (~8–15 minutes).

### Context pollution degrades summary quality

In the current sequential model, after processing 5 newsletters, the main agent's context is filled with all 5 articles' full content, summaries, AI analyses, API responses, and error messages. By item #6, the LLM's attention is split across tens of thousands of words of irrelevant prior content. This degrades summary quality for later items.

Subagent isolation gives each summary a **fresh context** with only the single article's content and the relevant skill references. No pollution from other items.

### The main agent's context also gets polluted

Even if summarisation were offloaded to subagents, having the main agent fetch content (via `gws gmail +read`, `read_url_content`, etc.) would still fill the main agent's context with every article's full text. With 7 newsletters + 2 websites + 1 YouTube transcript, the main agent accumulates ~40,000+ words of content it doesn't need for dispatch decisions.

Moving the fetch into the subagent eliminates this entirely. The main agent only handles metadata: message IDs, task IDs, URLs.

### Evidence from conversation history

Analysis of 11 conversations (2026-06-18 to 2026-06-25) shows:

| Date | Items Processed | Duration | Notes |
|---|---|---|---|
| Jun 18 | 18 tasks | ~4 hours | Heaviest session, sequential bottleneck dominant |
| Jun 22 | 8 tasks | ~1.8 hours | Sequential processing + fallback retries |
| Jun 24 | 9 items (2 websites + 7 newsletters) | ~7 min | Light load hid the bottleneck |

---

## Detailed Design

### 1. Architecture overview

```
Main agent (pure metadata dispatcher):
  1. Discover items (email IDs, task URLs)           ← metadata only, never content
  2. Pre-create report directories
  3. For each item → spawn a focused subagent        ← fire-and-forget
  4. Sync barrier (wait for all subagents)
  5. Merge suggestion files
  6. Distill (follow daily-distiller)
  7. Review suggestions

Each subagent (isolated worker):
  1. Load ONLY the skill relevant to its content type
  2. Fetch content
  3. Summarise + AI analysis
  4. Write report file
  5. Write suggestion to a per-subagent file
  6. Mark source as done (archive email / complete Google Task)
```

The main agent **never** sees article content. Its context contains only: task list metadata, subagent IDs, and completion status. This scales to any number of items without context window pressure.

### 2. Full-lifecycle subagent model

Each content item gets its own subagent. The subagent independently executes the relevant ingest skill's full pipeline: fetch → summarise → write report → append suggestion → mark done.

**Uniform pattern across all four content types:**

| Content Type | Subagent receives | Skill to follow |
|---|---|---|
| Newsletter | `MESSAGE_ID` | `ingest-newsletter` (single-email mode) |
| Threads | `THREADS_URL`, `TASK_ID`, `DELEGATE_LIST_ID` | `ingest-threads` |
| Website | `WEBSITE_URL`, `TASK_ID`, `DELEGATE_LIST_ID` | `ingest-website` |
| YouTube | `YOUTUBE_URL`, `TASK_ID`, `DELEGATE_LIST_ID` | `ingest-youtube` |

### 3. Focused subagent context

Each subagent should **only load the skill relevant to its content type** to minimise context pollution from unrelated skills. The orchestrator categorises tasks first (Step 1), then creates per-type subagents that carry only the necessary skill context.

For example, a newsletter subagent should only have `ingest-newsletter` and `content-summary` references in its context — not `ingest-youtube`, `agent-browser`, `study-github-repo`, or any other unrelated skills.

The orchestrator is responsible for:
- Determining the content type of each item (already done in Step 1)
- Ensuring each subagent is scoped to the correct skill
- Passing only the metadata needed for that specific item (IDs, URLs, report directory, suggestion output path)

### 4. Orchestrator procedure for `daily-workflow/SKILL.md`

Replace Steps 2–5 with a unified dispatch-and-collect flow:

```markdown
### Step 2 — Pre-create report directories

Create date-stamped report directories **only for content types that have
items** (based on Step 1 classification), plus the suggestion staging area:

    mkdir -p data/suggestions_pending
    # For each non-empty queue:
    mkdir -p reports/Newsletter_YYYY_MM_DD   # only if unread newsletters exist
    mkdir -p reports/Threads_YYYY_MM_DD      # only if threads_queue is non-empty
    mkdir -p reports/Website_YYYY_MM_DD      # only if website_queue is non-empty
    mkdir -p reports/YouTube_YYYY_MM_DD      # only if youtube_queue is non-empty

### Step 3 — Dispatch all content items in parallel

If all queues are empty (no unread newsletters, no Delegate tasks),
skip Steps 3–7 and report: "No content to process today." Exit.

#### 3a — Newsletter subagents

Fetch unread newsletter email IDs in batches of 10 (matching the current
`ingest-newsletter` batch size):

    gws gmail users messages list \
      --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 10}'

For each message ID in the batch, spawn a focused subagent scoped to the
`ingest-newsletter` skill. Pass the `MESSAGE_ID` so the subagent processes
only this single email — skipping the batch discovery step and going
directly to the content processing steps (read email → summarise →
write report → suggestion → mark read + archive).

The subagent should write its suggestion to:
`data/suggestions_pending/suggestion_newsletter_<MESSAGE_ID>.json`

Do not wait for completion — continue dispatching immediately.

If `nextPageToken` is present in the response, fetch the next batch
and dispatch those as well. Repeat until all unread newsletters
are dispatched.

#### 3b — Threads subagents

For each task in `threads_queue`, spawn a focused subagent scoped to the
`ingest-threads` skill. Pass: URL, task ID, Delegate list ID, report
directory, suggestion output path.

#### 3c — Website subagents

For each task in `website_queue`, spawn a focused subagent scoped to the
`ingest-website` skill. Pass: URL, task ID, Delegate list ID, report
directory, suggestion output path.

#### 3d — YouTube subagents

For each task in `youtube_queue`, spawn a focused subagent scoped to the
`ingest-youtube` skill. Pass: URL, task ID, Delegate list ID, report
directory, suggestion output path.

### Step 4 — Collect all results

Wait for all subagents to complete, with a **30-minute global timeout**.
The system automatically notifies the orchestrator when each subagent
finishes — no polling loop needed.

If the timeout is reached and some subagents are still running:
- Proceed with the results from completed subagents
- Report timed-out subagents as failures in the final summary
- Timed-out subagents may still complete in the background — their
  reports will appear in the report directory but won't be included
  in today's distillation

For each completed subagent, record: success/failure, report path,
error message.

### Step 4M — Merge suggestions

Read all files in data/suggestions_pending/suggestion_*.json.
Append each suggestion to the main suggestion log.
Delete the pending files after successful merge.
```

### 5. Suggestion log concurrency

Multiple subagents run concurrently and must not write to the same file.

**Solution: Per-subagent suggestion files.**

Each subagent writes its suggestion to a unique file:

```
data/suggestions_pending/suggestion_<type>_<item_id>.json
```

After all subagents complete (Step 4M), the orchestrator merges all pending suggestions into the main suggestion log in a single-threaded pass.

**Changes required:**
- Modify `content-summary/references/suggestion_log.md` to accept an optional `SuggestionOutputPath` parameter. When provided, write to that path instead of the default location.
- The orchestrator passes the suggestion output path to each subagent.
- Add Step 4M (merge) to `daily-workflow/SKILL.md`.

### 6. Report directory safety

The orchestrator pre-creates all date-stamped report directories in Step 2 (before dispatch). This prevents race conditions where two subagents attempt to create the same directory simultaneously.

Each report has a unique filename derived from content (per `filename_rules.md`), so multiple subagents writing to the same directory is safe.

### 7. Crash safety via operation ordering

Each subagent executes in this order:

```
write report → write suggestion → mark source as done
```

| Crash point | Report exists? | Marked done? | Next run behavior |
|---|---|---|---|
| Before writing report | ❌ | ❌ | Source stays unread/incomplete → retried ✅ |
| After report, before mark done | ✅ | ❌ | Source stays unread → duplicate check skips ✅ |
| After mark done | ✅ | ✅ | Fully completed ✅ |

There is **no window** where a source is marked done without a report existing. This is the same safety guarantee as the current sequential model.

### 8. Error isolation

Each subagent operates independently. A Cloudflare 403 blocking one website does not affect newsletter processing. The orchestrator collects success/failure from each subagent and reports a unified summary.

| Failure | Impact | Handling |
|---|---|---|
| Single subagent fails | Other subagents unaffected | Orchestrator logs failure, continues |
| GWS auth expired | All subagents using GWS fail | Pre-flight check (Step 0) catches this before dispatch |

### 9. Distillation synchronisation barrier

[daily-distiller/SKILL.md](../../.agents/skills/daily-distiller/SKILL.md) requires ALL reports to exist before synthesising. The orchestrator waits for every subagent to complete (Step 4) before proceeding to distillation (Step 6).

### 10. Concurrency limits

No concurrency limits for now. Typical daily volume is 5–15 items. All subagents are dispatched simultaneously.

If rate-limiting or resource exhaustion is observed in practice, per-type limits can be added as a backward-compatible change without modifying the subagent design.

---

## Drawbacks

- **Subagent bootstrap overhead**: Each subagent reads the relevant skill files on startup. With 10 subagents, this is ~60 file reads total. This is a fixed cost per subagent that does not grow with content size and is offset by the wall-clock time savings. Focused subagent contexts (§3) mitigate this by loading only the relevant skill per type.
- **Harder to debug**: Failures in parallel subagents are less visible than sequential failures in the main agent's context. Mitigated by the orchestrator's unified summary in the Final Summary step.
- **Suggestion merge adds a step**: The per-subagent suggestion file + merge pattern adds a small step to the orchestrator. Minimal overhead.

## Alternatives Considered

- **Main agent fetches content, dispatches summary-only subagents**: The main agent reads each item's content via tool calls, then passes content inline to summary subagents. Rejected: the main agent's context accumulates all fetched content (~40,000+ words on heavy days), creating context window pressure and unnecessary token cost. Moving fetch into the subagent keeps the main agent's context empty.

- **Parallelise only within each content type (not across types)**: Process all newsletters in parallel, then all Threads in parallel, etc. Rejected: this still serialises across types. A website with a 4-step fallback chain (8 min) would block all Threads processing.

- **Use a task queue system (Redis, Celery)**: Over-engineered. The agent's built-in subagent mechanism provides adequate concurrency without external infrastructure.

- **Per-type concurrency limits with wave dispatch**: Adds orchestrator complexity (track completions, dispatch replacements). Premature optimisation for typical 5–15 item volumes. Can be added later if needed.

- **Unfocused subagents (`TypeName: "self"`)**: Each subagent inherits the full agent configuration including ~30 skill descriptions. Rejected: wastes context on unrelated skills. Focused per-type subagents load only the relevant skill, keeping context clean and reducing bootstrap overhead.

---

## Architecture Decision Records

### ADR-001: Full-lifecycle subagents over summary-only subagents

**Status**: Accepted  
**Date**: 2026-07-07  

**Context**: Could either have main agent fetch content and dispatch summary-only subagents, or have each subagent handle its full lifecycle (fetch → summarise → report → mark done).

**Decision**: Full-lifecycle subagents

**Consequences**: Good: Keeps main agent context completely clean (zero content pollution). The main agent only handles metadata (IDs, URLs). Scales to any number of items without context window pressure. | Bad: Increases subagent responsibility and initial bootstrap overhead per item. | Mitigations: Focused per-type subagent context loads only the relevant skill per content type. Summary-only subagents rejected because main agent content fetching accumulates ~40,000+ words of content in context on heavy days.

### ADR-002: Fire-and-forget dispatch with subagent-owned mark-done

**Status**: Accepted  
**Date**: 2026-07-07  

**Context**: Who marks the source as done — the subagent or the main agent after sync barrier?

**Decision**: Subagent marks done itself (fire-and-forget)

**Consequences**: Good: Crash safety is guaranteed by operation ordering: write report → write suggestion → mark done. No window exists where marked done but no report. | Bad: Main agent lacks central control over individual item completion state during execution. | Mitigations: Main agent marks done after collecting results rejected as it adds orchestrator complexity and coordination overhead.

### ADR-003: Focused per-type subagent context over inherited full config

**Status**: Accepted  
**Date**: 2026-07-07  

**Context**: Should subagents inherit full agent config (~30 skills) or be scoped to only the relevant skill?

**Decision**: Focused per-type subagents that load only the relevant skill

**Consequences**: Good: Minimises context pollution from unrelated skills. A newsletter subagent shouldn't have ingest-youtube or study-github-repo in its context. | Bad: Requires upfront categorisation of content types by the orchestrator. | Mitigations: TypeName 'self' rejected because inheriting all ~30 skill descriptions wastes context.

### ADR-004: No concurrency limits for initial release

**Status**: Accepted  
**Date**: 2026-07-07  

**Context**: Should per-type limits cap simultaneous subagents?

**Decision**: No limits — dispatch all at once

**Consequences**: Good: Typical daily volume is 5–15 items. Avoids premature optimization. Limits can be added as a backward-compatible change. | Bad: Risk of rate limits or system pressure during large volume spikes. | Mitigations: Per-type limits with wave dispatch rejected because it adds significant orchestrator complexity.

### ADR-005: Per-subagent suggestion files with orchestrator merge

**Status**: Accepted  
**Date**: 2026-07-07  

**Context**: How to handle concurrent suggestion writes from parallel subagents?

**Decision**: Each subagent writes to data/suggestions_pending/suggestion_<type>_<item_id>.json. Orchestrator merges after sync barrier.

**Consequences**: Good: Eliminates file write contention entirely. Mirrors established patterns. | Bad: Requires a single-threaded merge step in the orchestrator pipeline. | Mitigations: Shared suggestion log with concurrent appends rejected due to race condition risk.

### ADR-006: 30-minute global timeout at sync barrier

**Status**: Accepted  
**Date**: 2026-07-07  

**Context**: What if a subagent hangs indefinitely (e.g., yt2doc never finishes)?

**Decision**: 30-minute global timeout. After timeout, proceed with completed results; timed-out items reported as failures.

**Consequences**: Good: YouTube transcription typically takes 5–55 minutes. 30-minute window accommodates most videos while preventing indefinite hangs. | Bad: Timed-out items are excluded from today's distillation pass. | Mitigations: No timeout / wait indefinitely rejected because one hung subagent blocks entire pipeline. Timed-out subagents still save reports to disk.

### ADR-007: No suggestion file cleanup at startup

**Status**: Accepted  
**Date**: 2026-07-07  

**Context**: Orphaned suggestion files from previous timed-out runs could accumulate.

**Decision**: No cleanup. Orphaned files merge into the next run.

**Consequences**: Good: A late-arriving suggestion is better than a lost one. The interactive review step lets the user decide relevance. | Bad: Late-arriving suggestions appear in subsequent runs. | Mitigations: rm -f at startup rejected because it loses suggestions from subagents that completed after timeout.

---

## Scope Boundaries

This RFC does NOT change:
- Core logic of individual ingest skills (`ingest-threads`, `ingest-website`, `ingest-youtube`): Each skill's processing steps remain unchanged. Subagents follow the same skill instructions.
- The fallback chain behaviour for website ingestion (independent of the smart fallback routing RFC).
- `daily-distiller` or `review-suggestions`: These remain sequential and run after all parallel processing completes.
- The suggestion log schema or report output format.

This RFC DOES change:
- `daily-workflow/SKILL.md`: Orchestrator rewritten from sequential to parallel dispatch-and-collect.
- `ingest-newsletter/SKILL.md`: Add single-email mode — when a `MESSAGE_ID` is provided, skip the batch discovery step (Step 1) and process only that email. The existing batch-loop mode remains for standalone invocations.
- `content-summary/references/suggestion_log.md`: Add optional `SuggestionOutputPath` parameter.

---

## Implementation Plan

### Phase 1 — Skill changes
1. Add single-email mode to `ingest-newsletter/SKILL.md`: when `MESSAGE_ID` is provided, skip Step 1 (batch discovery) and go directly to Step 2 (process that single email)
2. Add `SuggestionOutputPath` parameter to `content-summary/references/suggestion_log.md`
3. Create `data/suggestions_pending/` directory
4. Verify: standalone skill invocations still work unchanged (batch newsletter, individual threads/website/youtube)

### Phase 2 — Orchestrator rewrite
1. Replace Steps 2–5 in `daily-workflow/SKILL.md` with the dispatch-and-collect flow (§4)
2. Add Step 4M (suggestion merge)
3. Add directory pre-creation in Step 2 (§6)

### Phase 3 — Verification
1. Run daily workflow with mixed content (newsletters + Threads + websites + YouTube)
2. Verify: all reports written correctly, suggestions merged, tasks marked done
3. Verify: wall-clock time reduction vs. sequential baseline
4. Verify: failure isolation — one failed subagent doesn't block others
5. Verify: main agent context stays clean (only metadata, no content)
6. Verify: each subagent loads only its relevant skill, not all skills
