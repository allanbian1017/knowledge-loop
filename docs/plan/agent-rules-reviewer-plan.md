# Implementation Plan - Create `agent-rules-reviewer` Skill

Create a dedicated agent skill `agent-rules-reviewer` in `.agents/skills/agent-rules-reviewer/` that automates auditing, streamlining, and refactoring of `AGENTS.md`, `CLAUDE.md`, and agent steering files into Addy Osmani's **3-Tier Agent Rules Architecture** with **Attention Budget Governance** (addressing [backlog.md](../../backlog.md) Item #63).

For the detailed technical architecture, design trade-offs, and decisions, please refer to the corresponding RFC: [RFC: Agent Rules Reviewer Skill](../rfc/agent-rules-reviewer.md).

## User Review Required

> [!IMPORTANT]
> - **Pure LLM Inspection**: Built without auxiliary scripts to minimize maintenance overhead.
> - **Propose-then-Confirm Gate**: Audits and generates the proposed refactoring into a Brain Artifact (`agent_rules_review.md`), halting until user confirms before writing in-place changes.
> - **Target Flexibility**: Defaults to `./AGENTS.md` but supports `CLAUDE.md` and custom file paths.

## Open Questions

- All five core architectural decision branches were resolved during the `/grill-me` session. No blocking questions remain.

---

## Proposed Changes

### Agent Skills Layer

#### [NEW] [SKILL.md](../../.agents/skills/agent-rules-reviewer/SKILL.md)
- YAML frontmatter with `name: agent-rules-reviewer` and triggering phrases (`review AGENTS.md`, `audit AGENTS.md`, `optimize agent rules`, `3-tier agent rules`, `attention budget governance`).
- 4-stage Lean Spine (<200 lines) workflow:
  1. *Measure & Audit*: Measure line count, estimated tokens, and negative constraint keyword density (`MUST`, `NEVER`, `ALWAYS`, `DO NOT`).
  2. *Classify & Triage*: Map rules against the 5 audit vectors (Self-duplication, Base LLM baseline, System prompt conflicts, Skill domain leakage, Negative constraint bloat).
  3. *3-Tier Restructuring*: Structure into Tier 1 (Always Do), Tier 2 (Ask First), and Tier 3 (Never Do).
  4. *Deliver Review Artifact & Wait for Confirmation*: Output the review artifact (`agent_rules_review.md`) and concise inline chat summary, prompting user for approval before in-place modification.

#### [NEW] [three_tier_architecture.md](../../.agents/skills/agent-rules-reviewer/references/three_tier_architecture.md)
- Reference document explaining Addy Osmani's 3-Tier model and Attention Budget Governance:
  - Definition of the three tiers and concrete examples.
  - Why negative micro-rules lead to rule drift.
  - Conversion rules to reframe negative constraints into positive Tier 1 defaults or clear Tier 3 invariants.

#### [NEW] [audit_criteria.md](../../.agents/skills/agent-rules-reviewer/references/audit_criteria.md)
- Detailed checklist for evaluating directives across the 5 audit vectors:
  - Self-Duplication patterns.
  - Base model hygiene vs domain constraints.
  - System prompt conflicts (e.g. host `file:///` URLs vs portable repo paths).
  - Skill domain leakage.
  - Unenforceable aphorisms.

#### [NEW] [review_template.md](../../.agents/skills/agent-rules-reviewer/references/review_template.md)
- Standardized markdown template for the review artifact:
  - Header & Target File Metadata.
  - Attention Budget Telemetry (Lines, Estimated Tokens, Negative Keywords Before/After).
  - Audit Findings by Vector.
  - Proposed 3-Tier Drop-in Replacement.
  - Confirmation instructions.

#### [NEW] [evals.json](../../.agents/skills/agent-rules-reviewer/evals/evals.json)
- Realistic eval benchmark test cases covering `AGENTS.md`, `CLAUDE.md`, and legacy instruction sets.

---

### Verification Layer

#### [NEW] [test_agent_rules_reviewer.py](../../tests/test_agent_rules_reviewer.py)
- Automated unit test verifying:
  1. YAML frontmatter syntax and required fields (`name`, `description`) via `scripts/validate_skill.py`.
  2. Existence and non-emptiness of all referenced markdown documents (`three_tier_architecture.md`, `audit_criteria.md`, `review_template.md`).
  3. Syntax and schema validity of `evals/evals.json`.
  4. Lean Spine compliance (`SKILL.md` line count < 250 lines).

---

## Verification Plan

### Automated Tests
- **What to test**: Skill frontmatter validation and structural integrity of `agent-rules-reviewer`.
  - **How to test**:
    ```bash
    python3 scripts/validate_skill.py .agents/skills/agent-rules-reviewer/SKILL.md
    pytest tests/test_agent_rules_reviewer.py -v
    ```
  - **Expected behavior**: All validation checks pass with exit code 0.

### Manual Verification
1. Verify that `agent-rules-reviewer` is discoverable by the skill loader.
2. Confirm the skill references are properly linked with relative paths.
