#!/usr/bin/env bash
# Validate the selected personal preferences; never manufacture user configuration.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/../validate_language_config.py"
