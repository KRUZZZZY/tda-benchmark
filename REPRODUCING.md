# REPRODUCING — TDA Pipeline Benchmark Dissertation

How every result in *A Systematic Benchmark of Persistent Homology Pipelines
for Classification* (v1.0-dissertation, 73pp) was produced, and how to
regenerate it.

**Environment (load-bearing — do not deviate):** Python 3.12.3 with
`requirements.txt` pinned exactly (giotto-tda 0.6.2, scikit-learn 1.3.2,
ripser 0.6.15, gudhi 3.13.0, numpy 1.26.4). Use the `Dockerfile` for a
guaranteed match. The weak-alpha `IndexError` fragility, the Sparse Rips
30×-slower-at-design-point result, and the 3–27% wall-clock gaps are
**giotto-tda 0.6.2 findings** — a newer giotto-tda will not reproduce them.

**Compute:** all sweeps are single-CPU serial (`n_jobs=1`), run one at a
time. Total full reproduction ≈ 3–5 days of continuous serial compute plus
downloads.

## Artefact → script → database → runtime

| Paper artefact | Producing script | Database | Runtime (1 CPU, serial) |
|---|---|---|---|
| Main 616-config sweep (§4) | `run_all.sh` → `runner.py` + `expanded_config.yaml` | `data/tda/expanded_results.db` | ~1–2 days |
| ECG200 repeated CV r=25 (§4.1) | `scripts/sweep_repeated_cv_r25.py` | `data/tda/repeated_cv_r25.db` (84 configs × 25 reps) | ~90 min |
| r=25 harmonisation: ECG5000 / matched-genus / panel (§5.3.2) | `scripts/sweep_r25_ecg5000.py`, `sweep_r25_genus.py`, `sweep_r25_panel.py` | `data/tda/r25_ecg5000.db`, `r25_genus.db`, `r25_panel.db` (1500 runs total) | ~1–2 h each |
| Diverse-filtration check (§4.1) | `scripts/sweep_filtration_diversity.py` (+ `_more.py`) | `data/tda/filtration_diversity_sweep.db` | ~1–2 h |
| Level-matched panel (§5.3.1) | `scripts/sweep_panel_stagecapable.py` | `data/tda/panel_stagecapable.db` (144 runs) | ~1–2 h |
| Hyperparameter arm (§5.3.2) | `scripts/sweep_hyperparam.py` | `data/tda/hyperparam_sweep.db` | ~2–4 h |
| FPS ablation (§5.3.2) | `scripts/sweep_fps_ablation.py` | `data/tda/fps_ablation.db` | ~1 h |
| TDA+raw concatenation (§5.3.1) | `scripts/run_concat_ablation.py` | `data/tda/concat_ablation.db` (270 rows) | ~1 h |
| Multi-patient ECG, MIT-BIH (§5.3.1) | `scripts/build_mitbih.py` + `sweep_mitbih.py` (+ `_w256.py`) | `data/tda/mitbih_sweep_fast.db`, `mitbih_sweep_w256.db` | ~1 h each (fast recipe) |
| 10-class MNIST flip (§4.1) | `scripts/sweep_mnist10.py` | `data/tda/mnist10_sweep.db` | ~2–4 h |
| Topology-wins regime (§5.3.1) | `scripts/sweep_topology_wins.py` | `data/tda/topology_wins_sweep.db` | 3–8 h |
| Cross-library replication (§5.3.2) | `scripts/sweep_cross_library.py` | `data/tda/cross_library_sweep.db` (90 runs) | 2–4 h |
| H₂ via Alpha (§5.3.3) | `scripts/sweep_h2_alpha.py` | `data/tda/h2_alpha_sweep.db` (12 runs) | 1–2 h |
| Predictive theory (§5.3.3) | `scripts/analysis_predictive_theory.py` | reads existing DBs (no new sweep) | minutes |
| Hierarchical stage model (§5.3.3) | `scripts/analysis_hierarchical_stage.py` | reads panel DBs (no new sweep) | 1–3 min |
| Large-n / Sparse Rips design point (§5.3.2) | `scripts/sweep_large_n.py` | `data/tda/large_n_sweep.db` | ⚠️ see warnings |
| All figures (Fig 4.1–5.1, CD diagram) | `generate_figures.py`, `scripts/analysis_multidataset_friedman.py`, `scripts/analysis_large_n.py` | read the DBs above | minutes |

## Data

Do **not** redistribute the raw datasets. Regenerate or fetch them:

| Dataset | Script | Notes |
|---|---|---|
| Synthetic sphere/torus, matched-genus, dynamical systems | `scripts/generate_datasets.py`, `generate_matched_synthetic.py`, `generate_dynamical_systems.py` | Seeded (42), fully reproducible |
| UCR (ECG200, ECG5000, FordA/B, Wafer, ElectricDevices, HandOutlines) | `scripts/download_ucr.py`, `download_multidataset_ucr.py` | Downloads from the UCR archive |
| MNIST / Fashion-MNIST | `scripts/download_ucr.py` (or local source) | Subsampled with fixed seeds |
| MIT-BIH arrhythmia (beat windows) | `scripts/build_mitbih.py` | From PhysioNet — check its licence before redistributing anything derived |
| ModelNet10 / Outex | `scripts/download_modelnet.py`, `download_outex.py` | Documented sources; proxy generators if unreachable |

Every script ends by verifying **SHA256 checksums** of the produced `.npy`
arrays against `data/tda/checksums.sha256`, so readers can confirm
byte-identical inputs.

## ⚠️ Warnings (read before running)

1. **Sparse Rips at n=3000 does not terminate** (~42 h DNF, no mid-config
   checkpointing). The n=1000 arm completes (~1.8 h/config); the n=3000 arm
   of `sweep_large_n.py` is a known non-terminator — do not start it
   expecting a result. The paper reports this honestly.
2. **`repeated_cv_r25.db` contains 5 orphaned run rows** (ids 330–334) with
   no fold results — leftover from a killed parallel attempt. All analysis
   filters on `finished_at IS NOT NULL`; the orphans are cosmetic but
   expected if you see row-count mismatches.

## Verification conventions (match the paper's numbers)

- Per-config accuracy = mean over folds (never max).
- Stage-level mean = mean over the other stages' configs; stage range =
  max−min over the stage's levels.
- Friedman uses tie-averaged ranks (scipy `rankdata`, 1 = best); Nemenyi
  critical difference q₀.₀₅,₈ = 3.031, CD = 2.475.
- Every headline number in the paper can be re-derived from the named DB
  with these conventions.
