# SignBridge implementation plan

Scope agreed: a from-scratch local English text and speech to ISL dictionary prototype.
Repository: https://github.com/Pilli9375/Text_Speech-to-ISL-Sign-Generation
Workspace: C:\Pilli\Text_Speech-to-ISL Sign Generation

## Decisions

- FastAPI serves the JSON API, browser UI and allowlisted local videos.
- Semantic HTML, CSS and modular JavaScript keep playback in the browser.
- faster-whisper base.en runs on CPU with INT8 inference; model download is required once.
- One canonical signs.json dictionary; CSVs are generated audit/provenance reports.
- Longest available phrase at each offset, then word, then atomic complete-word fingerspelling.
- Independent ISL review remains mandatory for READY status. Source preview is a separate explicit mode.
- Clip sequencing does not claim to translate grammatical ISL. No model training or avatar synthesis.
- No legacy recognition code or three pre-existing ISL datasets exist in this new project.

## Milestones

1. Establish Git checkout, environment, directory structure and Windows launcher.
2. Discover and download 20 initial official dictionary word/phrase clips with attribution.
3. Decode every clip, record actual metadata and checksums, and prepare review records.
4. Implement retrieval, responsive UI, playback controls, cancellation and diagnostic feedback.
5. Implement microphone/audio uploads, local ASR and editable transcript confirmation.
6. Run automated engine/API checks, real browser checks, asset audit and real ASR smoke test.
7. Deliver startup, audit, provenance, test results, limitations and remaining review work.

## Remaining external dependencies

- A named ISL-fluent reviewer must check each actual clip's meaning, handshape, movement and context.
- The A–Z source set is now imported and plays in explicit source-preview mode. Independent review is still needed for READY status.
- Representative human recordings are needed for defensible word-error-rate measurement.

No production approval, sign-correctness metric or performance target is inferred from passing software tests.

## Original dictionary-prototype implementation — 2026-10-30

The original dictionary-prototype software milestones were implemented. Added the complete, attributable ISLAN A–Z set, reproducible
bootstrap, checksum invalidation, preloading/error recovery, recording cancellation, automated regression
tests, real browser recorder diagnostics, a small human-speech smoke test, CI configuration and a handover ZIP.
The remaining external sign-language review is recorded separately from completed software work.

## v1.2 reconciliation

The broader PDF completion checklist is now tracked in pdf_requirements_checklist.md. Exact reviewed sentence orders have an opt-in interface, but real reviewer-authored rules and held-out evaluation remain pending. Current media counts and final software-check evidence are in evaluation_report.md. Human review, representative recordings, broader hardware/browser validation and authenticated remote Git delivery remain independent completion conditions.
