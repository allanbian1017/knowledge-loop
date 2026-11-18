# Technical note: Truncated newsletter MIME content

This public copy retains the reusable technical lesson. Personal execution captures, account state, reading history and feedback are excluded; the historical filename is retained for existing links.

## Failure mode

A multipart newsletter can contain a short text/plain part while its full content exists in text/html.

## Recovery and prevention

Use the documented full HTML read with required headers. Verify completeness before summarizing and leave the source unread if required content is unavailable.

## Verification boundary

Use isolated synthetic fixtures for local contracts and failure injection. Tool authentication, source completeness and hardware throughput require the applicable authorized environment; offline storage tests do not establish them.

See [the storage protocol](../../.agents/skills/content-summary/references/storage.md), [macOS setup](../setup.md), and [known environment issues](../../known_issues.md).
