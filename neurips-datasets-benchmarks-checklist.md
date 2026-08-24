# NeurIPS Datasets & Benchmarks Checklist — TDA Pipeline Benchmark

Filled for the dissertation's benchmark contribution (v1.0-dissertation).
Serves as a final QA pass and is submission-ready for a D&B-track venue.

## For all datasets
- **Q1** Description: ✅ §4.1–§4.2 and Appendix B describe every dataset
  instance (synthetic sphere/torus with noise levels, ECG200, ECG5000,
  binary/10-class MNIST, Fashion-MNIST, UCR panel, MIT-BIH).
- **Q2** Motivation for collection: N/A — all datasets are public (UCR
  archive, MNIST, PhysioNet MIT-BIH) or synthetically generated.
- **Q3** Composition: ✅ datasets table in the paper (modality, n, points,
  classes, source).
- **Q4** Collection process: ✅ fetch/generate scripts with SHA256 checksums
  (`scripts/download_*.py`, `generate_*.py`; `data/tda/checksums.sha256`).
- **Q5** Preprocessing/cleaning: ✅ documented (§3.2; Takens embedding,
  subsampling with fixed seeds, MIT-BIH beat-window construction).
- **Q6** Uses (past/future): ✅ stated in the paper.
- **Q7** Distribution: 🔲 not redistributed — scripts + checksums shipped;
  MIT-BIH derivatives subject to PhysioNet licence.
- **Q8** Maintenance: ✅ repo + CI + REPRODUCING.md.

## For synthetic data
- **Q9** Generation process: ✅ seeded generators (`generate_*.py`, seed 42),
  fully reproducible.
- **Q10** Instance variations: ✅ noise levels σ ∈ {0, 0.05, 0.15, 0.30},
  n ∈ {100, 1000, 3000}, matched-genus pairs.

## For benchmarks
- **Q11** Existing benchmark? ✅ this is a benchmark contribution; compared
  against Conti et al. 2022, Ali et al. 2023, Sulowska 2026 (see §2).
- **Q12** Motivation: ✅ the fixed-dimension gap in prior benchmarks (§1).
- **Q13** Meaningful comparison: ✅ 616-config factorial sweep, repeated CV,
  level-matched analyses, Friedman/Nemenyi across datasets.
- **Q14** Metrics: ✅ accuracy + marginal stage ranges + η²/ω² + CIs +
  wall time + peak memory; balanced accuracy/macro-F1 on imbalanced sets.
- **Q15** Access to results: 🔲 DBs archived on Zenodo (DOI after archive);
  flat CSV exports in the archive; DBs local at `data/tda/`.
- **Q16** Statistical significance: ✅ repeated CV (r=25), Nadeau–Bengio
  CIs, Friedman Q=50 (p≈10⁻¹¹), Nemenyi CD; multiplicity (Holm/BH)
  disclosed; split-noise-only CI caveat stated.
- **Q17** Computational requirements: ✅ runtime table in REPRODUCING.md
  (single CPU, serial); per-config wall times in the DBs.
- **Q18** Licensing: ✅ MIT (code); datasets under their own licences
  (fetch scripts respect them).
