# RFC: Closed-Loop Session Logging

## Summary

Implement a closed-loop session logging framework to capture developer experience lessons (e.g., terminal blocks, tool exceptions, sandbox configuration errors) during active sessions, distill them automatically, and propagate them to subsequent sessions via a tiered memory architecture.

## Status

> **Status: Superseded** by [simplify-session-logging-to-known-issues.md](simplify-session-logging-to-known-issues.md) (2026-07-29)

**Proposed** — 2026-06-17

## Motivation

Our AI agents currently maintain a session-specific decision log file at `docs/decision_logs/session_<conversation-id>.md`. However, this log has three main limitations:
1. **Write-Only Amnesia**: Subsequent sessions never read past logs, so the agent starts with no awareness of past session blocks.
2. **Missing Outcomes (Open-Loop)**: The log captures the decision *intent* and *rationale* before execution, but never records whether the action succeeded, failed, or required a fallback.
3. **Token Bloat**: Reading all past raw logs (1,100+ lines of markdown) in future sessions would waste context tokens and dilute the model's focus.

By introducing a closed-loop lifecycle, we can parse session-level failures, distill them into actionable rules, and feed them into subsequent sessions without context bloat.

## Detailed Design

The architecture is divided into four main pillars:

```
[Session Start] ──> [1. Bootstrap Loader] ──> [2. Active Logging]
       ▲                                               │
       │                                               ▼
[Future Session] <── [4. Tiered Pruning] <── [3. Wrap-up Compiler]
```

### 1. Pillar 1: Schema Update
We modify the running decision log schema in `AGENTS.md` to include an `Outcome & Learning` column. During the session, execution steps are initially marked `Pending`. When a step finishes (or at wrap-up), the agent records the outcome:
* **Success**: The action succeeded without issues.
* **Failed: [Reason]**: The action failed.
* **Fallback: [Action]**: The action failed and required an alternative path.

### 2. Pillar 2: Agent Wrap-up Protocol
We define a strict "Session Wrap-up Protocol" in `AGENTS.md`. Before returning the final message to the user, the agent:
1. Reviews its conversation history and updates any `Pending` entries in `docs/decision_logs/session_<conversation-id>.md`, distilling any failures or fallbacks into a single, concise actionable rule in the `Outcome & Learning` column.
2. Triggers the compilation script: `python3 scripts/compile_session_learnings.py <conversation-id>`.


### 3. Pillar 3: Automation Compiler Script
The script `scripts/compile_session_learnings.py` is written in Python to ensure 100% accurate file parsing and safety:
* **Noise Filter**: Reads the session log and discards all rows with standard `Success` outcomes.
* **Extraction**: Extracts rows containing keywords like `Failed`, `Error`, `Blocked`, or `Fallback`.
* **Deduplication**: Reads `learnings/lessons.md` first. If a lesson matching the same tool/context already exists, it skips appending.
* **Append**: Distills the failure/fix into a bullet point under a `## Active Gotchas & Lessons` section in `learnings/lessons.md`.

### 4. Pillar 4: Memory Tiering and Pruning
We establish a Tiered Memory Hierarchy to keep the context thin:
* **Tier 1 (Short-term)**: Raw session tables in `docs/decision_logs/` (retained for manual audits/git history).
* **Tier 2 (Medium-term)**: Centralized gotchas list in `learnings/lessons.md` (read by future agents at startup).
* **Tier 3 (Long-term)**: Permanent instructions in `AGENTS.md` or specific skill `SKILL.md` files.
* **Pruning Rule**: When a Tier 2 gotcha is officially resolved in the source code or permanent instructions, it is removed from `learnings/lessons.md` to prevent clutter.

### 5. Pillar 5: Lazy Recovery Bootstrap
At session start, the agent reads `learnings/lessons.md` into context. Additionally, it scans all files in `docs/decision_logs/session_*.md` (excluding the current session's log file) for the term `Pending`. If any logs contain `Pending` outcomes (indicating a crash, interruption, or parallel session termination), the agent automatically runs the compilation script on those files to recover all leftover lessons.


## Alternatives Considered

### Alternative 1: Asynchronous Dreamer Reflection (RFC 1)
Using the async `agent-dreamer` to process traces from `.tmp/traces/` and inject rules into `SKILL.md`.
* **Conclusion**: Co-exists with Option B. Dreamer handles *algorithmic/skill* execution traces during daily workflows. Option B handles *interactive developer friction* (shell environment, wrapper configuration, auth gates) immediately after active sessions.

### Alternative 2: Manual LLM Lesson Injection
Instructing the LLM to edit `learnings/lessons.md` directly without a script.
* **Rejected**: Writing markdown files and checking for duplicates via LLM is error-prone, slow, and prone to duplicate inflation. A script handles this with 100% formatting fidelity.

## Consequences

* **Positive**: Agents starting a new session instantly inherit learnings from the previous session's command failures.
* **Negative**: Requires adding a checklist to `AGENTS.md` and running one extra tool call at wrap-up.

---

# ADR: Closed-Loop Session Logging Architecture

## Status

Proposed — 2026-06-17

## Context

We need a mechanism to capture developer friction and tool/command failures (gotchas) from active developer-agent sessions and propagate them to subsequent sessions, preventing the agent from repeating past mistakes. The current session logs are write-only, lack outcome status (success/failure), and would cause token bloat if read raw.

## Decision Drivers

- **Zero Token Bloat**: The context window at startup must not be bloated by multi-hundred-line raw tables.
- **Reliability**: Distillation and write logic must be robust and formatting-safe (avoiding LLM file-writing bugs).
- **Zero Runtime Friction**: The wrap-up process must be fast and sandboxed (no manual sandbox-bypass prompts at session end).
- **Multi-session Support**: Must safely handle parallel sessions or consecutive session crashes.

## Decisions Made

Five design decisions were resolved during the planning and design grill sessions:

### Decision 1: Option B (Closed-Loop Session Log Post-Mortem)
- **Decision**: Adopt a closed-loop session logging model over standard tools or async tracing for session gotchas.
- **Rationale**: Best suited for capturing interactive developer experience gotchas (auth walls, terminal permission quirks) that are conversation-specific, complementing the async skill-level traces in Option A.

### Decision 2: Tool-Based Classification & Header Checks
- **Decision**: Script-based deduplication using tool-based headers in `learnings/lessons.md`.
- **Rationale**: Groups lessons by tool sections, providing clear formatting and allowing cheap, deterministic keyword-based deduplication without expensive semantic vector lookups or LLM queries.

### Decision 3: "Scan-for-Pending-State" Bootstrap Recovery
- **Decision**: Sweep all log files in `docs/decision_logs/session_*.md` for the term `Pending` (excluding the current session's log file) during the bootstrap startup phase.
- **Rationale**: Solves the concurrent/consecutive session crash recovery issue, ensuring any interrupted log gets compiled and resolved, regardless of chronological file ordering.

### Decision 4: Agent-Side Distillation with Script-Based Copy
- **Decision**: The active LLM agent distills the lesson into a single-sentence gotcha during wrap-up, and a local Python script handles the file appending.
- **Rationale**: Keeps the Python compilation script simple, fast, and sandboxed (no outbound API calls needed), avoiding sandbox-bypass triggers during wrap-up, while leveraging the LLM's semantic context to summarize the issue.

### Decision 5: Manual/Developer Promotion-Time Pruning
- **Decision**: Remove gotchas manually from `learnings/lessons.md` when they are promoted to permanent files (e.g. `AGENTS.md` or code updates).
- **Rationale**: Prevents accidental deletion of unpatched gotchas via automated TTL/aging, linking pruning directly to code fixes.

## Consequences

### Positive
- Future agents start every session with immediate awareness of recent environment/tool failures.
- No sandbox-bypass friction during session wrap-up.
- High formatting safety and robustness against duplicate logs.
- Memory remains highly focused and token-efficient.

### Negative
- Adds a small wrap-up prompt compliance checklist to `AGENTS.md`.
- Requires executing one compiler tool call at the end of active sessions.

