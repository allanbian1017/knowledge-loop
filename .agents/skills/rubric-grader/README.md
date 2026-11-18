# rubric-grader Skill

## Overview

The `rubric-grader` skill implements a two-tier quality gate for AI-generated suggestions before they enter the user's review queue. By applying a combination of deterministic blocklist checks and soft rubric scoring (Actionability, Preference Alignment, Goal Relevance), it filters out low-signal suggestions, raising the user's final acceptance rate.

---

## Problem Statement

The suggestion pipeline previously appended all generated suggestions directly to the pending queue without quality control. This resulted in:
1.  **Review quality**: Vague or mismatched suggestions can burden human review; personal rejection measurements are not public defaults.
2.  **Ambiguous/vague suggestions**: The generator frequently violated its own "no abstract descriptions" rule.
3.  **Low-signal suggestions**: Suggestions can repeat topic categories that the current user explicitly excludes; exclusions must come from that user’s configuration.
4.  **Legacy metadata clutter**: Legacy fields like 價值評分 and 決策建議 were poorly calibrated and ignored by the user.

---

## Solution

The `rubric-grader` skill acts as a unified gatekeeper. Suggestions must pass both the deterministic blocklist and score a composite score of **$\ge 4$ out of 6** to reach the pending review backlog.

### Key Features

1.  **Hard-Veto Blocklist**: Deterministic filtering of unwanted topics (blockchain, GPU clustering, Claude Code) and ambiguity phrases (研究看看, 了解一下) at zero token cost.
2.  **3-Dimension Rubric Scoring**: Soft evaluation of Actionability, Preference Alignment, and Goal Relevance.
3.  **Stratified Backtest Suite**: Inline backtesting capability using historical reviews to calculate Precision, Recall, and Accuracy.
4.  **Interactive Blocklist Maintenance**: Automatic detection of rejected topic patterns (3+ repeats), presented to the user in chat for approval before blocking.
5.  **Score Calibration**: Auto-calibration of threshold scores based on bucket acceptance rates.

---

## File Structure

```
rubric-grader/
├── SKILL.md                    # Mode definitions and execution steps
├── README.md                   # This file
└── references/
    └── rubric.md               # Detailed rubric criteria and guidelines
```

### Related Data Files

```
data/
├── rubric_blocklist.md         # Seeded topic and ambiguity veto patterns
├── suggestions_pending.md      # Approved suggestions awaiting review
├── suggestions_filtered.md     # Ephemeral log of rejected suggestions
└── suggestions_reviewed.md     # History of reviewed entries with feedback
```

---

## Skill Modes

### 1. Grade Mode (Programmatic Ingestion)
Executed automatically during ingestion (e.g. website, threads, youtube, newsletter):
*   Reads suggestion details.
*   Checks `PersonalDataRoot/rubric_blocklist.md`. Vetoes if matched.
*   Grades A, P, G dimensions (0, 1, or 2).
*   If composite $\ge 4$: Appends with `📊` format to `PersonalDataRoot/suggestions_pending.md`.
*   If composite $< 4$: Appends to `PersonalDataRoot/suggestions_filtered.md`.

### 2. Backtest Mode (Chat Trigger)
Triggered by asking the agent to "backtest the rubric":
*   Samples 20 Accepted and 20 Rejected entries.
*   Scores them against the rubric.
*   Outputs Accuracy, Precision, Recall, and threshold validation matrix.

### 3. Maintain Mode (Post-Review Loop)
Invoked automatically at the end of suggestion reviews:
*   Scans rejects for 3+ keyword repeats. Prompts the user in the chat to approve additions to the blocklist.
*   If $\ge 30$ rubric-scored entries are reviewed, outputs bucket calibration metrics.

---

## Quality Guardrails

1.  **Deterministic Veto First**: If a suggestion matches any blocked topic or ambiguity phrase, it is immediately discarded before calling LLM grading.
2.  **Strict 0/1/2 Scale**: Simple scoring minimizes criteria drift.
3.  **Human-in-the-Loop Maintenance**: New veto blocks are suggested to the user, not written silently.

---

## Dependencies

*   `content-summary` reference library — delegates suggestion grading to `rubric-grader` during ingestion.
*   `review-suggestions` skill — invokes `rubric-grader` (Maintain mode) after updating the preference profile.

---

## Changelog

| Version | Date | Change Summary |
|---|---|---|
| v1.0.0 | 2026-06-11 | Initial release: Implemented Grade, Backtest, and Maintain modes. Seeded blocklists, filtered suggestions log, and threshold scoring. |
| v1.1.0 | 2026-09-30 | Added Archetype-Content Fit scoring to rubric.md and Forced Prompt Wrapping hard-veto to blocklist (ADR-0001). |
| v1.1.1 | 2026-11-18 | Replace machine-specific rubric and data links with file-relative links. |

---

## Architecture Decisions

### ADR-0001: Dual-Enforcement Anti-Gaming (Archetype-Content Fit & Forced Prompt Wrapping Veto)

**Status**: Accepted · **Date**: 2026-09-30

**Context**: In September 2026, generator agents discovered an incentive gaming loop: appending "15 分鐘" + "不另建自動化工具" to a `data/prompts/` proposal guaranteed a 6/6 rubric score and bypassed the redundancy veto.

**Decision**:
1. Implement cognitive scoring in `rubric.md`: `Preference Alignment (P)` evaluates Archetype-Content Fit. Inappropriate archetypes (e.g., prompt templates for macro news or backend database replication) are penalized with $P \le 1$.
2. Implement deterministic hard veto in `data/rubric_blocklist.md`: "Forced Prompt Wrapping" immediately auto-filters prompt template proposals on macro news, policy, or theoretical architecture.
3. Validate `JIRA_BACKLOG`, `ADR_DOC`, and `TEST_FIXTURE` as valid $A=2$ targets under Actionability.

**Consequences**: Eliminates degenerate prompt gaming, re-aligns rubric scoring with genuine task actionability, and ensures prompt templates are created only when an interactive tool is appropriate.

### ADR-0002 — Resolve reference links from the containing Markdown file

Accepted on 2026-11-18. Skill and reference links use paths relative to the containing Markdown file. Links into `data/` traverse to the repository root. This keeps links resolvable after relocation while retaining the shared repository data dependency.


## Home Repo setup

All required skill files come from this clone. See [macOS setup](../../../docs/setup.md) for the per-skill tool/capability matrix and [publication protocol](../content-summary/references/storage.md) for report workflows. Install external tools separately. Keep personal configuration, accounts and runtime data outside the checkout. For bundled third-party skills, retain the upstream license and provenance in the repository registry.

## ADR: Portable public Home Repo

- **Status:** Accepted.
- **Decision:** Keep reusable skill resources together and resolve report/personal roots from external configuration. Maintenance skills use the selected project; content workflows use the configured report repository.
- **Trade-off:** A report-producing skill needs explicit setup instead of assuming the author's working directory. Unavailable tools/capabilities stop only the affected workflow.

## Changelog — Home Repo migration

- Included complete reusable resources and documented external prerequisites.
- Preserved current workflow behavior and real human suggestion review.
- Removed dependence on personal paths and global companion skill installations.
