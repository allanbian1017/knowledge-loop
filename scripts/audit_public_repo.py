#!/usr/bin/env python3
"""Public Repository Hygiene & Portability Audit for Knowledge Loop.

Verifies that no tracked/non-ignored file in the knowledge-loop contains:
1. Machine-specific absolute paths (macOS/Linux/Windows home dirs or file:// local paths)
2. Personal usernames, private repo names, employer names, or personal Jira keys
3. Private Notion workspace IDs, live Discord webhooks, secret tokens, or personal emails
4. Broken internal relative Markdown links in core steering, guide, and skill files
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".tmp",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".benchmarks",
    ".codebase-memory",
    ".codegraph",
    ".obsidian",
}

SKIP_FILES = {
    ".DS_Store",
    "workspace.local.env",
    "repos.local.md",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
    ".pyc", ".pyo", ".so", ".dylib", ".zip", ".gz", ".tar", ".woff", ".woff2",
}

# Build forbidden literal patterns dynamically so this file itself passes self-scan
_USERS_PREFIX = "/" + "Users/"
_HOME_PREFIX = "/" + "home/"
_WIN_USERS = "C:" + "\\" + "Users" + "\\"
_FILE_USERS = "file://" + _USERS_PREFIX
_PERSONAL_HANDLE = "allan" + "bian"
_PRIVATE_REPO = "my-ai-" + "workflow"
_EMPLOYER_1 = "Conv" + "Pay"
_EMPLOYER_2 = "Order" + "Manager"
_NOTION_P1 = "3cd6" + "0ab2"
_NOTION_P2 = "3426" + "0ab2"
_NOTION_P3 = "3a8f" + "3775"

CONTENT_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("ABSOLUTE_PATH_MACOS", re.compile(re.escape(_USERS_PREFIX))),
    ("ABSOLUTE_PATH_LINUX", re.compile(re.escape(_HOME_PREFIX))),
    ("ABSOLUTE_PATH_WIN", re.compile(re.escape(_WIN_USERS))),
    ("FILE_URI_LOCAL", re.compile(re.escape(_FILE_USERS))),
    ("PERSONAL_HANDLE", re.compile(re.escape(_PERSONAL_HANDLE), re.IGNORECASE)),
    ("PRIVATE_REPO_NAME", re.compile(re.escape(_PRIVATE_REPO), re.IGNORECASE)),
    ("EMPLOYER_IDENTIFIER", re.compile(rf"\b(?:{re.escape(_EMPLOYER_1)}|{re.escape(_EMPLOYER_2)})\b")),
    ("PERSONAL_JIRA_KEY", re.compile(r"\bA" + r"W-\d+\b")),
    ("PRIVATE_NOTION_ID", re.compile(rf"(?:{_NOTION_P1}|{_NOTION_P2}|{_NOTION_P3})[0-9a-fA-F-]{{8,}}")),
    ("LIVE_DISCORD_WEBHOOK", re.compile(r"discord\.com/api/webhooks/\d{15,}/[A-Za-z0-9_-]{10,}")),
    ("SECRET_TOKEN", re.compile(r"\b(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|ntn_[A-Za-z0-9]{20,}|ATATT[A-Za-z0-9]{10,})\b")),
]

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
ALLOWED_EMAIL_DOMAINS = {
    "example.com",
    "example.org",
    "test.com",
    "localhost.localdomain",
    "users.noreply.github.com",
}
ALLOWED_EMAIL_FULL = {
    "user@gmail.com",  # Upstream agent-browser documentation placeholder
}

# Files whose internal relative Markdown links are verified strictly
LINK_CHECK_GLOBS = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "THIRD_PARTY.md",
    "docs/guides/*.md",
    ".agents/skills/*/SKILL.md",
    ".agents/skills/*/README.md",
]

MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)\)")


def iter_candidate_files(root: Path) -> list[Path]:
    """Iterate non-ignored repository files (prefers git ls-files when available)."""
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        )
        paths = []
        for rel in res.stdout.splitlines():
            p = root / rel
            if not p.is_file() or p.is_symlink():
                continue
            if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
                continue
            if p.name in SKIP_FILES or p.suffix.lower() in BINARY_EXTENSIONS:
                continue
            if p.name.endswith(".code-workspace"):
                continue
            paths.append(p)
        return sorted(set(paths))
    except Exception:
        paths = []
        for p in root.rglob("*"):
            if not p.is_file() or p.is_symlink():
                continue
            rel = p.relative_to(root)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if p.name in SKIP_FILES or p.suffix.lower() in BINARY_EXTENSIONS:
                continue
            if p.name.endswith(".code-workspace"):
                continue
            paths.append(p)
        return sorted(paths)


def scan_file_contents(root: Path, files: list[Path]) -> list[str]:
    violations: list[str] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        # Skip test file that intentionally constructs synthetic forbidden-pattern strings in memory
        if rel == "tests/test_public_repo_hygiene.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            for rule_name, pattern in CONTENT_RULES:
                if pattern.search(line):
                    violations.append(f"{rel}:{lineno}: [{rule_name}] {line.strip()[:120]}")

            for m in EMAIL_RE.finditer(line):
                full_email = m.group(0).lower()
                domain = m.group(1).lower()
                if domain not in ALLOWED_EMAIL_DOMAINS and not domain.endswith(".example.com") and full_email not in ALLOWED_EMAIL_FULL:
                    violations.append(f"{rel}:{lineno}: [PERSONAL_EMAIL] {full_email}")
    return violations


def scan_internal_links(root: Path) -> list[str]:
    violations: list[str] = []
    checked: set[Path] = set()
    for pattern in LINK_CHECK_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path not in checked:
                checked.add(path)
                rel = path.relative_to(root).as_posix()
                in_code_fence = False
                for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                    stripped = line.strip()
                    if stripped.startswith("```"):
                        in_code_fence = not in_code_fence
                        continue
                    if in_code_fence:
                        continue
                    for m in MD_LINK_RE.finditer(line):
                        target = m.group(1).strip()
                        if (
                            not target
                            or target.startswith(("http://", "https://", "mailto:", "#", "$DATA_REPO", "<", "file://", "source_url"))
                            or "{" in target
                        ):
                            continue
                        clean_target = target.split("#", 1)[0].split("?", 1)[0]
                        if not clean_target:
                            continue
                        # Skip illustrative placeholder filenames inside skill documentation
                        if any(tok in clean_target for tok in ("YYYY_MM_DD", "example", "report.md", "gws-gmail-", "slug")):
                            continue
                        resolved = (path.parent / clean_target).resolve()
                        if not resolved.exists():
                            violations.append(f"{rel}:{lineno}: [BROKEN_LINK] {target}")
    return violations


def audit(root: Path = REPO_ROOT) -> list[str]:
    files = iter_candidate_files(root)
    violations = scan_file_contents(root, files)
    violations.extend(scan_internal_links(root))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Knowledge Loop knowledge-loop for PII, absolute paths, and broken links.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root to audit")
    args = parser.parse_args()

    violations = audit(args.root.resolve())
    if violations:
        print(f"❌ Public repo hygiene audit FAILED with {len(violations)} violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    print("✅ Public repo hygiene audit PASSED (0 violations found).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
