"""Create a local handover ZIP containing code, provenance and all validated media.

Excludes model weights, virtual environments, node_modules, raw source photographs,
test recordings and Git metadata. Human review status is preserved, not elevated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from text_to_sign.engine import Dictionary, safe_asset


def package(target: Path):
    bank = Dictionary()
    entries = bank.entries()
    missing = [e['text'] for e in entries if not bank.available(e, preview=True)]
    if missing:
        raise ValueError('Missing or invalid source media: ' + ', '.join(missing))
    files = set()
    for folder in (ROOT / 'text_to_sign', ROOT / 'scripts', ROOT / '.github'):
        for path in folder.rglob('*'):
            if path.is_file() and path.name != 'release_validation.json' and not any(part in {'__pycache__', '.pytest_cache', 'signs'} for part in path.relative_to(ROOT).parts):
                files.add(path)
    for path in ROOT.iterdir():
        if path.is_file() and path.name in {'README.md', 'pyproject.toml', 'requirements.txt', 'requirements-dev.txt',
                                          'requirements-lock.txt', 'start.bat', 'start.ps1', 'package.json',
                                          'package-lock.json', '.gitignore', '.gitattributes'}:
            files.add(path)
    files.update(safe_asset(e['file']) for e in entries)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, 'SignBridge/' + path.relative_to(ROOT).as_posix())
    with target.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    target.with_suffix('.sha256').write_text(digest + '  ' + target.name + '\n')
    print(json.dumps({'archive': str(target), 'files': len(files), 'media': len(entries),
                      'bytes': target.stat().st_size, 'sha256': digest}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/SignBridge-1.2.zip')
    package(parser.parse_args().output.resolve())
