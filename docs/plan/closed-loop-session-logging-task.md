# Task Tracker: Closed-Loop Session Logging

- [ ] **Phase 1: Build the Compiler Script**
  - [ ] Create the script file `scripts/compile_session_learnings.py`.
  - [ ] Implement markdown table parsing to extract rows from `docs/decision_logs/session_[id].md`.
  - [ ] Filter out `Success` outcomes and extract `Failed/Error/Blocked/Fallback` outcomes.
  - [ ] Add deduplication checks against existing entries in `learnings/lessons.md`.
  - [ ] Implement appending formatting to append lessons under the correct markdown heading.

- [ ] **Phase 2: Update Workspace Instructions**
  - [ ] Modify the decision logging table schema in `AGENTS.md` to include `Outcome & Learning`.
  - [ ] Add the startup Bootstrap checklist (loading lessons, scanning for any Pending logs) to `AGENTS.md`.
  - [ ] Add the Wrap-up checklist (filling distilled outcomes, running compiler script) to `AGENTS.md`.

- [ ] **Phase 3: Testing & Verification**
  - [ ] Create a test suite `tests/test_compile_session_learnings.py` using `pytest`.
  - [ ] Verify parsing of mock log files.
  - [ ] Verify deduplication matches.
  - [ ] Run dry-run manual test with mock session log and confirm formatting in `learnings/lessons.md`.
