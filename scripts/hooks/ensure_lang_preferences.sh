#!/usr/bin/env bash

# ==============================================================================
# Lifecycle Hook: ensure_lang_preferences.sh
# ==============================================================================
# Description: Ensures data/lang_preferences.md always exists and contains valid
#              keys for Preferred Report Language and Preferred Conversation Language.
# Protocol:
#   - Input: stdin JSON payload (if called by Antigravity hook harness)
#   - Exit Code: 0 on success / auto-repair
# ==============================================================================

set -euo pipefail

# Find repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PREF_FILE="${REPO_ROOT}/data/lang_preferences.md"

# Auto-create if missing
if [[ ! -f "$PREF_FILE" ]]; then
  echo "[Hook: ensure_lang_preferences] ${PREF_FILE} missing, recreating default..." >&2
  mkdir -p "${REPO_ROOT}/data"
  cat << 'EOF' > "$PREF_FILE"
# Language Preferences

- **Preferred Report Language**: English
- **Preferred Conversation Language**: English
EOF
  echo "[Hook: ensure_lang_preferences] Restored default configuration." >&2
  exit 0
fi

# Validate content and repair missing keys if necessary
NEEDS_REPAIR=false

if ! grep -q "Preferred Report Language" "$PREF_FILE"; then
  NEEDS_REPAIR=true
fi

if ! grep -q "Preferred Conversation Language" "$PREF_FILE"; then
  NEEDS_REPAIR=true
fi

if [[ "$NEEDS_REPAIR" == true ]]; then
  echo "[Hook: ensure_lang_preferences] Corrupted or missing keys in ${PREF_FILE}, repairing..." >&2
  REPORT_LANG=$(grep "Preferred Report Language" "$PREF_FILE" | sed -E 's/.*:[[:space:]]*//' || true)
  CONV_LANG=$(grep "Preferred Conversation Language" "$PREF_FILE" | sed -E 's/.*:[[:space:]]*//' || true)

  if [[ -z "$REPORT_LANG" ]]; then
    REPORT_LANG="English"
  fi
  if [[ -z "$CONV_LANG" ]]; then
    CONV_LANG="English"
  fi

  cat << EOF > "$PREF_FILE"
# Language Preferences

- **Preferred Report Language**: ${REPORT_LANG}
- **Preferred Conversation Language**: ${CONV_LANG}
EOF
  echo "[Hook: ensure_lang_preferences] Repaired configuration." >&2
fi

exit 0
