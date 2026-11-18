import json
import os
from pathlib import Path
import re
import subprocess
import shutil
import sys

from check_setup import check
from validate_public import public_files, scan


ROOT = Path(__file__).resolve().parents[1]


def test_public_scan_finds_realistic_identifiers_without_echoing_values(tmp_path):
    machine_path = '/' + 'Users' + '/' + 'sample-account' + '/private'
    (tmp_path / 'unsafe.md').write_text(machine_path + '\n' + 'sample' + '@' + 'mail.example.com\n')
    issues = scan(tmp_path)
    assert {i['reason'] for i in issues} == {'personal machine path', 'non-synthetic email address'}
    assert machine_path not in json.dumps(issues)
    unicode_path = '/' + 'Users' + '/' + '用戶' + '/private'
    (tmp_path / 'unsafe.md').write_text(unicode_path)
    assert scan(tmp_path)[0]['reason'] == 'personal machine path'
    (tmp_path / 'unsafe.md').write_text('$HOME/<EXTERNAL_DIRECTORY>\nuser@example.invalid\n')
    assert scan(tmp_path) == []


def test_public_tree_is_clean():
    assert scan(ROOT) == []


def test_excluded_skills_are_not_bundled():
    excluded = {'hiring-panel', 'log-task-evidence', 'sync-diary', 'decision-sparring', 'writing-style-technical-english'}
    names = {p.parent.name for p in (ROOT / '.agents/skills').glob('*/SKILL.md')}
    assert not names & excluded
    assert {'architecture-decision-records', 'agent-rules-reviewer', 'skill-context-refactor', 'evolution-log'} <= names


def test_bundle_does_not_need_global_skills():
    for path in (ROOT / '.agents/skills').rglob('*.md'):
        if path.name in {'README.md', 'LICENSE'}:
            continue
        prose = re.sub(r'(?ms)^```[^\n]*\n.*?^```[^\n]*(?:\n|$)', '', path.read_text())
        for target in re.findall(r'\]\(([^)\s]+)\)', prose):
            if target.startswith(('http:', 'https:', '#', 'mailto:')) or any(token in target for token in ['<', '>', '{', '}', '[', ']']):
                continue
            target = target.split('#')[0]
            if target and ('SKILL.md' in target or target.endswith(('.md', '.json', '.py', '.sh'))):
                assert (path.parent / target).is_file(), f'Broken resource: {path.relative_to(ROOT)} -> {target}'


def test_offline_setup_does_not_require_accounts_or_user_directories(monkeypatch, tmp_path):
    monkeypatch.delenv('KNOWLEDGE_LOOP_CONFIG', raising=False)
    monkeypatch.setenv('HOME', str(tmp_path / 'empty-user'))
    result = check(offline=True)
    assert result['ok'], result
    assert not (tmp_path / 'empty-user').exists()


def test_adapter_check_does_not_modify_files():
    before = {str(p): p.read_bytes() for name in ['.codex', '.claude'] for p in (ROOT / name).rglob('*') if p.is_file()}
    result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/sync_subagents.py'), '--check'], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert all(Path(name).read_bytes() == data for name, data in before.items())


def test_relocated_clone_runs_without_original_checkout_or_global_skills(tmp_path):
    clone = tmp_path / 'unrelated clone 資料 with spaces'
    clone.mkdir()
    for path in public_files(ROOT):
        if not path.is_file():
            continue
        destination = clone / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    environment = {key: value for key, value in os.environ.items() if key not in {'KNOWLEDGE_LOOP_CONFIG', 'PYTHONPATH'}}
    environment.update(HOME=str(tmp_path / 'empty-profile'), PYTHONDONTWRITEBYTECODE='1')
    for script, flags in [('check_setup.py', ['--offline']), ('validate_skill.py', []), ('sync_subagents.py', ['--check'])]:
        result = subprocess.run([sys.executable, '-B', str(clone / 'scripts' / script), *flags], cwd=tmp_path, env=environment, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / 'empty-profile').exists()
