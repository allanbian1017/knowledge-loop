from pathlib import Path
import json
import os
import subprocess
import sys

import pytest

import report_store
from report_store import ReportStore, item_key


DAY = '2026-01-02'
REPORT = b'# Example learning\n\n## Core Thesis\nA useful finding.\n'
SUGGESTION = {'title': 'Example learning', 'source_url': 'https://example.invalid/article', 'category': 'Technical', 'suggestion': '[TEST_FIXTURE] Add one focused test'}


def publish(store, **kwargs):
    return store.publish('Website', 'source-1', DAY, 'Website_2026_01_02/article.md', REPORT, **kwargs)


def test_publish_replay_and_exact_source_identity(workspace):
    store = ReportStore(workspace)
    receipt = publish(store, suggestion=SUGGESTION)
    target = Path(receipt['absolute_path'])
    assert target.read_bytes() == REPORT
    original_mtime = target.stat().st_mtime_ns
    assert receipt['report_path'] == 'reports/Website_2026_01_02/article.md'
    assert receipt['suggestion_staged'] and not receipt['acknowledged']
    assert (workspace.personal_data / receipt['report_link']).resolve() == target
    repeated = publish(store, suggestion=SUGGESTION)
    assert repeated['key'] == receipt['key']
    assert target.stat().st_mtime_ns == original_mtime
    assert len(list((workspace.personal_data / 'suggestions_pending').glob('*.json'))) == 1
    assert item_key('Website', 'other-source', DAY) != receipt['key']
    assert store.mark_acknowledged(receipt['key'])['acknowledged']


def test_invalid_report_never_installs_an_output(workspace):
    store = ReportStore(workspace)
    with pytest.raises(ValueError):
        store.publish('Website', 'source', DAY, 'Website_2026_01_02/empty.md', b'')
    assert not workspace.reports.exists()


@pytest.mark.parametrize('path', ['../escape.md', '/absolute.md', '.metadata/fake.md', 'Website_2026_01_02/.hidden/file.md'])
def test_output_path_escape_is_rejected(workspace, path):
    with pytest.raises(ValueError):
        ReportStore(workspace).publish('Website', 'source', DAY, path, REPORT)


def test_symlinked_output_is_rejected(workspace, tmp_path):
    workspace.reports.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (workspace.reports / 'Website_2026_01_02').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='symlink'):
        publish(ReportStore(workspace))
    assert list(outside.iterdir()) == []


def test_filename_collision_preserves_unrelated_report(workspace):
    store = ReportStore(workspace)
    original = publish(store)
    other = store.publish('Website', 'source-2', DAY, 'Website_2026_01_02/article.md', REPORT + b'Another source.\n')
    assert other['report_path'] != original['report_path']
    assert Path(original['absolute_path']).read_bytes() == REPORT


def test_identical_reports_from_distinct_sources_keep_distinct_paths(workspace):
    store = ReportStore(workspace)
    first = publish(store)
    second = store.publish('Website', 'source-2', DAY, 'Website_2026_01_02/article.md', REPORT)
    assert first['report_path'] != second['report_path']
    store.publish('Website', 'source-1', DAY, 'Website_2026_01_02/article.md', REPORT + b'Update.\n', revise=True)
    assert store.lookup(second['key'])['sha256'] == second['sha256']


def test_requested_revision_preserves_previous_bytes(workspace):
    store = ReportStore(workspace)
    previous = publish(store)
    changed = REPORT + b'New evidence.\n'
    revised = store.publish('Website', 'source-1', DAY, 'Website_2026_01_02/article.md', changed, revise=True)
    assert revised['absolute_path'] == previous['absolute_path']
    assert Path(revised['absolute_path']).read_bytes() == changed
    assert (workspace.report_repository / revised['revisions'][0]).read_bytes() == REPORT


def test_modified_publication_stops_instead_of_overwriting(workspace):
    store = ReportStore(workspace)
    receipt = publish(store)
    Path(receipt['absolute_path']).write_bytes(b'# Local edit\n\nKeep this.\n')
    with pytest.raises(ValueError, match='differs'):
        publish(store)


def test_interruption_before_final_replace_is_recovered(workspace, monkeypatch):
    store = ReportStore(workspace)
    write = report_store.atomic_write
    def interrupt(path, data, staging):
        if path.name == 'article.md':
            raise OSError('injected interrupted publication')
        return write(path, data, staging)
    monkeypatch.setattr(report_store, 'atomic_write', interrupt)
    with pytest.raises(OSError, match='interrupted'):
        publish(store, suggestion=SUGGESTION)
    monkeypatch.setattr(report_store, 'atomic_write', write)
    receipt = store.lookup(item_key('Website', 'source-1', DAY))
    assert Path(receipt['absolute_path']).read_bytes() == REPORT
    assert receipt['suggestion_staged'] and not receipt['acknowledged']


def test_permission_failure_preserves_previous_version(workspace, monkeypatch):
    store = ReportStore(workspace)
    previous = publish(store)
    write = report_store.atomic_write
    def deny(path, data, staging):
        if path.name == 'article.md':
            raise PermissionError('injected permission denial')
        return write(path, data, staging)
    monkeypatch.setattr(report_store, 'atomic_write', deny)
    with pytest.raises(PermissionError):
        store.publish('Website', 'source-1', DAY, 'Website_2026_01_02/article.md', REPORT + b'Revision\n', revise=True)
    assert Path(previous['absolute_path']).read_bytes() == REPORT


def test_ledger_merge_recovers_without_duplicate_entry(workspace, monkeypatch):
    store = ReportStore(workspace)
    receipt = publish(store, suggestion=SUGGESTION)
    save = store.save
    def interrupt(receipt):
        if receipt.get('graded'):
            raise OSError('injected receipt failure after ledger write')
        return save(receipt)
    monkeypatch.setattr(store, 'save', interrupt)
    entry = f'### {DAY} | Website | [Example](https://example.invalid/article)\n- Report: [report]({receipt["report_link"]})'
    with pytest.raises(OSError):
        store.merge(receipt['key'], 'pending', entry)
    monkeypatch.setattr(store, 'save', save)
    assert store.merge(receipt['key'], 'pending', entry)['graded']
    assert (workspace.personal_data / 'suggestions_pending.md').read_text().count('### ') == 1
    with pytest.raises(ValueError, match='already routed'):
        store.merge(receipt['key'], 'filtered', entry)


def test_run_claim_requires_explicit_owner_reconciliation(workspace):
    store = ReportStore(workspace)
    first = store.claim_run('first')
    with pytest.raises(ValueError, match='claimed'):
        store.claim_run('retry')
    with pytest.raises(ValueError, match='owner'):
        store.claim_run('wrong', finish=True)
    assert not store.claim_run(first['run_id'], finish=True)['active']
    assert store.claim_run('second')['active']


def test_date_selection_ignores_modification_time_and_revisions(workspace):
    store = ReportStore(workspace)
    receipt = publish(store)
    old = workspace.reports / 'Website_2025_01_01/old.md'
    old.parent.mkdir()
    old.write_bytes(REPORT)
    store.publish('Distillation', DAY, DAY, 'distillations/Knowledge_Distillation_2026_01_02.md', REPORT)
    store.publish('Website', 'source-1', DAY, 'Website_2026_01_02/article.md', REPORT + b'Revised.\n', revise=True)
    assert store.today_reports(DAY) == [receipt['absolute_path']]


def test_competing_cli_publishers_create_one_artifact_and_suggestion(workspace, tmp_path):
    candidate = tmp_path / 'candidate with spaces.md'
    candidate.write_bytes(REPORT)
    suggestion = tmp_path / 'suggestion.json'
    suggestion.write_text(json.dumps(SUGGESTION))
    command = [sys.executable, '-B', str(Path(report_store.__file__)), '--config', str(workspace.config),
               'publish', '--source-type', 'Website', '--source-id', 'source-1', '--date', DAY,
               '--input', str(candidate), '--path', 'Website_2026_01_02/article.md', '--suggestion', str(suggestion)]
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    processes = [subprocess.Popen(command, cwd=tmp_path, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(3)]
    results = []
    for process in processes:
        output, errors = process.communicate(timeout=20)
        assert process.returncode == 0, errors
        results.append(json.loads(output))
    assert len({r['key'] for r in results}) == 1
    assert len(list(workspace.reports.glob('Website_*/*.md'))) == 1
    assert len(list((workspace.personal_data / 'suggestions_pending').glob('*.json'))) == 1


def test_revision_with_suggestion_keeps_previous_staged_input(workspace):
    store = ReportStore(workspace)
    previous = publish(store, suggestion=SUGGESTION)
    store.merge(previous['key'], 'pending', f'### {DAY} | Website | Example\n- Action')
    revised = store.publish('Website', 'source-1', DAY, 'Website_2026_01_02/article.md', REPORT + b'New evidence.\n', suggestion=SUGGESTION, revise=True)
    assert revised['suggestion_staged'] and not revised['graded']
    assert len(list((workspace.personal_data / 'suggestions_pending').glob('*.json'))) == 2


def test_acknowledgement_is_blocked_until_suggestion_is_durable(workspace, monkeypatch):
    store = ReportStore(workspace)
    write = report_store.atomic_write
    def deny_suggestion(path, data, staging):
        if path.parent.name == 'suggestions_pending':
            raise PermissionError('injected personal-state denial')
        return write(path, data, staging)
    monkeypatch.setattr(report_store, 'atomic_write', deny_suggestion)
    with pytest.raises(PermissionError):
        publish(store, suggestion=SUGGESTION)
    key = item_key('Website', 'source-1', DAY)
    assert not store.read(key)['acknowledged']
    with pytest.raises(PermissionError):
        store.mark_acknowledged(key)
    assert not store.read(key)['acknowledged']
