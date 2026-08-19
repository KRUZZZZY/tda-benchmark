"""
TDA benchmark factories — create filtration, vectorization, and classifier
components by name. All return sklearn-compatible transformers/estimators.

Usage:
    from tda_benchmark.factories import FiltrationFactory
    vr = FiltrationFactory.create("vietoris_rips", homology_dimensions=(0, 1))
"""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import FunctionTransformer
from sklearn.svm import SVC


def _pad_and_stack(diagrams: list) -> np.ndarray:
    """Pad variable-length diagram lists to a uniform 3D array."""
    if not diagrams:
        raise ValueError("Empty diagram list — nothing to pad")
    max_len = max(d.shape[0] for d in diagrams)
    padded = []
    for d in diagrams:
        if d.shape[0] < max_len:
            pad = np.full((max_len - d.shape[0], 3), np.nan)
            d = np.vstack([d, pad])
        padded.append(d)
    return np.array(padded)


# ── Filtration ──────────────────────────────────────────────────────────────

class FiltrationFactory:
    """Create persistent homology filtration transformers by name.

    Available: vietoris_rips, sparse_rips, euclidean_cech, weighted_rips,
               cubical, weak_alpha, flagser.
    """

    @staticmethod
    def create(name: str, **kwargs):
        from gtda.homology import (
            CubicalPersistence,
            EuclideanCechPersistence,
            FlagserPersistence,
            SparseRipsPersistence,
            VietorisRipsPersistence,
            WeakAlphaPersistence,
            WeightedRipsPersistence,
        )

        mapping = {
            "vietoris_rips": VietorisRipsPersistence,
            "sparse_rips": SparseRipsPersistence,
            "euclidean_cech": EuclideanCechPersistence,
            "weighted_rips": WeightedRipsPersistence,
            "cubical": CubicalPersistence,
            "weak_alpha": WeakAlphaPersistence,
            "flagser": FlagserPersistence,
        }
        cls = mapping.get(name)
        if cls is None:
            raise ValueError(f"Unknown filtration: {name}. Available: {sorted(mapping)}")
        defaults = {"n_jobs": 1}
        defaults.update(kwargs)
        return cls(**defaults)

    @staticmethod
    def list_available() -> list[str]:
        return [
            "vietoris_rips", "sparse_rips", "euclidean_cech",
            "weighted_rips", "cubical", "weak_alpha", "flagser",
        ]


# ── Vectorization ───────────────────────────────────────────────────────────

class VectorizationFactory:
    """Create persistence diagram vectorization transformers by name."""

    @staticmethod
    def create(name: str, **kwargs):
        from gtda.diagrams import (
            Amplitude,
            BettiCurve,
            ComplexPolynomial,
            HeatKernel,
            NumberOfPoints,
            PersistenceEntropy,
            PersistenceImage,
            PersistenceLandscape,
            PairwiseDistance,
            Silhouette,
        )

        mapping = {
            "persistence_image": PersistenceImage,
            "persistence_landscape": PersistenceLandscape,
            "betti_curve": BettiCurve,
            "silhouette": Silhouette,
            "persistence_entropy": PersistenceEntropy,
            "amplitude": Amplitude,
            "number_of_points": NumberOfPoints,
            "complex_polynomial": ComplexPolynomial,
            "heat_kernel": HeatKernel,
            "pairwise_distance": PairwiseDistance,
            "persistence_statistics": _PersistenceStatistics,
        }
        cls = mapping.get(name)
        if cls is None:
            raise ValueError(f"Unknown vectorization: {name}. Available: {sorted(mapping)}")

        defaults = {"n_jobs": 1}
        defaults.update(kwargs)
        vec = cls(**defaults)

        from sklearn.pipeline import Pipeline
        if name != "persistence_statistics":
            return Pipeline([
                ("vec", vec),
                ("flatten", FunctionTransformer(
                    lambda x: x.reshape(x.shape[0], -1), validate=False,
                )),
            ])
        return vec

    @staticmethod
    def list_available() -> list[str]:
        return [
            "persistence_image", "persistence_landscape", "betti_curve",
            "silhouette", "persistence_entropy", "amplitude",
            "number_of_points", "complex_polynomial", "heat_kernel",
            "pairwise_distance", "persistence_statistics",
        ]


class _PersistenceStatistics(BaseEstimator, TransformerMixin):
    """Summary statistics: mean/std/min/max of births, deaths, lifespans
    per homology dimension. Produces 2D output directly."""

    def __init__(self, n_jobs: int = 1):
        self.n_jobs = n_jobs

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if isinstance(X, list):
            X = _pad_and_stack(X)
        features = []
        dims = np.unique(X[:, :, 2][~np.isnan(X[:, :, 2])])
        if len(dims) == 0:
            dims = [0]
        for d in sorted(dims):
            mask = X[:, :, 2] == d
            births = np.where(mask, X[:, :, 0], np.nan)
            deaths = np.where(mask, X[:, :, 1], np.nan)
            lifespans = deaths - births
            for arr, _prefix in [(births, "birth"), (deaths, "death"), (lifespans, "lifespan")]:
                features.extend([
                    np.nanmean(arr, axis=1),
                    np.nanstd(arr, axis=1),
                    np.nanmin(arr, axis=1),
                    np.nanmax(arr, axis=1),
                ])
        return np.column_stack(features)


# ── Classifier ──────────────────────────────────────────────────────────────

class ClassifierFactory:
    """Create sklearn classifiers by name.

    Available: svm_linear, svm_rbf, random_forest, logistic.
    """

    _DEFAULTS = {
        "svm_linear": {"kernel": "linear", "C": 1.0, "random_state": 42},
        "svm_rbf": {"kernel": "rbf", "C": 1.0, "gamma": "scale", "random_state": 42},
        "random_forest": {"n_estimators": 100, "random_state": 42},
        "logistic": {"max_iter": 1000, "random_state": 42},
    }

    @staticmethod
    def create(name: str, **kwargs):
        mapping = {
            "svm_linear": SVC,
            "svm_rbf": SVC,
            "random_forest": RandomForestClassifier,
            "logistic": LogisticRegression,
        }
        cls = mapping.get(name)
        if cls is None:
            raise ValueError(f"Unknown classifier: {name}. Available: {sorted(mapping)}")

        params = dict(ClassifierFactory._DEFAULTS.get(name, {}))
        params.update(kwargs)
        return cls(**params)

    @staticmethod
    def list_available() -> list[str]:
        return list(ClassifierFactory._DEFAULTS.keys())
