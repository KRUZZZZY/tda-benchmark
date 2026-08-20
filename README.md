# TDA Pipeline Benchmark

Systematic comparison of persistent homology pipelines for classification:
**filtration × vectorization × classifier × dataset**.

## Quick Start

```bash
# 1. Create environment
python3 -m venv .venv-tda
source .venv-tda/bin/activate
pip install -r projects/tda-benchmark/requirements.txt

# 2. Download datasets
python scripts/tda_download_datasets.py

# 3. Run benchmark
python -c "
import sys; sys.path.insert(0, 'scripts')
from tda_benchmark.runner import run_benchmark
run_benchmark('projects/tda-benchmark/config.yaml')
"

# 4. Analyze results
python projects/tda-benchmark/analysis.py data/tda/results.db
```

## Architecture

```
projects/tda-benchmark/
├── factories.py      # FiltrationFactory, VectorizationFactory, ClassifierFactory
├── config.py         # YAML config loader (dataclass-based)
├── config.yaml       # Default benchmark sweep definition
├── storage.py        # Normalized SQLite result store
├── runner.py         # PipelineRunner — Cartesian product executor
├── analysis.py       # Report generator and statistical analysis
├── essay_framework.py # Dissertation essay structure + 10 key insights
└── requirements.txt  # Pinned dependencies
```

## Pipeline Components

| Stage | Available Methods | Count |
|---|---|---|
| Filtration | VR, Alpha, Sparse Rips, Čech, Cubical, Weighted Rips, Flagser | 7 |
| Vectorization | PI, PL, Betti curves, Silhouette, Entropy, Amplitude, Heat Kernel, Complex Polynomials, Pairwise Distance, Number of Points, Persistence Statistics | 11 |
| Classifier | SVM-linear, SVM-RBF, Random Forest, Logistic Regression | 4 |

## Datasets

| Name | Modality | Shape | Classes |
|---|---|---|---|
| Sphere+Torus | Point cloud | 200 × 100pts × 3D (× 4 noise levels: σ=0.00/0.05/0.15/0.30) | 2 |
| ECG200 | Time series | 200 × 96 (Takens→3D) | 2 |
| MNIST 0/1 | Image | 400 × 28×28 (binary subset, 200/class) | 2 |

## Key Findings

1. **Stage importance is modality-dependent** — vectorization dominates on time series (ECG200: 6.1pp marginal range across 7 vectorizers, 95% CI [4.8, 7.4]); filtration dominates on images (MNIST: cubical 98.0% vs Vietoris-Rips 96.25%). Qualifies the widely cited claim that filtration always dominates.
2. **Simple beats complex** — Persistence Statistics match kernel-based vectorizers on real data with zero hyperparameters (ECG200: 75.2% vs Landscapes 74.7%)
3. **Cubical wins on images** — the grid-aligned filtration captures image topology that point-cloud filtrations destroy
4. **Alpha > VR on 3D point clouds** — 11-21% faster at identical accuracy (measured on sphere/torus, Landscape+SVM)
5. **Noise robustness** — the topological signal survives Gaussian noise to σ=0.30 (99.85% mean accuracy on the 112 sphere/torus configs at that level, min 98.5%)
6. **Non-linear classifiers help on real data** — little benefit on clean synthetic
7. **Stages interact** — best vectorizer depends on filtration and classifier choice
8. **Betti curves are a strong middle ground** — competitive accuracy, faster than PI/PL
9. **Research gap is real** — a standardized harness varying all three stages (616 executed configs of a 672 grid) is exactly what the TDA community has called for
10. **Reproducibility is fragile** — giotto-tda's sklearn pin creates dependency conflicts; the repo pins versions and seeds

## Results Storage

SQLite database with normalized schema:

```
runs          — (dataset, filtration, vectorizer, classifier, rep, timings)
fold_results  — per-fold accuracy, F1, precision, recall
run_metadata  — pipeline parameters as JSON, data dimensions
config_snapshot — YAML config for reproducibility
```

Query example:
```sql
SELECT filtration, vectorizer, AVG(accuracy) as mean_acc
FROM runs r JOIN fold_results f ON r.run_id = f.run_id
WHERE dataset = 'ecg200'
GROUP BY filtration, vectorizer
ORDER BY mean_acc DESC;
```

## Citation

If you use this benchmark in your research, please cite:

```
@misc{tda-pipeline-benchmark,
  author = {AI-KOS TDA Benchmark},
  title = {A Systematic Benchmark of Persistent Homology Pipelines for Classification},
  year = {2026},
  note = {616-configuration benchmark: 6 datasets × 4 filtrations × 7 vectorizations × 4 classifiers},
}
```

## License

MIT — see LICENSE file.
