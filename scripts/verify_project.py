"""Run release-relevant code checks and retain exact observed counts."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    checks = []
    for name, command in [('python', [sys.executable, '-m', 'pytest', '-q']),
                          ('javascript', ['node', '--test', 'text_to_sign/tests/browser-state.test.mjs']),
                          ('syntax', ['node', '--check', 'text_to_sign/web/app.js']),
                          ('diff', ['git', 'diff', '--check', 'HEAD'])]:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
        log = ROOT / 'artifacts' / f'verify-{name}.log'; log.parent.mkdir(exist_ok=True)
        log.write_text(result.stdout + result.stderr, encoding='utf-8')
        match = re.search(r'(\d+) passed', result.stdout) if name == 'python' else re.search(r'(?:ℹ|#) pass (\d+)', result.stdout)
        row = dict(check=name, passed=result.returncode == 0,
                   count=int(match.group(1)) if match else None, log=str(log.relative_to(ROOT)))
        checks.append(row); print(json.dumps(row))
    (ROOT / 'text_to_sign/docs/code_verification.json').write_text(json.dumps(dict(checks=checks), indent=2), encoding='utf-8')
    raise SystemExit(0 if all(c['passed'] for c in checks) else 1)


if __name__ == '__main__': main()
