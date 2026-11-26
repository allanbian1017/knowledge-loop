#!/usr/bin/env bash
# Portable macOS/POSIX helper to resolve the Knowledge Loop Data Repo path.
#
# Precedence:
#   1. First positional argument (optional explicit override)
#   2. KNOWLEDGE_LOOP_DATA_REPO environment variable
#   3. DATA_REPO_DIR in <REPO_ROOT>/workspace.local.env
#   4. Single-repo fallback: <REPO_ROOT> if <REPO_ROOT>/data exists
#
# Prints the resolved absolute path to stdout, or exits 1 with a setup hint.

set -euo pipefail

_KL_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_KL_REPO_ROOT="${KNOWLEDGE_LOOP_ROOT:-$(cd "${_KL_SCRIPT_DIR}/../.." && pwd)}"

_kl_expand_path() {
  local raw="$1"
  case "$raw" in
    "~") raw="$HOME" ;;
    "~/"*) raw="${HOME}/${raw#~/}" ;;
  esac
  if [[ "$raw" = /* ]]; then
    printf '%s
' "$raw"
  else
    printf '%s/%s
' "$_KL_REPO_ROOT" "$raw"
  fi
}

_kl_read_local_env_var() {
  local key="$1"
  local env_file="${_KL_REPO_ROOT}/workspace.local.env"
  [[ -f "$env_file" ]] || return 0
  local line
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    line="${line#export }"
    if [[ "$line" == "${key}="* ]]; then
      local val="${line#*=}"
      val="${val#"${val%%[![:space:]]*}"}"
      val="${val%"${val##*[![:space:]]}"}"
      if [[ ${#val} -ge 2 ]]; then
        if [[ ("${val:0:1}" == '"' && "${val: -1}" == '"') || ("${val:0:1}" == "'" && "${val: -1}" == "'") ]]; then
          val="${val:1:${#val}-2}"
        fi
      fi
      printf '%s
' "$val"
      return 0
    fi
  done < "$env_file"
}

_kl_resolve_data_repo() {
  local raw="${1:-}"
  if [[ -z "$raw" && -n "${KNOWLEDGE_LOOP_DATA_REPO:-}" ]]; then
    raw="$KNOWLEDGE_LOOP_DATA_REPO"
  fi
  if [[ -z "$raw" ]]; then
    raw="$(_kl_read_local_env_var DATA_REPO_DIR)"
  fi
  if [[ -z "$raw" && -d "${_KL_REPO_ROOT}/data" ]]; then
    raw="$_KL_REPO_ROOT"
  fi
  if [[ -z "$raw" ]]; then
    echo "[knowledge-loop] Data Repo not configured. Run ./scripts/init_workspace.sh or set KNOWLEDGE_LOOP_DATA_REPO." >&2
    return 1
  fi

  local candidate
  candidate="$(_kl_expand_path "$raw")"
  if [[ -d "$candidate" ]]; then
    (cd "$candidate" && pwd)
  else
    printf '%s
' "$candidate"
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  _kl_resolve_data_repo "${1:-}"
fi
