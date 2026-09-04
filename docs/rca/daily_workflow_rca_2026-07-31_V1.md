# RCA: Daily Workflow — Subagent initialization failure due to invalid tool name (`no tool converter registered for read_file`)

## 1. Observed Problem

When invoking the subagent `rubric_grader` during Step 4 (or `distiller_reviewer` during Step 5) of the `daily-workflow`, subagent creation fails immediately with the error message:

```
failed to construct executor: no tool converter registered for read_file
```

This prevents `invoke_subagent` from constructing the subagent execution container, causing the subagent to halt before processing any tasks.

---

## 2. Alternative Hypotheses & Rejection Evidence

The following hypotheses were evaluated and rejected before identifying the root cause:

- **Hypothesis A**: The failure is caused by missing permission grants for file reading/writing in the sandbox workspace.
  - *Rejection evidence*: The main agent and worker subagents (`website_worker`) perform file reading (`view_file`) and writing (`write_to_file`, `replace_file_content`) without permission errors. The error `no tool converter registered for read_file` occurs at executor instantiation time inside the platform engine, prior to any file I/O invocation.

- **Hypothesis B**: The failure is caused by an invalid or missing `rubric-grader` skill path or YAML syntax in `.agents/skills/rubric-grader/SKILL.md`.
  - *Rejection evidence*: Running `python3 scripts/validate_skill.py` confirmed that all skills pass YAML frontmatter and required field validation (`✅ [OK] .agents/skills/rubric-grader/SKILL.md`).

- **Hypothesis C**: Subagents with `enable_write_tools: true` cannot be launched by `invoke_subagent`.
  - *Rejection evidence*: Worker subagents such as `website_worker` have `enable_write_tools: true` and successfully launched and executed 4 tasks in parallel during the same session.

---

## 3. Root Cause — Primary + Contributing

### 3.1 Primary Root Cause

**Invalid Tool Names (`read_file`, `write_file`) in Subagent Frontmatter (`tools`)**

In `.agents/agents/rubric_grader.md` and `.agents/agents/distiller_reviewer.md`, the `tools:` field in the YAML frontmatter was explicitly defined as:

```yaml
tools:
  - read_file
  - write_file
```

In Google Antigravity, built-in file operations are exposed as native tools (`view_file`, `write_to_file`, `replace_file_content`, `list_dir`, etc.). `read_file` is not a registered native tool converter in the platform's executor engine. When `invoke_subagent` parses `tools:` and attempts to look up a converter for `"read_file"`, it throws `failed to construct executor: no tool converter registered for read_file`.

### 3.2 Contributing Root Causes

- **Legacy Skill/Agent Spec Overlap**: Original RFC specifications listed `read_file` and `write_file` generically when describing subagent persona capabilities.
- **Session Configuration Pre-loading**: Subagent configurations in `.agents/agents/*.md` are loaded into memory at session startup. Modifying existing subagent persona files on disk fixes future sessions, but in-session invocations for existing registered subagent names re-use the pre-cached schema.

### 3.3 Architectural Rationale — Why Built-In Primitives Are Not Listed in `tools:`

1. **Capability Flags vs. Specific Domain Tools**: Native workspace primitives (`view_file`, `grep_search`, `write_to_file`, etc.) are enabled globally or via capability boolean flags (e.g. `enable_write_tools: true`). The `tools:` array in YAML frontmatter is strictly reserved for registering domain-specific CLI or MCP tools (such as `gws-gmail`, `agent-browser`, `yt2doc`).
2. **Built-in Primitives Are Already Active**: Subagents automatically inherit workspace reading and writing capabilities natively. Specifying built-in primitives like `view_file` in `tools:` is redundant and can break platform executor construction if the string name doesn't match an explicit converter registration.
3. **Cross-Platform Portability**: Native file tool method names vary across runtimes (`view_file` in AGY vs `View` in Claude Code vs `read_file` in Codex). Using `tools: []` for pure file-processing subagents preserves cross-platform compatibility without coupling persona definitions to specific runtime function names.


---

## 4. Fix Applied & Status Checklist

### 4.1 Fixes Applied

1. **Cleaned Subagent YAML Frontmatter**: Modified `.agents/agents/rubric_grader.md` and `.agents/agents/distiller_reviewer.md` to remove `read_file` and `write_file` from `tools:`, setting `tools: []`.
2. **Synchronized Platform Configs**: Executed `python3 scripts/sync_subagents.py` to propagate the updated YAML definitions across `.claude/` and `.codex/`.
3. **Verified Subagent Construction**: Defined and invoked `rubric_grader_v2` with `tools: []`, confirming that subagent executor construction succeeds cleanly without `no tool converter registered for read_file` errors.
4. **Updated Known Issues Registry**: Appended the error and resolution to `known_issues.md`.

### 4.2 Status Checklist

- [x] Documented failure in `docs/rca/daily_workflow_rca_2026-07-31_V1.md`
- [x] Removed invalid tool names from `.agents/agents/rubric_grader.md` and `.agents/agents/distiller_reviewer.md`
- [x] Executed `python3 scripts/sync_subagents.py` to sync changes
- [x] Verified clean subagent construction using `rubric_grader_v2`
- [x] Logged entry in `known_issues.md`

---

## 5. References

- Affected skill: [daily-workflow/SKILL.md](../../.agents/skills/daily-workflow/SKILL.md)
- Subagent persona definition: [rubric_grader.md](../../.agents/agents/rubric_grader.md)
- Subagent persona definition: [distiller_reviewer.md](../../.agents/agents/distiller_reviewer.md)
- Subagent sync script: [sync_subagents.py](../../scripts/sync_subagents.py)
- Known Issues: [known_issues.md](../../known_issues.md)
