"""YAML configuration loader for TDA benchmark."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DatasetConfig:
    name: str
    path: str
    labels: str
    modality: str
    description: str = ""
    takens_dimension: int | None = None
    takens_delay: int | None = None
    max_samples: int | None = None      # cap number of samples
    subsample_points: int | None = None  # cap points per cloud


@dataclass
class FiltrationConfig:
    name: str
    kwargs: dict = field(default_factory=dict)


@dataclass
class VectorizationConfig:
    name: str
    kwargs: dict = field(default_factory=dict)


@dataclass
class ClassifierConfig:
    name: str
    kwargs: dict = field(default_factory=dict)


@dataclass
class EvaluationConfig:
    cv_folds: int = 5
    scoring: str = "accuracy"
    random_seed: int = 42
    repetitions: int = 1


@dataclass
class OutputConfig:
    db_path: str = "data/tda/results.db"
    log_level: str = "INFO"


@dataclass
class BenchmarkConfig:
    datasets: list[DatasetConfig]
    filtrations: list[FiltrationConfig]
    vectorizations: list[VectorizationConfig]
    classifiers: list[ClassifierConfig]
    evaluation: EvaluationConfig
    output: OutputConfig

    @property
    def total_configs(self) -> int:
        return (
            len(self.datasets)
            * len(self.filtrations)
            * len(self.vectorizations)
            * len(self.classifiers)
            * self.evaluation.repetitions
        )

    def describe(self) -> str:
        return (
            f"{len(self.datasets)} datasets × "
            f"{len(self.filtrations)} filtrations × "
            f"{len(self.vectorizations)} vectorizations × "
            f"{len(self.classifiers)} classifiers × "
            f"{self.evaluation.repetitions} reps = "
            f"{self.total_configs} configs"
        )


def load_config(path: str | Path) -> BenchmarkConfig:
    """Load benchmark configuration from YAML file."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    datasets = [_parse_dataset(d) for d in raw.get("datasets", [])]
    filtrations = [_parse_filtration(f) for f in raw.get("filtrations", [])]
    vectorizations = [_parse_vectorization(v) for v in raw.get("vectorizations", [])]
    classifiers = [_parse_classifier(c) for c in raw.get("classifiers", [])]

    eval_raw = raw.get("evaluation", {})
    evaluation = EvaluationConfig(
        cv_folds=eval_raw.get("cv_folds", 5),
        scoring=eval_raw.get("scoring", "accuracy"),
        random_seed=eval_raw.get("random_seed", 42),
        repetitions=eval_raw.get("repetitions", 1),
    )

    out_raw = raw.get("output", {})
    output = OutputConfig(
        db_path=out_raw.get("db_path", "data/tda/results.db"),
        log_level=out_raw.get("log_level", "INFO"),
    )

    return BenchmarkConfig(
        datasets=datasets,
        filtrations=filtrations,
        vectorizations=vectorizations,
        classifiers=classifiers,
        evaluation=evaluation,
        output=output,
    )


def _parse_dataset(d: dict) -> DatasetConfig:
    return DatasetConfig(
        name=d["name"],
        path=d["path"],
        labels=d["labels"],
        modality=d.get("modality", "unknown"),
        description=d.get("description", ""),
        takens_dimension=d.get("takens_dimension"),
        takens_delay=d.get("takens_delay"),
        max_samples=d.get("max_samples"),
        subsample_points=d.get("subsample_points"),
    )


def _parse_filtration(f: dict) -> FiltrationConfig:
    name = f["name"]
    kwargs = {k: v for k, v in f.items() if k not in ("name",)}
    return FiltrationConfig(name=name, kwargs=kwargs)


def _parse_vectorization(v: dict) -> VectorizationConfig:
    name = v["name"]
    kwargs = {k: v for k, v in v.items() if k not in ("name",)}
    return VectorizationConfig(name=name, kwargs=kwargs)


def _parse_classifier(c: dict) -> ClassifierConfig:
    name = c["name"]
    kwargs = {k: v for k, v in c.items() if k not in ("name",)}
    return ClassifierConfig(name=name, kwargs=kwargs)
