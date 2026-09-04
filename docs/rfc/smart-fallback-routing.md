# RFC: Smart Fallback Routing Based on Historical Data

## Summary

Add a persistent domain-to-strategy routing table (`data/domain_routes.json`) that records which fetch strategies succeed or fail for each domain. Ingestion skills consult this table before starting their fallback chain, skipping strategies known to fail for the target domain. The table auto-updates after each fetch attempt, creating a self-learning routing system.

## Status

**Proposed** — 2026-06-25  
**Revised** — 2026-07-07 (post grill-me session)

## Motivation

### The linear fallback chain is wasteful

The current [ingest-website/SKILL.md](../../.agents/skills/ingest-website/SKILL.md) uses a fixed 4-step fallback chain:

```
Jina Reader → agent-browser headless → agent-browser headed → search_web
```

Every URL starts at step 1 regardless of history. For domains known to block automated access (Medium, Twitter/X, Facebook), the agent **always** exhausts 2–3 failing steps (each taking 1–3 minutes) before reaching the strategy that actually works.

### Evidence from past sessions

From [learnings/lessons.md](../../learnings/lessons.md) and decision logs:

| Domain / Pattern | Jina | Browser Headless | Browser Headed | search_web | Working Strategy |
|---|---|---|---|---|---|
| `medium.com` | ❌ 403 | ❌ 403 | ❌ 403 | ✅ | `search_web` |
| Dave Davies article | ❌ 403 | ❌ 403 | ❌ 500 | ✅ | `search_web` |
| `threads.net` | ❌ (not applicable) | Requires auth cookie | — | — | `agent-browser` + auth |
| `twitter.com` / `x.com` | ❌ 451 | ❌ login wall | ❌ login wall | — | Skip (login wall) |
| `facebook.com` | ❌ login wall | ❌ login wall | ❌ login wall | — | Skip (login wall) |

From the [stale cache RCA](../rca/daily_workflow_rca_2026-06-18_V1.md): the agent once invented its own fallback (reading stale `.tmp/` files) because all documented strategies failed. The anti-cache guardrail RFC addressed the symptom, but the root cause — no intelligent routing — remains.

### No persistent memory between sessions

The `lessons.md` file captures human-readable patterns ("Cloudflare blocks Medium"), but:
1. It's not machine-readable — no skill parses it for routing decisions
2. It's not automatically updated when new failures occur
3. It doesn't distinguish transient failures (timeout) from permanent blocks (Cloudflare 403)

Each daily workflow run re-discovers the same failures by trial and error.

---

## Detailed Design

### 1. Domain route table: `data/domain_routes.json`

A persistent JSON file mapping domains to their known fetch strategy outcomes:

```json
{
  "version": 1,
  "routes": {
    "medium.com": {
      "preferred_strategy": "search_web",
      "strategies": {
        "jina": { "status": "blocked", "error": "403 Cloudflare", "last_seen": "2026-06-20" },
        "browser_headless": { "status": "blocked", "error": "403 Cloudflare", "last_seen": "2026-06-20" },
        "browser_headed": { "status": "blocked", "error": "403 Cloudflare", "last_seen": "2026-06-20" },
        "search_web": { "status": "ok", "last_seen": "2026-06-20" }
      },
      "failure_class": "permanent"
    },
    "x.com": {
      "preferred_strategy": "skip",
      "strategies": {
        "jina": { "status": "blocked", "error": "451", "last_seen": "2026-06-18" },
        "browser_headless": { "status": "blocked", "error": "login_wall", "last_seen": "2026-06-18" }
      },
      "failure_class": "permanent",
      "skip_reason": "Login wall — no auth mechanism available"
    },
    "threads.net": {
      "preferred_strategy": "browser_headless",
      "requires": "threads-auth.json",
      "strategies": {
        "browser_headless": { "status": "ok", "last_seen": "2026-06-25", "condition": "auth cookie valid" }
      },
      "failure_class": "conditional"
    }
  },
  "blocklist": ["facebook.com", "instagram.com", "linkedin.com"]
}
```

**Schema details:**

| Field | Type | Description |
|---|---|---|
| `preferred_strategy` | string | The strategy to try first: `jina`, `browser_headless`, `browser_headed`, `search_web`, `skip` |
| `strategies.<name>.status` | string | `ok`, `blocked`, `unknown` |
| `strategies.<name>.error` | string | Error description from last failure |
| `strategies.<name>.last_seen` | string | ISO date of last attempt |
| `failure_class` | string | `permanent` (always fails), `transient` (sometimes fails), `conditional` (depends on auth/state) |
| `requires` | string | Optional prerequisite (e.g., auth cookie file) |
| `blocklist` | array | Domains to always skip immediately |
| `skip_reason` | string | Why a domain is permanently skipped |

### 2. Route lookup algorithm

Before starting the fallback chain, the ingestion skill consults the route table:

```
function resolve_strategy(url):
    domain = extract_domain(url)

    # Check blocklist first
    if domain in routes.blocklist:
        log "⚠️ Skipping '<title>': domain <domain> is blocklisted."
        return SKIP (do NOT mark task as completed — leave in Delegate list)

    # Check for a known route
    if domain in routes.routes:
        route = routes.routes[domain]

        # Check conditional requirements
        if route.requires and not file_exists(route.requires):
            log "⚠️ Skipping: missing prerequisite {route.requires}"
            return SKIP (do NOT mark task as completed)

        # Check staleness based on failure_class
        if route.failure_class == "permanent":
            # Never expires — manual reset only
            return route.preferred_strategy

        elif route.failure_class == "transient":
            if route.preferred_strategy.last_seen > 7 days ago:
                return DEFAULT_CHAIN  # re-test
            return route.preferred_strategy

        elif route.failure_class == "conditional":
            # Always check prerequisite, no time-based expiry
            if route.requires and file_exists(route.requires):
                return route.preferred_strategy
            else:
                return SKIP

        else:  # "unknown" or unset
            if route.preferred_strategy.last_seen > 30 days ago:
                return DEFAULT_CHAIN
            return route.preferred_strategy

    # Unknown domain — use default chain
    return DEFAULT_CHAIN
```

**Default chain** remains: `jina → browser_headless → browser_headed → search_web`.

The key behavior: for unknown domains, nothing changes. The routing table only accelerates domains that have been seen before.

### 3. Auto-update after each fetch attempt

After every fetch attempt (success or failure), the ingestion skill updates the route table:

```
function update_route(domain, strategy, success, error=null):
    if domain not in routes.routes:
        routes.routes[domain] = { strategies: {}, failure_class: "unknown" }

    route = routes.routes[domain]
    route.strategies[strategy] = {
        status: success ? "ok" : "blocked",
        error: error,
        last_seen: today()
    }

    if success:
        route.preferred_strategy = strategy

    # Classify failure class
    if all strategies are "blocked":
        route.failure_class = "permanent"
    elif any strategy is "blocked":
        route.failure_class = "transient"

    write(routes)
```

This means the route table grows organically. After the first run that encounters a new Cloudflare-blocked domain, all subsequent runs skip directly to the working strategy.

### 4. Integration with ingestion skills

#### `ingest-website/SKILL.md` changes

Add a new Step 0 before the fetch step:

```markdown
### Step 0 — Route lookup

Read `data/domain_routes.json`. Extract the domain from the target URL.

- If the domain is in `blocklist`: skip this task immediately. Log:
  "⚠️ Skipping '<title>': domain <domain> is blocklisted (<skip_reason>)."
  Do NOT mark the Google Task as completed — leave it in the Delegate list
  for manual review.

- If the domain has a `preferred_strategy`: start with that strategy instead
  of the default Jina Reader. If the preferred strategy fails, fall through
  to the remaining strategies in the default chain.

- If the domain is unknown: use the default chain (Jina → browser → search_web).

After each fetch attempt (success or failure), update `data/domain_routes.json`
with the result.
```

#### `ingest-threads/SKILL.md` changes

Add auth cookie pre-check:

```markdown
### Step 0 — Pre-check

Read `data/domain_routes.json` for `threads.net`.

If `requires` field specifies `threads-auth.json`, check if the file exists.
If missing, skip this task immediately and log:
"⚠️ Skipping Threads task: threads-auth.json not found."
```

#### `ingest-youtube/SKILL.md` — no changes

YouTube uses `yt2doc` (external binary). There's no fallback chain to optimise. If `yt2doc` fails with 403, the failure is logged but no alternative strategy exists.

#### `ingest-newsletter/SKILL.md` — no changes

Newsletter fetches content via Gmail API, not URL-based fetching. No fallback routing needed.

### 5. Seed data

Pre-populate `data/domain_routes.json` with known failures from `learnings/lessons.md` and decision logs:

```json
{
  "version": 1,
  "routes": {
    "medium.com": {
      "preferred_strategy": "search_web",
      "strategies": {
        "jina": { "status": "blocked", "error": "403 Cloudflare WAF", "last_seen": "2026-06-20" },
        "search_web": { "status": "ok", "last_seen": "2026-06-20" }
      },
      "failure_class": "permanent"
    },
    "x.com": {
      "preferred_strategy": "skip",
      "strategies": {
        "jina": { "status": "blocked", "error": "451", "last_seen": "2026-06-18" },
        "browser_headless": { "status": "blocked", "error": "login_wall", "last_seen": "2026-06-18" }
      },
      "failure_class": "permanent",
      "skip_reason": "Login wall — no auth mechanism available"
    },
    "twitter.com": {
      "preferred_strategy": "skip",
      "strategies": {
        "jina": { "status": "blocked", "error": "Redirects to x.com login", "last_seen": "2026-06-18" }
      },
      "failure_class": "permanent",
      "skip_reason": "Redirects to x.com login wall"
    },
    "threads.net": {
      "preferred_strategy": "browser_headless",
      "requires": "threads-auth.json",
      "strategies": {
        "browser_headless": { "status": "ok", "last_seen": "2026-06-25", "condition": "auth cookie valid" }
      },
      "failure_class": "conditional"
    }
  },
  "blocklist": ["facebook.com", "instagram.com", "linkedin.com"]
}
```

### 6. Staleness policy

Staleness windows are **differentiated by `failure_class`** to match the nature of each failure type:

| `failure_class` | Staleness window | Re-test behavior |
|---|---|---|
| `permanent` | **Never expires** | Manual reset only. To re-test, delete the entry from `domain_routes.json`. Rationale: Cloudflare WAF and login walls are business decisions that don't resolve themselves. |
| `transient` | **7 days** | After 7 days, falls back to the default chain and re-tests. Rationale: temporary outages and rate limits typically resolve within a week. |
| `conditional` | **No time-based expiry** | Checks the prerequisite file on every run. If the prerequisite exists, uses the preferred strategy. If missing, skips. Rationale: auth cookies expire independently of calendar time. |
| `unknown` / unset | **30 days** | Default fallback for entries without a classified failure type. |

This prevents the system from wasting 3–8 minutes re-testing permanently blocked domains (e.g., `medium.com` via Cloudflare) while ensuring transient failures are re-evaluated promptly.

---

## Drawbacks

- **Single JSON file for all skills**: Multiple ingestion subagents (from the parallel processing RFC) may try to update `domain_routes.json` concurrently. Mitigated by: (a) most updates are for different domains, and (b) a last-write-wins approach is acceptable since route data is append-mostly and idempotent.
- **Route table maintenance**: Over time, the table accumulates entries for one-off domains that won't be seen again. Mitigated by the 30-day staleness policy, which naturally prunes stale entries when re-tested.
- **Skill instruction complexity**: Adding Step 0 to `ingest-website/SKILL.md` increases instruction length. This is ~15 lines of clear, structured instructions — minimal compared to the existing skill (~80 lines).

## Alternatives Considered

- **Extend `learnings/lessons.md` to be machine-readable**: Add structured YAML blocks to lessons.md that skills could parse. Rejected: lessons.md serves a different purpose (human-readable gotchas for the bootstrap checklist). Mixing machine-readable routing data into it would violate separation of concerns.

- **Build a per-URL cache (not per-domain)**: Track outcomes for exact URLs, not domains. Rejected: most failure patterns are domain-level (Cloudflare protects the entire domain, not individual URLs). Per-URL tracking adds storage overhead without meaningful benefit.

- **Use a database (SQLite) instead of JSON**: Provides proper concurrency and query capabilities. Rejected: over-engineered. The route table will have < 100 entries. A single JSON file is readable, editable, and version-controllable.

- **Automatic blocklist promotion**: When all strategies for a domain fail 3+ times, auto-add to blocklist. Rejected for now: the blocklist should remain manually curated to avoid accidentally blocking domains that have transient issues. Can be revisited once the route table is in use and patterns emerge.

---

## Interaction with Parallel Processing RFC

> [!NOTE]
> This RFC is **fully independent** of the parallel content processing RFC. Either can be implemented first, and neither depends on the other. This section is a forward-looking note on how they compose if both are implemented.

If the parallel processing RFC is also implemented, multiple subagents may update `domain_routes.json` concurrently. Two mitigations:

1. **Read-before-dispatch**: The orchestrator reads the route table once before dispatching subagents, and passes the relevant route entry to each subagent in its prompt. The subagent uses the provided route without re-reading the file.

2. **Write-after-completion**: Each subagent reports its fetch outcomes (domain, strategy, success/failure) back to the orchestrator. The orchestrator batch-updates `domain_routes.json` after all subagents complete, in a single-threaded merge step (similar to the suggestion merge).

This eliminates concurrent file writes entirely.

---

## Implementation Plan

### Phase 1 — Seed data
1. Create `data/domain_routes.json` with seed entries from §5

### Phase 2 — Route lookup in `ingest-website`
1. Add Step 0 (route lookup) to `ingest-website/SKILL.md`
2. Add auto-update logic after each fetch attempt
3. Add `threads-auth.json` pre-check to `ingest-threads/SKILL.md`

### Phase 3 — Verification
1. Test with a known-blocked domain (e.g., `medium.com`): verify it skips directly to `search_web`
2. Test with an unknown domain: verify it uses the default chain and records the result
3. Test with a blocklisted domain: verify it skips immediately
4. Verify `domain_routes.json` is correctly updated after each run
