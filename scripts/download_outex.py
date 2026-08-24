#!/usr/bin/env python3
"""Expansion #6 — Outex texture dataset downloader (Outex_TC_00000).

Downloads the classic Outex texture classification suite Outex_TC_00000
(24 texture classes x 20 images, 128x128 grayscale, 30-degree rotated,
"test suite 0": 24 classes, 20 samples each; see Ojala et al. 2002) and
prepares (480, 64, 64) float32 arrays subsampled to 64x64, plus labels.

Primary source (documented):
  * Outex project home: https://www.outex.oulu.fi/
  * Outex_TC_00000 description + download page:
    https://www.outex.oulu.fi/index.php?page=download
  * Classic direct mirrors used by many reproduction repos (best-effort,
    may change): the Oulu temp/mirror paths and the Oulun yliopisto
    archive. The script tries a small list of candidate direct URLs and
    falls back to the synthetic texture proxy on ANY failure.

If the download is unreachable (offline / moved / blocked), the script
GRACEFULLY falls back to a numpy synthetic texture proxy: 24 classes of
band-pass filtered Gaussian noise with class-specific dominant frequency
and orientation (a Brodatz-like surrogate), same shape (480, 64, 64),
same label layout. A provenance JSON records which source was used:
  data/tda/images/outex_provenance.json  -> {"source": "outex_download"|"synthetic_proxy", "urls": [...]}

Output arrays (either way):
  data/tda/images/outex_64x64_X.npy   (480, 64, 64) float32 in [0, 1]
  data/tda/images/outex_64x64_y.npy   (480,) int64 in {0..23}

The sweep driver scripts/sweep_topology_wins.py consumes exactly these
filenames, so the real/proxy provenance only lives in the JSON + this
header. Modality is image; note the repo's documented VR-on-image
semantics (rows-as-points) apply to the sweep.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/download_outex.py
  # optional: force re-download / re-generate:
  .venv-tda/bin/python projects/tda-benchmark/scripts/download_outex.py --force

Expected runtime: seconds to minutes depending on network (proxy: seconds).
Additive-only: creates NEW files under data/tda/images/ only; never
touches existing data or code.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
OUT_DIR = PROJECT_ROOT / "data" / "tda" / "images"

OUT_X = OUT_DIR / "outex_64x64_X.npy"
OUT_Y = OUT_DIR / "outex_64x64_y.npy"
OUT_PROV = OUT_DIR / "outex_provenance.json"

# Documented primary source + best-effort direct URLs (tried in order).
OUTEX_HOME = "https://www.outex.oulu.fi/"
CANDIDATE_URLS = [
    "https://www.outex.oulu.fi/temp/outex/Outex_TC_00000.zip",
    "https://www.outex.oulu.fi/outex/Outex_TC_00000.zip",
    "http://www.outex.oulu.fi/temp/outex/Outex_TC_00000.zip",
]

SEED = 42
N_CLASSES = 24
N_PER_CLASS = 20
SIZE = 64  # subsampled resolution


# ── real download path ──────────────────────────────────────────────────────

def _try_download() -> bytes | None:
    """Return zip bytes from the first reachable candidate URL, else None."""
    for url in CANDIDATE_URLS:
        try:
            print(f"  trying {url}")
            with urllib.request.urlopen(url, timeout=30) as resp:
                data = resp.read()
            if len(data) > 1000:
                print(f"  downloaded {len(data)} bytes")
                return data
        except Exception as exc:  # noqa: BLE001 — any failure -> try next
            print(f"  failed ({type(exc).__name__}: {exc})")
    return None


def _read_ras(data: bytes, size: int) -> np.ndarray:
    """Read a Sun Raster (.ras) 8-bit grayscale image into (size, size)."""
    # header: magic(4) width(4) height(4) depth(4) length(4) type(4) ...
    magic = int.from_bytes(data[0:4], "big")
    if magic != 0x59A66A95:
        raise ValueError(f"not a Sun raster file (magic {magic:#x})")
    width = int.from_bytes(data[4:8], "big")
    height = int.from_bytes(data[8:12], "big")
    depth = int.from_bytes(data[12:16], "big")
    rastype = int.from_bytes(data[24:28], "big")
    if depth != 8:
        raise ValueError(f"unsupported depth {depth} (expected 8-bit gray)")
    body = data[32:]
    if rastype == 1:  # RLE — decompress (standard Sun raster RLE)
        body = _unrle(body, width * height)
    arr = np.frombuffer(body, dtype=np.uint8)[: width * height]
    arr = arr.reshape(height, width).astype(np.float32) / 255.0
    # center-crop/pad to the requested square size
    h, w = arr.shape
    top, left = max(0, (h - size) // 2), max(0, (w - size) // 2)
    out = arr[top: top + size, left: left + size]
    if out.shape != (size, size):
        pad = np.zeros((size, size), dtype=np.float32)
        pad[: out.shape[0], : out.shape[1]] = out
        out = pad
    return out


def _unrle(data: bytes, n_pixels: int) -> bytes:
    out = bytearray()
    i = 0
    while len(out) < n_pixels and i < len(data):
        b = data[i]
        i += 1
        if b == 0x80:  # RLE escape
            if i >= len(data):
                break
            cnt = data[i]
            i += 1
            if cnt == 0:
                out.append(0x80)
            else:
                if i >= len(data):
                    break
                val = data[i]
                i += 1
                out.extend(bytes([val]) * cnt)
        else:
            out.append(b)
    return bytes(out)


def _parse_zip(zdata: bytes) -> tuple[np.ndarray, np.ndarray] | None:
    """Extract 24x20 .ras images from the Outex_TC_00000 zip."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(zdata))
    except zipfile.BadZipFile as exc:
        print(f"  not a zip: {exc}")
        return None
    ras_files = sorted(n for n in zf.namelist() if n.lower().endswith(".ras"))
    # Outex_TC_00000 layout: <class>/<index>.ras, 24 classes x 20 images
    by_class: dict[str, list[str]] = {}
    for name in ras_files:
        cls = Path(name).parent.name or name.split("/")[0]
        by_class.setdefault(cls, []).append(name)
    classes = sorted(by_class)[:N_CLASSES]
    if len(classes) < N_CLASSES:
        print(f"  expected {N_CLASSES} classes, found {len(classes)} in zip")
        return None
    X, y = [], []
    for c_idx, cls in enumerate(classes):
        files = sorted(by_class[cls])[:N_PER_CLASS]
        for name in files:
            img = _read_ras(zf.read(name), SIZE)
            X.append(img)
            y.append(c_idx)
    if len(X) < N_CLASSES * N_PER_CLASS:
        print(f"  only {len(X)} images parsed (need {N_CLASSES * N_PER_CLASS})")
        return None
    X = np.stack(X).astype(np.float32)
    y = np.asarray(y, dtype=np.int64)
    perm = np.random.default_rng(SEED).permutation(len(y))
    return X[perm], y[perm]


# ── synthetic texture proxy fallback ────────────────────────────────────────

def gen_texture_proxy() -> tuple[np.ndarray, np.ndarray]:
    """24 classes of band-pass filtered noise (Brodatz-like surrogate).

    Each class = isotropic band-pass filtered white noise with a
    class-specific dominant frequency; a subset of classes adds a
    dominant orientation. Deterministic (seed 42). Same shape/layout as
    the real Outex arrays.
    """
    rng = np.random.default_rng(SEED)
    X, y = [], []
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    cx = (xx - SIZE / 2) / SIZE
    cy = (yy - SIZE / 2) / SIZE
    radius = np.sqrt(cx * cx + cy * cy)
    for c in range(N_CLASSES):
        f0 = 0.08 + 0.05 * (c % 8)          # dominant frequency per class
        theta = (c % 6) * np.pi / 6.0       # orientation for a subset
        band = np.exp(-((radius - f0) ** 2) / (2 * 0.035 ** 2))
        orient = np.exp(-((cy * np.cos(theta) - cx * np.sin(theta)) ** 2) / (2 * 0.25 ** 2))
        filt = band * (0.55 + 0.45 * orient)
        for _ in range(N_PER_CLASS):
            noise = rng.normal(0, 1, (SIZE, SIZE))
            spec = np.fft.fftshift(np.fft.fft2(noise))
            img = np.real(np.fft.ifft2(np.fft.ifftshift(spec * filt)))
            img = (img - img.min()) / (img.max() - img.min() + 1e-12)
            X.append(img.astype(np.float32))
            y.append(c)
    X = np.stack(X)
    y = np.asarray(y, dtype=np.int64)
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


# ── entry point ─────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Expansion #6 — Outex texture dataset downloader")
    ap.add_argument("--force", action="store_true",
                    help="re-download / re-generate even if files exist")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if (OUT_X.exists() and OUT_Y.exists()) and not args.force:
        print(f"[skip] {OUT_X.name} / {OUT_Y.name} already exist "
              f"(use --force to redo)")
        return

    source = "synthetic_proxy"
    X, y = gen_texture_proxy()
    print("downloading real Outex_TC_00000...")
    zdata = _try_download()
    if zdata is not None:
        parsed = _parse_zip(zdata)
        if parsed is not None:
            X, y = parsed
            source = "outex_download"
            print(f"  parsed {len(X)} real Outex images")
        else:
            print("  zip parse failed — using synthetic texture proxy")
    else:
        print("  download unreachable — using synthetic texture proxy "
              "(24 classes, band-pass filtered noise; documented in "
              "outex_provenance.json)")

    np.save(OUT_X, X)
    np.save(OUT_Y, y)
    prov = {
        "source": source,
        "primary_url": OUTEX_HOME,
        "candidate_urls": CANDIDATE_URLS,
        "classes": N_CLASSES,
        "per_class": N_PER_CLASS,
        "shape": list(X.shape),
        "note": "synthetic_proxy = 24 classes of band-pass filtered Gaussian "
                "noise (Brodatz-like surrogate), seeded 42; "
                "topology-wins sweep consumes outex_64x64_{X,y}.npy either way",
    }
    OUT_PROV.write_text(json.dumps(prov, indent=2))
    print(f"[write] {OUT_X.name} {X.shape} + {OUT_Y.name} {y.shape} "
          f"(source: {source})")
    print(f"[write] {OUT_PROV.name}")
    # ── SHA256 checksum verification (reproducibility; additive-only) ──────
    import _checksum_verify
    _checksum_verify.verify("images/outex_64x64_X.npy", OUT_DIR.parent)
    _checksum_verify.verify("images/outex_64x64_y.npy", OUT_DIR.parent)
    print("Next: run scripts/sweep_topology_wins.py (after sweep_large_n.py "
          "has finished — single CPU).")


if __name__ == "__main__":
    main()
