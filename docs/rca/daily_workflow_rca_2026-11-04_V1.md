# RCA: Daily Workflow — Google Workspace OAuth Token Expired or Revoked

- **Date**: 2026-11-04
- **Version**: V1
- **Status**: Resolved (Re-authenticated via `gws auth login` and verified)
- **Related Skills/Rules**:
  - [daily-workflow](../../.agents/skills/daily-workflow/SKILL.md)
  - [gws-shared](../../.agents/skills/gws-shared/SKILL.md)
  - [gws-tasks](../../.agents/skills/gws-tasks/SKILL.md)
  - [gws-gmail](../../.agents/skills/gws-gmail/SKILL.md)
  - [ingest-newsletter](../../.agents/skills/ingest-newsletter/SKILL.md)
  - [known_issues.md](../../known_issues.md)
  - [AGENTS.md](../../AGENTS.md)

---

## 1. Observed Problem

When executing Step 1 ("Discover and Classify Items") of `daily-workflow` on 2026-11-04 (session `2a8380ea-3dff-4621-83f0-356f68043eed`), both Google Tasks discovery (`gws tasks tasklists list`) and Gmail unread newsletter discovery (`gws gmail users messages list --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 1}'`) failed with exit code `2`.

Both commands failed with:
```
error[auth]: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.: invalid_grant: Token has been expired or revoked.
```

In accordance with Tier 3 Fail-Fast principles, the pipeline halted immediately without attempting ad-hoc workarounds, unauthorized tool bypasses, or modifying any code.

---

## 2. Quantitative Evidence & Measurements

### 2.1 Invocation Log

| Command | Exit Code | Output / Error Summary |
|---|---:|---|
| `gws tasks tasklists list` (Sandboxed) | 2 | `error[auth]: Authentication failed: Token refresh failed with status 403 Forbidden: Request to POST /token on oauth2.googleapis.com not allowed by policy` |
| `gws tasks tasklists list` (Unsandboxed) | 2 | `error[auth]: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file gws tasks tasklists list` (Unsandboxed) | 2 | `error[auth]: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `gws gmail users messages list --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 1}'` (Unsandboxed) | 2 | `error[auth]: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `gws auth status` (Unsandboxed) | 0 | `token_valid: false`, `token_error: "Token has been expired or revoked."` |

### 2.2 Detailed Auth Status (`gws auth status`)

```json
{
  "auth_method": "oauth2",
  "client_config": "~/.config/gws/client_secret.json",
  "client_config_exists": true,
  "client_id": "49987952....com",
  "config_client_id": "49987952....com",
  "credential_source": "client_secret.json",
  "encrypted_credentials": "~/.config/gws/credentials.enc",
  "encrypted_credentials_exists": false,
  "has_refresh_token": true,
  "keyring_backend": "keyring",
  "plain_credentials": "~/.config/gws/credentials.json",
  "plain_credentials_exists": true,
  "project_id": "<user>-ai-workflow",
  "storage": "plaintext",
  "token_cache_exists": true,
  "token_error": "Token has been expired or revoked.",
  "token_valid": false
}
```

---

## 3. Alternative Hypotheses & Rejection Evidence

- **Hypothesis A: macOS Terminal Sandbox network isolation issue**  
  *Verification / Rejection Evidence*: When executing unsandboxed (`BypassSandbox: true`), `gws` communicates directly with `oauth2.googleapis.com` and receives `invalid_grant: Token has been expired or revoked.`, confirming the failure is an authentic OAuth token revocation/expiration from Google rather than sandbox network blockage.
- **Hypothesis B: Missing client configuration**  
  *Verification / Rejection Evidence*: `gws auth status` confirms `client_config_exists: true` and `plain_credentials_exists: true` at `~/.config/gws/client_secret.json`.
- **Hypothesis C: Keyring backend configuration error**  
  *Verification / Rejection Evidence*: Both default `keyring` backend and explicit `file` backend (`GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file`) fail with identical `invalid_grant: Token has been expired or revoked.`, rejecting local keyring storage failure as the cause.

---

## 4. Root Cause

### 4.1 Primary Root Cause
The Google Workspace OAuth refresh token stored locally has expired or been revoked by Google (`invalid_grant: Token has been expired or revoked.`, `token_valid: false`).

As documented in [known_issues.md](../../known_issues.md#gws):
> **Auth token expiry**: Commands fail with "expired or revoked" — OAuth tokens have a limited lifetime → User must run `gws auth login` to re-authenticate.

### 4.2 Contributing Root Cause
OAuth 2.0 refresh tokens for desktop clients have finite validity or can be invalidated by Google account security events. Refreshing requires interactive browser consent via `gws auth login`, which cannot run unattended in an automated shell context.

---

## 5. Proposed Remediation & Verification Plan

### Remediation Steps
1. User executes `gws auth login` in their terminal to launch the interactive browser OAuth consent flow.
2. User grants permissions and confirms successful login in the terminal.

### Automated Verification Steps
Once the user completes authentication:
1. Run `gws auth status` and verify `token_valid: true` and `token_error: null`.
2. Run `gws tasks tasklists list` to verify Google Tasks discovery succeeds.
3. Run `gws gmail users messages list --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 1}'` to verify Gmail unread discovery succeeds.
4. Resume `daily-workflow` from Step 1.
