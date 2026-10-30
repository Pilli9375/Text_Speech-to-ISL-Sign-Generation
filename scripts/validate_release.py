"""Extract a handover into a new folder and test its actual HTTP startup and cached ASR.

Uses the invoking Python's dependencies, but code and media only from the extracted ZIP.
"""
import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(archive, speech_sample=None):
    parent = ROOT / 'artifacts'; parent.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='release-check-', dir=parent))
    with archive.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    sidecar = archive.with_suffix('.sha256')
    if sidecar.exists() and sidecar.read_text().split()[0] != digest:
        raise ValueError('Release archive checksum does not match sidecar')
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            target = (folder / item.filename).resolve()
            if not target.is_relative_to(folder.resolve()):
                raise ValueError('Unsafe ZIP member path')
        z.extractall(folder)
    checkout = folder / 'SignBridge'
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0)); port = listener.getsockname()[1]
    env = {**os.environ, 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1',
           'PYTHONDONTWRITEBYTECODE': '1', 'SIGNBRIDGE_DIAGNOSTICS': '0', 'PYTHONPATH': str(checkout)}
    # Exercise the archive's restoration path with HTTP fetches disabled in the
    # child interpreter. Included playback media must be sufficient on their own.
    for script, arguments in [('scripts/import_alphabet.py', []),
                              ('scripts/source_assets.py', ['--download']),
                              ('scripts/audit_assets.py', ['--changed-only'])]:
        code = ("import runpy,sys,urllib.request; "
                "urllib.request.urlopen=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('Network disabled for release restoration check')); "
                "sys.argv=" + repr([script, *arguments]) + '; runpy.run_path(' + repr(script) + ",run_name='__main__')")
        restored = subprocess.run([sys.executable, '-c', code], cwd=checkout, env=env,
                                  capture_output=True, text=True, timeout=180)
        (folder / (Path(script).stem + '.log')).write_text(restored.stdout + restored.stderr, encoding='utf-8')
        if restored.returncode: raise RuntimeError('Extracted offline media restoration failed: ' + script)
    log = (folder / 'server.log').open('w')
    options = dict(cwd=checkout, env=env, stdout=log, stderr=subprocess.STDOUT)
    if os.name == 'nt': options['creationflags'] = subprocess.CREATE_NO_WINDOW
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'text_to_sign.app:app',
                                '--host', '127.0.0.1', '--port', str(port)], **options)
    url = f'http://127.0.0.1:{port}'
    def get(path):
        with urllib.request.urlopen(url + path, timeout=30) as response:
            return json.load(response)
    try:
        for attempt in range(60):
            try:
                health = get('/api/health'); break
            except OSError:
                if process.poll() is not None: raise RuntimeError('Extracted server exited; see validation log')
                time.sleep(.25)
        else: raise TimeoutError('Extracted server did not start')
        inventory = get('/api/dictionary')
        request = urllib.request.Request(url + '/api/convert', method='POST',
                    data=json.dumps(dict(text='hello friend thank you', preview=True)).encode(),
                    headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=30) as response: conversion = json.load(response)
        if [e['text'] for e in conversion['sequence']] != ['hello', 'friend', 'thank you']:
            raise ValueError('Extracted conversion failed')
        request = urllib.request.Request(url + conversion['sequence'][0]['url'], headers={'Range': 'bytes=0-1023'})
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 206 or len(response.read()) != 1024: raise ValueError('Range playback failed')
        try:
            urllib.request.urlopen(url + '/diagnostics/recorder', timeout=10)
            raise ValueError('Diagnostic endpoint unexpectedly exposed')
        except urllib.error.HTTPError as exc:
            if exc.code != 404: raise
        report = dict(archive=archive.name, sha256=digest, extracted_folder=str(checkout),
                      health=health, entries=inventory['total'], previewable=inventory['previewable'],
                      ready=inventory['ready'], http_conversion='passed', range_media='passed',
                      included_media_restoration_with_http_disabled='passed',
                      diagnostics_disabled=True, cached_asr=None,
                      limitation='Fresh folder with shared installed Python dependencies; not a fresh OS or fresh dependency installation.')
        if inventory['total'] != inventory['previewable']:
            raise ValueError('Extracted media bank has missing/rejected/unusable entries')
        if speech_sample:
            code = ('import json; from pathlib import Path; from text_to_sign.speech import transcribe; '
                    'print(json.dumps(transcribe(Path(' + repr(str(speech_sample.resolve())) + '))))')
            result = subprocess.run([sys.executable, '-c', code], cwd=checkout, env=env,
                                    capture_output=True, text=True, timeout=180)
            if result.returncode: raise RuntimeError('Cached offline ASR check failed: ' + result.stderr[-1000:])
            report['cached_asr'] = json.loads(result.stdout)
        (ROOT / 'text_to_sign/docs/release_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        archive.with_suffix('.validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        if os.name == 'nt' and process.poll() is None:
            # Windows venv redirectors may own a Python child; terminate only
            # this validator's exact process tree, not other local servers.
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
        elif process.poll() is None:
            process.terminate()
        try: process.wait(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); process.wait()
        log.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--speech-sample', type=Path)
    args = parser.parse_args()
    validate(args.archive.resolve(), args.speech_sample)
