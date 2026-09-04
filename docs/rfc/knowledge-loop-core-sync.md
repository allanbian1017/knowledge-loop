# RFC: Simple Core Copy into Knowledge Loop

## 1. Summary

Use one Python script to copy the current core files from this repository into `knowledge-loop`. No export config directory, manifest, source hash approvals, rewritten skill copies, or sync-state files are required.

## 2. Status

- **Current Status**: Implemented; actual migration left to the user
- **Proposal Date**: 2026-09-04
- **Last Updated**: 2026-09-04
- **Plan**: [Implementation and usage](../plan/knowledge-loop-core-sync-plan.md)

## 3. Motivation

The user wants this growing repository to remain the only maintained source. The previous export bundle duplicated skills and required manual refreshes, creating unwanted overhead. That bundle has been removed.

## 4. Detailed Design

### 4.1 Architecture & Workflow

`source core files → scripts/sync_knowledge_loop.py → target core files`

Preview by default; `--apply` copies files. Each run reads current source files directly, including Git-ignored skills. New files within included directories are picked up automatically. Identical files are skipped. Existing matching destination paths are overwritten; destination-only files are retained.

### 4.2 File & Module Changes

- [Script](../../scripts/sync_knowledge_loop.py): copy `AGENTS.md`, `CLAUDE.md`, `CONTEXT.md`, `known_issues.md`, agent settings, validation/support scripts, hooks, document templates, all files under `docs/rfc/`, `docs/plan/` and `docs/rca/`, worker personas/adapters, and the 13 content-pipeline skills.
- [Tests](../../tests/test_sync_knowledge_loop.py): isolated copy, overwrite, no-op, exclusions, symlink checks, and package validation.
- Exclude root personal `data/`, `reports/`, `learnings/`, backlog, session decision logs, credentials/configuration outside selected paths, and caches. RFCs, plans and RCAs are explicitly included, with their existing contents and nested files.
- Copy selected files as authored, preserving contents and file permissions. This is a copy utility, not a prompt-rewriting or semantic privacy-sanitization system. Personal examples, assumptions or absolute paths embedded in included source instructions are not rewritten; shared-source cleanup belongs in the original files if needed.
- Do not copy root README, dependency lockfile or Git metadata; preserve the target's identity and existing dependency setup.
- No target data initialization, Git index modification, deletion, commit, push, or scheduler installation.

## 5. Drawbacks & Risks

- Included target files are overwritten when source differs, including local target edits. Preview before the first run; maintain shared functionality in this source repository.
- Removed source files remain in the target; there is deliberately no automatic deletion.
- Copying files does not verify live agent or connector compatibility. Existing tracked target data remains tracked; the script does not change `.gitignore` or Git history.
- A failed copy may leave some files updated; rerun to finish. No transactional synchronization mechanism is maintained.

## 6. Alternatives Considered

- **Manifest and override bundle:** rejected by the user because it creates another maintained version of the skills.
- **Whole-repository copy:** includes personal data, generated reports and unrelated capabilities.
- **Selected-directory copy:** chosen; one script, current source contents, no recurring configuration maintenance.

# ADR: Keep One Source of Truth

## Context

The user explicitly requested a simple copy script and removal of the export configuration overhead.

## Decision

Copy the core files directly from this repository. Keep the skill directory list in the script; automatically include additions within those directories. The user runs migration themselves.

## Consequences

No duplicated skill definitions or manual hash updates remain. The target shares source behavior and source-file limitations; the script does not maintain an independent neutralized product fork.
