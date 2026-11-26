# Set up Knowledge Loop on macOS

Start with one public article. By the end of this guide, your agent will have turned it into a Markdown report and marked the corresponding Google Task complete. Once that works, you can add Gmail newsletters, YouTube videos, and Threads posts to your daily reading workflow.

## Before you start

You'll need Git, Python 3.10 or later, and an AI agent that can read the repository's skills, run shell commands, fetch web pages, and write reports. The commands below use Homebrew to install the Google Workspace CLI (`gws`).

You’ll work with two folders side by side. `knowledge-loop` holds the workflows. Your **Data Repo** holds your personal settings, suggestions, and reports. The guide uses `my-knowledge-data` for the folder name and `$DATA_REPO` as shorthand for its path.

## 1. Set up your two folders

With an SSH key configured for your GitHub account, run these commands in Terminal.

```bash
git clone git@github.com:allanbian1017/knowledge-loop.git knowledge-loop
cd knowledge-loop
./scripts/init_workspace.sh --data-repo ../my-knowledge-data --with-code-workspace --skip-uv
```

Press Enter at the timezone prompt to accept the suggested value, or enter your own. The initializer creates the Data Repo folder, adds any missing starter files, and prints the folder it configured. It preserves existing files. If you already have a private Data Repo, pass its path instead. If you plan to sync your data with Git, use a private repository for that folder.

Open both folders in the same agent workspace so the agent can read the skills and write to the Data Repo.

- **Antigravity, VS Code, or Cursor.** Open the generated `knowledge-loop.code-workspace` file or add your Data Repo to the current workspace.
- **Claude Code or Codex CLI.** Start the agent from `knowledge-loop` with `--add-dir ../my-knowledge-data`.

To tailor your first report, set `Preferred Report Language` in `my-knowledge-data/data/lang_preferences.md` and add your current goals to `my-knowledge-data/data/goals.md`. The starter settings work for a first run.

## 2. Connect Google Tasks

Install `gws` in Terminal.

```bash
brew install googleworkspace-cli
```

Configure OAuth for the Google Tasks API. If you're already signed in to the `gcloud` CLI, run `gws auth setup`. For manual setup through Google Cloud Console, follow the [upstream authentication guide](https://github.com/googleworkspace/cli#authentication).

Sign in to the Google account where you’ll queue your article. Grant access to list and update tasks, then check that the CLI can see your task lists.

```bash
gws auth login -s tasks
gws tasks tasklists list
```

## 3. Generate your first report

1. In Google Tasks, choose an existing list or create one. The default name is `Delegate`. Add a task with the article’s title and put its public URL in the task notes.

   If you use a different list name, edit `$DATA_REPO/data/integrations.md` and set **Delegate Task List Name** to match the title in Google Tasks exactly. A list named `Reading Queue` uses this entry.

   ```markdown
   - **Delegate Task List Name**: `Reading Queue`
   ```

2. In your agent chat, paste the prompt below and replace the placeholder with the same URL. If you use a different list name, replace `Delegate` in the prompt with that name.

   > Use the skill in `.agents/skills/ingest-website/SKILL.md` to process the article at [paste article URL here]. Find its task in my `Delegate` list, save the Markdown summary to my Data Repo, and mark the task complete after the report is saved.

3. Open the file under `my-knowledge-data/reports/Website_YYYY_MM_DD/`, where `YYYY_MM_DD` is the run date. The report should summarize the article and include its source. The task should now be complete.

## Run the full daily workflow

Keep adding article, Threads, or YouTube links to your Google Tasks list. Label newsletters `newsletter` in Gmail and leave the ones you want processed unread. For the full workflow, enable the Gmail API in the OAuth project and sign in with `gws auth login -s tasks,gmail`. Grant task access and Gmail access to read, mark read, and archive messages.

| Integration | Setup |
| --- | --- |
| YouTube transcription | Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) with `brew install uv`, then install [`yt2doc`](https://github.com/shun-liang/yt2doc) with `uv tool install yt2doc`. |
| Threads | Install [`agent-browser`](https://agent-browser.dev/installation) with `brew install agent-browser`, then run `agent-browser install` to set up its browser. See the [Threads skill](../../.agents/skills/fetch-threads-post/SKILL.md) for authenticated access. |
| Discord delivery | Follow the [Discord and MCP setup guide](discord-mcp-setup-guide.md) if you want the daily digest delivered to Discord. |

Ask your agent, “Run my daily workflow.” If you use a custom list, include its name, for example, “Run my daily workflow using the Google Tasks list named Reading Queue.”

The workflow processes the queue, writes source reports under `$DATA_REPO/reports/`, and saves the daily digest as `$DATA_REPO/reports/distillations/Knowledge_Distillation_YYYY_MM_DD.md`. You can then accept or reject suggested actions. The [daily workflow skill](../../.agents/skills/daily-workflow/SKILL.md) describes the full sequence.

## Troubleshooting

| If you see this | What to check |
| --- | --- |
| The agent cannot find or write to the Data Repo | Open both folders in the same workspace. If you linked a different folder, check that `workspace.local.env` and `repos.local.md` point to it. The initializer preserves existing local settings. |
| `gws` cannot list your tasks | Confirm the Tasks API is enabled in the OAuth project, sign in again with `gws auth login -s tasks`, and rerun `gws tasks tasklists list`. Use the same Google account in Tasks and in `gws`. |
| The agent finds nothing to process | Check that your task is still open in `Delegate` or the custom list you named in your prompt, and that it contains the full URL. The default Gmail queue contains only unread messages with the `newsletter` label. |
| The article cannot be fetched | Try a public article that opens without signing in. If the fetch fails, the workflow leaves the task open. |

## Configuration reference

The initializer creates the files below in `knowledge-loop`. Git ignores them. For manual setup, copy the relevant template to the local filename in the table and replace the placeholder paths.

| Local file | Template | Purpose |
| --- | --- | --- |
| `workspace.local.env` | [Environment template](../../examples/workspace.local.env.example) | Sets `DATA_REPO_DIR` for scripts and `USER_TIMEZONE` for date handling. |
| `repos.local.md` | [Repository map template](../../examples/repos.local.md.example) | Tells the agent where to find the Data Repo. |
| `knowledge-loop.code-workspace` | [Editor workspace template](../../examples/knowledge-loop.code-workspace.example) | Opens both folders together in a supported editor. |

Scripts resolve the Data Repo using an explicit `--data-repo` path when supported, then `KNOWLEDGE_LOOP_DATA_REPO`, then `DATA_REPO_DIR` in `workspace.local.env`. They fall back to the current checkout if it contains a `data/` folder. Relative paths are resolved from the root of the `knowledge-loop` checkout.

The [starter data files](../../examples/data/) go in `$DATA_REPO/data/`. For manual setup, copy missing templates only and save `integrations.example.md` as `integrations.md`.

| Data file | What to customize |
| --- | --- |
| [`lang_preferences.md`](../../examples/data/lang_preferences.md) | Set the report language and the language for chat and internal documents. |
| [`goals.md`](../../examples/data/goals.md) | Add goals that help the workflow choose relevant actions. |
| [`user_preferences.md`](../../examples/data/user_preferences.md) | Describe the kinds of suggestions you prefer. Reviews help refine these preferences over time. |
| [`rubric_blocklist.md`](../../examples/data/rubric_blocklist.md) | List topics and vague phrases the workflow should filter out. |
| [`integrations.md`](../../examples/data/integrations.example.md) | Customize integration settings such as the default Gmail query and task list. |
| [`suggestions_pending.md`](../../examples/data/suggestions_pending.md), [`suggestions_reviewed.md`](../../examples/data/suggestions_reviewed.md), and [`suggestions_filtered.md`](../../examples/data/suggestions_filtered.md) | The workflow manages these suggestion queues and archives. Start with the supplied templates. |

## Verify your setup

Run the skill validator from `knowledge-loop`. It should report that all skill files passed.

```bash
python3 scripts/validate_skill.py
```

If you're contributing to the project, install the [development dependencies](../../requirements-dev.txt) in a Python virtual environment, then follow the [contributor checks](../../README.md#contributor-checks).
