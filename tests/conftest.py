import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from workspace_paths import load_workspace


@pytest.fixture
def workspace(tmp_path):
    home = tmp_path / 'renamed home with spaces'
    repository = tmp_path / 'different reports 資料'
    personal = repository / 'private data'
    home.mkdir()
    personal.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', str(repository)], check=True)
    (personal / 'lang_preferences.md').write_text(
        '# Languages\n- **Preferred Report Language**: English\n'
        '- **Preferred Conversation Language**: English\n'
    )
    (personal / 'goals.md').write_text('# Goals\n- Understand distributed systems\n')
    config = tmp_path / 'external config.json'
    config.write_text(json.dumps({'report_repository': repository.name, 'personal_data': str(personal.relative_to(tmp_path))}))
    return load_workspace(config, home_root=home)
