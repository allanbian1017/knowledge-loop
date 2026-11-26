# Setup Guide (macOS)

This guide walks any macOS user through setting up **Knowledge Loop** (`knowledge-loop`) paired with a separate private **Data Repo** (`$DATA_REPO`) — with zero machine-specific paths committed to Git.

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

## 2. Clone & Quick Initialize (Automated)

Keep your personal data (goals, preferences, reports, suggestion history) in a **separate private repository** (for example `../my-knowledge-data`).

```bash
git clone <YOUR_KNOWLEDGE_LOOP_REPO_URL> knowledge-loop
cd knowledge-loop

# Non-destructively link an existing Data Repo or scaffold a new one
./scripts/init_workspace.sh --data-repo ../my-knowledge-data --with-code-workspace
```

What `./scripts/init_workspace.sh` does automatically:
1. Creates gitignored **`workspace.local.env`** in `knowledge-loop` from [examples/workspace.local.env.example](../../examples/workspace.local.env.example).
2. Creates gitignored **`repos.local.md`** in `knowledge-loop` from [examples/repos.local.md.example](../../examples/repos.local.md.example).
3. Creates gitignored **`knowledge-loop.code-workspace`** (when `--with-code-workspace` is passed) from [examples/knowledge-loop.code-workspace.example](../../examples/knowledge-loop.code-workspace.example).
4. Copies any missing starter data files from [examples/data/](../../examples/data/) into `<DATA_REPO>/data/` **without overwriting existing files**.
5. Runs `uv sync --directory mcp_servers/discord_reports` (unless `--skip-uv` is passed).

---

## 3. Configuration Files & Examples (Manual Setup Reference)

Every configuration file has a ready-to-copy template under [`examples/`](../../examples/). You can either let `./scripts/init_workspace.sh` scaffold them or copy and edit them manually.

### 3.1 Local Pointer Files (Stored in `knowledge-loop`, Gitignored)

| Local File | Example Template | Purpose |
| :--- | :--- | :--- |
| `./workspace.local.env` | [examples/workspace.local.env.example](../../examples/workspace.local.env.example) | Tells Python scripts, shell hooks, and the `discord-reports` MCP server where your Data Repo lives (`DATA_REPO_DIR`) and your timezone (`USER_TIMEZONE`). |
| `./repos.local.md` | [examples/repos.local.md.example](../../examples/repos.local.md.example) | Plain-text repository map read by AI agents via `AGENTS.md` to locate `$DATA_REPO` and any extra repos. |
| `./knowledge-loop.code-workspace` | [examples/knowledge-loop.code-workspace.example](../../examples/knowledge-loop.code-workspace.example) | Optional IDE multi-root workspace mounting `knowledge-loop` and your Data Repo side by side. |

**Manual setup commands:**
```bash
cp examples/workspace.local.env.example workspace.local.env
cp examples/repos.local.md.example repos.local.md
cp examples/knowledge-loop.code-workspace.example knowledge-loop.code-workspace
```

**Example `workspace.local.env`:**
```bash
# Relative to the knowledge-loop directory, or ~/-prefixed path
DATA_REPO_DIR="../my-knowledge-data"
USER_TIMEZONE="Asia/Taipei"
```

**Example `repos.local.md`:**
```markdown
## Primary Data Repo (`$DATA_REPO`)
- **Path**: `../my-knowledge-data`
- **Key directories**:
  - `$DATA_REPO/data/` — preferences, goals, blocklist, suggestion queues, integrations
  - `$DATA_REPO/reports/` — daily source reports and distillations
```

**Example `knowledge-loop.code-workspace`:**
```json
{
  "folders": [
    { "name": "knowledge-loop", "path": "." },
    { "name": "data-repo (Private Data)", "path": "../my-knowledge-data" }
  ]
}
```

### 3.2 Data Repo Starter Files (Stored in `<DATA_REPO>/data/`)

Copy all starter templates into your private Data Repo (if not using `init_workspace.sh`):
```bash
mkdir -p ../my-knowledge-data/data ../my-knowledge-data/reports/distillations
cp examples/data/lang_preferences.md ../my-knowledge-data/data/
cp examples/data/goals.md ../my-knowledge-data/data/
cp examples/data/user_preferences.md ../my-knowledge-data/data/
cp examples/data/rubric_blocklist.md ../my-knowledge-data/data/
cp examples/data/suggestions_*.md ../my-knowledge-data/data/
cp examples/data/integrations.example.md ../my-knowledge-data/data/integrations.md
```

| File in `$DATA_REPO/data/` | Example Template | How to Customize |
| :--- | :--- | :--- |
| `lang_preferences.md` | [examples/data/lang_preferences.md](../../examples/data/lang_preferences.md) | Set `Preferred Report Language` (external summaries) and `Preferred Conversation Language` (chat & internal docs). |
| `goals.md` | [examples/data/goals.md](../../examples/data/goals.md) | List 3–5 bullet goals; `content-summary` and `rubric-grader` score every suggestion against these goals. |
| `user_preferences.md` | [examples/data/user_preferences.md](../../examples/data/user_preferences.md) | Describe preferred vs. avoided task styles; automatically calibrated over time by `review-suggestions`. |
| `rubric_blocklist.md` | [examples/data/rubric_blocklist.md](../../examples/data/rubric_blocklist.md) | Add `Topic Blocks` and vague `Ambiguity Blocklist` phrases for `rubric-grader` hard-veto filtering. |
| `suggestions_pending.md` | [examples/data/suggestions_pending.md](../../examples/data/suggestions_pending.md) | Queue of graded suggestions (`>= 4/6`) awaiting interactive review. Leave header as-is initially. |
| `suggestions_reviewed.md` | [examples/data/suggestions_reviewed.md](../../examples/data/suggestions_reviewed.md) | Archive of Accept/Reject feedback. Leave header as-is initially. |
| `suggestions_filtered.md` | [examples/data/suggestions_filtered.md](../../examples/data/suggestions_filtered.md) | Archive of vetoed or low-scoring suggestions. Leave header as-is initially. |
| `integrations.md` | [examples/data/integrations.example.md](../../examples/data/integrations.example.md) | Override default Gmail newsletter query (`label:newsletter is:unread`) or Google Tasks list name (`Delegate`). |

**Example `data/lang_preferences.md`:**
```markdown
# Language Preferences

- **Preferred Report Language**: English
- **Preferred Conversation Language**: English
```

**Example `data/goals.md`:**
```markdown
# My Current Goals

- Build and maintain reliable AI agent workflows
- Strengthen software engineering & system design skills
- Improve personal research synthesis and productivity
```

---

## 4. Opening Both Repos in Your Agent IDE / CLI (macOS Sandbox Tip)

Because macOS agent sandboxes restrict file writes outside the active workspace, mount **both** repos together:
- **Antigravity / VS Code / Cursor**: Open the generated `knowledge-loop.code-workspace` file (or add your Data Repo folder via *Add Folder to Workspace*).
- **Claude Code / Codex CLI**: Launch inside `knowledge-loop` with `--add-dir ../my-knowledge-data`.

---

## 5. Optional: Connect the Local `discord-reports` MCP Server

1. Copy [examples/mcp_config.example.json](../../examples/mcp_config.example.json) into `~/.gemini/config/mcp_config.json`.
2. Run `which uv` in your terminal and paste that path as `"command"`.
3. Replace `<KNOWLEDGE_LOOP_ROOT>` with your `knowledge-loop` clone path, `<DATA_REPO_ROOT>` with your Data Repo path, and `<DISCORD_WEBHOOK_URL>` with your Discord Forum channel webhook:
   ```json
   {
     "mcpServers": {
       "discord-reports": {
         "command": "<PATH_TO_UV>",
         "args": [
           "run",
           "--directory",
           "<KNOWLEDGE_LOOP_ROOT>/mcp_servers/discord_reports",
           "python",
           "server.py"
         ],
         "env": {
           "KNOWLEDGE_LOOP_DATA_REPO": "<DATA_REPO_ROOT>",
           "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN",
           "DISCORD_CHANNEL_TYPE": "forum",
           "DISCORD_DEFAULT_MODE": "per_report",
           "DISCORD_USERNAME": "Daily AI Digest"
         }
       }
     }
   }
   ```
4. See [Discord & MCP Setup Guide](discord-mcp-setup-guide.md) for creating the Discord Forum channel, webhook, and dry-run walkthrough.

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
