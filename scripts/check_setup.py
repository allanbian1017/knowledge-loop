#!/usr/bin/env python3
"""Read-only checks for local resources and selected skill prerequisites."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

from workspace_paths import HOME_ROOT, SetupError, load_workspace


TOOLS = {
    'daily-workflow': ['gws', 'agent-browser', 'yt2doc'],
    'ingest-newsletter': ['gws'], 'ingest-website': ['gws'],
    'ingest-threads': ['gws', 'agent-browser'], 'ingest-youtube': ['gws', 'yt2doc'],
    'fetch-threads-post': ['agent-browser'], 'agent-browser': ['agent-browser'],
    'gws-gmail': ['gws'], 'gws-tasks': ['gws'], 'gws-shared': ['gws'],
    'yt2doc': ['yt2doc'], 'study-github-repo': ['gh'],
}
PERSONAL_SKILLS = {
    'daily-workflow', 'ingest-newsletter', 'ingest-website', 'ingest-threads',
    'ingest-youtube', 'daily-distiller', 'review-newsletter-subscriptions',
    'rubric-grader', 'review-suggestions', 'content-summary',
}
REPORT_SKILLS = PERSONAL_SKILLS | {'yt2doc', 'web-to-markdown', 'content-cleaner', 'study-github-repo'}


def check_resources(home=HOME_ROOT):
    errors = []
    for path in (home / '.agents/skills').glob('*/SKILL.md'):
        if not (path.parent / 'README.md').is_file():
            errors.append(f'Missing skill README: {path.parent.name}')
    for path in (home / '.agents/agents').glob('*.md'):
        for directory, suffix in [('.codex/agents', '.toml'), ('.claude/agents', '.md')]:
            if not (home / directory / (path.stem + suffix)).is_file():
                errors.append(f'Missing generated adapter for {path.stem}')
    if importlib.util.find_spec('yaml') is None:
        errors.append('Install requirements.txt in the active virtual environment')
    return errors


def check(skill=None, config=None, offline=False):
    errors = check_resources()
    notes = []
    if sys.version_info < (3, 10):
        errors.append('Python 3.10 or later is required; use Python 3.10–3.12 for yt2doc')
    if offline:
        notes.append('Offline resources only; tools, configuration, host capabilities and authentication are not verified')
        return {'ok': not errors, 'errors': errors, 'notes': notes}
    for tool in sorted(set(['git', *TOOLS.get(skill, [])])):
        if shutil.which(tool) is None:
            errors.append(f'Missing {tool}; follow docs/setup.md')
    if skill in REPORT_SKILLS:
        try:
            workspace = load_workspace(config)
            if skill in PERSONAL_SKILLS:
                workspace.languages()
            if skill in {'daily-workflow', 'content-summary', 'ingest-newsletter', 'ingest-website', 'ingest-threads', 'ingest-youtube', 'rubric-grader'}:
                goals = workspace.personal_data / 'goals.md'
                if not goals.is_file() or not any(line.startswith('- ') and 'Add your goals here' not in line for line in goals.read_text().splitlines()):
                    errors.append('Add a real goal to personal goals.md before personalized analysis')
            if not all(os.access(p, os.W_OK | os.X_OK) for p in [workspace.report_repository, workspace.personal_data]):
                errors.append('Configured output directories are not writable in this process')
        except (SetupError, OSError) as exc:
            errors.append(str(exc))
    if skill == 'daily-workflow':
        notes.append('Host must support fresh worker contexts; verify all six personas before live dispatch')
    if TOOLS.get(skill):
        notes.append('Executable presence does not verify versions, authentication, browser sessions, models or network access')
    return {'ok': not errors, 'errors': errors, 'notes': notes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--skill', choices=sorted(p.parent.name for p in (HOME_ROOT / '.agents/skills').glob('*/SKILL.md')))
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    if not args.offline and not args.skill:
        parser.error('Choose --offline or --skill NAME')
    result = check(args.skill, args.config, args.offline)
    print(json.dumps(result, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
