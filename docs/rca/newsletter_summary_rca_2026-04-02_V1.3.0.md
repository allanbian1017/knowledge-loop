# Technical note: Summary depth and two-phase generation

This public copy retains the reusable technical lesson. Personal execution captures, account state, reading history and feedback are excluded; the historical filename is retained for existing links.

## Failure mode

A fetching phase followed by summary generation can omit required report depth when source completeness and output contracts are not checked separately.

## Recovery and prevention

Verify each full source, then apply the current report template independently to every item. Do not use arbitrary character length as a substitute for coverage and evidence.

## Verification boundary

Use isolated synthetic fixtures for local contracts and failure injection. Tool authentication, source completeness and hardware throughput require the applicable authorized environment; offline storage tests do not establish them.

See [the storage protocol](../../.agents/skills/content-summary/references/storage.md), [macOS setup](../setup.md), and [known environment issues](../../known_issues.md).
