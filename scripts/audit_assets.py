"""Decode source clips, record real metadata, and build the pending-review registry.

Run after source_assets.py --download. This checks media, not sign correctness.
Existing human review fields are retained only when the file checksum is unchanged.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from text_to_sign.engine import ROOT, is_ready, safe_asset

ATTRIBUTION = ('Indian Sign Language Research and Training Centre (ISLRTC), DEPwD, '
               'Ministry of Social Justice and Empowerment, Government of India')


def audit(changed_only=False):
    import av
    manifest_path = ROOT / 'data/source_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    old = {(e['type'], e['text']): e for e in json.loads((ROOT / 'data/signs.json').read_text(encoding='utf-8'))['entries']}
    entries, frames, report = [], [], []
    for item in manifest['candidates']:
        term = item['text']
        kind = item.get('type', 'phrase' if ' ' in term else 'word')
        file = item.get('file') or ('signs/' + ('phrases/' if ' ' in term else 'words/') + term.replace(' ', '_') + '.mp4')
        path = safe_asset(file)
        entry = {'id': item.get('id', term.replace(' ', '_')), 'text': term, 'file': file,
                 'type': kind,
                 'category': item.get('category', 'Alphabet' if kind == 'alphabet' else 'Everyday signs'),
                 'aliases': item.get('aliases', []),
                 'meaning': item.get('meaning') or f'Official dictionary label: {Path(item["source_file_name"]).stem.replace("_", " ")}. Semantic context awaits ISL review.',
                 'source_url': item['source_url'], 'source_file_name': item['source_file_name'],
                 'provider': item.get('provider', 'islrtc'),
                 'source_member': item.get('source_member', ''), 'source_sha256': item.get('source_sha256', ''),
                 'attribution': item.get('attribution', ATTRIBUTION), 'terms_url': item.get('terms_url', 'https://islrtc.nic.in/faq/'),
                 'usage_note': item.get('usage_note', 'Non-commercial research; no resale or profiteering; acknowledge ISLRTC.'),
                 'checks': {'playable': False, 'label_checked': False, 'isl_reviewed': False, 'usage_approved': True},
                 'reviewed_by': '', 'reviewed_on': '', 'status': 'FOUND'}
        result = {'term': term, 'file': file, 'exists': path.is_file()}
        if path.is_file():
            checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            entry['sha256'] = checksum
            try:
                if item.get('sha256') and item['sha256'] != checksum:
                    raise ValueError('Checksum differs from recorded source; re-source or review the changed file')
                item.setdefault('sha256', checksum)
                previous = old.get((kind, term), {})
                if (changed_only and previous.get('sha256') == checksum
                        and previous.get('checks', {}).get('playable') is True and previous.get('media')):
                    entry['media'] = previous['media']
                    entry['checks']['playable'] = True
                    for key in ('reviewed_by', 'reviewed_on', 'review_note', 'meaning'):
                        if key in previous:
                            entry[key] = previous[key]
                    for key in ('label_checked', 'isl_reviewed'):
                        entry['checks'][key] = previous.get('checks', {}).get(key, False)
                    entry['status'] = 'READY' if previous.get('status') == 'READY' else 'PLAYABLE'
                    if previous.get('status') == 'REJECTED':
                        entry['status'] = 'REJECTED'
                    if entry['status'] == 'READY' and not is_ready(entry):
                        entry['status'] = 'PLAYABLE'
                    result.update(previous['media'])
                    result.update(decoded=True, check_method='SHA256 matches previously fully decoded media')
                    entries.append(entry); report.append(result)
                    print(f'{term}: unchanged media checksum verified', flush=True)
                    continue
                with av.open(str(path)) as container:
                    stream = container.streams.video[0]
                    count, duration, sample = 0, 0.0, None
                    for frame in container.decode(stream):
                        count += 1
                        if frame.time is not None:
                            duration = frame.time
                        # Prefer a frame after the title introduction; fallback to first.
                        if sample is None or count == 60:
                            sample = frame.to_image()
                    fps = float(stream.average_rate or 0)
                    metadata = {'frames': count, 'fps': round(fps, 2), 'width': stream.width,
                                'height': stream.height, 'codec': stream.codec_context.name,
                                'duration_seconds': round(duration + (1 / fps if fps else 0), 2),
                                'bytes': path.stat().st_size}
                    if count == 0 or stream.width < 100 or stream.height < 100:
                        raise ValueError('No usable video frames')
                    entry['media'] = metadata
                    entry['checks']['playable'] = True
                    entry['status'] = 'PLAYABLE'
                    if old.get((kind, term), {}).get('sha256') == checksum:
                        previous = old[(kind, term)]
                        for key in ('reviewed_by', 'reviewed_on', 'review_note', 'meaning'):
                            if key in previous:
                                entry[key] = previous[key]
                        for key in ('label_checked', 'isl_reviewed'):
                            entry['checks'][key] = previous.get('checks', {}).get(key, False)
                        if previous.get('status') == 'READY':
                            entry['status'] = 'READY'
                            if not is_ready(entry):
                                entry['status'] = 'PLAYABLE'
                        if previous.get('status') == 'REJECTED':
                            entry['status'] = 'REJECTED'
                    if sample:
                        sample.thumbnail((310, 215))
                        frames.append((term, sample))
                    result.update(metadata)
                    result['decoded'] = True
            except Exception as exc:
                result['decoded'] = False; result['error'] = str(exc)
        entries.append(entry); report.append(result)
        print(f'{term}: {entry["status"]}', flush=True)
    # Preserve manually registered entries which are not managed by the source manifest.
    managed = {(e['type'], e['text']) for e in entries}
    entries.extend(e for identity, e in old.items() if identity not in managed)
    dictionary_path = ROOT / 'data/signs.json'
    dictionary_temp = dictionary_path.with_suffix('.tmp')
    dictionary_temp.write_text(json.dumps({'schema_version': 1, 'entries': entries}, indent=2), encoding='utf-8')
    dictionary_temp.replace(dictionary_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    docs = ROOT / 'docs'; docs.mkdir(exist_ok=True)
    (docs / 'asset_audit.json').write_text(json.dumps({'audit_date': str(date.today()), 'assets': report}, indent=2), encoding='utf-8')
    columns = ['text', 'type', 'category', 'status', 'file', 'source_url', 'source_file_name', 'source_member', 'source_sha256', 'attribution', 'terms_url', 'usage_note', 'sha256', 'reviewed_by', 'reviewed_on']
    with (docs / 'asset_register.csv').open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=columns, extrasaction='ignore'); writer.writeheader(); writer.writerows(entries)
    with (docs / 'vocabulary_inventory.csv').open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=['term', 'type', 'planned', 'found', 'playable', 'isl_reviewed', 'ready']); writer.writeheader()
        targets = [('phrase' if ' ' in term else 'word', term) for term in manifest['planned_terms']]
        targets += [('alphabet', e['text']) for e in entries if e['type'] == 'alphabet']
        for kind, term in targets:
            entry = next((e for e in entries if e['text'] == term and e['type'] == kind), None)
            writer.writerow({'term': term, 'planned': True, 'found': entry is not None,
                             'type': kind,
                             'playable': bool(entry and entry['checks']['playable']),
                             'isl_reviewed': bool(entry and entry['checks']['isl_reviewed']),
                             'ready': bool(entry and is_ready(entry))})
    if frames:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
        width, height, columns = 320, 255, 4
        sheet = Image.new('RGB', (width * columns, height * ((len(frames) + columns - 1) // columns)), '#f6f7f3')
        draw = ImageDraw.Draw(sheet)
        for i, (term, frame) in enumerate(frames):
            thumb = ImageOps.contain(frame, (310, 215))
            x, y = (i % columns) * width, (i // columns) * height
            sheet.paste(thumb, (x + (width - thumb.width) // 2, y + 5))
            try:
                font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
            except OSError:
                font = ImageFont.load_default(size=15)
            draw.text((x + 10, y + 224), f'{i + 1:02} {term} | REVIEW PENDING', fill='#173b36', font=font)
        target = ROOT.parent / 'artifacts'; target.mkdir(exist_ok=True)
        sheet.save(target / 'source-contact-sheet.jpg')
    print(f'Audited {len(entries)} entries; READY: {sum(is_ready(e) for e in entries)}')
    from scripts.export_metadata import export
    export()
    return all(item.get('decoded') for item in report)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--changed-only', action='store_true', help='Verify every checksum; reuse full-decode evidence only for unchanged files')
    raise SystemExit(0 if audit(parser.parse_args().changed_only) else 1)
