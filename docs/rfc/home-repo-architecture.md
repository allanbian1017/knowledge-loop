# RFC: Public Home Repo for the news-learning loop

## 1. Summary

Keep reusable skills, personas, templates and supporting code in one public Home Repo. Resolve report storage and personal state through external configuration so an unrelated macOS user can operate a clone without author-specific resources.

## 2. Status

- **Current Status:** Accepted; implementation in progress.
- **Plan:** [Implementation and cutover](../plan/home-repo-migration-plan.md).

## 3. Motivation

Duplicated implementations drift, relative paths mix code with personal state, and host-specific assumptions prevent reproducible setup. Personal paths, accounts and feedback must not enter public examples, tests or archives.

## 4. Detailed Design

Canonical sources remain `.agents/skills` and `.agents/agents`; platform adapters are generated. The 24 in-scope skills include source ingestion, relevance/feedback, synthesis, extraction, service guidance and direct technical-documentation maintenance. Hiring, evidence/outcomes, diaries, personal writing and general decision coaching are excluded.

`workspace_paths.py` reads an explicit external JSON config. Its paths resolve relative to that config, while code roots resolve from the helper. The report target must be an independent Git root; its origin can be pinned. Personal languages, goals and feedback stay in user-selected storage. Public data files are neutral seeds.

`report_store.py` owns deterministic local publication, collision handling, revisions, receipts and merge identity. Agents retain semantic analysis and use the existing source tools. No API call, Git operation or schedule is hidden in the storage helper. The [protocol](../../.agents/skills/content-summary/references/storage.md) defines invocation and recovery.

## 5. Drawbacks & Risks

Configuration is mandatory for report-producing/personal workflows. Offline tests cannot establish live account permissions, host discovery, model availability or scheduler reliability. Keep original source implementations through production verification and observation.

## 6. Alternatives Considered

- **Sibling paths without configuration:** simple but unable to support arbitrary storage or users.
- **Copied ongoing implementations:** permits source drift and ambiguous ownership.
- **Skill symlink/global installation requirements:** unnecessary when the clone already contains required resources.
- **Database or new orchestrator:** unnecessary for a local, agent-driven pipeline.

# ADR: Keep private state external and publish with recoverable receipts

## Context

Public code must remain independent of personal identities and filesystem layout. Reports must survive partial execution and code rollback.

## Decision

Use one external config and independent report Git repository. Preserve the existing semantic workflow, serialize local publication/merge operations, acknowledge sources after verified local artifacts, and retain replaced report bytes. Keep the current feedback behavior: acceptance calibrates preferences, not automatic implementation.

## Consequences

A single clone supplies in-scope skills but requires explicit account/tool/storage setup. No personal migration evidence is copied into this public RFC. Existing source histories and excluded workflows are preserved; cleanup follows verified cutover and explicit scope approval.
