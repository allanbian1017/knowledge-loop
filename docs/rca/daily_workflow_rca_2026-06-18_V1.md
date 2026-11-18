# Technical note: Stale source capture reuse

This public copy retains the reusable technical lesson. Personal execution captures, account state, reading history and feedback are excluded; the historical filename is retained for existing links.

## Failure mode

Generic cache filenames can associate a new URL with an older capture.

## Recovery and prevention

Use isolated run/source staging and bind source identity to publication. Fetch and read the complete selected source rather than inferring content from a cached filename.

## Verification boundary

Use isolated synthetic fixtures for local contracts and failure injection. Tool authentication, source completeness and hardware throughput require the applicable authorized environment; offline storage tests do not establish them.

See [the storage protocol](../../.agents/skills/content-summary/references/storage.md), [macOS setup](../setup.md), and [known environment issues](../../known_issues.md).
