# TDA Pipeline Benchmark — Dissertation Project

Independent dissertation research (Zachariah Markusson, independent researcher).
Persistent homology / topological data analysis pipeline benchmark.

## Facts
- Dissertation: `dissertation.tex` in this directory (6 chapters + 5 appendices), 38pp compiled, ~20 refs. This is the authoritative source — keep AGENTS.md/README in sync with it.
- Venv: `.venv-tda` (at AI_KOS_PROJECT root). Runner: `run_benchmark(cfg, n_jobs=-1)`.
- `expanded_config.yaml` drives the 616-configuration sweep; `analysis.py` analyses results from the SQLite DB (`data/tda/expanded_results.db`).
- E2E sanity check: sphere/torus = 100% (clean) / ≥99.5% (noisy).
- Reproducibility: seeds fixed (base 42, per-dataset CRC32 subsampling), `run_all.sh` reproduces end-to-end, MIT licence.

## Key finding (modality-dependent)
- Vectorization dominates ECG200 (6.1pp marginal range across 7 vectorizers, 95% CI [4.8, 7.4]).
- Filtration dominates MNIST (cubical 98.0% vs VR 96.25%).
- Noise: sphere/torus signal survives σ=0.30 (99.85% mean across the 112 configs at that level, min 98.5%).
- 616 of 672 configurations completed; 56 excluded where point-cloud filtrations (Weak Alpha, Sparse Rips) are incompatible with image data.

## Process
- Math rigor required: chain complexes, formal definitions, theorem citations.
- Framework playbook: `tda-experiments` skill (Hermes).
