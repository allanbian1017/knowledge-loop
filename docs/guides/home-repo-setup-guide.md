# Home Repo Setup Guide (macOS)

This guide walks any macOS user through setting up **Knowledge Loop** as a **Home Root** paired with a private **Data Repo** — with zero hardcoded paths committed to Git.

---

## 1. Prerequisites (macOS)

- **Git** & **Python 3.10+**
- **`uv`** (fast Python package/tool manager):
  ```bash
  brew install uv
  ```
- **Google Workspace CLI (`gws`)** (for Gmail newsletters & Google Tasks):
  ```bash
  brew tap googleworkspace/cli
  brew install gws
  gws auth setup
  gws auth login
  ```
- **YouTube Transcription (`yt2doc`)**:
  ```bash
  uv tool install yt2doc
  ```
- **Python test/validation dependencies**:
  ```bash
  pip install -r requirements-dev.txt
  ```

---

## 2. Clone the Home Root & Initialize Your Private Data Repo

Keep your personal data (goals, preferences, reports, suggestion history) in a **separate private repository** (e.g., `../my-knowledge-data`).

```bash
git clone <YOUR_KNOWLEDGE_LOOP_REPO_URL> knowledge-loop
cd knowledge-loop

# Non-destructively link an existing Data Repo or scaffold a new one
./scripts/init_workspace.sh --data-repo ../my-knowledge-data --with-code-workspace
```

What `./scripts/init_workspace.sh` creates:
1. **`workspace.local.env`** *(gitignored in `knowledge-loop`)* — sets `DATA_REPO_DIR` and `USER_TIMEZONE` for hooks, Python scripts, and MCP servers.
2. **`repos.local.md`** *(gitignored in `knowledge-loop`)* — plain-text Home Repo pointer map read by AI agents via `AGENTS.md`.
3. **`knowledge-loop.code-workspace`** *(gitignored, optional)* — multi-root workspace mounting both repositories side by side.
4. **Starter templates in `<DATA_REPO>/data/`** — copies missing files from `examples/data/` (`lang_preferences.md`, `goals.md`, `user_preferences.md`, `rubric_blocklist.md`, `suggestions_*.md`, `integrations.md`, `newsletter_aliases.json`) **without ever overwriting existing files**.

---

## 3. Customize Your Data Repo Configuration

Edit the files inside your private Data Repo (`<DATA_REPO>/data/`):
- `data/lang_preferences.md` — set `Preferred Report Language` and `Preferred Conversation Language`.
- `data/goals.md` — list your current engineering/learning priorities (used by `content-summary` & `rubric-grader`).
- `data/rubric_blocklist.md` — add topics or vague phrases to auto-filter.
- `data/integrations.md` — customize Gmail newsletter query (default `label:newsletter is:unread`), Google Tasks list name (default `Delegate`), and optional issue tracker config.
- `data/newsletter_aliases.json` — optional custom newsletter name normalization rules for `review-newsletter-subscriptions`.

---

## 4. Opening Both Repos in Your Agent IDE / CLI (macOS Sandbox Tip)

Because macOS agent sandboxes restrict file writes outside the active workspace, mount **both** repos together:
- **Antigravity / VS Code / Cursor**: Open the generated `knowledge-loop.code-workspace` file (or add your Data Repo folder via *Add Folder to Workspace*).
- **Claude Code / Codex CLI**: Launch inside `knowledge-loop` with `--add-dir ../my-knowledge-data`.

---

## 5. Optional: Connect the Local `discord-reports` MCP Server

1. Copy [examples/mcp_config.example.json](../../examples/mcp_config.example.json) into `~/.gemini/config/mcp_config.json`.
2. Run `which uv` and paste that path as `"command"`.
3. Set `"KNOWLEDGE_LOOP_DATA_REPO"` to your Data Repo path and `"DISCORD_WEBHOOK_URL"` to your Discord Forum channel webhook.
4. See [Discord & MCP Setup Guide](discord-mcp-setup-guide.md) for full Forum channel setup and verification.

---

## 6. Verify Everything Works

```bash
# 1. Validate all 20 SKILL.md files and cross-platform sub-agent sync
python3 scripts/validate_skill.py && python3 scripts/sync_subagents.py

# 2. Verify language configuration & self-healing hook against your Data Repo
python3 scripts/validate_language_config.py

# 3. Verify public repo hygiene (zero PII, zero absolute paths, zero broken links)
python3 scripts/audit_public_repo.py

# 4. Run full offline test suite
python3 -m pytest -p no:recording tests/ -v
```
