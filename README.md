# SignBridge

English text and speech → Indian Sign Language dictionary video sequences.

A local research prototype with a responsive browser workspace, phrase-first lookup, controlled playback,
and local speech transcription. It sequences dictionary assets; it does **not** perform grammatical ISL translation.

## Start on Windows

### Recipient checklist: first installation

`git clone` and `git pull` download tracked source code only. They **do not install Python packages,
sign videos, or the speech model**. Each recipient needs their own local setup.

| Item | Needed by recipients? |
| --- | --- |
| Windows and Python | Yes. Python 3.12 is the locally tested version; project requires Python 3.11+. Enable Python in PATH during installation. |
| Git | Needed for clone/pull; not needed to run an extracted handover ZIP. |
| Browser | Yes. Microphone recording requires permission on localhost. |
| Internet | Needed initially for Python dependencies, sign media and first speech-model download. |
| GPU, API key or paid service | Not required; transcription runs on the CPU. |
| Node.js/npm | Only for developers running JavaScript tests; not required to use the app. |
| Separate FFmpeg installation | Not required by this setup; audio/video decoding uses the PyAV dependency. |

Allow several GB of free disk space for the virtual environment, roughly 1.3 GB of playback media,
source-restoration caches and speech weights. First setup time depends on network speed and the machine.
The first transcription can be slow because it downloads and loads the model.

In PowerShell, use a folder where you have write permission:

```powershell
git clone https://github.com/Pilli9375/Text_Speech-to-ISL-Sign-Generation.git
cd Text_Speech-to-ISL-Sign-Generation
python --version
.\start.bat
```

Keep the server terminal open and visit **http://127.0.0.1:8000**.
The launcher creates `.venv`, installs runtime requirements, downloads missing videos from the recorded
external sources, verifies media and starts the server. You do not need to activate the virtual environment.
If any download fails, setup stops with an error; restore connectivity and run the launcher again.
Source access is controlled by its providers and cannot be guaranteed permanently.

If receiving a handover ZIP instead, extract it completely into a writable folder and run `start.bat`
inside the extracted SignBridge folder. Its included videos avoid downloading the media bank;
Python dependencies and uncached speech weights still need initial internet access.
Do not copy another person's `.venv` between computers. Model weights are not included in the ZIP.
Older ZIPs do not automatically receive GitHub updates: use a newly built archive or a Git checkout.

### Updating an existing installation

Stop the running server using **Ctrl+C in its terminal** before updating. Then, inside the project folder:

```powershell
git switch main
git pull --ff-only origin main
.\start.bat
```

The launcher installs changed runtime requirements and restores newly registered media automatically.
Existing matching downloads are reused. Refresh the browser with **Ctrl+F5** after restarting.
Running `git pull` alone does not update a running Python process or an already open browser page.
If Git reports local modifications or a divergent branch, preserve your changes and resolve them before updating;
do not delete your work or use a forced reset merely to follow this guide.
The launcher returns early when SignBridge is already running, so stop it first to apply updates.

### Dependency files and developer setup

- `requirements.txt`: runtime dependencies; installed automatically by the launcher.
- `requirements-dev.txt`: runtime plus pytest/httpx; use for development and Python tests.
- `requirements-lock.txt`: exact historical Windows/Python 3.12 environment snapshot; includes development tools.
  The normal launcher uses requirements.txt and may resolve newer compatible releases.
- `package.json` / `package-lock.json`: JavaScript test dependencies only; use `npm ci`, then `npm test`.
- `pyproject.toml`: package metadata and equivalent runtime dependency declarations.

For developer setup, after the first launch:

```powershell
.\.venv\Scripts\python.exe scripts/setup_project.py --dev
.\.venv\Scripts\python.exe -m pytest -q
npm ci
npm test
```

### First-run acceptance check

1. Confirm the server starts and the Sign library shows the downloaded entries.
2. With Source preview enabled (the default), convert `hello friend thank you` and play the sequence.
3. Test Pause, Resume, Next and Stop. Approved-only mode has no playable clips until actual review is completed.
4. Under Use your voice, record a short message or drop/select one supported audio file.
5. Confirm loading feedback, inspect/edit the transcript, then explicitly convert it to signs.

The recording/upload limits are 60 seconds and 20 MB. Drag files onto the webpage, not the browser's tab/address bar.
Audio stays on the local backend and temporary uploads are removed after processing.
After setup and an initial successful transcription, cached media/model use can work offline.
Moving to another computer or selecting an uncached model requires setup/downloads there again.

### Troubleshooting for recipients

| Symptom | Action |
| --- | --- |
| `python` not found or Microsoft Store opens | Install Python and enable PATH; reopen PowerShell, then check `python --version`. |
| PowerShell script policy blocks startup | Run `start.bat`; it invokes the project script with a process-scoped policy override. |
| Missing packages / `ModuleNotFoundError` | Use start.bat or the explicit `.venv` interpreter, rather than an unrelated system Python. |
| Media download fails | Check internet/provider availability, then rerun start.bat; consult canonical links in the source manifest. |
| First transcription takes time or fails | Allow the model download to complete; check connectivity, then retry. Typed input remains available. |
| Microphone denied | Allow access for localhost in your browser, or use the audio-file picker/drop area. |
| Unsupported audio file | Use a real WAV/MP3/M4A/OGG/WebM/MP4/FLAC recording within limits; renaming an extension does not convert a file. |
| Port 8000 in use | Stop the previous SignBridge terminal. Do not terminate unrelated applications indiscriminately. |
| UI still looks old | Restart after updating, then Ctrl+F5. |

For a manual alternate port, use `.venv/Scripts/python.exe -m uvicorn text_to_sign.app:app --host 127.0.0.1 --port 8001`
and visit http://127.0.0.1:8001. Binding to localhost keeps this a local app; public hosting is a separate deployment task.

### Handover limitations

This is dictionary-based English-to-sign clip sequencing, not general grammatical ISL translation.
All current source clips still await independent semantic/ISL review. The experimental reviewed-order registry
is empty; leave that option off for ordinary dictionary use. User-reported microphone/playback success does not
establish a measured speech error rate. Media retain their individual usage/attribution conditions listed below.

From this folder, double-click `start.bat` or run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start.ps1
```

Open **http://127.0.0.1:8000**. Python 3.11+ and an internet connection for initial dependencies/model/media are needed.
The launcher creates `.venv`, installs changed dependencies, restores the recorded media collection, and audits it.
Subsequent launches reuse matching files. If the app is already running, the launcher prints its URL.
Fresh source checkouts fetch about 127 MB of selected alphabet originals through bounded ZIP ranges;
they do not download the 1.4 GB archive. The handover ZIP already includes the normalized playback clips.

Manual setup:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/setup_project.py
.\.venv\Scripts\python.exe -m uvicorn text_to_sign.app:app --host 127.0.0.1 --port 8000
```

`requirements-lock.txt` records exact versions verified on Windows / Python 3.12; it includes testing/audit tools.
For the same platform, install it with `pip install -r requirements-lock.txt` instead.
PyAV is constrained below 17 because the observed newest release removed an API used by faster-whisper.

## Use it

1. **Source preview is enabled by default**, as requested, so the downloaded collection works immediately. Independent ISL review remains pending.
2. Uncheck **Preview source clips** to use approved-only mode, which plays only READY assets.
3. Enter `hello friend`, `thank you`, or `water please`, then choose **Convert to signs**.
4. Review the queue and unsupported-term warnings. Use Play, Pause/Resume, Stop, Next and speed controls.
5. Under **Use your voice**, record up to 60 seconds or upload WAV/MP3/M4A/OGG/WebM/MP4/FLAC (under 20 MB).
6. Review/edit the transcript in the text area, then convert it. Transcription never starts sign playback automatically.

The **Sign library** exposes each term's meaning, readiness, source, and an explicit source-preview action.
Only English input is supported. Non-English writing systems are rejected instead of partially dropped.
The expanded library contains **492 word/phrase clips plus 26 letters** (518 total). It covers greetings, people/family,
questions, daily actions, food/drink, places/travel, time, health, learning/work, objects and nature.
Use the library's category/type filters, search and 24-card pages to browse it. Exact sourced phrases include
`good afternoon`, `excuse me`, `I don't know`, `I don't understand`, `I know` and `I understand`.
The official I/Me source label supplies the pronoun I and its explicit synonym Me; it remains distinct from letter I.
The complete double-handed A–Z alphabet adds 26 clips, including the original J motion. For example,
`jazz` becomes J–A–Z–Z. Letter availability is shown for the selected review mode.
Pause/resume, queue selection and speed apply to both word and alphabet clips. Missing or timed-out media
are reported and skipped during playback. Typing during transcription cancels its result so your edits survive.

## Speech

faster-whisper runs `base.en` locally on the CPU with INT8 inference. The first transcription downloads model
weights from the model provider to the normal Hugging Face cache. Later transcriptions can use cached weights offline.
No API key is needed. Audio is sent only to the local backend, processed in a temporary file, then removed.

To choose a smaller model before startup:

```powershell
$env:SIGNBRIDGE_ASR_MODEL = 'tiny.en'
.\start.ps1
```

For microphone recording use localhost/127.0.0.1 or HTTPS. If microphone access is unavailable or declined,
upload audio or use typed text. Model-download/network failures and invalid media produce visible errors.
The visible Cancel transcription control cancels the browser request; an already running backend/model download
may finish its bounded current job before accepting another recording. Recordings are automatically stopped before 60 seconds.

## Asset workflow

`text_to_sign/data/signs.json` is the canonical playback dictionary. Each entry contains:

- Unique `id`, normalized `text`, `type` (`word`, `phrase`, `alphabet`), relative `file`, and contextual `meaning`.
- Canonical `source_url`, `attribution`, usage terms, media checksum and audit metadata.
- `checks`: `playable`, `label_checked`, `isl_reviewed`, `usage_approved`.
- `status`, actual `reviewed_by`, `reviewed_on`, and review observations.

READY requires every check plus named and dated review records, source attribution, and a local media file.
The audit script checks media integrity; it never invents human review. Replacing a reviewed asset invalidates
the recorded checksum and its eligibility pending reinspection.

The manifest contains 492 ISLRTC word/phrase clips plus 26 ISLAN alphabet clips. Restore excluded videos:

```powershell
.\.venv\Scripts\python.exe scripts/import_alphabet.py
.\.venv\Scripts\python.exe scripts/source_assets.py --download
.\.venv\Scripts\python.exe scripts/audit_assets.py
```

To rebuild source discovery use `scripts/source_assets.py --discover` first. This uses publicly accessible
official Drive folder listings. If a provider changes access, use the canonical source links in the manifest;
failed downloads are explicit and are never represented as successful.
Everyday vocabulary targets and categories are in `data/vocabulary_targets.json`. Discovery selects a balanced
collection from exact source labels across all A–Z folders, preserving existing clips and recorded exclusions.
To request a larger curated set, run `scripts/source_assets.py --discover --limit 500 --download`, then audit it.
Source downloads are bounded to 50 MB per clip. Unavailable/oversized responses are not treated as valid media.

An ISL-fluent reviewer can record an actual completed review using `scripts/review_asset.py --help`.
Do not populate review fields without the corresponding human inspection. Re-run the audit afterward to refresh CSVs.

For new terms, add source records to the manifest, download the actual media, run the audit, and arrange review.
For alphabet assets, add dictionary entries of type `alphabet` with single-letter keys and `signs/letters/a.mp4`
style paths, then complete the same media/usage/human checks. The included set has all 26 source letters.
Fingerspelling emits an entire word only when every required letter is available. Digits and hyphens are never silently dropped.

## Source acknowledgement and usage

Indian Sign Language Research and Training Centre, Department of Empowerment of Persons with Disabilities,
Ministry of Social Justice and Empowerment, Government of India.

Official source policy: https://islrtc.nic.in/faq/ (Q23). This project's use is non-commercial research with
acknowledgement; dictionary media must not be resold or used for profiteering. Source videos retain their
original captions and attribution. Do not treat code licensing as granting rights to the media.
Video binaries and speech-model weights are excluded from Git. No AI-generated hand gestures are used.

Alphabet source: Elakkiya R and Rajalakshmi E (2021), **ISLAN**, Mendeley Data V1,
DOI **10.17632/rc349j45m5.1**, https://data.mendeley.com/datasets/rc349j45m5/1, **CC BY 4.0**.
The selected signer-1 double-handed stills are rotated upright, resized and encoded as one-second videos;
the original J video is copied unchanged. The source's double-handed Z is a static image. No moving gesture
was synthesized. Original source/member hashes, license, attribution and transformation notes are recorded.
Word clips retain ISLRTC's separate non-commercial/acknowledgement conditions.

## Structure

```text
text_to_sign/
  app.py             FastAPI routes and local UI/media serving
  engine.py          Normalization, review gates, phrase lookup, atomic fallback
  speech.py          Lazy local ASR and duration checks
  web/               HTML, CSS, modular browser JavaScript
  data/              Canonical dictionary, source manifest, source folder metadata
  signs/             Downloaded words, phrases and complete A–Z source clips
  docs/              Asset audits, provenance, plan and evaluation
  tests/             Engine/API tests and browser test matrix
scripts/             Reproducible source, audit, review and evaluation tools
```

## Checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
npm ci
npm test
.\.venv\Scripts\python.exe scripts/audit_assets.py
.\.venv\Scripts\python.exe scripts/evaluate.py
.\.venv\Scripts\python.exe scripts/evaluate_speech.py
```

Engine tests use explicitly synthetic fixtures, not real sign correctness labels. See
`text_to_sign/docs/evaluation_report.md` for observed results and limitations and
`text_to_sign/tests/test-cases.md` for the browser execution matrix.

The browser state tests use JSDOM media/permission adapters to test cancellation and failure behavior.
The opt-in real-browser diagnostic harness uses actual MediaRecorder with a synthetic speech stream,
simulates permission denial, and injects a missing-media HTTP response. It never captures the room microphone.
Enable it with `$env:SIGNBRIDGE_DIAGNOSTICS='1'` before starting the server, then open
`http://127.0.0.1:8000/diagnostics/recorder`. Generate its test WAV with `scripts/speech_smoke.ps1`.
The diagnostic route is absent during normal startup.

To create the handover archive, run `python scripts/package_release.py` with the venv interpreter.
The resulting `artifacts/SignBridge-1.2.zip` contains code, provenance and 518 validated playback clips,
plus a SHA-256 sidecar. It excludes model weights, raw photographs, recordings, environments and Git metadata.
The included workflow runs Python and JavaScript checks on Windows and Linux when pushed to GitHub;
its remote execution is not claimed until GitHub actually runs it.
Startup verifies every media checksum and reuses previous full-decode evidence for unchanged files.
Run `scripts/audit_assets.py` without `--changed-only` whenever you want a fresh full decode of the whole library.

No existing sign-recognition models or datasets were present or modified. Code is on `feature/text-to-sign`.
The remote repository is configured; pushing and public deployment are separate delivery operations.

## Completion work (v1.2)

The fixed everyday target list contains 699 terms; 488 exact target labels are sourced (69.81%),
plus four additional phrases. All 518 clips still await actual human label/context and ISL review.
The source-availability ratio for the selected manifest is not the >85% approved-vocabulary benchmark.
There are currently zero READY assets and zero registered sentence orders.

`data/metadata/sign_dictionary.csv` is generated from canonical signs.json by `scripts/export_metadata.py`
and the asset audit. `docs/review_worklist.csv` is a reviewer snapshot. Actual approvals or rejections can be
recorded with `scripts/review_asset.py`; rejected clips are excluded even from source preview.

The experimental **Use reviewed sentence orders** option accepts only exact constructions registered by a
real ISL-fluent reviewer with `scripts/review_sentence.py`. Unsupported constructions return a warning and
no partial sentence. Default dictionary mode preserves its existing behavior; this is not general grammatical translation.

The About view can download this session's playback quality report. Run `scripts/benchmark.py --browser-report PATH`
to aggregate submit-to-loaded-frame latency, transition gaps, observed buffering and playback reliability.
`--speech-manifest`, `--lookup-manifest` and `--sentence-manifest` accept independently labelled held-out corpora.
Empty/unreviewed corpora never pass. Missing benchmark evidence is reported as null.
See `text_to_sign/docs/reviewer_and_evaluation_guide.md` for fields, collection procedure and sample-size defaults.

Run `scripts/verify_project.py` for recorded code checks and `scripts/validate_release.py artifacts/SignBridge-1.2.zip`
for a fresh-folder HTTP check. `--speech-sample PATH` additionally verifies cached ASR with provider offline flags.
Release validation uses shared installed dependencies; it does not claim a fresh operating-system installation.
The archive excludes its own digest-bearing validation JSON to avoid a self-referential checksum; validation is
saved alongside the archive and in the local docs. No recordings or model weights are included.

The current A–G handover and remaining PDF requirements are in `text_to_sign/docs/evaluation_report.md`
and `text_to_sign/docs/pdf_requirements_checklist.md`. GitHub authentication is needed for push/PR/remote CI/merge.

After GitHub authentication, run `python scripts/deliver_github.py --merge` from a clean committed feature branch to push, open the prepared PR, wait for both actual CI jobs and request a normal merge. The script does not bypass repository rules.
