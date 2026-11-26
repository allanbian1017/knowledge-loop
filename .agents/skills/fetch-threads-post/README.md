# `fetch-threads-post` Skill

Part of the Knowledge Loop knowledge-loop skill catalog.
### ADR (Portable Data Repo Separation)
- **Decision**: Parameterized data/report paths to `$DATA_REPO/...` and removed all machine-specific absolute paths so this skill runs cleanly from the public `knowledge-loop` knowledge-loop against any user's private Data Repo on macOS.
- **Changelog (2026-11-26)**: Adopted portable `$DATA_REPO` path convention and verified zero-PII / zero-absolute-path portability.
