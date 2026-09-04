#!/usr/bin/env python3
"""
SKILL.md Validator

Validates YAML frontmatter syntax and required fields (`name`, `description`) for Agent Skills.
Usage:
    python3 scripts/validate_skill.py [path/to/SKILL.md ...]
    If no paths provided, validates all SKILL.md files under .agents/skills/
"""

import sys
import os
import glob
import yaml

def validate_skill_file(filepath):
    if not os.path.exists(filepath):
        print(f"❌ [ERROR] File not found: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f"❌ [ERROR] {filepath}: Missing YAML frontmatter enclosed by '---'")
        return False

    frontmatter_raw = parts[1]
    try:
        data = yaml.safe_load(frontmatter_raw)
    except Exception as e:
        print(f"❌ [ERROR] {filepath}: Invalid YAML in frontmatter:\n  {e}")
        return False

    if not isinstance(data, dict):
        print(f"❌ [ERROR] {filepath}: Frontmatter must be a YAML dictionary")
        return False

    name = data.get('name')
    if not name or not isinstance(name, str):
        print(f"❌ [ERROR] {filepath}: Missing or invalid 'name' field in frontmatter")
        return False

    description = data.get('description')
    if not description or not isinstance(description, str):
        print(f"❌ [ERROR] {filepath}: Missing or invalid 'description' field in frontmatter")
        return False

    print(f"✅ [OK] {filepath} (skill: {name})")
    return True

def main():
    if len(sys.argv) > 1:
        targets = sys.argv[1:]
    else:
        # Default: scan all SKILL.md files in .agents/skills/ and .gemini/config/skills/
        targets = glob.glob('.agents/skills/**/SKILL.md', recursive=True) + \
                  glob.glob('../.gemini/config/skills/**/SKILL.md', recursive=True)
        targets = sorted(list(set(targets)))

    if not targets:
        print("No SKILL.md files found to validate.")
        sys.exit(0)

    all_passed = True
    for path in targets:
        if not validate_skill_file(path):
            all_passed = False

    if not all_passed:
        print("\n❌ Validation failed for one or more skill files.")
        sys.exit(1)
    else:
        print(f"\n🎉 All {len(targets)} skill file(s) passed validation!")
        sys.exit(0)

if __name__ == '__main__':
    main()
