"""Portable `knowledge-loop` -> Data Repo path resolution.

Resolution precedence for the Data Repo:
1. Explicit ``override`` path (e.g., ``--data-repo`` CLI flag)
2. ``KNOWLEDGE_LOOP_DATA_REPO`` environment variable
3. ``DATA_REPO_DIR`` defined in ``<REPO_ROOT>/workspace.local.env``
4. Single-repo fallback: ``<REPO_ROOT>`` if ``<REPO_ROOT>/data`` exists

Relative paths are resolved against ``REPO_ROOT``. ``~`` is expanded via
``os.path.expanduser``. Zero hardcoded absolute paths are required.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_DATA_REPO = "KNOWLEDGE_LOOP_DATA_REPO"
ENV_TIMEZONE = "USER_TIMEZONE"
LOCAL_ENV_FILENAME = "workspace.local.env"


def get_repo_root(start: Path | None = None) -> Path:
    """Return the Knowledge Loop knowledge-loop directory."""
    if start is not None:
        return Path(start).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def load_local_env(repo_root: Path | None = None) -> dict[str, str]:
    """Parse KEY=VALUE pairs from ``<REPO_ROOT>/workspace.local.env`` if present."""
    root = get_repo_root(repo_root)
    env_file = root / LOCAL_ENV_FILENAME
    values: dict[str, str] = {}
    if not env_file.is_file():
        return values

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def _resolve_candidate(raw_path: str, repo_root: Path) -> Path:
    expanded = os.path.expanduser(raw_path.strip())
    candidate = Path(expanded)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def resolve_data_repo(
    override: str | Path | None = None,
    *,
    repo_root: Path | None = None,
    require_exists: bool = True,
) -> Path:
    """Resolve the active Data Repo directory using deterministic precedence."""
    root = get_repo_root(repo_root)
    candidate: Path | None = None

    if override is not None and str(override).strip():
        candidate = _resolve_candidate(str(override), root)
    else:
        env_val = os.environ.get(ENV_DATA_REPO, "").strip()
        if env_val:
            candidate = _resolve_candidate(env_val, root)
        else:
            local_env = load_local_env(root)
            local_val = local_env.get("DATA_REPO_DIR", "").strip()
            if local_val:
                candidate = _resolve_candidate(local_val, root)
            elif (root / "data").is_dir():
                candidate = root

    if candidate is None:
        raise FileNotFoundError(
            "Data Repo is not configured. Set KNOWLEDGE_LOOP_DATA_REPO, create "
            f"{LOCAL_ENV_FILENAME} via ./scripts/init_workspace.sh, or run in single-repo mode."
        )

    if require_exists and not candidate.is_dir():
        raise FileNotFoundError(
            f"Resolved Data Repo directory does not exist: {candidate}. "
            "Run ./scripts/init_workspace.sh --data-repo <path> to initialize it."
        )

    return candidate


def data_dir(override: str | Path | None = None, *, repo_root: Path | None = None, require_exists: bool = False) -> Path:
    return resolve_data_repo(override, repo_root=repo_root, require_exists=require_exists) / "data"


def reports_dir(override: str | Path | None = None, *, repo_root: Path | None = None, require_exists: bool = False) -> Path:
    return resolve_data_repo(override, repo_root=repo_root, require_exists=require_exists) / "reports"


def get_timezone(repo_root: Path | None = None, default: str = "UTC") -> str:
    env_tz = os.environ.get(ENV_TIMEZONE, "").strip()
    if env_tz:
        return env_tz
    local_tz = load_local_env(repo_root).get(ENV_TIMEZONE, "").strip()
    return local_tz or default
