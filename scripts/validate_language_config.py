#!/usr/bin/env python3
"""
validate_language_config.py

Automated verification suite for the dual-language configuration architecture:
1. $DATA_REPO/data/lang_preferences.md exists and is valid.
2. scripts/hooks/ensure_lang_preferences.sh executes and self-heals missing/corrupted configs.
3. .agents/settings.json registers the ensure-lang-preferences hook.
4. AGENTS.md and relevant skills reference $DATA_REPO/data/lang_preferences.md.
"""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HOME_ROOT = Path(__file__).resolve().parent.parent
if str(HOME_ROOT) not in sys.path:
    sys.path.insert(0, str(HOME_ROOT))

from scripts.lib.workspace_paths import resolve_data_repo

HOOK_SCRIPT = HOME_ROOT / "scripts" / "hooks" / "ensure_lang_preferences.sh"
SETTINGS_FILE = HOME_ROOT / ".agents" / "settings.json"


def test_lang_preferences_file(lang_pref_file: Path) -> None:
    print(f"[1/5] Testing {lang_pref_file}...")
    assert lang_pref_file.is_file(), f"Missing {lang_pref_file}"
    content = lang_pref_file.read_text(encoding="utf-8")

    report_match = re.search(r"[-*]\s*\*\*Preferred Report Language\*\*:\s*(.+)", content)
    conv_match = re.search(r"[-*]\s*\*\*Preferred Conversation Language\*\*:\s*(.+)", content)

    assert report_match and report_match.group(1).strip(), "Preferred Report Language missing or empty"
    assert conv_match and conv_match.group(1).strip(), "Preferred Conversation Language missing or empty"
    print(f"  ✅ Report Language: {report_match.group(1).strip()}")
    print(f"  ✅ Conversation Language: {conv_match.group(1).strip()}")


def test_hook_auto_healing(data_repo: Path, lang_pref_file: Path) -> None:
    print("[2/5] Testing lifecycle hook self-healing...")
    assert HOOK_SCRIPT.is_file(), f"Missing {HOOK_SCRIPT}"
    assert os.access(HOOK_SCRIPT, os.X_OK), f"{HOOK_SCRIPT} is not executable"

    backup_file = lang_pref_file.with_suffix(".md.bak")
    shutil.copy2(lang_pref_file, backup_file)
    env = os.environ.copy()
    env["KNOWLEDGE_LOOP_DATA_REPO"] = str(data_repo)

    try:
        lang_pref_file.unlink()
        assert not lang_pref_file.exists()

        res = subprocess.run([str(HOOK_SCRIPT)], capture_output=True, text=True, cwd=HOME_ROOT, env=env)
        assert res.returncode == 0, f"Hook failed with {res.stderr}"
        assert lang_pref_file.is_file(), "Hook failed to recreate missing lang_preferences.md"

        recreated = lang_pref_file.read_text(encoding="utf-8")
        assert "Preferred Report Language" in recreated
        assert "Preferred Conversation Language" in recreated
        print("  ✅ Auto-healed missing lang_preferences.md successfully.")

        lang_pref_file.write_text(
            "# Language Preferences\n\n- **Preferred Conversation Language**: English\n",
            encoding="utf-8",
        )
        res = subprocess.run([str(HOOK_SCRIPT)], capture_output=True, text=True, cwd=HOME_ROOT, env=env)
        assert res.returncode == 0, f"Hook failed with {res.stderr}"

        repaired = lang_pref_file.read_text(encoding="utf-8")
        assert "Preferred Report Language" in repaired
        assert "Preferred Conversation Language" in repaired
        print("  ✅ Repaired missing keys successfully.")
    finally:
        if backup_file.exists():
            shutil.move(str(backup_file), str(lang_pref_file))


def test_hook_registered_in_settings() -> None:
    print("[3/5] Testing .agents/settings.json hook registration...")
    assert SETTINGS_FILE.is_file(), f"Missing {SETTINGS_FILE}"
    settings_content = SETTINGS_FILE.read_text(encoding="utf-8")
    assert "ensure-lang-preferences" in settings_content
    assert "ensure_lang_preferences.sh" in settings_content
    print("  ✅ Hook registered in settings.json.")


def test_agents_md_policy() -> None:
    print("[4/5] Testing AGENTS.md policy pointer...")
    content = (HOME_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "data/lang_preferences.md" in content
    assert "Preferred Conversation Language" in content
    assert "Preferred Report Language" in content
    print("  ✅ AGENTS.md contains policy pointer to $DATA_REPO/data/lang_preferences.md.")


def test_skills_reference_lang_preferences() -> None:
    print("[5/5] Testing skill files reference data/lang_preferences.md...")
    targets = [
        (HOME_ROOT / ".agents/skills/content-summary/references/summarise.md", "summarise.md"),
        (HOME_ROOT / ".agents/skills/daily-distiller/SKILL.md", "daily-distiller/SKILL.md"),
    ]
    for path, label in targets:
        assert path.is_file(), f"Missing {path}"
        content = path.read_text(encoding="utf-8")
        assert "data/lang_preferences.md" in content, f"{label} missing data/lang_preferences.md"
        assert "Preferred Report Language" in content, f"{label} missing Preferred Report Language"
        print(f"  ✅ {label} correctly references data/lang_preferences.md.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify dual-language configuration architecture.")
    parser.add_argument("--data-repo", default=None, help="Explicit Data Repo directory")
    args = parser.parse_args()

    print("=== Running Language Configuration Verification Suite ===")
    try:
        data_repo = resolve_data_repo(args.data_repo, home_root=HOME_ROOT, require_exists=True)
        lang_pref_file = data_repo / "data" / "lang_preferences.md"
        test_lang_preferences_file(lang_pref_file)
        test_hook_auto_healing(data_repo, lang_pref_file)
        test_hook_registered_in_settings()
        test_agents_md_policy()
        test_skills_reference_lang_preferences()
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! Dual-language architecture is fully verified.")
        return 0
    except (AssertionError, FileNotFoundError) as exc:
        print(f"\n❌ VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
