"""Discover publicly listed ISLRTC dictionary clips; never mark them ISL-reviewed.

The official FAQ links the root Drive collection. Embedded public folder listings
are used because the portal times out and connector folder reads are capped at 100.
No API keys, account credentials, or private Drive data are needed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
import json
import re
import itertools
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = json.loads((ROOT / 'text_to_sign/data/vocabulary_targets.json').read_text(encoding='utf-8'))
TERMS = set(itertools.chain.from_iterable(TARGETS.values()))
ATTRIBUTION = ('Indian Sign Language Research and Training Centre (ISLRTC), DEPwD, '
               'Ministry of Social Justice and Empowerment, Government of India')


def listing(letter: str, folder_id: str) -> list[dict]:
    url = f'https://drive.google.com/embeddedfolderview?id={folder_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'SignBridge research asset inventory/0.1'})
    with urllib.request.urlopen(req, timeout=35) as response:
        page = response.read().decode('utf-8')
    results = []
    for file_id, title in re.findall(r'class="flip-entry" id="entry-([^\"]+)".*?class="flip-entry-title">(.*?)</div>', page, re.S):
        title = html.unescape(title)
        name = re.sub(r'[_\s]+', ' ', Path(title).stem).strip().lower()
        name = re.sub(r' \(sign [12]\)$', '', name)
        if name in TERMS and title.lower().endswith('.mp4'):
            results.append({'text': name, 'source_file_name': title, 'drive_id': file_id,
                            'source_url': f'https://drive.google.com/file/d/{file_id}/view',
                            'source_folder': url})
    print(f'{letter}: {len(results)} candidate terms')
    return results


def discover(limit=350) -> list[dict]:
    candidates = []
    folders = json.loads((ROOT / 'text_to_sign/data/source_folders.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(listing, letter, id): letter for letter, id in folders.items()}
        for future in concurrent.futures.as_completed(jobs):
            try:
                candidates.extend(future.result())
            except Exception as exc:
                print(f'{jobs[future]}: source unavailable ({exc})')
    # Prefer the plain source label over an explicitly numbered variant.
    candidates.sort(key=lambda x: ('(sign' in x['source_file_name'].lower(), x['source_file_name']))
    found = {}
    for item in candidates:
        found.setdefault(item['text'], item)
    target = ROOT / 'text_to_sign/data/source_manifest.json'
    old = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
    prior = {item['text']: item for item in old.get('candidates', []) if item.get('type') != 'alphabet'}
    limit = max(limit, len(prior))
    # Preserve existing terms, then select a balanced spread across everyday categories.
    ordered = list(prior)
    for row in itertools.zip_longest(*TARGETS.values()):
        ordered.extend(term for term in row if term is not None and term not in ordered)
    selected = []
    for term in ordered:
        if term in old.get('excluded_terms', {}):
            continue
        if term not in found and term not in prior:
            continue
        item = {**prior.get(term, {}), **found.get(term, {})}
        item['category'] = next((category for category, terms in TARGETS.items() if term in terms), item.get('category', 'Everyday signs'))
        if len(term) == 1:
            item['id'] = 'word_' + term
        selected.append(item)
        if len(selected) >= limit:
            break
    selected.sort(key=lambda item: item['text'])
    extra = [item for item in old.get('candidates', []) if item.get('type') == 'alphabet']
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps({**old, 'source': 'https://islrtc.nic.in/faq/', 'planned_terms': [item['text'] for item in selected],
                                  'candidates': selected + extra}, indent=2), encoding='utf-8')
    temporary.replace(target)
    report = {'requested': len(TERMS), 'matched_exact_source_labels': len(found), 'selected': len(selected),
              'unmatched': sorted(TERMS - set(found)), 'selected_terms': [item['text'] for item in selected]}
    (ROOT / 'text_to_sign/docs/vocabulary_expansion.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'{len(found)} exact-label matches found; {len(selected)} word/phrase clips selected plus {len(extra)} letters', flush=True)
    return selected + extra


def download(candidates: list[dict], workers=5):
    def fetch(item):
        relative = item.get('file') or ('signs/' + ('phrases/' if ' ' in item['text'] else 'words/') + item['text'].replace(' ', '_') + '.mp4')
        from text_to_sign.engine import safe_asset
        target = safe_asset(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if not item.get('sha256') or hashlib.sha256(target.read_bytes()).hexdigest() == item['sha256']:
                print(f'{item["text"]}: already present; run audit_assets.py to validate')
                return None
            print(f'{item["text"]}: local checksum changed; restoring original source')
        if 'drive_id' not in item:
            print(f'{item["text"]}: use the source-specific importer to restore this asset')
            return item['text']
        url = f'https://drive.usercontent.google.com/download?id={item["drive_id"]}&export=download'
        temporary = target.with_suffix('.download')
        try:
            digest = hashlib.sha256()
            with urllib.request.urlopen(url, timeout=45) as response, temporary.open('wb') as out:
                if 'text/html' in response.headers.get('Content-Type', ''):
                    raise ValueError('Provider returned an HTML page, not media')
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > 50 * 1024 * 1024:
                        raise ValueError('Source clip exceeds 50 MB limit')
                    out.write(chunk); digest.update(chunk)
            expected = item.get('sha256')
            if expected and digest.hexdigest() != expected:
                raise ValueError('Checksum changed; inspect the replacement source before using it')
            temporary.replace(target)
            print(f'{item["text"]}: downloaded')
        except Exception as exc:
            temporary.unlink(missing_ok=True)
            print(f'{item["text"]}: download failed ({exc}); use the canonical source URL in the manifest')
            return item['text']
        return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        return [term for term in pool.map(fetch, candidates) if term]


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(ROOT))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--discover', action='store_true')
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--limit', type=int, default=350, help='Maximum word/phrase clips, balanced across categories')
    parser.add_argument('--workers', type=int, default=5)
    args = parser.parse_args()
    candidates = discover(args.limit) if args.discover else json.loads((ROOT / 'text_to_sign/data/source_manifest.json').read_text())['candidates']
    if args.download:
        raise SystemExit(1 if download(candidates, args.workers) else 0)
