import csv
import hashlib
import json

import pytest

from scripts.benchmark import browser_benchmark, coverage, edits, speech_benchmark
from scripts.export_metadata import export
from text_to_sign.engine import Dictionary
from text_to_sign.sentences import convert_sentence


@pytest.fixture
def corpus_bank(tmp_path):
    (tmp_path / 'data').mkdir(); (tmp_path / 'docs').mkdir()
    data = b'synthetic fixture, not sign media'
    entries = []
    for text in ('i', 'water', 'need'):
        path = tmp_path / f'signs/words/{text}.mp4'
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        entries.append(dict(id=text, text=text, type='word', file=f'signs/words/{text}.mp4',
                            status='READY', reviewed_by='SYNTHETIC FIXTURE', reviewed_on='2026-10-30',
                            source_url='https://example.org/fixture', attribution='Synthetic fixture',
                            sha256=hashlib.sha256(data).hexdigest(),
                            checks=dict(playable=True, label_checked=True, isl_reviewed=True, usage_approved=True)))
    (tmp_path / 'data/signs.json').write_text(json.dumps(dict(entries=entries)))
    (tmp_path / 'data/vocabulary_targets.json').write_text(json.dumps(dict(test=['i', 'water', 'need', 'hello'])))
    (tmp_path / 'data/sentence_rules.json').write_text(json.dumps(dict(rules=[dict(
        id='fixture', input='i need water', sign_ids=['i', 'water', 'need'], status='verified',
        reviewed_by='SYNTHETIC FIXTURE', reviewed_on='2026-10-30', review_note='Not a linguistic claim')])))
    return Dictionary(tmp_path)


def test_reviewed_order_and_atomic_missing_asset(corpus_bank):
    result = convert_sentence(corpus_bank, 'I need water')
    assert [e['id'] for e in result['sequence']] == ['i', 'water', 'need']
    (corpus_bank.root / 'signs/words/need.mp4').unlink()
    assert convert_sentence(corpus_bank, 'I need water')['sequence'] == []


def test_no_grammar_guess_for_unsupported_construction(corpus_bank):
    result = convert_sentence(corpus_bank, 'water please')
    assert result['sequence'] == []
    assert result['warnings'][0]['code'] == 'UNSUPPORTED_CONSTRUCTION'


def test_unreviewed_rule_rejected(corpus_bank):
    path = corpus_bank.root / 'data/sentence_rules.json'
    data = json.loads(path.read_text()); data['rules'][0]['reviewed_by'] = ''
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError): convert_sentence(corpus_bank, 'i need water')


def test_rejection_excludes_even_source_preview(corpus_bank):
    e = corpus_bank.entries()[0]
    e['status'] = 'REJECTED'
    assert not corpus_bank.available(e, preview=True)


def test_coverage_denominator_is_fixed_targets(corpus_bank):
    result = coverage(corpus_bank)
    assert result['target_terms'] == 4
    assert result['approved_exact_percent'] == 75
    assert not result['passes_over_85_percent']


def test_metadata_matches_registry_without_inventing_approval(corpus_bank):
    path = corpus_bank.root / 'data/signs.json'
    data = json.loads(path.read_text()); data['entries'][0]['status'] = 'PLAYABLE'
    path.write_text(json.dumps(data))
    assert export(corpus_bank.root) == 3
    with (corpus_bank.root / 'data/metadata/sign_dictionary.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert rows[0]['status'] == 'pending' and rows[0]['verified_by'] == ''
    assert rows[1]['status'] == 'verified'


def test_weighted_word_errors():
    assert edits(['a', 'b', 'c'], ['a', 'z']) == 2


def test_one_clean_sample_cannot_pass_representative_wer(tmp_path):
    path = tmp_path / 'corpus.json'
    (tmp_path / 'fixture.wav').write_bytes(b'fixture')
    path.write_text(json.dumps(dict(samples=[dict(id='fixture', split='test', reference_reviewed_by='Fixture',
        speaker_id='fixture', accent='Indian English', condition='clean', reference='hello water',
        audio='fixture.wav', source='Synthetic unit fixture', usage_permission='Test fixture')])))
    result = speech_benchmark(path, lambda audio: dict(text='hello water', elapsed_ms=1))
    assert result['wer_percent'] == 0
    assert not result['representative'] and not result['passes']


def test_empty_corpus_fails_instead_of_passing(tmp_path):
    path = tmp_path / 'corpus.json'; path.write_text('{"samples": []}')
    with pytest.raises(ValueError): speech_benchmark(path, lambda _: {})


def test_failed_or_partial_playback_is_not_reliable_success():
    runs = [dict(started_playback=True, outcome='completed', media_errors=0,
                 clip_count=2, ended_clips=2, submit_to_loaded_ms=12, stall_count=0),
            dict(started_playback=True, outcome='completed', media_errors=1,
                 clip_count=2, ended_clips=1, submit_to_loaded_ms=400, stall_count=1)]
    result = browser_benchmark(dict(runs=runs))
    assert result['reliability_percent'] == 50
    assert not result['latency_under_300ms']
    assert not result['zero_observed_stalls']
