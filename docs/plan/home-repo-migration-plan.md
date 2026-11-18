# Implementation Plan — Public news-learning Home Repo

See the accepted [RFC/ADR](../rfc/home-repo-architecture.md) and [macOS setup](../setup.md).

## Approved scope

Migrate the current news-learning implementation and direct technical-documentation maintenance. Bundle all required skill resources. Personal configuration is external. Preserve independent Git histories, report formats, historical outputs and real human feedback. Exclude hiring-panel, log-task-evidence, sync-diary, personal writing, general decision coaching and one-off historical Jira migration utilities.

## Tasks and acceptance

| Task | Dependency | Acceptance | Rollback |
|---|---|---|---|
| T0 Protect baseline | Approval | Verify source state and keep private backup/manifests outside checkout | Original working trees remain intact |
| T1 Classify and import | T0 | Complete in-scope resources; excluded files preserved | Revert only Home import |
| T2 External resolution | T0 | Config-relative paths, independent cwd, correct Git root, no personal fallback | Keep old entrypoints |
| T3 Generalize public resources | T1–T2 | No personal paths/accounts/mappings; neutral setup/examples | Preserve originals privately |
| T4 Safe publication | T2 | Atomic storage, revisions, receipts, deduplicated merging and claims | Keep reports/receipts/candidates |
| T5 Integrate consumers | T3–T4 | Standalone and daily workflows use configured roots | Restore original entrypoints |
| T6 Setup and preflight | T1–T3 | Guide, declared dependencies, read-only per-skill check | Hold cutover |
| T7 Offline verification | T5–T6 | Isolated fixtures and arbitrary macOS paths; source hashes unchanged | Correct gaps before switching |
| T8 Entrypoint cutover | T7 + verified access | Correct working directory; explicitly authorized scheduler updates preserve status | Restore saved references/states |
| T9 Production verification | T8 + authorized run | Verify one source, report, suggestion, acknowledgement and replay | Reconcile exact item identities |
| T10 Observation/cleanup | T9 + cleanup authorization | Two successful daily invocations; no remaining consumers of migrated source copies | Restore affected implementation from backup |

Do not clean shared parent directories: excluded workflows remain in the source repository and may still need existing instructions or dependencies. No automatic push, merge, schedule creation or enablement is part of implementation.

## Verification

```bash
python3 scripts/check_setup.py --offline
python3 scripts/validate_skill.py
python3 scripts/validate_public.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:recording -p no:cacheprovider tests
python3 scripts/sync_subagents.py --check
```

Tests cover external configuration, different roots/cwd, Unicode/spaces, missing/invalid roots, origin pinning, personal language, report structure, symlink/traversal rejection, identity collisions, replay, revision preservation, interrupted replacement, permission denial, post-ledger interruption, run claims and date selection. Fixtures need no personal histories, account access or user-level skill installations. Public scans include docs and examples, not only code.

## Baseline and execution gates

The inspected source's runnable baseline has 63 passing tests. Full source collection separately fails on an absent historical session-learning module; that obsolete test is not a dependency of the migrated learning loop. Real report/checkpoint-dependent source tests are replaced by synthetic fixtures for migrated behavior.

Remote/PR status, cron coverage, actual-host cross-repository permissions, fresh-session skill discovery and authenticated production behavior require verification before cutover. No offline result proves these. Preserve the daily schedule's existing state; excluded evidence/diary/hiring integrations remain untouched.

## Cutover and recovery

Before switching, verify current heads, working changes and preservation manifests; stop competing runs. Read destination instructions and confirm configured personal language/roots. Switch only migrated entrypoints. After a bounded authorized run, replay exact source identity and compare historical hashes.

Rollback restores execution references and code while keeping all new reports, revisions, receipts, suggestions and staged candidates. Never reset the report repository to undo a migration. Unknown source acknowledgement outcomes require status readback before any repeat write. A Git failure is reported separately from successful local storage.

## Implementation status

- Baseline privately preserved outside the checkout; source preservation manifests match, including excluded skills and existing report/personal state.
- All 24 in-scope skills validate. Public-content scanning, resource/dependency checks and six-persona adapter checks pass.
- The isolated suite passes 69 tests, including concurrent CLI publishers, interrupted publication/ledger updates, revision retention and a relocated clone with an empty user profile.
- Operational configuration was created outside the checkout without overwriting personal state. It selects the existing report and personal-data locations.
- The default session sandbox cannot write the configured output directories. The normal scoped approval mechanism passes live setup preflight and a synthetic cross-repository publication/replay probe in ignored staging; real reports and personal directories are untouched.
- Unattended host permissions, fresh-session discovery and authenticated production behavior remain unverified. Scheduler-reference changes, live processing and source cleanup stay behind the production/observation gates. Existing scheduler states are preserved; migration never enables a job.
