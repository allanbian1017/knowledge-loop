#!/usr/bin/env python3
"""Validate external language preferences without repairing user files."""
import argparse
import json
from pathlib import Path
from workspace_paths import SetupError, load_workspace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(load_workspace(args.config).languages(), ensure_ascii=False, indent=2))
    except (SetupError, OSError) as exc:
        parser.exit(2, f'Language setup required: {exc}\n')


if __name__ == '__main__':
    main()
