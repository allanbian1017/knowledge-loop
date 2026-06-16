# Skill Plan: Rubric Grader for Suggestion Pipeline

Introduce a `rubric-grader` skill that scores AI-generated suggestions against a 3-dimension rubric, automatically filtering low-quality suggestions before they enter the pending review queue. Remove 3 legacy suggestion fields (💎 價值評分, ⚡ 可行動性, 🎯 決策建議) and replace with a single rubric score line.

**RFC**: [rubric-grader.md](../rfc/rubric-grader.md)

---

## Proposed Changes

### 1. rubric-grader (New Skill)

#### [NEW] [SKILL.md](.agents/skills/rubric-grader/SKILL.md)
- Set frontmatter with `name: rubric-grader` and description.
- Implement 3-mode skill:
  - **Grade mode**: Read `references/rubric.md` and `data/rubric_blocklist.md`. Apply hard-veto check → deterministic ambiguity check → 3-dimension rubric scoring. If pass (≥4/6): append to `data/suggestions_pending.md`. If fail: append to `data/suggestions_filtered.md` with score and reason.
  - **Backtest mode**: Accept sample size parameter (default 20+20). Read `data/suggestions_reviewed.md`, stratified sample by accept/reject. Score each suggestion against rubric. Output accuracy table (accept rate per score bucket, threshold validation).
  - **Maintain mode**: (a) Read `data/suggestions_reviewed.md`, detect 3+ rejection patterns on same topic/keyword → append to `data/rubric_blocklist.md`. (b) If ≥30 scored+reviewed suggestions exist: compute rubric calibration (accept rate per score bucket, threshold recommendation). If <30: output "📊 Rubric calibration: {N}/30 — collecting more data."

#### [NEW] [references/rubric.md](.agents/skills/rubric-grader/references/rubric.md)
- Define 3 active rubric dimensions (Actionability, Preference Alignment, Goal Relevance) with 0/1/2 scoring criteria.
- Document 2 future dimensions (Source Grounding, Novelty) with activation criteria.
- Define composite score (0–6) and threshold (≥4).
- Document future retry mechanism (prerequisites, constraints).

---

### 2. Data Files (New)

#### [NEW] [data/rubric_blocklist.md](data/rubric_blocklist.md)
- Seed with known hard-veto patterns from `data/user_preferences.md`:
  - Topic blocks: Claude Code / Cursor, token budget reduction, GPU clustering, blockchain / Web3 / NFT.
  - Ambiguity blocklist: 研究看看, 了解一下, 評估看看, 觀察看看.

#### [NEW] [data/suggestions_filtered.md](data/suggestions_filtered.md)
- Create with heading `# 🚫 Filtered Suggestions`.
- Entry format: date, source type, title, rubric score, suggestion text, filter reason, report link.

---

### 3. content-summary (Shared References)

#### [MODIFY] [ai_analysis.md](.agents/skills/content-summary/references/ai_analysis.md)
- **Remove** field definitions: 價值評分（High / Mid / Low）, 可行動性評估（High / Mid / Low）, 決策建議（Action / Store / Drop）.
- **Keep**: 分類（技術 | 商業 | 心態 | 靈感 | 其他）, 建議下一步（specific [Action + Object + Scope]）.
- **Update** Prerequisites: remove references to 價值評分 and 決策建議 calibration from `user_preferences.md`.
- **Add** at the end: rubric grading delegation — "After determining the suggestion fields above, use the `rubric-grader` skill to grade the suggestion. Follow the skill's instructions for pass/fail handling."

#### [MODIFY] [suggestion_log.md](.agents/skills/content-summary/references/suggestion_log.md)
- Update entry format: replace `🏷️ {分類} | 💎 {價值評分} | ⚡ {可行動性} | 🎯 {決策建議}` with `🏷️ {分類} | 📊 {total}/6 (A:{n} P:{n} G:{n})`.

#### [MODIFY] [README.md](.agents/skills/content-summary/README.md)
- Document rubric-grader integration.
- Update field list (remove 3 deprecated fields, add rubric score).

---

### 4. review-suggestions (Skill Update)

#### [MODIFY] [SKILL.md](.agents/skills/review-suggestions/SKILL.md)
- **Step 3** (Present artifact): Update display format — replace `💎 High | ⚡ High | 🎯 Action` with `📊 5/6`.
- **Step 5** (Update files): Update reviewed entry format to match new schema.
- **Step 6**: Remove §6-4 Decision Calibration (no longer applicable — 🎯 field removed).
- **Step 6 (end)**: Add one line: "After regenerating the preference profile, use the `rubric-grader` skill (maintain mode)."

#### [MODIFY] [README.md](.agents/skills/review-suggestions/README.md)
- Update suggestion entry format examples to match new schema.

---

### 5. Backlog Update

#### [MODIFY] [backlog.md](backlog.md)
- Update Backlog #4 sub-items:
  - ✅ Rubric-based filter — implemented (rubric-grader skill, grade mode)
  - ✅ Preference grounding — implemented (hard-veto blocklist + soft rubric)
  - ✅ De-duplication of blocklist patterns — implemented (maintain mode)
  - ⏳ Dreaming Memory Aggregator — deferred (separate workstream)
- Update Backlog #1 sub-item:
  - ✅ Suggestion Relevance grading — implemented (Goal Relevance dimension)

---

## Verification Plan

### Automated Tests

- **What to test**: Rubric backtest accuracy on historical suggestions.
  - **How to test**: Invoke rubric-grader skill in backtest mode with default 20+20 sample.
  - **Expected behavior**: ≥80% of accepted suggestions score ≥4; ≥60% of rejected suggestions score <4. If thresholds not met, adjust rubric criteria or threshold before launch.

- **What to test**: Suggestion entry format compliance.
  - **How to test**: After first daily-workflow run post-launch, `grep "📊" data/suggestions_pending.md` and `grep "💎\|⚡\|🎯" data/suggestions_pending.md`.
  - **Expected behavior**: All new entries contain `📊 Rubric:` line. No new entries contain `💎`, `⚡`, or `🎯`.

- **What to test**: Hard-veto blocklist enforcement.
  - **How to test**: Create a test suggestion about "Claude Code" and invoke rubric-grader skill (grade mode).
  - **Expected behavior**: Suggestion is hard-vetoed and appended to `data/suggestions_filtered.md` with reason "Hard-veto: Claude Code".

- **What to test**: Deterministic ambiguity blocklist enforcement.
  - **How to test**: Create a test suggestion with `建議下一步: 研究看看這個工具` and invoke rubric-grader skill (grade mode).
  - **Expected behavior**: Suggestion is auto-failed and appended to `data/suggestions_filtered.md` with reason "Ambiguity blocklist: 研究看看".

### Live Validation (after 1 week)

- Compare pre-rubric acceptance rate (70.9% baseline) vs. post-rubric.
- Review `data/suggestions_filtered.md` for false positives (good suggestions incorrectly filtered).
- Target: acceptance rate ≥80% on post-rubric suggestions.
