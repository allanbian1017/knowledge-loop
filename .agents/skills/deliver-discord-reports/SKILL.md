---
name: deliver-discord-reports
description: "Deliver daily-workflow Knowledge Distillation and source .md reports to Discord via the local discord-reports MCP server. Use when the user says 'send today's reports to Discord', 'deliver reports to Discord', 'push daily digest to Discord', or when invoked by daily-workflow Step 6."
---

# deliver-discord-reports

Publishes daily-workflow intelligence reports (Knowledge Distillation + all daily source `.md` reports) to a Discord Forum (or Text) channel via the `discord-reports` MCP server.

> **Setup Guide**: See [Discord & MCP Setup Guide](../../../docs/guides/discord-mcp-setup-guide.md) for creating a Discord Forum Webhook and registering `discord-reports` in `~/.gemini/config/mcp_config.json`.

---

## Workflow

### Step 1 — Verify `discord-reports` MCP Availability

1. Check that the `discord-reports` MCP tools (`discord_publish_daily_reports`, `discord_send_report_file`, `discord_delivery_status`) are available in the current session.
2. **Fail-Fast (No Tool Circumvention)**: If the MCP server is unavailable or returns `DISCORD_WEBHOOK_URL is not configured`, **stop immediately** and report the setup pointer (`docs/guides/discord-mcp-setup-guide.md`). Never bypass the MCP server with ad-hoc `curl` or shell scripts.

### Step 2 — Deliver Reports

- **Daily Bundle (Default)**: Call `discord_publish_daily_reports`:
  - `date`: `"YYYY-MM-DD"` (optional; defaults to today's local date)
  - `mode`: `"per_report"` (default — **Pure Native Discord Markdown, no Embed boxes, no `.md` attachments**: opens 1 Forum post per source report and 1 top `📰 Daily Digest — YYYY-MM-DD` post with `# / ## / ### / -#` headings, 2-line structured table cards, Unicode Mermaid step flows, angle-bracketed links, and chunked `🔍 深入解構` replies; also supports `"digest"`, `"distillation_only"`, `"full"`)
  - `include_source_files`: `false` (default; set `true` only if you also want `.md` files attached)
  - `force`: `false` (set `true` only if the user explicitly asks to resend an already-delivered date)
  - `dry_run`: `false` (set `true` when the user asks to preview payloads without posting)

- **Single Report File**: If the user specifies one report path under `$DATA_REPO/reports/`, call `discord_send_report_file`:
  - `report_path`: workspace-relative path under `$DATA_REPO/reports/` (e.g., `$DATA_REPO/reports/Website_2026_11_25/article.md`)
  - `thread_id`: optional existing Discord Forum thread ID
  - `attach_markdown`: `false` (default; sends pure native Discord Markdown)
  - `dry_run`: `false`

### Step 3 — Report Receipt

Report the structured delivery result concisely:
- `status`: `sent` / `skipped` / `no_reports` / `dry_run` / `error`
- `thread_id`, `messages_sent`, `files_attached` (or `error` reason if failed)
