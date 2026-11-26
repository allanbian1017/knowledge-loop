# RCA: `[ADR_DOC]` Monoculture in the Suggestion Queue

- **Date**: 2026-11-26 | **Version**: V1 | **Status**: Awaiting approval (no fix implemented)
- **Affected skills**: [content-summary](../../.agents/skills/content-summary/README.md) (`references/ai_analysis.md`), [rubric-grader](../../.agents/skills/rubric-grader/README.md) (`references/rubric.md`), [review-suggestions](../../.agents/skills/review-suggestions/SKILL.md)
- **Related**: [RCA 2026-09-29 V2](daily_workflow_rca_2026-09-29_V2.md) (the earlier `PROMPT_TEMPLATE` monoculture), [audit 2026-11-20, open question 5](../daily_workflow_deterministic_audit_2026-11-20.md)

## Symptom
`data/suggestions_pending.md` holds 56 items; **54 (96%) are `[ADR_DOC]`**. Nearly every Newsletter/Website item since 2026-11-14 produces the same "write 1 ADR into `docs/adr/`" suggestion.

## Evidence

| Metric | Value |
|---|---|
| Pending by archetype | ADR_DOC 54, JIRA_BACKLOG 1, PROMPT_TEMPLATE 1, TEST_FIXTURE 0 |
| Pending ADR_DOC score | 53 × 6/6, 1 × 4/6 (the rubric cannot discriminate) |
| Pending ADR_DOC sources | Newsletter 36, Website 17, Threads 1 |
| Reviewed ADR_DOC | 123, all "accept", all with the comment `accept` |
| Reviewed ADR_DOC dates | **121 on 2026-11-13 (one batch)**, 2 on 2026-11-09 |
| Batch result 2026-11-13 | 180 reviewed / 180 accepted (0 rejects) |
| Does `docs/adr/` exist? | **No.** Zero ADRs written despite 123 accepted. The only decision doc is `docs/decisions/2026-09-04_kill_item_62_prompt_profiler.md` |
| Template boilerplate | 53/54 end with "不另建自動化工具/代碼" |
| Theme overlap (pending ADRs) | verification/judge ≈ 22, sandbox/isolation ≈ 17, multi-agent boundaries ≈ 10 |
| Topics that are not the user's decisions | ≥ 7 (Instacart LoRA/FP8, DoorDash Dispatch, Prefill-Decode/KV cache, agent payments, …) |

## Root Causes

1. **ADR_DOC is the catch-all for "architecture-flavored" content.**
   [`ai_analysis.md` L25-27](../../.agents/skills/content-summary/references/ai_analysis.md#L25-L27) defines it as "trade-offs, anti-patterns, selection boundaries". Almost any technical article matches. `TAKEAWAY_ONLY` is the intended alternative, but nothing makes it the default for "interesting but no decision to record".
2. **An ADR records a decision *you made*; these are essays about someone else's system.**
   The template turns "article describes trade-off X" into "write an ADR about X". For Instacart, DoorDash, KV cache and similar topics, the user has no decision to document. The action is really `TAKEAWAY_ONLY`.
3. **The rubric rewards the format, not the substance.**
   [`rubric.md` L18-21](../../.agents/skills/rubric-grader/references/rubric.md#L18-L21): Actionability = 2 whenever the archetype tag, scope and time estimate are present. Preference Alignment = 2 for "system architecture → `JIRA_BACKLOG` or `ADR_DOC`" (L32). Goal Relevance is easy to satisfy given the goals. The result is 6/6 for nearly everything, so the 4/6 pass bar filters nothing.
4. **Positive feedback loop through `user_preferences.md`.**
   The 2026-11-13 rubber-stamp batch (180/180, comment `accept`) was recorded as a strong preference: "Documentation / ADRs 94.5%", "ADR proposals … accepted and preferred", plus the 2× recency weighting. `ai_analysis.md` tells the worker to "prefer the user's preferred action types", so more ADRs are generated and more reach the queue. The same loop caused the earlier `PROMPT_TEMPLATE` monoculture.
5. **Acceptance does not mean execution, and nothing connects the two.**
   `docs/adr/` was never created and no ADR was ever drafted. Accepting is cheap, producing an ADR costs 15 minutes, so the backlog is a queue of items nobody is going to complete. The "acceptance rate" signal then reports false value.
6. **No deduplication or diversity guard.**
   There is no check against existing ADRs or pending items, so about 40 near-duplicate themes accumulate. The tests ([`test_suggestion_archetypes.py`](../../tests/test_suggestion_archetypes.py)) verify that the archetype names exist, not their distribution. The 2026-09-29 RCA fix was forward-only and prompt-level only, and it only banned the *PROMPT_TEMPLATE* monoculture. The same pressure moved to the next archetype that the rubric rewards.

## Proposed Fix (not applied; needs approval)

| # | Change | Layer |
|---|---|---|
| 1 | **Tighten ADR_DOC eligibility** in `ai_analysis.md`: allowed only when the content forces a *decision in this repo* (name the decision and the alternatives in this workflow). Otherwise use `TAKEAWAY_ONLY`. Add a negative list: third-party system internals, industry case studies, infrastructure the user does not operate. | Prompt |
| 2 | **Add a rubric rule**: ADR_DOC requires a named in-repo decision. Without it, Preference Alignment ≤ 1 (so a fail or borderline score). Remove ADR_DOC from the automatic "architecture → 2" mapping. | Rubric |
| 3 | **Deterministic dedup and cap** in the grade/apply step (matches the planned `suggestion_ops.py apply-grades` in the 2026-11-20 audit): normalized-theme similarity check against pending/reviewed ADRs, and a cap such as ≤ 3 pending `ADR_DOC` items per day or ≤ 30% of the queue. | Code |
| 4 | **Exclude bulk batches from preference learning**: reviews with identical comments, or ≥ 50 items in one session, count as "unreviewed signal" and are not recorded as `Preferred` or given 2× weighting. | `review-suggestions` / profile |
| 5 | **Close the execution gap**: decide whether ADRs go in `docs/adr/` or the existing `docs/decisions/`. Fix the path in the template, and optionally track "accepted but not implemented" counts. | Process |
| 6 | **Backlog triage** (needs your decision): archive or consolidate the 54 pending ADRs. Group the ~40 overlapping themes into 3-5 real ADRs (e.g. *Author/Verifier separation*, *Sandbox/permission boundaries*, *Single vs multi-agent*) and send the rest to `TAKEAWAY_ONLY`. | Data |

## Verification Plan (after approval)
- **What**: pytest cases for (a) the ADR eligibility rules in `ai_analysis.md` and `rubric.md`, (b) the dedup/cap logic, (c) the bulk-batch exclusion.
- **How**: `python3 -m pytest -p no:recording --ignore=tests/test_compile_session_learnings.py tests/test_suggestion_archetypes.py` plus new tests, and `python3 scripts/validate_skill.py` on both modified skills.
- **Expected**: synthetic "Instacart/DoorDash-style" payloads route to `TAKEAWAY_ONLY` or fail the grade. In a replay of the last 10 days of ADR items, the pending ADR share falls below 30% and duplicates are collapsed.
