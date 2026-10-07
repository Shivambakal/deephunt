# Agent #91 — Evidence Normalizer Report

**Task:** Normalize every entry in `~/workspace/hacker-agent/deephunt/swarm/*.jsonl` into a consistent schema (n, role, type, title, detail, evidence, confidence). Truth was not judged — structure only.

## Source files read

| File | Entries |
|---|---|
| obs_recon.jsonl | 84 |
| obs_app.jsonl | 123 |
| obs_diff.jsonl | 84 |
| obs_verify.jsonl | 10 |
| hyp_known.jsonl | 76 |
| hyp_novel.jsonl | 36 |
| **Total** | **413** |

## Schema violations found and fixed

- **3 total violations** (0 malformed JSON lines; 0 invalid confidence values; 0 wrong-type fields).
- All three were in `hyp_novel.jsonl`, lines 4–6: **missing `evidence` field**.
- Fix applied: set `evidence` to the explicit marker `"none provided"` (no evidence was invented — the entries' original wording is preserved verbatim in `title`/`detail`).
- Also added a `source_file` field to every entry (structural provenance, not a content change).

No confidence values needed lower-casing or remapping; all were already one of `low`/`medium`/`high`. Extra fields (`falsifier`, `verdict`, etc.) were preserved untouched.

## Normalized output

- `~/workspace/hacker-agent/deephunt/swarm/memory_normalized.jsonl` — 413 entries, one JSON object per line, each containing all 7 required fields plus `source_file`.
- Type distribution: 282 observation · 121 hypothesis · 10 verification.
- Confidence distribution: 143 high · 149 medium · 121 low.

## Caveat

Sibling swarm agents were actively appending to these files during normalization (observed `obs_recon` grow 76→84, `obs_app` 109→123, `obs_diff` 78→84, `obs_verify` 5→10 mid-run). The normalized file is a consistent point-in-time snapshot; later appends are not included. Re-running the normalizer before downstream use is recommended.
