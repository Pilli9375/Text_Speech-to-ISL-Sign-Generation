# SignBridge v1.2 engineering handover — 2026-10-30

The local dictionary prototype and completion tooling are implemented. Full PDF compliance remains incomplete:
human asset/order review, representative evaluation and authenticated remote delivery are independent outstanding conditions.

## A. Dataset audit summary

The user selected a from-scratch repository. No RealSign, 29-class isolated-word or continuous dataset,
legacy recognition endpoints, models or landmark arrays were supplied. Their reuse and checksum preservation
are N/A, not successful inspections of unavailable datasets. Unrelated nearby Capstone files were left untouched.

The current collection contains **518 real source assets**: **476 words,
16 phrases and 26 letters**. Every clip passed a new full decode:
54,832 frames, 2,202.15 seconds,
1,252,331,796 bytes. See asset_full_decode_audit_v1.2.json.
The source discovery exhausted the current exact-label matches within the recorded targets and exclusions.
Oversized/non-video provider responses were excluded explicitly; no missing file is counted as usable.

## B. Verified asset registry

Canonical signs.json drives source metadata, checksums, the review worklist and generated roadmap CSV
data/metadata/sign_dictionary.csv. The CSV's pending/verified state never substitutes for human sign approval.
All 518 clips remain **PLAYABLE, not READY**: zero semantic label checks and zero ISL-fluent approvals.
Usage/provenance checks are recorded separately. A review CLI supports actual approval and rejection;
rejected media are excluded from preview as well as approved mode. Changed media invalidate prior checksums.

ISLRTC words/phrases retain their source, attribution and recorded non-commercial/acknowledgement conditions.
ISLAN V1 alphabet assets retain CC BY 4.0 attribution, original/derived hashes and transformation notices.
Twenty-five source stills are upright timed clips; original J motion is retained. Static-letter adequacy still needs review.

## C. Functional features implemented

- Phrase-first English dictionary retrieval, complete-word alphabet fallback, safe paths and explicit unsupported terms.
- Responsive text/speech workspace, editable local ASR transcripts, explicit conversion, library filters/search/pagination.
- Sequential video controls, next preloading, cancellation isolation, timeout/missing-media recovery and attribution.
- Checksum verification before server traffic reduces first-request work; modified media are still rechecked.
- Opt-in exact reviewed-construction API/UI with atomic asset gating; unsupported constructions never get guessed grammar.
  The rule registry is EMPTY pending actual ISL-fluent authoring; general grammatical translation remains unimplemented.
- Required CSV export, reviewer worklist, held-out corpus templates, corpus/lookup/order/browser benchmark tooling.
- In-memory browser quality export contains timings/outcomes without text/audio; at most 200 attempts are retained.
- Windows bootstrap, source restoration, CI configuration, release packaging and fresh-folder validation tool.

## D. Measured performance metrics

| Measure | Observed evidence / limitation |
| --- | --- |
| Code checks | 69 Python and 16 JavaScript tests pass; syntax/diff checks pass |
| Exact source retrieval | 492/492 expected IDs; not independent semantic accuracy |
| Warm local lookup | Median 5.90 ms, p95 6.21 ms over 200 samples; excludes HTTP/media/ASR |
| Fixed source target coverage | 488/699 = 69.81%; alphabet and aliases excluded |
| Approved exact target coverage | 0/699 = 0.0%; >85% target NOT MET |
| Remaining source target mappings | At least 107 more exact target mappings to reach 595, assuming retained mappings pass review |
| Verified lookup / grammatical correctness | Not established; real independent references and approved assets/orders pending |
| Representative WER <12% | Not established; existing zero-error 17-word human utterance is one clean smoke sample only |
| Physical microphone / cross-browser matrix | Pending; prior actual MediaRecorder test used a synthetic stream |

Actual browser sample summary (see browser_quality_v1.2.json and completion_metrics.json):

```json
{
  "conversions": 4,
  "playback_attempts": 4,
  "successful_continuous": 4,
  "reliability_percent": 100.0,
  "loaded_samples": 4,
  "maximum_submit_to_loaded_ms": 87.20000000298023,
  "latency_under_300ms": true,
  "stall_count": 0,
  "maximum_transition_gap_ms": 4.5,
  "dropped_video_frames": 0,
  "zero_observed_stalls": true,
  "note": "Browser waiting events measure observed buffering, not proof of zero decoder frame stalls. User pauses excluded."
}
```

Initial instrumentation recorded one 585.8-ms alphabet load during concurrent full media auditing.
Startup checksum prewarming was added and the affected paths rechecked with the audit finished; original evidence
is retained in browser_quality_v1.2.initial.json. Small local samples do not establish latency or zero stalls universally.
User pauses, cancellations, failed clips and successful continuous attempts are distinguished by the evaluator.

Representative defaults: at least 40 held-out utterances, 400 reference words, five speakers, clean/noisy groups
and Indian English. These are project defaults, not PDF-prescribed sample sizes. Missing evaluations stay null;
empty/unreviewed corpora fail rather than become passing scores. See reviewer_and_evaluation_guide.md.

## E. Git preservation and delivery

Branch: feature/text-to-sign. A local main baseline exists for a reviewable PR. Code and lightweight metadata
are tracked; media, model weights, raw originals, recordings, environments and artifacts are excluded.
Report generation observed local revision b3b3857; the final delivery revision is in Git history.
Current remote-delivery state: Blocked: GitHub HTTPS credentials unavailable; baseline push failed.
No legacy checksum or recognition-endpoint preservation result is invented for this initially empty repository.

## F. Technical limitations and remaining work

All 518 clips require named human semantic/ISL review. Additional verified target vocabulary,
reviewer-authored sentence constructions, held-out grammatical assessment, representative human speech,
physical microphone and wider browser/hardware evaluation remain necessary. Finite construction retrieval is
not a general English-to-ISL grammar model, spatial language system or avatar synthesizer.
The manual's dictionary-only baseline and roadmap's grammar extension are tracked separately in
pdf_requirements_checklist.md. The >85%, 100% verified lookup, >90% grammar and <12% representative WER targets
cannot truthfully be signed off from source labels or software tests.

## G. Startup and operational instructions

Double-click start.bat, then open http://127.0.0.1:8000. Initial dependencies, source restoration and first speech-model
download require connectivity. Cached media and model weights support later local use. Choose source preview
while human approval is pending; enter text or record/upload, edit the transcript, then explicitly convert.

Run scripts/verify_project.py for code checks; scripts/audit_assets.py for full decoding;
scripts/benchmark.py for fixed-target and supplied held-out evaluation; and scripts/package_release.py for
artifacts/SignBridge-1.2.zip. Run scripts/validate_release.py on that archive for fresh-folder HTTP verification.
Its --speech-sample option verifies cached ASR with provider offline flags. Shared installed dependencies are used;
this does not claim a fresh OS/dependency installation or physical network isolation.
release_validation.json and the archive's .validation.json sidecar identify the tested ZIP digest. That report is
excluded from the ZIP to avoid self-referential checksums. Archive bytes and code are distinct from Git media tracking.
