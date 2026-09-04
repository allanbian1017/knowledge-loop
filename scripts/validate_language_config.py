#!/usr/bin/env python3
"""
validate_language_config.py

Automated test suite verifying the dual-language configuration architecture:
1. data/lang_preferences.md exists and is valid.
2. scripts/hooks/ensure_lang_preferences.sh executes and self-heals missing/corrupted configs.
3. .agents/settings.json registers the ensure-lang-preferences hook.
4. AGENTS.md and relevant skills reference data/lang_preferences.md.
"""

import os
import re
import shutil
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LANG_PREF_FILE = os.path.join(REPO_ROOT, "data", "lang_preferences.md")
HOOK_SCRIPT = os.path.join(REPO_ROOT, "scripts", "hooks", "ensure_lang_preferences.sh")
SETTINGS_FILE = os.path.join(REPO_ROOT, ".agents", "settings.json")


def test_lang_preferences_file():
    print("[1/5] Testing data/lang_preferences.md...")
    assert os.path.exists(LANG_PREF_FILE), f"Missing {LANG_PREF_FILE}"
    with open(LANG_PREF_FILE, "r", encoding="utf-8") as fp:
        content = fp.read()

    report_match = re.search(r"[-*]\s*\*\*Preferred Report Language\*\*:\s*(.+)", content)
    conv_match = re.search(r"[-*]\s*\*\*Preferred Conversation Language\*\*:\s*(.+)", content)

    assert report_match and report_match.group(1).strip(), "Preferred Report Language missing or empty"
    assert conv_match and conv_match.group(1).strip(), "Preferred Conversation Language missing or empty"
    print(f"  ✅ Report Language: {report_match.group(1).strip()}")
    print(f"  ✅ Conversation Language: {conv_match.group(1).strip()}")


def test_hook_auto_healing():
    print("[2/5] Testing lifecycle hook self-healing...")
    assert os.path.exists(HOOK_SCRIPT), f"Missing {HOOK_SCRIPT}"
    assert os.access(HOOK_SCRIPT, os.X_OK), f"{HOOK_SCRIPT} is not executable"

    # Backup existing file
    backup_file = LANG_PREF_FILE + ".bak"
    shutil.copy2(LANG_PREF_FILE, backup_file)

    try:
        # Case A: File deleted -> Hook recreates it
        os.remove(LANG_PREF_FILE)
        assert not os.path.exists(LANG_PREF_FILE)

        res = subprocess.run([HOOK_SCRIPT], capture_output=True, text=True, cwd=REPO_ROOT)
        assert res.returncode == 0, f"Hook failed with {res.stderr}"
        assert os.path.exists(LANG_PREF_FILE), "Hook failed to recreate missing lang_preferences.md"

        with open(LANG_PREF_FILE, "r", encoding="utf-8") as fp:
            recreated = fp.read()
        assert "Preferred Report Language" in recreated
        assert "Preferred Conversation Language" in recreated
        print("  ✅ Auto-healed missing lang_preferences.md successfully.")

        # Case B: Missing key -> Hook repairs it
        with open(LANG_PREF_FILE, "w", encoding="utf-8") as fp:
            fp.write("# Language Preferences\n\n- **Preferred Conversation Language**: English\n")

        res = subprocess.run([HOOK_SCRIPT], capture_output=True, text=True, cwd=REPO_ROOT)
        assert res.returncode == 0, f"Hook failed with {res.stderr}"

        with open(LANG_PREF_FILE, "r", encoding="utf-8") as fp:
            repaired = fp.read()
        assert "Preferred Report Language" in repaired
        assert "Preferred Conversation Language" in repaired
        print("  ✅ Repaired missing keys successfully.")

    finally:
        # Restore backup
        if os.path.exists(backup_file):
            shutil.move(backup_file, LANG_PREF_FILE)


def test_hook_registered_in_settings():
    print("[3/5] Testing .agents/settings.json hook registration...")
    assert os.path.exists(SETTINGS_FILE), f"Missing {SETTINGS_FILE}"
    with open(SETTINGS_FILE, "r", encoding="utf-8") as fp:
        settings_content = fp.read()

    assert "ensure-lang-preferences" in settings_content, "ensure-lang-preferences not registered in settings.json"
    assert "ensure_lang_preferences.sh" in settings_content, "ensure_lang_preferences.sh command missing in settings.json"
    print("  ✅ Hook registered in settings.json.")


def test_agents_md_policy():
    print("[4/5] Testing AGENTS.md policy pointer...")
    agents_file = os.path.join(REPO_ROOT, "AGENTS.md")
    with open(agents_file, "r", encoding="utf-8") as fp:
        content = fp.read()

    assert "data/lang_preferences.md" in content, "AGENTS.md does not reference data/lang_preferences.md"
    assert "Preferred Conversation Language" in content, "AGENTS.md missing Preferred Conversation Language rule"
    assert "Preferred Report Language" in content, "AGENTS.md missing Preferred Report Language rule"
    print("  ✅ AGENTS.md contains policy pointer to data/lang_preferences.md.")


def test_skills_reference_lang_preferences():
    print("[5/5] Testing skill files reference data/lang_preferences.md...")
    targets = [
        (os.path.join(REPO_ROOT, ".agents", "skills", "content-summary", "references", "summarise.md"), "summarise.md"),
        (os.path.join(REPO_ROOT, ".agents", "skills", "daily-distiller", "SKILL.md"), "daily-distiller/SKILL.md"),
        (os.path.join(REPO_ROOT, ".agents", "skills", "study-github-repo", "SKILL.md"), "study-github-repo/SKILL.md"),
    ]

    for path, label in targets:
        assert os.path.exists(path), f"Missing {path}"
        with open(path, "r", encoding="utf-8") as fp:
            content = fp.read()
        assert "data/lang_preferences.md" in content, f"{label} does not reference data/lang_preferences.md"
        assert "Preferred Report Language" in content, f"{label} does not reference Preferred Report Language"
        print(f"  ✅ {label} correctly references data/lang_preferences.md.")


def main():
    print("=== Running Language Configuration Verification Suite ===")
    try:
        test_lang_preferences_file()
        test_hook_auto_healing()
        test_hook_registered_in_settings()
        test_agents_md_policy()
        test_skills_reference_lang_preferences()
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! Dual-language architecture is fully verified.")
        return 0
    except AssertionError as e:
        print(f"\n❌ VALIDATION FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
