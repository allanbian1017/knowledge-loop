# Implementation Plan: Agents That Dream

## Overview
This document outlines the detailed execution plan for the "Agents That Dream" asynchronous reflection architecture. It covers the end-to-end integration of tracing, background batch processing (the Dreamer), and memory injection.

For the rationale and architectural trade-offs, please refer to the corresponding ADR at [docs/rfc/agents-that-dream.md](../rfc/agents-that-dream.md).

## Phase 1: Establish Trace Logging (The "Waking" Phase)
- **Objective**: Standardize the output of complex skills into a parseable `Trace` artifact.
- **Details**:
    - We will define a strict JSON schema for traces containing `Goal`, `Steps`, `Result`, and `Skill Name`.
    - We will target `agent-browser` as the first skill. We'll modify its logic to dump a final trace into `.tmp/traces/trace_[timestamp].json`.
    - We will ensure `.tmp/traces/` is ignored by git, as these are ephemeral artifacts meant to be consumed and deleted by the Dreamer.

## Phase 2: Build the Dreamer Engine (The "Dreaming" Phase)
- **Objective**: Create the core background processor that extracts lessons from traces.
- **Details**:
    - We will establish a new skill directory at `.agents/skills/agent-dreamer/`.
    - The skill will be powered by a Python script (`script.py`) that:
        1. Reads and aggregates all traces in the `.tmp/traces/` directory.
        2. Queries the LLM to identify specific, actionable anti-patterns or success rules.
        3. Formats the lesson into a single concise sentence.
        4. Archives or clears the processed traces to prevent duplicate analysis.

## Phase 3: Implement Memory Injection (The "Evolution" Phase)
- **Objective**: Persist the learned lessons into the local context of the affected skills.
- **Details**:
    - The Dreamer's script will be extended to programmatically locate the target skill's `SKILL.md`.
    - It will append the new lesson under a dedicated `## Known Gotchas & Lessons` heading.
    - Concurrently, it will insert a timestamped changelog entry in the target skill's `README.md` to ensure the injection is auditable.

## Phase 4: Integration & Verification
- **Objective**: Tie the workflow together and prove it functions autonomously.
- **Details**:
    - We will inject the `agent-dreamer` skill as the final background step of the `daily-workflow`.
    - To verify, we will intentionally trigger a failure mode in `agent-browser`, run the Dreamer, and manually confirm that the lesson is injected into `agent-browser`'s context files.
