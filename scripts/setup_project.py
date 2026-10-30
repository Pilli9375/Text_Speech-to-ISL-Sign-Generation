"""Reproducible setup for the local checkout. Run with the project's venv Python."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run(*args):
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def setup(skip_assets=False, dev=False):
    requirement = ROOT / ('requirements-dev.txt' if dev else 'requirements.txt')
    inputs = [ROOT / 'requirements.txt', requirement]
    digest = hashlib.sha256(b''.join(p.read_bytes() for p in inputs)).hexdigest()
    stamp = Path(sys.prefix) / '.signbridge-dependencies'
    if not stamp.exists() or stamp.read_text() != digest:
        run('-m', 'pip', 'install', '-r', str(requirement))
        stamp.write_text(digest)
    if skip_assets:
        print('Dependencies ready. Asset restoration was explicitly skipped.')
        return
    manifest = json.loads((ROOT / 'text_to_sign/data/source_manifest.json').read_text(encoding='utf-8'))
    if (ROOT / 'text_to_sign/data/alphabet_manifest.json').exists():
        run('scripts/import_alphabet.py')
    run('scripts/source_assets.py', '--download')
    run('scripts/audit_assets.py', '--changed-only')
    print(f'Setup complete: {len(manifest["candidates"])} source assets audited. Human review status is unchanged.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-assets', action='store_true')
    parser.add_argument('--dev', action='store_true')
    args = parser.parse_args()
    setup(args.skip_assets, args.dev)
