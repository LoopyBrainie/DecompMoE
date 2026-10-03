"""Task 7.1 verification: the new guard must FAIL if the shortcut is adopted.

Rather than editing src/decompmoe/sphere.py, this monkeypatches
`canonical_voronoi_angle` in memory and calls the test function directly. A
guard that only passes on the correct implementation proves nothing; it has to
be shown to reject the defect it names.
"""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from decompmoe import sphere  # noqa: E402
import test_sphere  # noqa: E402

SHORTCUT = lambda: math.atan(math.pi / math.sqrt(16))  # noqa: E731

print("=== baseline: current implementation ===")
test_sphere.test_canonical_voronoi_angle_not_arctan_shortcut()
print("  PASS on the real implementation (expected)")

print("\n=== defect injected: implementation returns the shortcut ===")
original = sphere.canonical_voronoi_angle
try:
    sphere.canonical_voronoi_angle = lambda num_experts, signature_dim: SHORTCUT()
    try:
        test_sphere.test_canonical_voronoi_angle_not_arctan_shortcut()
    except AssertionError as exc:
        head = str(exc).splitlines()[0]
        print(f"  FAIL as required. First assertion that fired:\n    {head}")
        rc = 0
    else:
        print("  ERROR: the guard passed on the shortcut implementation — it is vacuous")
        rc = 1
finally:
    sphere.canonical_voronoi_angle = original

print("\n=== defect injected: exact value, but body touches a banned token ===")
src = sphere.canonical_voronoi_angle
try:
    def _exact_but_bypassing(num_experts: int, signature_dim: int) -> float:
        # The value IS the exact root (same bisection as the real one), so
        # axes 1 and 2 both pass. Only the source check can catch this: the
        # body reaches for an inverse-trig call before bisecting.
        lo, hi = 0.0, math.pi / 2
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            half = 0.5 * sphere._betainc_regularized(
                math.sin(mid) ** 2, (signature_dim - 1) / 2.0, 0.5
            )
            if half < 1.0 / num_experts:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi) + math.atan(0.0)  # atan(0.0) == 0.0

    _exact_but_bypassing.__name__ = src.__name__
    _exact_but_bypassing.__doc__ = src.__doc__
    sphere.canonical_voronoi_angle = _exact_but_bypassing
    try:
        test_sphere.test_canonical_voronoi_angle_not_arctan_shortcut()
    except AssertionError as exc:
        print(f"  FAIL as required (source check, not a value check):\n    {str(exc).splitlines()[0]}")
    else:
        print("  ERROR: a bisection-bypassing body with the exact value passed")
        rc = 1
finally:
    sphere.canonical_voronoi_angle = original

test_sphere.test_canonical_voronoi_angle_not_arctan_shortcut()
print("\n  restored implementation still passes")
sys.exit(rc)
