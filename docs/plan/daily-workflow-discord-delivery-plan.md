# Implementation Plan - Daily Workflow Discord Report Delivery

Execute this plan to build the local Python MCP server (`mcp_servers/discord_reports/`), standalone `deliver-discord-reports` skill, automatic fail-soft Step 6 integration in `daily-workflow`, and full offline `pytest` verification suite.

For the full MCP survey, PRD, detailed Acceptance Criteria (`AC-1`–`AC-13`), and ADR, see: [Daily Workflow Discord Report Delivery RFC](../rfc/daily-workflow-discord-delivery.md).

## User Review Required

> [!NOTE]
> **Approved & Ready for `/goal` Execution (2026-11-25)**
> - **MCP**: Custom local Python Webhook MCP (`mcp_servers/discord_reports/`), push-only `.md` report delivery (no two-way chat).
> - **Channel**: Discord **Forum channel** (`DISCORD_CHANNEL_TYPE=forum` default; `text` fallback supported).
> - **Default Payload**: `mode="per_report"` + **`include_source_files=True`** (1 dedicated Forum post per individual source report with full rendered content + `.md` attached, followed by the top `📰 Daily Digest — YYYY-MM-DD` Forum post; also supports `digest`, `distillation_only`, `full`).
> - **Trigger**: Automatic **fail-soft Step 6** in `daily-workflow` + standalone `deliver-discord-reports` skill.

## Open Questions

- None. All decisions are locked in; use this plan + RFC AC-1..AC-13 directly with `/goal`.

---

## Execution Order & Proposed Changes

### Phase 1 — Local Discord MCP Server (`mcp_servers/discord_reports/`)

#### [NEW] [pyproject.toml](../../mcp_servers/discord_reports/pyproject.toml)
* Define package metadata (`requires-python = ">=3.10"`, dependencies: `mcp>=1.0.0`, `httpx>=0.27.0`) runnable via `uv run --directory mcp_servers/discord_reports python server.py`.

#### [NEW] [formatter.py](../../mcp_servers/discord_reports/formatter.py)
* Implement AC-1, AC-2, AC-3, AC-4, AC-5:
  * `discover_daily_reports(repo_root, date)` — locates distillation + sorted `Newsletter_`/`Threads_`/`Website_`/`YouTube_` `.md` files.
  * `parse_distillation(md_text)` & `parse_source_report(md_text)` — v5.0 Answer-First parser + graceful legacy fallback.
  * `sanitize_for_discord(md_text)` — converts GFM tables to bullet lines, strips `<details>/<summary>/<b>` tags into headings, strips/replaces relative workspace links, strips `mermaid` blocks from Embed descriptions.
  * `build_delivery_plan(reports, mode, include_source_files, channel_type)` — produces ordered Discord message payloads enforcing all Discord API limits (`content ≤ 2,000` [target `1,900`], `embed.title ≤ 256`, `embed.description ≤ 4,096`, `field.value ≤ 1,024`, `total embed chars ≤ 6,000`, `thread_name ≤ 100`, attachments `≤ 10 files` & `≤ 8 MB` per batch).

#### [NEW] [publisher.py](../../mcp_servers/discord_reports/publisher.py)
* Implement AC-6, AC-7, AC-8, AC-10 (token redaction):
  * `redact_webhook_url(text)` — replaces `/webhooks/<id>/<token>` with `/webhooks/<id>/***` in all logs, exceptions, and responses.
  * `DeliveryLedger(ledger_path)` — deterministic SHA-256 content hash over included files; skip when matching & `force=False`; update on successful live send; untouched on `dry_run=True`.
  * `DiscordWebhookPublisher(webhook_url, channel_type, username, transport=None)` — `httpx` client supporting Forum (`?wait=true` + `thread_name` → extract `channel_id` → `?wait=true&thread_id=...`) and Text fallback, `multipart/form-data` (`payload_json` + `files[n]`), and `429 Retry-After` backoff (up to 3 retries).

#### [NEW] [server.py](../../mcp_servers/discord_reports/server.py)
* Implement AC-9, AC-10 (path containment):
  * Thin `FastMCP("discord-reports")` stdio server exposing:
    * `discord_publish_daily_reports(date=None, mode=None, include_source_files=True, force=False, dry_run=False)`
    * `discord_send_report_file(report_path, thread_id=None, attach_markdown=True, dry_run=False)`
    * `discord_delivery_status(date=None)`
  * Strict path containment helper verifying resolved `report_path` is strictly inside `<repo_root>/reports/`.

---

### Phase 2 — Skills, Daily Workflow Integration & Hygiene

#### [NEW] [SKILL.md](../../.agents/skills/deliver-discord-reports/SKILL.md) & [README.md](../../.agents/skills/deliver-discord-reports/README.md)
* Implement AC-11:
  * Lean Spine `SKILL.md` (<200 lines) calling `discord-reports` MCP tools.
  * `README.md` documenting Discord Forum Webhook setup, Antigravity MCP config snippet (using `uv run`), ADRs, and Changelog.

#### [MODIFY] [SKILL.md](../../.agents/skills/daily-workflow/SKILL.md), [dispatch_spec.md](../../.agents/skills/daily-workflow/references/dispatch_spec.md), & [README.md](../../.agents/skills/daily-workflow/README.md)
* Implement AC-12:
  * Insert **Step 6 — Deliver to Discord** (automatic fail-soft after Step 5 Distill Knowledge; shift Review Suggestions to Step 7 and Final Summary to Step 8).
  * Add `Discord delivery:` status line to Final Summary schema in `dispatch_spec.md`.
  * Add ADR & Changelog entry to `daily-workflow/README.md`.

#### [MODIFY] [.gitignore](../../.gitignore)
* Implement AC-13 (hygiene): ignore `data/discord_delivery_log.json` and `mcp_servers/discord_reports/.venv/`.

---

### Phase 3 — Automated Verification Suite

#### [NEW] [test_discord_reports.py](../../tests/test_discord_reports.py)
* Implement comprehensive offline pytest tests (using `httpx.MockTransport` and `tmp_path`, zero network calls) mapped 1:1 to every AC below.

---

## AC-to-Verification Traceability Matrix (for `/goal`)

| AC ID | Requirement Summary | Verification Method / Test Case |
|---|---|---|
| **AC-1** | Daily report discovery (`distillations/` + 4 source dirs), `no_reports` early exit, missing-distillation fallback | `test_discover_daily_reports_*` in `tests/test_discord_reports.py` |
| **AC-2** | Content Summary v5.0 distillation & source report parsing + legacy v4 fallback | `test_parse_v5_*` and `test_parse_legacy_distillation` (tested against real v5.0 & legacy fixtures) |
| **AC-3** | GFM table → bullet conversion, `<details>/<summary>/<b>` stripping, relative link removal, `mermaid` cleanup | `test_sanitize_gfm_table`, `test_sanitize_details_tags`, `test_sanitize_relative_links_and_mermaid` |
| **AC-4** | Hard Discord limits: content ≤2,000, embed desc ≤4,096, field ≤1,024, total embeds ≤6,000, `thread_name` ≤100 | `test_hard_character_and_embed_limits` with oversized synthetic inputs |
| **AC-5** | `.md` attachment batching: opener distillation + ≤10 files / ≤8 MB batches in `digest`, `distillation_only`, `full` | `test_attachment_batching_over_10_files`, `test_delivery_modes` |
| **AC-6** | Forum `thread_name` + `?wait=true` → `thread_id` chaining, Text channel fallback, actionable 400 error | `test_forum_thread_chaining`, `test_text_channel_fallback`, `test_forum_mismatch_400_hint` |
| **AC-7** | HTTP `429 Retry-After` backoff (≤3 retries) + clean structured error return (no unhandled exceptions) | `test_rate_limit_429_retry_and_exhaustion` |
| **AC-8** | SHA-256 idempotency ledger: skip duplicate, re-send on change or `force=True`, zero side effects on `dry_run=True` | `test_idempotency_skip_change_force`, `test_dry_run_no_http_no_ledger` |
| **AC-9** | 3-tool `FastMCP` server contract + env var defaults + missing `DISCORD_WEBHOOK_URL` structured error | `test_mcp_tool_exports_and_missing_webhook_env` |
| **AC-10** | Webhook token redaction on all errors/logs + path traversal/escape rejection in `discord_send_report_file` | `test_webhook_token_redaction`, `test_path_traversal_rejected` |
| **AC-11** | `deliver-discord-reports` skill Lean Spine + `README.md` (setup + ADRs + Changelog) | `python3 scripts/validate_skill.py .agents/skills/deliver-discord-reports/SKILL.md` |
| **AC-12** | `daily-workflow` automatic fail-soft Step 6 + `dispatch_spec.md` Final Summary + `README.md` ADR/Changelog | `python3 scripts/validate_skill.py .agents/skills/daily-workflow/SKILL.md` + content assertions |
| **AC-13** | `.gitignore` updated + zero regressions across repo test suite | Full `pytest` command below |

---

## Verification Plan (Definition of Done for `/goal`)

### Automated Gate (ALL must pass with exit code 0)
- **What to test**: Discord formatter, webhook publisher, idempotency ledger, security invariants, and MCP tool handlers (AC-1 through AC-10)
  - **How to test**: `pytest -p no:recording tests/test_discord_reports.py`
  - **Expected behavior**: All tests pass, exit code 0, zero outbound network calls.
- **What to test**: New and modified agent skill schemas and Lean Spine compliance (AC-11, AC-12)
  - **How to test**: `python3 scripts/validate_skill.py .agents/skills/deliver-discord-reports/SKILL.md && python3 scripts/validate_skill.py .agents/skills/daily-workflow/SKILL.md`
  - **Expected behavior**: Both validations pass, exit code 0.
- **What to test**: Repository-wide regression suite (AC-13, respecting `known_issues.md`)
  - **How to test**: `pytest -p no:recording --ignore=tests/test_compile_session_learnings.py`
  - **Expected behavior**: All existing and new tests pass, exit code 0.

### Post-Implementation Live Smoke Test (Manual — requires user's Discord Webhook URL)
1. Pre-warm dependencies: `uv sync --directory mcp_servers/discord_reports`.
2. Add `discord-reports` to Antigravity MCP config with `DISCORD_WEBHOOK_URL` and `DISCORD_CHANNEL_TYPE=forum`.
3. Call `discord_publish_daily_reports(date="2026-11-25", dry_run=True)` and verify payload preview.
4. Call `discord_publish_daily_reports(date="2026-11-25", dry_run=False)` and confirm in Discord Forum: 1 daily post with Answer-First Embed + `Knowledge_Distillation_2026_11_25.md`, follow-up thread replies with clean headings, and all individual `.md` files attached.
5. Re-run `discord_publish_daily_reports(date="2026-11-25")` and verify `status: "skipped"` (no duplicate post).
