# Skill Redesign: DRY Refactoring of Content Intelligence Pipeline

Refactor four content intelligence skills to eliminate duplication by extracting shared logic into a `content-summary` reference library, splitting `process-delegate-tasks` by latency into `ingest-threads` + `ingest-youtube`, renaming `newsletter-summary` → `ingest-newsletter`, and adding a `daily-workflow` orchestrator.

## Proposed Changes

### 1. content-summary (Reference Library)

#### [NEW] [SKILL.md](../.agents/skills/content-summary/SKILL.md)
- Frontmatter: name, description ("Do not invoke directly")
- Body: Brief index of reference files and when to read them

#### [NEW] [references/summarise.md](../.agents/skills/content-summary/references/summarise.md)
- Extract from: `newsletter-summary/SKILL.md` §2-2 + `process-delegate-tasks/SKILL.md` §5T
- Content: Zero Hallucination, Comprehensiveness, Objectivity, TC language, Teaser Detection

#### [NEW] [references/ai_analysis.md](../.agents/skills/content-summary/references/ai_analysis.md)
- Extract from: all 3 `output_template.md` files (the 🏷️ AI 分析 block)
- Content: `data/goals.md` read instruction, `data/user_preferences.md` calibration, field definitions, template

#### [NEW] [references/suggestion_log.md](../.agents/skills/content-summary/references/suggestion_log.md)
- Extract from: Steps 6Tb, 6Yb, 2-4b
- Content: Append format, create-if-missing, file path

#### [NEW] [references/filename_rules.md](../.agents/skills/content-summary/references/filename_rules.md)
- Extract from: both output templates
- Content: Sanitisation rules, date-based directory convention

---

### 2. ingest-newsletter (Refactored from newsletter-summary)

#### [MODIFY] [SKILL.md](../.agents/skills/newsletter-summary/SKILL.md)
- Rename directory: `newsletter-summary/` → `ingest-newsletter/`
- Update frontmatter name
- Replace §2-2 summary rules → `> 📄 Read ../content-summary/references/summarise.md`
- Replace AI analysis in output template → `> 📄 Read ../content-summary/references/ai_analysis.md`
- Replace §2-4b → `> 📄 Follow ../content-summary/references/suggestion_log.md`

#### [MODIFY] [assets/output_template.md](../.agents/skills/newsletter-summary/assets/output_template.md)
- Remove the AI 分析 block (26 lines) → replace with reference pointer
- Keep newsletter-specific fields (來源, headline, 檔案命名規則)

---

### 3. ingest-threads (New, extracted from process-delegate-tasks)

#### [NEW] [SKILL.md](../.agents/skills/ingest-threads/SKILL.md)
- Extract from: `process-delegate-tasks/SKILL.md` Steps 4T–7T + Anti-Truncation
- References `content-summary` for summarise/analysis/suggestion
- Includes mark-task-done lifecycle

#### [NEW] [assets/output_template.md](../.agents/skills/ingest-threads/assets/output_template.md)
- Extract: Threads-specific report template from `process-delegate-tasks/assets/output_template.md`
- AI 分析 block → reference pointer to `content-summary`

---

### 4. ingest-youtube (New, extracted from process-delegate-tasks)

#### [NEW] [SKILL.md](../.agents/skills/ingest-youtube/SKILL.md)
- Extract from: `process-delegate-tasks/SKILL.md` Steps 4Y–7Y + Troubleshooting
- References `content-summary` for summarise/analysis/suggestion
- Includes mark-task-done lifecycle
- Includes Video Strategist table

#### [NEW] [assets/output_template.md](../.agents/skills/ingest-youtube/assets/output_template.md)
- Extract: YouTube-specific report template from `process-delegate-tasks/assets/output_template.md`
- AI 分析 block → reference pointer to `content-summary`

---

### 5. daily-workflow (New orchestrator)

#### [NEW] [SKILL.md](../.agents/skills/daily-workflow/SKILL.md)
- Absorbs router logic from `process-delegate-tasks` (Steps 1–3)
- Chains: fire YouTube → ingest-newsletter → ingest-threads → poll YouTube → daily-distiller → review-suggestions
- YouTube post-processing done by orchestrator using `content-summary` references

---

### 6. Deprecation

#### [DELETE] [process-delegate-tasks/](../.agents/skills/process-delegate-tasks/)
- Router logic → `daily-workflow`
- Threads processing → `ingest-threads`
- YouTube processing → `ingest-youtube`
- Shared logic → `content-summary`

---

## Verification Plan

### Automated Tests
1. Verify all new skill files exist and have valid YAML frontmatter
2. Verify all `> 📄 Read ../` references point to files that exist
3. Verify `process-delegate-tasks` is removed
4. Verify `newsletter-summary` is renamed to `ingest-newsletter`
5. Grep: no remaining duplicated AI 分析 blocks outside `content-summary`
