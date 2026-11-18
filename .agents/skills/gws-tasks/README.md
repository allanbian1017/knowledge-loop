# gws-tasks

Bundled skill for the news-learning Home Repo.


## Home Repo setup

All required skill files come from this clone. See [macOS setup](../../../docs/setup.md) for the per-skill tool/capability matrix and [publication protocol](../content-summary/references/storage.md) for report workflows. Install external tools separately. Keep personal configuration, accounts and runtime data outside the checkout. For bundled third-party skills, retain the upstream license and provenance in the repository registry.

## ADR: Portable public Home Repo

- **Status:** Accepted.
- **Decision:** Keep reusable skill resources together and resolve report/personal roots from external configuration. Maintenance skills use the selected project; content workflows use the configured report repository.
- **Trade-off:** A report-producing skill needs explicit setup instead of assuming the author's working directory. Unavailable tools/capabilities stop only the affected workflow.

## Changelog — Home Repo migration

- Included complete reusable resources and documented external prerequisites.
- Preserved current workflow behavior and real human suggestion review.
- Removed dependence on personal paths and global companion skill installations.
