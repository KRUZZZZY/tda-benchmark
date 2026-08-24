#!/usr/bin/env python3
"""Shared SHA256 checksum verification for tda-benchmark data-generation scripts.

Every script that writes .npy artifacts under data/tda/ ends by verifying its
outputs against the committed manifest ``checksums.sha256`` at the repo root
(git-hash-object style: ``<sha256>  <relative-path>`` on each line, paths
relative to the data directory, e.g. ``data/tda``).

Importing this module has NO side effects: no I/O, no prints. Only the
``verify*`` functions read the manifest and hash files.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "checksums.sha256"

_CHUNK = 1 << 20  # 1 MiB


def _load_manifest(manifest: Path) -> dict[str, str]:
    """Parse ``<sha256>  <relative-path>`` lines into {path: digest}."""
    if not manifest.exists():
        raise FileNotFoundError(
            f"checksum manifest not found: {manifest} "
            f"(expected at the tda-benchmark repo root)")
    entries: dict[str, str] = {}
    for lineno, line in enumerate(manifest.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ValueError(
                f"malformed checksum manifest line {manifest}:{lineno}: {line!r}")
        digest, rel = parts[0].lower(), parts[1].strip()
        entries[rel] = digest
    return entries


def sha256_file(path: Path) -> str:
    """SHA256 hex digest of a file, streamed in 1 MiB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(relative_path: str, data_root) -> bool:
    """Strictly verify ``data_root/relative_path`` against the manifest.

    Raises FileNotFoundError when the artifact or its manifest entry is
    missing, and ValueError when the SHA256 does not match. Returns True on
    success.
    """
    data_root = Path(data_root)
    rel = relative_path.replace("\\", "/").lstrip("/")
    target = data_root / rel
    entries = _load_manifest(MANIFEST)
    if rel not in entries:
        raise FileNotFoundError(
            f"checksum: {rel!r} is not listed in {MANIFEST} — "
            f"this artifact is not covered by the committed manifest")
    if not target.exists():
        raise FileNotFoundError(
            f"checksum: {target} does not exist — cannot verify {rel!r}")
    actual = sha256_file(target)
    if actual != entries[rel]:
        raise ValueError(
            f"checksum MISMATCH for {rel} (file {target}):\n"
            f"  expected {entries[rel]}\n"
            f"  actual   {actual}\n"
            f"The regenerated artifact is NOT byte-identical to the "
            f"committed benchmark inputs.")
    print(f"  [checksum ok] {rel}")
    return True


def verify_if_covered(relative_path: str, data_root) -> bool:
    """Verify an artifact only when it exists AND the manifest covers it.

    Used for outputs a script may legitimately skip or replace (e.g. an
    optional download that fell back to a proxy, or a file whose source
    archive is absent): prints an informative note instead of raising.
    Returns True when verified, False when skipped.
    """
    data_root = Path(data_root)
    rel = relative_path.replace("\\", "/").lstrip("/")
    target = data_root / rel
    if not target.exists():
        print(f"  [checksum] {rel} absent — nothing to verify (skipped)")
        return False
    entries = _load_manifest(MANIFEST)
    if rel not in entries:
        print(f"  [checksum] {rel} exists but is NOT covered by "
              f"{MANIFEST.name} (not present when the manifest was built) "
              f"— skipped")
        return False
    return verify(rel, data_root)
