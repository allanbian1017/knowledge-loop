# RFC: Anti-Cache Guardrails for Ingestion Skills

## Summary

Add explicit anti-cache instructions to ingestion skills and a staging area cleanup step to the daily workflow, preventing agents from hallucinating cache-lookup behaviors that silently reuse stale local files.

## Status

**Proposed** — 2026-06-18

## Motivation

On 2026-06-18, the daily workflow processed a Facebook task URL. Instead of performing a fresh network fetch as instructed by [ingest-website/SKILL.md](../../.agents/skills/ingest-website/SKILL.md), the agent autonomously scanned `.tmp/`, found a 10-day-old file named `facebook_body.txt`, associated it with the current task by string matching on "facebook", and produced a hallucinated report based on stale content. The task was then marked as completed. Full analysis in [daily_workflow_rca_2026-06-18_V1.md](../rca/daily_workflow_rca_2026-06-18_V1.md).

### Why the original backlog proposals are over-engineered

The RCA proposed two backlog items:

- **Backlog Item 29** (Canonical URL Resolution & Cache Mirroring) — attempts to resolve redirect URLs and store snapshots. This addresses auditability, not the root cause. Facebook/Instagram canonical resolution consistently fails behind login walls, making this unreliable for the exact URLs that triggered the bug.

- **Backlog Item 30** (Cryptographic Cache Keys & Validation Gates) — proposes hash-based filenames, TTL enforcement, and metadata validation. However, **no caching protocol exists in any skill**. No skill references `.tmp/` as a cache source. The agent invented the cache-lookup behavior entirely on its own. Building a cache validation framework for a cache that doesn't exist is solving a phantom problem.

### The actual root cause

The real failure is an **instruction-following gap**: the skills tell the agent *what to do* (fetch via Jina Reader) but never explicitly say *what not to do* (never substitute local files for a network fetch). When the agent encountered a URL it couldn't easily resolve, it creatively improvised by scanning the filesystem — a reasonable heuristic in general but catastrophic here.

---

## Detailed Design

### 1. Task-Isolated Subdirectories inside `.tmp/`

To prevent data collision and race conditions when tasks run in parallel, all ingestion skills must write intermediate files to task-specific subdirectories rather than the root of `.tmp/`.

- **Naming Convention**: 
  - For Google Tasks: `.tmp/<task_id>/`
  - For Manual triggers / URL invocations: `.tmp/<url_hash>/` (where `<url_hash>` is a unique md5/sha256 hash or slug of the target URL).
- **Prohibition on Root Writing**: Writing generic filenames (e.g. `.tmp/body.txt`, `.tmp/snapshot.txt`) directly to the root of `.tmp/` is strictly prohibited.
- **Task Lifecycle Cleanup**: Every ingestion skill must clean up its own task subdirectory upon successful completion or exit by running `rm -rf .tmp/<task_id>/` (or `.tmp/<url_hash>/`).

#### Modified Instruction Template:
```markdown
> ⛔ **Never** reuse leftover or pre-existing files in `.tmp/` (or any other directory)
> from previous runs or different tasks. Every task invocation MUST execute its own
> fresh fetch.
>
> 📂 **Task Isolation**: Create and use a dedicated directory `.tmp/<task_id>/` (or 
> `.tmp/<url_hash>/` if run manually) for all intermediate files. It is only acceptable
> to read files from this directory if they were newly written during the active task's
> current execution sequence.
>
> 🧹 **Task Cleanup**: Delete the directory (`rm -rf .tmp/<task_id>/`) at the end of
> the task lifecycle.
```

**Target skills**:

| Skill | File | Location |
|---|---|---|
| `ingest-website` | [SKILL.md](../../.agents/skills/ingest-website/SKILL.md) | After the Step 1 heading, before Jina Reader fetch, and before Step 5 |
| `ingest-threads` | [SKILL.md](../../.agents/skills/ingest-threads/SKILL.md) | After the Step 1 heading, before agent-browser fetch, and before Step 5 |

> [!NOTE]
> `ingest-youtube` is excluded because it invokes `yt2doc` (an external binary) which handles its own fetching.
> `ingest-newsletter` is excluded because it reads directly from the Gmail API via `gws`, not from a URL-based fetch.

### 2. Pre-Run Staging Area Cleanup in Daily Workflow

Add a Step 0 to [daily-workflow/SKILL.md](../../.agents/skills/daily-workflow/SKILL.md) that clears leftover task subdirectories from previous daily runs:

```markdown
### Step 0 — Clean staging area

Remove leftover task-specific directories from previous runs to prevent stale data interference:

```bash
find .tmp/ -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
```
```

This is a belt-and-suspenders measure: it ensures any task subdirectories that failed to clean up themselves due to unexpected errors/crashes in previous runs are completely wiped before a new day's workflow begins.

**Scope limitation**: The cleanup command only targets subdirectories under `.tmp/`. It leaves root files (email caches, scripts, JSON data) completely untouched.


---

## Drawbacks

- **Negative instruction fragility**: Agents may not always respect "don't do X" instructions as reliably as "do X" instructions. The pre-run cleanup mitigates this.
- **Directory-scoped cleanup**: The `find .tmp/` command will delete all subdirectories (including python's `__pycache__` if present), but since no critical persistent data is stored in `.tmp/` subdirectories, this is safe and resolves the fragility of pattern-specific glops.


---

## Alternatives Considered

- **Implement a full cache validation system (Backlog Item 30)**: Hash-based filenames, TTL enforcement, URL metadata headers.
  - *Rejected*: No caching code exists. Adding validation for a non-existent cache adds instruction complexity without addressing the root cause (the agent should never look for cached files in the first place). This is the definition of over-engineering.

- **Canonical URL resolution for social media (Backlog Item 29)**:
  - *Rejected*: Login-walled platforms (Facebook, Instagram, LinkedIn) actively block programmatic URL resolution. This solves an unrelated auditability concern, not the stale-cache reuse bug.

- **Nuke the entire `.tmp/` directory at the start of each run**:
  - *Rejected*: `.tmp/` contains legitimate long-lived files (email caches, utility scripts, JSON configs). A full wipe would break other workflows.

- **Move to isolated per-run directories** (e.g., `.tmp/run_2026-06-18_1021/`):
  - *Rejected*: Adds structural complexity. The problem is not directory isolation — it's the agent inventing a behavior that no instruction authorized.

---

## Implementation Plan

See [anti-cache-guardrails-plan.md](../plan/anti-cache-guardrails-plan.md).
