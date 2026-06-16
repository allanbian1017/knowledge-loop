# Skill Plan: Ingest Website Integration

Integrate the `ingest-website` skill to process generic URLs in the "Delegate" Google Task list, leveraging the `web-to-markdown` skill. Update daily routing logic and shared templates, and add automated verification scripts.

---

## Proposed Changes

### 1. content-summary (Shared References)

#### [MODIFY] [filename_rules.md](.agents/skills/content-summary/references/filename_rules.md)
- Register `Website` as a valid `{SourceType}`.
- Document directory path structure: `reports/Website_YYYY_MM_DD/`.
- Add naming convention rule: `[domain]_[slugified_title].md`.

#### [MODIFY] [output_template.md](.agents/skills/content-summary/references/output_template.md)
- Register `Website` under the valid `來源類型` values.
- Document website-specific fields under `🔖 來源 Metadata` (Domain/Host, original URL, scraped date).
- Update the `📄 原始內容` guidelines to explicitly omit this section for `Website` reports.

#### [MODIFY] [suggestion_log.md](.agents/skills/content-summary/references/suggestion_log.md)
- Register `Website` as a valid source type in the log metadata line definition.

---

### 2. ingest-website (New Skill)

#### [NEW] [SKILL.md](.agents/skills/ingest-website/SKILL.md)
- Set frontmatter with `name: ingest-website` and appropriate description.
- Implement the step-by-step procedure:
  1. Fetch website Markdown from `https://r.jina.ai/<target_url>`.
  2. Implement soft-failure fallback: run `content-cleaner` skill if fetch fails.
  3. Generate Traditional Chinese summary based on `content-summary/references/summarise.md`.
  4. Write the report according to `content-summary/references/output_template.md`.
  5. Append a suggestion to `data/suggestions_pending.md` based on `content-summary/references/suggestion_log.md`.
  6. Mark the task completed in Google Tasks using `gws tasks tasks patch`.

#### [NEW] [README.md](.agents/skills/ingest-website/README.md)
- Add standard Overview, Problem Statement, Solution, File Structure, Dependencies, Triggering, and Output Location documentation.

---

### 3. daily-workflow (Orchestrator Integration)

#### [MODIFY] [SKILL.md](.agents/skills/daily-workflow/SKILL.md)
- Modify Step 1 routing table to include a generic website classification to `website_queue` for valid URLs that do not belong to Threads or YouTube.
- Add Step 4W to process `website_queue` tasks synchronously using `ingest-website` right after Threads tasks.
- Modify Step 5/6 Final Summary template to output the count and files created for Website tasks, as well as any soft failures.

#### [MODIFY] [README.md](.agents/skills/daily-workflow/README.md)
- Document the new website queue, synchronous execution sequence, and directory output locations.

---

### 4. Verification & Test Scripts

#### [NEW] [validate_website_report.py](scripts/validate_website_report.py)
- Create a Python quality scoring script that validates website report structural integrity.
- Ensures all headings and sections are present, `來源類型` is `Website`, and the raw content section is omitted.

#### [NEW] [test_website_routing.py](scripts/test_website_routing.py)
- Create a Python test suite that mocks a Google Task list API response and verifies task URLs are correctly routed to `threads_queue`, `youtube_queue`, and `website_queue` or skipped if no URL is present.

---

## Verification Plan

### Automated Tests

- **What to test**: Daily workflow routing logic.
  - **How to test**: Run `python3 scripts/test_website_routing.py`.
  - **Expected behavior**: The script validates that tasks are correctly split into Threads, YouTube, and Website queues based on their URLs.

- **What to test**: Website report structural template validation.
  - **How to test**: Run `python3 scripts/validate_website_report.py reports/Website_<date>/<filename>.md`.
  - **Expected behavior**: Returns exit code 0 if all expected 7-layer headings exist, `來源類型` is `Website`, and `## 📄 原始內容` is omitted. Returns error code if verification fails.

- **What to test**: Suggestion log appending.
  - **How to test**: Verify that running the ingest-website task appends a valid suggestion entry to `data/suggestions_pending.md`.
  - **Expected behavior**: A Markdown table row is appended with the `Website` source type and correct path.
