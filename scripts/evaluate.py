"""Measure actual dictionary retrieval; do not substitute this for linguistic review."""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from text_to_sign.engine import Dictionary, ROOT

bank = Dictionary()
manifest = json.loads((ROOT / 'data/source_manifest.json').read_text())
terms = manifest['planned_terms']
expected = {item['text']: item.get('id', item['text'].replace(' ', '_')) for item in manifest['candidates'] if item.get('type') != 'alphabet'}
inventory = bank.inventory()
word_entries = [e for e in inventory['entries'] if e['type'] != 'alphabet']
preview_words = sum(e['previewable'] for e in word_entries)
ready_words = sum(e['ready'] for e in word_entries)
rows, times = [], []
for term in terms:
    result = bank.convert(term, preview=True)
    expected_id = expected[term]
    rows.append({'query': term, 'expected_ids': [expected_id],
                 'actual_ids': [e['id'] for e in result['sequence']],
                 'passed': [e['id'] for e in result['sequence']] == [expected_id]})
for i in range(200):
    result = bank.convert('hello friend thank you water please', preview=True)
    times.append(result['elapsed_ms'])
report = {'planned_terms': len(terms), 'source_preview_terms': preview_words,
          'approved_terms': ready_words, 'approved_coverage_percent': ready_words / len(terms) * 100,
          'source_preview_coverage_percent': preview_words / len(terms) * 100,
          'alphabet_previewable': inventory['alphabet_previewable'], 'alphabet_ready': inventory['alphabet_ready'],
          'retrieval_queries': rows, 'retrieval_passed': sum(r['passed'] for r in rows),
          'lookup_sample_count': len(times), 'lookup_median_ms': statistics.median(times),
          'lookup_p95_ms': sorted(times)[int(len(times) * .95) - 1],
          'notes': 'Warm local dictionary lookup only. Excludes browser load, video buffers and ASR. Label/ISL correctness not measured.'}
(ROOT / 'docs/evaluation_metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'retrieval_queries'}, indent=2))
