"""Generate the roadmap CSV and a blank reviewer worklist from canonical signs.json."""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from text_to_sign.engine import ROOT, is_ready


def export(root=ROOT):
    entries = json.loads((root / 'data/signs.json').read_text(encoding='utf-8'))['entries']
    folder = root / 'data/metadata'
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'sign_dictionary.csv').open('w', encoding='utf-8', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=['sign_id', 'english_text', 'category', 'asset_path', 'verified_by', 'status'])
        writer.writeheader()
        for e in entries:
            writer.writerow(dict(sign_id=e['id'], english_text=e['text'], category=e['type'],
                                 asset_path=e['file'], verified_by=e.get('reviewed_by', '') if is_ready(e) else '',
                                 status='verified' if is_ready(e) else 'pending'))
    with (root / 'docs/review_worklist.csv').open('w', encoding='utf-8', newline='') as out:
        fields = ['id', 'text', 'type', 'file', 'sha256', 'source_url', 'status', 'meaning',
                  'reviewed_by', 'reviewed_on', 'review_note']
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(entries)
    return len(entries)


if __name__ == '__main__':
    print(f'Exported {export()} canonical entries; no approval state changed.')
