# Dataset audit — 2026-10-30

## Starting state

The selected local workspace and the remote GitHub repository were empty. This is a new standalone project.
The manual's legacy repository path C:\ISL-Project\ISL-Based-Assistive-Communication-System does not exist on this machine.
No existing ISL recognition models, landmark files or sign media were provided in this workspace.

| Dataset described by manual | Actual availability in this project | Reuse decision |
| --- | --- | --- |
| RealSign alphabet | Not provided | No reuse claim; source and review letter media separately |
| 29 isolated word classes | Not provided | No reuse claim |
| Continuous sequences | Not provided | No reuse claim; no automatic segmentation |

The nearby C:\Pilli\Capstone\Dataset folder contained intrusion-detection CSVs; those are unrelated and were not imported.

## Original source collection (historical v1.0)

The official ISLRTC FAQ links the publicly accessible dictionary Drive root:
https://drive.google.com/drive/folders/1U-Pr4r1-cupgNOOq9NH_uTsQnPSVEKco

The dictionary web portal timed out during inspection. Connector folder retrieval returns at most 100 children,
which omitted some everyday vocabulary; public embedded folder listings exposed the full relevant names.
Those listings were used for exact file-label matching. No account credentials or private files were used by the downloader.

`data/source_manifest.json` records the selected 20 exact labels and canonical source URLs.
`asset_audit.json` records actual full-decoding frame counts, codec, dimensions, duration and byte sizes.
`asset_register.csv` records provenance, usage conditions, checksums and reviewer fields.

These are real MP4 video files, not .npy landmark arrays. Label correspondence and ISL correctness remain
separate checks: a source filename or a playable video is not sufficient to mark a sign READY.

Official source terms, accessed 2026-10-30: https://islrtc.nic.in/faq/ (Q23).
The dictionary permits research/teaching/ISL technology use with acknowledgement and no resale/profiteering.
Media are kept out of normal Git history and fetched reproducibly instead.

## ISLAN alphabet source (historical v1.0)

Elakkiya R and Rajalakshmi E (2021), ISLAN, Mendeley Data V1, DOI 10.17632/rc349j45m5.1:
https://data.mendeley.com/datasets/rc349j45m5/1. The author page explicitly lists CC BY 4.0.
The Multi-Signers ZIP label CSV grounds `Signer_1/Double_Handed_Alphabets/A1.jpg` through Z,
with `J1.mp4` as the moving double-handed J. The double-handed Z is `Z1.jpg`; lowercase z video
belongs to the separate single-handed set and was not mixed into this set.

Twenty-six selected members were fetched using bounded public HTTP ranges, ZIP CRC-checked and SHA-256
pinned. The source archive is 1,406,375,448 bytes, but only 126,590,254 bytes of selected originals were retained.
All 25 portrait-stored stills need 90-degree counterclockwise rotation to upright; EXIF does not fix them.
They were resized to fit 960×720 and encoded as one-second H.264 clips. J was copied unchanged:
1,920×1,080, 55 frames, about 2.21 seconds. No hand motion was synthesized.

`data/alphabet_manifest.json` records exact source members, original checksums and attribution.
`data/source_manifest.json` records the derived clips, transformation notes and their checksums.
All 46 final media clips (20 words/phrases + 26 letters) fully decoded: 1,960 frames,
93.41 seconds total, 48,144,793 bytes. Source/label inspection does not replace ISL-fluent review.

## Current v1.2 collection

The original counts above are historical. The current canonical collection contains 492 word/phrase clips and 26 letters (518 total). All 518 passed a fresh full decode during completion work. Refer to asset_full_decode_audit_v1.2.json for current per-file metadata. Human label/context and ISL verification remain pending for every clip.
