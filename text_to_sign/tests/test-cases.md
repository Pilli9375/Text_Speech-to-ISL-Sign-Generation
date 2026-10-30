# Browser and functional test matrix — 2026-10-30

Executed against the local FastAPI app in the in-app Chromium browser. Real ISLRTC and ISLAN media were
used in **explicit source-preview mode**. No pending clip was marked READY to make a test pass.

The supplied manual says "24 standardized test cases" but enumerates only T01–T12. T13–T24 below extend
the matrix to cover the agreed full text/speech prototype. Browser results and automated fixture results are distinguished.

| ID | Case | Observed result | Evidence / limit |
| --- | --- | --- | --- |
| T01 | Single supported word | Browser pass | hello loaded; decoded video width 1920 |
| T02 | Case normalization | Browser pass | HELLO normalized to hello |
| T03 | Whitespace | Browser pass | Leading/trailing repeated spaces removed from mixed sentence |
| T04 | Punctuation | Browser pass | HELLO, friend! thank you normalized to hello friend thank you |
| T05 | Phrase precedence | Browser pass | thank you emitted as one clip |
| T06 | Automatic multi-sign playback | Browser pass | hello → friend → thank you reached SEQUENCE COMPLETE |
| T07 | Empty input | Browser pass | Please enter text to convert; textarea focused |
| T08 | Unsupported term | Browser and automated pass | Unknown words use complete alphabet fallback; digits/hyphens and incomplete spellings remain explicit warnings |
| T09 | Missing asset | Browser and automated pass | Diagnostic harness injected a real HTTP 404; warning shown, failed clip skipped, remaining friend clip completed; fixture file removal also tested |
| T10 | Pause/resume | Browser pass | Paused video at 0.2764 seconds; resumed and skipped to friend |
| T11 | New conversion during playback | Browser pass | Active friend playback replaced by water please queue; old queue did not advance |
| T12 | Complete fingerspelling | Browser pass | Real jazz sequence J–A–Z–Z reached SEQUENCE COMPLETE, retaining original J motion; all 26 source letters decoded |
| T13 | Stop | Browser pass | Water sequence stopped and reset to sign 1 |
| T14 | Skip next | Browser pass | hello → friend immediately |
| T15 | Playback speed | Browser pass | Video playbackRate observed as 0.75 |
| T16 | Clear | Browser pass | Input, queue, media, labels and warnings reset; controls disabled |
| T17 | Review gate / explicit preview | Browser pass | Default approved mode excluded hello; opt-in preview admitted pending clip with warning |
| T18 | Library search | Browser pass | Search thank returned one pending phrase entry |
| T19 | Speech audio upload | Browser pass | Uploaded synthetic 6.45-second WAV; expected transcript appeared in textarea |
| T20 | Edit transcript and convert | Browser pass | Edited speech transcript became hello / friend / thank you queue |
| T21 | Recording pipeline | Browser pass with synthetic stream | Actual browser MediaRecorder captured synthetic speech through Web Audio, uploaded WebM and produced the expected editable transcript; no room microphone captured |
| T22 | Microphone permission denial | Browser simulation pass | Injected NotAllowedError; recovery feedback shown; upload/text controls usable; actual OS permission prompt unchanged |
| T23 | Invalid/traversal paths | Automated pass | Relative escape, absolute/Windows paths and unsupported suffixes rejected |
| T24 | Responsive layout | Browser pass | 390×844 viewport; document width 375 ≤ viewport 390; no horizontal overflow; viewport restored afterward |

## Other automated checks

- 69 pytest cases passed, covering engine behavior, review gates, checksum invalidation, malformed inputs, HTTP validation,
  unsupported formats, empty/oversized audio, transcription failures, duration limit and busy-worker lock release.
- Python/API transcription of the synthetic recording succeeded after pinning PyAV to 16.1.0.
- HTTP Range GET for hello returned 206, exactly 1,024 bytes, and Content-Range bytes 0-1023/1690827.
- JavaScript syntax check passed; pip reported no broken requirements.
- Sixteen JavaScript state tests passed, including stale responses/events, permission denial, late microphone acquisition and media failure.
- All 381 final MP4 clips fully decoded (36,985 frames total). Decoding alone is not a browser continuity benchmark.
- A real 5.86-second LibriSpeech utterance produced zero edits across 17 normalized reference words. This is a single-sample smoke test.

No human ISL correctness review, physical room-microphone capture, multi-browser matrix, frame-stall instrumentation,
or representative human-speech WER benchmark has been claimed as complete.

## v1.2 completion regression

69 Python and 16 JavaScript tests pass. New tests cover exact reviewed orders, unsupported constructions, atomic missing-asset behavior, rejected preview exclusion, fixed coverage denominator, metadata consistency, empty/unrepresentative corpus rejection, playback quality accounting and explicit sentence-mode requests. All 518 source clips passed a new full decode. Actual current browser timing evidence is recorded separately; no synthetic tests certify linguistic correctness.
