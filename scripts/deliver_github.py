"""Push local branches, open a PR, and optionally merge only after both real CI jobs pass.

Requires existing GitHub credentials; never prints, stores or asks for tokens.
API reference: https://docs.github.com/en/rest/pulls/pulls
"""
import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = 'Pilli9375/Text_Speech-to-ISL-Sign-Generation'
BRANCH = 'feature/text-to-sign'
ENV = {**os.environ, 'GIT_TERMINAL_PROMPT': '0', 'GCM_INTERACTIVE': 'Never'}


def git(*args):
    result = subprocess.run(['git', *args], cwd=ROOT, env=ENV, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError('Git operation failed: ' + ' '.join(args) + '; inspect authentication/remote state locally')
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--merge', action='store_true', help='Merge after both actual Windows/Linux check jobs pass')
    args = parser.parse_args()
    if git('status', '--porcelain'):
        raise RuntimeError('Commit reviewed source changes before delivery; the working tree must be clean')
    if git('branch', '--show-current') != BRANCH:
        raise RuntimeError('Deliver from the feature/text-to-sign branch')
    remote = git('remote', 'get-url', 'origin')
    if remote.rstrip('/').removesuffix('.git') != 'https://github.com/' + REPO:
        raise RuntimeError('Unexpected remote; refusing to send project data to another destination')
    credential = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                                text=True, capture_output=True, env=ENV, timeout=25)
    values = dict(line.split('=', 1) for line in credential.stdout.splitlines() if '=' in line)
    token = values.get('password')
    if credential.returncode or not token:
        raise RuntimeError('Authenticate Git for github.com with repository write access, then retry; no token was stored')
    def api(path, method='GET', body=None):
        request = urllib.request.Request('https://api.github.com' + path, method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                     'Content-Type': 'application/json', 'User-Agent': 'SignBridge-delivery'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response: return json.load(response)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'GitHub API returned HTTP {exc.code}; authentication, permissions or branch rules need attention') from None
    api('/user')
    git('push', '-u', 'origin', 'main', BRANCH)
    sha = git('rev-parse', 'HEAD')
    prefix = '/repos/' + REPO
    query = urllib.parse.urlencode(dict(state='open', head='Pilli9375:' + BRANCH, base='main'))
    pulls = api(prefix + '/pulls?' + query)
    pull = pulls[0] if pulls else api(prefix + '/pulls', 'POST', dict(
        title='Add SignBridge text and speech dictionary prototype with review and evaluation tools',
        head=BRANCH, base='main', body=(ROOT / 'text_to_sign/docs/github_pr.md').read_text(encoding='utf-8')))
    print('Pull request:', pull['html_url'], flush=True)
    status = dict(branch=BRANCH, head_sha=sha, push=True, pull_request=pull['html_url'], remote_ci=False,
                  merged=False, remote_status='Pushed; pull request open; CI pending')
    def save():
        (ROOT / 'text_to_sign/docs/delivery_status.json').write_text(json.dumps(status, indent=2), encoding='utf-8')
    save()
    if not args.merge: return
    expected = {'checks-ubuntu-latest', 'checks-windows-latest'}
    for attempt in range(60):
        runs = api(prefix + '/commits/' + sha + '/check-runs?per_page=100')['check_runs']
        relevant = {r['name']: r for r in runs if r['name'] in expected}
        if any(r['status'] == 'completed' and r['conclusion'] != 'success' for r in relevant.values()):
            status['remote_status'] = 'CI failed; no merge attempted'; save()
            raise RuntimeError('Actual remote CI failed; inspect the pull request')
        if set(relevant) == expected and all(r['conclusion'] == 'success' for r in relevant.values()):
            status['remote_ci'] = True; save(); break
        print('Waiting for both real CI jobs...', flush=True); time.sleep(10)
    else:
        raise TimeoutError('CI did not finish; PR remains open and no merge was attempted')
    merged = api(prefix + f'/pulls/{pull["number"]}/merge', 'PUT', dict(sha=sha, merge_method='merge'))
    status.update(merged=merged.get('merged') is True, merge_sha=merged.get('sha'),
                  remote_status='Merged after passing Windows/Linux CI' if merged.get('merged') else 'GitHub declined merge')
    save()
    if not status['merged']: raise RuntimeError('GitHub did not merge the PR; branch rules remain enforced')
    print(status['remote_status'])


if __name__ == '__main__': main()
