# Human review and held-out evaluation

No reviewer or participant approval has been inferred from software tests. Templates are deliberately empty.
Use a copy of each template to collect real evidence; never replace placeholders with invented records.

## Asset review

`review_worklist.csv` is a generated snapshot of canonical `data/signs.json`, not a bulk approval import.
Inspect every actual full clip via source preview and its canonical source. Check upright orientation, visible hands,
meaning/part of speech, contextual variants, handshape, movement, facial information and the suitability of static letters.
Reject misleading or incomplete media. Record the actual ISL-fluent reviewer's identifier, date, findings and meaning.

After a real review, use `scripts/review_asset.py --term TERM --type TYPE --reviewer ACTUAL_NAME
--meaning REVIEWED_MEANING --note ACTUAL_OBSERVATIONS --label-checked --isl-reviewed`.
For a rejected clip replace both approval flags with `--reject`. These are placeholders, not runnable review evidence.
Rejection excludes the clip even from source preview. A changed checksum requires fresh review.
Then run `scripts/audit_assets.py --changed-only` to refresh metadata, worklists and checks.

All commands in this guide use `.venv/Scripts/python.exe` followed by the script path.

## Sentence order

Default dictionary mode preserves English match order; it is not grammatical translation.
The optional `reviewed_sentence` API/UI mode uses exact normalized constructions in `data/sentence_rules.json`.
Only a named, dated human review can register an explicit ordered list of existing sign IDs via
`scripts/review_sentence.py --help`. No heuristic SOV rewrite, invented rule or partial sentence fallback is used.
Rules and assets have independent approval gates. Source preview may show pending assets in a reviewed order;
approved mode requires every asset READY. The initial rule registry is empty.
Finite supported constructions do not establish general English-to-ISL translation, spatial syntax or facial grammar.

## Evaluation manifests

Templates are under `data/evaluation/`; recordings remain outside Git and release archives.
Each sample needs a unique `id`, `split: "test"`, and actual `reference_reviewed_by`.
Do not reuse development/tuning examples as test data or create expected values from current engine outputs.

Speech sample fields: `audio` (local path relative to manifest), `reference`, `speaker_id` (pseudonym), `accent`,
`condition` (`clean` or `noisy`), `source`, `usage_permission`, plus the common fields.
Collect consented/licensed multi-speaker English recordings including Indian English. Record exact verbatim references.
The project default for a representative evaluation is at least 40 utterances, 400 reference words, five speakers,
both clean/noisy conditions and an Indian English group. This is a documented project minimum, not a PDF-prescribed sample size.
Report WER by corpus and subgroup. A single clean audiobook sample is only smoke evidence.
Audio must obey the app's 60-second/20-MB limits. No recording is automatically uploaded or captured by the benchmark.

Lookup sample fields: `input`, independently verified `expected_sign_ids`, plus the common fields.
Sentence sample fields: `input`, independent `expected_sign_ids`, `grammatical_acceptable` (a real human judgment),
plus the common fields. Have the reviewer assess the actual generated visual sequence as well as its ID order;
use `false` if the result is grammatically unacceptable even when the IDs match. Test finite constructions and record
unsupported ones; do not extrapolate correctness to unseen grammar.

Run `scripts/benchmark.py --speech-manifest PATH --lookup-manifest PATH --sentence-manifest PATH` as evidence arrives.
Missing evaluations stay null; empty or unreviewed corpora fail validation. WER is word-weighted, not an average of percentages.
Speech normalization only ignores case/punctuation; it does not replace words to improve a score.

## Browser measurements and hardware

Submit actual text queries, wait for loaded media, play full sequences without manual skips, and repeat across target browsers.
About → Download playback quality report exports at most 200 in-memory attempts with no message text/audio.
Run `scripts/benchmark.py --browser-report PATH` to aggregate it. New conversion, stop and navigation cancel an attempt;
skipped/failed clips cannot count as a successful continuous playback. Each deliberate user pause is excluded from stall duration.
Initial load latency runs from text submission to the first loaded video frame, before the explicit Play click.
ASR latency is measured separately. Browser `waiting` events, transition gaps and dropped-frame counters have distinct meanings;
zero observed waiting events is not proof of zero frame stalls under all conditions.

Use the actual microphone with participant consent; test grant/denial, record/stop/cancel, editable transcript and explicit convert.
Record browser/version, device, input type, cache state, sequence count, failures and conditions in the evaluation notes.
Check first-run restoration online and cached text/media/ASR offline. Do not change system networking merely to simulate offline use.

## Acceptance and external dependencies

- Strict approved exact coverage >85% of the fixed 699 targets requires at least 595 reviewed target terms.
- Verified lookup must be 100%; grammatical correctness >90%; representative speech WER <12%.
- Text submit-to-playback-load must be <300 ms under recorded conditions; record stalls and reliability honestly.
- Human review, representative participant recordings, physical microphone checks and a signed-in GitHub account
  are external dependencies. The toolchain prepares these tasks; it cannot manufacture their results.
