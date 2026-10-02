# RCA: Daily Workflow — Google Workspace OAuth Token Expired or Revoked

- **Date**: 2026-09-20
- **Version**: V1
- **Status**: Resolved; authentication restored and verified.
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

When executing Step 1 ("Discover and Classify Items") of `daily-workflow` on 2026-09-20, both Google Tasks discovery (`gws tasks tasklists list`) and Gmail unread newsletter discovery (`gws gmail users messages list ...`) failed with exit code `2`.

Both commands failed with:
```
error[auth]: Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.: invalid_grant: Token has been expired or revoked.
```

The pipeline halted under the Fail-Fast rule without bypassing documented tools or modifying any code.

---

## 2. Quantitative Evidence & Measurements

### 2.1 Invocation Log

| Command | Exit Code | Output / Error Summary |
|---|---:|---|
| `gws tasks tasklists list` | 2 | `Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `gws gmail users messages list --params '{"userId": "me", "q": "label:newsletter is:unread", "maxResults": 1}'` | 2 | `Authentication failed: Failed to get token: Server error: invalid_grant: Token has been expired or revoked.` |
| `gws auth status` | 0 | `token_valid: false`, `token_error: "Token has been expired or revoked."` |

### 2.2 Detailed Auth Status (`gws auth status`)

```json
{
  "auth_method": "oauth2",
  "client_config": "/Users/allanbian/.config/gws/client_secret.json",
  "client_config_exists": true,
  "client_id": "49987952....com",
  "credential_source": "client_secret.json",
  "encrypted_credentials_exists": true,
  "encryption_valid": true,
  "has_refresh_token": true,
  "keyring_backend": "keyring",
  "project_id": "allanbian-ai-workflow",
  "token_error": "Token has been expired or revoked.",
  "token_valid": false
}
```

---

## 3. Alternative Hypotheses Evaluated

- **Hypothesis 1: macOS Terminal Sandbox network isolation issue**  
  *Evidence against*: When running outside the sandbox (`BypassSandbox: true`), the command reaches the Google OAuth token endpoint and returns an explicit `invalid_grant` from Google servers.
- **Hypothesis 2: Corrupted client secret or missing credentials file**  
  *Evidence against*: `gws auth status` confirms `client_config_exists: true`, `encrypted_credentials_exists: true`, and `encryption_valid: true`. The error is specific to token expiry/revocation on Google's OAuth2 server side.
- **Hypothesis 3: Keyring backend lock**  
  *Evidence against*: Keyring access succeeded (`Using keyring backend: keyring`). The returned error is `invalid_grant` from Google OAuth server, not a keychain/keyring access error.

---

## 4. Root Cause

The Google Workspace OAuth refresh token stored locally in the keyring has expired or been revoked by Google. As documented in [known_issues.md](../../known_issues.md#gws):
> **Auth token expiry**: Commands fail with "expired or revoked" — OAuth tokens have a limited lifetime → User must run `gws auth login` to re-authenticate.

Because `gws auth login` triggers an interactive browser-based OAuth consent screen, the user must run `gws auth login` in their terminal to restore a valid token.

---

## 5. Remediation & Verification Results

- [x] User re-authenticated via `gws auth login`.
- [x] Verified `gws auth status`: `token_valid: true`, 7 scopes authorized (`email`, `profile`, `gmail.modify`, `tasks`, etc.).
- [x] Verified `gws tasks tasklists list`: exit 0, retrieved tasklists including `Delegate` (`QnNIeVNoUmxOalM1bTNsRg`).
- [x] Verified `gws gmail users messages list`: exit 0, retrieved unread newsletter list.
- [x] Pipeline unblocked; resumed daily workflow.
