"""tda-benchmark CLI entry point (expansion item #20).

A thin, dependency-light command surface for the installed framework.
Imports are lazy so ``tda-benchmark --version`` works even when the heavy
optional backends (gtda/gudhi) are missing.

Usage::

    tda-benchmark --version
    tda-benchmark list-components
    tda-benchmark run <config.yaml> [--n-jobs N]
"""

from __future__ import annotations

import argparse
import importlib.metadata
import sys

__all__ = ["main"]


def _version() -> str:
    try:
        return importlib.metadata.version("tda-benchmark")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover
        return "0.0.0-dev (not installed - run 'pip install -e .')"


def _list_components() -> None:
    from tda_benchmark.factories import (
        ClassifierFactory,
        FiltrationFactory,
        VectorizationFactory,
    )

    print("filtrations: ", ", ".join(FiltrationFactory.list_available()))
    print("vectorizers: ", ", ".join(VectorizationFactory.list_available()))
    print("classifiers: ", ", ".join(ClassifierFactory.list_available()))


def _run(config_path: str, n_jobs: int) -> int:
    from tda_benchmark.runner import run_benchmark

    run_benchmark(config_path, n_jobs=n_jobs)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tda-benchmark",
        description="Persistent-homology pipeline benchmark framework.",
    )
    parser.add_argument(
        "--version", action="store_true", help="print the installed version"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser(
        "list-components",
        help="print the factory-registered filtrations, vectorizers, classifiers",
    )

    run_p = sub.add_parser("run", help="run a benchmark YAML configuration")
    run_p.add_argument("config", help="path to the YAML configuration")
    run_p.add_argument(
        "--n-jobs", type=int, default=1,
        help="worker processes (default 1 = serial; the production rule)",
    )

    args = parser.parse_args(argv)

    if args.version:
        print(f"tda-benchmark {_version()}")
        return 0
    if args.command == "list-components":
        _list_components()
        return 0
    if args.command == "run":
        return _run(args.config, args.n_jobs)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
