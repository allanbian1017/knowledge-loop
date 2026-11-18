# Technical note: Worker file access and output contracts

This public copy retains the reusable technical lesson. Personal execution captures, account state, reading history and feedback are excluded; the historical filename is retained for existing links.

## Failure mode

Removing file-reading capability to work around an initialization error prevents workers from loading preferences and templates.

## Recovery and prevention

Use supported file-access tools, explicit resolved roots and a fixed report date. Preserve required capabilities and validate output contracts instead of hiding initialization failures.

## Verification boundary

Use isolated synthetic fixtures for local contracts and failure injection. Tool authentication, source completeness and hardware throughput require the applicable authorized environment; offline storage tests do not establish them.

See [the storage protocol](../../.agents/skills/content-summary/references/storage.md), [macOS setup](../setup.md), and [known environment issues](../../known_issues.md).
