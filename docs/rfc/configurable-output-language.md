# RFC: Configurable Output Language for AI Workflows

## Summary

This Request for Comments (RFC) proposes making the output language of all intelligence reports (newsletters, Threads, YouTube, websites, daily distillations, and GitHub repository studies) globally configurable via the user preference profile (`data/user_preferences.md`). If no language is explicitly configured, the system defaults to **English** to maintain backward compatibility.

## Status

**Proposed** (Approved in Design review) — 2026-06-16

## Motivation

Currently, the default language for summaries and reports in the content intelligence pipeline is hardcoded to Traditional Chinese in multiple places, while the `study-github-repo` skill is hardcoded to English. 

Users want a way to configure their preferred reading language globally. By replacing hardcoded language instructions in the skills and reference files with dynamic instructions that refer to the user's preference profile, we can support multi-language output (e.g. English, Traditional Chinese, etc.) across the entire workspace.

---

## Detailed Design

### 1. Configuration Storage (`data/user_preferences.md`)

We will add a new `## Configuration` section at the top of the existing `data/user_preferences.md` profile:

```markdown
## Configuration
- **Preferred Output Language**: Traditional Chinese（繁體中文）
```

If this setting is absent, empty, or invalid, the system automatically falls back to **English**.

### 2. Reference & Prompts Updates

-   **`content-summary/references/summarise.md`**:
    Update the `## Language` section to instruct the agent to check the configured language in `data/user_preferences.md` and generate all report headers and summaries in that language.
-   **`daily-distiller/SKILL.md`**:
    Update the synthesis step to check the configuration and write the daily distillation document in the preferred language.
-   **`study-github-repo/SKILL.md`**:
    Update Step 7 (Write Report) to check the configuration and generate the repository analysis report in the preferred language.
-   **Ingest Skills (`ingest-*` folders)**:
    Update descriptions and steps in `SKILL.md` files to refer to the "configured output language summary" instead of hardcoding "Traditional Chinese".

### 3. Verification & Validation Script

We will introduce a Python script `scripts/validate_language_config.py` that parses the configuration and runs static checks on the skill files to ensure no hardcoded language rules remain in the procedures.

---

## Drawbacks

-   **Agent Interpretation Overhead**: Adding a lookup step slightly increases the instructions length, but since these are markdown-based text prompts, the performance impact on LLM reasoning is negligible.
-   **Translation/Summarisation Quality**: Prompting the LLM to output in a specific language dynamically may introduce slight variations in style compared to hardcoded instructions. This is mitigated by defining clear fallbacks and templates.

---

## Alternatives Considered

-   **Option 2: Dedicated JSON Configuration File (`data/config.json`)**:
    Create a separate JSON file for settings.
    *Rejected*: The codebase uses Markdown files for all user-level profile tracking (`goals.md`, `user_preferences.md`). Adding a JSON file introduces a new format and file unnecessarily.
-   **Option 3: Dedicated Markdown Configuration File (`data/config.md`)**:
    Create a separate configuration Markdown file.
    *Rejected*: `user_preferences.md` is already loaded by the agent to grade goals and align recommendations. Reusing this file keeps the workspace clean and avoids file fragmentation.
-   **Keeping `study-github-repo` strictly in English**:
    *Rejected*: The user explicitly requested that repository studies should also respect the configured output language.

---

## Implementation Plan

1.  Modify `data/user_preferences.md` to add the configuration block.
2.  Update `content-summary/references/summarise.md` language rules.
3.  Update `ingest-newsletter/SKILL.md`, `ingest-threads/SKILL.md`, `ingest-website/SKILL.md`, and `ingest-youtube/SKILL.md`.
4.  Update `daily-distiller/SKILL.md`.
5.  Update `study-github-repo/SKILL.md`.
6.  Create `scripts/validate_language_config.py` for automated validation.

---

# ADR: Output Language Configuration Storage

## Context

We need to store a persistent user configuration for the preferred output language of the agent's reports.

## Decision

We will store the setting in the existing `data/user_preferences.md` file under a new `## Configuration` section:

```markdown
## Configuration
- **Preferred Output Language**: <Language>
```

## Consequences

-   **Easy editing**: The user can easily change the language by editing the Markdown file.
-   **Context preservation**: The agent already reads `data/user_preferences.md` as part of the ingestion pipeline (for suggestion calibration), meaning no additional files need to be opened/tracked.
