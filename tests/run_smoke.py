#!/usr/bin/env python3
"""Canonical smoke-suite runner for the tda-benchmark repo (expansion #20).

Runs the same 6 tests pytest would, without pytest's test-module import
machinery. This is the CI gate because the framework package lives at the repo
root (__init__.py) and the root directory is hyphenated ("tda-benchmark"):
pytest (verified 8.4.x and 9.1.1, 2026-08-22, both import modes, with and
without tests/__init__.py and consider_namespace_packages=false) resolves the
test module into that package, tries to import the root __init__.py under the
invalid name, and dies with "attempted relative import with no known parent
package". The tests themselves are pytest-compatible (pytest.raises,
importorskip) and will run under pytest directly once the root package is
importable by a valid name (e.g. a future src/ layout).

Usage (from repo root):
    python tests/run_smoke.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_framework_smoke as t  # noqa: E402

_TESTS = (
    t.test_import_shim_public_api,
    t.test_driver_importlib_shim_loads_functional_package,
    t.test_config_dataclasses_construct_and_count,
    t.test_factories_list_expected_entries,
    t.test_unknown_factory_names_raise,
    t.test_tiny_vr_pi_svm_roundtrip,
)


def main() -> int:
    failures = 0
    for fn in _TESTS:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {fn.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"PASS {fn.__name__}")
    print(f"{len(_TESTS) - failures}/{len(_TESTS)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
