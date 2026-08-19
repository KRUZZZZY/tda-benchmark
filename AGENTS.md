# TDA Pipeline Benchmark — Dissertation Project

Independent dissertation research (Zachariah Markusson, independent researcher).
Persistent homology / topological data analysis pipeline benchmark.

## Facts
- Dissertation: `dissertation.tex` in this directory (8 chapters + 3 appendices), 35pp target, ~20 refs.
- Venv: `.venv-tda` (at AI_KOS_PROJECT root). Runner: `run_benchmark(cfg, n_jobs=-1)`.
- `config.yaml` drives runs; `analysis.py` analyses results.
- E2E sanity check: sphere/torus = 100%.

## Key finding (modality-dependent)
- Vectorization dominates ECG200 (+1.9pp, p=0.038).
- Filtration dominates MNIST (cubical 97.5% vs VR 96.25%).
- Neutral on clean synthetic data.

## Process
- Math rigor required: chain complexes, formal definitions, theorem citations.
- Framework playbook: `tda-experiments` skill (Hermes).
