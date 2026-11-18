---
name: gws-gmail
description: "Gmail: Send, read, and manage email."
metadata:
  version: 0.22.5
  openclaw:
    category: "productivity"
    requires:
      bins:
        - gws
    cliHelp: "gws gmail --help"
---

# gmail (v1)

> **PREREQUISITE:** Read `../gws-shared/SKILL.md` for auth, global flags, and security rules. If missing, the clone is incomplete; restore the bundled skill before proceeding.

```bash
gws gmail <resource> <method> [flags]
```

## Helper Commands

| Command | Description |
|---------|-------------|
| [`+send`](https://github.com/googleworkspace/cli/tree/main/skills/gws-gmail-send) | Send an email |
| [`+triage`](https://github.com/googleworkspace/cli/tree/main/skills/gws-gmail-triage) | Show unread inbox summary (sender, subject, date) |
| [`+reply`](https://github.com/googleworkspace/cli/tree/main/skills/gws-gmail-reply) | Reply to a message (handles threading automatically) |
| [`+reply-all`](https://github.com/googleworkspace/cli/tree/main/skills/gws-gmail-reply-all) | Reply-all to a message (handles threading automatically) |
| [`+forward`](https://github.com/googleworkspace/cli/tree/main/skills/gws-gmail-forward) | Forward a message to new recipients |
| [`+read`](https://github.com/googleworkspace/cli/tree/main/skills/gws-gmail-read) | Read a message and extract its body or headers |
| [`+watch`](https://github.com/googleworkspace/cli/tree/main/skills/gws-gmail-watch) | Watch for new emails and stream them as NDJSON |

## API Resources

### users

  - `getProfile` — Gets the current user's Gmail profile.
  - `stop` — Stop receiving push notifications for the given user mailbox.
  - `watch` — Set up or update a push notification watch on the given user mailbox.
  - `drafts` — Operations on the 'drafts' resource
  - `history` — Operations on the 'history' resource
  - `labels` — Operations on the 'labels' resource
  - `messages` — Operations on the 'messages' resource
  - `settings` — Operations on the 'settings' resource
  - `threads` — Operations on the 'threads' resource

## Discovering Commands

Before calling any API method, inspect it:

```bash
# Browse resources and methods
gws gmail --help

# Inspect a method's required params, types, and defaults
gws schema gmail.<resource>.<method>
```

Use `gws schema` output to build your `--params` and `--json` flags.


Helper links above are optional upstream documentation. Required ingestion uses the bundled skills and `gws gmail +read --help`; no companion skill checkout is required.
