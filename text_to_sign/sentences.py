"""Opt-in, finite sentence orders authored and approved by a human ISL reviewer.

This is deliberately not an automatic English-to-ISL grammar model.
"""
import json
from datetime import date
from time import perf_counter

from .engine import normalize


def validate_rule(rule):
    if not all(isinstance(rule.get(k), str) and rule[k].strip()
               for k in ('id', 'input', 'reviewed_by', 'reviewed_on', 'review_note')):
        raise ValueError('Sentence approval requires an ID, input, named reviewer, date and observations')
    date.fromisoformat(rule['reviewed_on'])
    if rule.get('status') != 'verified' or not normalize(rule['input']):
        raise ValueError('Sentence rule must be verified and have English input')
    ids = rule.get('sign_ids')
    if not isinstance(ids, list) or not ids or len(ids) > 1000 or not all(isinstance(x, str) and x for x in ids):
        raise ValueError('Sentence order must contain 1–1000 explicit sign IDs')


def convert_sentence(bank, text, preview=False):
    started = perf_counter()
    normalized = normalize(text)
    if not normalized or len(normalized.split()) > 200:
        raise ValueError('Please enter 1–200 English words')
    path = bank.root / 'data/sentence_rules.json'
    rules = json.loads(path.read_text(encoding='utf-8'))['rules'] if path.exists() else []
    matches = [r for r in rules if normalize(r.get('input', '')) == normalized]
    if len(matches) > 1:
        raise ValueError('Duplicate sentence rules; resolve the reviewer registry')
    result = {'normalized': normalized, 'sequence': [], 'warnings': [],
              'input_words': len(normalized.split()), 'matched_words': 0,
              'coverage': 0, 'preview': preview, 'elapsed_ms': 0,
              'mode': 'reviewed_sentence'}
    def finish():
        result['elapsed_ms'] = round((perf_counter() - started) * 1000, 2)
        return result
    if not matches:
        result['warnings'] = [{'code': 'UNSUPPORTED_CONSTRUCTION', 'term': normalized,
                              'message': 'No reviewed sentence order exists for this construction. Use dictionary mode for vocabulary practice.'}]
        return finish()
    rule = matches[0]
    validate_rule(rule)
    index = {e['id']: e for e in bank.entries()}
    if any(i not in index or not bank.available(index[i], preview) for i in rule['sign_ids']):
        result['warnings'] = [{'code': 'ASSET_UNAVAILABLE', 'term': normalized,
                              'message': 'The reviewed order contains unavailable or unapproved assets; no partial sentence was emitted.'}]
        return finish()
    result['sequence'] = [{'id': i, 'text': index[i]['text'], 'type': index[i]['type'],
                           'input': normalized, 'url': f'/api/media/{i}',
                           'ready': bank.available(index[i]),
                           'source_url': index[i].get('source_url', ''),
                           'attribution': index[i].get('attribution', '')} for i in rule['sign_ids']]
    result.update(matched_words=result['input_words'], coverage=100, rule_id=rule['id'],
                  reviewed_by=rule['reviewed_by'])
    return finish()
