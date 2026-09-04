# Agent Rules Reviewer — Task Checklist

**RFC**: [agent-rules-reviewer.md](../rfc/agent-rules-reviewer.md)  
**Plan**: [agent-rules-reviewer-plan.md](agent-rules-reviewer-plan.md)

---

## Phase 1: Reference Documents & Evaluation Benchmarks

- [x] Create `.agents/skills/agent-rules-reviewer/references/three_tier_architecture.md`
  - Document Addy Osmani's 3-Tier model (Tier 1 Always Do, Tier 2 Ask First, Tier 3 Never Do).
  - Document Attention Budget Governance and rule drift mechanics.
  - Document negative-to-positive conversion heuristics.
- [x] Create `.agents/skills/agent-rules-reviewer/references/audit_criteria.md`
  - Document the 5 audit vectors (Self-duplication, Base LLM baseline, System conflicts, Skill leakage, Bloat).
  - Include concrete good/bad rule classification examples.
- [x] Create `.agents/skills/agent-rules-reviewer/references/review_template.md`
  - Define the structured schema for `agent_rules_review.md` artifact.
  - Include Telemetry Table, Findings by Vector, 3-Tier Proposed Draft, and Confirmation Checkpoint.
- [x] Create `.agents/skills/agent-rules-reviewer/evals/evals.json`
  - Define 3 benchmark test cases (`AGENTS.md` audit, `CLAUDE.md` multi-platform audit, negative-constraint compaction).

## Phase 2: Core Skill Definition (`SKILL.md`)

- [x] Create `.agents/skills/agent-rules-reviewer/SKILL.md`
  - Write YAML frontmatter (`name`, `description` with pushy triggering keywords).
  - Document 4-stage Lean Spine (<200 lines) workflow.
  - Document Propose-then-Confirm interaction protocol and Brain Artifact generation.
  - Document reference pointers with progressive disclosure.

## Phase 3: Automated Verification Suite

- [x] Create `tests/test_agent_rules_reviewer.py`
  - Test skill frontmatter validation via `scripts/validate_skill.py`.
  - Test reference files existence and non-emptiness.
  - Test `evals/evals.json` syntax and schema conformance.
  - Test Lean Spine compliance (SKILL.md line count budget).
- [x] Run automated tests:
  - `python3 scripts/validate_skill.py .agents/skills/agent-rules-reviewer/SKILL.md`
  - `pytest -p no:recording tests/test_agent_rules_reviewer.py -v`

## Phase 4: Preferences Persistence

- [x] Append confirmed preferences from the `/grill-me` session to `/Users/allanbian/.gemini/config/skills/grill-me/preferences.md`.
