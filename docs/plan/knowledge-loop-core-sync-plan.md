# Implementation Plan - Simple Knowledge Loop Copy

Copy the core functionality directly from this repository, excluding its personal data and generated output. See [RFC/ADR](../rfc/knowledge-loop-core-sync.md).

## User Review Required

The user will run migration themselves. The script has not been applied to the actual `knowledge-loop` checkout. `--apply` overwrites included target files with current source contents; review the preview before copying.

## Open Questions

None for script delivery. This repository remains the maintained source.

## Proposed Changes

- [x] Replace the manifest-driven exporter with [one copy script](../../scripts/sync_knowledge_loop.py).
- [x] Remove `config/knowledge-loop/`, including manifests and rewritten skill copies.
- [x] Copy `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `known_issues.md`, related hooks/settings/templates, core skills and worker definitions.
- [x] Include all files under `docs/rfc/`, `docs/plan/` and `docs/rca/` recursively.
- [x] Exclude source personal state, generated reports, session decision logs, caches and unrelated skills.
- [x] Automatically include new files within selected core directories; skip identical destination files.
- [x] Keep destination-only files and leave Git metadata/index untouched.
- [x] Add [automated tests](../../tests/test_sync_knowledge_loop.py).
- [ ] User runs the script against the actual target.

## Usage

From this repository:

```bash
# Preview
python3 scripts/sync_knowledge_loop.py --target ../knowledge-loop

# Copy now; run the same command again for future updates
python3 scripts/sync_knowledge_loop.py --target ../knowledge-loop --apply
```

Use `--source` for a different source checkout. The target can be created by the copy operation. For periodic execution, call the same command from your existing scheduler; no schedule or background service is installed. No config file or maintained sync record is required.

The 13 core skill names are listed once in the script. Changes and new files inside them copy automatically. Add a new skill name there only when intentionally expanding core scope.

Files are copied as authored: there is no separate personalization mode, generated profile, or rewritten prompt bundle. Existing target preferences and reports remain untouched. The script does not scrub embedded examples or rewrite source-machine paths, and it does not untrack existing target runtime files.

## Verification Plan

### Automated Tests

- **What to test**: preview writes nothing; copy overwrites selected files; RFCs, plans and RCAs copy recursively and update on reruns; repeat runs skip identical files; new core files are picked up; private/unrelated directories remain excluded; target-only files remain; symlinks/nested repositories are rejected; copied skill packages validate.
- **How to test**: `python3 -m pytest -p no:recording tests/test_sync_knowledge_loop.py --basetemp=.tmp/knowledge-loop-tests -q`.
- **Expected behavior**: all tests pass in isolated sibling source/target fixtures. The actual target remains unchanged.
