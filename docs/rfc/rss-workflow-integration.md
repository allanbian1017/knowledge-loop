# RFC: RSS Ingestion into Daily Workflow

## Summary

This Request for Comments (RFC) proposes integrating RSS and Atom feed monitoring into the existing daily content intelligence pipeline (`daily-workflow`). By introducing a feed registry and deduplication tracker, the workflow will automatically fetch, process, and summarize new articles from subscribed feeds each day.

## Status

**Proposed** (Approved in Design review) — 2026-06-26

## Motivation

Currently, the daily workflow processes newsletters (from Gmail), Threads posts, website links, and YouTube videos. However, many valuable engineering blogs (like ByteByteGo, Netflix Tech Blog, etc.) publish updates via RSS feeds. 

Users need to monitor these feeds without manually copying links into Google Tasks. Integrating RSS monitoring directly into the daily workflow enables automated, daily tracking of these sources, feeding their insights directly into the daily distillation and suggestion backlog.

---

## Detailed Design

### 1. Feed Registry (`data/feeds.yaml`)

We will store subscribed RSS feeds in a new configuration file:

```yaml
feeds:
  - name: ByteByteGo
    url: https://blog.bytebytego.com/feed
    limit: 5
```

### 2. State Storage & Deduplication (`data/rss/seen/`)

To prevent processing the same article multiple times across daily runs, seen URLs will be tracked in plain text files under `data/rss/seen/<feed_slug>.txt`. 
- These files are committed to Git to ensure that the seen-URL state is synced across different environments and machines.
- The `rss-reader` script uses `--skip <url1,url2,...>` to deduplicate.

### 3. Workflow Integration (`daily-workflow` Step 2R)

We will introduce a new step, **Step 2R — Process RSS feeds**, into the daily workflow between YouTube background jobs (Step 2) and newsletters (Step 3).

For each feed:
1. Load seen URLs from `data/rss/seen/<feed_slug>.txt`.
2. Fetch the feed via `fetch-rss.mjs`.
3. For **full-content articles**: Summarize the content directly (no network fetch needed) and save reports to `reports/RSS_YYYY_MM_DD/`.
4. For **summary-only/preview articles**:
   - Attempt to fetch the full page via Jina Reader (`r.jina.ai`).
   - If Jina Reader / `content-cleaner` fails or gets blocked by WAF/paywalls, proceed to generate the report using the available snippet/preview text from the feed (ensuring metadata and partial insights are still distilled).
5. Append suggestions to the pending backlog under the `{SourceType}` = `RSS` category, which automatically triggers `rubric-grader` validation.
6. Append the new article URLs to `data/rss/seen/<feed_slug>.txt`.

---

## Drawbacks

- **Git Noise**: Committing seen-URL files to Git creates small, daily diffs in the repository. This is accepted in order to ensure seen state is synced across devices.
- **Paywall Quality**: Summarizing paywalled articles using only their preview text may result in shallow reports. This is accepted as a fallback to ensure we do not crash or get blocked by login walls.

---

## Alternatives Considered

- **Gitignoring seen-URL state**:
  *Rejected*: While it avoids git commit noise, checking out the workspace on another machine would trigger re-summarization of all old articles, leading to redundant reports and suggestion duplicates.
- **Skipping paywalled/preview articles entirely**:
  *Rejected*: Creating a report with snippet text preserves the metadata, link, and initial preview of the article, which the daily distillation can still capture.
- **Merging snippet-only RSS articles into the `website_queue`**:
  *Rejected*: Splitting RSS handling across steps increases daily-workflow state complexity. Processing them in a single self-contained step (Step 2R) keeps the logic clean and simple.

---

## Implementation Plan

1. Create `data/feeds.yaml` with the initial subscription list.
2. Update the `rss-reader` skill (`SKILL.md`) to define the batch mode and seen state management.
3. Update the `daily-workflow` skill (`SKILL.md`) to add Step 2R and update final output summaries.
4. Update the test/validation suite if any assertions exist for daily workflow steps.

---

# ADR: RSS Seen-URL State Storage

## Context

We need a way to track which RSS article URLs have already been processed to prevent duplicate summarization in subsequent daily runs.

## Decision

We will store seen URLs in plain text files (one URL per line) in a dedicated directory: `data/rss/seen/<feed_slug>.txt`. These files will be committed to Git.

## Rationale

Storing state files in the workspace repository and tracking them in Git guarantees that the seen state is synchronized across all devices where the repository is cloned. This completely eliminates the duplicate processing of old articles when running the workflow in a new setup or after a workspace clean. The downside of minor daily commit diffs is outweighed by this consistency.

## Consequences

- **Consistent State**: No duplicate articles will be summarized on new machine setups.
- **Git Diff Noise**: Every daily run that finds new articles will create minor git diff changes in `data/rss/seen/`.
- **Easy Maintenance**: State files are simple text lists, making it easy to manually edit them if a feed needs to be re-run.
