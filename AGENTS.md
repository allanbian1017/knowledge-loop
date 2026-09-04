# AGENTS.md

## Project
Personal AI workflow orchestrating daily productivity, research ingestion, and task automation.

---

## Tier 1: Always Do (Safe Defaults & Autonomous Automation)
- **Automated Verification**: Verify all code and script changes with automated tests before completion (`What to test`, `How to test`, `Expected behavior`). Pure documentation, markdown notes, and backlog updates are exempt from code-level test harnesses.
- **Skill Validation**: Run `python3 scripts/validate_skill.py <path/to/SKILL.md>` on every new or modified skill before completion.
- **Skill Documentation & ADRs**: Always create or update the skill's `README.md` whenever an agent skill is created or modified. The `README.md` must include Architecture Decision Records (ADRs) documenting design rationale/trade-offs and an updated Changelog.
- **Repository Registry & Hygiene**:
  - Check `known_issues.md` at session start; append newly encountered environment failures and workarounds using `- **[Context]**: [What failed] — [Why] → [Workaround]`.
  - Maintain all enhancements, tech debt, and ideas in the unified `backlog.md`, merging overlapping items.
  - Scan destination directories to identify and skip duplicates before batch data generation.
  - Stage all intermediate caches, temporary logs, and scratch scripts in `.tmp/`.
- **Minimal Code Scope**: Make minimal necessary changes. Match existing style, preserve untouched adjacent code, and clean up orphan variables/imports created by your own changes.
- **Documentation & Language Standards**:
  - Sync implementation plans and tasks to `docs/rfc/` (using `docs/templates/rfc_template.md`) and `docs/plan/` (using `docs/templates/plan_template.md`).
  - Language settings are configured in `data/lang_preferences.md`. Use Preferred Conversation Language for all internal docs (RCAs, plans, RFCs) and conversation. Use Preferred Report Language strictly for external content summaries.
  - Use relative workspace links in committed repository documents (`docs/`, `reports/`, `backlog.md`) rather than machine-specific local absolute paths.

---

## Tier 2: Ask First (Human-in-the-Loop & Approval Gates)
- **Issue Resolution (RCA)**: For user-reported bugs, pipeline failures, or regressions in existing functionality, document root causes with quantitative evidence in `docs/rca/<workflow_name>_rca_<YYYY-MM-DD>_V<version>.md` (linking to affected skill) with a proposed fix and automated verification method. **Stop and obtain user approval before implementing the fix.** (Iterative test failures during active development do not trigger an RCA).
- **Ambiguity & Trade-offs**: When requirements are underspecified or multiple viable approaches exist, surface trade-offs and clarify assumptions before writing code.
- **Destructive or Structural Changes**: Obtain confirmation before deleting pre-existing code, altering database schemas, or modifying core agent steering contracts.

---

## Tier 3: Never Do (Hard Invariants & Inviolable Boundaries)
- **Tool Circumvention (Fail-Fast)**: Never bypass documented tools in a skill (`SKILL.md`) with ad-hoc scripts, unauthorized fallbacks, or alternative APIs. Stop and report tool failures immediately for user intervention.
- **Manual Testing Proposals**: Never propose manual testing when automated verification is feasible for code changes.
- **Credential Exposure**: Never log, print, or commit raw credentials, tokens, or API keys. Use environment variables or keychain helpers.
- **Scope Creep**: Never add unrequested features, speculative abstractions, or unrequested refactoring outside the defined scope.


