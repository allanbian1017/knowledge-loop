# Task Tracker: Agents That Dream

- [ ] **Phase 1: Establish Trace Logging**
  - [ ] Define the exact JSON schema for a `Trace` object (Goal, Steps, Result, Skill Name).
  - [ ] Modify `agent-browser` (as the first test candidate) to output a `Trace` file to `.tmp/traces/trace_[timestamp].json` upon completion.
  - [ ] Ensure `.tmp/traces/` is ignored by git but maintained locally.

- [ ] **Phase 2: Build the Dreamer Engine**
  - [ ] Create a new skill directory: `.agents/skills/agent-dreamer/`.
  - [ ] Write the `SKILL.md` detailing the Dreamer's standard operating procedure.
  - [ ] Implement `script.py` for the Dreamer that:
      - [ ] Reads all files in `.tmp/traces/`.
      - [ ] Constructs a prompt asking the LLM to identify recurring errors or critical missing context.
      - [ ] Outputs a specific, single-sentence lesson (if applicable).
      - [ ] Clears the processed traces from `.tmp/`.

- [ ] **Phase 3: Implement Memory Injection**
  - [ ] Extend the Dreamer's `script.py` to support programmatic file modification.
  - [ ] Ensure the script appends the extracted lesson to `.agents/skills/[Skill X]/SKILL.md` under `## Known Gotchas & Lessons`.
  - [ ] Ensure the script appends a timestamped changelog entry to `.agents/skills/[Skill X]/README.md`.

- [ ] **Phase 4: Integration**
  - [ ] Update `.agents/skills/daily-workflow/SKILL.md` to trigger the `agent-dreamer` skill as its final cleanup step.
  - [ ] Perform a dry-run test: manually fail an `agent-browser` task, trigger the Dreamer, and verify the `SKILL.md` and `README.md` injections.
