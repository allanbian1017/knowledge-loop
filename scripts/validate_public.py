#!/usr/bin/env python3
"""Check publishable files for machine paths, account defaults and private IDs."""

import argparse
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
RULES = {
    'personal machine path': re.compile(r'(?:file://)?/(?:Users|home)/(?![<$\{])[^\s<>\]\)"\x27`]+|[A-Za-z]:\\Users\\[^\s<>]+'),
    'private workspace identifier': re.compile(r'collection://[0-9a-fA-F-]{32,36}|https?://(?:app\.)?notion\.(?:com|so)/(?:p/)?[0-9a-fA-F-]{32,36}'),
    'personal tenant': re.compile(r'https?://(?!example\.)[\w.-]+\.atlassian\.net'),
    'credential-shaped value': re.compile(r'\b(?:ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{30,})\b'),
}
EMAIL = re.compile(r'(?<![\w.-])[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def public_files(root):
    top = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if top.returncode == 0 and Path(top.stdout.strip()).resolve() == root.resolve():
        result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], capture_output=True, check=True)
        return sorted({root / name for name in result.stdout.decode().split('\0') if name})
    return sorted(p for p in root.rglob('*') if p.is_file() and not {'.git', '.tmp', '.venv', '__pycache__', 'node_modules'} & set(p.relative_to(root).parts))


def scan(root=ROOT):
    issues = []
    for path in public_files(root):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if path.suffix in {'.pyc', '.pyo'}:
            issues.append({'file': relative, 'reason': 'compiled cache must not be published'})
            continue
        if path.name in {'LICENSE', 'NOTICE'}:
            continue
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except UnicodeError:
            issues.append({'file': relative, 'reason': 'binary asset needs an explicit publication review'})
            continue
        for number, line in enumerate(lines, 1):
            reasons = [name for name, pattern in RULES.items() if pattern.search(line)]
            if any(value != 'git@github.com' and not value.endswith(('.invalid', '.example')) for value in EMAIL.findall(line)):
                reasons.append('non-synthetic email address')
            for reason in reasons:
                issues.append({'file': relative, 'line': number, 'reason': reason})
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    issues = scan(args.root)
    print(json.dumps({'ok': not issues, 'issues': issues, 'limit': 'Pattern checks need a reviewed public diff; they cannot prove absence of all personal information.'}, indent=2))
    return 1 if issues else 0


if __name__ == '__main__':
    raise SystemExit(main())
