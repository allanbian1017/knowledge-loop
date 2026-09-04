# Implementation Plan - `decision-sparring` Skill (9 Decision Mental Models)

Build a specialized conversational & analytical Agent Skill, `decision-sparring`, that stress-tests decisions, eliminates cognitive biases, resolves analysis paralysis, and breaks through procrastination using Nicolas Cole's 9 Decision Mental Models (synthesized from 朱騏's newsletter).

## User Review & Alignment (Resolved via `/grill-me`)

| Branch | Decision Resolved | Rationale |
|---|---|---|
| **1. Operational Scope** | Both personal/career dilemmas & technical trade-offs | Activated whenever the user is in analysis paralysis, procrastination, or hesitating between competing options. Distinct from `/grill-me` which stress-tests structured plans/architectures. |
| **2. Interaction Cadence** | **Adaptive Hybrid** | Asks 1 sharp diagnostic question if input is brief/vague; goes straight to the 4-part Action Contract if context is rich or user asks for a quick verdict. |
| **3. Model Selection** | **Targeted Top 3–4 Lenses** | Internally screens all 9 models, but displays only the top 3–4 most discriminating lenses to eliminate cognitive bloat and token waste. |
| **4. Rendering & Persistence** | **In-Chat First -> Artifact for Final Conclusion** | Keeps interactive dialogue in chat to maintain conversational velocity; renders the finalized Action Contract as an Artifact for clean reference. |
| **5. Action Contract Anatomy** | **4-Part Contract (Format B)** | 1. Primary Constraint (True Blocker), 2. 15-Min Micro-Experiment, 3. The Stop List, 4. Decision Checkpoint (Go / No-Go rule). |
| **6. Implementation Architecture** | **Zero-Script Pure Markdown** | Aligned with user preference: pure LLM inspection and reasoning, avoiding bespoke helper scripts. |

---

## Proposed Changes

### New Skill: `.agents/skills/decision-sparring/`

#### [NEW] [SKILL.md](../../.agents/skills/decision-sparring/SKILL.md)
* Core spine (< 200 lines): triggers, adaptive routing, and progressive disclosure to references.

#### [NEW] [mental_models.md](../../.agents/skills/decision-sparring/references/mental_models.md)
* Deep reference for the 9 mental models and domain lens selection matrix.

#### [NEW] [action_contract_template.md](../../.agents/skills/decision-sparring/assets/action_contract_template.md)
* Standardized 4-part Action Contract template with Go / No-Go Decision Checkpoints.

#### [NEW] [evals.json](../../.agents/skills/decision-sparring/evals/evals.json)
* 3 realistic test prompts for skill evaluation and regression checks.

---

## Verification Plan

### Automated Tests
- **Skill Validation**:
  - `python3 scripts/validate_skill.py .agents/skills/decision-sparring/SKILL.md`
  - Expected behavior: Pass all frontmatter and schema validation rules with exit code 0.
- **Evaluation Assertions**:
  - Verify eval cases in `evals/evals.json` against the 4-part contract schema.

### Manual Verification
1. Invoke the skill with a real dilemma (e.g. "I can't decide whether to refactor X or build Y").
2. Check that the identified bottleneck is non-obvious and the 15-minute micro-experiment is directly actionable with an explicit Go / No-Go checkpoint.
