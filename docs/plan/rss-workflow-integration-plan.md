# Skill Plan: RSS Workflow Integration

Integrate RSS feed monitoring into the daily content intelligence pipeline. Introduce feed configuration, seen-URL state tracking, a new Step 2R in `daily-workflow`, and update associated skills.

---

## Proposed Changes

### 1. Feed Configuration & Preferences

#### [NEW] [feeds.yaml](../../data/feeds.yaml)
- Create `data/feeds.yaml` to store subscribed RSS/Atom feeds:
  ```yaml
  feeds:
    - name: ByteByteGo
      url: https://blog.bytebytego.com/feed
      limit: 5
  ```

---

### 2. rss-reader Skill

#### [MODIFY] [SKILL.md](../../.agents/skills/rss-reader/SKILL.md)
- Add **Step 0 — Batch Mode** documentation:
  - If no URL is passed, read feeds from `data/feeds.yaml`.
  - Explain how `data/rss/seen/<feed_slug>.txt` is used to load and update seen URLs.
- Update file paths and descriptions to match the new workflow integration.

---

### 3. daily-workflow Skill

#### [MODIFY] [SKILL.md](../../.agents/skills/daily-workflow/SKILL.md)
- Insert **Step 2R — Process RSS feeds** between Step 2 and Step 3:
  - Parse `data/feeds.yaml` to retrieve subscribed feeds.
  - Load seen URLs from `data/rss/seen/<feed_slug>.txt`.
  - Invoke `node /Users/allanbian/my-ai-workflow/.agents/skills/rss-reader/scripts/fetch-rss.mjs <url> --limit <limit> --skip <seen_urls>`.
  - For full-content articles: Summarize directly and write to `reports/RSS_YYYY_MM_DD/[feed_slug]_[article_slug].md`.
  - For snippet-only articles: Fetch via Jina Reader (`r.jina.ai`), falling back to snippet text if Jina/cleaner fails. Write to `reports/RSS_YYYY_MM_DD/[feed_slug]_[article_slug].md`.
  - Log suggestions to the pending backlog using `{SourceType}` = `RSS` (automatically delegating to `rubric-grader`).
  - Append processed URLs to `data/rss/seen/<feed_slug>.txt`.
- Update **Final Summary** section to include RSS statistics:
  ```
  Processed R RSS feed(s):
    ✅ ByteByteGo — "Top Anti-Patterns…" → reports/RSS_YYYY_MM_DD/filename.md
    ⏭️  ByteByteGo — 3 article(s) skipped (already seen)
  ```

---

### 4. Verification & Validation

#### [NEW] [validate_rss_config.py](../../scripts/validate_rss_config.py)
- Create a Python script to validate the RSS integration setup:
  - Verify that `data/feeds.yaml` is present and valid YAML.
  - Verify that `daily-workflow/SKILL.md` documents Step 2R.
  - Verify that `rss-reader/SKILL.md` documents `data/rss/seen/` usage.
  - Confirm the existence of `/Users/allanbian/my-ai-workflow/.agents/skills/rss-reader/scripts/fetch-rss.mjs`.

---

## Verification Plan

### Automated Tests

- **What to test**: Integrity of RSS configurations and skill documentation.
  - **How to test**: Run `python3 scripts/validate_rss_config.py`.
  - **Expected behavior**: Returns exit code 0.
- **What to test**: Execution of the daily workflow with RSS.
  - **How to test**: Run `daily-workflow` (or simulate Step 2R).
  - **Expected behavior**: Fetches, summarizes, and generates reports under `reports/RSS_YYYY_MM_DD/`, and updates `data/rss/seen/*.txt`. Subsequent runs skip already-seen URLs.
