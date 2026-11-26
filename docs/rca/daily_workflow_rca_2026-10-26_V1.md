# RCA: Daily Workflow — Google Workspace OAuth Token Expired or Revoked

- **Date**: 2026-10-26
- **Version**: V1
- **Status**: Pending User Action (requires manual interactive re-authentication via `gws auth login`)
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

When executing Step 1 ("Discover and Classify Items") of `daily-workflow` on 2026-10-26, both Google Tasks discovery (`gws tasks tasklists list`) and Gmail unread newsletter discovery (`gws gmail users messages list --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 1}'`) failed with exit code `2`.

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
| `gws tasks tasklists list` (Sandboxed) | 4 | `error[discovery]: Failed to fetch Discovery Document for tasks/v1: HTTP 403 Forbidden` |
| `gws tasks tasklists list` (Unsandboxed) | 2 | `error[auth]: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `gws gmail users messages list --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 1}'` (Unsandboxed) | 2 | `error[auth]: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `gws auth status` | 0 | `encryption_valid: false`, `encryption_error: "Could not decrypt. May have been created on a different machine."` |

### 2.2 Detailed Auth Status (`gws auth status`)

```json
{
  "auth_method": "oauth2",
  "client_config": "~/.config/gws/client_secret.json",
  "client_config_exists": true,
  "config_client_id": "49987952....com",
  "credential_source": "client_secret.json",
  "encrypted_credentials": "~/.config/gws/credentials.enc",
  "encrypted_credentials_exists": true,
  "encryption_error": "Could not decrypt. May have been created on a different machine.",
  "encryption_valid": false,
  "keyring_backend": "keyring",
  "plain_credentials": "~/.config/gws/credentials.json",
  "plain_credentials_exists": true,
  "project_id": "<user>-ai-workflow",
  "storage": "encrypted",
  "token_cache_exists": true
}
```

---

## 3. Alternative Hypotheses Evaluated

- **Hypothesis 1: macOS Terminal Sandbox network isolation issue**  
  *Evidence against*: When executing unsandboxed (`BypassSandbox: true`), `gws` communicates with Google OAuth servers and receives `401 / invalid_grant: Token has been expired or revoked.` directly from Google.
- **Hypothesis 2: Missing client configuration**  
  *Evidence against*: `gws auth status` confirms `client_config_exists: true` at `~/.config/gws/client_secret.json`.
- **Hypothesis 3: Keyring backend failure or lock**  
  *Evidence against*: Keyring lookup succeeded (`Using keyring backend: keyring`), but the stored token is invalid/expired and encryption state failed decryption.

---

## 4. Root Cause

The Google Workspace OAuth refresh token stored locally in the keyring has expired or been revoked by Google. As documented in [known_issues.md](../../known_issues.md#gws):
> **Auth token expiry**: Commands fail with "expired or revoked" — OAuth tokens have a limited lifetime → User must run `gws auth login` to re-authenticate.

Because `gws auth login` triggers an interactive browser-based OAuth consent flow requiring human interaction in the browser, it cannot be run unattended.

---

## 5. Proposed Remediation & Verification Plan

### Remediation Steps
1. User runs `gws auth login` in their terminal to open the Google OAuth browser consent flow and re-authenticate.
2. Confirm successful login in the terminal.

### Verification Steps
Once the user has completed `gws auth login`:
1. Run `gws auth status` to verify `token_valid: true`.
2. Run `gws tasks tasklists list` to confirm access to Google Tasks.
3. Run `gws gmail users messages list --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 1}'` to confirm access to Gmail.
4. Resume `daily-workflow` from Step 1.
