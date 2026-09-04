# RCA: Daily Workflow — Redirected Gmail Reads Lose Keyring Access

- **Date**: 2026-09-04
- **Version**: V1
- **Status**: Remediation verified; 10 newsletters processed and unread queue cleared.
- **Related Skills/Rules**:
  - [daily-workflow](../../.agents/skills/daily-workflow/SKILL.md)
  - [ingest-newsletter](../../.agents/skills/ingest-newsletter/SKILL.md)
  - [AGENTS.md](../../AGENTS.md)

## 1. Observed Problem

Nine newsletters were discovered. One report and staged suggestion were saved, and that email was subsequently marked read and archived. Two workers repeatedly failed when redirecting full HTML reads into `.tmp/`; six items were not dispatched. Eight newsletters remain unfinished. Grading, distillation, and interactive review have not run.

A sequential comparison in the primary agent reproduced the failure for the same message, using the same executable and arguments:

| Invocation | Exit | Evidence |
|---|---:|---|
| `gws gmail +read --id 1a0683db73da4abc --headers --html` | 0 | Returned From, Subject and HTML; 800 output lines, approximately 27,881 tokens before display truncation |
| Same command followed by `> .tmp/gws_read_diagnostic_2026_09_04.html` | 2 | Keyring authorization denied; output file only 147 bytes |

The redirected invocation reported `Failed to set key in OS keyring`, `Unable to obtain authorization for this operation`, and `Failed to build authorized user authenticator`. It also attempted to remove credentials/cache files and reported `Operation not permitted` for both. No credential contents were inspected. The two earlier worker output files were also 147 bytes each and are not usable newsletter captures.

## 2. Alternative Hypotheses & Evidence

- **Expired or missing Gmail authorization:** Does not explain the successful full read immediately before the failed redirected read. Earlier list and modify operations also succeeded. Reauthentication alone is not an established fix.
- **Missing Gmail read scope or inaccessible message:** Contradicted by the successful direct read of the exact same message.
- **Parallel worker contention as the sole cause:** Contradicted by reproducing the issue sequentially in the primary agent.
- **Unable to write the destination:** The shell created a 147-byte destination; the reported failure occurs during keyring authentication, not destination creation.
- **Redirection changes the execution permission context:** Leading hypothesis. The controlled invocation difference is output redirection, and the failure includes both keyring authorization and protected-file permission denials. The exact sandbox/approval routing decision is not exposed by the command results and is not proven.
- **Transient keyring state:** Not fully excluded by one paired diagnostic, although repeated worker failures follow the same redirected-read pattern.

## 3. Root Cause

### 3.1 Confirmed failure boundary

The redirected read cannot access the OS keyring in its execution context. A direct read can. This is an execution-dependent authorization failure, not evidence that the user failed to restore Gmail credentials. The precise mechanism behind the differing contexts remains a hypothesis pending permission-aware verification.

### 3.2 Contributing causes

The ingestion skill requests HTML and says to retry truncated output, but does not specify an authorized full-output capture procedure. This newsletter produces roughly 28k tokens of HTML, triggering truncation and a redirected retry. Earlier status messages incorrectly generalized the failure into a missing user login/keyring restoration requirement without comparing the command shapes.

## 4. Proposed Fix & Status

No workflow, skill, authentication configuration, or permission settings have been changed.

1. Run the exact redirected read through the tool's explicit `require_escalated` approval mechanism, requesting permission for macOS keyring access and full newsletter capture into `.tmp/`. Do not change credential storage, wrap commands to evade controls, or substitute an API.
2. If approved and successful, use that authorized capture method for remaining newsletter reads; resume reports, grading, distillation, and feedback collection without duplicating the completed item.
3. If it fails, stop and report the exact error. Do not infer a need to delete credentials or reauthenticate without further evidence.

### Automated verification after approval

- **What to test:** The identical redirected `gws +read` under explicitly approved execution.
- **How to test:** Check exit code; assert the saved result includes nonempty From and Subject fields and an HTML body; verify it is not the 147-byte error artifact. Keep body and credentials out of diagnostic logs.
- **Expected behavior:** Exit 0 and a complete content artifact. Only mark an email read/archive after its report has been saved and verified.
- **Skill validation:** If a later skill edit is approved, run `python3 scripts/validate_skill.py` for each changed skill.

- [x] Reproduced the command-shape-dependent failure.
- [x] Documented evidence and uncertainty.
- [x] Obtain approval for proposed remediation under AGENTS.md Tier 2 RCA gate.
- [x] Verify explicit permission execution: redirected command returned exit 0; automated assertions verified 111,390 bytes, From/Subject headers, and opening/closing HTML.
- [x] Resume ingestion: 10 newsletters completed, including one new arrival; final Gmail unread result was 0. Grading accepted 9 suggestions and filtered 1; distillation/review preparation follow.

## 5. References

- [Known issues](../../known_issues.md)
- [Saved report](../../reports/Newsletter_2026_09_04/Matt_Pocock_grill-with-docs.md)

## Approved Remediation Result

The user approved the proposed permission test. The exact redirected read executed with `sandbox_permissions=require_escalated` succeeded (exit 0). Automated content assertions passed. This supports execution permissions as the operative difference; no credential restoration or configuration edit was needed during this test. Remaining ingestion resumed using explicit approved execution for redirected reads.
