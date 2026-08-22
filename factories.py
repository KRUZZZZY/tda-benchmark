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
            # Learned vectorizers (torch-backed; lazy-imported — safe without torch).
            # See requirements-learned.md for the .venv-perslay install recipe.
            "perslay": _PersLayLayer,
            "hofer_deepset": _HoferDeepSetLayer,
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
            "perslay", "hofer_deepset",
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


# ── Learned vectorizers (torch-backed, lazy-imported) ────────────────────────
#
# These two entries implement the #8 "learned vectorizer" expansion: a
# PersLay-style trainable layer (Karimi et al., ICML 2020) and a Hofer-style
# deep-set input layer (Hofer et al., ICLR 2017). They are STUBS: they follow
# the factory's sklearn BaseEstimator/TransformerMixin contract and provide the
# defining architecture (per-point MLP + permutation-invariant additive
# pooling), but they do NOT train in this revision and are NOT executed by any
# sweep until torch is installed.
#
# Critical property: torch (and perslay) are imported ONLY inside methods, so
# `import factories` / `VectorizationFactory.list_available()` succeed in the
# stock .venv-tda (no torch). Any attempt to actually fit/transform without
# torch raises ImportError with the requirements-learned.md pointer.
#
# Env preparation: see requirements-learned.md (repo root) — install into a
# SEPARATE .venv-perslay to protect the sklearn 1.3.2 pin that giotto-tda 0.6.2
# requires.

_TORCH_MISSING_MSG = (
    "{cls} requires torch ({missing}); see requirements-learned.md for the "
    ".venv-perslay install recipe. The factory entry itself is safe to import "
    "without torch — only fit/transform need it."
)


class _LearnedVectorizerBase(BaseEstimator, TransformerMixin):
    """Shared lazy-import + diagram-batch handling for torch-backed vectorizers.

    Input contract (gtda convention): a padded 3D array (n_samples, n_points, 3)
    of [birth, death, homology_dim] triples, or a list of variable-length
    (n_i, 3) arrays (padded internally with NaN). Output: 2D (n_samples,
    out_dim) — already classifier-ready, so the factory's flatten wrapper is a
    no-op for these entries.
    """

    #: extra module (besides torch) that must be importable; "" for none
    _EXTRA_MODULE = ""

    def __init__(self, hidden_dim: int = 32, out_dim: int = 16,
                 pooling: str = "mean", seed: int = 42, n_jobs: int = 1):
        self.hidden_dim = hidden_dim
        self.out_dim = out_dim
        self.pooling = pooling
        self.seed = seed
        self.n_jobs = n_jobs  # accepted for factory parity; ignored (single-threaded stub)

    # ── helpers ────────────────────────────────────────────────────────────

    def _ensure_imports(self):
        """Lazy torch (+ perslay) import; raise the documented error if absent."""
        try:
            import torch  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                _TORCH_MISSING_MSG.format(cls=type(self).__name__,
                                          missing="torch")
            ) from exc
        if self._EXTRA_MODULE:
            import importlib.util
            if importlib.util.find_spec(self._EXTRA_MODULE) is None:
                raise ImportError(
                    _TORCH_MISSING_MSG.format(
                        cls=type(self).__name__,
                        missing=f"torch + {self._EXTRA_MODULE}",
                    )
                )

    @staticmethod
    def _as_batch(X):
        """Normalise list-of-diagrams input to a padded (n, pts, 3) float array."""
        if isinstance(X, list):
            X = _pad_and_stack(X)
        arr = np.asarray(X, dtype=np.float64)
        if arr.ndim != 3 or arr.shape[2] != 3:
            raise ValueError(
                f"{type(X).__name__}: expected (n_samples, n_points, 3) diagram "
                f"batch, got {arr.shape}"
            )
        return arr

    def _build_torch_module(self):
        """Construct the trainable torch.nn.Module (imported lazily)."""
        import torch
        from torch import nn

        class _AdditivePoolingLayer(nn.Module):
            """Per-point MLP + permutation-invariant pooling — the defining
            architecture of PersLay (Karimi et al. 2020) and deep sets
            (Zaheer et al. 2017) / Hofer et al. (ICLR 2017). Shared weights
            across points; pooling is over the point axis, so the output is
            invariant to point ordering (and, with NaN masking, to padding).
            """

            def __init__(self, in_dim: int, hidden_dim: int, out_dim: int,
                         pooling: str, seed: int):
                super().__init__()
                torch.manual_seed(seed)
                self.pooling = pooling
                self.net = nn.Sequential(
                    nn.Linear(in_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Linear(hidden_dim, out_dim),
                )

            def forward(self, x, valid):
                # x: (n, pts, in_dim), valid: (n, pts) bool mask (padding rows)
                h = self.net(x)                      # (n, pts, out_dim)
                h = h.masked_fill(~valid.unsqueeze(-1), 0.0)
                if self.pooling == "mean":
                    return h.sum(dim=1) / valid.sum(dim=1, keepdim=True).clamp(min=1.0)
                return h.sum(dim=1)                  # "sum" pooling

        in_dim = 4  # [birth, death, death-birth, dim]
        return _AdditivePoolingLayer(in_dim, self.hidden_dim, self.out_dim,
                                     self.pooling, self.seed)

    # ── sklearn interface ──────────────────────────────────────────────────

    def fit(self, X, y=None):
        """Lazy-import torch, build the (untrained) layer, store it."""
        self._ensure_imports()
        self.layer_ = self._build_torch_module()
        return self

    def transform(self, X):
        """Lazy-import torch and run the layer's forward pass (no training)."""
        self._ensure_imports()
        if not hasattr(self, "layer_"):
            self.fit(X)
        import torch
        arr = self._as_batch(X)
        with torch.no_grad():
            births = arr[:, :, 0]
            deaths = arr[:, :, 1]
            lifespans = deaths - births
            dims = arr[:, :, 2]
            valid = ~(np.isnan(arr[:, :, 0]) | np.isnan(arr[:, :, 1]) |
                      (lifespans <= 0))
            feat = np.stack([births, deaths, lifespans, dims], axis=-1)
            feat = np.nan_to_num(feat, nan=0.0)
            out = self.layer_(torch.from_numpy(feat).float(),
                              torch.from_numpy(valid)).numpy()
        return out


class _PersLayLayer(_LearnedVectorizerBase):
    """PersLay-style trainable layer stub (Karimi et al., ICML 2020).

    Architecture: per-point MLP over [birth, death, persistence, dim] followed
    by permutation-invariant additive pooling — the defining property of
    PersLay. This stub builds and runs the layer with default (untrained)
    weights; the trainable fit loop is intentionally NOT implemented in this
    revision (additive-only, no torch in the stock venv).

    Registration: VectorizationFactory.create("perslay", ...). The factory's
    flatten wrapper is a no-op because transform() already emits 2D output.
    """

    _EXTRA_MODULE = "perslay"


class _HoferDeepSetLayer(_LearnedVectorizerBase):
    """Hofer-style deep-set input layer stub (Hofer et al., ICLR 2017).

    Architecture: shared per-point MLP + sum/mean pooling over the diagram's
    points — a deep-set encoder applied to the persistence diagram seen as a
    point cloud in birth-death space. Same lazy-import contract as
    _PersLayLayer; only torch is required (no perslay package needed).

    Registration: VectorizationFactory.create("hofer_deepset", ...).
    """

    _EXTRA_MODULE = ""  # torch only
