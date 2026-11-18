# Technical note: Language preference drift

This public copy retains the reusable technical lesson. Personal execution captures, account state, reading history and feedback are excluded; the historical filename is retained for existing links.

## Failure mode

Regenerating a preference profile can drop language keys, while language-heavy templates can bias subsequent output.

## Recovery and prevention

Keep language settings in the external personal-data file. Validate both keys before execution and preserve them during feedback calibration; template language does not override user configuration.

## Verification boundary

Use isolated synthetic fixtures for local contracts and failure injection. Tool authentication, source completeness and hardware throughput require the applicable authorized environment; offline storage tests do not establish them.

See [the storage protocol](../../.agents/skills/content-summary/references/storage.md), [macOS setup](../setup.md), and [known environment issues](../../known_issues.md).
