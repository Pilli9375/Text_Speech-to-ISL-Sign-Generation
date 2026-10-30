# SignBridge 1.1 evaluation — 2026-10-30

The word/phrase library has expanded from **20 to 355 clips**. With all 26 alphabet clips,
the current app has **381 playable source entries**: 339 words, 16 phrases and 26 letters.
The previous 1.0 handover is preserved in evaluation_report_v1.0.md; the figures below supersede its library counts.

## Vocabulary and browsing

The ISLRTC collection was searched across all A–Z folders using exact labels against 699 everyday targets.
490 source labels matched. A balanced selection was made across ten everyday categories, retaining previous
terms and adding five explicitly located pronoun/phrase entries. One oversized clip and one non-video
provider response were excluded and replaced with other exact source terms.

Categories cover greetings, people/family, questions/descriptions, daily actions, food/drink, places/travel,
time/numbers, feelings/health, learning/work, and objects/nature. The library now includes type/category
filters, alias-aware search and 24-card pagination. Words and alphabet letters remain distinct even if
their text is identical, such as the I/Me pronoun asset and the letter I.

## Actual checks

- Full decoding passed for **381/381 clips**, comprising 36,985 frames,
  1,486.91 seconds and 852,302,672 bytes of local media.
- Exact source retrieval passed **355/355** word/phrase queries.
- Warm conversion median: **5.56 ms**; p95: **9.87 ms** over 200 samples.
  This excludes HTTP, video buffering and transcription.
- **59 Python tests and 14 JavaScript tests pass**. New checks cover the word/letter namespace,
  source-labelled aliases, pagination/category/search behavior and exact letter preview.
- Live API examples passed: please give me water; I don't understand; school teacher student book;
  doctor hospital medicine; good afternoon. Source-label I/Me is used for me, without manufacturing a new clip.
- Browser checks confirmed 381 entries, 339/16/26 type counts, page 2 navigation, 39 food/drink entries,
  exact phrase search, and playback of I don't understand as one actual 1,920×1,080 clip.

Full media decode evidence is retained in asset_full_decode_audit_v1.1.json. Startup's --changed-only audit
still verifies every checksum, but reuses the full-decode record when bytes are unchanged. This avoids
decoding hundreds of videos on every launch. Manual audit without that flag always does a full decode.

## Review, scope and delivery

All 381 clips are available through explicit source-preview mode. **0 clips are independently ISL-reviewed/READY**;
human review remains required for approved-mode playback. No reviewer records or sign-correctness metrics
were invented. Dictionary clip sequencing does not translate grammatical ISL.

Source terms remain separate: ISLRTC words/phrases use the official non-commercial/acknowledgement conditions;
ISLAN alphabet derivatives retain CC BY 4.0 attribution, source and modification notices. Provenance and
checksums are recorded in source_manifest.json and asset_register.csv.

The local app runs at http://127.0.0.1:8000. Refresh the browser to load the new library. The v1.1 handover
ZIP includes all 381 playback clips; model weights, raw source photos, environments and recordings remain excluded.
Code remains on feature/text-to-sign; no GitHub push or public deployment was performed.
