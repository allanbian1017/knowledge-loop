import json
from pathlib import Path
import subprocess
import sys

import report_store
from check_setup import check
from report_store import ReportStore
from workspace_paths import load_workspace


def test_daily_publication_feedback_boundary_and_synthesis(workspace):
    store = ReportStore(workspace)
    claim = store.claim_run('offline-fixture')
    day = claim['date']
    for kind in ['Newsletter', 'Website', 'Threads', 'YouTube']:
        receipt = store.publish(kind, f'{kind}-fixture', day, f'{kind}_{day.replace("-", "_")}/fixture.md',
                                f'# {kind} fixture\n\n## Core Thesis\nSynthetic evidence.\n'.encode(),
                                suggestion={'title': 'Synthetic evidence', 'source_url': 'https://example.invalid/source',
                                            'category': 'Technical', 'suggestion': '[TEST_FIXTURE] Verify a boundary'})
        assert receipt['suggestion_staged'] and not receipt['acknowledged']
        store.mark_acknowledged(receipt['key'])
        store.merge(receipt['key'], 'pending', f'### {day} | {kind} | Synthetic\n- [Report]({receipt["report_link"]})')
    assert len(store.today_reports(day)) == 4
    store.publish('Distillation', day, day, f'distillations/Knowledge_Distillation_{day.replace("-", "_")}.md',
                  b'# Knowledge Distillation\n\n## Executive Summary\nConnected fixture findings.\n')
    store.claim_run(claim['run_id'], finish=True)
    assert (workspace.personal_data / 'suggestions_pending.md').read_text().count('### ') == 4
    assert not (workspace.personal_data / 'suggestions_reviewed.md').exists()
    assert list(workspace.home.iterdir()) == []


def test_two_users_do_not_share_personal_preferences(workspace):
    original = workspace.languages()
    personal = workspace.config.parent / 'another profile'
    personal.mkdir()
    (personal / 'lang_preferences.md').write_text('# Language\n- **Preferred Report Language**: Français\n- **Preferred Conversation Language**: English\n')
    settings = json.loads(workspace.config.read_text())
    settings.update(personal_data=str(personal), timezone='UTC')
    another = workspace.config.parent / 'another config.json'
    another.write_text(json.dumps(settings))
    second = load_workspace(another, home_root=workspace.home)
    assert second.languages()['Preferred Report Language'] == 'Français'
    assert workspace.languages() == original


def test_language_validator_never_repairs_configuration(workspace):
    language = workspace.personal_data / 'lang_preferences.md'
    language.write_text('# Incomplete profile\n')
    script = Path(report_store.__file__).with_name('validate_language_config.py')
    result = subprocess.run([sys.executable, '-B', str(script), '--config', str(workspace.config)], capture_output=True, text=True)
    assert result.returncode == 2
    assert language.read_text() == '# Incomplete profile\n'


def test_setup_reports_missing_configuration_without_writing(monkeypatch):
    monkeypatch.delenv('KNOWLEDGE_LOOP_CONFIG', raising=False)
    result = check('daily-distiller')
    assert not result['ok']
    assert any('KNOWLEDGE_LOOP_CONFIG' in error for error in result['errors'])
