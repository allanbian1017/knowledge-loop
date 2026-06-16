# Skill Plan: Configurable Output Language Integration

Integrate output language configurability across all summaries, daily distillations, and GitHub repository studies. Update shared references and individual skills, and add an automated python validation script.

---

## Proposed Changes

### 1. Configuration & Preferences

#### [MODIFY] [user_preferences.md](../../data/user_preferences.md)
- Add a new `## Configuration` section at the top of the file:
  ```markdown
  ## Configuration
  - **Preferred Output Language**: Traditional Chinese（繁體中文）
  ```

---

### 2. content-summary (Shared References)

#### [MODIFY] [summarise.md](../../.agents/skills/content-summary/references/summarise.md)
- Update `## Language` section to instruct the agent to check `data/user_preferences.md` for `Preferred Output Language` configuration.
- Instruct the agent to translate and write all report headers and summaries in the configured language.
- Default to **English** if the configuration is missing or not set.

---

### 3. Ingest Skills (Individual Rules)

#### [MODIFY] [SKILL.md (ingest-newsletter)](../../.agents/skills/ingest-newsletter/SKILL.md)
- Replace references to "Traditional Chinese summary" with "configured output language summary".

#### [MODIFY] [SKILL.md (ingest-threads)](../../.agents/skills/ingest-threads/SKILL.md)
- Replace references to "Traditional Chinese summary" with "configured output language summary".

#### [MODIFY] [SKILL.md (ingest-website)](../../.agents/skills/ingest-website/SKILL.md)
- Replace references to "Traditional Chinese summary" with "configured output language summary".

#### [MODIFY] [SKILL.md (ingest-youtube)](../../.agents/skills/ingest-youtube/SKILL.md)
- Replace references to "Traditional Chinese summary" with "configured output language summary".

---

### 4. Daily Distiller

#### [MODIFY] [SKILL.md (daily-distiller)](../../.agents/skills/daily-distiller/SKILL.md)
- Add instructions in the synthesis steps to check `data/user_preferences.md` and generate the daily distillation document in the configured language.

---

### 5. GitHub Repository Study

#### [MODIFY] [SKILL.md (study-github-repo)](../../.agents/skills/study-github-repo/SKILL.md)
- Update Step 7 (Write Report) to check `data/user_preferences.md` and write the study report sections/metadata in the configured language.

---

### 6. Verification & Test Scripts

#### [NEW] [validate_language_config.py](../../scripts/validate_language_config.py)
- Create a Python script to validate the configurable language setup.
- Checks:
  1. The preferred output language is parseable from `data/user_preferences.md`.
  2. `content-summary/references/summarise.md` contains instructions to check `data/user_preferences.md`.
  3. `daily-distiller/SKILL.md` contains instructions to check the configured language.
  4. `study-github-repo/SKILL.md` contains instructions to check the configured language.
  5. The `ingest-*` skills do not contain hardcoded Traditional Chinese instructions in their step procedures.

---

## Verification Plan

### Automated Tests

- **What to test**: Validation of the language configuration setup across reference files and skills.
  - **How to test**: Run `python3 scripts/validate_language_config.py`.
  - **Expected behavior**: The script parses `data/user_preferences.md` successfully, asserts that the necessary instructions exist in `summarise.md`, `daily-distiller/SKILL.md`, `study-github-repo/SKILL.md`, and that no hardcoded language rules remain in `ingest-*` skills. Returns exit code 0.
