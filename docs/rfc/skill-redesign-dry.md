# Skill Redesign Analysis: DRY Principle (v5)

## Design Decisions

### 1. Consistent naming: `ingest-*` family

All ingest skills follow the same naming convention:

| Old Name | New Name |
|---|---|
| `newsletter-summary` | `ingest-newsletter` |
| *(new)* | `ingest-threads` |
| *(new)* | `ingest-youtube` |

### 2. `process-delegate-tasks` → deprecated

The router logic (discover Delegate list → classify by URL) moves into `daily-workflow`. Processing logic splits into `ingest-threads` and `ingest-youtube`. The old skill is retired.

### 3. Who marks the data source as done?

**Principle: whoever initiates the processing marks the source as done.**

| Scenario | Who marks done | Why |
|---|---|---|
| User triggers `ingest-newsletter` standalone | `ingest-newsletter` | It owns the full lifecycle |
| User triggers `ingest-threads` standalone | `ingest-threads` | It owns the full lifecycle |
| User triggers `ingest-youtube` standalone | `ingest-youtube` | It owns the full lifecycle: launch → poll → summarise → mark done |
| `daily-workflow` runs newsletters | `ingest-newsletter` | Orchestrator delegates; skill runs its full lifecycle |
| `daily-workflow` runs Threads | `ingest-threads` | Same — full lifecycle delegation |
| `daily-workflow` runs YouTube | **`daily-workflow` itself** | See explanation below |

#### Why YouTube is different in the orchestrator

The orchestrator needs to interleave YouTube with other work:

```
Orchestrator timeline:
  t=0    Fire Docker for Video A (background shell process)
  t=0    Fire Docker for Video B (background shell process)
  t=1s   Run ingest-newsletter (full lifecycle, marks emails done) ✅
  t=30s  Run ingest-threads (full lifecycle, marks tasks done) ✅
  t=45s  Start polling Docker commands...
  t=12m  Video A ready → summarise → suggest → mark task done ← orchestrator does this
  t=38m  Video B ready → summarise → suggest → mark task done ← orchestrator does this
```

The orchestrator can't delegate a complete `ingest-youtube` invocation to the background — skills aren't separate processes. The "background" is the Docker shell command. So the orchestrator:

1. **Fires** the Docker transcription (background shell)
2. **Polls** until Docker completes
3. **Reads** the transcript
4. **Summarises** using `> 📄 Read ../content-summary/references/summarise.md`
5. **Analyses** using `> 📄 Read ../content-summary/references/ai_analysis.md`
6. **Appends suggestion** using `> 📄 Read ../content-summary/references/suggestion_log.md`
7. **Writes** the report using YouTube-specific template
8. **Marks the Google Task as completed** via `gws tasks tasks patch`

This is fine because `content-summary` references provide all the shared logic. The orchestrator just follows the references directly.

Meanwhile, `ingest-youtube` as a standalone skill does the same thing synchronously (launch → poll → summarise → mark done) for one-off requests.

---

## Final Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  daily-workflow (ORCHESTRATOR)                                       │
│  Trigger: "run my daily workflow"                                    │
│                                                                      │
│  1. Discover Delegate list → classify tasks by URL                   │
│  2. Fire Docker for YouTube tasks (background)                       │
│  3. Delegate to ingest-newsletter (full lifecycle, marks done)       │
│  4. Delegate to ingest-threads (full lifecycle, marks done)          │
│  5. Poll YouTube → summarise → suggest → mark done (self-handled)   │
│  6. Delegate to daily-distiller                                      │
│  7. Delegate to review-suggestions                                   │
└──────────────────────────────────────────────────────────────────────┘

      Each ingest skill is also independently triggerable:

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ ingest-      │  │ ingest-      │  │ ingest-      │
│ newsletter   │  │ threads      │  │ youtube      │
│              │  │              │  │              │
│ Fetch email  │  │ Fetch post   │  │ Launch yt2doc│
│ Summarise  ──┼──┼── refs ──────┼──┼── content-   │
│ AI Analysis──┼──┼── refs ──────┼──┼── summary/   │
│ Suggest    ──┼──┼── refs ──────┼──┼── references │
│ Write report │  │ Write report │  │ Write report │
│ Mark read  ✅│  │ Mark done  ✅│  │ Mark done  ✅│
└──────────────┘  └──────────────┘  └──────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │  content-summary             │
          │  (reference library)         │
          │                              │
          │  references/                 │
          │  ├── summarise.md            │
          │  ├── ai_analysis.md          │
          │  ├── suggestion_log.md       │
          │  └── filename_rules.md       │
          └──────────────────────────────┘
                         │
               produces: reports/ + data/
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
  ┌──────────────┐            ┌─────────────────┐
  │ daily-       │            │ review-         │
  │ distiller    │            │ suggestions     │
  └──────────────┘            └─────────────────┘
```

---

## Complete Skill Inventory

### Skills (7 total)

| # | Skill | Type | Trigger | Lines (est.) |
|---|---|---|---|---|
| 1 | `content-summary` | Reference library | Never directly | ~50 + 4 ref files |
| 2 | `ingest-newsletter` | Ingest (fast) | "幫我整理電子報" | ~70 |
| 3 | `ingest-threads` | Ingest (fast) | "process this Threads post" | ~80 |
| 4 | `ingest-youtube` | Ingest (slow) | "transcribe this YouTube video" | ~100 |
| 5 | `daily-distiller` | Post-process | "distill today's knowledge" | ~53 (unchanged) |
| 6 | `review-suggestions` | Post-process | "review my suggestions" | ~214 (unchanged) |
| 7 | `daily-workflow` | Orchestrator | "run my daily workflow" | ~80 |

### Deprecated

| Skill | Replacement |
|---|---|
| `process-delegate-tasks` | Router → `daily-workflow`; Threads → `ingest-threads`; YouTube → `ingest-youtube` |
| `newsletter-summary` | Renamed → `ingest-newsletter` |

### Unchanged

| Skill | Why |
|---|---|
| `daily-distiller` | Already DRY — consumes `reports/` |
| `review-suggestions` | Already DRY — consumes `data/` |
| `fetch-threads-post` | Low-level extraction — still delegated by `ingest-threads` |
| `yt2doc` | Low-level transcription — still delegated by `ingest-youtube` |

---

## `daily-workflow` Orchestrator (Detail)

```markdown
# daily-workflow

Chains the full content intelligence pipeline in optimal order.

## Procedure

### Step 1 — Discover and classify Delegate tasks
- Run `gws tasks tasklists list` → find "Delegate" list ID
- Fetch incomplete tasks
- Classify each by URL: threads_queue, youtube_queue, skipped

### Step 2 — Fire YouTube background jobs
For each YouTube task:
- Determine Whisper model (> 📄 Read ../ingest-youtube/SKILL.md §Video Strategist)
- Launch Docker transcription in background
- Store: { task_id, youtube_url, command_id, output_path }

### Step 3 — Process newsletters
> 📄 Follow ../ingest-newsletter/SKILL.md
(Full lifecycle: fetch → summarise → suggest → mark read)

### Step 4 — Process Threads tasks
For each task in threads_queue:
> 📄 Follow ../ingest-threads/SKILL.md
(Full lifecycle: fetch → summarise → suggest → mark task done)

### Step 5 — Complete YouTube tasks
For each YouTube background job:
1. Poll command_id until done
2. Read transcript output
3. Summarise (> 📄 Read ../content-summary/references/summarise.md)
4. AI Analysis (> 📄 Read ../content-summary/references/ai_analysis.md)
5. Write report using YouTube template (> 📄 Read ../ingest-youtube/assets/output_template.md)
6. Append suggestion (> 📄 Read ../content-summary/references/suggestion_log.md)
7. Mark Google Task as completed (`gws tasks tasks patch`)

### Step 6 — Distill
> 📄 Follow ../daily-distiller/SKILL.md

### Step 7 — Review suggestions
> 📄 Follow ../review-suggestions/SKILL.md

### Final Summary
Report: N newsletters, T threads, Y youtube (F failed), distillation, suggestions reviewed.
```

---

## Migration Path

| Step | Action | Risk |
|---|---|---|
| 1 | Create `content-summary/` with extracted reference files | None — additive |
| 2 | Create `ingest-threads/` and `ingest-youtube/` | None — additive |
| 3 | Rename `newsletter-summary/` → `ingest-newsletter/`, refactor to use references | Low — rename |
| 4 | Create `daily-workflow/` | None — additive |
| 5 | Deprecate `process-delegate-tasks/` (keep for 1 week, then delete) | Low |
| 6 | Verify: run `daily-workflow` end-to-end | Integration test |

---

# ADR: DRY Refactoring of Content Intelligence Pipeline

## Status

Accepted

## Context

Our content intelligence pipeline (`newsletter-summary`, `process-delegate-tasks`, `daily-distiller`, `review-suggestions`) organically grew with duplicated logic. The core summarization rules, AI analysis structure, suggestion logging logic, and file naming conventions were copy-pasted across multiple skills and output templates. This violation of the DRY principle made maintenance error-prone (e.g., adding a new analysis field required updating three separate templates). Additionally, combining fast, synchronous tasks (Threads) with slow, asynchronous tasks (YouTube transcription) within `process-delegate-tasks` led to architectural complexity and potential bottlenecks.

## Decision Drivers

- **Maintainability**: Need a single source of truth for the AI Analysis and summarization pipelines.
- **Modularity**: Skills should handle specific, bounded tasks without mixing different latency profiles.
- **Idempotency**: Ingestions need to handle failures gracefully with an "at-least-once" guarantee.
- **Workflow Orchestration**: Need a flexible way to run tasks independently or as part of a daily workflow sequence.

## Considered Options

### Option 1: Shared module folder (`_shared/`)
- **Pros**: Groups all common code centrally.
- **Cons**: Violates the existing skill loading convention (progressive disclosure via `SKILL.md` and `references/`). The skill creator framework has no concept of a "module" folder.

### Option 2: Extract shared logic into a formal reference skill (`content-summary`)
- **Pros**: Adheres to the established skill design pattern (e.g., `gws-shared`). Allows ingestion skills to use progressive disclosure by reading standard `references/` files.
- **Cons**: Creates an abstract skill that the user should never invoke directly.

### Option 3: Implement a central processing ledger for state tracking
- **Pros**: Guarantees exactly-once processing and robust retry states.
- **Cons**: Over-engineering. The current write-then-mark pattern already ensures at-least-once processing, which is sufficient for this context.

## Decision

We will extract the shared logic into a formal reference skill named `content-summary` and refactor the pipeline into distinct, single-purpose skills.

Specifically:
1. Create `content-summary` as a reference library holding `summarise.md`, `ai_analysis.md`, `suggestion_log.md`, and `filename_rules.md`.
2. Rename `newsletter-summary` to `ingest-newsletter` and use the shared references.
3. Split the deprecated `process-delegate-tasks` into `ingest-threads` (fast) and `ingest-youtube` (slow, async) to eliminate latency mixing.
4. Create a `daily-workflow` orchestrator skill to handle the chained execution of all ingest and post-processing skills while managing the async YouTube transcription lifecycle internally.

## Rationale

Using a formal `content-summary` reference skill perfectly aligns with the project's existing progressive disclosure mechanisms (`gws-shared`), ensuring proper agent loading and context management. Splitting the ingest skills strictly by latency ensures fast tasks don't get blocked by slow ones, simplifying individual skill logic. Relying on the orchestrator to handle the background processing loop, while letting standalone skills own their own lifecycle, maintains maximum flexibility.

## Consequences

### Positive
- Single source of truth for all content intelligence logic.
- Adding a new ingestion source now requires minimal code (~50 lines) because the entire summarization pipeline is externalized.
- Fast processing tasks are no longer blocked by heavy audio transcription jobs.

### Negative
- Adds two new skills and deprecates one, requiring a short migration/testing period.
- Orchestrator logic carries some minor complexity regarding background Docker process polling.

## Implementation Notes
- Use the standard `../content-summary/references/...` pattern for all cross-skill includes.
- Keep the `daily-distiller` and `review-suggestions` skills unchanged, as they already adhere to DRY by just consuming outputs.
