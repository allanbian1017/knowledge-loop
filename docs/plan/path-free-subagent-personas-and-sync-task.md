# Tasks: Path-Free Custom Sub-Agent Personas & Cross-Platform Sync

- [x] **Phase 1: Single Source of Truth Setup**
  - [x] Create `.agents/agents/` directory if it does not exist.
  - [x] Create `.agents/agents/newsletter_worker.md` (AGY Schema + Persona Prompt).
  - [x] Create `.agents/agents/threads_worker.md` (AGY Schema + Persona Prompt).
  - [x] Create `.agents/agents/website_worker.md` (AGY Schema + Persona Prompt).
  - [x] Create `.agents/agents/youtube_worker.md` (AGY Schema + Persona Prompt).
  - [x] Create `.agents/agents/rubric_grader.md` (AGY Schema + Persona Prompt).
  - [x] Create `.agents/agents/distiller_reviewer.md` (AGY Schema + Persona Prompt).
  - [x] Enforce tool scoping rule: `tools:` specifies domain CLI/MCP tools only (`gws-gmail`, `agent-browser`, `yt2doc`); native workspace file primitives (`view_file`, `write_to_file`) are omitted from `tools:` to preserve runtime compatibility.


- [x] **Phase 2: Sync Script Implementation**
  - [x] Create `scripts/sync_subagents.py`.
  - [x] Implement scanner for `.agents/agents/*.md`.
  - [x] Implement AGY YAML Schema validation.
  - [x] Implement **Claude Code Translation Logic** (preserve/format YAML frontmatter, prepend DO NOT EDIT header, write to `.claude/subagents/*.md`).
  - [x] Implement **OpenAI Codex Translation Logic** (convert YAML metadata + prompt body to native TOML configuration files `.codex/subagents/*.toml` & `.codex/agents/*.toml`).
  - [x] Ensure script prints clean CLI status output upon completion.

- [x] **Phase 3: Dispatch Workflow Update**
  - [x] Identify workflow files/scripts using subagent paths (e.g. `dispatch_spec.md`, `daily-workflow`).
  - [x] Update invocations to use logical path-free names (e.g. `newsletter_worker`).
  - [x] Update execution logic to pass dynamic parameters (e.g. `<MESSAGE_ID>`) as the **First User Message** / Task Argument (to preserve persona caching).

- [x] **Phase 4: Verification & Validation**
  - [x] Execute `python3 scripts/sync_subagents.py`.
  - [x] Verify targets in `.claude/subagents/` contain YAML frontmatter.
  - [x] Verify targets in `.codex/subagents/` and `.codex/agents/` are valid TOML configuration files with `developer_instructions`.
  - [x] Execute `python3 scripts/validate_skill.py`.

