# deliver-discord-reports Skill

## Overview

The `deliver-discord-reports` skill delivers `daily-workflow` Markdown reports (`$DATA_REPO/reports/distillations/Knowledge_Distillation_YYYY_MM_DD.md` and `$DATA_REPO/reports/<Type>_YYYY_MM_DD/*.md`) to a Discord Forum or Text channel using the local Python `discord-reports` MCP server (`mcp_servers/discord_reports/`).

## Quick Setup

See the full step-by-step guide: [Discord & MCP Setup Guide](../../../docs/guides/discord-mcp-setup-guide.md).

Minimal `~/.gemini/config/mcp_config.json` entry:

```json
{
  "mcpServers": {
    "discord-reports": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "<REPO_ROOT>/mcp_servers/discord_reports",
        "python",
        "server.py"
      ],
      "env": {
        "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN",
        "DISCORD_CHANNEL_TYPE": "forum",
        "DISCORD_DEFAULT_MODE": "per_report",
        "DISCORD_USERNAME": "Daily AI Digest"
      }
    }
  }
}
```

## MCP Tools Exposed

| Tool | Purpose | Key Parameters |
|---|---|---|
| `discord_publish_daily_reports` | Publish daily distillation + source `.md` bundle | `date`, `mode`, `include_source_files`, `force`, `dry_run` |
| `discord_send_report_file` | Send a single `.md` report inside `$DATA_REPO/reports/` | `report_path`, `thread_id`, `attach_markdown`, `dry_run` |
| `discord_delivery_status` | Query SHA-256 idempotency ledger (`$DATA_REPO/data/discord_delivery_log.json`) | `date` |

---

## Architecture Decision Records (ADRs)

### ADR-0001: Webhook-First Local Python MCP over Open-Source Alternatives
- **Context**: Neither Discord, Anthropic, nor the Antigravity Marketplace ships an official Discord MCP. Community Bot MCPs (`IQAIcom/mcp-discord`, `barryyip0625/mcp-discord`) require Bot Token + Privileged Intents and expose 20–160+ tools without Markdown sanitization or `.md` batching; community Webhook MCPs (`@kongyo2/discord-webhook-mcp`, `thesammykins/notifyme_mcp`) lack Forum `thread_name`/`thread_id` chaining and `.md` file uploads.
- **Decision**: Build a local 3-tool Python `FastMCP` + `httpx` stdio server (`mcp_servers/discord_reports/`) authenticated solely via `DISCORD_WEBHOOK_URL`.
- **Consequences**: One-minute setup with channel-scoped least-privilege access, deterministic v5.0 Markdown conversion, and full offline `pytest` coverage; push-only by design (no Discord message reading).

### ADR-0002: Forum Channel Daily Threading & Multi-File `.md` Batching
- **Context**: Daily runs can produce 1 distillation + 20+ source `.md` reports containing GFM tables and `<details>` accordions, while Discord caps messages at 2,000 chars, embeds at 6,000 total chars, and attachments at 10 files / 10 MB per request.
- **Decision**: Open one daily Forum post via `POST ?wait=true` (`thread_name`), capture `channel_id` as `thread_id`, convert tables/accordions deterministically, chunk prose `<= 1,900` chars, and upload `.md` files in `<= 10`-file / `<= 8 MB` batches via `?thread_id=...`.
- **Consequences**: Clean mobile/desktop Forum archive per day without hitting Discord 400 limits.

### ADR-0003: SHA-256 Idempotency Ledger & Credential Redaction
- **Context**: Rerunning `daily-workflow` or `deliver-discord-reports` on the same day should not spam duplicate Forum posts, and webhook tokens must never leak into logs or agent transcripts.
- **Decision**: Record a SHA-256 hash of delivered files in `$DATA_REPO/data/discord_delivery_log.json` (skipping identical reruns unless `force=True`), enforce `<repo_root>/reports/` path containment, and scrub webhook tokens on all errors.
- **Consequences**: Safe idempotent reruns and strict adherence to credential-isolation rules.

### ADR-0004: Compact 1-Message Forum Post Per Report (`per_report` Default Mode)
- **Context**: Posting full pillar deep dives and processed-report tables as thread replies adds noise, while raw `.md` attachments showed literal `<details>` HTML tags in Discord's plain-text preview.
- **Decision**: Make `per_report` the default mode: each individual source report opens 1 single-message Forum post (`🎯` + `⭐` + `⚡` + `🔗` Embed + in-memory sanitized `.md` attachment, zero thread replies), and the Daily Knowledge Distillation opens 1 single-message post last at the top (`🎯 今日一句話結論` + `⚡ 本週唯一行動` Embed + in-memory sanitized `Knowledge_Distillation_YYYY_MM_DD.md`, zero thread replies).
- **Consequences**: Every Forum post is a clean 1-message Answer-First card with full detail available cleanly in the sanitized `.md` preview, reducing HTTP volume from ~67 to ~28 requests/day while leaving local `.md` files untouched.

### ADR-0005: Pure Native Discord Markdown Without `.md` Attachments (Option C)
- **Context**: Discord's inline `.md` attachment viewer displays raw unrendered plain text (breaking GFM tables, Mermaid diagrams, and Markdown typography), while Embed borders narrow mobile viewport width.
- **Decision**: Render `per_report` and `discord_send_report_file` directly as **full-width native Discord Markdown** (`# / ## / ### / -#`, `> blockquote`, angle-bracketed `[Label](<url>)` suppressing link preview spam, GFM tables converted to 2-line bullet + column-0 `-# ↳` subtext cards, Mermaid flowcharts/subgraphs converted to Unicode arrow flows, `<details>` converted to `###` sections) with zero Embed boxes and `include_source_files=False` / `attach_markdown=False` by default.
- **Consequences**: Full-width, native typography on desktop and mobile with zero raw `<details>`, pipe tables, or Mermaid code; local `.md` files remain unchanged in git.

### ADR-0006: Dark-Mode PNG Rendering for Tables & Mermaid Diagrams (`table_renderer.py`)
- **Context**: Discord does not render GFM tables or Mermaid diagrams natively; vertical text workarounds lose side-by-side column comparison and visual flow clarity.
- **Decision**: Render `## 📊 一張表看懂` / `## 📊 跨來源主題速覽` into `overview_table.png` (`1240px` dark-mode card, 27–28px CJK typography) and each `mermaid` block into `diagram_N.png` (matching Discord dark-mode step-card or subgraph flow diagram) in memory via Pillow, sending `diagram_N.png` in its own dedicated `### 🔄 系統流程` message so neither image shrinks into a 2-up thumbnail grid (falling back gracefully to indented `` `Column` `` badges and text flows if Pillow is absent).
- **Consequences**: Full-width side-by-side comparison tables and visual flowcharts natively inside Discord with zero external API calls and ~30ms local render time.

---

## Changelog

| Version | Date | Change Summary |
|---|---|---|
| v1.3.0 | 2026-11-25 | Added dark-mode Pillow PNG renderers (`table_renderer.py`) for both GFM tables (`overview_table.png`, `1240px` larger CJK typography, CJK punctuation-aware wrapping) and Mermaid diagrams (`diagram_N.png`, dedicated full-width message), upgraded star ratings to bright gold `⭐` emoji + `(N/5)`, and retained graceful text fallbacks. |
| v1.2.0 | 2026-11-25 | Switched `per_report` and `discord_send_report_file` to **Option C (Pure Native Discord Markdown)**: full-width `# / ## / ### / -#` formatting, 2-line subtext table cards, Mermaid-to-Unicode flow converter (`convert_mermaid_to_discord`), angle-bracketed preview-free links, and zero `.md` attachments by default (`include_source_files=False`). |
| v1.1.0 | 2026-11-25 | Added `per_report` mode as the new default (1 Forum post per source report + top Daily Digest post), multi-thread tracking (`thread_ids`, `posts_created`), polite pacing, and in-memory `.md` attachment sanitization (strips `<details>`/`<summary>`/`<b>` and flattens tables for Discord file previews while leaving local `.md` files untouched). |
| v1.0.0 | 2026-11-25 | Initial release: `deliver-discord-reports` skill paired with local `discord-reports` Python MCP server (`mcp_servers/discord_reports/`), Forum threading, v5.0 sanitization, `.md` batching, and SHA-256 idempotency ledger. |

### ADR (Home Repo Pattern Portability)
- **Decision**: Parameterized data/report paths to `$DATA_REPO/...` and removed all machine-specific absolute paths so this skill runs cleanly from the public `knowledge-loop` knowledge-loop against any user's private Data Repo on macOS.
- **Changelog (2026-11-26)**: Adopted Home Repo `$DATA_REPO` path convention and verified zero-PII / zero-absolute-path portability.
