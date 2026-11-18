# Bundled skill provenance

Required skills are present in this clone. These sources document provenance; users do not need additional skill checkouts. Preserve notices when redistributing.

| Bundled resources | Upstream | License notice |
|---|---|---|
| `agent-browser` | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | [Apache-2.0](.agents/skills/agent-browser/LICENSE) |
| `gws-shared`, `gws-gmail`, `gws-tasks` | [googleworkspace/cli](https://github.com/googleworkspace/cli) | [Apache-2.0](.agents/skills/gws-shared/LICENSE) |
| `architecture-decision-records` | [wshobson/agents](https://github.com/wshobson/agents), documentation-generation plugin | [MIT](.agents/skills/architecture-decision-records/LICENSE) |

The existing registry in `skills-lock.json` retains source references/hashes. The bundled files contain documented local changes for public portability: neutral synthetic identities, complete dependency guidance and adjacent setup/decision records. They are not claimed to be byte-identical current upstream releases. CLI-provided browser command help is loaded from the installed tool so its syntax matches that version.

Other maintained learning-loop resources are covered by the repository [license](LICENSE). Hiring, outcome/evidence logging, diaries, personal writing and general decision coaching are not bundled.
