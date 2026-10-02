# RCA: Daily Workflow — Google Workspace OAuth Token Expired or Revoked

- **Date**: 2026-09-29
- **Version**: V1
- **Status**: Resolved; authentication restored and verified.
- **Related Skills/Rules**:
  - [daily-workflow](../../.agents/skills/daily-workflow/SKILL.md)
  - [gws-shared](../../.agents/skills/gws-shared/SKILL.md)
  - [gws-tasks](../../.agents/skills/gws-tasks/SKILL.md)
  - [gws-gmail](../../.agents/skills/gws-gmail/SKILL.md)
  - [known_issues.md](../../known_issues.md)
  - [AGENTS.md](../../AGENTS.md)

---

## 1. Observed Problem

When executing Step 1 ("Discover and Classify Items") of `daily-workflow` on 2026-09-29, discovering the Google Task `Delegate` list (`gws tasks tasklists list`) failed with exit code `2`.

The command returned:
```json
{
  "error": {
    "code": 401,
    "message": "Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.: invalid_grant: Token has been expired or revoked.",
    "reason": "authError"
  }
}
```

In accordance with the Fail-Fast rule (Tier 3: Tool Circumvention) in `AGENTS.md`, the pipeline immediately halted without attempting ad-hoc scripts or alternative unverified APIs.

---

## 2. Quantitative Evidence & Measurements

### 2.1 Invocation Log

| Command | Exit Code | Output / Error Summary |
|---|---:|---|
| `gws tasks tasklists list` (sandboxed) | 4 | `discoveryError: Failed to fetch Discovery Document for tasks/v1: HTTP 403 Forbidden` (sandbox network restriction) |
| `gws tasks tasklists list` (unsandboxed) | 2 | `authError: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `gws auth status` | 0 | `token_valid: false`, `token_error: "Token has been expired or revoked."` |

### 2.2 Detailed Auth Status (`gws auth status`)

```json
{
  "auth_method": "oauth2",
  "client_config": "/Users/allanbian/.config/gws/client_secret.json",
  "client_config_exists": true,
  "client_id": "49987952....com",
  "config_client_id": "49987952....com",
  "credential_source": "client_secret.json",
  "encrypted_credentials": "/Users/allanbian/.config/gws/credentials.enc",
  "encrypted_credentials_exists": true,
  "encryption_valid": true,
  "has_refresh_token": true,
  "keyring_backend": "keyring",
  "plain_credentials": "/Users/allanbian/.config/gws/credentials.json",
  "plain_credentials_exists": true,
  "project_id": "allanbian-ai-workflow",
  "storage": "encrypted",
  "token_cache_exists": true,
  "token_error": "Token has been expired or revoked.",
  "token_valid": false
}
```

---

## 3. Alternative Hypotheses Evaluated

- **Hypothesis 1: macOS Terminal Sandbox network isolation issue**  
  *Evidence against*: When running outside the sandbox (`BypassSandbox: true`), the command successfully contacts the Google OAuth token endpoint and returns an explicit `invalid_grant: Token has been expired or revoked` response from Google servers.
- **Hypothesis 2: Corrupted client secret or missing credentials file**  
  *Evidence against*: `gws auth status` confirms `client_config_exists: true`, `encrypted_credentials_exists: true`, and `encryption_valid: true`. The configuration files are intact.
- **Hypothesis 3: Keyring backend lock**  
  *Evidence against*: Keyring access succeeded (`Using keyring backend: keyring`). The failure is an OAuth2 server-side `invalid_grant`, not a keychain lock or OS permission error.

---

## 4. Root Cause

The Google Workspace OAuth refresh token stored locally has expired or been revoked on Google's authorization server. As documented in [known_issues.md](../../known_issues.md#gws):
> **Auth token expiry**: Commands fail with "expired or revoked" — OAuth tokens have a limited lifetime → User must run `gws auth login` to re-authenticate.

Because `gws auth login` requires interactive browser-based OAuth consent that cannot be automated in non-interactive agent execution, the user must run `gws auth login` directly in their terminal.

---

## 5. Remediation & Verification Results

- [x] User re-authenticated via `gws auth login`.
- [x] Verified `gws auth status`: `token_valid: true`, 7 scopes authorized (`email`, `profile`, `gmail.modify`, `tasks`, etc.), user `tselunbien@gmail.com`.
- [x] Verified `gws tasks tasklists list`: exit 0, retrieved tasklists including `Delegate` (`QnNIeVNoUmxOalM1bTNsRg`).
- [x] Verified `gws gmail users messages list`: exit 0, retrieved unread newsletter list (`resultSizeEstimate: 201`).
- [x] Pipeline unblocked; resumed daily workflow.
