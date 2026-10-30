"""Record an actual human review. Do not run on behalf of an absent reviewer."""
import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from text_to_sign.engine import ROOT, is_ready, safe_asset

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--term', required=True)
parser.add_argument('--type', choices=['word', 'phrase', 'alphabet'], help='Required when a word and a letter share the same text')
parser.add_argument('--reviewer', required=True, help='Name/identifier of the ISL-fluent reviewer who actually reviewed the clip')
parser.add_argument('--meaning', required=True, help='Reviewed meaning, context and part of speech')
parser.add_argument('--note', required=True, help='Review observations including handshape, movement and context')
parser.add_argument('--label-checked', action='store_true')
parser.add_argument('--isl-reviewed', action='store_true')
parser.add_argument('--reject', action='store_true', help='Record a human rejection and exclude the clip even from preview')
args = parser.parse_args()
if not args.reject and not (args.label_checked and args.isl_reviewed):
    parser.error('Approval requires both --label-checked and --isl-reviewed')
if not args.reviewer.strip() or not args.meaning.strip() or not args.note.strip():
    parser.error('Reviewer, meaning and review observations must not be blank')
file = ROOT / 'data/signs.json'
data = json.loads(file.read_text(encoding='utf-8'))
matches = [e for e in data['entries'] if e['text'] == args.term.lower() and (args.type is None or e['type'] == args.type)]
if len(matches) > 1:
    parser.error('Ambiguous term: specify --type word, phrase or alphabet')
entry = matches[0] if matches else None
if entry is None:
    parser.error('Term not found')
if not entry.get('checks', {}).get('playable') or not safe_asset(entry['file']).is_file():
    parser.error('Run audit_assets.py on the actual playable media first')
if hashlib.sha256(safe_asset(entry['file']).read_bytes()).hexdigest() != entry.get('sha256'):
    parser.error('The clip changed since the last audit. Audit and inspect the actual file before approval.')
entry['checks']['label_checked'] = not args.reject
entry['checks']['isl_reviewed'] = not args.reject
entry.update(reviewed_by=args.reviewer, reviewed_on=str(date.today()), meaning=args.meaning,
             review_note=args.note, status='REJECTED' if args.reject else 'READY')
if not args.reject and not is_ready(entry):
    parser.error('Other readiness requirements are missing')
temporary = file.with_suffix('.tmp')
temporary.write_text(json.dumps(data, indent=2), encoding='utf-8')
temporary.replace(file)
print(f'Recorded {entry["status"]} review for {entry["text"]}; re-run audit_assets.py to refresh CSV reports.')
