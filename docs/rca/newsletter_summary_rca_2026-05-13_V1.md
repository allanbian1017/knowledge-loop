# Technical note: Stale report validation contract

This public copy retains the reusable technical lesson. Personal execution captures, account state, reading history and feedback are excluded; the historical filename is retained for existing links.

## Failure mode

A validator can continue requiring fields that have intentionally moved from reports into a separate suggestion ledger.

## Recovery and prevention

Keep validators aligned with current report and suggestion contracts. Test both independently; do not add obsolete report sections merely to satisfy stale assertions.

## Verification boundary

Use isolated synthetic fixtures for local contracts and failure injection. Tool authentication, source completeness and hardware throughput require the applicable authorized environment; offline storage tests do not establish them.

See [the storage protocol](../../.agents/skills/content-summary/references/storage.md), [macOS setup](../setup.md), and [known environment issues](../../known_issues.md).
