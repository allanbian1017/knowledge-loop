#!/usr/bin/env bash
# ==============================================================================
# Knowledge Loop — Portable macOS Workspace Initializer
# ==============================================================================
# Links this knowledge-loop repository to a private Data Repo (or single-repo dir),
# creates gitignored local pointer files (workspace.local.env, repos.local.md),
# scaffolds missing starter data templates without overwriting existing files,
# and optionally pre-warms the local discord-reports MCP server.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DATA_REPO_INPUT=""
TIMEZONE_INPUT=""
WITH_CODE_WORKSPACE=false
SKIP_UV=false
NON_INTERACTIVE=false
FORCE_LOCAL_FILES=false

usage() {
  cat <<'EOF'
Usage: ./scripts/init_workspace.sh [options]

Options:
  --data-repo PATH       Path to your private Data Repo (relative to knowledge-loop or ~/...)
  --timezone TZ          IANA timezone name (default: detected macOS system timezone or UTC)
  --with-code-workspace  Generate gitignored knowledge-loop.code-workspace multi-root file
  --skip-uv              Skip running `uv sync` for mcp_servers/discord_reports
  --force                Overwrite existing workspace.local.env and repos.local.md
  --non-interactive      Do not prompt; use defaults or supplied flags
  -h, --help             Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --data-repo)
      DATA_REPO_INPUT="${2:?Missing value for --data-repo}"
      shift 2
      ;;
    --timezone)
      TIMEZONE_INPUT="${2:?Missing value for --timezone}"
      shift 2
      ;;
    --with-code-workspace)
      WITH_CODE_WORKSPACE=true
      shift
      ;;
    --skip-uv)
      SKIP_UV=true
      shift
      ;;
    --force)
      FORCE_LOCAL_FILES=true
      shift
      ;;
    --non-interactive)
      NON_INTERACTIVE=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

detect_timezone() {
  if [[ -L /etc/localtime ]]; then
    local target
    target="$(readlink /etc/localtime 2>/dev/null || true)"
    if [[ "$target" == *zoneinfo/* ]]; then
      printf '%s
' "${target#*zoneinfo/}"
      return 0
    fi
  fi
  printf '%s
' "UTC"
}

if [[ -z "$DATA_REPO_INPUT" ]]; then
  if [[ "$NON_INTERACTIVE" == true ]]; then
    DATA_REPO_INPUT="../my-knowledge-data"
  else
    read -r -p "Path to your private Data Repo [../my-knowledge-data]: " DATA_REPO_INPUT
    DATA_REPO_INPUT="${DATA_REPO_INPUT:-../my-knowledge-data}"
  fi
fi

if [[ -z "$TIMEZONE_INPUT" ]]; then
  DEFAULT_TZ="$(detect_timezone)"
  if [[ "$NON_INTERACTIVE" == true ]]; then
    TIMEZONE_INPUT="$DEFAULT_TZ"
  else
    read -r -p "Preferred IANA timezone [${DEFAULT_TZ}]: " TIMEZONE_INPUT
    TIMEZONE_INPUT="${TIMEZONE_INPUT:-$DEFAULT_TZ}"
  fi
fi

expand_target() {
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
' "$REPO_ROOT" "$raw"
  fi
}

DATA_REPO_ABS="$(expand_target "$DATA_REPO_INPUT")"
mkdir -p "$DATA_REPO_ABS/data" "$DATA_REPO_ABS/reports/distillations" "$DATA_REPO_ABS/.tmp"
DATA_REPO_ABS="$(cd "$DATA_REPO_ABS" && pwd)"

ENV_FILE="${REPO_ROOT}/workspace.local.env"
if [[ ! -f "$ENV_FILE" || "$FORCE_LOCAL_FILES" == true ]]; then
  cat > "$ENV_FILE" <<EOF
# Local Knowledge Loop configuration (gitignored — never commit)
DATA_REPO_DIR="${DATA_REPO_INPUT}"
USER_TIMEZONE="${TIMEZONE_INPUT}"
EOF
  echo "✅ Wrote ${ENV_FILE}"
else
  echo "ℹ️  Preserved existing ${ENV_FILE} (pass --force to overwrite)"
fi

REPOS_FILE="${REPO_ROOT}/repos.local.md"
if [[ ! -f "$REPOS_FILE" || "$FORCE_LOCAL_FILES" == true ]]; then
  sed "s|<DATA_REPO_PATH>|${DATA_REPO_INPUT}|g"     "${REPO_ROOT}/examples/repos.local.md.example" > "$REPOS_FILE"
  echo "✅ Wrote ${REPOS_FILE}"
else
  echo "ℹ️  Preserved existing ${REPOS_FILE} (pass --force to overwrite)"
fi

if [[ "$WITH_CODE_WORKSPACE" == true ]]; then
  WS_FILE="${REPO_ROOT}/knowledge-loop.code-workspace"
  if [[ ! -f "$WS_FILE" || "$FORCE_LOCAL_FILES" == true ]]; then
    sed "s|<DATA_REPO_PATH>|${DATA_REPO_INPUT}|g"       "${REPO_ROOT}/examples/knowledge-loop.code-workspace.example" > "$WS_FILE"
    echo "✅ Wrote ${WS_FILE}"
  else
    echo "ℹ️  Preserved existing ${WS_FILE}"
  fi
fi

echo "📂 Scaffolding missing starter templates into ${DATA_REPO_ABS}/data/..."
for src in "${REPO_ROOT}"/examples/data/*; do
  [[ -f "$src" ]] || continue
  base="$(basename "$src")"
  dest_name="${base/.example/}"
  dest="${DATA_REPO_ABS}/data/${dest_name}"
  if [[ ! -f "$dest" ]]; then
    cp "$src" "$dest"
    echo "  + Created data/${dest_name}"
  else
    echo "  = Kept existing data/${dest_name}"
  fi
done

if [[ "$SKIP_UV" == false ]] && command -v uv >/dev/null 2>&1; then
  if [[ -f "${REPO_ROOT}/mcp_servers/discord_reports/pyproject.toml" ]]; then
    echo "📦 Pre-warming discord-reports MCP virtual environment with uv..."
    uv sync --directory "${REPO_ROOT}/mcp_servers/discord_reports" ||       echo "⚠️  uv sync failed (network unavailable?); rerun manually later." >&2
  fi
fi

UV_BIN="$(command -v uv 2>/dev/null || echo 'uv')"
cat <<EOF

🎉 Workspace initialized!

  Knowledge Loop : ${REPO_ROOT}
  Data Repo : ${DATA_REPO_ABS}
  Timezone  : ${TIMEZONE_INPUT}

Next steps:
  1. Customize ${DATA_REPO_ABS}/data/goals.md and lang_preferences.md
  2. Open both folders together in a multi-root workspace (or pass --add-dir "${DATA_REPO_ABS}")
  3. Optional Discord MCP config (~/.gemini/config/mcp_config.json):
     "command": "${UV_BIN}"
     "args": ["run", "--directory", "${REPO_ROOT}/mcp_servers/discord_reports", "python", "server.py"]
     "env": { "KNOWLEDGE_LOOP_DATA_REPO": "${DATA_REPO_ABS}", "DISCORD_WEBHOOK_URL": "..." }
  4. Verify setup:
     python3 scripts/validate_skill.py && python3 scripts/validate_language_config.py
EOF
