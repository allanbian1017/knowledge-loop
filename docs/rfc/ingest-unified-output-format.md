# RFC: Unified Output Format for Ingest Skills

## Summary

Standardise the Markdown report format across all three ingest skills (`ingest-newsletter`, `ingest-threads`, `ingest-youtube`) by moving the shared template into `content-summary/references/output_template.md` and removing the three per-skill `assets/output_template.md` files.

## Status

**Proposed** — 2026-05-14

## Motivation

The three ingest skills currently maintain separate output templates that are ~70% identical. The shared core sections (`## 來源`, `## 📝 核心總結`, `## 📌 關鍵重點`, `## 🚀 行動呼籲`, `## ⚠️ 資訊免責聲明`) are duplicated across three files. The divergences are:

| Aspect | Threads | YouTube | Newsletter |
|---|---|---|---|
| H1 title format | `@{handle} — {topic}` | `📹 {Title} — YouTube 影片摘要` | `[寄件者] - [標題]` |
| `來源` fields | author, url, timestamp, task\_id | url, whisper model, timestamp, task\_id | sender, subject, url |
| Action section name | `行動呼籲 / 延伸思考` | `行動呼籲 / 延伸思考` | `行動呼籲 / 期限` |
| `⚠️ Disclaimers` | ✅ | ❌ | ✅ |
| Raw content section | `📄 原始內容` | `📄 完整逐字稿` | ❌ |

These differences are not semantically meaningful — they are accidental divergence from the skills growing independently. Every time the shared structure needs updating (e.g., a new top-level section), it must be changed in three places.

Additionally, `content-summary` already centralises all other shared references (`summarise.md`, `ai_analysis.md`, `suggestion_log.md`, `filename_rules.md`). The output template is the only shared artefact still living outside it.

## Detailed Design

### Unified Template

A single `content-summary/references/output_template.md` file replaces all three per-skill templates:

```markdown
# {title}

## 來源
- **來源類型**: {Newsletter | Threads | YouTube}
- **作者 / 寄件者**: {author}       ← optional; omit if not applicable
- **原文連結**: {url}
- **處理時間**: {timestamp}
- **任務 ID**: {task_id}            ← optional; omit for Newsletter

## 🔖 來源 Metadata
{Each skill fills source-specific metadata here.}
- YouTube: Whisper Model, video duration
- Newsletter: sender email address, subject line
- Threads: engagement metrics (likes, replies, reposts)

## 📝 核心總結（Executive Summary）
- [1–3 句話精準概括主旨]

## 📌 關鍵重點（Key Highlights）
- **[主題分類 1]**: [詳細重點，必須包含原文具體細節]
- **[主題分類 2]**: [詳細重點]
- *(依此類推)*

## 🚀 行動呼籲 / 延伸思考（Action Items / Reflections）
- [若無則填「無」]

## ⚠️ 資訊免責聲明（Disclaimers）
- [若資訊完整清晰，此項可省略]

---

## 📄 原始內容（Raw Content）
- YouTube: verbatim yt2doc transcript, including TOC and all chapters
- Threads: verbatim extracted post content from fetch-threads-post
- Newsletter: plaintext-converted email body.
  If the email is HTML-only and cannot be meaningfully converted
  to plaintext, omit this section entirely.
```

### Key Decisions

**`🔖 來源 Metadata` section** — Replaces the bespoke `來源` fields that diverged across skills. Each skill populates this block with whatever source-specific metadata it holds. This keeps the unified template extensible without adding dead optional fields.

**`⚠️ 資訊免責聲明` normalised to all three** — YouTube reports can legitimately benefit from this section (e.g., flagging low audio quality that degraded transcription). The section is always present but can be omitted from the rendered output when there is nothing to report.

**`📄 原始內容` extends to Newsletter** — The `gws gmail +read` command returns the email body as plaintext (not HTML). Including it improves traceability and allows `daily-distiller` to reference the original source if needed. If a newsletter arrives as a HTML-only email with no plaintext part, the section is omitted.

**Action section name unified** — `行動呼籲 / 期限` (Newsletter) → `行動呼籲 / 延伸思考`. The `/ 期限` variant was an accident of the original Newsletter template and carries no semantic distinction in practice.

**No retroactive reformatting** — Existing reports (~50 dated directories) are left as-is. `daily-distiller` already handles mixed formats by reading section headings narratively rather than with rigid field parsing.

### File Changes

```
content-summary/
└── references/
    └── output_template.md          [NEW] unified template

ingest-newsletter/
├── SKILL.md                        [MODIFY] update reference pointer
└── assets/output_template.md       [DELETE]

ingest-threads/
├── SKILL.md                        [MODIFY] update reference pointer
└── assets/output_template.md       [DELETE]

ingest-youtube/
├── SKILL.md                        [MODIFY] update reference pointer
└── assets/output_template.md       [DELETE]
```

**SKILL.md change (identical for all three):**

```diff
-  > 📄 Read `assets/output_template.md`
+  > 📄 Read `../content-summary/references/output_template.md`
```

### Newsletter Plaintext Feasibility

`gws gmail +read` already returns the message body as decoded UTF-8 text. In practice, all newsletters processed to date have had plaintext bodies (the HTML part is stripped by the tool). The implementation note in the template ("omit if HTML-only") is a safety guard for edge cases, not the expected path.

## Drawbacks

- **Historical reports remain inconsistent** — Reports generated before this change will not have the `🔖 來源 Metadata` section or `📄 原始內容` for newsletters. This is accepted; the inconsistency only affects manual reading, not any automated consumer.
- **Template is slightly more verbose** — The `🔖 來源 Metadata` section adds a few lines to every report compared to the tightest current template (Newsletter). This is a minor tradeoff for a single maintainable template.

## Alternatives Considered

**Keep per-skill templates, extract only diverging sections** — This reduces the change surface but leaves three files to update for every future structural change. Rejected.

**Merge all `來源` fields into a flat list with optional markers** — Simpler than the `🔖 來源 Metadata` block, but produces visually inconsistent reports as some fields are present and others are blank. Rejected in favour of the flexible metadata section.

**Rename `📄 原始內容` differently per skill** — The old names (`完整逐字稿` for YouTube, `原始內容` for Threads) carried mild semantic distinction. Unified under `原始內容` for simplicity; the content of the section makes the distinction obvious.

## Unresolved Questions

None. All decisions are resolved.

## Implementation Plan

1. Create `content-summary/references/output_template.md` with the unified template.
2. Update `ingest-threads/SKILL.md` — change the reference pointer.
3. Update `ingest-youtube/SKILL.md` — change the reference pointer. Also update the `daily-workflow` reference in `daily-workflow/SKILL.md` (Step 5 references the YouTube per-skill template directly).
4. Update `ingest-newsletter/SKILL.md` — change the reference pointer.
5. Delete the three `assets/output_template.md` files.
6. Verify by running one report from each skill and confirming output structure matches the unified template.

---

# ADR: Unified Output Template for Content Intelligence Pipeline

## Status

Proposed

## Context

The `ingest-newsletter`, `ingest-threads`, and `ingest-youtube` skills each maintain a separate `assets/output_template.md` file. These templates share ~70% structure but diverged over time in field naming, section presence, and title format. The `content-summary` skill already centralises all other shared references for the pipeline. The output template is the sole outlier.

## Decision Drivers

- **Single source of truth**: Every other shared reference lives in `content-summary/references/`. The output template should too.
- **Extensibility**: Adding a new ingest source (e.g., `ingest-podcast`) must not require designing a new template from scratch.
- **Downstream consistency**: `daily-distiller` reads all ingest reports. Uniform headings improve reliability of insight extraction across sources.

## Considered Options

### Option 1: Unified template in `content-summary/references/`

- **Pros**: Follows existing `gws-shared` / `content-summary` precedent; single file to update; skills stay thin.
- **Cons**: Slightly less self-contained per skill (one more reference hop).

### Option 2: Per-skill templates with a shared base file

- **Pros**: Skills remain self-contained.
- **Cons**: Adds indirection without reducing duplication — the base file must still be read, and overrides must be managed. More files to maintain, not fewer.

### Option 3: No change

- **Pros**: Zero effort.
- **Cons**: Every structural template change requires three edits. Current divergence (missing `⚠️` in YouTube, no raw content in Newsletter) will compound over time.

## Decision

Adopt **Option 1**: move the unified template to `content-summary/references/output_template.md` and delete the three per-skill template files.

## Rationale

The `content-summary` reference library pattern is proven and already accepted by the pipeline (ADR in `docs/rfc/skill-redesign-dry.md`). Extending it with the output template is the most consistent choice. The `🔖 來源 Metadata` section design avoids the rigid optional-field problem while keeping each skill's report distinct without requiring separate templates.

## Consequences

### Positive
- One template to update for pipeline-wide structural changes.
- `daily-distiller` benefits from consistent headings across all three source types.
- New ingest skills can be built against a known, stable format with zero template design work.

### Negative
- Existing historical reports do not match the new format. Accepted — no automated consumer relies on rigid field-level parsing of historical reports.
- The `daily-workflow` orchestrator references `ingest-youtube/assets/output_template.md` directly in its Step 5; that reference must be updated alongside the skill changes.

## Implementation Notes

- The `gws gmail +read` command returns plaintext body — the Newsletter `📄 原始內容` addition is low-risk.
- Validate with one real run per skill before closing the task.
