"""Expansion #20 — framework smoke tests.

Runs in < 30 s. NO heavy sweeps: the heaviest test is a single
Vietoris-Rips -> Persistence-Image -> SVM round trip on a 20-point
synthetic cloud (well under a second on one core).

Import-light by design: the top-level package import must succeed without
torch — the #8 learned-vectorizer entries (perslay, hofer_deepset) are
lazy-imported stubs that only require torch inside fit/transform.

Run from the repo root:
    python -m pytest tests/          (pytest installed)
or without pytest (venv has none):
    python - <<'PY'
    import sys; sys.path.insert(0, "tests")
    import test_framework_smoke as t
    for f in (t.test_import_shim_public_api, t.test_driver_importlib_shim_loads_functional_package,
              t.test_config_dataclasses_construct_and_count, t.test_factories_list_expected_entries,
              t.test_unknown_factory_names_raise, t.test_tiny_vr_pi_svm_roundtrip):
        f(); print(f.__name__, "OK")
    PY
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from sklearn.model_selection import train_test_split

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# The framework package lives at the repo root, whose directory name is
# "tda-benchmark" (hyphen) — NOT importable as tda_benchmark by name alone.
# Installed (pip install -e .) it imports directly; uninstalled we replicate
# the drivers' importlib shim (scripts/sweep_large_n.py etc.) verbatim.
try:
    import tda_benchmark  # noqa: F401
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location(
        "tda_benchmark",
        os.path.join(str(REPO_ROOT), "__init__.py"),
        submodule_search_locations=[str(REPO_ROOT)],
    )
    assert spec is not None and spec.loader is not None, "shim spec failed to build"
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["tda_benchmark"] = pkg
    spec.loader.exec_module(pkg)

import tda_benchmark  # noqa: E402
from tda_benchmark.config import (  # noqa: E402
    BenchmarkConfig,
    ClassifierConfig,
    DatasetConfig,
    EvaluationConfig,
    FiltrationConfig,
    OutputConfig,
    VectorizationConfig,
)
from tda_benchmark.factories import (  # noqa: E402
    ClassifierFactory,
    FiltrationFactory,
    VectorizationFactory,
)


def test_import_shim_public_api():
    """The package's public API surface is importable after a plain import."""
    for name in (
        "BenchmarkConfig",
        "ClassifierFactory",
        "FiltrationFactory",
        "PipelineRunner",
        "ResultStore",
        "VectorizationFactory",
        "load_config",
        "run_benchmark",
    ):
        assert hasattr(tda_benchmark, name), name


def test_driver_importlib_shim_loads_functional_package():
    """The drivers' importlib shim (scripts/*.py) yields a working package.

    Reproduces the exact shim from scripts/sweep_large_n.py
    (spec_from_file_location on the repo-root __init__.py with
    submodule_search_locations=[repo]) under a fresh module name so it does
    not collide with the already-imported tda_benchmark. Once the framework
    is pip-installed the shim is redundant but must keep working for the
    uninstalled scripts/ workflow.
    """
    name = "tda_benchmark_shim_probe"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(
        name,
        os.path.join(str(REPO_ROOT), "__init__.py"),
        submodule_search_locations=[str(REPO_ROOT)],
    )
    assert spec is not None and spec.loader is not None, "shim spec failed to build"
    pkg = importlib.util.module_from_spec(spec)
    sys.modules[name] = pkg
    spec.loader.exec_module(pkg)

    assert pkg.load_config is not None
    assert "vietoris_rips" in pkg.FiltrationFactory.list_available()
    assert pkg.ResultStore is not None


def test_config_dataclasses_construct_and_count():
    """Config dataclasses construct programmatically and count configs."""
    ds = DatasetConfig(
        name="d", path="x.npy", labels="y.npy", modality="point_cloud")
    cfg = BenchmarkConfig(
        datasets=[ds],
        filtrations=[FiltrationConfig("vr"), FiltrationConfig("cubical")],
        vectorizations=[VectorizationConfig("betti_curve")] * 3,
        classifiers=[
            ClassifierConfig("svm_rbf"), ClassifierConfig("random_forest")],
        evaluation=EvaluationConfig(cv_folds=5, repetitions=1),
        output=OutputConfig(db_path=":memory:"),
    )
    assert cfg.total_configs == 1 * 2 * 3 * 2 * 1  # = 12
    assert "12 configs" in cfg.describe()
    # Optional-field defaults
    assert ds.max_samples is None and ds.subsample_points is None
    assert ds.takens_dimension is None and ds.takens_delay is None


def test_factories_list_expected_entries():
    """Factory registries contain the expected component names.

    Core names are asserted as a SUBSET so future additive registrations
    (e.g. more filtrations) do not break the smoke test; the #8 learned
    vectorizer stubs are asserted present because they are part of the
    current working tree (lazy-imported, torch-free at import time).
    """
    filtrations = set(FiltrationFactory.list_available())
    assert {
        "vietoris_rips", "weak_alpha", "sparse_rips", "cubical",
        "weighted_rips", "euclidean_cech", "flagser",
    } <= filtrations

    vectorizers = set(VectorizationFactory.list_available())
    assert {
        "persistence_image", "persistence_landscape", "betti_curve",
        "silhouette", "persistence_entropy", "amplitude",
        "number_of_points", "complex_polynomial", "heat_kernel",
        "pairwise_distance", "persistence_statistics",
    } <= vectorizers
    # #8 learned-vectorizer stubs (torch-backed, lazy-imported)
    assert {"perslay", "hofer_deepset"} <= vectorizers

    classifiers = set(ClassifierFactory.list_available())
    assert {"svm_linear", "svm_rbf", "random_forest", "logistic"} == classifiers


def test_unknown_factory_names_raise():
    """Unknown names raise ValueError with the available list in the message."""
    for factory, bad in (
        (FiltrationFactory, "not_a_filtration"),
        (VectorizationFactory, "not_a_vectorizer"),
        (ClassifierFactory, "not_a_classifier"),
    ):
        with pytest.raises(ValueError):
            factory.create(bad)


def test_tiny_vr_pi_svm_roundtrip():
    """20-point synthetic cloud: VR -> Persistence Image -> SVM-RBF.

    Two well-separated Gaussians in R^3. Expects a plausible accuracy (far
    above chance); asserts a lower bound of 0.6 so the test is robust to the
    tiny train set while still catching a broken pipeline (wrong diagram
    shape, NaN features, degenerate classifier).
    """
    pytest.importorskip("gtda")  # skip cleanly if giotto-tda is unavailable

    # 20 sample-clouds (10 per class), 24 points each, in R^3. The classes
    # differ in TOPOLOGY, not location: class 0 is a noisy circle (one
    # persistent H1 loop, beta_1 = 1), class 1 is a uniform ball (H1 is
    # noise). Location-only differences are invisible to persistent homology
    # (translation invariance) and would give chance accuracy — mirroring
    # the paper's sphere/torus design (beta_1 = 0 vs 2, S4.2).
    n_per_class, pts_per_cloud = 10, 24
    rng = np.random.default_rng(42)
    X = np.empty((2 * n_per_class, pts_per_cloud, 3))
    for i in range(n_per_class):
        th = np.linspace(0.0, 2.0 * np.pi, pts_per_cloud, endpoint=False)
        circle = np.column_stack([np.cos(th), np.sin(th), np.zeros(pts_per_cloud)])
        X[i] = circle + rng.normal(scale=0.04, size=(pts_per_cloud, 3))
        v = rng.normal(size=(pts_per_cloud, 3))
        radii = rng.uniform(0.0, 1.0, size=(pts_per_cloud, 1))
        X[n_per_class + i] = v / np.linalg.norm(v, axis=1, keepdims=True) * radii
    y = np.array([0] * n_per_class + [1] * n_per_class)

    filtration = FiltrationFactory.create(
        "vietoris_rips", homology_dimensions=(0, 1))
    vectorizer = VectorizationFactory.create(
        "persistence_image", sigma=0.2, n_bins=10)
    classifier = ClassifierFactory.create("svm_rbf")

    diagrams = filtration.fit_transform(X)  # list of (n_points, 3) arrays
    features = vectorizer.fit_transform(diagrams)  # (20, n_features)

    assert features.ndim == 2
    assert features.shape[0] == 20
    assert features.shape[1] >= 10
    assert np.isfinite(features).all(), "NaN/Inf leaked into vectorized features"

    Xtr, Xte, ytr, yte = train_test_split(
        features, y, test_size=0.4, random_state=42, stratify=y)
    classifier.fit(Xtr, ytr)
    acc = classifier.score(Xte, yte)
    assert acc >= 0.6, f"plausible accuracy expected, got {acc:.2f}"
