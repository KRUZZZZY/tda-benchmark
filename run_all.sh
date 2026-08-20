#!/bin/bash
# run_all.sh — end-to-end reproduction of the TDA Pipeline Benchmark.
#
# Reproduces the full 616-configuration sweep:
#   1. regenerate the synthetic sphere/torus data (seeded, exact shapes)
#   2. run the sweep (fresh results DB — idempotent)
#   3. produce the analysis report
#
# ECG200 and MNIST 0/1 are sourced from the UCR archive / standard MNIST;
# place ECG200.arff in data/tda/ucr/ and mnist_X.npy + mnist_y.npy in
# data/tda/images/ (see scripts/generate_datasets.py) — or provide the
# pre-parsed .npy files from the author.
#
# Usage: bash run_all.sh            (from the repo root)
# Env:   TDA_NJOBS (default 1)      parallel worker count
set -euo pipefail
cd "$(dirname "$0")"

# The runner resolves data paths relative to the parent project root
# (runner.py: project_root = Path(__file__).parent.parent.parent),
# i.e. AI_KOS_PROJECT/data/tda — matching the repo's AGENTS.md layout.
DATA_DIR="$(cd ../.. && pwd)/data/tda"
mkdir -p "$DATA_DIR/synthetic" "$DATA_DIR/ucr" "$DATA_DIR/images"

echo "[1/4] Creating environment (if missing)..."
if [ ! -d ../.venv-tda ]; then
  python3 -m venv ../.venv-tda
fi
# shellcheck disable=SC1091
source ../.venv-tda/bin/activate
pip install -q -r requirements.txt

echo "[2/4] Generating / checking datasets..."
python scripts/generate_datasets.py --data-dir "$DATA_DIR"
if [ ! -f "$DATA_DIR/ucr/ecg200_X.npy" ] || [ ! -f "$DATA_DIR/images/mnist_01_X.npy" ]; then
  echo "[!] ECG200 / MNIST 0/1 sources missing — see scripts/generate_datasets.py."
  echo "    Synthetic sphere/torus data are ready; the sweep will run those only."
fi

echo "[3/4] Running benchmark sweep (fresh DB, this takes ~2h)..."
# Idempotency: start from a clean results DB so a re-run cannot double rows.
rm -f "$DATA_DIR/expanded_results.db"
python - <<'PY'
import sys, importlib.util, os
# The repo dir is hyphenated (tda-benchmark), so register it as the
# importable package name tda_benchmark (matches relative imports in *.py).
pkg_dir = os.path.abspath(os.getcwd())
spec = importlib.util.spec_from_file_location(
    "tda_benchmark", os.path.join(pkg_dir, "__init__.py"),
    submodule_search_locations=[pkg_dir])
pkg = importlib.util.module_from_spec(spec)
sys.modules["tda_benchmark"] = pkg
spec.loader.exec_module(pkg)
from tda_benchmark.runner import run_benchmark
run_benchmark("expanded_config.yaml", n_jobs=${TDA_NJOBS:-1})
PY

echo "[4/4] Generating analysis report..."
python analysis.py "$DATA_DIR/expanded_results.db"

echo "Done. Results: $DATA_DIR/expanded_results.db (path set by the config's output.db_path)"
