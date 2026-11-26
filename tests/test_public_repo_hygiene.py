"""Automated privacy, portability, skill validation, and persona-sync hygiene tests."""

from pathlib import Path
import subprocess
import sys

HOME_ROOT = Path(__file__).resolve().parents[1]
if str(HOME_ROOT) not in sys.path:
    sys.path.insert(0, str(HOME_ROOT))

from scripts.audit_public_repo import audit, scan_file_contents


def test_public_repo_has_zero_hygiene_violations():
    violations = audit(HOME_ROOT)
    assert violations == [], "Public hygiene violations detected:\n" + "\n".join(violations)


def test_audit_detects_synthetic_pii_and_absolute_paths(tmp_path):
    bad = tmp_path / "leaky.md"
    bad.write_text(
        "Path: " + "/" + "Users/someone/project\n"
        "Webhook: https://discord.com/api/webhooks/123456789012345678/AbCdEfGhIjKlMnOpQrSt\n"
        "Email: personal.name@gmail.com\n",
        encoding="utf-8",
    )
    findings = scan_file_contents(tmp_path, [bad])
    joined = "\n".join(findings)
    assert "ABSOLUTE_PATH_MACOS" in joined
    assert "LIVE_DISCORD_WEBHOOK" in joined
    assert "PERSONAL_EMAIL" in joined


def test_all_20_skills_pass_validation():
    skills = sorted((HOME_ROOT / ".agents" / "skills").glob("*/SKILL.md"))
    assert len(skills) == 20, f"Expected 20 approved skills, found {len(skills)}"
    res = subprocess.run(
        [sys.executable, "scripts/validate_skill.py"],
        cwd=HOME_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr


def test_subagent_personas_synced_without_drift():
    before = {
        p.relative_to(HOME_ROOT): p.read_bytes()
        for folder in (".claude/agents", ".claude/subagents", ".codex/agents", ".codex/subagents")
        for p in sorted((HOME_ROOT / folder).glob("*"))
        if p.is_file()
    }
    res = subprocess.run(
        [sys.executable, "scripts/sync_subagents.py"],
        cwd=HOME_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    after = {
        p.relative_to(HOME_ROOT): p.read_bytes()
        for folder in (".claude/agents", ".claude/subagents", ".codex/agents", ".codex/subagents")
        for p in sorted((HOME_ROOT / folder).glob("*"))
        if p.is_file()
    }
    assert before == after, "Generated persona adapters drifted from .agents/agents/"
