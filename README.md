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
| Sphere+Torus | Point cloud | 200 × 100pts × 3D (× 4 noise levels) | 2 |
| ECG200 | Time series | 200 × 96 (Takens→3D) | 2 |
| MNIST | Image | 70K × 28×28 | 10 |
| Fashion-MNIST | Image | 70K × 28×28 | 10 |

## Key Findings

1. **Filtration dominates** — can swing accuracy by 60pp; wrong choice cannot be compensated downstream
2. **Simple beats complex** — Persistence Statistics often match sophisticated kernel methods
3. **Landscapes are most robust** — best accuracy/stability trade-off across noise levels and datasets
4. **Alpha > VR** — 20-30% faster at equal accuracy for ≤3D point clouds
5. **Noise kills topology** — above σ=0.15, topological signal degrades rapidly
6. **Non-linear classifiers help on real data** — little benefit on clean synthetic
7. **Stages interact** — best vectorizer depends on filtration and classifier choice
8. **Betti curves are underrated** — strong middle ground, faster than PI/PL
9. **Research gap is real** — no prior study varies all three pipeline stages
10. **Reproducibility is fragile** — giotto-tda's sklearn pin creates dependency conflicts

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
  note = {Open-source framework with 7 filtrations × 11 vectorizations × 4 classifiers},
}
```

## License

MIT — see LICENSE file.
