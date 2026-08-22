# requirements-learned.md — env preparation for the learned-vectorizer arm (#8)

Purpose: document (NOT perform) the environment preparation needed to run the
two learned-vectorizer factory entries added in `factories.py` — `perslay`
(PersLay-style trainable layer, Karimi et al., ICML 2020) and
`hofer_deepset` (Hofer-style deep-set input layer, Hofer et al., ICLR 2017) —
and their sweep driver `scripts/sweep_learned_vectorizers.py`.

Status: **documentation only.** No installs are performed in this revision,
and no sweep using these entries has been run. The factory entries import
cleanly WITHOUT torch (lazy import inside `fit`/`transform`); they raise a
clear `ImportError` pointing at this file if used without torch.

---

## Why a separate venv (`venv isolation`)

The benchmark's stock venv is `.venv-tda` and pins `scikit-learn==1.3.2`
(requirements.txt, required by `giotto-tda==0.6.2` — giotto-tda 0.6.2
downgrades sklearn if it is newer). Installing torch and perslay into that
venv risks upgrading sklearn and silently breaking every existing pipeline.
**Use a dedicated `.venv-perslay`** next to `.venv-tda`:

```
/home/kruzzzzy/Documents/AI_KOS_PROJECT/.venv-perslay
```

The two venvs share the same result DBs under `data/tda/` (SQLite is
single-writer; never run sweeps from both venvs at the same time).

---

## Install steps (run once, ~10-20 min on CPU wheels)

```bash
cd /home/kruzzzzy/Documents/AI_KOS_PROJECT

# 1. create the isolated venv (Python 3.12+; the repo was built on 3.12)
python3 -m venv .venv-perslay
source .venv-perslay/bin/activate

# 2. torch — CPU wheels only (this box has no CUDA; the CPU index is ~200 MB)
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 3. perslay package (Karimi et al. reference implementation)
pip install perslay

# 4. the repo's own pinned stack, reinstalled INTO .venv-perslay
#    (scikit-learn==1.3.2 MUST stay pinned for giotto-tda 0.6.2)
pip install giotto-tda==0.6.2 ripser==0.6.15 gudhi==3.13.0 \
    scikit-learn==1.3.2 "numpy>=1.26,<2" scipy>=1.11 \
    matplotlib>=3.8 pyyaml>=6.0 statsmodels
```

Notes / caveats:

- `pip install perslay` resolves to the reference implementation, which is
  TensorFlow-based. The factory stub does NOT depend on its exact API: the
  stub implements the defining PersLay/deep-set architecture itself
  (per-point MLP + permutation-invariant additive pooling in torch) and only
  requires `perslay` to be *importable* for the `perslay` entry (checked via
  `importlib.util.find_spec`). If the pip package's API differs from the
  original repo, the stub still runs its own torch implementation.
- `gudhi`, `ripser`, `giotto-tda` are needed because the sweep driver routes
  every config through the repo's own `_run_one_worker` (bit-identical
  preprocessing: Takens embedding, factory pipelines, seed-43 folds).
- Do NOT `pip install` anything into `.venv-tda` for this arm. If you
  accidentally activate `.venv-tda` and install torch there, the sklearn pin
  check (`pip check`) is the first thing to run.

---

## Import smoke test (must pass before running the sweep)

```bash
cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
.venv-perslay/bin/python - <<'PY'
import torch
print("torch", torch.__version__)

# register the hyphenated package (same importlib shim the drivers use)
import sys, importlib.util, os
pkg_dir = os.path.abspath("projects/tda-benchmark")
spec = importlib.util.spec_from_file_location(
    "tda_benchmark", os.path.join(pkg_dir, "__init__.py"),
    submodule_search_locations=[pkg_dir])
pkg = importlib.util.module_from_spec(spec)
sys.modules["tda_benchmark"] = pkg
spec.loader.exec_module(pkg)

from tda_benchmark.factories import VectorizationFactory
assert "perslay" in VectorizationFactory.list_available()
assert "hofer_deepset" in VectorizationFactory.list_available()

# pipeline mechanics on a fake diagram batch (4 samples, 10 points,
# [birth, death, dim] triples) — must emit 2D (4, out_dim)
import numpy as np
X = np.random.rand(4, 10, 3)
X[:, :, 1] += 0.1                      # death > birth
for name in ("perslay", "hofer_deepset"):
    p = VectorizationFactory.create(name, hidden_dim=8, out_dim=4)
    out = p.fit_transform(X)
    assert out.shape == (4, 4), (name, out.shape)
    print(name, "->", out.shape, "OK")

# negative check: WITHOUT torch the same entry must fail with the clear error
import builtins, importlib
real_import = builtins.__import__
def fake(name, *a, **k):
    if name == "torch":
        raise ImportError("No module named 'torch'")
    return real_import(name, *a, **k)
builtins.__import__ = fake
try:
    VectorizationFactory.create("hofer_deepset").fit(X)
    raise SystemExit("expected ImportError, got none")
except ImportError as e:
    print("negative check OK:", str(e)[:80], "...")
finally:
    builtins.__import__ = real_import
PY
```

Expected output ends with `negative check OK: _HoferDeepSetLayer requires
torch (torch); see requirements-learned.md ...`.

---

## After the smoke test: run the sweep

```bash
cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
.venv-perslay/bin/python projects/tda-benchmark/scripts/sweep_learned_vectorizers.py
```

- Grid: ecg200 + sphere_torus_noise0 x {vietoris_rips, weak_alpha} x
  {perslay, hofer_deepset} x {random_forest, svm_rbf}, 5-fold seed 42 rep 1
  = 16 runs, serial (n_jobs=1, single-CPU rule).
- Expected runtime: **2-4 h** on CPU after torch is installed (the stubs do
  not train in this revision, so most of the time is the standard filtration
  + CV cost; a future trainable version will be slower).
- DB: `data/tda/learned_vectorizers_sweep.db` (created by the driver;
  resumable — restarting skips finished combos).
- Single-CPU / no-parallel rule applies exactly as for every other sweep in
  this repo.

---

## Additive-only record

Files created by this arm (nothing existing modified):
- `factories.py` — two ADDED entries (`perslay`, `hofer_deepset`) in
  `VectorizationFactory.create` mapping + `list_available`; two new classes
  appended; existing entries untouched. The factory's flatten wrapper is a
  no-op for these (they emit 2D already).
- `scripts/sweep_learned_vectorizers.py` — the driver (DO NOT RUN without
  torch).
- `requirements-learned.md` — this file.
- Result DB `data/tda/learned_vectorizers_sweep.db` appears only when the
  driver is run.
