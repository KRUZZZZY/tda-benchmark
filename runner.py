"""Pipeline runner — executes all benchmark configurations and stores results.

Supports serial (n_jobs=1, default) and parallel (n_jobs>1 via joblib)
execution. In parallel mode each worker gets its own SQLite connection;
WAL mode handles concurrent writes safely.
"""

from __future__ import annotations

import logging
import os
import time
import traceback
import zlib
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

from .config import BenchmarkConfig, DatasetConfig, FiltrationConfig, VectorizationConfig, ClassifierConfig, load_config
from .factories import ClassifierFactory, FiltrationFactory, VectorizationFactory
from .storage import ResultStore

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
#  Worker function — pure, pickleable, no shared state
# ═══════════════════════════════════════════════════════════════════════════

def _run_one_worker(
    ds: DatasetConfig,
    fil: FiltrationConfig,
    vec: VectorizationConfig,
    clf: ClassifierConfig,
    rep: int,
    cv_folds: int,
    random_seed: int,
    db_path: str,
    project_root: str,
) -> dict[str, Any]:
    """Execute a single pipeline configuration in a worker process.

    Returns a dict with status + metrics for the parent to aggregate.
    Each worker opens its own ResultStore connection to the shared DB.
    """
    store = ResultStore(db_path)
    # Deterministic per-dataset seed: zlib.crc32 is stable across processes
    # (Python's hash() is salted per interpreter via PYTHONHASHSEED).
    dataset_seed = zlib.crc32(ds.name.encode("utf-8"))
    rng = np.random.default_rng(random_seed + rep * 1000 + dataset_seed % 2**31)

    try:
        # ── Load & preprocess ──────────────────────────────────────────
        X = np.load(os.path.join(project_root, ds.path))
        y = np.load(os.path.join(project_root, ds.labels))

        if ds.subsample_points and X.ndim == 3 and X.shape[1] > ds.subsample_points:
            idx = rng.choice(X.shape[1], ds.subsample_points, replace=False)
            idx.sort()
            X = X[:, idx, :]

        if ds.max_samples and len(X) > ds.max_samples:
            idx = rng.choice(len(X), ds.max_samples, replace=False)
            X, y = X[idx], y[idx]

        if ds.modality == "time_series":
            dim = ds.takens_dimension or 3
            delay = ds.takens_delay or 1
            stride = (dim - 1) * delay
            if stride >= X.shape[1]:
                raise ValueError(f"Series length {X.shape[1]} too short for dim={dim}, delay={delay}")
            n_points = X.shape[1] - stride
            embedded = np.zeros((X.shape[0], n_points, dim), dtype=X.dtype)
            for d in range(dim):
                embedded[:, :, d] = X[:, d * delay : d * delay + n_points]
            X = embedded

        # ── Build pipeline ─────────────────────────────────────────────
        pipeline = Pipeline([
            ("filtration",  FiltrationFactory.create(fil.name, **fil.kwargs)),
            ("vectorizer",  VectorizationFactory.create(vec.name, **vec.kwargs)),
            ("classifier",  ClassifierFactory.create(clf.name, **clf.kwargs)),
        ])

        n_features = 0
        try:
            sample_idx = rng.choice(len(X), min(10, len(X)), replace=False)
            n_features = pipeline[:-1].fit_transform(X[sample_idx]).shape[1]
        except Exception:
            pass

        pipeline_params = {
            "filtration":  {"name": fil.name, **fil.kwargs},
            "vectorizer":  {"name": vec.name, **vec.kwargs},
            "classifier":  {"name": clf.name, **clf.kwargs},
        }

        train_approx = int(len(X) * (1 - 1.0 / cv_folds))

        # ── Run CV ─────────────────────────────────────────────────────
        run_id = store.start_run(
            dataset=ds.name, filtration=fil.name,
            vectorizer=vec.name, classifier=clf.name,
            repetition=rep, pipeline_params=pipeline_params,
            n_train=train_approx, n_test=len(X) - train_approx,
            n_features=n_features,
        )

        t0 = time.perf_counter()
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True,
                             random_state=random_seed + rep)
        scores = cross_validate(
            pipeline, X, y, cv=cv,
            scoring=["accuracy", "f1_weighted", "precision_weighted", "recall_weighted"],
            n_jobs=1, error_score="raise", return_train_score=False,
        )
        wall_time = time.perf_counter() - t0

        for fold_idx in range(cv_folds):
            store.save_fold(run_id, fold_idx + 1, {
                "accuracy":  float(scores["test_accuracy"][fold_idx]),
                "f1":        float(scores["test_f1_weighted"][fold_idx]),
                "precision": float(scores["test_precision_weighted"][fold_idx]),
                "recall":    float(scores["test_recall_weighted"][fold_idx]),
            })

        store.finish_run(run_id, wall_time_s=wall_time)
        avg_acc = float(scores["test_accuracy"].mean())

        return {
            "status": "ok",
            "accuracy": avg_acc,
            "wall_time": wall_time,
            "label": f"{ds.name} | {fil.name} | {vec.name} | {clf.name} | rep {rep}",
        }

    except Exception as exc:
        return {
            "status": "failed",
            "label": f"{ds.name} | {fil.name} | {vec.name} | {clf.name} | rep {rep}",
            "error": traceback.format_exc(),
        }
    finally:
        store.close()


# ═══════════════════════════════════════════════════════════════════════════

class PipelineRunner:
    """Execute a full benchmark sweep defined by a BenchmarkConfig.

    Parameters
    ----------
    config : BenchmarkConfig
        Parsed configuration.
    config_path : Path or str, optional
        Path to the YAML file (for snapshot).
    n_jobs : int, default 1
        Number of parallel workers. 1 = serial, -1 = all CPUs.
        Uses joblib with process-based backend (loky).
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        config_path: str | Path | None = None,
        n_jobs: int = 1,
    ):
        self.config = config
        self.config_path = config_path
        self.n_jobs = n_jobs
        self.store = ResultStore(config.output.db_path)
        self.rng = np.random.default_rng(config.evaluation.random_seed)
        self._setup_logging()

    def _setup_logging(self):
        level = getattr(logging, self.config.output.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=level, format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )

    def run(self):
        """Execute the full benchmark sweep (serial or parallel)."""
        config = self.config
        total = config.total_configs
        log.info(f"Starting benchmark: {config.describe()}")
        log.info(f"Results → {config.output.db_path}")
        log.info(f"Workers: {self.n_jobs} ({'serial' if self.n_jobs == 1 else 'parallel'})")

        # Save config snapshot
        self.store.save_config(yaml.dump({
            "datasets": [{"name": d.name, "path": d.path, "modality": d.modality}
                         for d in config.datasets],
            "filtrations": [{"name": f.name, **f.kwargs} for f in config.filtrations],
            "vectorizations": [{"name": v.name, **v.kwargs} for v in config.vectorizations],
            "classifiers": [{"name": c.name, **c.kwargs} for c in config.classifiers],
            "evaluation": {
                "cv_folds": config.evaluation.cv_folds,
                "scoring": config.evaluation.scoring,
                "random_seed": config.evaluation.random_seed,
                "repetitions": config.evaluation.repetitions,
            },
        }))

        # Build the flat list of all configs
        jobs = []
        for ds, fil, vec, clf in product(
            config.datasets, config.filtrations,
            config.vectorizations, config.classifiers,
        ):
            for rep in range(1, config.evaluation.repetitions + 1):
                jobs.append((ds, fil, vec, clf, rep))

        if self.n_jobs == 1:
            self._run_serial(jobs, total)
        else:
            self._run_parallel(jobs, total)

        log.info(f"Benchmark complete. {total} configs attempted.")
        summary = self.store.summary()
        if summary:
            self._print_summary(summary)
        self.store.close()

    # ── Serial path (unchanged) ──────────────────────────────────────────

    def _run_serial(self, jobs: list, total: int):
        completed = 0
        for ds, fil, vec, clf, rep in jobs:
            completed += 1
            label = f"{ds.name} | {fil.name} | {vec.name} | {clf.name} | rep {rep}/{self.config.evaluation.repetitions}"
            log.info(f"[{completed}/{total}] {label}")

            result = _run_one_worker(
                ds, fil, vec, clf, rep,
                cv_folds=self.config.evaluation.cv_folds,
                random_seed=self.config.evaluation.random_seed,
                db_path=self.config.output.db_path,
                project_root=str(Path(__file__).parent.parent.parent),
            )
            if result["status"] == "ok":
                log.info(f"  ✓ accuracy={result['accuracy']:.4f}  wall={result['wall_time']:.1f}s")
            else:
                log.error(f"FAILED: {result['label']}\n{result['error']}")

    # ── Parallel path ────────────────────────────────────────────────────

    def _run_parallel(self, jobs: list, total: int):
        from joblib import Parallel, delayed

        cv_folds = self.config.evaluation.cv_folds
        random_seed = self.config.evaluation.random_seed
        db_path = self.config.output.db_path
        project_root = str(Path(__file__).parent.parent.parent)

        log.info(f"Dispatching {total} configs across {self.n_jobs} workers...")

        results = Parallel(n_jobs=self.n_jobs, backend="loky", verbose=0)(
            delayed(_run_one_worker)(
                ds, fil, vec, clf, rep,
                cv_folds=cv_folds,
                random_seed=random_seed,
                db_path=db_path,
                project_root=project_root,
            )
            for ds, fil, vec, clf, rep in jobs
        )

        ok_count = 0
        fail_count = 0
        for r in results:
            if r["status"] == "ok":
                ok_count += 1
                log.info(f"  ✓ {r['label']}  accuracy={r['accuracy']:.4f}  wall={r['wall_time']:.1f}s")
            else:
                fail_count += 1
                log.error(f"FAILED: {r['label']}\n{r['error']}")

        log.info(f"Complete: {ok_count} ok, {fail_count} failed")

    @staticmethod
    def _print_summary(rows: list[dict]):
        print(f"\n{'='*80}")
        print(f"{'Dataset':<18} {'Filtration':<18} {'Vectorizer':<22} {'Classifier':<16} {'Acc':>8} {'CI95':>16} {'Time':>8}")
        print(f"{'-'*80}")
        for r in rows:
            ci = f"[{r['ci_lower']:.3f}, {r['ci_upper']:.3f}]" if r.get('ci_lower') is not None else "N/A"
            print(
                f"{r['dataset']:<18} {r['filtration']:<18} {r['vectorizer']:<22} "
                f"{r['classifier']:<16} {r['mean_accuracy']:>8.4f} {ci:>16} {r.get('mean_wall_time', 0):>7.1f}s"
            )


def run_benchmark(config_path: str | Path | None = None, n_jobs: int = 1):
    """Entry point: load config and run the full benchmark.

    Parameters
    ----------
    config_path : Path or str, optional
        Path to YAML config file.
    n_jobs : int, default 1
        Number of parallel workers. -1 = all CPUs.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    cfg = load_config(config_path)
    runner = PipelineRunner(cfg, config_path=config_path, n_jobs=n_jobs)
    runner.run()
