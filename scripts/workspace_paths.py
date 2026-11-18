#!/usr/bin/env python3
"""Resolve a Home Repo's external configuration without changing user state."""

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


HOME_ROOT = Path(__file__).resolve().parents[1]


class SetupError(ValueError):
    """Configuration or prerequisites need attention before execution."""


def outside_home(path, home):
    resolved = path.resolve()
    if resolved == home or home in resolved.parents:
        raise SetupError('Personal configuration and runtime data must be outside the Home Repo')
    return resolved


def git_output(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
    if result.returncode:
        raise SetupError('Cannot inspect the configured report repository; check Git access')
    return result.stdout.strip()


def normalize_origin(value):
    value = re.sub(r'^git@([^:]+):', r'https://\1/', value.strip())
    value = re.sub(r'^ssh://git@', 'https://', value)
    return value.rstrip('/').removesuffix('.git')


@dataclass(frozen=True)
class Workspace:
    home: Path
    config: Path
    report_repository: Path
    personal_data: Path
    settings: dict

    @property
    def reports(self):
        return self.report_repository / 'reports'

    def report_date(self):
        timezone = self.settings.get('timezone')
        return datetime.now(ZoneInfo(timezone) if timezone else None).date().isoformat()

    def languages(self):
        path = self.personal_data / 'lang_preferences.md'
        try:
            content = path.read_text(encoding='utf-8')
        except OSError as exc:
            raise SetupError('Create lang_preferences.md in the configured personal-data directory') from exc
        languages = {}
        for key in ('Preferred Report Language', 'Preferred Conversation Language'):
            match = re.search(r'\*\*' + re.escape(key) + r'\*\*:\s*([^\r\n]+)', content)
            if not match or not match.group(1).strip():
                raise SetupError(f'Personal language configuration is missing {key}')
            languages[key] = match.group(1).strip()
        return languages

    def as_dict(self):
        return {
            'home_root': str(self.home),
            'report_repository': str(self.report_repository),
            'report_root': str(self.reports),
            'scratch_root': str(self.report_repository / '.tmp' / 'knowledge-loop'),
            'personal_data_root': str(self.personal_data),
            'report_date': self.report_date(),
            'task_list': self.settings.get('task_list', 'Delegate'),
            'newsletter_query': self.settings.get('newsletter_query', 'label:newsletter is:unread'),
        }


def load_workspace(config=None, *, home_root=None, check_repository=True):
    home = Path(home_root or HOME_ROOT).resolve()
    selected = config or os.environ.get('KNOWLEDGE_LOOP_CONFIG')
    if not selected:
        raise SetupError('Set KNOWLEDGE_LOOP_CONFIG to an external JSON file; see docs/setup.md')
    path = outside_home(Path(selected).expanduser(), home)
    try:
        settings = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise SetupError('Cannot read external configuration as JSON; see docs/setup.md') from exc
    if not isinstance(settings, dict):
        raise SetupError('External configuration must be a JSON object')
    roots = {}
    for name in ('report_repository', 'personal_data'):
        value = settings.get(name)
        if not isinstance(value, str) or not value.strip() or '<' in value or '>' in value:
            raise SetupError(f'Configure {name} with a real directory outside the Home Repo')
        candidate = Path(value).expanduser()
        resolved = outside_home(candidate if candidate.is_absolute() else path.parent / candidate, home)
        if resolved in home.parents:
            raise SetupError(f'{name} must not contain the Home Repo')
        if not resolved.is_dir():
            raise SetupError(f'The configured {name} directory is missing')
        roots[name] = resolved
    if roots['personal_data'] == roots['report_repository']:
        raise SetupError('personal_data must be a separate directory, such as the report repository data directory')
    if 'expected_origin' in settings and not isinstance(settings['expected_origin'], str):
        raise SetupError('expected_origin must be a string when configured')
    for name in ('task_list', 'newsletter_query'):
        if name in settings and (not isinstance(settings[name], str) or not settings[name].strip()):
            raise SetupError(f'{name} must be a nonempty string')
    timezone = settings.get('timezone')
    if timezone is not None:
        try:
            ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, TypeError, ValueError) as exc:
            raise SetupError('timezone must be a valid IANA timezone') from exc
    if check_repository:
        repo = roots['report_repository']
        if Path(git_output(repo, 'rev-parse', '--show-toplevel')).resolve() != repo:
            raise SetupError('report_repository must be its own Git root')
        expected = settings.get('expected_origin')
        if expected and normalize_origin(git_output(repo, 'remote', 'get-url', 'origin')) != normalize_origin(expected):
            raise SetupError('Report repository origin differs from expected_origin')
    return Workspace(home, path, roots['report_repository'], roots['personal_data'], settings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--path', choices=['home_root', 'report_repository', 'report_root', 'scratch_root', 'personal_data_root', 'report_date'])
    parser.add_argument('--languages', action='store_true')
    args = parser.parse_args()
    try:
        workspace = load_workspace(args.config)
        values = workspace.languages() if args.languages else workspace.as_dict()
        print(values[args.path] if args.path else json.dumps(values, ensure_ascii=False, indent=2))
    except (SetupError, OSError) as exc:
        parser.exit(2, f'Setup required: {exc}\n')


if __name__ == '__main__':
    main()
