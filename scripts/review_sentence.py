"""Register an order that an identified ISL-fluent human has actually reviewed."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from text_to_sign.engine import ROOT, Dictionary, normalize
from text_to_sign.sentences import validate_rule


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--input', required=True)
    parser.add_argument('--sign-ids', nargs='+', required=True, help='Explicit ordered dictionary IDs')
    parser.add_argument('--reviewer', required=True)
    parser.add_argument('--note', required=True)
    args = parser.parse_args()
    rule = dict(id=args.id, input=args.input, sign_ids=args.sign_ids, reviewed_by=args.reviewer,
                reviewed_on=str(date.today()), review_note=args.note, status='verified')
    validate_rule(rule)
    ids = {e['id'] for e in Dictionary().entries()}
    if any(i not in ids for i in args.sign_ids):
        parser.error('Unknown sign ID; review actual dictionary assets first')
    path = ROOT / 'data/sentence_rules.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if any(r['id'] == rule['id'] or normalize(r['input']) == normalize(rule['input']) for r in data['rules']):
        parser.error('Rule ID or normalized input already exists; review the existing record explicitly')
    data['rules'].append(rule)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2), encoding='utf-8'); temporary.replace(path)
    print('Recorded the supplied human review. Asset approval remains independently required.')


if __name__ == '__main__':
    main()
