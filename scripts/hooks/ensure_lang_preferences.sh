#!/usr/bin/env bash
# ==============================================================================
# Lifecycle Hook: ensure_lang_preferences.sh
# ==============================================================================
# Ensures $DATA_REPO/data/lang_preferences.md exists and contains valid keys for
# Preferred Report Language and Preferred Conversation Language.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# shellcheck source=../lib/resolve_data_repo.sh
source "${HOME_ROOT}/scripts/lib/resolve_data_repo.sh"

DATA_REPO="$(_kl_resolve_data_repo 2>/dev/null || true)"
if [[ -z "$DATA_REPO" ]]; then
  echo "[Hook: ensure_lang_preferences] Data Repo not configured yet; skipping (run ./scripts/init_workspace.sh)." >&2
  exit 0
fi

PREF_FILE="${DATA_REPO}/data/lang_preferences.md"

if [[ ! -f "$PREF_FILE" ]]; then
  echo "[Hook: ensure_lang_preferences] ${PREF_FILE} missing, recreating default..." >&2
  mkdir -p "${DATA_REPO}/data"
  cat << 'EOF' > "$PREF_FILE"
# Language Preferences

- **Preferred Report Language**: English
- **Preferred Conversation Language**: English
EOF
  echo "[Hook: ensure_lang_preferences] Restored default configuration." >&2
  exit 0
fi

NEEDS_REPAIR=false
if ! grep -q "Preferred Report Language" "$PREF_FILE"; then
  NEEDS_REPAIR=true
fi
if ! grep -q "Preferred Conversation Language" "$PREF_FILE"; then
  NEEDS_REPAIR=true
fi

if [[ "$NEEDS_REPAIR" == true ]]; then
  echo "[Hook: ensure_lang_preferences] Missing keys in ${PREF_FILE}, repairing..." >&2
  REPORT_LANG=$(grep "Preferred Report Language" "$PREF_FILE" | sed -E 's/.*:[[:space:]]*//' || true)
  CONV_LANG=$(grep "Preferred Conversation Language" "$PREF_FILE" | sed -E 's/.*:[[:space:]]*//' || true)
  [[ -z "$REPORT_LANG" ]] && REPORT_LANG="English"
  [[ -z "$CONV_LANG" ]] && CONV_LANG="English"
  cat << EOF > "$PREF_FILE"
# Language Preferences

- **Preferred Report Language**: ${REPORT_LANG}
- **Preferred Conversation Language**: ${CONV_LANG}
EOF
  echo "[Hook: ensure_lang_preferences] Repaired configuration." >&2
fi

exit 0
