#!/usr/bin/env python3
"""
SKILL.md Validator

Validates YAML frontmatter syntax and required fields (`name`, `description`) for Agent Skills.
Usage:
    python3 scripts/validate_skill.py [path/to/SKILL.md ...]
    If no paths provided, validates all SKILL.md files under .agents/skills/
"""

import argparse
import glob
import os
import sys
import yaml


def validate_skill_file(filepath: str) -> bool:
    if not os.path.exists(filepath):
        print(f"❌ [ERROR] File not found: {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("---", 2)
    if len(parts) < 3:
        print(f"❌ [ERROR] {filepath}: Missing YAML frontmatter enclosed by '---'")
        return False

    try:
        data = yaml.safe_load(parts[1])
    except Exception as exc:
        print(f"❌ [ERROR] {filepath}: Invalid YAML in frontmatter:\n  {exc}")
        return False

    if not isinstance(data, dict):
        print(f"❌ [ERROR] {filepath}: Frontmatter must be a YAML dictionary")
        return False

    name = data.get("name")
    if not name or not isinstance(name, str):
        print(f"❌ [ERROR] {filepath}: Missing or invalid 'name' field in frontmatter")
        return False

    description = data.get("description")
    if not description or not isinstance(description, str):
        print(f"❌ [ERROR] {filepath}: Missing or invalid 'description' field in frontmatter")
        return False

    print(f"✅ [OK] {filepath} (skill: {name})")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate SKILL.md frontmatter.")
    parser.add_argument("paths", nargs="*", help="Explicit SKILL.md paths to validate")
    parser.add_argument(
        "--extra-dir",
        action="append",
        default=[],
        help="Optional extra directory to scan recursively for SKILL.md files",
    )
    args = parser.parse_args()

    if args.paths:
        targets = args.paths
    else:
        targets = glob.glob(".agents/skills/**/SKILL.md", recursive=True)
        for extra in args.extra_dir:
            targets.extend(glob.glob(os.path.join(extra, "**", "SKILL.md"), recursive=True))
        targets = sorted(set(targets))

    if not targets:
        print("No SKILL.md files found to validate.")
        sys.exit(0)

    all_passed = all(validate_skill_file(path) for path in targets)
    if not all_passed:
        print("\n❌ Validation failed for one or more skill files.")
        sys.exit(1)
    print(f"\n🎉 All {len(targets)} skill file(s) passed validation!")
    sys.exit(0)


if __name__ == "__main__":
    main()
