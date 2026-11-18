# macOS setup

One Home Repo clone provides every in-scope skill and shared helper. This guide installs tools separately and keeps personal configuration and outputs outside the public checkout. macOS is the supported platform; do not infer Linux, native Windows, or every agent-host capability from the portable file layout.

## 1. Install the Python environment

Install Git and Python 3.12 using your preferred supported macOS distribution. Homebrew users can run `brew install git python@3.12`. [Python downloads](https://www.python.org/downloads/macos/) provide another installation route.

From the cloned repository:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/check_setup.py --offline
```

`requirements.txt` contains the runtime validator dependency; `requirements-dev.txt` adds pytest. The new storage/resolution helpers use the standard library. Initial local verification uses Python 3.10, PyYAML 6.0.3 and pytest 8.2.2. The inspected yt2doc 0.3.3 declares Python >=3.10,<3.13, so use Python 3.10–3.12 when enabling transcription. Other Python versions are not claimed as transcription-compatible.

No `npx skills add`, user-level skill copy, or other skill-repository clone is needed. Keep bundled upstream notices intact.

## 2. Choose storage and personal state

Choose directories outside the Home Repo. The personal-data directory may live inside the report repository or at an independent location. Existing locations do not need moving.

For a **new** report repository only, replace the placeholders and run:

```bash
ReportRepository='<REPORT_REPOSITORY>'
PersonalDataRoot='<PERSONAL_DATA_DIRECTORY>'
mkdir -p "$ReportRepository" "$PersonalDataRoot"
git -C "$ReportRepository" init
cp -n data/*.md "$PersonalDataRoot/"
mkdir -p "$PersonalDataRoot/prompts"
cp -n data/prompts/index.md "$PersonalDataRoot/prompts/index.md"
```

For an existing report repository, skip `git init`; select its actual Git root. Copy only missing seed files if needed. `cp -n` preserves existing contents. Edit your external `goals.md` with at least one real goal and select both language preferences in `lang_preferences.md`. Start with empty feedback ledgers and no topic exclusions, or use your own existing state. Do not copy anybody else's profile.

## 3. Create external configuration

Choose a configuration file outside the checkout. The following conventional location is an example, not an embedded personal destination:

```bash
export KNOWLEDGE_LOOP_CONFIG="$HOME/.config/knowledge-loop/config.json"
mkdir -p "$(dirname "$KNOWLEDGE_LOOP_CONFIG")"
cp -n data/repositories.example.json "$KNOWLEDGE_LOOP_CONFIG"
```

Edit that external file. `report_repository` and `personal_data` are required paths; relative paths resolve from the configuration file's directory. Replace all placeholders. Optional fields:

| Field | Meaning |
|---|---|
| `expected_origin` | Expected Git origin; SSH/HTTPS forms are normalized. Omit for an intentionally local-only repository. |
| `timezone` | IANA timezone, such as `UTC`; omitted means machine local time. Set it explicitly for scheduled work. |
| `task_list` | Google Tasks list title, default `Delegate`; ambiguous matching lists require user selection. |
| `newsletter_query` | Gmail query, default `label:newsletter is:unread`; create/select the label in your own account. |

Credentials do not belong in this JSON. Use the external tools' normal credential stores. Export `KNOWLEDGE_LOOP_CONFIG` to the agent/automation environment as well as the terminal; desktop apps do not necessarily inherit shell startup exports. Alternatively pass `--config` to every helper invocation and include the selected external config in the worker brief.

```bash
python scripts/workspace_paths.py
python scripts/workspace_paths.py --languages
python scripts/validate_language_config.py
```

These commands read configuration. They do not initialize, repair or overwrite personal state. Invalid paths, nested repositories, missing language keys or an unexpected configured origin stop the workflow.

## 4. Install only the tools you need

| Skills | Tool | Verification and additional requirements |
|---|---|---|
| Daily workflow, newsletters, Google Tasks | `gws` | `gws --version`; account access and matching Gmail/Tasks scopes |
| Browser and Threads | `agent-browser` | `agent-browser --version`; browser binary, network and session access |
| YouTube ingestion/transcription | `yt2doc` | `yt2doc --help`; ffmpeg, media/model downloads and sufficient memory |
| GitHub study | `gh` | `gh --version` and `gh auth status`; access to requested repositories |
| Website extraction | Native URL-fetch tool or documented `curl` | Network access to Jina Reader; never bypass an unavailable documented route |
| Cleanup | `trash` | `command -v trash`; recoverable deletion requires scope authorization |

### Google Workspace

[Official installation and authentication](https://github.com/googleworkspace/cli):

```bash
brew install googleworkspace-cli
gws --version
```

Use your own Google Cloud project, consent configuration and account. `gws auth setup` requires `gcloud`; the upstream guide documents manual OAuth setup when it is unavailable. After credentials are configured, use `gws auth login` and select only the services needed by this workflow. Verify Gmail and Tasks access with bounded read-only queries before live ingestion. Never export raw tokens or credentials into a public file or test fixture.

### Browser

Install using the [official agent-browser guide](https://agent-browser.dev/installation):

```bash
npm install -g agent-browser
agent-browser install
agent-browser --version
agent-browser skills get agent-browser
```

The last command loads version-specific CLI documentation; it does not require a second skill checkout. Complete authenticated site login only when required and authorized. Keep session state outside tracked files. Native Chrome/CDP modes depend on the installed tool/platform; do not assume every mode works on macOS.

### YouTube

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), ffmpeg, and the inspected [yt2doc release](https://pypi.org/project/yt2doc/0.3.3/):

```bash
brew install ffmpeg
uv tool install --python 3.12 'yt2doc==0.3.3'
yt2doc --help
```

Its Python dependencies include yt-dlp and transcription libraries; first use can download large models. Follow the skill's duration/model selection and memory guidance. Retain the documented no-local-LLM command flags. Tool installation alone does not verify downloads, video access, memory capacity, or model availability. Pin a different version only after revalidating its CLI and behavior.

### GitHub and cleanup

```bash
brew install gh trash
gh auth login
gh auth status
command -v trash
```

Authenticate your own account. No study report, commit, push, public deployment, or schedule is created during setup.

## 5. Configure the host

The primary target is the Codex macOS app/CLI. Start at the Home Repo root, confirm `.agents/skills` discovery and all six `.codex/agents` personas, and select approved workspace access for report and personal-data directories. A configuration entry does not grant filesystem access. Never change protection files or use sandbox bypasses to make preflight pass.

Skills use host file reading, command execution, worker invocation and display capabilities. Where a host supports a native URL-fetch tool, `web-to-markdown` documents that route; its explicit `curl` route supports hosts without that tool. Fresh independent worker contexts are required for parallel orchestration. A missing worker capability blocks the daily orchestrator; invoke a standalone supported ingest skill instead of pretending to dispatch workers.

Content artifacts, raw captures and candidates live under the resolved external `scratch_root` (the report repository's `.tmp/knowledge-loop/<skill>/<run>/`), presented using the host's display/link capability. Reserve Home Repo `.tmp/` for nonpersonal development artifacts. Antigravity hooks remain specific to that harness; Codex must invoke verification explicitly. Global skills with the same name are independent installations; use the repository skill's explicit path to avoid ambiguity.

## 6. Preflight and offline smoke test

```bash
python scripts/check_setup.py --offline
python scripts/check_setup.py --skill daily-workflow
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:recording -p no:cacheprovider tests
python scripts/sync_subagents.py --check
```

The setup checker never installs, authenticates, schedules, creates databases or writes a probe file. Executable presence and access checks cannot prove live account/host permissions. The automated suite exercises a synthetic independent report repository, external personal state, publication, replay, revisions and recovery without touching your configured storage.

Before a live run, separately authorize the workflow and verify read-only access to its sources. Successful storage and suggestion persistence precede Gmail/Task acknowledgement. Automatic Git commits/pushes are not included.

## 7. Optional automation and recovery

Configure an existing scheduler only after an interactive run succeeds. Supply the Home Repo working directory, external config, environment/tool PATH, timezone and scoped filesystem access. Preserve existing job states during migration and ensure only one producer runs. Setup does not create or enable a schedule.

A stale run claim requires reconciliation before `finish-run --run-id` releases it. Keep reports and receipts after partial failures; use the returned identities to resume. A Git failure does not invalidate stored reports. See [publication and recovery](../.agents/skills/content-summary/references/storage.md).

## Troubleshooting

- **Missing config:** export/pass the external config to the actual host process, not only an unrelated shell.
- **Unexpected English or missing goals:** read the configured personal files; public seeds are not runtime defaults.
- **Permission/keyring failure:** stop and restore the supported host/tool authorization; do not replace tools or relax protections.
- **Missing command:** check the scheduler/app PATH and documented installation; skip unrelated optional tools.
- **Invalid report date:** use the fixed run date and report inventory, not file modification time.
- **pytest plugin incompatibility:** the documented command disables the incompatible optional recording plugin.

No fresh-machine or authenticated-service success is claimed by offline tests. Record tested tool versions when performing live verification.
