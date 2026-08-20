#!/bin/bash
# run_all.sh — end-to-end reproduction of the TDA Pipeline Benchmark.
#
# NOTE on data: the paper's datasets (synthetic sphere/torus at four noise
# levels, ECG200, MNIST 0/1) are NOT bundled in the repo (gitignored under
# data/). They are regenerable:
#   - synthetic sphere/torus: run scripts in the `synthetic` generation code
#     (see AGENTS.md / the ai-kos repo's scripts/tda_download_datasets.py for
#     the canonical generator) — or request the .npy files from the author.
#   - ECG200: UCR archive (timeseriesclassification.com), parsed to npy.
#   - MNIST 0/1: torchvision/keras MNIST, binary subset 200/class.
# If data/tda/ is already populated (e.g. pulled from the author's local
# copy), this script runs the full sweep and analysis directly.
#
# Usage: bash run_all.sh            (from the repo root)
# Env:   TDA_NJOBS (default 1)      parallel worker count
set -euo pipefail
cd "$(dirname "$0")"

# The runner resolves data paths relative to the parent project root
# (runner.py: project_root = Path(__file__).parent.parent.parent),
# i.e. AI_KOS_PROJECT/data/tda — matching the repo's AGENTS.md layout.
DATA_DIR="$(cd ../.. && pwd)/data/tda"
if [ ! -d "$DATA_DIR/synthetic" ] || [ ! -f "$DATA_DIR/ucr/ecg200_X.npy" ] || [ ! -f "$DATA_DIR/images/mnist_01_X.npy" ]; then
  echo "[!] Datasets not found under $DATA_DIR."
  echo "    See the header comment in this script for how to obtain them."
  echo "    (Synthetic generator: ai-kos repo scripts/tda_download_datasets.py;"
  echo "     ECG200: UCR archive; MNIST 0/1: 200/class binary subset.)"
  exit 1
fi
echo "[ok] Datasets present: $DATA_DIR"

echo "[1/3] Creating environment (if missing)..."
if [ ! -d .venv-tda ]; then
  python3 -m venv .venv-tda
fi
source .venv-tda/bin/activate
pip install -q -r requirements.txt

echo "[2/3] Running benchmark sweep (this takes a while)..."
export PYTHONHASHSEED=0   # pin hash() for full reproducibility
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

echo "[3/3] Generating analysis report..."
python analysis.py data/tda/expanded_results.db

echo "Done. Results: data/tda/expanded_results.db (path set by the config's output.db_path)"
