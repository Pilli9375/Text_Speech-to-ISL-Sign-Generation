import json
import hashlib
from pathlib import Path

import pytest

from text_to_sign.engine import Dictionary, is_ready, normalize, safe_asset


def entry(text, kind='word', ready=True):
    return {'id': text.replace(' ', '_'), 'text': text, 'type': kind,
            'file': f'signs/{kind}/{text.replace(" ", "_")}.mp4',
            'status': 'READY' if ready else 'PLAYABLE', 'reviewed_by': 'Test fixture reviewer' if ready else '',
            'reviewed_on': '2026-10-30' if ready else '', 'source_url': 'https://example.org/test-fixture',
            'attribution': 'Synthetic test fixture; not a real sign',
            'sha256': hashlib.sha256(b'fixture-placeholder-not-real-media').hexdigest(),
            'checks': {'playable': True, 'usage_approved': True, 'label_checked': ready, 'isl_reviewed': ready}}


@pytest.fixture
def bank(tmp_path):
    items = [entry('hello'), entry('friend'), entry('thank you', 'phrase'), entry('thank'), entry('you'),
             entry('water'), entry('pending', ready=False), entry('good morning', 'phrase')]
    items.extend(entry(c, 'alphabet') for c in 'cat')
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data/signs.json').write_text(json.dumps({'entries': items}))
    for item in items:
        file = tmp_path / item['file']; file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b'fixture-placeholder-not-real-media')
    return Dictionary(tmp_path)


@pytest.mark.parametrize('raw,expected', [(' HELLO ', 'hello'), ('hello,world!', 'hello world'),
    ('thank\n\tyou', 'thank you'), ('well-known', 'well-known'), ("don't", 'dont'),
    ('hello—friend', 'hello friend'), ('...hello...', 'hello')])
def test_normalization(raw, expected):
    assert normalize(raw) == expected


def test_single_word(bank):
    assert [e['text'] for e in bank.convert('HELLO')['sequence']] == ['hello']


def test_phrase_precedence_at_each_position(bank):
    assert [e['text'] for e in bank.convert('hello thank you friend')['sequence']] == ['hello', 'thank you', 'friend']


def test_multiple_phrases(bank):
    assert [e['text'] for e in bank.convert('good morning thank you')['sequence']] == ['good morning', 'thank you']


def test_full_fingerspelling(bank):
    result = bank.convert('cat')
    assert [e['text'] for e in result['sequence']] == list('cat')
    assert result['coverage'] == 100


@pytest.mark.parametrize('text', ['cab', 'cat2', 'cat-cat'])
def test_never_partial_spellings(bank, text):
    result = bank.convert(text)
    assert result['sequence'] == []
    assert result['warnings'][0]['term'] == text


def test_fingerspelling_disabled(bank):
    assert bank.convert('cat', fingerspell=False)['sequence'] == []


def test_unknown_warning_and_coverage(bank):
    result = bank.convert('hello unknown friend')
    assert result['coverage'] == 67
    assert [e['text'] for e in result['sequence']] == ['hello', 'friend']
    assert result['warnings'][0]['code'] == 'UNSUPPORTED_TERM'


def test_missing_media(bank):
    (bank.root / 'signs/word/hello.mp4').unlink()
    result = bank.convert('hello')
    assert result['sequence'] == []
    assert result['warnings'][0]['code'] == 'ASSET_UNAVAILABLE'


def test_pending_excluded_by_default(bank):
    assert bank.convert('pending')['sequence'] == []


def test_preview_explicit(bank):
    result = bank.convert('pending', preview=True)
    assert len(result['sequence']) == 1
    assert result['sequence'][0]['ready'] is False


def test_ready_requires_every_check():
    item = entry('hello'); item['checks']['isl_reviewed'] = False
    assert not is_ready(item)
    item['checks']['isl_reviewed'] = True; item['reviewed_by'] = ''
    assert not is_ready(item)


def test_preview_requires_usage_and_provenance(bank):
    data_path = bank.root / 'data/signs.json'
    data = json.loads(data_path.read_text())
    for item in data['entries']:
        item['checks']['usage_approved'] = False
    data_path.write_text(json.dumps(data))
    assert bank.convert('pending', preview=True)['sequence'] == []


@pytest.mark.parametrize('text', ['', ' \n ', '!!!', 'नमस्ते', 'café'])
def test_invalid_input(bank, text):
    with pytest.raises(ValueError): bank.convert(text)


def test_word_limit(bank):
    with pytest.raises(ValueError): bank.convert('hello ' * 201)


@pytest.mark.parametrize('path', ['../secret.mp4', 'signs/../../secret.mp4', 'C:/secret.mp4',
    '/signs/test.mp4', 'signs\\hello.mp4', 'signs/hello.html', 'web/app.js'])
def test_asset_paths_reject_escape(path, tmp_path):
    with pytest.raises(ValueError): safe_asset(path, tmp_path)


def test_duplicate_keys_rejected(bank):
    path = bank.root / 'data/signs.json'; data = json.loads(path.read_text())
    data['entries'].append(entry('HELLO')); path.write_text(json.dumps(data))
    with pytest.raises(ValueError): bank.entries()


def test_inventory_counts(bank):
    result = bank.inventory()
    assert result['previewable'] == len(result['entries'])
    assert result['ready'] == result['total'] - 1


def test_changed_clip_loses_eligibility_without_rerunning_audit(bank):
    assert bank.convert('hello')['sequence']
    (bank.root / 'signs/word/hello.mp4').write_bytes(b'replacement-media')
    assert bank.convert('hello')['sequence'] == []
    assert bank.convert('hello', preview=True)['sequence'] == []


def test_duplicate_ids_rejected(bank):
    path = bank.root / 'data/signs.json'; data = json.loads(path.read_text())
    data['entries'][1]['id'] = data['entries'][0]['id']; path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='unique'): bank.entries()


def test_invalid_alphabet_label_rejected(bank):
    path = bank.root / 'data/signs.json'; data = json.loads(path.read_text())
    data['entries'].append(entry('ab', 'alphabet')); path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='single English letter'): bank.entries()


def test_fingerspelling_queue_bound(bank):
    with pytest.raises(ValueError, match='1,000 signs'):
        bank.convert('c' * 1001)


def test_word_and_letter_with_same_label_stay_distinct(bank):
    word = entry('i'); word['id'] = 'word_i'; word['aliases'] = ['me']
    letter = entry('i', 'alphabet')
    path = bank.root / 'data/signs.json'; data = json.loads(path.read_text())
    data['entries'].extend([word, letter]); path.write_text(json.dumps(data))
    for item in (word, letter):
        media = bank.root / item['file']; media.parent.mkdir(parents=True, exist_ok=True)
        media.write_bytes(b'fixture-placeholder-not-real-media')
    assert bank.convert('i')['sequence'][0]['id'] == 'word_i'
    assert bank.convert('me')['sequence'][0]['id'] == 'word_i'
    assert [item['id'] for item in bank.convert('it')['sequence']] == ['i', 't']
