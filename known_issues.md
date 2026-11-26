# Known Issues Registry

Generic macOS, sandbox, and CLI environment failures and workarounds. Read at session start. Append directly on newly discovered generic failures (never log personal paths, usernames, or credentials).

## gws
- **[gws macOS keyring authorization failure in subagents]**: `gws` commands fail with `Failed to set key in OS keyring: Platform secure storage failure` — macOS sandbox blocks access to the OS keychain → Prefix commands with `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file` to use file-backed credential storage.
- **[Multipart email truncation in gws gmail +read]**: `gws gmail +read` may return a truncated body for complex HTML newsletters — multipart MIME parsing or zero-width spacer handling drops remaining text/html → Fallback to `gws gmail users messages get` with base64 decoding of the payload part.
- **[Optional Gmail helper reference]**: `gws-gmail` may link to an absent `gws-gmail-read/SKILL.md` → Use the documented `gws gmail +read --id ... --headers --html` command in `ingest-newsletter`.
- **[CLI execution in macOS sandbox]**: Direct `gws` calls can be blocked by sandbox permission wrappers → Wrap in `bash -c "gws ..."` or run with explicit user approval.
- **[gws discovery cache error in sandbox]**: Sandboxed `gws` calls fail with `error[discovery]: File exists (os error 17)` — macOS sandbox blocks accessing/updating `~/.config/gws/` discovery cache → Run `gws` outside sandbox (with `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file` when needed).
- **[Auth token expiry]**: Commands fail with `expired or revoked` — OAuth tokens have a limited lifetime → Run `gws auth login` to re-authenticate.
- **[Tasks update API quirk]**: `gws tasks tasks update` returns `Missing task ID` — API requires `id` in JSON body despite also being in URL path params → Include `id` in both path and body.
- **[Subagent concurrency]**: 7+ parallel subagents can trigger 429 quota exhaustion → Limit concurrency or fall back to sequential processing.
- **[distiller_reviewer missing filesystem tools]**: Some agent harnesses omit directory-listing/write tools on read-focused subagent personas → Pass explicit report paths from the parent orchestrator and write `$DATA_REPO/reports/distillations/Knowledge_Distillation_YYYY_MM_DD.md` from the parent if needed.

## sandbox
- **[agent-browser on macOS]**: Socket path permission denied — macOS sandbox does not expose the Unix domain socket `agent-browser` requires → Run outside sandbox or fall back to Jina Reader for public web pages.
- **[Chrome mode on macOS]**: `agent-browser` local chrome mode is Linux-only → Use headless mode or Jina Reader fallback.
- **[Relative paths in agent permissions config]**: `run_command` fails with `sandbox configuration error: readonly node: non-absolute file path` — relative or tilde-prefixed paths exist in local tool permission grants → Ensure local machine-only permission entries in `~/.gemini/config/` use absolute paths and restart the session.
- **[git global config in sandbox]**: `git` fails with `unable to access '~/.gitconfig': Operation not permitted` — macOS sandbox blocks reading home-directory git config → Prefix sandboxed git commands with `GIT_CONFIG_GLOBAL=/dev/null git ...`.

## content_ingestion
- **[Threads login wall]**: Posts redirect to login/invalid_post page — `threads-auth.json` is missing or expired → Skip or use Jina Reader for public post extraction.
- **[Cloudflare 403]**: Headless scraping blocked by WAF bot protection → Fall back to web search or manual copy.
- **[X/Twitter login wall]**: Direct `x.com` URLs fail on Jina Reader with 403 / login wall → Rewrite URL to `twitter.com` when fetching via Jina Reader (`https://r.jina.ai/https://twitter.com/...`).

## shell
- **[Backticks in zsh double quotes]**: Double-quoted patterns containing backticks trigger command substitution in zsh → Use single quotes for patterns containing backticks.

## python_testing
- **[pytest_recording urllib3 incompatibility]**: `pytest` fails with `AttributeError: module 'urllib3.connectionpool' has no attribute 'VerifiedHTTPSConnection'` when a global `pytest-recording` plugin conflicts with system `urllib3` → Pass `-p no:recording` when invoking `pytest`.
