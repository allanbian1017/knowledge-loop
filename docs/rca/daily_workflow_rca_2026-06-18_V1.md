# RCA: Daily Workflow — Stale Cache Reuse in Website Ingestion

## 1. Observed Problem

During the website task processing phase of `daily-workflow`, the system attempted to process
`https://www.facebook.com/share/1EPqXGQdsq/` (Task ID: `Yy1DQ1MwSnd5X0d2SXJqTQ`). Without
performing any network fetch, the agent incorrectly read a stale local cache file
`.tmp/facebook_body.txt` and generated a Traditional Chinese report titled "6 Types of Agent
Workflow Patterns" based on its outdated content, then marked the task as completed.

The Facebook URL actually redirects unauthenticated browsers to a login page, and the content
does not match the report that was produced. This revealed a bug where stale or unrelated cache
files are silently reused, resulting in hallucinated task completion.

## 2. Alternative Hypotheses & Rejection Evidence

The following hypotheses were evaluated and rejected before identifying the root cause:

- **Hypothesis A**: The fetcher did execute a network request in this session, and Facebook
  happened to return the same snapshot as 10 days ago.
  - *Rejection evidence*: Running `ls -l .tmp/facebook_body.txt` showed a last-modified timestamp
    of **Jun 8 16:34** — 10 days prior to this session. No new snapshot was written during the
    run. This confirms no fetch was executed. **Rejected.**

- **Hypothesis B**: `facebook_body.txt` was legitimately named and scoped to task
  `Yy1DQ1MwSnd5X0d2SXJqTQ`.
  - *Rejection evidence*: All other tasks in `.tmp/` use Task ID-derived or URL-hashed prefixes
    (e.g., `MU1pNnM3aDdsa2VjZmFtNg_body.txt`). The file `facebook_body.txt` uses a generic,
    non-unique name with no binding to any task ID or URL. **Rejected.**

## 3. Root Cause — Primary + Contributing

### 3.1 Primary Root Cause

**Stale Cache Reuse via Filename-Based Association Hallucination**

When processing the Facebook task URL, the agent scanned `.tmp/` for a cached body file. Upon
finding `facebook_body.txt`, it incorrectly associated it with the current task solely based on
the filename containing the string `"facebook"`, ignoring the file's last-modified timestamp
(10 days old). This caused the agent to treat a stale, unrelated cache entry as valid content for
the current task.

### 3.2 Contributing Root Causes

- **Non-deterministic cache key naming**: `ingest-website` and `daily-workflow` allowed generic
  filenames such as `facebook_body.txt` instead of enforcing unique keys derived from a URL hash
  or Task ID (e.g., `Yy1DQ1MwSnd5X0d2SXJqTQ_body.txt`).

- **No TTL or URL metadata verification**: The cache-loading path did not validate file age (e.g.,
  TTL < 2 hours) or check that the file's content header matched the current task's URL.

- **No pre-run staging area sanitation**: The daily workflow did not clear leftover body snapshots
  from previous runs before starting, leaving `.tmp/` in a polluted state from days or weeks prior.

## 4. Fix Applied & Status Checklist

### 4.1 Fixes Applied

1. **Corrected suggestion review state**: Updated suggestion #8 (previously rejected due to the
   hallucinated content) to Accepted in
   [suggestions_reviewed.md](../data/suggestions_reviewed.md).

2. **Recompiled user preferences**: Re-ran the preference compiler to regenerate
   [user_preferences.md](../data/user_preferences.md) with
   corrected acceptance rate statistics.

3. **Backlog items created**: Added defensive mechanism backlog items to
   [backlog.md](../backlog.md):
   - **Item 29**: Canonical URL Resolution & Cache Mirroring (unique hash-based filenames).
   - **Item 30**: Cryptographic Cache Validation (TTL enforcement, URL metadata headers, pre-run
     sanitation).

### 4.2 Status Checklist

- [x] Confirmed `facebook_body.txt` last-modified timestamp (10 days prior — stale)
- [x] Rejected all alternative hypotheses with measured evidence
- [x] Documented root cause analysis in `docs/rca/`
- [x] Created Backlog Items 29 & 30 for preventative cache enforcement
- [x] Updated `suggestions_reviewed.md` and `user_preferences.md`
- [ ] Implement deterministic cache key naming in `ingest-website` (Backlog Item 29)
- [ ] Implement TTL checks and pre-run sanitation in `daily-workflow` (Backlog Item 30)

## 5. References

- Affected skill: [daily-workflow/SKILL.md](../.agents/skills/daily-workflow/SKILL.md)
- Affected skill: [ingest-website/SKILL.md](../.agents/skills/ingest-website/SKILL.md)
