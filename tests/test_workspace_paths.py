import json
from pathlib import Path
import subprocess

import pytest

from workspace_paths import SetupError, load_workspace


def test_paths_are_config_relative_and_cwd_independent(workspace, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path.parent)
    resolved = load_workspace(workspace.config, home_root=workspace.home)
    assert resolved.personal_data == workspace.personal_data
    assert resolved.report_repository == workspace.report_repository
    assert resolved.reports == workspace.report_repository / 'reports'
    assert Path(resolved.as_dict()['scratch_root']).is_relative_to(workspace.report_repository)
    assert not resolved.reports.exists()


def test_configuration_is_required(monkeypatch):
    monkeypatch.delenv('KNOWLEDGE_LOOP_CONFIG', raising=False)
    with pytest.raises(SetupError, match='KNOWLEDGE_LOOP_CONFIG'):
        load_workspace()


def test_environment_and_explicit_configuration(workspace, monkeypatch, tmp_path):
    monkeypatch.setenv('KNOWLEDGE_LOOP_CONFIG', str(tmp_path / 'missing'))
    assert load_workspace(workspace.config, home_root=workspace.home).config == workspace.config
    monkeypatch.setenv('KNOWLEDGE_LOOP_CONFIG', str(workspace.config))
    assert load_workspace(home_root=workspace.home).personal_data == workspace.personal_data


@pytest.mark.parametrize('value', ['not json', '[]', '{}', '{"report_repository": "<REPLACE_ME>"}'])
def test_invalid_configuration_is_rejected(workspace, value):
    workspace.config.write_text(value)
    with pytest.raises(SetupError):
        load_workspace(workspace.config, home_root=workspace.home)


def test_private_configuration_cannot_be_in_home(workspace):
    local = workspace.home / 'config.json'
    local.write_bytes(workspace.config.read_bytes())
    with pytest.raises(SetupError, match='outside'):
        load_workspace(local, home_root=workspace.home)


def test_runtime_data_cannot_be_in_home(workspace):
    settings = json.loads(workspace.config.read_text())
    settings['personal_data'] = str(workspace.home)
    workspace.config.write_text(json.dumps(settings))
    with pytest.raises(SetupError, match='outside'):
        load_workspace(workspace.config, home_root=workspace.home)


def test_missing_and_nested_repository_are_rejected(workspace):
    settings = json.loads(workspace.config.read_text())
    settings['report_repository'] = 'missing'
    workspace.config.write_text(json.dumps(settings))
    with pytest.raises(SetupError, match='missing'):
        load_workspace(workspace.config, home_root=workspace.home)
    settings['report_repository'] = str(workspace.personal_data)
    alternate = workspace.config.parent / 'other personal data'
    alternate.mkdir()
    settings['personal_data'] = str(alternate)
    workspace.config.write_text(json.dumps(settings))
    with pytest.raises(SetupError, match='Git root'):
        load_workspace(workspace.config, home_root=workspace.home)


def test_optional_origin_pin(workspace):
    subprocess.run(['git', '-C', str(workspace.report_repository), 'remote', 'add', 'origin', 'https://example.invalid/team/reports.git'], check=True)
    settings = json.loads(workspace.config.read_text())
    settings['expected_origin'] = 'git@example.invalid:team/reports.git'
    workspace.config.write_text(json.dumps(settings))
    load_workspace(workspace.config, home_root=workspace.home)
    settings['expected_origin'] = 'https://example.invalid/another/repository.git'
    workspace.config.write_text(json.dumps(settings))
    with pytest.raises(SetupError, match='origin'):
        load_workspace(workspace.config, home_root=workspace.home)


def test_languages_are_personal_and_read_only(workspace):
    path = workspace.personal_data / 'lang_preferences.md'
    path.write_text('# Languages\n- **Preferred Report Language**: 日本語\n- **Preferred Conversation Language**: English\n')
    before = path.read_bytes()
    assert workspace.languages()['Preferred Report Language'] == '日本語'
    assert path.read_bytes() == before
    path.write_text('# Incomplete\n')
    with pytest.raises(SetupError, match='missing'):
        workspace.languages()
    assert path.read_text() == '# Incomplete\n'


def test_invalid_timezone_stops_setup(workspace):
    settings = json.loads(workspace.config.read_text())
    settings['timezone'] = 'Invalid/Timezone'
    workspace.config.write_text(json.dumps(settings))
    with pytest.raises(SetupError, match='timezone'):
        load_workspace(workspace.config, home_root=workspace.home)
