# Technical note: CPU-only transcription latency

This public copy retains the reusable technical lesson. Personal execution captures, account state, reading history and feedback are excluded; the historical filename is retained for existing links.

## Failure mode

A model-selection table calibrated for accelerated hardware can overestimate CPU-only throughput and block a synchronous pipeline.

## Recovery and prevention

Select a model appropriate to the actual execution environment, preserve transcription state, and monitor completion without assuming GPU performance.

## Verification boundary

Use isolated synthetic fixtures for local contracts and failure injection. Tool authentication, source completeness and hardware throughput require the applicable authorized environment; offline storage tests do not establish them.

See [the storage protocol](../../.agents/skills/content-summary/references/storage.md), [macOS setup](../setup.md), and [known environment issues](../../known_issues.md).
