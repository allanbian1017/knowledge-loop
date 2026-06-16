# RFC: Agents That Dream (Asynchronous Background Reflection)

## Summary

Implement an asynchronous background reflection loop ("Agents That Dream") to evaluate execution traces during downtime. This mechanism extracts permanent, specific rules and injects them locally into the corresponding skill's context, ensuring agents learn continuously without suffering from global context bloat.

## Status

**Proposed** — 2026-05-19

## Motivation

Currently, our AI agents (e.g., `agent-browser`, `ingest-newsletter`) suffer from "amnesia." When they encounter a novel edge case, hallucinate a tool call, or get stuck in a loop, they might eventually recover or fail. However, they forget the lesson immediately after the process ends. 

If the agent gets stuck failing to interact with a specific website's DOM structure today, it will make the exact same mistake tomorrow because its memory resets with each new runtime execution.

By decoupling the "Execution Phase" (fast, goal-oriented) from the "Reflection Phase" (slow, analytical), the agent can genuinely get smarter and more customized to the personal workflow every single day, without bloating the context window during active runtime.

## Detailed Design

### The Three Pillars

The architecture consists of three core components:

1. **Trace (The Waking Phase)**
   - Complex skills explicitly log a structured `Trace` artifact (`.json` or `.md`) to `.tmp/traces/` upon completion.
   - This trace contains the agent's goal, intermediate tool calls, errors encountered, and the final success/failure state.

2. **Dreamer (The Dreaming Phase)**
   - An asynchronous batch-processing script (or skill) that runs during downtime (e.g., as part of the `daily-workflow`).
   - It consumes accumulated `Trace` files and evaluates them using an LLM to identify recurring errors, anti-patterns, or successful edge-case navigations.
   - It distills these into specific, single-sentence rules.

3. **Memory Injection (The Evolution Phase)**
   - The process of permanently storing the rules extracted by the `Dreamer`.
   - To prevent global context bloat, the rule is appended locally to the specific skill's `SKILL.md` (e.g., under a `## Known Gotchas & Lessons` section).
   - Concurrently, the skill's `README.md` changelog is updated to reflect the newly injected rule for auditability.

### Workflow Integration
The `agent-dreamer` skill will be added as the final background step in the `daily-workflow`. It will silently process the traces left behind by the day's tasks, clean up the `.tmp/traces/` directory, and update the skill instructions for tomorrow.

## Drawbacks

- **Increased Development Overhead:** Requires modifying existing complex skills to support structured trace generation.
- **LLM Token Costs:** Evaluating traces during the dreaming phase consumes additional tokens daily.
- **Write Access Risks:** The Dreamer requires write access to source files (`SKILL.md`, `README.md`). Erroneous rules could degrade skill performance over time if not audited.

## Alternatives Considered

### Alternative 1: Synchronous/Eager Reflection
Run the reflection LLM call immediately at the end of every agent execution before the process exits.

**Rejected:** This bloats the runtime, consumes extra tokens during active work, and slows down immediate execution. Batch processing during downtime is much more efficient.

### Alternative 2: Global Context Injection
Append all extracted lessons directly to `AGENTS.md` or `user_preferences.md`.

**Rejected:** As the agent learns hundreds of lessons across different skills, the global context will bloat, causing token overflow and attention dilution. Injecting the knowledge locally into the specific `SKILL.md` ensures context remains thin and highly relevant.

## Unresolved Questions

None. All design decisions were resolved during the `grill-with-docs` planning session.

## Implementation Plan

The detailed execution steps and task tracker have been separated into the planning directory for clarity.
- **Plan Details:** `docs/plan/agents-that-dream-plan.md`
- **Task Tracker:** `docs/plan/agents-that-dream-task.md`

---

# ADR: Asynchronous Reflection Architecture

## Status

Proposed — 2026-05-19

## Context

We need a mechanism for agents to learn from their past executions. Raw conversation logs are too noisy for reliable LLM reflection, and appending lessons globally risks degrading reasoning performance via context bloat.

## Decision Drivers

- **Reliability**: Reflection must be based on clear, structured execution data, not raw chat logs.
- **Performance**: Reflection must not slow down active agent execution.
- **Context Efficiency**: Learned rules must not bloat the global system prompt.

## Decisions Made

Three design decisions were resolved during the planning session:

### Decision 1: Structured Tracing over Implicit Logs
**Context**: How to provide input to the reflection engine.
**Decision**: Complex skills will explicitly log a structured `Trace` artifact to `.tmp/traces/` rather than relying on raw Antigravity brain logs.
**Rationale**: Structured logging provides a cleaner input for the LLM, isolating exactly what the agent attempted and where it failed.

### Decision 2: Asynchronous Batch Processing
**Context**: When to trigger the reflection phase.
**Decision**: Build an `agent-dreamer` script that runs asynchronously as a batch process at the end of the day.
**Rationale**: Acts like real dreaming—consolidating memories during downtime to avoid bloating the runtime and consuming extra tokens during active work.

### Decision 3: Local Memory Injection
**Context**: Where to store the extracted lessons permanently.
**Decision**: The Dreamer will append the rule directly to the specific skill's `SKILL.md` (e.g., under a `## Known Gotchas & Lessons` section) rather than a global `AGENTS.md`.
**Rationale**: Ensures that the lesson is only loaded into the context window when that *specific skill* is invoked, keeping the agent highly focused and token-efficient.

## Consequences

### Positive
- Agents become continuously smarter and self-correcting for edge cases.
- Global context (`AGENTS.md`) remains clean and concise.
- Trace logs provide a clear, queryable history of agent actions for debugging.

### Negative
- Requires upfront investment to instrument existing skills with tracing.
- Extracted rules could theoretically conflict if the Dreamer LLM hallucinates an incorrect fix.

## References
- Newsletter: "Claude Mythos breaks into Apple's M5" (concept of "Agents That Dream")
- `data/user_preferences.md` — guidelines on maintaining thin global context.
