# Technical note: Command-wrapper parsing failure

This public copy retains the reusable technical lesson. Personal execution captures, account state, reading history and feedback are excluded; the historical filename is retained for existing links.

## Failure mode

A host command wrapper can reject CLI invocation before the underlying tool executes.

## Recovery and prevention

Report the host failure and restore supported command execution. Do not use alternate interpreters, paths or APIs as permission bypasses.

## Verification boundary

Use isolated synthetic fixtures for local contracts and failure injection. Tool authentication, source completeness and hardware throughput require the applicable authorized environment; offline storage tests do not establish them.

See [the storage protocol](../../.agents/skills/content-summary/references/storage.md), [macOS setup](../setup.md), and [known environment issues](../../known_issues.md).
