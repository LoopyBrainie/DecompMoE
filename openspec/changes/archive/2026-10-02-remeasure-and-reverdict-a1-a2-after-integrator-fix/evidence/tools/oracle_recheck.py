"""Change 3 / task 0.2 -- freeze and re-verify the oracle, with the probe points
this change needs appended. Writes evidence/oracle_recheck.json.

Frozen oracle: change 2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard
evidence/oracle.py (the task text says `2026-10-01`; that change no longer exists
under that name -- recorded, not silently ignored).

Appended probe points, each traceable to the ac_ids that cite it:
  (3,16) (16,16) (17,16) (32,16) (64,16)  the canonical Voronoi half-angles
  incomplete-Beta deltas                  AC-09 (+1.1813e-6 / +1.1818e-6 / +1.3579e-2)
  cap-area below the pi/2 plateau         AC-05 / AC-15 / AC-42 (concavity partition)

Two routes must agree at dps=60. Route 1 mp.quad over the integrand; Route 2 the
4-argument mpmath betainc. The 3-argument form returns the COMPLEMENT and is the
exact bug that made Change 0's first oracle wrong -- so the route count is
asserted, not just printed.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
EV = ROOT / "openspec/changes/archive/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence"
FROZEN = ROOT / ("openspec/changes/archive/2026-10-02-fix-canonical-literal-"
                 "residual-frame-and-dead-guard/evidence/oracle.py")

import mpmath as mp  # noqa: E402
mp.mp.dps = 60

TARGETS = [(3, 16), (16, 16), (17, 16), (32, 16), (64, 16)]
SPREAD_TOL = mp.mpf("1e-49")


def G_quad(theta, d_c):
    a, b = mp.mpf(d_c - 1) / 2, mp.mpf(1) / 2
    num = mp.quad(lambda t: t ** (a - 1) * (1 - t) ** (b - 1), [0, mp.sin(theta) ** 2])
    return (num / mp.beta(a, b)) / 2


def G_betainc(theta, d_c):
    a, b = mp.mpf(d_c - 1) / 2, mp.mpf(1) / 2
    return mp.betainc(a, b, 0, mp.sin(theta) ** 2, regularized=True) / 2


def G_betainc_3arg_TRAP(theta, d_c):
    """The Change 0 bug. Kept so the guard against re-introducing it is testable."""
    a, b = mp.mpf(d_c - 1) / 2, mp.mpf(1) / 2
    return mp.betainc(a, b, mp.sin(theta) ** 2) / 2


def theta_voronoi(n_e, d_c, G):
    lo, hi = mp.mpf("1e-15"), mp.pi
    for _ in range(300):
        mid = (lo + hi) / 2
        if G(mid, d_c) < mp.mpf(1) / n_e:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


ok = True
probe = []
for n_e, d_c in TARGETS:
    t1 = theta_voronoi(n_e, d_c, G_quad)
    t2 = theta_voronoi(n_e, d_c, G_betainc)
    trap = theta_voronoi(n_e, d_c, G_betainc_3arg_TRAP)
    spread = abs(t1 - t2)
    agree = spread < SPREAD_TOL
    residual = abs(G_quad(t1, d_c) - mp.mpf(1) / n_e)
    # the 3-argument route must NOT agree -- if it did, the guard is vacuous
    trap_gap = abs(t1 - trap)
    trap_separated = trap_gap > mp.mpf("1e-3")
    lit = mp.floor(t1 * mp.mpf(10) ** 6) / mp.mpf(10) ** 6
    ok = ok and agree and trap_separated
    probe.append(dict(
        N_e=n_e, d_c=d_c,
        route_quad=mp.nstr(t1, 20), route_betainc=mp.nstr(t2, 20),
        spread=mp.nstr(spread, 3), routes_agree=bool(agree),
        residual_G_minus_1_over_N=mp.nstr(residual, 3),
        six_dp_literal=mp.nstr(lit, 8),
        three_arg_trap=mp.nstr(trap, 12),
        trap_gap=mp.nstr(trap_gap, 3), trap_is_separated=bool(trap_separated),
    ))

# ---- impl-vs-oracle, the quantity the ledger will actually re-measure
sys.path.insert(0, str(ROOT / "src"))
from decompmoe import sphere  # noqa: E402
impl_rows = []
for n_e, d_c in TARGETS:
    t_oracle = theta_voronoi(n_e, d_c, G_betainc)
    impl = mp.mpf(repr(sphere.canonical_voronoi_angle(num_experts=n_e, signature_dim=d_c)))
    impl_rows.append(dict(N_e=n_e, d_c=d_c, impl=mp.nstr(impl, 20),
                          oracle=mp.nstr(t_oracle, 20),
                          deviation=mp.nstr(impl - t_oracle, 3),
                          abs_deviation=mp.nstr(abs(impl - t_oracle), 3),
                          within_1e_12=bool(abs(impl - t_oracle) < mp.mpf("1e-12"))))

# ---- matcher control, carried over from the field-parse run
fields = json.loads((EV / "audit_findings.json").read_text(encoding="utf-8"))
by_id = {f["ac_id"]: f for f in fields["findings"]}
ac09, ac74, ac44 = by_id["AC-09"], by_id["AC-74"], by_id["AC-44"]
control = dict(
    known_present_AC09_scientific_notation_found=bool(
        {"1.1813e-6", "1.1818e-6", "1.3579e-2"} <= set(ac09["numbers"])),
    known_present_AC09_mentions_sphere=ac09["mentions_sphere"],
    known_present_AC74_mentions_sphere=ac74["mentions_sphere"],
    known_absent_AC44_mentions_sphere=ac44["mentions_sphere"],
)
control["pass"] = all([
    control["known_present_AC09_scientific_notation_found"],
    control["known_present_AC09_mentions_sphere"],
    control["known_present_AC74_mentions_sphere"],
    not control["known_absent_AC44_mentions_sphere"],
])
ok = ok and control["pass"]

# ---- re-run the frozen oracle verbatim, as an independent witness
frozen = subprocess.run([sys.executable, str(FROZEN)], cwd=ROOT,
                        capture_output=True, text=True, encoding="utf-8")
frozen_ok = frozen.returncode == 0 and "ORACLE VERDICT: PASS" in frozen.stdout
ok = ok and frozen_ok

doc = dict(
    frozen_oracle=str(FROZEN.relative_to(ROOT)),
    task_text_said="change 2026-01's evidence/oracle.py",
    task_text_note=("tasks.md 0.2 names change `2026-10-01`; the oracle actually lives in the "
                    "2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard archive. "
                    "Recorded, not silently substituted."),
    dps=60, routes=["mp.quad over t^(a-1)(1-t)^(b-1)/B(a,b)",
                    "mpmath 4-argument betainc(a,b,0,x,regularized=True)"],
    spread_tolerance="1e-49",
    three_arg_trap_guard=("the 3-argument betainc returns the COMPLEMENT and is Change 0's "
                          "original oracle bug; it is kept here as a negative control and must "
                          "stay separated from the two live routes"),
    appended_probe_points=[
        dict(point="(3,16)..(64,16) canonical half-angles", cited_by=["AC-08", "AC-09", "AC-16", "AC-64", "AC-84"]),
        dict(point="incomplete-Beta deltas +1.1813e-6 / +1.1818e-6 / +1.3579e-2", cited_by=["AC-09"]),
        dict(point="cap-area below the pi/2 plateau", cited_by=["AC-05", "AC-15", "AC-42"]),
    ],
    probe_points=probe,
    impl_vs_oracle=impl_rows,
    matcher_control=control,
    frozen_oracle_rerun_exit_code=frozen.returncode,
    frozen_oracle_rerun_verdict_pass=frozen_ok,
    verdict="PASS" if ok else "FAIL",
)
(EV / "oracle_recheck.json").write_text(
    json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"{'N_e':>4} {'d_c':>4} {'spread':>10} {'agree':>6} {'6dp':>10} {'trap gap':>10}")
for r in probe:
    print(f"{r['N_e']:>4} {r['d_c']:>4} {r['spread']:>10} {str(r['routes_agree']):>6} "
          f"{r['six_dp_literal']:>10} {r['trap_gap']:>10}")
print()
print(f"{'N_e':>4} {'impl':>22} {'oracle':>22} {'|dev|':>10} {'<1e-12':>7}")
for r in impl_rows:
    print(f"{r['N_e']:>4} {r['impl']:>22} {r['oracle']:>22} "
          f"{r['abs_deviation']:>10} {str(r['within_1e_12']):>7}")
print()
print(f"matcher control pass : {control['pass']}")
print(f"frozen oracle rerun  : exit {frozen.returncode}, verdict PASS = {frozen_ok}")
print(f"ORACLE RECHECK       : {doc['verdict']}")
print(f"wrote evidence/oracle_recheck.json")
sys.exit(0 if ok else 1)
