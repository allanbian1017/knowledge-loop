# Implementation Plan - 5-Dimension Subscription Rubric Grader

Upgrade `.agents/skills/review-newsletter-subscriptions` to evaluate newsletter subscriptions using a multi-dimensional **Subscription Rubric Grader** ($0 \sim 10$ points), self-contained within the skill.

For the detailed technical architecture, design trade-offs, and decisions, please refer to the corresponding RFC/ADR: [newsletter-subscription-rubric.md](../rfc/newsletter-subscription-rubric.md).

## User Review Required

> [!IMPORTANT]
> **Read Rate Definition**: Read Rate is strictly anchored to the **`## ⭐ Reading Decision`** star rating in the generated report (`推薦指數: [★☆]+`, $\ge 4★$ = read-worthy). It completely ignores whether suggestions were reviewed in `data/suggestions_reviewed.md`, eliminating any noise from delayed human suggestion reviews.
>
> **Uniqueness Evaluation**: Evaluated via **LLM-as-a-Judge** during Step 2 of the audit workflow, matching the user's explicit preference that semantic novelty across the tech ecosystem cannot be captured by deterministic scripts.
>
> **Scope Boundaries**: All changes are strictly confined to `review-newsletter-subscriptions` and its test suite. We will **NOT** modify `rubric-grader`, `ingest-newsletter`, or `review-suggestions`.

---

## Proposed Changes

### Component: `.agents/skills/review-newsletter-subscriptions`

#### [MODIFY] [analyze_subscriptions.py](file:///Users/allanbian/my-ai-workflow/.agents/skills/review-newsletter-subscriptions/scripts/analyze_subscriptions.py)
* Read each report file during discovery to parse `## ⭐ Reading Decision` star ratings (`推薦指數: [★☆]+`) and compute Read Rate ($RR$).
* Multi-source trace for High-value count ($H$): parse user comments in `data/suggestions_reviewed.md` (`add to backlog`, `prompts.md`, `知識庫`), references in `backlog.md`, and citations in `reports/distillations/` to compute High-value Rate ($HR$).
* Compute Volume Cost ($VC$) based on monthly report count ($N$).
* Output individual dimension telemetry ($RR, AR, HR, VC$) in structured JSON and markdown table.

#### [MODIFY] [triage_criteria.md](file:///Users/allanbian/my-ai-workflow/.agents/skills/review-newsletter-subscriptions/references/triage_criteria.md)
* Document the 5 rubric dimensions, scoring formulas, point anchors, LLM-as-a-Judge Uniqueness instructions, and triage mapping.

#### [MODIFY] [review_template.md](file:///Users/allanbian/my-ai-workflow/.agents/skills/review-newsletter-subscriptions/references/review_template.md)
* Update markdown audit template to include the 5-dimension rubric columns and composite score.

#### [MODIFY] [SKILL.md](file:///Users/allanbian/my-ai-workflow/.agents/skills/review-newsletter-subscriptions/SKILL.md) & [README.md](file:///Users/allanbian/my-ai-workflow/.agents/skills/review-newsletter-subscriptions/README.md)
* Update skill documentation to reflect the 5-dimension rubric workflow.
* Add ADR-0005 documenting the 5-Dimension Subscription Rubric design rationale and update Changelog.

---

### Component: Automated Verification

#### [MODIFY] [test_newsletter_subscription_reviewer.py](file:///Users/allanbian/my-ai-workflow/tests/test_newsletter_subscription_reviewer.py)
* Add unit test for Reading Decision star rating extraction regex.
* Add unit test for High-value action comment and citation detection.
* Add unit test for Volume Cost and telemetry calculation.
* Verify skill validation (`scripts/validate_skill.py`) passes.

---

## Verification Plan

### Automated Tests
- **Run Skill Unit Tests**:
  ```bash
  python3 tests/test_newsletter_subscription_reviewer.py
  ```
  Expected: All tests pass (exit code 0), verifying star extraction, high-value rate, volume cost, and table formatting.
- **Skill Validation**:
  ```bash
  python3 scripts/validate_skill.py .agents/skills/review-newsletter-subscriptions/SKILL.md
  ```
  Expected: `✅ [OK]` frontmatter validation and line budget checks pass.

### Manual Verification
- Run live telemetry:
  ```bash
  python3 .agents/skills/review-newsletter-subscriptions/scripts/analyze_subscriptions.py --days 30
  ```
  Verify the markdown table renders the dimensions clearly and accurately reflects the past 30 days of newsletters.
