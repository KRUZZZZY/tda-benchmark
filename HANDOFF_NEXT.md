# HANDOFF — next agent (2026-08-24 session close)

State at handoff: **restructured dissertation, 69pp, forward-only, all audits applied.**

## Where things stand

- **Paper:** `dissertation.tex` → 6 chapters: Ch1 Intro · Ch2 Foundations · Ch3 Framework (+§3.4 Data and Code Availability) · Ch4 Results (§4.1 Stage Variance, §4.2 Robustness of the Ordering, §4.3 Generalisation and Conditions, §4.4 Mechanism, §4.5 Computational Costs) · Ch5 Boundary Conditions and Operational Guidance (§5.1 Scope, §5.2 Boundary Conditions, §5.3 Operational Guidance) · Ch6 Conclusion (thesis only). Appendices A–E unchanged. Compiles clean: 0 undefined, 0 multiply-defined, 69pp.
- **Commits this session (main):** `844b851` (restructure P2) · `554bf34` (restructure P1) · `c7e023e` (`>` fix) · `33eed00` (detailed plan) · `af2db4c` (plan) · `7926f58`/`b80911d`/`91aedf2` (Figure 1.1 fixes) · `297032a` (checksums) · `758dd02` (reproducibility) · `e55aa77` (round-3 audit) · `8a4ebf6` (cross-ref fix) · `7a08476` (audit round 2) · `88495ba` (audit round 2 batch).
- **Tag:** `v1.0-dissertation` (at `758dd02` — NOTE: the tag predates the restructure commits; the restructure changed the document materially. If the tag must match the final PDF, re-tag at HEAD before Zenodo archiving).
- **Knowledge vault** (ai-kos-knowledge, master): session articles — `tda-benchmark-restructure-2026-08-24`, `tda-benchmark-reproducibility-checklist-2026-08-24`, `tda-benchmark-figure11-clipping-fix-2026-08-24`, `tda-benchmark-audit-round3-fixes-2026-08-24`, `tda-benchmark-audit-round2-fixes-2026-08-24`, `tda-benchmark-l11-prose-audit-2026-08-24`, `tda-benchmark-audit-wave1/2-...` (earlier), `multi-sweep-adversarial-audit-prompts`.

## Plan docs (in repo)

- `RESTRUCTURE_PLAN.md` — goals + target structure.
- `RESTRUCTURE_PLAN_DETAILED.md` — 510-line execution spec (per-number KEEP/REMOVE anchors, B1–B30 backtracking inventory, merge maps, cross-ref plan, 16 corrections). **All executed**; keep as reference for the audit wave.
- `REPRODUCING.md`, `CITATION.cff`, `dissertation.bib`, `neurips-datasets-benchmarks-checklist.md`, `checksums.sha256` (+ `scripts/_checksum_verify.py`), `Dockerfile`, `requirements.txt` (fully pinned) — reproducibility package, done.

## Pending / open items

1. **3-agent L5 + L11 audit of the restructured doc** (per plan execution step 7) — the restructure moved many blocks; an internal-consistency + prose pass is the recommended next step. Offer was made; user ended session before deciding.
2. **Zenodo (user action):** archive release `v1.0-dissertation` → insert DOI into 3 placeholders (`CITATION.cff`, `dissertation.bib`, availability paragraph §3.4 — all marked `10.5281/zenodo.XXXXXXX`). Re-tag at HEAD first (see above).
3. **arXiv (user action):** cs.LG cross-listed math.AT; Appendix E satisfies the AI-tools policy.
4. **Interactive results explorer** (optional, from the checklist): a single HTML page over `data/tda/exports/*.csv`.
5. **B5 large-n sweep:** `data/tda/large_n_sweep.db` 8/12 done; n=3000 arm is a known ~42h DNF (documented in REPRODUCING.md) — do not restart expecting a result.

## Verification conventions (match the paper)

- Per-config accuracy = mean over folds; stage range = max−min over stage-level means.
- 13-key number baseline (values must never change): 6.39, 3.22, 1.65, 24.89, 3.60, 4.30, 0.96, 99.85, 95.83, 0.434, 1.82, 616, 672.
- Gates after any edit: 2× pdflatex 0 undefined/multiply-defined; number presence; backtracking greps (`again`/`resolves the earlier`/`ranks fourth` = 0; `single-split` = protocol labels only).
- Backslash-corruption check: grep `\\\\%|\\\\sigma|\\\\S[0-9]` (double-backslash before command chars) — this class of bug slipped through twice before.
- LaTeX edits: Python line-surgery only (never the patch tool — backslash doubling).
