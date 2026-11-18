# Technical note: Lost asynchronous transcription completion

This public copy retains the reusable technical lesson. Personal execution captures, account state, reading history and feedback are excluded; the historical filename is retained for existing links.

## Failure mode

A background transcription can finish without its result entering the remaining ingestion lifecycle when completion tracking is lost.

## Recovery and prevention

Track exact process/source identities through completion, validate the transcript, publish the final report and suggestion, then acknowledge the source. A running process is not a completed report.

## Verification boundary

Use isolated synthetic fixtures for local contracts and failure injection. Tool authentication, source completeness and hardware throughput require the applicable authorized environment; offline storage tests do not establish them.

See [the storage protocol](../../.agents/skills/content-summary/references/storage.md), [macOS setup](../setup.md), and [known environment issues](../../known_issues.md).
