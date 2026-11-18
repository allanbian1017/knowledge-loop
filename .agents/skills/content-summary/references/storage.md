# Workspace and publication protocol

Read this before any report-producing or personal-state workflow, including standalone ingestion. Run from the Home Repo root. All skill files and shared helpers are included in this clone; no user-level companion skill is required.

## Resolve once

```bash
python3 scripts/check_setup.py --skill daily-workflow
python3 scripts/workspace_paths.py
```

For a standalone skill, select its name in the setup check. `KNOWLEDGE_LOOP_CONFIG` or `--config` must point to a JSON file **outside** this checkout. See [macOS setup](../../../../docs/setup.md). An absent or invalid configuration stops the affected workflow; never substitute the repository's seed data.

Read the returned `home_root`, `report_repository`, `report_root`, `personal_data_root`, `scratch_root`, `report_date`, `task_list`, and `newsletter_query`. Before writing across repositories, explicitly read the destination repository's `AGENTS.md`, if present. Verify the host has approved access to both output roots.

Pass `HomeRoot`, `ReportRoot`, `PersonalDataRoot`, `ScratchRoot`, and the fixed `ReportDate` to workers together with the existing input IDs and URLs. Workers stay rooted in `HomeRoot`. Preserve this date across midnight and retries.

Examples elsewhere using `reports/...` are paths relative to the **report repository**, not the Home Repo. Examples using `data/...` designate the configured **personal-data directory**. Resolve every read/write accordingly, including goals, language, preferences, blocklists, prompts and suggestion ledgers. Relative links are based on the file containing them. Never write personal state or reports into this public checkout.

Shell variables can be resolved without evaluating configuration as shell code:

```bash
ReportRoot="$(python3 scripts/workspace_paths.py --path report_root)"
PersonalDataRoot="$(python3 scripts/workspace_paths.py --path personal_data_root)"
ReportDate="$(python3 scripts/workspace_paths.py --path report_date)"
ScratchRoot="$(python3 scripts/workspace_paths.py --path scratch_root)"
```

Content-workflow examples elsewhere using `.tmp/...` are logical paths beneath ScratchRoot; resolve them before execution. Never put private captures in Home Repo scratch. Always quote resolved paths. Commands requiring a service use the skill's documented tool; no undocumented API or browser fallback is authorized by this protocol.

## Source identity and lookup

Use the Gmail message ID for newsletters, `task-list-ID:task-ID` for delegated URLs, and the supplied source URL for direct ingestion. A report date is YYYY-MM-DD. Never deduplicate different emails merely because their titles match.

```bash
python3 scripts/report_store.py lookup \
  --source-type Website --source-id '<STABLE_SOURCE_ID>' --date "$ReportDate"
```

A verified receipt reuses the existing report. Resume only unfinished suggestion grading or source acknowledgement; do not regenerate or append the suggestion again. A content mismatch stops processing for reconciliation.

## Stage, validate and publish

Generate candidate Markdown, raw captures, review artifacts and optional suggestion JSON beneath external `ScratchRoot/<skill>/<run>/`. ScratchRoot is the report repository’s ignored `.tmp/knowledge-loop/`, not the Home Repo. Keep raw browser captures and transcriptions here; they are not final reports. Follow the applicable content template before publishing. The helper checks title/body structure; the agent remains responsible for content accuracy, attribution, language and completeness.

```bash
python3 scripts/report_store.py publish \
  --source-type Website --source-id '<STABLE_SOURCE_ID>' --date "$ReportDate" \
  --input "$ScratchRoot/ingestion/run/candidate.md" \
  --path 'Website_YYYY_MM_DD/domain_title.md' \
  --suggestion "$ScratchRoot/ingestion/run/suggestion.json"
```

Replace the path's date with the fixed run date. `--path` is beneath `ReportRoot`, with no `reports/` prefix. Omit `--suggestion` for raw article/transcript utilities or publications with no generated suggestion. Suggestion JSON needs `title`, `source_url`, `category`, and `suggestion`; the helper binds its date, source type, report path and publication key. Existing additional fields remain supported.

The helper stages on the destination filesystem, records publication intent, atomically publishes and verifies bytes, then stages the suggestion in `PersonalDataRoot/suggestions_pending/`. It returns `absolute_path`, `report_link`, `key`, `graded`, and `acknowledged`. Use the returned relative `report_link` when formatting personal ledgers; do not construct an absolute or author-specific link.

Only after successful publication and suggestion staging may the documented source skill acknowledge its exact email/task. After verified API success record it:

```bash
python3 scripts/report_store.py acknowledged --key '<PUBLICATION_KEY>'
```

An API failure leaves the source open. An uncertain API outcome requires reading the exact source status before retrying. A Git failure is separate from storage: retain files and receipts, and report stored/uncommitted status. No Git operation is automatic.

## Grading and human review

The grader reads ungraded publication suggestions, scores them under the existing rubric, and writes one formatted `### ...` ledger entry to a external scratch file. Route through:

```bash
python3 scripts/report_store.py merge --key '<PUBLICATION_KEY>' \
  --ledger pending --entry "$ScratchRoot/grading/run/entry.md"
```

Use `filtered` for vetoes, low scores, and TAKEAWAY_ONLY. The helper serializes updates and adds an identity marker so replay cannot append twice, even after interruption between the ledger write and receipt update. Keep staged JSON for recovery; do not repeatedly grade completed receipts. Older staged JSON lacking a publication key remains a legacy input and needs a checked duplicate identity before one controlled merge.

Human Accept/Reject review is unchanged: only actual user feedback updates reviewed history and preferences. Acceptance does not implement the proposal or create an external issue.

## Revisions and daily selection

Normal ingestion replay is a no-op. Use `--revise` only for an explicitly requested ingestion revision. The previous bytes are archived under `reports/.revisions/`; the current filename is retained. A pending old suggestion must be graded before revision.

```bash
python3 scripts/report_store.py today-reports --date "$ReportDate"
```

Use this inventory immediately before synthesis. It selects date-stamped report directories and verified receipts, excludes distillations/revisions, and recognizes legacy GitHub Analysis Date fields. Filesystem modification time is not a report date. Undated legacy files need an explicit date decision before inclusion.

For distillation use source type `Distillation`, source ID equal to the report date, the existing `distillations/Knowledge_Distillation_YYYY_MM_DD.md` filename, no suggestion, and `--revise` when updating. Failed synthesis leaves the previous publication intact.

## Orchestration claim and recovery

Daily orchestration begins with `python3 scripts/report_store.py begin-run` and records the returned run ID/date. Finish with `python3 scripts/report_store.py finish-run --run-id '<RUN_ID>'` after all workers stop. An existing claim blocks a second producer. On interruption, inspect the original run and reconcile receipts before explicitly finishing that run ID; never expire or steal a claim automatically.

Preserve successful reports when another item fails. Surface failures and pending human review honestly. Cleanup requires the applicable user authorization and recoverable macOS Trash operations; never permanently delete existing data.
