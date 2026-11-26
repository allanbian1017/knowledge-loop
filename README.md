# Knowledge Loop

Knowledge Loop helps you get through a reading backlog spread across your inbox, saved links, and video queue. An AI agent turns newsletters, articles, Threads posts, and YouTube videos into Markdown reports you can revisit. The daily workflow brings the day's reports together and suggests actions based on your goals.

## Get started on macOS

Start with one public article. Set up a local folder for your reports, put the article in Google Tasks, and ask your agent to process it. You'll get a Markdown summary in `reports/Website_YYYY_MM_DD/` inside your data folder, and the task will be marked complete after the report is saved. The article walkthrough uses Google Tasks and can be done before setting up Gmail, YouTube, Threads, or Discord.

[Set up Knowledge Loop and create your first report](docs/guides/setup-guide.md).

## How the daily workflow works

1. **Collect.** Save links to a Google Tasks list named `Delegate` and label newsletters `newsletter` in Gmail.
2. **Process.** Ask your agent to “Run my daily workflow.” It summarizes queued links and unread newsletters. After saving each report, it marks the task complete or marks the newsletter read and archives it.
3. **Review.** Read the daily digest, which connects takeaways across sources. Accept or reject suggested actions to shape future suggestions. Discord delivery is optional.

## Where your data lives

| Folder | What it holds |
| --- | --- |
| `knowledge-loop` | The public repository with reusable agent skills, scripts, and starter templates. |
| Your private Data Repo | Your goals, language settings, suggestion history, and generated reports. The docs refer to this folder as `$DATA_REPO`. |

The [setup guide's configuration reference](docs/guides/setup-guide.md#configuration-reference) explains how the two folders are linked. The [architecture decision record](docs/rfc/data-repo-separation-architecture.md) covers the design in more detail.

## Included Skills Catalog (20 Skills)

| Layer | Skills | Purpose |
| :--- | :--- | :--- |
| **Orchestrator (1)** | `daily-workflow` | End-to-end daily pipeline: discover Gmail/Tasks → dispatch parallel workers → grade suggestions → distill → deliver to Discord → interactive review |
| **Ingestion (4)** | `ingest-newsletter`, `ingest-threads`, `ingest-website`, `ingest-youtube` | Source-specific fetch, summarize, report write, and task/email completion |
| **Core Loop (5)** | `content-summary`, `rubric-grader`, `daily-distiller`, `deliver-discord-reports`, `review-suggestions` | Shared Answer-First Pyramid summarization, 3-dimension suggestion scoring, cross-source distillation, Discord delivery, and preference calibration |
| **Extraction Helpers (4)** | `content-cleaner`, `fetch-threads-post`, `web-to-markdown`, `yt2doc` | Pure article extraction, Threads SPA scraping, Jina Reader conversion, and Whisper transcription |
| **Companion Workflows (2)** | `review-newsletter-subscriptions`, `evolution-log` | 30-day newsletter ROI audit & narrative project evolution chronicler |
| **CLI Adapters (4)** | `agent-browser`, `gws-gmail`, `gws-shared`, `gws-tasks` | External tool instructions tracked in `skills-lock.json` |

---

## Contributor checks

```bash
# Check public repository hygiene and internal links
python3 scripts/audit_public_repo.py

# Validate the skill manifests
python3 scripts/validate_skill.py

# Run the offline test suite, including the sub-agent sync check
python3 -m pytest -p no:recording tests/ -v
```

---

## Documentation
- [Evolution Log](EvolutionLog.md)
- [Setup Guide](docs/guides/setup-guide.md)
- [Discord & MCP Setup Guide](docs/guides/discord-mcp-setup-guide.md)
- [Data Repo Separation Architecture RFC & ADR](docs/rfc/data-repo-separation-architecture.md)
- [Cognitive Bandwidth Protection Guide](docs/cognitive_bandwidth_protection_guide.md)
- [Templates](docs/templates/) (`rfc_template.md`, `plan_template.md`, `rca_template.md`, `prd_template.md`)
