"""Automated privacy, portability, skill validation, and persona-sync hygiene tests."""

from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.audit_public_repo import audit, scan_file_contents


def test_public_repo_has_zero_hygiene_violations():
    violations = audit(REPO_ROOT)
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


def test_audit_allows_only_the_exact_public_clone_command_in_the_setup_guide(tmp_path):
    guide = tmp_path / "docs/guides/setup-guide.md"
    guide.parent.mkdir(parents=True)
    clone = "git clone git@github.com:allanbian1017/knowledge-loop.git knowledge-loop"
    guide.write_text(f"{clone}\n{clone} # personal.name@gmail.com\n", encoding="utf-8")
    other = tmp_path / "other.md"
    other.write_text(f"{clone}\n", encoding="utf-8")

    findings = scan_file_contents(tmp_path, [guide, other])

    assert not any(finding.startswith("docs/guides/setup-guide.md:1:") for finding in findings)
    assert any(finding.startswith("docs/guides/setup-guide.md:2: [PERSONAL_EMAIL]") for finding in findings)
    assert any(finding.startswith("other.md:1: [PERSONAL_HANDLE]") for finding in findings)


def test_all_20_skills_pass_validation():
    skills = sorted((REPO_ROOT / ".agents" / "skills").glob("*/SKILL.md"))
    assert len(skills) == 20, f"Expected 20 approved skills, found {len(skills)}"
    res = subprocess.run(
        [sys.executable, "scripts/validate_skill.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr


def test_subagent_personas_synced_without_drift():
    before = {
        p.relative_to(REPO_ROOT): p.read_bytes()
        for folder in (".claude/agents", ".claude/subagents", ".codex/agents", ".codex/subagents")
        for p in sorted((REPO_ROOT / folder).glob("*"))
        if p.is_file()
    }
    res = subprocess.run(
        [sys.executable, "scripts/sync_subagents.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, res.stdout + res.stderr
    after = {
        p.relative_to(REPO_ROOT): p.read_bytes()
        for folder in (".claude/agents", ".claude/subagents", ".codex/agents", ".codex/subagents")
        for p in sorted((REPO_ROOT / folder).glob("*"))
        if p.is_file()
    }
    assert before == after, "Generated persona adapters drifted from .agents/agents/"
