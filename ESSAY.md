# TDA Pipeline Benchmark — Complete Essay Framework

**A Systematic Comparison of Persistent Homology Pipelines for Classification**

> **STALENESS WARNING (2026-08-20):** This is a working planning document.
> Its numbers predate the final 616-configuration sweep and are OUTDATED.
> The authoritative source is `dissertation.tex` (6 chapters + 5 appendices).
> Key corrections: 616 executed configs (not 88); ECG200 vectorizer range
> 6.1pp (not 1.9pp); MNIST cubical 98.0% vs VR 96.25%; noise survives to
> σ=0.30 (not degrading after 0.15); Alpha 11-21% faster than VR (not
> 20-30%). This file is kept for structure/methodology reference only.

---

## ABSTRACT

Topological Data Analysis (TDA) transforms raw data into topological signatures via a three-stage pipeline: filtration (constructing simplicial complexes), vectorization (mapping persistence diagrams to fixed-length vectors), and classification (applying machine learning). While each stage has been studied in isolation, no prior benchmark systematically varies all three. We evaluate 6 dataset instances × 4 filtrations × 7 vectorizations × 4 classifiers — 616 completed configurations of a 672 grid. Our key finding: stage impact depends entirely on dataset modality. On clean synthetic data, topological signal survives σ=0.15 noise at 100% accuracy across all pipelines. On real time series (ECG200), vectorization choice dominates (6.1pp range) while filtration is neutral (0.7pp). This partially contradicts prior claims that "filtration always dominates" — that holds for image data but not time series. Alpha complex is 3-21% faster than Vietoris-Rips at equal accuracy. Persistence landscapes achieve the best accuracy/stability trade-off. We release a modular, reproducible benchmarking framework with normalized SQLite storage and YAML configuration.

---

## 1. INTRODUCTION

### 1.1 Motivation

Traditional machine learning operates on raw features — pixel intensities, time-series values, point coordinates. But data has shape: loops, voids, connected components that persist across scales. Topological Data Analysis extracts these invariants, and persistent homology is the dominant tool.

The adoption of TDA in materials science, neuroscience, and time-series analysis is growing. Yet practitioners face a bewildering choice: which filtration? Which vectorization? Which classifier? The pipeline has three stages, each with 5-15 options, creating hundreds of possible combinations.

### 1.2 The Three-Stage Pipeline

```
Raw Data → [FILTRATION] → Persistence Diagram → [VECTORIZATION] → Feature Vector → [CLASSIFIER] → Prediction
```

**Filtration**: Constructs a nested sequence of simplicial complexes from data. Vietoris-Rips connects nearby points; Alpha complex uses Delaunay triangulation; Cubical complex processes pixel grids. Output: persistence diagram — a multiset of (birth, death) pairs.

**Vectorization**: Maps the variable-length persistence diagram to a fixed-length feature vector suitable for ML. Persistence Images apply Gaussian kernels; Persistence Landscapes form a Banach space; Betti curves count active features. Output: numeric vector.

**Classification**: Applies standard ML to the vectorized features. SVM-RBF is the most common in prior work; Random Forest handles non-linear interactions; Logistic Regression provides a linear baseline.

### 1.3 The Research Gap

Every prior study fixes at least one pipeline stage:

| Study | Fixes | Tests |
|---|---|---|
| Conti et al. (2022) | Classifiers | Filtrations × vectorizations on 1 pipeline |
| Ali et al. (2023) | 1 filtration/dataset | 13 vectorizations |
| Sulowska (2026) | Vietoris-Rips only | 4 vectorizations × 3 classifiers |
| Barnes et al. (2021) | 1 filtration/dataset | 6 featurization methods |
| Turkes et al. (2022) | Synthetic data only | PH vs deep learning |

**No prior study varies filtration × vectorization × classifier × dataset simultaneously.** Fixing one dimension masks interaction effects — a vectorizer that shines with VR may fail with cubical; a classifier that works on clean data may break under noise.

### 1.4 Contributions

1. **First systematic benchmark varying all three pipeline stages** across datasets
2. **Noise robustness analysis** across 4 noise levels (σ = 0.00, 0.05, 0.15, 0.30)
3. **Stage impact quantification** — marginal accuracy contribution of each pipeline component
4. **Evidence that "filtration dominates" is dataset-dependent** — true for images, false for time series
5. **Open-source modular framework** with 7 filtrations, 11 vectorizers, 4 classifiers, YAML config, and normalized SQLite storage

---

## 2. MATHEMATICAL BACKGROUND

### 2.1 Simplicial Complexes

A **k-simplex** is the convex hull of k+1 affinely independent points. A 0-simplex is a vertex, a 1-simplex an edge, a 2-simplex a triangle, a 3-simplex a tetrahedron. A **simplicial complex** K is a collection of simplices closed under taking faces: if σ ∈ K and τ ⊆ σ, then τ ∈ K.

### 2.2 Filtrations

A **filtration** is a nested sequence of simplicial complexes indexed by a scale parameter ε:

```
K_{ε₁} ⊆ K_{ε₂} ⊆ ... ⊆ K_{εₘ}    where ε₁ < ε₂ < ... < εₘ
```

**Vietoris-Rips complex** VR_ε(X): a simplex σ is included if all pairwise distances between its vertices are ≤ ε. Simple to compute but large — grows as O(n^k) for k-dimensional homology.

**Alpha complex** A_ε(X): intersection of Voronoi balls. In 2D/3D, uses Delaunay triangulation — only O(n log n) simplices. Geometrically faithful to the underlying space (Nerve theorem: homotopy equivalent to union of balls).

**Cubical complex**: built from pixels/voxels. Each pixel is a vertex; adjacent pixels form edges; 2×2 blocks form squares. Natural for image data.

### 2.3 Persistent Homology

As ε increases, topological features appear (birth at b) and disappear (death at d). The **persistence** of a feature is d − b. Short-lived features are noise; long-lived features are signal.

**Betti numbers**: β₀ counts connected components, β₁ counts 1-dimensional cycles (holes), β₂ counts 2-dimensional voids. A sphere has β = (1, 0, 1); a torus has β = (1, 2, 1).

**Persistence diagram**: multiset of points (b, d) in the half-plane above the diagonal d = b. The **bottleneck distance** between two diagrams is the infimum over bijections of the sup norm difference. The **stability theorem**: bottleneck distance between diagrams ≤ Gromov-Hausdorff distance between point clouds.

### 2.4 Vectorization Methods

**Persistence Images** (Adams et al. 2017): Apply Gaussian kernel φ(b, p) where p = d − b is persistence. Discretize the birth-persistence plane into n_bins × n_bins grid. Output: 2D image per homology dimension.

**Persistence Landscapes** (Bubenik 2015): For each (b, d), define tent function Λ(t) = max(0, min(t−b, d−t)). The k-th landscape λ_k(t) is the k-th largest value of these tent functions at each t. Landscapes form a Banach space — you can compute means, variances, and confidence intervals.

**Betti Curves**: β_k(ε) = number of k-dimensional features alive at filtration value ε. Direct count of topological activity. Chung & Lawson (2022) unify these with normalized and entropy variants.

**Persistence Statistics**: Mean, standard deviation, min, max of births, deaths, and lifespans per homology dimension. Surprising effectiveness despite simplicity.

### 2.5 Classification

Standard sklearn-compatible classifiers. **SVM with RBF kernel** dominates prior work. **Random Forest** excels when SVM convergence is slow. **Logistic Regression** provides a linear baseline — if it achieves high accuracy, the topology signal is linearly separable and complex classifiers add no value.

---

## 3. METHODS

### 3.1 Benchmark Design

**Full factorial design**: For each dataset, we evaluate ALL combinations of filtrations × vectorizations × classifiers. This captures interaction effects that marginal experiments miss.

**YAML-driven configuration**: A single `config.yaml` file defines the sweep space. Adding a new dataset or method requires editing one file, not changing code.

**Factory pattern**: `FiltrationFactory.create("vietoris_rips")` returns a configured sklearn transformer. Adding a new method requires adding one entry to the factory — no other code changes.

### 3.2 Datasets

| Dataset | Modality | Samples | Dim | Classes | Filtration |
|---|---|---|---|---|---|
| Sphere+Torus (σ=0.00) | Point cloud | 200 | 100pts×3D | 2 | VR/Alpha/Sparse Rips |
| Sphere+Torus (σ=0.05) | Point cloud | 200 | 100pts×3D | 2 | VR/Alpha/Sparse Rips |
| Sphere+Torus (σ=0.15) | Point cloud | 200 | 100pts×3D | 2 | VR/Alpha/Sparse Rips |
| Sphere+Torus (σ=0.30) | Point cloud | 200 | 100pts×3D | 2 | VR/Alpha/Sparse Rips |
| ECG200 | Time series | 200 | 96 (Takens→3D) | 2 | VR/Alpha |

The sphere (β=1,0,1) has no 1D holes; the torus (β=1,2,1) has two. This clean topological difference provides ground truth. Noise levels test robustness. ECG200 maps 1D time series to 3D point clouds via Takens embedding with delay=1 and dimension=3.

### 3.3 Pipeline Components

| Stage | Available Methods | Count |
|---|---|---|
| Filtration | Vietoris-Rips, Alpha, Sparse Rips, Čech, Cubical, Weighted Rips, Flagser | 7 |
| Vectorization | PI, PL, Betti Curves, Silhouette, Entropy, Amplitude, Heat Kernel, Complex Polynomials, Pairwise Distance, Number of Points, Persistence Statistics | 11 |
| Classifier | SVM-linear, SVM-RBF, Random Forest, Logistic Regression | 4 |

### 3.4 Evaluation Protocol

- **Stratified 5-fold cross-validation** with fixed random seed (42) per config
- **Metrics**: Accuracy, F1 (weighted), precision (weighted), recall (weighted) — stored per fold
- **Wall time**: `time.perf_counter()` from pipeline construction to final fold completion
- **Storage**: Normalized SQLite schema — `runs` (one per config×rep), `fold_results` (per-fold metrics), `run_metadata` (pipeline params as JSON), `config_snapshot` (YAML for reproducibility)

### 3.5 Implementation

Python 3.12, giotto-tda 0.6.2 (scikit-learn 1.3.2 pin), ripser 0.6.15, gudhi 3.13.0. All components implement sklearn `fit`/`transform` interface. Benchmark runner: `projects/tda-benchmark/runner.py`. Analysis: `projects/tda-benchmark/analysis.py`. Essay framework: `projects/tda-benchmark/essay_framework.py`.

---

## 4. RESULTS

### 4.1 Pipeline Stage Impact

**Synthetic data (sphere_torus, all noise levels):**
All pipeline stages achieve 100% accuracy. Filtration range: 0.00pp. Vectorizer range: 0.00pp. Classifier range: 0.00pp. The β₁=0 vs β₁=2 signal is so strong that even the worst pipeline combination separates perfectly. This persists up to σ=0.15 Gaussian noise.

**Real data (ECG200 arrhythmia):**

| Factor | Range | Top Performer | Top Acc | Worst Performer | Worst Acc |
|---|---|---|---|---|---|
| Filtration | 0.12pp | VR | 76.0% | Alpha | 76.0% |
| Vectorizer | **1.87pp** | Landscape | 76.0% | Image | 66.5% |
| Classifier | 1.25pp | RF | 75.0% | SVM | 66.5% |

**Key finding**: Vectorization choice matters most on real data, not filtration. This partially contradicts Conti et al. (2022) — their claim that "filtration dominates" holds for image data (MNIST: 30% → 94% by switching filtrations) but breaks down for time series.

### 4.2 Noise Robustness

All sphere_torus configurations at σ=0.00, 0.05, and 0.15 achieve 100% accuracy. The topological signal (β₁=0 vs β₁=2) survives moderate Gaussian noise remarkably well. This is consistent with the stability theorem: bottleneck distance between diagrams ≤ data perturbation, but even perturbed, the two classes remain separable.

At σ=0.30, the signal degrades (not yet benchmarked — requires larger sample sizes to detect).

### 4.3 Runtime/Accuracy Trade-off

| Pipeline | Accuracy | Wall Time |
|---|---|---|
| Alpha + Landscape + SVM (ECG200) | **76.0%** | 2.0s |
| Alpha + Image + SVM (ECG200) | 66.5% | 2.3s |
| Alpha + Landscape + SVM (sphere) | 100% | **2.7s** |
| VR + Landscape + SVM (sphere) | 100% | 4.2s |
| Sparse Rips + Betti + Logistic (sphere) | 100% | 32.7s |

**Finding**: Alpha complex is 20-30% faster than Vietoris-Rips at identical accuracy. Sparse Rips offers zero accuracy benefit at 10× the runtime. Alpha + Landscape + SVM-RBF is the Pareto-optimal default: 76% on real data, 100% on synthetic, in 2-3 seconds.

### 4.4 Interaction Effects

- **Vectorizer × Classifier**: Persistence Images + Random Forest (75.0%) > Images + SVM (66.5%) on ECG200. Landscapes + SVM (76.0%) > Landscapes + RF (73.0%). The gap depends on the pairing.
- **Filtration × Dataset**: Filtration choice is critical for images (Conti: 18-94% range) but neutral for time series (0.12pp range). Data modality determines which stage matters.
- **Noise × Filtration**: At σ=0.15, Alpha maintains 100% accuracy. VR also maintains 100%. Sparse Rips maintains 100% but at 10× cost.

### 4.5 Simple vs Complex

Persistence Statistics (mean/std of births/deaths/lifespans) ranks in the top tier for ECG200 despite requiring zero hyperparameters. This confirms Ali et al. (2023): simple statistical summaries consistently compete with sophisticated kernel methods. The bottleneck distance on persistence diagrams — the "natural" metric — is well-captured by simple statistics; kernel methods add computation without necessarily better capturing this structure.

---

## 5. DISCUSSION

### 5.1 Which Pipeline Choices Matter?

| Choice | Impact | When It Matters |
|---|---|---|
| Filtration | **Dataset-dependent** | Critical for images; neutral for time series |
| Vectorizer | **Consistently important** | 2-10pp range across all datasets |
| Classifier | **Moderate** | Helps on noisy/real data; irrelevant on clean topology |
| Noise level | **Robust to σ=0.30** | signal survives; min config 98.5% at σ=0.30 |

### 5.2 Practical Recommendations

1. **Start with Alpha complex** — faster than VR, equally accurate, numerically stable
2. **Default to Persistence Landscapes** — Banach space structure, top accuracy on time series, competitive everywhere
3. **Use SVM-RBF as classifier default** — most common in literature, reliable
4. **Always include a linear baseline** (Logistic Regression) — if it achieves >90%, complex classifiers add nothing
5. **Subsample point clouds to ≤100 points** for VR; use full clouds with Alpha
6. **Pin ALL dependencies** — giotto-tda's strict sklearn==1.3.2 pin creates fragility

### 5.3 Limitations

- Only H₀+H₁ homology (H₂ computationally prohibitive for VR)
- No deep learning vectorizers (PersLay, Hofer input layer)
- Two-class problems only (sphere/torus, normal/abnormal)
- Single implementation library (giotto-tda) — cross-library variance unknown
- Synthetic data may overstate topology's discriminative power
- 200-sample datasets — small-N statistics may inflate variance estimates

### 5.4 Future Work

- Add Flood Complex (Graf 2025) for million-point datasets
- Integrate PersLay and topological neural networks for learned vectorization
- Cross-library comparison: giotto-tda vs GUDHI vs Ripser
- Extend to multi-class problems (MNIST 10-class, Outex 68-class)
- Bayesian hyperparameter optimization instead of grid search
- Multiparameter persistence when software matures

---

## 6. CONCLUSION

This benchmark provides the first systematic evidence that while filtration choice dominates persistent homology pipeline performance on image data (as Conti et al. showed), vectorization choice matters more on time series data. The claim that "filtration always dominates" is an overgeneralization — stage impact is fundamentally dataset-dependent.

Persistence landscapes with Alpha complex and SVM-RBF are a robust default pipeline: 76% on ECG200, 99.9%+ on sphere/torus classification up to σ=0.30 noise.

The topological signal is remarkably noise-robust: the β₁=0 vs β₁=2 difference between spheres and tori survives Gaussian noise at σ=0.15 without accuracy degradation.

All code, data, and results are open-source. A single `config.yaml` file defines the benchmark sweep; a single Python script reproduces all results.

---

## REFERENCES

1. Adams et al. (2017). Persistence Images: A Stable Vector Representation of Persistent Homology. *JMLR*, 18(8).
2. Ali et al. (2023). A Survey of Vectorization Methods for Persistent Homology. *IEEE TPAMI*, 45(12).
3. Barnes et al. (2021). A Comparative Study of Machine Learning Methods for Persistence Diagrams. *Frontiers in AI*, 4.
4. Bubenik (2015). Statistical TDA Using Persistence Landscapes. *JMLR*, 16(3).
5. Carriere et al. (2020). PersLay: A Neural Network Layer for PDs. *AISTATS*.
6. Chung & Lawson (2022). Persistence Curves: A Framework. *JMLR*, 23.
7. Conti et al. (2022). Pipeline Comparisons of PH Approaches for Classification. *Machine Learning and Knowledge Extraction*.
8. Graf et al. (2025). The Flood Complex. *NeurIPS*.
9. Hatwar & Thangaraj (2026). TDA and ML: A Survey.
10. Hofer et al. (2017). Deep Learning with Topological Signatures. *NeurIPS*.
11. Perea et al. (2022). Template Functions. *Foundations of Computational Mathematics*.
12. Somasundaram et al. (2021). Benchmarking R Packages for PH.
13. Sulowska (2026). Comparative Analysis of PD Vectorization Methods. Preprint.
14. Tauzin et al. (2021). giotto-tda: A TDA Toolkit for ML. *JMLR*, 22(39).
15. Telyatnikov et al. (2024). TopoBench: Benchmarking TDL. *NeurIPS*.
16. Turkes et al. (2022). PH vs Deep Learning for Shape Analysis.

---

## APPENDIX: 10 KEY INSIGHTS

### 1. Filtration Choice is Dataset-Dependent
**Claim**: "Filtration dominates" is not universal — it's true for images, false for time series.
**Evidence**: Conti: MNIST 18-94% by switching filtrations. Our ECG200: 0.12pp range.
**Practical**: Match filtration to data type (Alpha/VR for clouds, Cubical for images).

### 2. Simple Beats Complex
**Claim**: Persistence Statistics often match kernel methods at zero hyperparameter cost.
**Evidence**: Ali 2023: PS won 3/3 benchmarks. Confirmed on ECG200.
**Practical**: Always baseline with Persistence Statistics first.

### 3. Landscapes Are the Most Robust
**Claim**: PL provides best accuracy/stability/interpretability trade-off.
**Evidence**: Top accuracy on ECG200 (76%), Banach space enables classical statistics.
**Practical**: Default to PL (n_layers=3, n_bins=50).

### 4. Alpha is Faster than VR (3-21%)
**Claim**: 20-30% faster at equal accuracy for ≤3D point clouds.
**Evidence**: measured 3.5-3.9s (Alpha) vs 3.9-4.4s (VR) for sphere_torus + Landscape + SVM.
**Practical**: Use Alpha for ≤3D; VR only when metric is non-Euclidean.

### 5. Topology Survives Moderate Noise
**Claim**: β₁ signal survives σ=0.15 Gaussian noise at 100% accuracy.
**Evidence**: All 112 pipeline combos on sphere_torus at σ=0.15 ≥ 99.5%.
**Practical**: Denoise first, then filter features with lifetime < noise_level.

### 6. Non-Linear Classifiers Help on Real Data
**Claim**: SVM-RBF adds value on ECG200 (76% vs ~72% logistic) but not on synthetic.
**Evidence**: Sulowska: 30pp gap linear vs non-linear on ECG5000.
**Practical**: Start with Logistic Regression; upgrade if accuracy < 0.9.

### 7. Pipeline Stages Interact
**Claim**: Best vectorizer depends on classifier choice.
**Evidence**: Image+RF (75.0%) > Image+SVM (66.5%); Landscape+SVM (76.0%) > Landscape+RF (73.0%).
**Practical**: Run a 2×2×2 factorial before committing to a full sweep.

### 8. Betti Curves Are Underrated
**Claim**: Strong middle-ground — better than images, simpler than landscapes.
**Evidence**: Chung & Lawson 2022 unified framework. Faster than both PI and PL.
**Practical**: Use Betti curves when runtime matters more than 1-2pp accuracy.

### 9. The Research Gap is Real
**Claim**: No prior study varies all three pipeline stages simultaneously.
**Evidence**: Conti fixes classifiers, Ali fixes filtrations, Sulowska fixes VR, Barnes fixes filtrations.
**Practical**: This is the dissertation's core contribution.

### 10. Reproducibility Requires Pinning
**Claim**: giotto-tda's sklearn==1.3.2 pin creates dependency conflicts with the broader ecosystem.
**Evidence**: tslearn upgrades sklearn → breaks giotto-tda. Docker/conda recommended.
**Practical**: Pin all versions. Our `requirements.txt` is the lockfile.

---

## APPENDIX: 7-PHASE PROJECT PLAN

| Phase | Duration | Goal | Key Deliverable | Status |
|---|---|---|---|---|
| 1. Foundation | 1 week | Learn TDA math + minimal e2e | sphere/torus classifier = 100% | ✅ |
| 2. Data Curation | 1 week | Collect 5-8 datasets | 4 datasets cached + registry | ✅ |
| 3. Pipeline Implementation | 2 weeks | Factory pattern framework | 7F×11V×4C, YAML, SQLite | ✅ |
| 4. Benchmark Execution | 1-2 weeks | Full sweep across configs | 88 configs, normalized DB | ✅ |
| 5. Analysis | 1-2 weeks | Figures + key questions | Stage impact, noise curves, Pareto | ✅ |
| 6. Writing | 2 weeks | Manuscript | This essay framework | ✅ |
| 7. Open Source | 1 week | Reproducible release | README, requirements.txt | ✅ |
