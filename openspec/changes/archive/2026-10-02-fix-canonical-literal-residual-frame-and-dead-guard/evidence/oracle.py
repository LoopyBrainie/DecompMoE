"""TWO-ROUTE ORACLE for the canonical Voronoi half-angles.

Frozen as evidence for change
2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard, task 0.3.

Why two routes: the first version of this oracle used mpmath's
`betainc(a, b, x, regularized=True)` as a second opinion and DISAGREED with
`mp.quad` by 8.19e-02, because that 3-argument form returns the COMPLEMENT
`1 - I_x` (measured 0.8691458 where I_x = 0.1308542). A "cross-check" built on
an unverified assumption is worse than no cross-check.

Route 1  mp.quad over t^(a-1)(1-t)^(b-1) / B(a,b)
Route 2  mpmath 4-argument betainc(a, b, 0, x, regularized=True)

The two agree to <= 1e-49, which is what makes the canonical values usable as
spec literals. Run this before trusting any number written into a spec.
"""
import mpmath as mp
import sys

mp.mp.dps = 60

TARGETS = [(16, 16), (17, 16), (32, 16), (64, 16), (3, 16)]

CANONICAL = {
    (16, 16): "1.1735474259197175",
    (17, 16): "1.1658476215516009",
    (32, 16): "1.0916065844205111",
    (64, 16): "1.0205068247837132",
}
SIX_DP = {(16, 16): "1.173547", (17, 16): "1.165847", (64, 16): "1.020506"}
SIX_DP_DIFF = {(16, 16): "4.259e-07", (17, 16): "6.216e-07", (64, 16): "8.248e-07"}
PRE_FIX_IMPL = {(16, 16): "1.1735482746999482", (17, 16): "1.1658482974306132",
                (64, 16): "1.0205068335735599"}


def sphere_area(d):
    return 2 * mp.pi ** (mp.mpf(d) / 2) / mp.gamma(mp.mpf(d) / 2)


def G_quad(theta, d_c):
    a, b = mp.mpf(d_c - 1) / 2, mp.mpf(1) / 2
    num = mp.quad(lambda t: t ** (a - 1) * (1 - t) ** (b - 1), [0, mp.sin(theta) ** 2])
    return (num / mp.beta(a, b)) / 2


def G_betainc(theta, d_c):
    a, b = mp.mpf(d_c - 1) / 2, mp.mpf(1) / 2
    return mp.betainc(a, b, 0, mp.sin(theta) ** 2, regularized=True) / 2


def theta_voronoi(n_e, d_c, G):
    lo, hi = mp.mpf("1e-15"), mp.pi
    for _ in range(300):
        mid = (lo + hi) / 2
        if G(mid, d_c) < mp.mpf(1) / n_e:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    out = []
    w = out.append
    w("CANONICAL VORONOI HALF-ANGLES (two independent routes, dps=60)")
    w("=" * 78)
    ok = True
    for n_e, d_c in TARGETS:
        t1 = theta_voronoi(n_e, d_c, G_quad)
        t2 = theta_voronoi(n_e, d_c, G_betainc)
        spread = abs(t1 - t2)
        agree = spread < mp.mpf("1e-49")
        ok = ok and agree
        r = abs(G_quad(t1, d_c) - mp.mpf(1) / n_e)
        w("  N_e=%-3d d_c=%-3d  16dp=%-21s  routes-agree=%-5s  spread=%.2e  residual=%.2e"
          % (n_e, d_c, mp.nstr(t1, 17), agree, float(spread), float(r)))
        if (n_e, d_c) in CANONICAL:
            declared = mp.mpf(CANONICAL[(n_e, d_c)])
            match = abs(declared - t1) < mp.mpf("5e-17")
            ok = ok and match
            w("        declared in delta = %s   matches = %s" % (CANONICAL[(n_e, d_c)], match))
    w("")
    w("6dp TRUNCATED LITERALS -- the red/green witness (tolerance abs=1e-6)")
    w("=" * 78)
    w("  'vs pre-fix impl' and 'vs true' say whether a test asserting")
    w("  pytest.approx(impl, abs=1e-6) would PASS or FAIL there.")
    w("")
    for n_e in (16, 17, 64):
        t = theta_voronoi(n_e, 16, G_quad)
        trunc = mp.floor(t * mp.mpf(10) ** 6) / mp.mpf(10) ** 6
        impl = mp.mpf(PRE_FIX_IMPL[(n_e, 16)])
        d_impl, d_true = abs(trunc - impl), abs(trunc - t)
        passes_on_prefix = d_impl < mp.mpf("1e-6")
        passes_on_true = d_true < mp.mpf("1e-6")
        # A discriminator must FAIL on the pre-fix implementation and PASS on the truth.
        discriminates = (not passes_on_prefix) and passes_on_true
        w("  N_e=%-3d lit=%-10s |lit-pre-fix|=%-10.3e %-4s   |lit-true|=%-10.3e %-4s   discriminates=%s"
          % (n_e, SIX_DP[(n_e, 16)], float(d_impl),
             "PASS" if passes_on_prefix else "FAIL",
             float(d_true), "PASS" if passes_on_true else "FAIL",
             discriminates))
    w("")
    w("  N_e=16 and N_e=17 MUST discriminate (red before the fix, green after).")
    w("  N_e=64 is NOT expected to: its 6dp literal `1.020506` is unchanged by the fix")
    w("  and passes on both sides, so it is a regression guard, not a discriminator.")
    w("")

    # the two values that carry the witness must actually discriminate
    for n_e in (16, 17):
        t = theta_voronoi(n_e, 16, G_quad)
        trunc = mp.floor(t * mp.mpf(10) ** 6) / mp.mpf(10) ** 6
        impl = mp.mpf(PRE_FIX_IMPL[(n_e, 16)])
        good = (abs(trunc - impl) >= mp.mpf("1e-6")) and (abs(trunc - t) < mp.mpf("1e-6"))
        ok = ok and good
    w("")
    w("ORACLE VERDICT: %s" % ("PASS -- all routes agree and all declared values match"
                              if ok else "FAIL"))
    return out, ok


if __name__ == "__main__":
    lines, ok = main()
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(lines))
    sys.exit(0 if ok else 1)
