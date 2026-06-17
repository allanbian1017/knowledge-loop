# AGENTS.md

## Project

This is an AI workflow template for building a **personal content intelligence pipeline**. It automates daily knowledge digestion — ingesting newsletters, YouTube videos, social media posts, and web articles — then summarizing, distilling, and surfacing actionable insights through AI-powered suggestions.

Built for [Antigravity](https://blog.google/technology/google-deepmind/) (Google's agentic coding assistant) with a modular skill-based architecture.

## Constraints

- Strict Tool Enforcement & Fail-Fast: Always use the specific tools/APIs documented in a skill (`SKILL.md`). Do not use alternative tools, write custom helper scripts, or use fallback methods if the designated tools fail or cannot be used. If a specified tool cannot be used or fails, stop immediately, report the failure, and notify the user for intervention.
- Do not propose manual testing. Always use automated tests to verify your changes.
- Don't assume. Don't hide confusion. Surface tradeoffs. Before implementing:
    - State your assumptions explicitly. If uncertain, ask.
    - If multiple interpretations exist, present them - don't pick silently.
    - If a simpler approach exists, say so. Push back when warranted.
    - If something is unclear, stop. Name what's confusing. Ask.
- Use relative workspace links or web-accessible URLs instead of absolute paths for workspace references (e.g. avoid absolute local `file:///` paths that break when the repository is checked out on another machine).

## Conventions

- When implementing a change, make every change as simple as possible, with minimal code changes. Do not over-engineer.
    - No features beyond what was asked.
    - No abstractions for single-use code.
    - No "flexibility" or "configurability" that wasn't requested.
    - No error handling for impossible scenarios.
    - If you write 200 lines and it could be 50, rewrite it.
- When making any changes, pause and implement the most elegant solution known. Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify. Do not rush through tasks.
- Touch only what you must. When editing existing code:
    - Don't "improve" adjacent code, comments, or formatting.
    - Don't refactor things that aren't broken.
    - Match existing style, even if you'd do it differently.
    - If you notice unrelated dead code, mention it - don't delete it.
- Clean up only your own mess. When your changes create orphans:
    - Remove imports/variables/functions that YOUR changes made unused.
    - Don't remove pre-existing dead code unless asked.
- Transform tasks into verifiable goals, and never propose manual testing. All verification steps must strictly use the following structure:
    - What to test: [description]
    - How to test: [description]
    - Expected behavior: [description]
- Before marking the task as complete, you should always complete the automated test and verify it passes.
- When identifying a bug, find root causes, not symptoms. Do not make temporary or "hacky" fixes.

## Project Specific Instructions
- Eagerly check `data/user_preferences.md` at the start of any session to identify the `Preferred Report Language` (for generated summaries and reports) and `Preferred Conversation Language` (for direct user communication) and adhere to both strictly.
- When identifying a bug or unexpected behavior, you should always document it in `docs/rca/` with the naming convention: `<workflow_name>_rca_<YYYY-MM-DD>_V<version>.md`.
    - Root cause conclusions must be supported by quantitative evidence (e.g., measured counts, script output, grep results). Qualitative descriptions alone do not constitute proof. If a claim cannot be verified with a tool, it must be labelled a hypothesis, not a conclusion.
    - An RCA document must always include: observed problem, root cause (primary + contributing), fix applied, and status checklist.
    - RCA docs must link back to the affected skill and its SKILL.md and README.md if available.
    - Before naming a primary root cause, explicitly document and reject all alternative hypotheses with measured evidence.
- When summarizing any external content (like emails or newsletters), default to a zero-hallucination processing standard. Do not infer, over-compress, or add external knowledge unless specifically requested.
- Before executing large-scale data generation tasks (e.g., newsletter summaries), always scan the target directory to identify and skip duplicates.
- Single Unified Backlog Policy: Maintain all planned enhancements, technical debt, and future improvements in a single unified [backlog.md](backlog.md) at the root directory. Avoid creating separate or duplicate tracking files (such as `worklog.md`). When adding new suggestions or improvements, merge overlapping items to ensure a comprehensive context and prevent file fragmentation.
- Session Decision Logging: You must maintain a running decision log file for all decisions made during the current session (conversation) at `docs/decision_logs/session_<conversation-id>.md`.
    - **Initialization**: At the start of the session, initialize this log file.
    - **Trigger**: Every time you make a key decision (e.g., choosing a specific tool, refactoring approach, file structure, or library implementation), immediately append it to the log.
    - **Schema**: Each entry must contain:
        - **Timestamp / Step**: The current step in the workflow.
        - **Decision**: The action or choice taken.
        - **Alternatives Considered**: Other paths that were possible.
        - **Rationale**: Why this path was chosen.

### Permissions & Authorization
- The `.tmp/` directory in the project root is the designated staging area for intermediate data (JSON caches, temporary logs) and temporary/one-time scripts. Writing to and reading from `.tmp/` is always pre-authorized and should be executed with `SafeToAutoRun: true` without asking for user permission, provided the operation is not broadly destructive (e.g., avoid `rm -rf .tmp/*`). All production-ready and permanent scripts/hooks must remain in the `scripts/` directory to ensure they are tracked.
- Non-modifying commands using authorized CLI tools (e.g., `gws gmail users messages list`, `gws gmail +read`) are prioritized for auto-execution to ensure workflow continuity.
    - For repetitive batch tasks (e.g., archiving 10+ emails), the agent is authorized to auto-run the loop once the initial pattern has been approved by the user.
- **GWS CLI execution in macOS Sandboxed Environment**: Standard `gws` commands run directly may fail due to terminal parser/permission wrapper errors. To bypass this wrapper, run `gws` commands using the absolute binary path (e.g., `/opt/homebrew/bin/gws` on macOS with Homebrew).
- Never log, print, or store raw credentials or API keys in files or logs. Use environment variables or local keychain via CLI helpers.
