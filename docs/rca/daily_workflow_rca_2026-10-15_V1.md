# RCA: Daily Workflow — Google Workspace OAuth Token Expired or Revoked

- **Date**: 2026-10-15
- **Version**: V1
- **Status**: Resolved; authentication restored and verified via `gws auth status`.
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

When executing Step 1 ("Discover and Classify Items") of `daily-workflow` on 2026-10-15, both Google Tasks discovery (`gws tasks tasklists list`) and Gmail unread newsletter discovery (`gws gmail users messages list --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 1}'`) failed with exit code `2`.

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
| `gws tasks tasklists list` | 2 | `error[auth]: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `gws gmail users messages list --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 1}'` | 2 | `error[auth]: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `gws auth status` | 0 | `token_valid: false`, `token_error: "Token has been expired or revoked."` |

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
  "encrypted_credentials_exists": true,
  "encryption_valid": true,
  "has_refresh_token": true,
  "keyring_backend": "keyring",
  "plain_credentials": "~/.config/gws/credentials.json",
  "plain_credentials_exists": true,
  "project_id": "<user>-ai-workflow",
  "storage": "encrypted",
  "token_cache_exists": true,
  "token_error": "Token has been expired or revoked.",
  "token_valid": false
}
```

---

## 3. Alternative Hypotheses Evaluated

- **Hypothesis 1: macOS Terminal Sandbox network isolation issue**  
  *Evidence against*: When executing unsandboxed (`BypassSandbox: true`), `gws` communicates with Google OAuth servers and receives `401 / invalid_grant: Token has been expired or revoked.` directly from Google.
- **Hypothesis 2: Missing or corrupted client configuration**  
  *Evidence against*: `gws auth status` confirms `client_config_exists: true`, `encrypted_credentials_exists: true`, and `encryption_valid: true`.
- **Hypothesis 3: Keyring backend lock or keychain failure**  
  *Evidence against*: Keyring lookup succeeded (`Using keyring backend: keyring`). The failure originates from Google OAuth server rejecting the refresh token.

---

## 4. Root Cause

The Google Workspace OAuth refresh token stored locally in the keyring has expired or been revoked by Google. As documented in [known_issues.md](../../known_issues.md#gws):
> **Auth token expiry**: Commands fail with "expired or revoked" — OAuth tokens have a limited lifetime → User must run `gws auth login` to re-authenticate.

Because `gws auth login` triggers an interactive browser-based OAuth consent flow requiring human interaction, it cannot be run unattended.

---

## 5. Remediation & Verification Results

- [x] User re-authenticated via `gws auth login`.
- [x] Verified `gws auth status`: `token_valid: true`, 7 scopes authorized (`email`, `profile`, `gmail.modify`, `tasks`, etc.), user `<user-email@example.com>`.
- [x] Verify `gws tasks tasklists list`: exit code 0, successfully retrieved task lists including `Delegate` list (`QnNIeVNoUmxOalM1bTNsRg`).
- [x] Verify `gws gmail users messages list`: exit code 0, discovered 7 unread newsletters (`resultSizeEstimate: 7`).
- [x] Resume `daily-workflow` pipeline execution.
