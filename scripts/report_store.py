#!/usr/bin/env python3
"""Publish reports and resume local publication work without calling external APIs."""

import argparse
from contextlib import contextmanager
from datetime import date
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import uuid

from workspace_paths import SetupError, load_workspace


SOURCE_TYPES = {'Newsletter', 'Threads', 'Website', 'YouTube', 'Articles', 'GitHub', 'Distillation'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def item_key(source_type, source_id, report_date):
    if source_type not in SOURCE_TYPES or not source_id.strip():
        raise ValueError('Provide a supported source type and a nonempty stable source identity')
    if date.fromisoformat(report_date).isoformat() != report_date:
        raise ValueError('Use a report date in YYYY-MM-DD format')
    return digest(json.dumps([source_type, source_id, report_date]).encode())


def safe_path(base, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Output paths must be relative and must not traverse parent directories')
    target = base / relative
    for part in (target, *target.parents):
        if part.is_symlink():
            raise ValueError('Output paths must not contain symlinks')
        if part == base:
            break
    target.resolve().relative_to(base.resolve())
    return target


def atomic_write(path, data, staging):
    path.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    if staging.stat().st_dev != path.parent.stat().st_dev:
        raise ValueError('Staging and destination must be on the same filesystem')
    temporary = staging / (uuid.uuid4().hex + '.tmp')
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def validate_report(data):
    content = data.decode('utf-8')
    lines = content.strip().splitlines()
    if len(lines) < 2 or not lines[0].startswith('# ') or not any(line.strip() for line in lines[1:]):
        raise ValueError('A report must have a Markdown title and nonempty body')


class ReportStore:
    def __init__(self, workspace):
        self.workspace = workspace
        self.repository = workspace.report_repository
        self.reports = safe_path(self.repository, 'reports')
        self.staging = safe_path(self.repository, '.tmp/report-store')

    @contextmanager
    def locked(self):
        self.staging.mkdir(parents=True, exist_ok=True)
        path = safe_path(self.repository, '.tmp/report-store/store.lock')
        with path.open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def receipt_path(self, key):
        if not re.fullmatch(r'[0-9a-f]{64}', key):
            raise ValueError('Invalid publication key')
        return safe_path(self.repository, f'reports/.metadata/{key}.json')

    def save(self, receipt):
        data = json.dumps(receipt, ensure_ascii=False, indent=2).encode() + b'\n'
        atomic_write(self.receipt_path(receipt['key']), data, self.staging)

    def read(self, key):
        path = self.receipt_path(key)
        if not path.exists():
            return None
        receipt = json.loads(path.read_text(encoding='utf-8'))
        if receipt.get('key') != key:
            raise ValueError('Publication receipt identity mismatch')
        return receipt

    def verify(self, receipt):
        path = safe_path(self.reports, Path(receipt['report_path']).relative_to('reports'))
        if not path.is_file() or digest(path.read_bytes()) != receipt['sha256']:
            raise ValueError('Published content differs from its receipt; reconcile before retrying')
        return path

    def result(self, receipt):
        result = dict(receipt)
        target = self.repository / receipt['report_path']
        result['absolute_path'] = str(target)
        result['report_link'] = os.path.relpath(target, self.workspace.personal_data)
        return result

    def recover(self, receipt):
        if receipt['state'] == 'publishing':
            target = safe_path(self.reports, Path(receipt['report_path']).relative_to('reports'))
            if not target.is_file() or digest(target.read_bytes()) != receipt['sha256']:
                candidate = safe_path(self.repository, receipt['candidate'])
                if not candidate.is_file() or digest(candidate.read_bytes()) != receipt['sha256']:
                    raise ValueError('Interrupted publication has no verified candidate; keep the source open')
                current_hash = digest(target.read_bytes()) if target.is_file() else None
                if current_hash != receipt.get('previous_sha256'):
                    raise ValueError('Destination changed during interrupted publication; reconcile first')
                atomic_write(target, candidate.read_bytes(), self.staging)
            receipt['state'] = 'stored'
            self.save(receipt)
        self.verify(receipt)
        if receipt.get('suggestion') and not receipt.get('suggestion_staged'):
            pending = safe_path(self.workspace.personal_data, f'suggestions_pending/suggestion_{receipt["key"]}_{receipt["sha256"][:12]}.json')
            # Personal state may live on another volume, so stage beside its own directory.
            personal_staging = safe_path(self.workspace.personal_data, '.tmp/report-store')
            data = json.dumps(receipt['suggestion'], ensure_ascii=False, indent=2).encode() + b'\n'
            if pending.exists() and pending.read_bytes() != data:
                raise ValueError('A staged suggestion was edited; reconcile before retrying')
            if not pending.exists():
                atomic_write(pending, data, personal_staging)
            receipt['suggestion_staged'] = True
            self.save(receipt)
        return receipt

    def lookup(self, key):
        with self.locked():
            receipt = self.read(key)
            return self.result(self.recover(receipt)) if receipt else None

    def publish(self, source_type, source_id, report_date, relative_path, data, suggestion=None, revise=False):
        key = item_key(source_type, source_id, report_date)
        validate_report(data)
        relative = Path(relative_path)
        if relative.suffix != '.md' or not relative.parts or any(part.startswith('.') for part in relative.parts):
            raise ValueError('Choose a Markdown report path outside metadata and revision directories')
        target = safe_path(self.reports, relative)
        with self.locked():
            previous = self.read(key)
            if previous:
                previous = self.recover(previous)
                if not revise or previous['sha256'] == digest(data):
                    return self.result(previous)
                if relative.as_posix() != Path(previous['report_path']).relative_to('reports').as_posix():
                    raise ValueError('A revision must retain the existing report path')
                if previous.get('suggestion') and not previous.get('graded'):
                    raise ValueError('Grade the previous suggestion before publishing a revision')
            # A pre-existing filename can belong to another identity even when bytes match.
            if target.exists() and not previous:
                relative = relative.with_name(f'{relative.stem}_{key[:12]}.md')
                target = safe_path(self.reports, relative)
                if target.exists() and target.read_bytes() != data:
                    raise ValueError('Conflicting report identity at the collision-safe path')
            old_data = target.read_bytes() if target.exists() else None
            revisions = list(previous.get('revisions', [])) if previous else []
            if old_data is not None and old_data != data:
                revision_path = Path('.revisions') / relative / (digest(old_data) + '.md')
                archive = safe_path(self.reports, revision_path)
                atomic_write(archive, old_data, self.staging)
                revisions.append('reports/' + revision_path.as_posix())
            report_path = 'reports/' + relative.as_posix()
            if suggestion is not None:
                required = {'title', 'source_url', 'category', 'suggestion'}
                if not isinstance(suggestion, dict) or any(not isinstance(suggestion.get(k), str) or not suggestion[k].strip() for k in required):
                    raise ValueError('Suggestion requires title, source_url, category, and suggestion strings')
                if not suggestion['source_url'].startswith(('https://', 'http://', 'mailto:')):
                    raise ValueError('Suggestion source_url must be an HTTP(S) or mailto URL')
                suggestion = {**suggestion, 'date': report_date, 'source_type': source_type, 'report_path': report_path, 'publication_key': key}
            candidate = f'.tmp/report-store/{key}/candidate.md'
            atomic_write(safe_path(self.repository, candidate), data, self.staging)
            receipt = {
                'key': key, 'source_type': source_type, 'source_id': source_id,
                'date': report_date, 'report_path': report_path, 'sha256': digest(data),
                'state': 'publishing', 'candidate': candidate,
                'previous_sha256': digest(old_data) if old_data is not None else None,
                'suggestion': suggestion, 'suggestion_staged': False,
                'acknowledged': bool(previous and previous.get('acknowledged')),
                'graded': suggestion is None, 'revisions': revisions,
            }
            self.save(receipt)
            return self.result(self.recover(receipt))

    def mark_acknowledged(self, key):
        with self.locked():
            receipt = self.read(key)
            if receipt is None:
                raise ValueError('Unknown publication')
            self.recover(receipt)
            receipt['acknowledged'] = True
            self.save(receipt)
            return self.result(receipt)

    def merge(self, key, ledger, entry):
        if ledger not in {'pending', 'filtered'} or not entry.strip().startswith('### '):
            raise ValueError('Provide a pending/filtered ledger and a Markdown entry beginning with ###')
        with self.locked():
            receipt = self.read(key)
            if receipt is None:
                raise ValueError('Unknown publication')
            self.recover(receipt)
            if not receipt.get('suggestion'):
                raise ValueError('Publication has no suggestion to grade')
            if receipt.get('graded') and receipt.get('ledger') != ledger:
                raise ValueError('Suggestion already routed; use human review for subsequent feedback')
            path = safe_path(self.workspace.personal_data, f'suggestions_{ledger}.md')
            marker = f'<!-- publication:{key}:{receipt["sha256"]} -->'
            content = path.read_text(encoding='utf-8') if path.exists() else f'# {ledger.title()} Suggestions\n'
            if marker not in content:
                content = content.rstrip() + '\n\n---\n\n' + entry.strip() + '\n' + marker + '\n'
                atomic_write(path, content.encode(), safe_path(self.workspace.personal_data, '.tmp/report-store'))
            receipt.update(graded=True, ledger=ledger)
            self.save(receipt)
            return self.result(receipt)

    def claim_run(self, run_id=None, finish=False):
        if run_id is not None and not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', run_id):
            raise ValueError('Invalid run identity')
        path = safe_path(self.repository, '.tmp/report-store/active-run.json')
        with self.locked():
            existing = json.loads(path.read_text()) if path.exists() else None
            if finish:
                if not run_id or not existing or existing.get('run_id') != run_id:
                    raise ValueError('Only the recorded run owner can finish a run')
                existing['active'] = False
                atomic_write(path, json.dumps(existing).encode(), self.staging)
                return existing
            if existing and existing.get('active'):
                raise ValueError('Another run is claimed; reconcile its outcome before explicitly finishing its run ID')
            claim = {'run_id': run_id or uuid.uuid4().hex, 'active': True, 'date': self.workspace.report_date()}
            atomic_write(path, json.dumps(claim).encode(), self.staging)
            return claim

    def today_reports(self, report_date):
        date.fromisoformat(report_date)
        selected = set()
        if not self.reports.exists():
            return []
        for directory in self.reports.iterdir():
            if directory.is_symlink():
                raise ValueError('Report discovery refuses symlinked directories')
            if directory.is_dir() and directory.name.endswith('_' + report_date.replace('-', '_')):
                for path in directory.glob('*.md'):
                    selected.add(safe_path(self.reports, path.relative_to(self.reports)))
        for path in self.reports.glob('.metadata/*.json'):
            if path.is_symlink():
                raise ValueError('Report metadata must not be symlinked')
            receipt = json.loads(path.read_text())
            if receipt.get('date') == report_date and receipt.get('source_type') != 'Distillation' and receipt.get('state') == 'stored':
                selected.add(self.verify(receipt))
        github = safe_path(self.reports, 'GitHub')
        if github.exists():
            for path in github.glob('*.md'):
                path = safe_path(github, path.name)
                if re.search(r'\*\*Analysis Date\*\*:\s*' + re.escape(report_date) + r'\b', path.read_text(encoding='utf-8')):
                    selected.add(path)
        return [str(path) for path in sorted(selected)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('lookup', 'publish'):
        command = commands.add_parser(name)
        command.add_argument('--source-type', choices=sorted(SOURCE_TYPES), required=True)
        command.add_argument('--source-id', required=True)
        command.add_argument('--date')
        if name == 'publish':
            command.add_argument('--input', type=Path, required=True)
            command.add_argument('--path', required=True, help='Path beneath the report root')
            command.add_argument('--suggestion', type=Path)
            command.add_argument('--revise', action='store_true')
    command = commands.add_parser('acknowledged')
    command.add_argument('--key', required=True)
    command = commands.add_parser('merge')
    command.add_argument('--key', required=True)
    command.add_argument('--ledger', choices=['pending', 'filtered'], required=True)
    command.add_argument('--entry', type=Path, required=True)
    commands.add_parser('begin-run')
    command = commands.add_parser('finish-run')
    command.add_argument('--run-id', required=True)
    command = commands.add_parser('today-reports')
    command.add_argument('--date')
    args = parser.parse_args()
    try:
        store = ReportStore(load_workspace(args.config))
        report_date = getattr(args, 'date', None) or store.workspace.report_date()
        if args.command == 'lookup':
            result = store.lookup(item_key(args.source_type, args.source_id, report_date))
        elif args.command == 'publish':
            suggestion = json.loads(args.suggestion.read_text()) if args.suggestion else None
            result = store.publish(args.source_type, args.source_id, report_date, args.path, args.input.read_bytes(), suggestion, args.revise)
        elif args.command == 'acknowledged':
            result = store.mark_acknowledged(args.key)
        elif args.command == 'merge':
            result = store.merge(args.key, args.ledger, args.entry.read_text())
        elif args.command == 'begin-run':
            result = store.claim_run()
        elif args.command == 'finish-run':
            result = store.claim_run(args.run_id, finish=True)
        else:
            result = store.today_reports(report_date)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (SetupError, ValueError, OSError, KeyError) as exc:
        parser.exit(2, f'Publication stopped: {exc}\n')


if __name__ == '__main__':
    main()
