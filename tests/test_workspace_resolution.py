"""Tests for portable `knowledge-loop` -> Data Repo path resolution, hooks, and init_workspace.sh."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.workspace_paths import get_timezone, resolve_data_repo


def test_precedence_override_env_local_and_fallback(tmp_path, monkeypatch):
    home = tmp_path / "repo-root"
    home.mkdir()
    d_override = tmp_path / "d-override"
    d_env = tmp_path / "d-env"
    d_local = tmp_path / "d-local"
    for d in (d_override, d_env, d_local):
        d.mkdir()

    monkeypatch.delenv("KNOWLEDGE_LOOP_DATA_REPO", raising=False)

    # Unconfigured raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        resolve_data_repo(repo_root=home)

    # 4. Single-repo fallback if <home>/data exists
    (home / "data").mkdir()
    assert resolve_data_repo(repo_root=home) == home.resolve()

    # 3. workspace.local.env overrides single-repo fallback (supports relative paths)
    (home / "workspace.local.env").write_text(
        'DATA_REPO_DIR="../d-local"\nUSER_TIMEZONE="America/New_York"\n',
        encoding="utf-8",
    )
    assert resolve_data_repo(repo_root=home) == d_local.resolve()
    assert get_timezone(repo_root=home) == "America/New_York"

    # 2. Env var overrides workspace.local.env
    monkeypatch.setenv("KNOWLEDGE_LOOP_DATA_REPO", str(d_env))
    assert resolve_data_repo(repo_root=home) == d_env.resolve()

    # 1. Explicit override beats env var
    assert resolve_data_repo(override=d_override, repo_root=home) == d_override.resolve()


def test_bash_resolver_and_hook_in_arbitrary_data_repo(tmp_path):
    data_repo = tmp_path / "any-mac-user-data"
    data_repo.mkdir()

    env = os.environ.copy()
    env["KNOWLEDGE_LOOP_DATA_REPO"] = str(data_repo)

    res = subprocess.run(
        [str(REPO_ROOT / "scripts/lib/resolve_data_repo.sh")],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stderr
    assert Path(res.stdout.strip()).resolve() == data_repo.resolve()

    # Hook auto-creates data/lang_preferences.md in external Data Repo, never in knowledge-loop
    hook = subprocess.run(
        [str(REPO_ROOT / "scripts/hooks/ensure_lang_preferences.sh")],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert hook.returncode == 0, hook.stderr
    pref = data_repo / "data" / "lang_preferences.md"
    assert pref.is_file()
    assert "Preferred Report Language" in pref.read_text(encoding="utf-8")
    assert not (REPO_ROOT / "data").exists()


def test_init_workspace_scaffolds_and_preserves_existing_data(tmp_path):
    fake_home = tmp_path / "knowledge-loop-copy"
    shutil.copytree(REPO_ROOT / "examples", fake_home / "examples")
    (fake_home / "scripts").mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "scripts/init_workspace.sh", fake_home / "scripts/init_workspace.sh")

    data_repo = tmp_path / "private-data"
    res = subprocess.run(
        [
            str(fake_home / "scripts/init_workspace.sh"),
            "--data-repo",
            "../private-data",
            "--timezone",
            "UTC",
            "--with-code-workspace",
            "--skip-uv",
            "--non-interactive",
        ],
        cwd=fake_home,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    assert (fake_home / "workspace.local.env").is_file()
    assert (fake_home / "repos.local.md").is_file()
    assert (fake_home / "knowledge-loop.code-workspace").is_file()
    assert (data_repo / "data" / "lang_preferences.md").is_file()
    assert (data_repo / "data" / "goals.md").is_file()
    assert (data_repo / "data" / "integrations.md").is_file()
    assert (data_repo / "data" / "newsletter_aliases.json").is_file()

    # Customize goals.md and re-run: must NEVER overwrite existing user data
    custom_goals = "# Custom Private Goals\n- Ship safely\n"
    (data_repo / "data" / "goals.md").write_text(custom_goals, encoding="utf-8")
    res2 = subprocess.run(
        [
            str(fake_home / "scripts/init_workspace.sh"),
            "--data-repo",
            "../private-data",
            "--skip-uv",
            "--non-interactive",
        ],
        cwd=fake_home,
        capture_output=True,
        text=True,
    )
    assert res2.returncode == 0, res2.stdout + res2.stderr
    assert (data_repo / "data" / "goals.md").read_text(encoding="utf-8") == custom_goals
