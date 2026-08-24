#!/usr/bin/env python3
"""Expansion #6 — ModelNet10 downloader / shape point-cloud preparer.

Downloads the Princeton ModelNet10 3D shape dataset (10 classes: bathtub,
bed, chair, desk, dresser, monitor, night_stand, sofa, table, toilet),
samples 500 points per mesh, caps at 40 samples/class, and prepares
(n, 500, 3) float32 point-cloud arrays + labels.

Primary source (documented):
  * ModelNet project home: https://modelnet.cs.princeton.edu/
  * Classic direct zip used by the 3DShapeNets/PointNet reproduction
    community (best-effort, may move):
      https://3dvision.princeton.edu/projects/2014/3DShapeNets/ModelNet10.zip
      https://shapenet.cs.stanford.edu/media/ModelNet10.zip
  The script tries these in order; on ANY failure it falls back to the
  synthetic-shape proxy below and records the provenance.

Fallback (if unreachable): a small 'synthetic shape' proxy — point clouds
from parametrized primitives: sphere, cube, cylinder, cone, torus —
40 samples/class, 500 points each, seeded 42. Same array format
(n, 500, 3). NOTE the class count differs (5 primitives vs ModelNet10's
10 classes); scripts/sweep_topology_wins.py names the dataset by what it
finds (modelnet10 vs shapes_proxy) and the difference is recorded in
modelnet_provenance.json.

Output arrays (either way):
  data/tda/shapes/modelnet10_X.npy / modelnet10_y.npy   (real, 400 x 500 x 3, 10 classes)
  data/tda/shapes/shapes_proxy_X.npy / shapes_proxy_y.npy (proxy, 200 x 500 x 3, 5 classes)
  data/tda/shapes/modelnet_provenance.json

Point sampling is uniform-random per mesh at a fixed seed (disclosed —
not FPS; the sweep caps to subsample_points=100 anyway, matching the
repo's VR budget). Meshes are zero-centered and scaled to unit max
radius before sampling so classes differ in shape, not scale.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/download_modelnet.py
  .venv-tda/bin/python projects/tda-benchmark/scripts/download_modelnet.py --force

Expected runtime: minutes (network) or seconds (proxy).
Additive-only: creates NEW files under data/tda/shapes/ only.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
OUT_DIR = PROJECT_ROOT / "data" / "tda" / "shapes"

OUT_REAL_X = OUT_DIR / "modelnet10_X.npy"
OUT_REAL_Y = OUT_DIR / "modelnet10_y.npy"
OUT_PROXY_X = OUT_DIR / "shapes_proxy_X.npy"
OUT_PROXY_Y = OUT_DIR / "shapes_proxy_y.npy"
OUT_PROV = OUT_DIR / "modelnet_provenance.json"

MODELNET_HOME = "https://modelnet.cs.princeton.edu/"
CANDIDATE_URLS = [
    "https://3dvision.princeton.edu/projects/2014/3DShapeNets/ModelNet10.zip",
    "https://shapenet.cs.stanford.edu/media/ModelNet10.zip",
]

SEED = 42
N_PER_CLASS = 40
N_POINTS = 500
MODELNET10_CLASSES = [
    "bathtub", "bed", "chair", "desk", "dresser", "monitor",
    "night_stand", "sofa", "table", "toilet",
]
PRIMITIVES = ["sphere", "cube", "cylinder", "cone", "torus"]


# ── real download path ──────────────────────────────────────────────────────

def _try_download() -> bytes | None:
    for url in CANDIDATE_URLS:
        try:
            print(f"  trying {url}")
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = resp.read()
            if len(data) > 100_000:
                print(f"  downloaded {len(data)} bytes")
                return data
        except Exception as exc:  # noqa: BLE001
            print(f"  failed ({type(exc).__name__}: {exc})")
    return None


def _parse_off(text: str) -> np.ndarray:
    """Parse a ModelNet OFF mesh -> (n_vertices, 3) vertex array."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines[0].upper() == "OFF":
        lines = lines[1:]
    n_vert = int(lines[0].split()[0])
    verts = np.array(
        [[float(v) for v in ln.split()[:3]] for ln in lines[1:1 + n_vert]],
        dtype=np.float64,
    )
    return verts


def _sample_cloud(verts: np.ndarray, n: int, rng) -> np.ndarray:
    """Zero-center, unit-scale, and uniformly sample n points from a mesh."""
    verts = verts - verts.mean(axis=0)
    scale = np.max(np.linalg.norm(verts, axis=1)) + 1e-12
    verts = verts / scale
    if len(verts) >= n:
        idx = rng.choice(len(verts), n, replace=False)
        return verts[idx]
    # mesh with fewer vertices than requested: sample with replacement
    idx = rng.choice(len(verts), n, replace=True)
    return verts[idx]


def _parse_modelnet10(zdata: bytes) -> tuple[np.ndarray, np.ndarray] | None:
    """Extract ModelNet10 train split -> (400, 500, 3) clouds + labels."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(zdata))
    except zipfile.BadZipFile as exc:
        print(f"  not a zip: {exc}")
        return None
    rng = np.random.default_rng(SEED)
    names = [n for n in zf.namelist() if n.lower().endswith(".off")]
    by_class: dict[str, list[str]] = {}
    for name in names:
        parts = Path(name).parts
        # ModelNet10 zip layout: ModelNet10/<class>/train/<class>_<id>.off
        for i, p in enumerate(parts):
            if p in MODELNET10_CLASSES and i + 1 < len(parts) and parts[i + 1] == "train":
                by_class.setdefault(p, []).append(name)
                break
    missing = [c for c in MODELNET10_CLASSES if c not in by_class]
    if missing:
        print(f"  missing classes in zip: {missing}")
        return None
    X, y = [], []
    for c_idx, cls in enumerate(MODELNET10_CLASSES):
        files = sorted(by_class[cls])[:N_PER_CLASS]
        for name in files:
            verts = _parse_off(zf.read(name).decode("latin-1"))
            X.append(_sample_cloud(verts, N_POINTS, rng))
            y.append(c_idx)
    if len(X) < len(MODELNET10_CLASSES) * N_PER_CLASS:
        print(f"  only {len(X)} clouds parsed")
        return None
    X = np.stack(X).astype(np.float32)
    y = np.asarray(y, dtype=np.int64)
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


# ── synthetic shape proxy fallback ──────────────────────────────────────────

def _sphere(n, rng):
    u = rng.uniform(0, 1, n)
    v = rng.uniform(0, 2 * np.pi, n)
    z = 1 - 2 * u
    r = np.sqrt(np.maximum(0, 1 - z * z))
    return np.column_stack([r * np.cos(v), r * np.sin(v), z])


def _cube(n, rng):
    pts = rng.uniform(-1, 1, (n, 3))
    # project onto the cube surface: push the largest-magnitude coord to +/-1
    ax = np.argmax(np.abs(pts), axis=1)
    for i, a in enumerate(ax):
        pts[i, a] = np.sign(pts[i, a])
    return pts


def _cylinder(n, rng):
    t = rng.uniform(0, 2 * np.pi, n)
    z = rng.uniform(-1, 1, n)
    return np.column_stack([np.cos(t), np.sin(t), z])


def _cone(n, rng):
    t = rng.uniform(0, 2 * np.pi, n)
    z = rng.uniform(-1, 1, n)
    r = (1 - z) / 2  # apex at z=1, base radius 1 at z=-1
    return np.column_stack([r * np.cos(t), r * np.sin(t), z])


def _torus(n, rng, R=1.2, r=0.5):
    t = rng.uniform(0, 2 * np.pi, n)
    s = rng.uniform(0, 2 * np.pi, n)
    return np.column_stack([
        (R + r * np.cos(s)) * np.cos(t),
        (R + r * np.cos(s)) * np.sin(t),
        r * np.sin(s),
    ])


def gen_shapes_proxy() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    makers = [_sphere, _cube, _cylinder, _cone, _torus]
    X, y = [], []
    for c_idx, make in enumerate(makers):
        for _ in range(N_PER_CLASS):
            pts = make(N_POINTS, rng) + rng.normal(0, 0.02, (N_POINTS, 3))
            X.append(pts.astype(np.float32))
            y.append(c_idx)
    X = np.stack(X)
    y = np.asarray(y, dtype=np.int64)
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


# ── entry point ─────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Expansion #6 — ModelNet10 downloader / shape preparer")
    ap.add_argument("--force", action="store_true",
                    help="re-download / re-generate even if files exist")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    real_done = OUT_REAL_X.exists() and OUT_REAL_Y.exists()
    if real_done and not args.force:
        print(f"[skip] {OUT_REAL_X.name} already exists (use --force to redo)")
        return

    source = "synthetic_proxy"
    print("downloading ModelNet10...")
    zdata = _try_download()
    if zdata is not None:
        parsed = _parse_modelnet10(zdata)
        if parsed is not None:
            X, y = parsed
            np.save(OUT_REAL_X, X)
            np.save(OUT_REAL_Y, y)
            source = "modelnet10_download"
            print(f"[write] {OUT_REAL_X.name} {X.shape} (10 classes)")
        else:
            print("  zip parse failed — using synthetic shape proxy")
    else:
        print("  download unreachable — using synthetic shape proxy "
              "(5 primitives x 40 samples x 500 pts; documented in "
              "modelnet_provenance.json)")

    if source == "synthetic_proxy":
        Xp, yp = gen_shapes_proxy()
        np.save(OUT_PROXY_X, Xp)
        np.save(OUT_PROXY_Y, yp)
        print(f"[write] {OUT_PROXY_X.name} {Xp.shape} "
              f"(classes {np.unique(yp).tolist()})")

    prov = {
        "source": source,
        "primary_url": MODELNET_HOME,
        "candidate_urls": CANDIDATE_URLS,
        "real": {"path": str(OUT_REAL_X), "classes": MODELNET10_CLASSES,
                 "per_class": N_PER_CLASS, "points": N_POINTS},
        "proxy": {"path": str(OUT_PROXY_X), "classes": PRIMITIVES,
                  "per_class": N_PER_CLASS, "points": N_POINTS},
        "note": "sweep_topology_wins.py uses modelnet10_* if present, "
                "else shapes_proxy_*; class count differs between the two.",
    }
    OUT_PROV.write_text(json.dumps(prov, indent=2))
    print(f"[write] {OUT_PROV.name}")
    # ── SHA256 checksum verification (reproducibility; additive-only) ──────
    # modelnet10_* is covered by checksums.sha256; the shapes_proxy_*
    # fallback is NOT (absent when the manifest was built) — warned, not raised.
    import _checksum_verify
    for rel in ("shapes/modelnet10_X.npy", "shapes/modelnet10_y.npy",
                "shapes/shapes_proxy_X.npy", "shapes/shapes_proxy_y.npy"):
        _checksum_verify.verify_if_covered(rel, OUT_DIR.parent)
    print("Next: run scripts/sweep_topology_wins.py (after sweep_large_n.py "
          "has finished — single CPU).")


if __name__ == "__main__":
    main()
