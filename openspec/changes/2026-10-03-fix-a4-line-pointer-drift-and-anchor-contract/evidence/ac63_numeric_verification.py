#!/usr/bin/env python3
"""Phase 0.3 — AC-63 numeric verification.

The A-4 finding AC-63 says skeleton req-15's handoff sentence points at a guard
that does not exist: req-15 claims the `arctan(pi / sqrt(d_c))` invariant was
"restated under Requirement 'Centroid Driver Semantic Invariants' (req-16) and
enforced by the corresponding named test scenario", but req-16 contains no such
invariant and `arctan` / `38.146` have zero hits in tests/ and src/.

Plan section 0.3 forbids importing the magnitude quoted in
`.audit/wayfinder-opsx-code-review/context/05-mutation-evidence.md`
(`5.08e5 / 3.55e5 / 1.53e5`). That figure is NOT reproducible from the actual
quantities and is therefore NOT used here. Everything below is computed from
first principles, per the "agent report != measurement" discipline.

What is actually defensible: the forbidden token `arctan(pi / sqrt(d_c))` is an
ALTERNATIVE CLOSED FORM for the Voronoi half-angle. If an implementation
substituted it for the correct root of `0.5 * I_{sin^2 T}((d_c-1)/2, 1/2) = 1/N_e`,
the existing 6dp literal guard (normative `abs=1e-6`, per governance req-gov-1
obligation 3) would fail by a margin of ~5e5 tolerances. That margin is the
discriminating quantity the new guard should pin.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))

from decompmoe import sphere  # noqa: E402

# 6dp spec literals currently pinned by tests/test_sphere.py (governance
# req-gov-1 obligation 3); normative tolerance abs=1e-6.
SIX_DP_LITERALS = {16: 1.173547, 17: 1.165847, 64: 1.020506}
NORMATIVE_ABS = 1e-6

D_C = 16


def main() -> None:
    print("=" * 72)
    print("AC-63 numeric verification (all values computed, none imported)")
    print("=" * 72)
    print()
    print("d_c =", D_C)
    print()
    print("1) The FORBIDDEN shortcut closed form")
    shortcut = math.atan(math.pi / math.sqrt(D_C))
    print("   arctan(pi / sqrt(d_c))      = %.12f rad" % shortcut)
    print("                               = %.6f deg" % math.degrees(shortcut))
    print("   (this is the '38.146' figure the audit list cites)")
    print()

    print("2) The CORRECT closed form (root of the defining equation)")
    for n_e in sorted(SIX_DP_LITERALS):
        theta = sphere.canonical_voronoi_angle(n_e, D_C)
        print(
            "   canonical_voronoi_angle(N_e=%-2d, d_c=%d) = %.12f rad"
            % (n_e, D_C, theta)
        )
    print()

    print("3) Substitution test: what if the shortcut were used instead?")
    print("   %-6s %-14s %-12s %-14s %-10s %s" % ("N_e", "literal(6dp)", "shortcut", "abs err", "in 1e-6?", "x tolerance"))
    for n_e, lit in sorted(SIX_DP_LITERALS.items()):
        err = abs(shortcut - lit)
        print(
            "   %-6d %-14.6f %-12.6f %-14.3e %-10s %.1fx"
            % (n_e, lit, shortcut, err, "NO" if err > NORMATIVE_ABS else "yes", err / NORMATIVE_ABS)
        )
    print()
    print("   => Substituting the forbidden token moves the value OUTSIDE the")
    print("      6dp literal guard by ~5e5 normative tolerances. The existing")
    print("      literal pins DO discriminate; what is missing is that no")
    print("      guard names the forbidden form itself.")
    print()

    print("4) Residual-frame check on the CORRECT values (per req-gov-1 obl. 4)")
    # Signature is _betainc_regularized(x, a, b) -- x FIRST. An earlier draft of
    # this script called it as (a, b, x) and produced a plausible-looking
    # residual of ~0.44, i.e. a confidently wrong number.
    for n_e in sorted(SIX_DP_LITERALS):
        theta = sphere.canonical_voronoi_angle(n_e, D_C)
        x = math.sin(theta) ** 2
        a = (D_C - 1) / 2
        b = 0.5
        resid = abs(0.5 * sphere._betainc_regularized(x, a, b) - 1.0 / n_e)
        print(
            "   N_e=%-2d  |0.5*I_{sin^2T}(%.1f,0.5) - 1/N_e| = %.6e  %s"
            % (n_e, a, resid, "OK (<1e-9)" if resid < 1e-9 else "*** FAIL ***")
        )
    print()

    print("5) Provenance of the audit list's '3.58'")
    print("   RESOLVED: 3.58 is NOT part of the arctan invariant. It is the")
    print("   quadrature error 3.58e-16 reported in sphere._betainc_regularized's")
    print("   own docstring at theta = 82.6036 deg. The audit list swept it into the")
    print("   arctan zero-hit check, so its absence proved nothing about arctan.")
    print("   It is NOT used in any assertion.")
    print()
    print("CONCLUSION: the invariant is real and worth a named guard (it is a")
    print("banned TOKEN that was moved out of grep scope, so nothing currently")
    const = True
    print("names it). The correct remedy is an explicit req-16 Scenario + test,")
    print("not relying on the value pins alone (CLAUDE.md 6: prose assertions")
    print("are not verifiable clauses).")


if __name__ == "__main__":
    main()
