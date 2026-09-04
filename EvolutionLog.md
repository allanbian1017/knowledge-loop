# Evolution Log

A chronicle of how this project evolved — told through the problems I discovered, the options I weighed, the decisions I made, and the new problems that emerged.

---

## The Starting Point

**Date**: March 31, 2026

I was drowning in unread newsletters. Every morning, my Gmail inbox had 10–15 AI/engineering newsletters I genuinely wanted to read, but never had time for. The information was valuable, but the volume was unmanageable.

I had one clear goal: **build an AI agent that reads my newsletters for me and produces structured summaries I can scan in minutes instead of hours.**

That single goal would spiral into a 4-month journey of iterative problem-solving, eventually producing a 21-skill agentic content intelligence system.

---

## How to Read This Document

Each section follows the same pattern:

> **🔍 Problem** → **🛤️ Options** → **⚖️ Decision** → **📊 Result** → 🔁 *...which revealed a new problem*

This isn't linear. Solving one problem always uncovered the next. The document traces the actual chain of discoveries as they happened.

---

## Phase 1: The Newsletter Summarizer

**Period**: March 31 – April 15, 2026

### 🔍 Problem

Too many newsletters, not enough time. I wanted to extract the signal without reading every word.

### 🛤️ Options

1. Use a third-party newsletter digest service (Stoop, Meco, etc.)
2. Build a custom AI agent that reads Gmail and produces Markdown summaries

### ⚖️ Decision

Build it myself. A third-party tool wouldn't understand my specific interests (AI agents, context engineering, developer tools) or produce the analysis depth I wanted. I created a `newsletter-summary` skill backed by the Google Workspace CLI (`gws`) for Gmail access.

### 📊 Result

It worked — newsletters got fetched, summarized, and saved as Markdown reports. But within the first week, three sub-problems surfaced:

- **Output token exhaustion**: Long newsletters caused the model to truncate output mid-report. *Fixed with write-as-you-go streaming* ([RCA 2026-04-02](docs/rca/newsletter_summary_rca_2026-04-02_V1.3.0.md)).
- **Hallucinated content**: The model sometimes "filled in" information not in the source. *Fixed by adding a zero-hallucination processing standard* ([RCA 2026-04-02 V1.4](docs/rca/newsletter_summary_rca_2026-04-02_V1.4.0.md)).
- **Duplicate reports**: Running the workflow twice on the same day overwrote previous reports. *Fixed with timestamp-based filenames.*

> 🔁 **New problem discovered**: Newsletters were only *one* of my content sources. I also consumed Threads posts, YouTube videos, and web articles daily. The single-source tool wasn't enough.

---

## Phase 2: Multi-Source Ingestion & Knowledge Distillation

**Period**: April 16 – April 30, 2026

### 🔍 Problem

Newsletters were handled, but I was also saving Threads posts and YouTube videos to Google Tasks for later reading — and never getting to them. I needed the same "summarize for me" capability across all my content sources.

### 🛤️ Options

1. Expand the existing `newsletter-summary` skill to handle all content types
2. Create separate specialized skills for each source type
3. Build a unified orchestrator that routes to specialized skills

### ⚖️ Decision

Option 2 first (specialized skills), with a plan to add an orchestrator later. Each content type had fundamentally different extraction needs:
- **Newsletters**: Gmail API → plain text
- **Threads**: Browser automation → scrape post content
- **YouTube**: Whisper transcription → structured text

I also introduced **Knowledge Distillation** — a daily synthesis step that reviews all reports from the day and distills cross-cutting AI/engineering insights.

### 📊 Result

The pipeline expanded to handle 4 content types with a daily distillation layer. The reports directory grew a clear structure: `Newsletter_YYYY_MM_DD/`, `Threads_YYYY_MM_DD/`, `YouTube_YYYY_MM_DD/`, and `reports/distillations/`.

But the codebase was getting messy — I now had 3+ skills with ~70% identical instructions for summarization, AI analysis, and suggestion logging.

> 🔁 **New problem discovered**: Massive instruction duplication across skills. Changing the output format meant editing 3 separate SKILL.md files and hoping they stayed consistent.

---

## Phase 3: DRY Refactoring — The Content-Summary Shared Layer

**Period**: May 5 – May 18, 2026
**Key RFC**: [skill-redesign-dry.md](docs/rfc/skill-redesign-dry.md)

### 🔍 Problem

Three ingestion skills (`newsletter-summary`, `process-delegate-tasks` for Threads, and a YouTube processing flow) all contained duplicated rules for:
- How to summarize content
- How to format the output Markdown
- How to generate AI suggestions
- How to name files

One change required editing all three. Drift was inevitable.

### 🛤️ Options

1. **Shared `_shared/` module folder** — Rejected: breaks skill loader conventions.
2. **Central database ledger** — Rejected: over-engineered for what's essentially shared documentation.
3. **Reference library pattern** — Extract common rules into a `content-summary` skill containing shared reference files that other skills read.

### ⚖️ Decision

Option 3. Created `content-summary` as a reference library with shared files for summarization rules, AI analysis templates, suggestion logging format, and filename conventions. Also standardized naming:
- `newsletter-summary` → `ingest-newsletter`
- `process-delegate-tasks` → split into `ingest-threads` + `ingest-youtube`
- Created `daily-workflow` as the top-level orchestrator

### 📊 Result

Adding a new content type became a matter of creating one new `ingest-*` skill that references the shared `content-summary` layer. The unified output template ([ingest-unified-output-format.md](docs/rfc/ingest-unified-output-format.md)) ensured all reports shared the same structure.

Around this time, I also hit a YouTube transcription bottleneck — Whisper on CPU was painfully slow. RCA ([2026-05-13](docs/rca/daily-workflow_rca_2026-05-13_V1.md)) led to switching default models from `large` to `base`/`small` for daily workflows.

> 🔁 **New problem discovered**: The architecture was clean, but **content analysis quality** was still shallow. Reports captured *what* a source said but not *why it mattered* or *how to apply it*.

---

## Phase 4: Analysis Depth & Operational Robustness

**Period**: May 15 – June 18, 2026
**Key RFCs**: [content-summary-7-layers-of-learning.md](docs/rfc/content-summary-7-layers-of-learning.md), [configurable-output-language.md](docs/rfc/configurable-output-language.md), [anti-cache-guardrails.md](docs/rfc/anti-cache-guardrails.md), [ingest-website-skill.md](docs/rfc/ingest-website-skill.md)

### 🔍 Problem (Quality)

Reports were functional summaries, but I wanted *learning artifacts* — documents that help me understand mechanisms, assess personal relevance, and generate new ideas. A simple "here's what they said" wasn't enough.

### 🛤️ Options

1. Add more prompt instructions incrementally
2. Design a systematic learning depth framework

### ⚖️ Decision

Option 2. I designed a "7 Layers of Learning" framework — from surface-level Core Idea down to Reflection & Prediction. Each layer extracted progressively deeper insights, with a Two-Zone Quality Rule: Zone 1 (extraction) required zero hallucination, Zone 2 (synthesis) allowed grounded inference citing sources.

### 📊 Result

Reports became substantially richer. But three operational problems emerged simultaneously:

**Problem A: Language was hardcoded.** Output defaulted to Traditional Chinese for some skills and English for others. No global setting existed.
- *Decision*: Store language preference in `data/user_preferences.md`, read dynamically by all skills ([configurable-output-language.md](docs/rfc/configurable-output-language.md)).

**Problem B: Agent hallucinated from stale cache.** The agent found 10-day-old files in `.tmp/`, used them instead of fetching fresh content, and produced a report based on completely wrong data. One incident even fabricated a non-existent Google Task ID ([RCA 2026-06-03](docs/rca/daily_workflow_rca_2026-06-03_V1.md)).
- *Decision*: Added explicit anti-cache guardrails — prohibiting local file substitution, enforcing task-isolated subdirectories, and adding pre-run staging cleanup ([anti-cache-guardrails.md](docs/rfc/anti-cache-guardrails.md)).

**Problem C: No website ingestion.** Generic URLs (blog posts, documentation) delegated via Google Tasks were simply skipped.
- *Decision*: Created `ingest-website` using Jina Reader API with fallback routing ([ingest-website-skill.md](docs/rfc/ingest-website-skill.md)).

> 🔁 **New problem discovered**: With richer analysis came more AI-generated suggestions (recommendations appended to reports). But ~29% of them were rejected during review — too vague ("研究看看"), not aligned with my goals, or just noise.

---

## Phase 5: Quality Intelligence — Rubric Grading & Thesis-Driven Analysis

**Period**: June 5 – July 22, 2026
**Key RFCs**: [rubric-grader.md](docs/rfc/rubric-grader.md), [content-summary-thesis-driven-analysis.md](docs/rfc/content-summary-thesis-driven-analysis.md), [report-quality-grader.md](docs/rfc/report-quality-grader.md), [content-summary-key-insight.md](docs/rfc/content-summary-key-insight.md)

This phase attacked quality from two angles: filtering bad suggestions and improving report structure.

### 🔍 Problem 1: Low-Signal Suggestions

~29% of AI suggestions were rejected during user review. The top rejection reason: ambiguous phrasing. Three legacy metadata fields (💎 Value, ⚡ Urgency, 🎯 Alignment) provided poor signal.

### 🛤️ Options

1. Keyword-based filtering (block vague phrases)
2. Multi-dimensional rubric scoring with hard vetoes
3. Dedicated second LLM grader pass (rejected: doubles token cost)

### ⚖️ Decision

Option 2 with elements of Option 1. Built `rubric-grader` with 3 scoring dimensions (Actionability 0–2, Preference Alignment 0–2, Goal Relevance 0–2), plus a deterministic blocklist for known-bad patterns. Score < 4 → filtered to `data/suggestions_filtered.md` instead of `data/suggestions_pending.md`.

### 📊 Result

User acceptance rate improved from ~71% to ≥80%. The blocklist caught the most obvious noise, while the rubric handled nuanced quality assessment.

---

### 🔍 Problem 2: Report Scan Fatigue

The 7-layer analysis produced thorough reports, but at 9 sections per report, scanning 15+ reports daily was exhausting. Readers couldn't quickly answer: *"Should I even read this?"* and *"What's the core argument?"*

### 🛤️ Options

1. Keep 9 sections, add a triage section on top
2. Redesign around thesis-driven analysis (fewer, sharper sections)
3. Full minimalist 3-section format (rejected: loses Reasoning Map and AI Analysis)

### ⚖️ Decision

Option 2. Redesigned the entire output template from v2.0 to v4.0 (and further optimized in v4.3.0 for instant triage):
- **Reading Decision** (personalized ★ rating + Novel Insight upfront) → **TL;DR** → **Core Thesis** → **Reasoning Map** (auto-selected from 3 templates) → **AI Analysis** (preserved layers 4–7)

This also absorbed the earlier `Key Insight` section ([content-summary-key-insight.md](docs/rfc/content-summary-key-insight.md)) into Reading Decision's Novel Insight, splitting source extraction (`📌 原文洞察`) from synthesis (`💡 延伸洞察`).

### 📊 Result

Reports became instantly triagable (< 5 seconds without scrolling). The top-placed Reading Decision with star ratings let me triage 15+ reports in under 1 minute, diving deep only into ★★★★☆+ content.

> 🔁 **New problem discovered**: Quality was up, but **processing speed** was abysmal. 10–15 daily items took 30–80 minutes to process sequentially. The main agent's context window also got polluted with raw article text from earlier items, degrading later summaries.

---

## Phase 6: Parallel Architecture

**Period**: July 7 – July 24, 2026
**Key RFC**: [parallel-content-processing.md](docs/rfc/parallel-content-processing.md)

### 🔍 Problem

Sequential processing caused two interrelated issues:
1. **Speed**: 30–80 minutes for a daily run was unacceptable.
2. **Context pollution**: The main agent accumulated ~40,000+ words of raw content in its context window, causing later summaries to degrade in quality.

### 🛤️ Options

1. **Sequential with optimizations** — Process faster but still serial. Doesn't fix context pollution.
2. **Parallelize within content type** — Process all newsletters in parallel, then all YouTube, etc. Slow items still block.
3. **Full-lifecycle parallel subagents** — Main agent becomes a pure metadata dispatcher; each content item gets its own subagent with a clean context window.
4. **Redis/Celery task queue** — Rejected: massively over-engineered for this use case.

### ⚖️ Decision

Option 3. The `daily-workflow` orchestrator was transformed into a dispatcher that:
1. Discovers task metadata (IDs, URLs, types) from Google Tasks
2. Spawns one subagent per content item with only the URL/ID — no raw content
3. Each subagent runs the full lifecycle independently (fetch → summarize → write report → grade suggestions → mark task done)
4. A 30-minute sync barrier merges per-subagent suggestion files

### 📊 Result

- **Wall-clock time**: 30–80 min → 8–15 min
- **Context integrity**: Each subagent processes exactly one item in a pristine context window
- **Reliability**: Individual failures don't cascade; failed items can be retried independently

> 🔁 **New problem discovered**: With parallel execution came new debugging challenges — sandbox path resolution errors ([RCA 2026-07-29](docs/rca/daily_workflow_rca_2026-07-29_V1.md)) and the need for better error isolation per subagent.

---

## Sidebar: The Session Logging Experiment

**Period**: June 1 – July 29, 2026
**RFCs**: [closed-loop-session-logging.md](docs/rfc/closed-loop-session-logging.md) → [simplify-session-logging-to-known-issues.md](docs/rfc/simplify-session-logging-to-known-issues.md)

This is worth calling out separately because it's a clean example of the **build → discover it's over-engineered → simplify** cycle.

### 🔍 Problem

Developer-agent session decisions (tool failures, workarounds, design choices) were lost between sessions. The agent had no memory of what went wrong last time.

### ⚖️ Decision (Attempt 1)

Built a full closed-loop 4-pillar logging system: structured session log schema, wrap-up protocol, `compile_session_learnings.py` compiler script, tiered memory hierarchy, and pending recovery bootstrap.

### 📊 Result

It accumulated 78 session log files. Nobody ever re-read them (conversation transcripts already exist in the agent's app data). The compiler script grew to 247 lines. The overhead was real but the value was marginal.

### ⚖️ Decision (Attempt 2)

Replaced the entire system with a single `known_issues.md` file at the project root. Agents read it at startup, append new failures in a one-liner format, and that's it.

### 📊 Result

5–10% reduction in per-session bookkeeping overhead. The most valuable information (failure workarounds) was preserved; everything else was cut.

> **Lesson**: Not every problem needs a system. Sometimes a flat file with a clear format is the right answer.

---

## Phase 7: Instant Triage UX & Declarative Sub-Agent Standardization

**Period**: July 30 – August 7, 2026
**Key RFCs**: [content-summary-reading-decision-first.md](docs/rfc/content-summary-reading-decision-first.md), [path-free-subagent-personas-and-sync.md](docs/rfc/path-free-subagent-personas-and-sync.md)

### 🔍 Problem 1: Triage UX Friction

Even after adopting thesis-driven reports in Phase 5, daily triage was slower than it needed to be. The `⭐ Reading Decision` section (containing the star rating, judgment rationale, and novel insight) was placed at line 50+ after `TL;DR`, `Core Thesis`, and `Reasoning Map`. To decide whether a report was worth reading, I had to scroll past ~35 lines or read through summary details first. Across 15+ daily reports, this friction accumulated into scan fatigue.

### 🛤️ Options

1. **Keep status quo**: Read summary sections sequentially before reaching the rating.
2. **Title-only rating badge**: Add star rating to `# [★★★★☆] Title`, keeping body layout unchanged.
3. **Move Reading Decision to top**: Place `⭐ Reading Decision` directly below `🔖 來源 Metadata` (before `📝 TL;DR`).

### ⚖️ Decision

Option 3. Moved `Reading Decision` to the top of the report layout. To prevent the LLM from making biased relevance judgments before fact extraction, I decoupled visual document layout from prompt reasoning order in `.agents/skills/content-summary/references/summarise.md`: the LLM performs internal zero-hallucination Chain-of-Thought (CoT) factual extraction first, but renders the Markdown starting with the `Reading Decision` section second.

### 📊 Result

Triage speed dropped to <5 seconds per report without scrolling. Low-rated items (★★☆☆☆) are abandoned in 2 seconds, while 4–5★ reports provide an immediate executive teaser framing the reader's focus before diving into details.

---

### 🔍 Problem 2: Sub-Agent Persona Fragmentation & Platform Coupling

Parallel processing (Phase 6) spawned worker sub-agents using a single generic system prompt, creating a performance ceiling for specialized tasks (e.g. `rubric_grader` requiring rigid audit precision vs `newsletter_worker` filtering promotional fluff). Additionally, different AI agent runtimes (Antigravity, Claude Code, OpenAI Codex) expect sub-agent configurations in platform-specific folders (`.agents/agents/`, `.claude/subagents/`, `.codex/subagents/`), forcing manual duplication or hardcoded path couplings in workflow prompts.

### 🛤️ Options

1. **Hardcode platform paths**: Hardcode relative paths like `.agents/agents/newsletter_worker.md` directly into workflow prompts.
2. **Declarative single-source persona architecture**: Single Source of Truth in `.agents/agents/*.md` with path-free logical references and automated cross-platform sync.

### ⚖️ Decision

Option 2. Established a 6-subagent roster (`newsletter_worker`, `threads_worker`, `website_worker`, `youtube_worker`, `rubric_grader`, `distiller_reviewer`), defined in `.agents/agents/*.md` with standardized YAML frontmatter. Prompts reference sub-agents strictly by logical name (`newsletter_worker`), and an automated sync script (`scripts/sync_subagents.py`) formats personas for target runtimes. Also added `scripts/validate_skill.py` to enforce skill quality and YAML validity automatically.

### 📊 Result

Platform-agnostic prompts, single-sourced persona maintenance, clean system prompt caching (via static persona definitions + first-message parameter injection), automated skill validation (`scripts/validate_skill.py`), and full multi-target synchronization via `scripts/sync_subagents.py` generating native Markdown for Claude Code (`.claude/agents/`) and TOML configurations for OpenAI Codex (`.codex/agents/`).

Additionally, capability declarations were formally migrated, moving domain tools (`gws-gmail`, `agent-browser`, `yt2doc`) into `skills:` across worker configurations (`newsletter_worker`, `threads_worker`, `youtube_worker`) to strictly separate native agent operations from modular Agent Skills.

> 🔁 **New problem discovered**: Sub-agent personas and triage UX are standardized, but verifying sub-agent execution performance and preventing regressions across 21 skills requires an automated evaluation harness and live benchmark runner.

---

## Sidebar: The Blind Sub-Agent Incident

**Period**: July 31, 2026
**Key RCAs**: [2026-07-31 V1](docs/rca/daily_workflow_rca_2026-07-31_V1.md), [2026-07-31 V2](docs/rca/daily_workflow_rca_2026-07-31_V2.md)

Deploying the single-source declarative sub-agents in Phase 7 immediately triggered a cascading failure, providing a perfect lesson in platform tool resolution.

### 🔍 Problem

When launching the new `rubric_grader` persona, the system crashed immediately with `no tool converter registered for read_file`. I had explicitly listed `read_file` and `write_file` in the sub-agent's YAML `tools:` array, but Antigravity's native primitives are `view_file` and `write_to_file`.

### 🛤️ Options & ⚖️ Decision (Attempt 1)

I assumed native file tools were inherited by default, so I changed the YAML to `tools: []` to bypass the error, and re-synced.

### 📊 Result (Attempt 1)

The sub-agents successfully launched, but they started generating reports in English (ignoring my Traditional Chinese preference in `data/user_preferences.md`) and completely hallucinated the report formatting, ignoring the Markdown template. 

*Why?* Because explicitly setting `tools: []` in Antigravity doesn't mean "default tools"; it means "zero tools." The sub-agents were completely blind. Unable to read the preference files or templates, they fell back to their base LLM behavior and hallucinated the rest.

### ⚖️ Decision (Attempt 2)

I restored the exact native tools (`view_file`, `list_dir`, `grep_search`, and `run_command`) into the sub-agent personas, replacing the invalid tool names, and removed the workaround. I also formalized the RCA process in `AGENTS.md` and added an `AfterTool` hook to automatically sync the personas whenever their source files change.

### 📊 Result (Attempt 2)

The blind sub-agents got their vision back. A fresh `website_worker` test perfectly adhered to the Traditional Chinese setting and correctly formatted the `Reading Decision` and `AI Analysis` sections.

> 💡 **Lesson**: Never assume implied capabilities in declarative configurations. Explicit is always better than implicit, especially when bridging across multiple AI runtime engines.

---

## Phase 8: Reader-Centric Knowledge & Attention Budget Governance

**Period**: August 12 – September 3, 2026
**Key RFCs**: [content-summary-what-can-i-learn.md](docs/rfc/content-summary-what-can-i-learn.md), [agent-rules-reviewer.md](docs/rfc/agent-rules-reviewer.md), [3-tier-agent-rules-architecture.md](docs/rfc/3-tier-agent-rules-architecture.md)
**Key RCA**: [daily_workflow_rca_2026-09-03_V1.md](docs/rca/daily_workflow_rca_2026-09-03_V1.md)

### 🔍 Problem 1: Reader-Centric Knowledge vs. Author-Centric Arguments

Even with <5-second triage and thesis-driven summaries from Phase 5 and Phase 7, consuming 10–15 daily reports revealed an awkward cognitive friction. The `Core Thesis` section answered: *"What is the author's primary thesis and how do they defend it?"* — structured like an academic defense brief. But when I read a report in the morning, my primary question wasn't *"How does the author construct their rhetorical argument?"* It was: *"What transferable knowledge, methodologies, or mental models do I walk away with?"*

To get practical value, I had to mentally reverse-engineer the author's claims into personal takeaways.

### 🛤️ Options

1. **Expand TL;DR**: Cram takeaways into the opening summary (overcrowds the 3-sentence executive overview).
2. **Bury in AI Analysis**: Rely on the downstream reflection sections (forces scrolling past 50+ lines to find actionable knowledge).
3. **Dedicated Reader-Centric Section**: Introduce `## 🧠 What Can I Learn From It` immediately between `📝 TL;DR` and `🎯 Core Thesis`.

### ⚖️ Decision

Option 3 ([content-summary-what-can-i-learn.md](docs/rfc/content-summary-what-can-i-learn.md)). Standardized the reading flow:

$$\text{Triage (Reading Decision)} \longrightarrow \text{Context (TL;DR)} \longrightarrow \textbf{What do I learn?} \longrightarrow \text{Verify logic (Core Thesis)}$$

Updated `.agents/skills/content-summary/references/output_template.md` and `.agents/skills/content-summary/references/summarise.md` with strict Zone A rules: 2–5 portable, high-density bullet points articulating actionable knowledge, workflows, or architectural insights without generic fluff.

### 📊 Result

Reports now deliver transferable takeaways within 15 seconds. Factual extraction stays anchored in source material without muddying the author's logical proofs.

---

### 🔍 Problem 2: Steering Rule Drift & Attention Budget Exhaustion

Across five months of adding capabilities, skills, and edge-case fixes, the repository's root steering contract (`AGENTS.md`) decayed into an unstructured collection of negative micro-rules. A systematic audit revealed:

- **17 negative prohibitive constraints** (`NEVER`, `DO NOT`) and **29 restrictive keywords** across 76 lines.
- **~50% semantic redundancy**: automated testing mandates were stated in 4 separate locations; dead-code rules were repeated in adjacent lines; anti-overengineering warnings appeared in multiple paragraphs.
- **Attention Budget Degradation ("Rule Drift")**: In long multi-step reasoning, dense negative suppression exhausted the LLM's self-attention budget, paradoxically increasing rule violations on critical boundaries.
- **Platform & environment friction**: Links using `file:///` caused ambiguity between git commits and Antigravity chat links, and domain rules leaked into global instructions.

### 🛤️ Options

1. **Manual line-by-line pruning**: Delete obvious duplicates by hand (fragile; bloat inevitably re-accumulates).
2. **Automated 3-tier rules architecture with governance tooling**: Adopt Addy Osmani's 3-Tier Agent Rules Architecture (Always Do / Ask First / Never Do) and build a dedicated skill (`agent-rules-reviewer`) with an automated 5-vector audit model.

### ⚖️ Decision

Option 2 ([3-tier-agent-rules-architecture.md](docs/rfc/3-tier-agent-rules-architecture.md), [agent-rules-reviewer.md](docs/rfc/agent-rules-reviewer.md)). Built the `agent-rules-reviewer` skill. Evaluated all directives against 5 vectors (Self-Duplication, Base LLM Baseline, System Conflicts, Skill Domain Leakage, Negative Constraint Bloat), then mapped surviving directives into 3 clean tiers:
- **Tier 1 (Always Do)**: Autonomous safe defaults (automated test verification, skill validation via `scripts/validate_skill.py`, session registry hygiene in `known_issues.md` / `backlog.md`, minimal code scope, relative doc links).
- **Tier 2 (Ask First)**: Human approval gates (RCA fix review gate, trade-off & ambiguity resolution, destructive or structural modifications).
- **Tier 3 (Never Do)**: Inviolable boundaries (tool circumvention / fail-fast, manual testing proposals, credential exposure, scope creep).

Also renamed `CLADE.md` to `CLAUDE.md` to standardize cross-platform steering.

### 📊 Result

- **54% line reduction**: 76 lines → 35 lines.
- **53% token reduction**: ~1,743 tokens → ~820 tokens.
- **65% reduction in negative constraints**: 17 → 6 occurrences.
- **76% reduction in restrictive keywords**: 29 → 7 occurrences.
- Clear operational boundaries, eliminating rule drift in complex tasks while preserving hard invariants.

> 🔁 **New problem discovered**: While rules and report layouts were streamlined, a silent failure in dynamic data management was corrupting system preferences behind our backs, while prompt "template gravity" was overriding fallback defaults.

---

## Sidebar: The Vanishing Preferences & Template Gravity Incident

**Period**: September 3, 2026
**Key RCA**: [2026-09-03 V1](docs/rca/daily_workflow_rca_2026-09-03_V1.md)

### 🔍 Problem

On September 3, 2026, 10 external intelligence documents were generated during the daily run. All 10 were written in Traditional Chinese (averaging 86.9% Chinese characters), even though 8 of the 9 sources were English engineering blogs and papers (ByteByteGo, Anthropic documentation, Waymo autonomous driving engineering, Hugging Face papers).
When checking `.agents/skills/content-summary/references/summarise.md`, the rule explicitly specified: *"If configuration is missing, default to English"*.

Why did every subagent produce Chinese?

### 🔬 Investigation

Digging through commit history and prompt contexts revealed two intertwined failures:
1. **Silent Overwrite**: `data/user_preferences.md` had originally held the dual-language configuration (`Preferred Report Language` / `Preferred Conversation Language`). However, `review-suggestions` Step 6 rebuilt `data/user_preferences.md` from scratch after suggestion reviews, using a template that omitted `## Configuration`. A suggestion review had silently obliterated the language settings!
2. **Template Gravity**: In the absence of an explicit config key, subagents didn't fall back to English. Why? Because the prompt context had overwhelming **template gravity**: `.agents/skills/content-summary/references/output_template.md` had Chinese headers (`## 🔖 來源 Metadata`, `## ⭐ Reading Decision`, `## 📝 TL;DR`), `data/goals.md` had Chinese goals, and `.agents/skills/ingest-newsletter/SKILL.md` was written in Chinese. The in-context priors completely overpowered the abstract fallback rule.

### ⚖️ Decision

1. **Architectural Separation**: Separated dynamic, machine-regenerated user interest stats (`data/user_preferences.md`) from persistent system configuration (`data/lang_preferences.md`).
2. **Deterministic Lifecycle Guard Hook**: Created `scripts/hooks/ensure_lang_preferences.sh` registered in `.agents/settings.json` under `BeforeTool` and `AfterTool`. If `data/lang_preferences.md` is deleted or corrupted, the hook immediately heals and restores it before any tool or subagent workflow proceeds.
3. **Automated Test Validation**: Wrote `scripts/validate_language_config.py` to assert config validity, test self-healing against simulated deletions, and check skill file references.
4. **Dual-Language Contract**: Formalized in `AGENTS.md` that internal docs and chat use Preferred Conversation Language (English), while external summaries use Preferred Report Language (Traditional Chinese).

### 📊 Result

System settings are permanently decoupled from AI-generated statistics. The lifecycle hook guarantees zero-drift configuration across all sessions and runtimes.

> 💡 **Lesson**: Never store persistent system configuration in files frequently rewritten by AI agents. Separate immutable system configuration from mutable learned statistics, and protect configuration with deterministic lifecycle hooks rather than prompt instructions.

---

## Where It Stands Today

**Date**: September 4, 2026
**Stats**: 13 skills, 26 RFCs, 16 RCAs, ~5 months of iteration

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   SYSTEM GOVERNANCE & CONFIGURATION LAYER                        │
│                                                                                  │
│  ┌─────────────────────────────────┐     ┌────────────────────────────────────┐  │
│  │  AGENTS.md & CLAUDE.md          │     │  data/lang_preferences.md          │  │
│  │  • 3-Tier Agent Rules           │     │  • Preferred Report Language       │  │
│  │  • agent-rules-reviewer Skill   │     │  • Preferred Conversation Language │  │
│  │  • Attention Budget Governance  │     │  • Lifecycle Guard Hook (Healing)  │  │
│  └─────────────────────────────────┘     └────────────────────────────────────┘  │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────┴─────────────────────────────────────────┐
│                             DAILY WORKFLOW ARCHITECTURE                          │
│                                                                                  │
│  ┌──────────────┐     ┌──────────────────────────────────────┐                   │
│  │  Google Tasks │     │  Gmail (Newsletter Labels)           │                   │
│  │  (Delegate)   │     │                                      │                   │
│  └──────┬───────┘     └──────────────┬───────────────────────┘                   │
│         │                            │                                           │
│         ▼                            ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐                    │
│  │               daily-workflow (Orchestrator)              │                    │
│  │  • Classify tasks by URL type                            │                    │
│  │  • Dispatch path-free subagent personas by logical name  │                    │
│  │  • Merge suggestions at sync barrier                     │                    │
│  └──────┬────────────┬──────────────────┬─────────────┬─────┘                    │
│         │            │                  │             │                          │
│         ▼            ▼                  ▼             ▼                          │
│  ┌────────────┐ ┌──────────┐     ┌───────────┐ ┌───────────┐                     │
│  │newsletter_ │ │threads_  │     │youtube_   │ │website_   │ (Declarative       │
│  │worker      │ │worker    │     │worker     │ │worker     │  Sub-Agents)       │
│  └─────┬──────┘ └────┬─────┘     └─────┬─────┘ └────┬──────┘                     │
│        │             │                 │            │                            │
│        └─────────────┴────────┬────────┴────────────┘                            │
│                               ▼                                                  │
│                    ┌──────────────────┐                                          │
│                    │  content-summary │  (shared analysis pipeline)              │
│                    │  • Reading Dec.  │  (Instant Triage UX)                     │
│                    │  • What Can Learn│  (Portable Reader Takeaways)             │
│                    └────────┬─────────┘                                          │
│                             ▼                                                    │
│                    ┌──────────────────┐                                          │
│                    │  rubric_grader   │  (autonomous quality gate subagent)      │
│                    └────────┬─────────┘                                          │
│                             ▼                                                    │
│                    ┌──────────────────┐                                          │
│                    │distiller_reviewer│  (cross-report synthesis subagent)       │
│                    └──────────────────┘                                          │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### The Evolution at a Glance

| Phase | Period | Core Problem | Key Decision | Outcome |
|:---:|:---|:---|:---|:---|
| 1 | Mar–Apr 2026 | Too many newsletters | Build custom Gmail → Markdown pipeline | Working summarizer, but single-source |
| 2 | Apr 2026 | Only one content source | Add Threads, YouTube, distillation | Multi-source, but duplicated code |
| 3 | May 2026 | 70% instruction duplication | Extract `content-summary` shared layer | DRY architecture, easy to extend |
| 4 | May–Jun 2026 | Shallow analysis, operational bugs | 7 Layers of Learning, anti-cache, website skill | Deeper analysis, but noisy suggestions |
| 5 | Jun–Jul 2026 | 29% suggestion rejection, scan fatigue | Rubric grading, thesis-driven redesign | ≥80% acceptance, scannable reports |
| 6 | Jul 2026 | 30–80 min sequential processing | Parallel subagent dispatch | 8–15 min, clean context per item |
| 7 | Jul 30 – Aug 7, 2026 | Triage scroll friction & persona coupling | Top-placed Reading Decision & path-free subagent roster | <5s triage UX, cross-platform subagent sync (MD & TOML) |
| 8 | Aug 12 – Sep 3, 2026 | Reader takeaway friction & steering rule drift | "What Can I Learn" section, Addy Osmani 3-tier rules, dedicated config isolation | <15s actionable takeaways, -54% rule lines (-53% tokens), zero-drift config |

### Key Recurring Patterns

1. **Every quality improvement created a speed problem.** Richer analysis → more tokens → slower processing → need for parallelization.
2. **Duplication is the first sign of a missing abstraction.** The DRY refactoring was inevitable once the third content type was added.
3. **Over-engineering is a real failure mode.** Session logging taught me that the simplest solution that captures the core value is usually the right one.
4. **Bugs reveal design gaps.** The hallucination RCAs weren't just bugs — they exposed missing guardrails that should have been there from the start.
5. **Decouple visual presentation from internal execution.** Rendering `Reading Decision` upfront for human UX while preserving internal CoT fact extraction in prompts keeps triage fast without compromising factual accuracy.
6. **Separate immutable configuration from mutable agent state.** Storing system configuration in files rewritten by agents invites silent data loss. Isolate system configuration in dedicated files and guard them with deterministic lifecycle hooks.
7. **Attention budget is a scarce cognitive resource.** Adding rules without pruning existing ones creates cognitive overload for LLMs. High-density negative constraints (`NEVER`, `DO NOT`) cause rule drift; structured positive defaults (Always Do / Ask First / Never Do) preserve attention and boost compliance.

---

## What's Next

The current backlog includes several threads that could trigger the next phase of evolution:

- **Bilingual Template Internationalization**: Internationalize section headers in `.agents/skills/content-summary/references/output_template.md` to match `Preferred Report Language` dynamically, eliminating remaining template gravity.
- **LLM-as-a-Judge Evaluation & Test Harness** ([RFC](docs/rfc/daily-workflow-evals.md)): Quantitative regression testing suite (`.agents/skills/daily-distiller/evals/evals.json` / Auditor Agent) to verify report quality, zero-hallucination compliance, and token consumption without mutating live Google Tasks.
- **Universal Architecture Tradeoff Checklist**: Implement Andrew Ng-inspired pre-implementation tradeoff checklist across Concurrency, Data Consistency, Resilience, Security, and Verification.
- **Smart Fallback Routing** ([RFC](docs/rfc/smart-fallback-routing.md)): Persistent domain routing table to skip known-blocking websites instead of retrying every run.

---

Five months ago, I wanted an AI agent to summarize my newsletters.
Today, I have something much more valuable: a system that helps me learn, think, and improve.

The biggest evolution was not the workflow itself — it was learning how to design a system that evolves with me.

*Last updated: September 4, 2026*
