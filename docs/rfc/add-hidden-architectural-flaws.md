# RFC: Add 5 Hidden Architectural Flaws Dimension to study-github-repo

## Summary

Propose adding a 14th dimension to the `study-github-repo` skill that requires identifying 5 hidden architectural flaws in plain sight. This includes documenting the exact file and line number for each flaw, along with an assessment of its impact on future maintainability.

## Motivation

Evaluating a repository's architecture requires more than just understanding its design patterns and boundaries; it also requires identifying potential pitfalls, technical debt, and maintenance challenges. 

By explicitly requiring the identification of "hidden flaws in plain sight," we force the agent to perform a more critical evaluation of the codebase. Furthermore, demanding exact files and line numbers ensures the analysis remains grounded in reality and reduces the likelihood of generic, unhelpful AI hallucinations. This addition will help users make better-informed decisions on whether to trust, use, or extend the studied project.

## Detailed Design

The implementation requires updates to both the skill instructions and the output template:

1. **Update `SKILL.md`**:
   - Update the dimension count from 13 to 14.
   - Add a new item to `Phase 3: Deep Analysis`:
     `7. **Hidden Architectural Flaws** — Identify exactly 5 architectural flaws hidden in plain sight. Pinpoint the exact file paths and line numbers, and evaluate their impact on future maintainability.`

2. **Update `assets/output_template.md`**:
   - Insert a new section `## 14. 5 Hidden Architectural Flaws` immediately before `## Key Learnings`.
   - Add a prompt blockquote for the AI: `> "Identify 5 architectural flaws hidden in plain sight. For each, list the exact file and line number, and evaluate its impact on future maintainability."`
   - Provide a markdown table template with columns: `Flaw`, `File & Line`, and `Impact on Future Maintainability`.

## Drawbacks

- **Increased Report Length**: The final report will be slightly longer.
- **Potential for Hallucination**: Despite the file and line number requirement, the agent may still struggle to identify *genuine* architectural flaws in very clean codebases, potentially leading to nitpicking.
- **Token Usage**: Deeply analyzing code for specific flaws requires comprehensive context, which may increase token usage and processing time.

## Alternatives

1. **Integrate into Existing Sections**: Instead of adding a 14th dimension, this requirement could be merged into the existing `## 11. Tradeoffs & Constraints` or `## 12. Repo Health` sections. However, creating a dedicated section ensures the 5 flaws are prominently highlighted and formatted consistently.
2. **Variable Flaw Count**: Instead of strictly demanding 5 flaws, we could ask for "up to 5" to account for exceptionally clean codebases. The current design strictly asks for 5 to enforce rigor.

## Unresolved Questions

- What should the agent do if a repository is exceptionally well-architected and genuinely lacks 5 identifiable flaws? Should it state this factually, or is it always expected to find at least 5 areas for improvement?
- Does the prompt structure provide enough guidance for the agent to differentiate between minor code smells and true "architectural flaws"?

## Implementation Plan

1. [x] Update `SKILL.md` to reflect the 14th dimension.
2. [x] Append the `14. 5 Hidden Architectural Flaws` section to `assets/output_template.md`.
3. [ ] (Pending) Test the updated skill on a sample GitHub repository to verify that the agent correctly identifies 5 flaws with accurate line numbers and actionable maintainability assessments.
