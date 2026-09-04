#!/usr/bin/env bash

# ==============================================================================
# BeforeTool Hook: prevent_dangerous_commands.sh
# ==============================================================================
# Description: Intercepts run_command tools before they execute in the agent loop.
# Protocol:
#   - Input: JSON payload from stdin describing the tool and its arguments.
#   - Output (stdout): Must be valid JSON (or empty if no state changes).
#   - Output (stderr): Log messages.
#   - Exit Code 0: Allow command execution.
#   - Exit Code 2: Block command execution (stderr content is displayed to agent).
# ==============================================================================

# Read JSON payload from stdin
PAYLOAD=$(cat)

# Log the invocation to stderr (stdout must remain clean of non-JSON output)
echo "[Hook: BeforeTool] Intercepting command execution..." >&2

# Extract command string using simple grep/sed/awk/jq if available
# The payload shape generally includes arguments like:
# { "arguments": { "CommandLine": "command to run", "Cwd": "..." } }
COMMAND_LINE=$(echo "$PAYLOAD" | grep -o '"CommandLine": *"[^"]*"' | head -n 1 | cut -d'"' -f4)

if [ -z "$COMMAND_LINE" ]; then
  # Fallback: check if we could extract commandLine (case variations)
  COMMAND_LINE=$(echo "$PAYLOAD" | grep -oi '"CommandLine": *"[^"]*"' | head -n 1 | cut -d'"' -f4)
fi

echo "[Hook: BeforeTool] Extracted command: $COMMAND_LINE" >&2

# Simple check: block commands attempting force push or deleting root files
if [[ "$COMMAND_LINE" =~ "git push".*"--force" ]] || [[ "$COMMAND_LINE" =~ "rm -rf /" ]]; then
  echo "CRITICAL SAFETY VIOLATION: Dangerous command blocked by BeforeTool Hook: '$COMMAND_LINE'" >&2
  exit 2
fi

# Allow execution
echo "[Hook: BeforeTool] Command approved for execution." >&2
exit 0
