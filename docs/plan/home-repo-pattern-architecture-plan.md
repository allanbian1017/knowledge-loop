# Implementation Plan - Adopt Home Repo Pattern (`knowledge-loop` Home Root + `<data-repo>` Data Repo)

Transform `knowledge-loop` into a public, portable, zero-PII **Home Root** repository containing the **20 approved agent skills** (18 `daily-workflow` pipeline skills + `evolution-log` + `review-newsletter-subscriptions`), 6 sub-agent personas, hooks, scripts, MCP servers, sanitized design docs/guidelines, and starter configuration examples, while refactoring `<data-repo>` into a clean private **Data Repo**.

For the detailed technical architecture, validated dependency closure, design trade-offs, and ADR, please refer to the corresponding RFC: [Adopt Home Repo Pattern](../rfc/home-repo-pattern-architecture.md).

## Confirmed Decisions

1. **Included Skills (20)**: All 18 `daily-workflow` skills + `evolution-log` + `review-newsletter-subscriptions`.
2. **Excluded Skills (9)**: `agent-rules-reviewer`, `ai-level-check`, `decision-sparring`, `log-task-evidence`, `skill-context-refactor`, `study-github-repo`, `sync-diary`, `tech-deconstructor`, `writing-style-technical-english` — retained privately in `<data-repo>/.agents/skills/`.
3. **Home Root Checkout Location**: Sibling directory `../knowledge-loop` (linked via gitignored `workspace.local.env` — zero absolute paths committed).
4. **`EvolutionLog.md`**: Excluded from `knowledge-loop`; existing personal `EvolutionLog.md` stays in `<data-repo>`.
5. **Docs Sign-Off**:
   - Exclude `knowledge-loop-core-sync.md` & `knowledge-loop-core-sync-plan.md` (**27 RFCs** + **28 plans** included).
   - Include all **24 RCAs** (sanitized).
   - Include `daily_workflow_deterministic_audit_2026-11-20.md` (sanitized).
6. **Git Workflow**: Work in dedicated **git worktrees** for both repositories, preserve previous commits (no history rewrite), and open PRs for both `knowledge-loop` and `<data-repo>` for review.

## User Review Required

> [!IMPORTANT]
> **Structural & Destructive Cutover (Tier 2 Approval Gate)**:
> Phase 5 removes the 20 migrated skills, personas (`.agents/agents/`, `.claude/`, `.codex/`), hooks, `mcp_servers/`, generic scripts/tests/docs, and `scripts/sync_knowledge_loop.py` from `<data-repo>` so `knowledge-loop` becomes the Single Source of Truth. Excluded skills remain intact in `<data-repo>/.agents/skills/`. No files will be deleted from `<data-repo>` until Phase 4 shadow verification passes and you explicitly approve cutover.

> [!WARNING]
> **Public Repository Git History Check**:
> Before pushing `knowledge-loop` to its public remote, inspect its existing Git log to verify whether earlier `sync_knowledge_loop.py` commits contain legacy `<HOME_DIR>` paths and confirm whether to squash/clean history or commit forward.

> [!NOTE]
> **Multi-Root Workspace & MCP Re-Pointing**:
> After cutover, open the multi-root workspace (`knowledge-loop` + `<data-repo>`) so macOS sandboxed tools can access both repos seamlessly, and update `~/.gemini/config/mcp_config.json` so `discord-reports` runs from `<HOME_REPO_ROOT>/mcp_servers/discord_reports` with `KNOWLEDGE_LOOP_DATA_REPO` pointing to your Data Repo.

## Open Questions

All open questions resolved and signed off (2026-11-26).

---

## Docs Classification Inventory (Complete Audit of `docs/`)

### `docs/rfc/` (38 files: 27 Include / 11 Exclude)

- **Include in `knowledge-loop/docs/rfc/` (27 files, sanitized)**:
  1. `3-tier-agent-rules-architecture.md`
  2. `agents-that-dream.md`
  3. `anti-cache-guardrails.md`
  4. `closed-loop-session-logging.md`
  5. `configurable-output-language.md`
  6. `content-summary-7-layers-of-learning.md`
  7. `content-summary-key-insight.md`
  8. `content-summary-reading-decision-first.md`
  9. `content-summary-subagent.md`
  10. `content-summary-thesis-driven-analysis.md`
  11. `content-summary-v5-reader-first.md`
  12. `content-summary-what-can-i-learn.md`
  13. `daily-workflow-discord-delivery.md`
  14. `daily-workflow-evals.md`
  15. `home-repo-pattern-architecture.md`
  16. `ingest-unified-output-format.md`
  17. `ingest-website-skill.md`
  18. `newsletter-subscription-rubric.md`
  19. `parallel-content-processing.md`
  20. `path-free-subagent-personas-and-sync.md`
  21. `report-quality-grader.md`
  22. `review-newsletter-subscriptions.md`
  23. `rss-workflow-integration.md`
  24. `rubric-grader.md`
  25. `simplify-session-logging-to-known-issues.md`
  26. `skill-redesign-dry.md`
  27. `smart-fallback-routing.md`

- **Exclude — Keep in `<data-repo>/docs/rfc/` (11 files)**:
  1. `add-hidden-architectural-flaws.md` *(for excluded `study-github-repo`)*
  2. `agent-rules-reviewer.md` *(for excluded `agent-rules-reviewer`)*
  3. `hourly-backlog-grooming-agent.md` *(personal Jira backlog grooming)*
  4. `jira-notion-github-actions-sync.md` *(personal Jira ↔ Notion sync)*
  5. `knowledge-loop-core-sync.md` *(retired legacy sync script)*
  6. `log-task-evidence.md` *(for excluded `log-task-evidence`)*
  7. `migrate-backlog-to-jira.md` *(personal `backlog.md` → Jira `AW` migration)*
  8. `mock-interview-simulator.md` *(personal career mock interview prep)*
  9. `skill-creator-quality-pillars.md` *(global `skill-creator`, outside `daily-workflow`)*
  10. `study-github-repo-skill.md` *(for excluded `study-github-repo`)*
  11. `sync-diary.md` *(for excluded `sync-diary`)*

### `docs/plan/` (42 files: 28 Include / 14 Exclude)

- **Include in `knowledge-loop/docs/plan/` (28 files, sanitized)**:
  1. `agents-that-dream-plan.md` & `agents-that-dream-task.md`
  2. `anti-cache-guardrails-plan.md`
  3. `closed-loop-session-logging-plan.md` & `closed-loop-session-logging-task.md`
  4. `configurable-output-language-plan.md`
  5. `content-summary-subagent-plan.md`
  6. `content-summary-thesis-driven-plan.md` & `content-summary-thesis-driven-task.md`
  7. `content-summary-v5-reader-first-plan.md`
  8. `content-summary-what-can-i-learn-plan.md` & `content-summary-what-can-i-learn-task.md`
  9. `daily-workflow-discord-delivery-plan.md`
  10. `daily-workflow-evals-plan.md`
  11. `evolution-log-audit-plan.md` *(for kept `evolution-log` skill)*
  12. `home-repo-pattern-architecture-plan.md`
  13. `ingest-website-plan.md`
  14. `newsletter-subscription-rubric-plan.md` *(for kept `review-newsletter-subscriptions` skill)*
  15. `parallel-content-processing-plan.md` & `parallel-content-processing-task.md`
  16. `path-free-subagent-personas-and-sync-plan.md` & `path-free-subagent-personas-and-sync-task.md`
  17. `report-quality-grader-plan.md` & `report-quality-grader-task.md`
  18. `rss-workflow-integration-plan.md`
  19. `rubric-grader-plan.md`
  20. `skill-redesign-plan.md` & `skill-redesign-task.md`

- **Exclude — Keep in `<data-repo>/docs/plan/` (14 files)**:
  1. `agent-rules-reviewer-plan.md` & `agent-rules-reviewer-task.md`
  2. `decision-sparring-skill-plan.md` & `decision-sparring-skill-task.md`
  3. `hourly-backlog-grooming-agent-plan.md`
  4. `jira-notion-github-actions-sync-plan.md` & `jira-notion-github-actions-sync-task.md`
  5. `knowledge-loop-core-sync-plan.md`
  6. `log-task-evidence.md`
  7. `migrate-backlog-to-jira-plan.md` & `migrate-backlog-to-jira-task.md`
  8. `mock-interview-simulator-plan.md`
  9. `skill-creator-quality-pillars-plan.md`
  10. `sync-diary.md`

### `docs/rca/` (24 files — Include All 24, Sanitized)

All 24 `daily-workflow`, `ingest-*`, `gws_shared`, `newsletter_summary`, and `yt2doc` RCAs are included and sanitized of local paths/PII.

### Guides, Templates & Other `docs/` Files

- **Include in `knowledge-loop/docs/`**:
  - `docs/guides/discord-mcp-setup-guide.md` (+ new `docs/guides/home-repo-setup-guide.md`)
  - `docs/templates/{plan,prd,rca,rfc}_template.md` (all 4)
  - `docs/cognitive_bandwidth_protection_guide.md`
  - `docs/loop_engineering_coverage_assessment.md` *(sanitized)*
  - `docs/daily_workflow_deterministic_audit_2026-11-20.md` *(sanitized)*
- **Exclude — Keep in `<data-repo>/docs/`**:
  - `docs/career_mock_interview_log.md`
  - `docs/archive/backlog_historical.md`
  - `docs/decisions/2026-09-04_kill_item_62_prompt_profiler.md`
  - `docs/figures/` *(empty directory)*

---

## Proposed Changes

### Phase 1: Home Root Bootstrap & Portable Path Infrastructure (`knowledge-loop`)

#### [NEW] `knowledge-loop/scripts/lib/workspace_paths.py`
* Shared zero-dependency Python module resolving `HOME_ROOT` and `DATA_REPO` via deterministic precedence:
  1. explicit `override` argument (`--data-repo`)
  2. `KNOWLEDGE_LOOP_DATA_REPO` environment variable (supports `~` and paths relative to `HOME_ROOT`)
  3. `DATA_REPO_DIR` key parsed from `<HOME_ROOT>/workspace.local.env`
  4. single-repo fallback (`HOME_ROOT` if `<HOME_ROOT>/data/` exists)
* Provides helper accessors: `data_dir()`, `reports_dir()`, `diary_dir()`, `tmp_dir()`.

#### [NEW] `knowledge-loop/scripts/lib/resolve_data_repo.sh`
* Portable Bash helper (macOS BSD-compatible, no GNU-only flags) implementing the exact same resolution precedence for shell hooks and scripts.

#### [NEW] `knowledge-loop/scripts/init_workspace.sh`
* Interactive / flag-driven macOS bootstrap script (`--data-repo <path>`, `--non-interactive`):
  * Copies `examples/workspace.local.env.example` → `workspace.local.env` (gitignored) and writes chosen `DATA_REPO_DIR`.
  * Copies `examples/repos.local.md.example` → `repos.local.md` (gitignored).
  * Optionally generates `knowledge-loop.code-workspace` (gitignored) from `examples/knowledge-loop.code-workspace.example`.
  * Scaffolds missing starter files from `examples/data/*` into `<DATA_REPO>/data/` **without overwriting** any existing files in the user's Data Repo.
  * Runs `uv sync --directory mcp_servers/discord_reports` (if `uv` is installed) and prints the exact `which uv` + `<HOME_REPO_ROOT>` / `<DATA_REPO_ROOT>` snippet for `mcp_config.json`.

#### [NEW] `knowledge-loop/examples/` (Starter Configuration Package)
* `examples/workspace.local.env.example` — `DATA_REPO_DIR="../my-knowledge-data"`, `USER_TIMEZONE="UTC"`.
* `examples/repos.local.md.example` — Home Repo pointer template listing `DATA_REPO` and optional additional code repositories.
* `examples/knowledge-loop.code-workspace.example` — Multi-root workspace config mounting `.` and `../my-knowledge-data`.
* `examples/mcp_config.example.json` — Generic MCP server setup for `discord-reports` with `KNOWLEDGE_LOOP_DATA_REPO` env var and placeholders.
* `examples/data/lang_preferences.md` — Default `English` / `English`.
* `examples/data/goals.md` — Generic developer goals template.
* `examples/data/user_preferences.md` — Starter calibration template.
* `examples/data/rubric_blocklist.md` — Starter topic & ambiguity blocklist template.
* `examples/data/suggestions_pending.md`, `suggestions_reviewed.md`, `suggestions_filtered.md` — Empty initialized headers.
* `examples/data/newsletter_aliases.example.json` — Sample newsletter source normalization map for `review-newsletter-subscriptions`.
* `examples/data/integrations.example.md` — Configurable Gmail newsletter label (`newsletter`), Google Tasks list name (`Delegate`), and optional Jira project/epic mapping.

#### [NEW / MODIFY] `knowledge-loop/{AGENTS.md,CLAUDE.md,CONTEXT.md,README.md,known_issues.md,.gitignore}`
* `AGENTS.md`: Rewritten for Home Repo Pattern — instructs agents to read `repos.local.md` (or `workspace.local.env`) to resolve `$DATA_REPO`, removes hardcoded Jira project `<PROJECT_KEY>` / `PROJ-1..PROJ-7` (delegating to optional `$DATA_REPO/data/integrations.md`), keeps 3-Tier Rules Architecture, skill validation, ADR, and language rules.
* `CLAUDE.md`: Pointer to `AGENTS.md` and `repos.local.md`.
* `CONTEXT.md`: Portable glossary (`Trace`, `Dreamer`, `Memory Injection`, `Home Root`, `Data Repo`).
* `README.md`: Public-facing architecture overview (Home Root + Data Repo diagram), macOS quickstart (`git clone` → `./scripts/init_workspace.sh` → multi-root workspace / MCP setup), full skill catalog, and verification commands.
* `known_issues.md`: Sanitized generic macOS/sandbox/CLI troubleshooting entries (replacing `~/.gitconfig` → `~/.gitconfig`, `<project-key>` → `<project-key>`, removing private session anecdotes).
* `.gitignore`: Ignores `workspace.local.env`, `repos.local.md`, `*.code-workspace`, `.tmp/`, `mcp_servers/discord_reports/.venv/`, `__pycache__/`, `.DS_Store`, `node_modules/`, and optional local `data/` / `reports/` / `diary/` (for single-repo trial users).

---

### Phase 2: Migrate & Parameterize the 20 Approved Skills, Personas, Hooks, Scripts & MCP Server (`knowledge-loop`)

#### [MIGRATE + MODIFY] `knowledge-loop/.agents/skills/` (20 Approved Skills)
* Migrate strictly the **20 approved skills**:
  * **Orchestrator (1)**: `daily-workflow`
  * **Ingestion (4)**: `ingest-newsletter`, `ingest-threads`, `ingest-website`, `ingest-youtube`
  * **Core Loop (5)**: `content-summary`, `rubric-grader`, `daily-distiller`, `deliver-discord-reports`, `review-suggestions`
  * **Extraction Helpers (4)**: `content-cleaner`, `fetch-threads-post`, `web-to-markdown`, `yt2doc`
  * **Companion Workflow Skills (2)**: `evolution-log`, `review-newsletter-subscriptions`
  * **External CLI Adapters (4 via `skills-lock.json`)**: `agent-browser`, `gws-gmail`, `gws-shared`, `gws-tasks`
* Update all data/report path references across `SKILL.md`, `references/`, `README.md`, and `evals/` from repo-local `./data/...` / `./reports/...` / `file://<HOME_DIR>` to `$DATA_REPO/data/...`, `$DATA_REPO/reports/...`, and repo-relative links:
  * **`rubric-grader`**: Replace all 19 `...` paths across `SKILL.md`, `README.md`, `references/rubric.md`.
  * **`review-newsletter-subscriptions`**: Update `scripts/analyze_subscriptions.py` to resolve `$DATA_REPO` via `workspace_paths.py` and load optional custom newsletter aliases from `$DATA_REPO/data/newsletter_aliases.json`.
  * **`evolution-log`**: Audit `SKILL.md`, `references/`, and `evals/evals.json` to ensure zero personal paths/names.
  * **`daily-workflow`, `ingest-*`, `content-summary`, `daily-distiller`, `review-suggestions`, `deliver-discord-reports`, `content-cleaner`, `web-to-markdown`, `yt2doc`**: Parameterize all data/report paths to `$DATA_REPO/...`; reference `$DATA_REPO/data/integrations.md` for configurable Gmail label / Google Tasks list name (retaining sensible defaults `newsletter` and `Delegate`).
  * Clean `skills-lock.json` to retain only the 4 `daily-workflow` external skills (`agent-browser`, `gws-gmail`, `gws-shared`, `gws-tasks`).
  * Update each modified skill's `README.md` with an ADR entry & Changelog note (per `AGENTS.md` Tier 1).

#### [MIGRATE + MODIFY] `knowledge-loop/.agents/agents/` + Synced Adapters
* Migrate all 6 persona files (`distiller_reviewer.md`, `newsletter_worker.md`, `rubric_grader.md`, `threads_worker.md`, `website_worker.md`, `youtube_worker.md`), updating `data/` and `reports/` pointers to `$DATA_REPO/...`.
* Run `python3 scripts/sync_subagents.py` to regenerate `.claude/{agents,subagents}/` and `.codex/{agents,subagents}/`.

#### [MIGRATE + MODIFY] `knowledge-loop/scripts/` & `.agents/settings.json`
* `scripts/hooks/ensure_lang_preferences.sh`: Source `scripts/lib/resolve_data_repo.sh` so auto-healing targets `${DATA_REPO}/data/lang_preferences.md` (and gracefully no-ops with a helpful stderr hint if `DATA_REPO` is not yet configured on a brand-new clone).
* `scripts/hooks/prevent_dangerous_commands.sh`: Migrate cleanly (verify macOS BSD shell compatibility).
* `scripts/validate_skill.py`: Remove hardcoded `../.gemini/config/skills/**/SKILL.md` relative parent assumption (scan `.agents/skills/**/SKILL.md` by default, with optional `--extra-dir` flag) so it behaves identically on any user's directory layout.
* `scripts/validate_language_config.py`: Resolve `LANG_PREF_FILE` via `workspace_paths.py` and verify `$DATA_REPO/data/lang_preferences.md` references in `content-summary/references/summarise.md` and `daily-distiller/SKILL.md` (remove `study-github-repo` check since that skill is excluded).
* `scripts/sync_subagents.py`: Migrate cleanly (already uses `Path(__file__).resolve().parent.parent`).
* `.agents/settings.json`: Migrate hooks configuration using repo-relative `./scripts/...` commands.

#### [MIGRATE + MODIFY] `knowledge-loop/mcp_servers/discord_reports/`
* Update `server.py` (`_publish_daily_reports_impl`, `_send_report_file_impl`, `_delivery_status_impl`) to resolve the data root via `workspace_paths.resolve_data_repo()` (`KNOWLEDGE_LOOP_DATA_REPO` env var → `workspace.local.env` → fallback to `DEFAULT_REPO_ROOT`).
* Verify `formatter.py`, `publisher.py`, `table_renderer.py`, and `pyproject.toml` contain zero hardcoded paths or personal references.

---

### Phase 3: Migrate & Sanitize Design Docs & Guidelines (`knowledge-loop/docs/`)

#### [MIGRATE + SANITIZE] `knowledge-loop/docs/`
* Migrate `docs/templates/*`, `docs/figures/*`, `docs/cognitive_bandwidth_protection_guide.md`, `docs/loop_engineering_coverage_assessment.md`.
* Migrate and sanitize `docs/rfc/*`, `docs/plan/*`, `docs/rca/*` (excluding personal-only docs per Open Question #3):
  * Replace all `<DATA_REPO>/...` and `file://<HOME_DIR>` paths with relative workspace links or `<REPO_ROOT>` / `<DATA_REPO>` placeholders.
  * Redact personal usernames, private Notion IDs, personal Jira keys (`AW-*`), and real email/report filenames where needed.
  * Update `docs/guides/discord-mcp-setup-guide.md` to reference `<HOME_REPO_ROOT>`, `<DATA_REPO_ROOT>`, and `KNOWLEDGE_LOOP_DATA_REPO`.
* **[NEW]** `knowledge-loop/docs/guides/home-repo-setup-guide.md`: Step-by-step macOS onboarding guide covering cloning `knowledge-loop`, creating/linking a private Data Repo, running `scripts/init_workspace.sh`, setting up multi-root workspace / `--add-dir`, configuring `gws` / `yt2doc` / Discord MCP / Notion MCP, and running verification checks.

---

### Phase 4: Automated Privacy, Portability & Regression Gate (`knowledge-loop`)

#### [NEW] `knowledge-loop/scripts/audit_public_repo.py`
* Zero-dependency audit script scanning all git-tracked (or workspace non-ignored) text files for:
  * Absolute local paths (machine-specific home directories (macOS, Linux, Windows, and local `file://` URIs))
  * Personal identifiers (`<user>`, `<data-repo>`, `PaymentService`, `OrderService`, personal Jira keys `AW-\d+`)
  * Private Notion IDs (`3cd60ab2`, `34260ab2`, `3a8f3775`), live Discord webhooks, secret tokens (`sk-`, `ghp_`, `ntn_`, `ATATT`)
  * Broken internal relative Markdown links
* Exits non-zero with exact `file:line:rule` diagnostics on any violation.

#### [NEW] `knowledge-loop/tests/test_public_repo_hygiene.py` & `tests/test_workspace_resolution.py`
* `test_public_repo_hygiene.py`: Runs `audit_public_repo.py` against the entire `knowledge-loop` repo, verifies all 20 skills pass `validate_skill.py`, and verifies `sync_subagents.py` produces zero drift.
* `test_workspace_resolution.py`: Tests all 4 resolution precedence levels (`--data-repo`, `KNOWLEDGE_LOOP_DATA_REPO`, `workspace.local.env`, single-repo fallback), `~` expansion, relative paths, missing-config fail-fast, `ensure_lang_preferences.sh` targeting an arbitrary `tmp_path` Data Repo, and `init_workspace.sh` non-destructive scaffolding.

#### [MIGRATE + UPDATE] `knowledge-loop/tests/`
* Migrate `test_discord_reports.py` (update to test `KNOWLEDGE_LOOP_DATA_REPO` resolution & remove `<data-repo>` string), `test_newsletter_subscription_reviewer.py`, `test_output_template.py`, `test_suggestion_archetypes.py`, `test_suggestion_payload_schema.py`.
* Omit tests belonging to excluded/personal/retired items (`test_agent_rules_reviewer.py`, `test_compile_session_learnings.py`, `test_jira_*.py`, `test_sync_diary.py`, `test_sync_knowledge_loop.py`).

#### [NEW] `knowledge-loop/.github/workflows/ci.yml`
* Runs `audit_public_repo.py`, `validate_skill.py`, `sync_subagents.py --check`, and `pytest -p no:recording` on macOS/Ubuntu runners on every push and PR.

---

### Phase 5: Convert `<data-repo>` into Clean Private Data Repo (After Phase 4 Shadow Verification)

#### [NEW] Private Config Files in `<data-repo>/data/`
* `data/integrations.md` — Personal Jira project (`AW`, Epics `PROJ-1`–`PROJ-7`), Gmail label (`newsletter`), and Google Tasks list (`Delegate`).
* `data/newsletter_aliases.json` — Moved personal newsletter alias normalization map from `analyze_subscriptions.py`.

#### [MODIFY] `<data-repo>/{AGENTS.md,CLAUDE.md,README.md,.gitignore}`
* `AGENTS.md` / `CLAUDE.md`: Slim Data Repo instructions pointing agents to `knowledge-loop` as the Home Root for the 20 core skills, hooks, scripts, and engineering rules, plus Data Repo hygiene rules (no credentials, data/report layout).
* `README.md`: Updated to describe `<data-repo>` as the private Data Repo paired with `knowledge-loop`.

#### [DELETE] Retired Duplicated Infrastructure from `<data-repo>`
* Remove only the **20 migrated skills** from `.agents/skills/` — **retain the 9 excluded skills** (`agent-rules-reviewer`, `decision-sparring`, `log-task-evidence`, `skill-context-refactor`, `study-github-repo`, `sync-diary`, `tech-deconstructor`, `writing-style-technical-english`, plus empty `ai-level-check` if desired) in `<data-repo>/.agents/skills/`. Remove `.agents/agents/`, `.claude/`, `.codex/`, `.agents/settings.json`, `skills-lock.json`.
* Remove `mcp_servers/discord_reports/` (now owned exclusively by `knowledge-loop`).
* Remove `scripts/sync_knowledge_loop.py`, `scripts/sync_knowledge_loop.md`, `scripts/sync_subagents.py`, `scripts/validate_skill.py`, `scripts/validate_language_config.py`, `scripts/hooks/` (keep `scripts/jira_migration/` privately as historical archive).
* Remove migrated tests (`test_sync_knowledge_loop.py`, `test_discord_reports.py`, `test_newsletter_subscription_reviewer.py`, `test_output_template.py`, `test_suggestion_archetypes.py`, `test_suggestion_payload_schema.py`) and migrated docs listed in `Docs Classification Inventory` above — **retaining** excluded RFCs/plans, `EvolutionLog.md`, `docs/career_mock_interview_log.md`, `docs/archive/backlog_historical.md`, `docs/decisions/`, `data/`, `reports/`, `diary/`, `raw/`.

---

## Verification Plan

### Automated Tests

- **What to test**: Zero PII, zero absolute paths, zero private IDs/credentials, and zero broken internal links in `knowledge-loop`.
  - **How to test**: `python3 scripts/audit_public_repo.py` (run from `knowledge-loop` root)
  - **Expected behavior**: Exit code `0`, `0 violations found` across all tracked files.

- **What to test**: All 20 migrated skills have valid YAML frontmatter and sub-agent persona adapters are synchronized.
  - **How to test**: `python3 scripts/validate_skill.py && python3 scripts/sync_subagents.py`
  - **Expected behavior**: Exit code `0`, all 20 `SKILL.md` files pass and `.claude/` / `.codex/` files are cleanly generated with no unexpected diff.

- **What to test**: Full portability of workspace path resolution, hooks, language validator, subscription analyzer, and Discord MCP server against an arbitrary temporary Data Repo (simulating another user on another Mac).
  - **How to test**: `python3 -m pytest -p no:recording tests/ -v` (run from `knowledge-loop` root)
  - **Expected behavior**: Exit code `0`, all unit, hygiene, portability, Discord MCP, subscription analyzer, output template, and suggestion schema tests pass without touching the real `<data-repo>` repo.

- **What to test**: Bootstrap script (`init_workspace.sh`) initializes a fresh temporary Data Repo and never overwrites existing user data on reruns.
  - **How to test**: Covered inside `tests/test_workspace_resolution.py` using `tmp_path`.
  - **Expected behavior**: Fresh directory receives all `examples/data/*` templates; modified existing files remain byte-identical on rerun.

### Manual Verification (Shadow Cutover & End-to-End Check)

1. Point `knowledge-loop/workspace.local.env` (gitignored) to `DATA_REPO_DIR="../<data-repo>"` and run `python3 scripts/validate_language_config.py` from `knowledge-loop` → verify it reads `<data-repo>/data/lang_preferences.md`.
2. Update `~/.gemini/config/mcp_config.json` to run `discord-reports` from `<HOME_REPO_ROOT>/mcp_servers/discord_reports` with `KNOWLEDGE_LOOP_DATA_REPO="<DATA_REPO_ROOT>"`, restart/refresh MCP, and run `discord_publish_daily_reports(dry_run=True)` → verify it discovers reports in `<data-repo>/reports/` without error.
3. Open the multi-root workspace (`knowledge-loop` + `<data-repo>`) in Antigravity, verify all 20 core skills are discovered from `knowledge-loop` (and retained private skills from `<data-repo>`), and run a read-only check confirming `$DATA_REPO/data/` resolves cleanly.
4. Run `git status` and `git diff` in `knowledge-loop` to confirm `workspace.local.env`, `repos.local.md`, and `*.code-workspace` are ignored and never staged.
