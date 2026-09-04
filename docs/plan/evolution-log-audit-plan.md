# Implementation Plan - Add Audit Function to Evolution-Log Skill

Add an automated audit function to the `/evolution-log` skill, enabling it to detect and remediate nonexistent commit hashes, broken markdown links, and missing file references across both standalone audit invocations and generation/update verification cycles.

## User Decisions (from /grill-me)

- **Agent-Pure Execution**: Implemented entirely via prompt instructions in `SKILL.md` using standard shell primitives (`git cat-file`, `test -f`, Python one-liners), adhering to the *Zero-Script Agent Skill Design* preference. No bespoke helper scripts.
- **Dual-Role Lifecycle**: Available as an on-demand audit mode (`"audit my evolution log"`, `"check evolution log for missing files or commits"`) and enforced as a mandatory Step 7 quality gate in Generate/Update modes.
- **Intent-Driven with Propose-then-Confirm**: Diagnostic requests present audit findings in an Artifact; remediation/clean-up requests propose the diff and require explicit user confirmation before applying in-place edits.
- **Context-Aware Historical Heuristics**: Distinguishes between hallucinated phantom files (which never existed in git or RFCs, and should be removed) and legitimate historically deleted/renamed artifacts (which existed in past experiments and are discussed in past tense, and should be preserved in narrative context).

---

## Proposed Changes

### `evolution-log` Skill Core (`/Users/allanbian/.gemini/config/skills/evolution-log/`)

#### [MODIFY] [SKILL.md](file:///Users/allanbian/.gemini/config/skills/evolution-log/SKILL.md)
- **Frontmatter Description**: Add audit trigger phrases (`"audit my evolution log"`, `"verify evolution log"`, `"check evolution log for missing files or commits"`, `"clean up evolution log"`, `"audit evolution log"`).
- **Mode Detection**: Add **Audit Mode** alongside Generate Mode and Update Mode.
- **Audit Workflow Section**: Add step-by-step instructions for performing the audit:
  1. Commit Hash Verification: Parse backticked 7-character hex strings and `**Key commit**:` lines; verify via `GIT_CONFIG_GLOBAL=/dev/null git cat-file -t <hash>`.
  2. Relative Markdown Link Verification: Extract `[text](path)` links (non-http) and verify file existence (`test -f <path>`).
  3. Backticked File Verification: Extract backticked filenames/paths and verify existence or check git history (`git log --all --full-history -- <file>`) to distinguish between phantom files and historically deleted files.
  4. Accuracy Cross-Check: Cross-reference high-level metrics against repo reality.
- **Propose-then-Confirm Remediation**: Instructions to present findings and proposed diffs in an Artifact and wait for user confirmation before applying in-place modifications.
- **Step 7 (Save, Audit and Verify)**: Upgrade the verification step to run the audit checks as an automated quality gate ensuring zero phantom commits and zero broken links.

#### [MODIFY] [references/output_template.md](file:///Users/allanbian/.gemini/config/skills/evolution-log/references/output_template.md)
- Add strict rules regarding commit hashes: only real, verified git commit hashes from `git log` may be included. If no specific commits exist for a phase, omit the `**Key commits**:` line or use descriptive milestones.
- Add strict rules against referencing nonexistent test files, uncreated templates, or phantom backlog anchors.

#### [MODIFY] [README.md](file:///Users/allanbian/.gemini/config/skills/evolution-log/README.md)
- Document the new **Audit Mode** and its agent-pure workflow.
- Add **ADR-001**: Architecture Decision Record documenting the problem of LLM hallucination in historical chronicles, options considered (prompt-only rules vs. helper script vs. agent-pure shell inspection), and decision rationale adhering to the Zero-Script preference.
- Add an updated **Changelog**.

#### [MODIFY] [evals/evals.json](file:///Users/allanbian/.gemini/config/skills/evolution-log/evals/evals.json)
- Add a 4th evaluation case for auditing an `EvolutionLog.md` that contains missing files or nonexistent commit hashes.

---

## Verification Plan

### Automated Tests
1. **Skill Frontmatter & Syntax Validation**:
   - **How to test**: `python3 scripts/validate_skill.py /Users/allanbian/.gemini/config/skills/evolution-log/SKILL.md`
   - **Expected behavior**: Returns exit code 0 (`✅ [OK]`).

### Manual & Behavioral Verification
1. **Live Repository Audit**:
   - Run the audit steps defined in `SKILL.md` on `/Users/allanbian/knowledge-loop/EvolutionLog.md`.
   - Verify that 0 phantom commits and 0 missing links are found on the cleaned file.
2. **Documentation & ADR Review**:
   - Verify that `README.md` contains a complete ADR-001 and an updated Changelog.
