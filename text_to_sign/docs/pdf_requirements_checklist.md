# PDF requirements and evidence

The PDFs are specifications, not authority to fabricate reviews or change unrelated legacy projects.
The user authorized this from-scratch text/speech project and the completion work. Statuses below distinguish
software implementation from external evidence. Full PDF compliance is NOT claimed.

| Requirement | Status | Evidence / completion condition |
| --- | --- | --- |
| Manual phases 1–2: workspace, branch, three datasets | Implemented / legacy N/A | Standalone workspace, feature/text-to-sign, dataset_audit.md; no supplied legacy models/datasets |
| Manual 3: inventory and verification lifecycle | Partial | signs.json, review worklist and approval/rejection CLI; genuine human label/ISL review pending |
| Manual 4: sourced attributable media | Implemented sourcing | Source/alphabet manifests, hashes and usage records; correctness is independently pending |
| Manual 5–6: modular structure, safe dictionary | Implemented equivalent | FastAPI, web/, signs/, canonical JSON and path/checksum validation |
| Manual 7: responsive single-page UI | Implemented / browser checks recorded | Input, video, labels, controls, queue, warnings, library; broader browser matrix pending |
| Manual 8: normalization, phrases, cancellation | Implemented equivalent | engine.py and generation/media-element isolation; regression tests |
| Manual 9: complete approved alphabet fallback | Partial | 26 playable letters and atomic fallback; no letters READY until human review |
| Manual 10: translation scope disclosure | Implemented | UI and README distinguish dictionary sequencing from grammar and avatar synthesis |
| Manual 11: 24 browser cases | Recorded with limits | test-cases.md; PDF lists only T01–T12, project adds T13–T24; simulations explicitly labelled |
| Manual 12: coverage, accuracy, playback reliability | Partial | Fixed-target completion_metrics.json, retrieval report and browser telemetry; verified references pending |
| Manual 13–15: HTTP startup and handover | Implemented / release validation separate | Windows launcher, local FastAPI and A–G evaluation report |
| Manual 16: Git and model preservation | Partial / legacy N/A | Local commits planned/delivered status in delivery_status.json; no legacy files supplied to checksum |
| Manual final A–G report | Implemented | evaluation_report.md; historical reports labelled separately |
| Roadmap workspace/environment | Implemented | Dependencies, feature branch, launcher and buildless UI |
| Roadmap metadata CSV | Implemented | data/metadata/sign_dictionary.csv generated from signs.json, pending/verified values |
| Roadmap automated integrity checks | Implemented equivalent | PyAV full video decoding, dimensions/fps/durations/hashes; replaces OpenCV implementation detail |
| Roadmap alphabet/word/phrase collection | Partial | Source preview available; human verification pending |
| Roadmap retrieval hierarchy | Implemented | Longest phrase at each offset, word, atomic complete fingerspelling |
| Roadmap sentence order | Framework only | Exact reviewed-construction mode, registry and review CLI; registry EMPTY pending ISL-fluent authoring/review |
| Roadmap speech with editable confirmation | Implemented | CPU ASR, actual browser recording pipeline, transcript editing and explicit convert |
| Roadmap >85% common vocabulary | NOT MET | Fixed 699 targets; approved exact coverage currently zero; source coverage reported separately |
| Roadmap 100% verified lookup | NOT EVALUATED | Source-ID retrieval is not independent semantic ground truth; held-out lookup manifest pending |
| Roadmap >90% grammatical correctness | NOT EVALUATED | Human-reviewed sentence corpus and supported constructions pending; finite mode is not general translation |
| Roadmap WER <12% | NOT ESTABLISHED | One human smoke utterance only; representative multi-speaker corpus pending |
| Roadmap generation <300 ms | Measured sample only | Browser quality export measures submit-to-first-loaded-frame; scope and sample results in completion_metrics.json |
| Roadmap 0 frame stalls | NOT ESTABLISHED | Waiting events, gaps and dropped frames instrumented; universal zero-stall claim requires broader evidence |
| Roadmap Git media strategy | Implemented | Media excluded from normal Git; external canonical sources and reproducible downloads |
| Roadmap PR, CI and merge | Blocked on authentication | delivery_status.json; no credentials available during current completion work |

## Reconciled defaults

The manual excludes grammatical translation while the roadmap requests basic ISL word order. Dictionary mode
remains the baseline; opt-in reviewed constructions are a separate extension and do not change default API behavior.
Named/date review evidence is mandatory for both asset approval and sentence-order registration.
No rules or reviewers are invented to obtain a passing benchmark.

The existing 699-term target list remains fixed. Exact approved vocabulary, approved aliases and fingerspelling
are separate measures; selecting only downloaded words as the denominator is not the roadmap coverage metric.
Strictly >85% needs 595 exact reviewed targets. Missing external datasets are N/A, not successfully audited datasets.

FastAPI instead of a static Python HTTP server, PyAV instead of OpenCV, and generation counters instead of timestamps
are documented implementation equivalents. The old path C:/ISL-Project is not this user's from-scratch workspace.
The manual calls for 20 phases but only specifies named phases through sixteen; no missing phases are invented.
