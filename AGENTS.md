# TDA Pipeline Benchmark — Dissertation Project

Independent dissertation research (Zachariah Markusson, independent researcher).
Persistent homology / topological data analysis pipeline benchmark.

## Facts
- Dissertation: `dissertation.tex` in this directory (6 chapters + 5 appendices), 54pp compiled, 24 refs. This is the authoritative source — keep AGENTS.md/README in sync with it.
- Venv: `.venv-tda` (at AI_KOS_PROJECT root). Runner: `run_benchmark(cfg, n_jobs=-1)`.
- `expanded_config.yaml` drives the 616-configuration sweep; `analysis.py` analyses results from the SQLite DB (`data/tda/expanded_results.db`).
- E2E sanity check: sphere/torus = 100% (clean) / mean 99.85%, min 98.5% at sigma=0.30 (noisy).
- Reproducibility: seeds fixed (base 42, per-dataset CRC32 subsampling), `run_all.sh` reproduces end-to-end (fixed 2026-08-21: heredoc expansion + canonical DB path), MIT licence.

## Key finding (modality-dependent)
- Vectorization dominates ECG200 (6.39pp marginal range across 7 vectorizers, 95% CI [6.13, 6.65]).
- Vectorization also dominates MNIST variance (vec 3.22pp vs filtration 1.65pp); cubical is best-of-family on images (98.0% vs VR 96.25%).
- Noise: sphere/torus signal survives σ=0.30 (99.85% mean across the 112 configs at that level, min 98.5%).
- 616 of 672 configurations completed; 56 excluded where point-cloud filtrations (Weak Alpha, Sparse Rips) are incompatible with image data.

## Process
- Math rigor required: chain complexes, formal definitions, theorem citations.
- Framework playbook: `tda-experiments` skill (Hermes).
