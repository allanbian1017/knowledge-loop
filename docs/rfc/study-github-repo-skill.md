# RFC: `study-github-repo` Agent Skill

**Date**: 2026-05-13
**Status**: Accepted
**Skill**: `.agents/skills/study-github-repo/`

## Summary

Design and implementation of a new on-demand agent skill that analyzes any GitHub repository by cloning it locally and studying it systematically across 13 dimensions, producing a comprehensive English study report.

---

## Motivation

When studying a GitHub repository, the goal is not to read every line of code, but to answer four key questions:

1. What problem does this repo solve?
2. How is it designed?
3. Can I trust/use/extend it?
4. What can I learn from it?

No existing skill in the pipeline addressed this need. The closest skill (`web-to-markdown`) only fetches static page content — it cannot read a codebase, trace execution flows, or analyze architectural patterns. A dedicated skill with local clone access enables deeper, question-driven code analysis.

---

## Design Decisions

### 1. Local Clone vs. GitHub API Only

**Decision**: Clone the repository locally via `gh repo clone`, then read files directly.

**Rejected alternative**: API-only approach (fetch file contents via `gh api repos/{owner}/{repo}/contents/{path}`).

**Rationale**: The central user requirement is understanding *how the repo solves the problem stated in its README*. This demands tracing execution flows end-to-end, which requires reading multiple files along a critical path — not fetching a pre-determined list via API. Local clone gives the agent full filesystem access to read any file it judges relevant.

**Clone specifics**:
- Destination: `.tmp/github_study/{owner}_{repo}/` (project's pre-authorized staging area)
- Shallow clone (`--depth=1`) — full history not needed; commit history is fetched via API
- Deleted after report is written — repos can be large and the report captures all useful content
- HTTPS forced via `-c url.https://github.com/.insteadOf=git@github.com:` to avoid SSH key issues

---

### 2. Code Reading Depth — No Artificial Cap

**Decision**: Question-driven reading with no artificial file limit. The agent reads as many files as needed to answer how the repo delivers on its README promise.

**Rejected alternative**: A tiered approach capping at ~20–30 key files with prescribed selection rules.

**Rationale**: A cap optimizes for context budget over comprehension. The user's explicit requirement is to understand the solution mechanism, not just the shape. The agent uses engineering judgment to know when it has enough understanding. For small repos (< 20 files), this is comprehensive. For large repos (thousands of files), quality naturally varies — this is acceptable for a first version.

**Guidance in SKILL.md**: "No artificial file cap. Use engineering judgment to determine when you have enough understanding to explain how the repo delivers on its README promise."

---

### 3. Varying Quality for Large Repos

**Decision**: Accept varying quality across repo sizes. Small utility libraries get thorough reports; large monorepos may have gaps.

**Rationale**: Iterating on quality requires real usage data. Imposing an artificial scope constraint (e.g., "focus on core module only") adds complexity before we know which repos the skill will be used against. The skill will note what it couldn't cover when relevant.

---

### 4. Report Output Path — No Date Subdirectory

**Decision**: `reports/GitHub/{owner}_{repo}.md` — flat directory, one file per repo, overwritten on re-run.

**Rejected alternative**: `reports/GitHub_YYYY_MM_DD/{owner}_{repo}.md` (matching other ingest skills).

**Rationale**: Other ingest skills (newsletter, threads, YouTube) produce time-series reports — you run them daily and accumulate history. A GitHub repo study is a reference document, not a daily digest. If you re-study a repo, you want the latest view. Using a flat path avoids accumulating stale snapshots while maintaining the `reports/GitHub/` namespace consistent with the project convention.

---

### 5. Independent Skill — No `content-summary` Dependency

**Decision**: `study-github-repo` is fully self-contained. It does not reference `content-summary` for summarization rules, AI analysis, or suggestion logging.

**Rejected alternative**: Reuse `content-summary/references/summarise.md` for quality rules and `ai_analysis.md` for suggestion generation.

**Rationale**: The `content-summary` skill was designed for the Traditional Chinese content intelligence pipeline (newsletters, Threads posts, YouTube videos). Its quality rules (zero-hallucination TC summarization), AI analysis fields (分類, 價值評分), and suggestion log format are domain-specific. A GitHub repo study is a different artifact — English, engineering-focused, structured around a fixed 13-dimension framework. Coupling to `content-summary` would entangle two unrelated domains. The skill is small enough that self-containment is the right tradeoff.

---

### 6. Output Language — English

**Decision**: Report output is in English.

**Rejected alternative**: Traditional Chinese (matching other pipeline reports).

**Rationale**: The 13-factor framework provided by the user is written in English. The subject matter (code, technical architecture, engineering patterns) is inherently English-dominant. The target use case is deep technical study, not daily content digest.

---

### 7. No Google Tasks Integration

**Decision**: Purely on-demand — user provides a GitHub URL directly. No task lifecycle management.

**Rejected alternative**: Integrate with Google Tasks (as `ingest-threads` and `ingest-youtube` do), allowing the Delegate list to queue repo studies.

**Rationale**: GitHub repo studies are ad-hoc exploratory tasks, not a recurring batch workflow. There is no existing pattern of queueing GitHub URLs as Delegate tasks. Adding Tasks integration would add complexity with no current use case.

---

### 8. Report Format — 13-Section Framework

**Decision**: Use the user's 13-factor framework directly as the report structure, in English.

The sections are:
1. Problem & Purpose
2. Mental Model of the System
3. Entry Points
4. Folder Structure & Boundaries
5. Core Abstractions
6. State Management
7. Decision Logic
8. Feedback Loops
9. Developer Experience (DX)
10. Tests
11. Tradeoffs & Constraints
12. Repo Health
13. Engineering Taste

Plus: Executive Summary (top) and Key Learnings (bottom).

**Rationale**: The framework is a complete, principled methodology covering both static structure (architecture, abstractions) and dynamic behavior (execution flow, state, decision logic), plus meta-dimensions (repo health, DX, engineering taste). Using it verbatim ensures the report answers all four executive questions and teaches transferable engineering knowledge.

---

### 9. Private Repo Handling

**Decision**: Handle private repos transparently via `gh` auth. When community health metrics are sparse (e.g., 0 stars, no releases), note factually: "This appears to be a private/internal repository; community health metrics are not applicable."

**Rationale**: `gh` is already authenticated with `repo` scope. No special branching logic needed — the report just reflects what the data shows.

---

### 10. Metadata Collection Strategy

**Decision**: Collect repo metadata via `gh api` before cloning, in parallel with the clone.

Data collected:
- Repo overview (stars, forks, language, license, topics, description)
- Language breakdown
- Recent releases (last 5)
- Top contributors (top 10)
- Recent commits (last 30)
- Recent issues (last 10, all states)
- Recent PRs (last 10, all states)

**Rationale**: API calls are fast and lightweight. Gathering metadata upfront means the Repo Health section (section 12) can be populated with quantitative data from the first step, before any code reading begins.

**Implementation note**: All `gh api` URLs must be wrapped in single quotes in zsh to prevent glob expansion on `?` and `&` query parameters.

---

## Final Architecture

```
User provides GitHub URL
        ↓
Step 1: Parse owner/repo from URL
        ↓
Step 2: Gather metadata (gh api) ──→ stars, forks, commits, issues, PRs
        ↓
Step 3: Clone to .tmp/github_study/{owner}_{repo}/ (--depth=1, HTTPS)
        ↓
Step 4: Phase 1 — Orientation
        Read README → extract problem statement
        List directory structure (find)
        Read config files (package.json, pyproject.toml, etc.)
        Scan docs/ and examples/
        ↓
Step 5: Phase 2 — Trace Execution Flow
        Identify entry points
        Trace critical path end-to-end
        No file cap — engineering judgment
        ↓
Step 6: Phase 3 — Deep Analysis
        Core abstractions, state, decision logic, feedback loops, tests, DX
        Use grep/ripgrep for cross-codebase pattern search
        ↓
Step 7: Write report to reports/GitHub/{owner}_{repo}.md
        All 13 sections + Executive Summary + Key Learnings
        ↓
Step 8: Cleanup — rm -rf .tmp/github_study/{owner}_{repo}/
```

---

## Verification

Verified against `sindresorhus/slugify` (public, small, clean):

| Check | Result |
|---|---|
| Report at `reports/GitHub/sindresorhus_slugify.md` | ✅ |
| All 15 section headers present | ✅ |
| No empty sections | ✅ |
| Clone directory cleaned up | ✅ |

Three bugs were found and fixed during verification testing:
1. SSH clone failure → forced HTTPS via `-c url.https://github.com/.insteadOf=git@github.com:`
2. `gh api` URL glob expansion in zsh → single-quoted all API URLs
3. `tree` not installed → replaced with portable `find` command

---

## Files Created

| File | Description |
|---|---|
| `.agents/skills/study-github-repo/SKILL.md` | Main 8-step skill procedure |
| `.agents/skills/study-github-repo/assets/output_template.md` | 13-section report template |
| `.agents/skills/study-github-repo/README.md` | Skill usage documentation |
| `reports/GitHub/sindresorhus_slugify.md` | Verification test report |

---

# ADR: `study-github-repo` — Standalone Skill with Local Clone

## Status

Accepted

## Context

The project's existing skills focus on content ingestion from newsletters, social posts, and videos. No skill existed for deep technical analysis of source code repositories. The user wanted a systematic way to study a GitHub repo and produce an engineering-quality report covering architecture, design decisions, code quality, and repo health — following a specific 13-dimension framework.

## Decision Drivers

- **Depth**: Must trace actual execution flows, not just read static documentation
- **Independence**: Repo studies are ad-hoc, not part of the daily content pipeline
- **Completeness**: Must answer all 13 dimensions of the provided framework
- **Simplicity**: No external dependencies; the skill should be fully self-contained

## Considered Options

### Option 1: API-only (no clone)
- **Pros**: No disk usage, no cleanup required, faster for small repos
- **Cons**: Cannot trace execution paths; can only fetch specific files by name; misses the "how does it solve the problem" requirement

### Option 2: Local clone with fixed file cap (~20–30 files)
- **Pros**: Bounded context usage
- **Cons**: Artificial constraint breaks question-driven tracing for complex repos; adds prescriptive logic that may be wrong for different repo structures

### Option 3: Local clone with question-driven reading (chosen)
- **Pros**: Adapts to any repo structure; enables genuine execution tracing; quality scales naturally with repo size
- **Cons**: Quality varies for very large repos — accepted as a known limitation for v1

## Decision

Implement `study-github-repo` as an independent, self-contained skill that shallow-clones the target repo locally, gathers metadata via `gh api`, reads the codebase question-driven (starting from README → entry points → critical path), and produces an English report in `reports/GitHub/{owner}_{repo}.md` covering the 13-dimension framework. The clone is deleted after the report is written.

## Consequences

### Positive
- Full filesystem access enables genuine execution flow tracing
- Self-contained skill has no coupling to the TC content intelligence pipeline
- Flat report path (`reports/GitHub/`) makes reports easy to reference and update

### Negative
- Disk usage during analysis (shallow clone only; typically < 50 MB for most repos)
- Quality varies for very large repos (known, accepted limitation)
- No suggestion backlog integration (by design — not part of the daily workflow)

## Implementation Notes
- Always use single-quoted URLs in `gh api` calls to prevent zsh glob expansion
- Use `-c url.https://github.com/.insteadOf=git@github.com:` in `gh repo clone` for HTTPS fallback
- Use `find` instead of `tree` for directory listing (portability)
