# Plan: Anti-Cache Guardrails for Ingestion Skills

Prevent agents from hallucinating cache-lookup behaviors by adding explicit anti-cache instructions to ingestion skills and a pre-run staging area cleanup to the daily workflow.

RFC: [anti-cache-guardrails.md](../rfc/anti-cache-guardrails.md)
RCA: [daily_workflow_rca_2026-06-18_V1.md](../rca/daily_workflow_rca_2026-06-18_V1.md)

---

## Proposed Changes

### 1. ingest-website (Anti-Cache Instruction)

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-website/SKILL.md)

- Insert an anti-cache guardrail block immediately after the `### Step 1 — Fetch the website content` heading, before the Jina Reader URL instruction.
- Content to add:

```markdown
> ⛔ **Never** reuse leftover or pre-existing files in `.tmp/` (or any other directory)
> from previous runs or different tasks. Every task invocation MUST execute its own
> fresh fetch.
>
> 📂 **Task Isolation**: Create and use a dedicated directory `.tmp/<task_id>/` (or 
> `.tmp/<url_hash>/` if run manually) for all intermediate files. It is only acceptable
> to read files from this directory if they were newly written during the active task's
> current execution sequence.
```

- Insert a cleanup step in the completion phase before `### Step 5 — Mark the task as completed`:
- Content to add:

```markdown
### Step 4C — Clean up task isolated directory

Delete the intermediate storage folder:

```bash
rm -rf .tmp/<task_id>/
```
```

---

### 2. ingest-threads (Anti-Cache Instruction)

#### [MODIFY] [SKILL.md](../../.agents/skills/ingest-threads/SKILL.md)

- Insert the same anti-cache guardrail block immediately after the `### Step 1 — Fetch the Threads post content` heading, before the `fetch-threads-post` reference.
- Content to add:

```markdown
> ⛔ **Never** reuse leftover or pre-existing files in `.tmp/` (or any other directory)
> from previous runs or different tasks. Every task invocation MUST execute its own
> fresh fetch via `agent-browser`.
>
> 📂 **Task Isolation**: Create and use a dedicated directory `.tmp/<task_id>/` (or 
> `.tmp/<url_hash>/` if run manually) for all intermediate files. It is only acceptable
> to read files from this directory if they were newly written during the active task's
> current execution sequence.
```

- Insert a cleanup step at the end of `### Step 4 — Process Threads tasks` before completion:
- Content to add:

```markdown
### Step 4C — Clean up task isolated directory

Delete the intermediate storage folder:

```bash
rm -rf .tmp/<task_id>/
```
```

---

### 3. daily-workflow (Pre-Run Cleanup)

#### [MODIFY] [SKILL.md](../../.agents/skills/daily-workflow/SKILL.md)

- Insert a new `### Step 0 — Clean staging area` section before the existing `### Step 1 — Discover and classify Delegate tasks`.
- Content to add:

```markdown
### Step 0 — Clean staging area

Remove leftover task-specific directories from previous runs to prevent stale data interference:

```bash
find .tmp/ -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
```
```


---

### 4. Backlog Housekeeping

#### [MODIFY] [backlog.md](../../backlog.md)

- Update **Backlog Item 29** status from `⏳ Pending` to `❌ Rejected — see RFC` with a note explaining rejection rationale (unreliable for walled-garden URLs; addresses auditability, not root cause).
- Update **Backlog Item 30** status from `⏳ Pending` to `🔄 Superseded — see RFC` with a note that the pre-run wipe sub-measure was adopted but the cryptographic cache keys and TTL validation were rejected (no caching system exists).
- Update the RCA status checklist items 80–81 to reference this plan.

---

## Verification Plan

### Automated Tests

- **What to test**: Anti-cache instruction presence in skill files.
  - **How to test**: `grep -c "Never.*reuse leftover or pre-existing files" .agents/skills/ingest-website/SKILL.md .agents/skills/ingest-threads/SKILL.md`
  - **Expected behavior**: Returns count `1` for each file.

- **What to test**: Pre-run cleanup step presence in daily-workflow.
  - **How to test**: `grep -c "Step 0.*Clean staging area" .agents/skills/daily-workflow/SKILL.md`
  - **Expected behavior**: Returns count `1`.

- **What to test**: Cleanup command targets only safe directory patterns under `.tmp/`.
  - **How to test**: `grep "find .tmp/ -mindepth" .agents/skills/daily-workflow/SKILL.md`
  - **Expected behavior**: Command specifically uses directory find/removal to prevent recursive deletion of root files.

