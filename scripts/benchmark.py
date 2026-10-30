"""Measure fixed-target coverage and optional independently labelled held-out corpora.

No missing benchmark is reported as passing. Corpus audio is local and never uploaded.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from text_to_sign.engine import Dictionary, ROOT, normalize
from text_to_sign.sentences import convert_sentence


def words(text):
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower().replace('’', "'"))


def edits(reference, actual):
    row = list(range(len(actual) + 1))
    for i, left in enumerate(reference, 1):
        current = [i]
        for j, right in enumerate(actual, 1):
            current.append(min(current[-1] + 1, row[j] + 1, row[j-1] + (left != right)))
        row = current
    return row[-1]


def coverage(bank):
    groups = json.loads((bank.root / 'data/vocabulary_targets.json').read_text(encoding='utf-8'))
    targets = {normalize(t) for group in groups.values() for t in group}
    entries = [e for e in bank.entries() if e['type'] != 'alphabet']
    direct = {normalize(e['text']) for e in entries if bank.available(e, True)}
    approved = {normalize(e['text']) for e in entries if bank.available(e)}
    aliases = {normalize(a) for e in entries if bank.available(e) for a in e.get('aliases', [])}
    direct_count, approved_count = len(targets & direct), len(targets & approved)
    return dict(target_terms=len(targets), exact_source_matches=direct_count,
                exact_source_percent=round(100 * direct_count / len(targets), 2),
                approved_exact_matches=approved_count,
                approved_exact_percent=round(100 * approved_count / len(targets), 2),
                approved_alias_only_matches=sorted((targets & aliases) - approved),
                missing_exact_source=sorted(targets - direct),
                passes_over_85_percent=approved_count / len(targets) > .85,
                note='Fixed everyday target list; alphabet fallback and aliases excluded from exact coverage.')


def load_corpus(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    rows = data['samples']
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate evaluation sample IDs')
    if not rows:
        raise ValueError('Empty corpus; collect actual independently labelled samples')
    for r in rows:
        if r.get('split') != 'test' or not r.get('reference_reviewed_by', '').strip():
            raise ValueError('Every evaluation reference needs an independent reviewer and test split')
    return rows


def speech_benchmark(path, transcribe):
    rows = load_corpus(path)
    results = []
    for row in rows:
        for field in ('speaker_id', 'accent', 'condition', 'reference', 'audio', 'source', 'usage_permission'):
            if not row.get(field):
                raise ValueError(f'Missing speech field: {field}')
        audio = (path.parent / row['audio']).resolve()
        if audio.stat().st_size > 20 * 1024 * 1024:
            raise ValueError('Evaluation recording exceeds the app 20 MB limit')
        result = transcribe(audio)
        reference = words(row['reference'])
        if not reference:
            raise ValueError('Empty reference transcript')
        results.append(dict(id=row['id'], speaker_id=row['speaker_id'], accent=row['accent'],
                            condition=row['condition'], words=len(reference),
                            edits=edits(reference, words(result['text'])), observed=result['text'],
                            elapsed_ms=result.get('elapsed_ms')))
    total = sum(r['words'] for r in results)
    errors = sum(r['edits'] for r in results)
    representative = (len(rows) >= 40 and total >= 400 and len({r['speaker_id'] for r in rows}) >= 5
                      and {'clean', 'noisy'} <= {r['condition'] for r in rows}
                      and 'Indian English' in {r['accent'] for r in rows})
    groups = {}
    for field in ('speaker_id', 'accent', 'condition'):
        groups[field] = {}
        for value in sorted({r[field] for r in results}):
            subset = [r for r in results if r[field] == value]
            n = sum(r['words'] for r in subset)
            groups[field][value] = dict(samples=len(subset), words=n, wer_percent=round(100 * sum(r['edits'] for r in subset) / n, 2))
    return dict(samples=len(rows), reference_words=total, edits=errors, groups=groups,
                wer_percent=round(100 * errors / total, 2), representative=representative,
                passes=representative and errors / total < .12, results=results,
                normalization='Lowercase, punctuation ignored; no lexical substitutions.')


def sentence_benchmark(bank, path):
    rows = load_corpus(path)
    results = []
    for row in rows:
        result = convert_sentence(bank, row['input'])
        actual = [e['id'] for e in result['sequence']]
        expected = row['expected_sign_ids']
        if not expected or not isinstance(row.get('grammatical_acceptable'), bool):
            raise ValueError('Sentence references require explicit order and human grammatical judgment')
        results.append(dict(id=row['id'], actual=actual, expected=expected,
                            correct=actual == expected and row['grammatical_acceptable'],
                            retrieved=actual == expected))
    correct = sum(r['correct'] for r in results)
    return dict(samples=len(rows), results=results, correctness_percent=100 * correct / len(rows),
                passes=correct / len(rows) > .9,
                limitation='Finite reviewed constructions only; human grammatical judgment required.')


def lookup_benchmark(bank, path):
    rows = load_corpus(path)
    results = []
    for row in rows:
        expected = row['expected_sign_ids']
        if not expected:
            raise ValueError('Lookup references need nonempty independently verified sign IDs')
        actual = [e['id'] for e in bank.convert(row['input'], fingerspell=False)['sequence']]
        results.append(dict(id=row['id'], actual=actual, expected=expected, correct=actual == expected))
    correct = sum(r['correct'] for r in results)
    return dict(samples=len(rows), correct=correct, accuracy_percent=100 * correct / len(rows),
                passes=correct == len(rows), results=results)


def browser_benchmark(data):
    runs = data['runs']
    attempts = [r for r in runs if r.get('started_playback')]
    completed = [r for r in attempts if r['outcome'] == 'completed' and r['media_errors'] == 0
                 and r.get('ended_clips') == r.get('clip_count') and not r.get('manual_navigation')]
    loads = [r['submit_to_loaded_ms'] for r in runs if r.get('submit_to_loaded_ms') is not None]
    gaps = [g for r in runs for g in r.get('transition_gaps_ms', [])]
    stalls = sum(r.get('stall_count', 0) for r in attempts)
    return dict(conversions=len(runs), playback_attempts=len(attempts), successful_continuous=len(completed),
                reliability_percent=100 * len(completed) / len(attempts) if attempts else None,
                loaded_samples=len(loads), maximum_submit_to_loaded_ms=max(loads) if loads else None,
                latency_under_300ms=all(x < 300 for x in loads) if loads else None,
                stall_count=stalls, maximum_transition_gap_ms=max(gaps) if gaps else None,
                dropped_video_frames=sum(r.get('dropped_video_frames', 0) for r in attempts),
                zero_observed_stalls=stalls == 0 if attempts else None,
                note='Browser waiting events measure observed buffering, not proof of zero decoder frame stalls. User pauses excluded.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--speech-manifest', type=Path)
    parser.add_argument('--sentence-manifest', type=Path)
    parser.add_argument('--lookup-manifest', type=Path)
    parser.add_argument('--browser-report', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/completion_metrics.json')
    args = parser.parse_args()
    bank = Dictionary()
    report = dict(vocabulary=coverage(bank), speech=None, sentence=None, lookup=None, browser=None,
                  status='Incomplete until human review and missing evaluations are supplied')
    if args.speech_manifest:
        from text_to_sign.speech import transcribe
        report['speech'] = speech_benchmark(args.speech_manifest.resolve(), transcribe)
    if args.sentence_manifest:
        report['sentence'] = sentence_benchmark(bank, args.sentence_manifest.resolve())
    if args.lookup_manifest:
        report['lookup'] = lookup_benchmark(bank, args.lookup_manifest.resolve())
    if args.browser_report:
        report['browser'] = browser_benchmark(json.loads(args.browser_report.read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'vocabulary'}, indent=2))
    print('Vocabulary:', report['vocabulary']['exact_source_matches'], '/', report['vocabulary']['target_terms'],
          'source matches;', report['vocabulary']['approved_exact_matches'], 'approved')


if __name__ == '__main__':
    main()
