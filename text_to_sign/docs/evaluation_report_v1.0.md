# SignBridge 1.0 evaluation and handover — 2026-10-30

## A. Dataset audit summary

This standalone project started from the user's empty repository. No legacy recognition models,
landmark files or pre-existing ISL datasets were supplied or modified.

The playback collection now contains 46 real source assets:

- 20 word/phrase videos from the official ISLRTC dictionary collection linked in its FAQ.
- 26 signer-1 double-handed alphabet assets from ISLAN V1, by Elakkiya R and Rajalakshmi E (2021),
  DOI 10.17632/rc349j45m5.1, CC BY 4.0.
- All final clips fully decoded: **1,960 frames, 93.41 seconds, 48,144,793 bytes**.
- ISLAN stills were rotated upright, resized and encoded as one-second H.264 clips. Original J motion
  is retained unchanged. Double-handed Z is static in this author-labelled collection. No gesture was synthesized.

See dataset_audit.md, asset_audit.json, data/alphabet_manifest.json and data/source_manifest.json.

## B. Asset registry and verification

asset_register.csv records source/member paths, original/derived checksums, attribution, usage terms,
transformation notes and reviewer fields. vocabulary_inventory.csv includes the 20 terms and all 26 letters.
Contact sheets were inspected for actual footage, visible hands and upright orientation. This is not an ISL-fluent semantic review.

| Readiness measure | Result |
| --- | --- |
| Word/phrase source availability | 20/20 planned terms |
| Alphabet source availability | 26/26 letters |
| Total source-preview availability | 46/46 assets |
| Independently reviewed READY assets | 0/46 |
| Approved word vocabulary coverage | 0%; review pending |

Approved mode requires every check and a real named/dated ISL review. Explicit source-preview mode makes
the complete sourced prototype usable while preserving this distinction. Changed clip bytes immediately
invalidate playback eligibility; cached dictionary lookups do not bypass checksum checks.

## C. Functional implementation

- English normalization, longest phrase matching at each offset, word lookup and atomic A–Z fallback.
- Spelling/word labels, source links, sequence counters, unsupported-term and media-error feedback.
- Responsive text/speech workspace, explicit preview onboarding and searchable 46-entry library.
- Browser playback with next-clip preloading, automatic transitions, pause/resume, stop/reset, next,
  speed changes and queue selection. Failed media are reported and skipped during active playback;
  startup/buffering timeouts are bounded.
- Generation and media-element isolation prevent stale events from changing newer sequences.
- Recording/uploads use local faster-whisper base.en CPU INT8. Editable transcripts require explicit
  conversion. Typing, clear, tab changes and Cancel transcription protect against stale speech results.
- Audio is bounded to 60 seconds / 20 MB, one ASR job at a time, with temporary-file cleanup.
- Startup installs changed dependencies, restores recorded source media, and fully audits them.
  The alphabet importer fetches selected ZIP byte ranges rather than the full 1.4-GB archive.
- A handover packager includes code, provenance and validated normalized media. Raw photographs,
  model weights, test recordings, environments, node_modules and Git metadata are excluded.
- Windows/Linux CI configuration is included. Remote CI is not claimed until a push actually runs it.

## D. Measured checks and performance

| Measurement | Observed result | Scope |
| --- | --- | --- |
| Python tests | 58 pass | Engine, API, integrity, input/audio boundaries and ASR locking |
| JavaScript state tests | 12 pass | JSDOM adapters: cancellation, late responses/events, recording denial and media failures |
| Exact source retrieval | 20/20 expected IDs | Label mapping; not sign-language accuracy |
| Warm lookup median / p95 | 4.82 / 5.75 ms | 200 local conversions; excludes ASR, HTTP and buffering |
| Alphabet playback | jazz → J–A–Z–Z completed | Real media; original moving J preserved |
| Actual MediaRecorder | Browser PASS | Synthetic speech stream → actual WebM recording → upload → ASR → editable transcript |
| Permission recovery | Browser simulation PASS | No physical microphone permission requested or changed |
| Missing media | Browser PASS with real HTTP 404 | Warning shown; remaining friend video completed |
| Synthetic WAV ASR | Expected transcript reproduced | 6.45-second generated sample; warm API observation 609 ms |
| Human-speech smoke | 0 edits / 17 normalized reference words | One clean 5.86-second LibriSpeech utterance; Mr. normalized to mister |
| Human-speech ASR latency | 3,632 ms | Separate process with cached weights, including model initialization |
| Media byte ranges | HTTP 206 / exactly 1,024 bytes | hello.mp4 partial request |
| Mobile overflow | None at 390×844 | Document width 375 px ≤ viewport 390 px; temporary viewport restored |

Machine evidence: evaluation_metrics.json, speech_smoke_result.json, browser_integration_result.json
and human_speech_smoke.json. Browser/fixture distinctions: ../tests/test-cases.md.

The real speech sample is from LibriSpeech (Panayotov, Chen, Povey and Khudanpur, 2015; CC BY 4.0),
https://www.openslr.org/12. Its audio mirror, reference source, checksum, normalization and output are recorded.
**One clean sample does not establish WER across accents, microphones, noise or the intended user population.**

No grammatical sequence correctness, human sign-accuracy percentage, zero-frame-stall metric or population-wide
reliability has been fabricated. Roadmap thresholds remain targets pending representative evaluation.

## E. Repository delivery

Remote: https://github.com/Pilli9375/Text_Speech-to-ISL-Sign-Generation.git.
Branch: feature/text-to-sign. The repository started empty; no legacy checksum/model preservation claim applies.
All changes are inside the selected project. Unrelated Capstone files were left untouched.

Source changes are reviewable locally. No remote push, PR, paid service or public deployment was performed.
Media and speech weights are excluded from ordinary Git history. The handover ZIP includes the 46
source-preview media files with their separate source conditions and a SHA-256 sidecar.

## F. Remaining external validation and scope

The agreed dictionary-based software prototype is implemented and tested. The outstanding sign-language
verification is an external human task: an ISL-fluent reviewer must inspect actual meanings, handshape,
movement and context, then use scripts/review_asset.py to record real evidence. Software tests cannot
truthfully replace this review, and no reviewer names or approval records were invented.

Physical microphone capture remains for the user to exercise. The actual browser recording pipeline and
permission-denial recovery were tested without recording the room. Representative speech samples and
ISL-fluent user evaluation remain necessary before broader deployment claims.

Clip sequencing follows dictionary matches and English input order. It does not translate grammatical ISL,
facial expressions or spatial syntax and does not synthesize avatar movement.

## G. Startup, restoration and packaging

Double-click start.bat, or run powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1.
Open http://127.0.0.1:8000. Choose **Use source preview**, then try hello friend, thank you or jazz.
For speech, record/upload, review/edit the transcript, then explicitly convert it.

The launcher restores dependencies/assets and audits them. The handover ZIP includes normalized media,
so its startup does not need raw source archives. First speech-model download still needs internet;
cached ASR and local playback work afterward without a hosted transcription service.

Run scripts/setup_project.py --dev with the venv interpreter for developer setup. Run pytest -q and
npm ci followed by npm test for checks. scripts/package_release.py creates the handover ZIP and checksum.
The README documents attribution, review procedure, diagnostic harness and configuration.
