# Tasks: `decision-sparring` Skill Implementation

## 1. Skill Structure & Core Spine
- [x] Create directory `.agents/skills/decision-sparring/` and subdirectories (`references/`, `assets/`, `evals/`)
- [x] Write `.agents/skills/decision-sparring/SKILL.md` (Lean Spine < 200 lines, YAML frontmatter, adaptive hybrid routing)

## 2. References & Templates
- [x] Write `.agents/skills/decision-sparring/references/mental_models.md` (detailed guide for the 9 models + Lens Selection Matrix)
- [x] Write `.agents/skills/decision-sparring/assets/action_contract_template.md` (standardized 4-part contract with Go/No-Go Decision Checkpoints)

## 3. Evaluation & Verification
- [x] Write `.agents/skills/decision-sparring/evals/evals.json` (3 realistic test cases: tech stack choice, procrastinated task, shiny distraction)
- [x] Run `python3 scripts/validate_skill.py .agents/skills/decision-sparring/SKILL.md` (automated schema & link check passed)
- [x] Run full repository skill validation across all 31 skills (all passed)
- [x] Run automated integrity check script on contract template sections, model counts, and line limits

## 4. Documentation & Preferences
- [x] Update `preferences.md` for `grill-me` with new confirmed preferences
- [x] Sync `docs/plan/decision-sparring-skill-plan.md`
- [x] Create `docs/plan/decision-sparring-skill-task.md`
