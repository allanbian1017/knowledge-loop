# RFC: Suggestion rubric grading

## Summary

Score generated suggestions before they enter human review. The public rubric defines reusable quality criteria; personal goals, exclusions and feedback are external inputs, never public defaults or evidence.

## Status

Implemented. The [Home Repo architecture](home-repo-architecture.md) supersedes historical location and account assumptions.

## Motivation

Suggestions can be vague, unrelated to current goals, or forced into an inappropriate output type. Personal review statistics and rejection histories are excluded from this public design record. Validate behavior using synthetic examples with explicit preferences.

## Design

The bundled [grader](../../.agents/skills/rubric-grader/SKILL.md) has three modes:

| Mode | Behavior |
|---|---|
| Grade | Apply the current user's approved blocklist, score Actionability/Preference Alignment/Goal Relevance from 0–2 each, and route the result |
| Backtest | Evaluate an explicitly selected external feedback sample and report metrics without importing it into public files |
| Maintain | Propose recurring exclusions for human approval and report calibration only when enough scored feedback exists |

The initial composite threshold is 4/6. A hard veto overrides scoring. No publisher, tool, career interest or technical topic is a universal exclusion. The public blocklist template is neutral; its runtime counterpart belongs in PersonalDataRoot.

Check archetype-content fit. Preserve legacy JIRA_BACKLOG, ADR_DOC, PROMPT_TEMPLATE, TEST_FIXTURE and TAKEAWAY_ONLY records, but use the configured project backlog rather than an embedded account or epic. TAKEAWAY_ONLY bypasses pending actions. Do not wrap unrelated news or architecture theory into prompt tools merely to satisfy a rubric.

For keyed publications, build one formatted entry and call report_store.py merge as documented in the [storage protocol](../../.agents/skills/content-summary/references/storage.md). Serialized identity markers prevent duplicate appends after retries. Existing unkeyed input requires a duplicate check before one controlled merge.

## Compatibility

Read both legacy metadata and current rubric scores. Accept/Reject feedback comes from the user; it updates external reviewed history and preferences. It does not implement an idea or create an external issue. New blocklist entries require actual approval.

## Verification

Use synthetic users with different goals/exclusions and synthetic report histories. Verify pass/veto routing, empty histories, low samples and replay without disclosing personal data. Deterministic subscription calculations and publication/merge failure injection are covered separately by automated tests.

## ADR

Keep reusable scoring criteria in the clone and personal calibration outside it. This requires explicit setup but avoids author-specific judgments and ambiguous public seed state. A database or additional grading service is unnecessary for the current local workflow.
