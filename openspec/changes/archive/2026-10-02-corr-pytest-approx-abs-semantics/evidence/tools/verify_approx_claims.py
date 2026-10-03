"""Behavioural check of the two claims beta's correction rests on.

Both are written into the truth source and into a test comment, so both must
be re-measured rather than copied from a prior report.

1. `pytest.approx(1.173547, abs=4.3e-7)` passes -- the claim that `1e-6` is NOT
   the minimum tolerance the 6dp display format permits.
2. `pytest.approx(1.173547, abs=1e-6)` FAILS against the pre-fix integrator
   output `1.1735482746999482` -- the discriminating red/green pair the guard
   is justified by. If this no longer discriminates, the guard's rationale
   collapses and the comment above it would be asserting a false purpose.
"""
import sys
from pathlib import Path

import pytest

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(r"D:\myProject\DecompMoE") / "src"))

from decompmoe import sphere  # noqa: E402

CANONICAL_6DP = 1.173547
PRE_FIX_OUTPUT = 1.1735482746999482

theta = float(sphere.canonical_voronoi_angle(num_experts=16, signature_dim=16))
print(f"theta(16,16) = {theta!r}")
print(f"truncation diff vs {CANONICAL_6DP} = {abs(theta - CANONICAL_6DP):.6e}")

checks = [
    ("abs=1e-6  vs canonical value", CANONICAL_6DP, theta, 1e-6, True),
    ("abs=4.3e-7 vs canonical value", CANONICAL_6DP, theta, 4.3e-7, True),
    ("abs=1e-6  vs pre-fix output", CANONICAL_6DP, PRE_FIX_OUTPUT, 1e-6, False),
    ("abs=4.3e-7 vs pre-fix output", CANONICAL_6DP, PRE_FIX_OUTPUT, 4.3e-7, False),
]

bad = 0
print()
for name, expected, actual, tol, should_pass in checks:
    passed = bool(actual == pytest.approx(expected, abs=tol))
    ok = (passed == should_pass)
    bad += 0 if ok else 1
    print(f"  {'OK  ' if ok else 'WRONG'} {name:<34} -> "
          f"{'pass' if passed else 'fail'} (expected {'pass' if should_pass else 'fail'})")

# the tolerance property itself, so the comment's pytest-version claim is measured
ap = pytest.approx(1.0, abs=1e-9)
print()
print(f"  pytest.approx(1.0, abs=1e-9).tolerance = {ap.tolerance!r}  "
      f"(comment claims: exactly 1e-9)")
if ap.tolerance != 1e-9:
    bad += 1

print()
print("ALL CLAIMS HOLD" if bad == 0 else f"ABORT: {bad} claim(s) contradicted")
sys.exit(1 if bad else 0)
