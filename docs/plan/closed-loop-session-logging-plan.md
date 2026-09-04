# Implementation Plan - Closed-Loop Session Logging

Implement the Closed-Loop Session Logging framework to record, extract, and propagate developer experience lessons from active conversations.

For the rationale and architectural trade-offs, please refer to the corresponding ADR inside [closed-loop-session-logging.md](../rfc/closed-loop-session-logging.md).

## User Review Required

> [!IMPORTANT]
> This change modifies [AGENTS.md](../../AGENTS.md) to add mandatory "Bootstrap" and "Wrap-up" checklists for all sessions. This ensures the loop executes reliably at the start and end of every session.

## Open Questions

None. The workflow design was aligned in the Option B deep dive.

---

## Proposed Changes

### Configuration & Rules

#### [MODIFY] [AGENTS.md](../../AGENTS.md)
* Modify the decision logging table schema to include the `Outcome & Learning` column.
* Add the **Bootstrap Protocol** at the start of the session (scanning all `session_*.md` files for leftover `Pending` entries to recover crashed sessions, and reading [learnings/lessons.md](../../learnings/lessons.md)).
* Add the **Wrap-up Protocol** at the end of the session (filling log table outcomes with distilled, single-sentence gotchas, and executing `compile_session_learnings.py`).

---

### Scripts & Automation

#### [NEW] [compile_session_learnings.py](../../scripts/compile_session_learnings.py)
* Parse the markdown session log for a given conversation ID.
* Ignore rows with `Success` outcomes.
* Extract rows containing keywords like `Failed`, `Error`, `Blocked`, or `Fallback`.
* Match target tools or context keywords to avoid duplicate entries in [learnings/lessons.md](../../learnings/lessons.md).
* Append new distilled bullet points under a structured heading in [learnings/lessons.md](../../learnings/lessons.md).

---

### Verification Plan

### Automated Tests
* We will write a unit test suite `tests/test_compile_session_learnings.py` to:
  * Assert that a mock decision log table with mixed `Success` and `Failed` outcomes is parsed correctly.
  * Verify that only failures are extracted.
  * Verify that pre-existing lessons are not duplicated in `learnings/lessons.md`.
  * Run the tests using:
    ```bash
    pytest tests/test_compile_session_learnings.py
    ```

### Manual Verification
1. Manually create a mock session log file in `docs/decision_logs/` containing a simulated permission failure and fallback choice.
2. Run the compiler script on the mock session ID.
3. Verify that the distilled gotcha is correctly appended to [learnings/lessons.md](../../learnings/lessons.md) and formatted properly.
4. Run the script again on the same ID to verify that no duplicate is added.
