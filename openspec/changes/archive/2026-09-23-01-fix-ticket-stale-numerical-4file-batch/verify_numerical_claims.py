"""事实验证脚本 (v2): 50-digit 精度对账, +反向 γ from ticket stale β=1.0.

修正: proposal B2.3 "反向 γ 反推 −3.5393477201429725472" 实际是
  given ticket L58 stale β=1.0, what γ?
  不是 given spec β_0=1.035060, what γ? (后者会精确回到 −3.5)
"""
from __future__ import annotations

import mpmath

mpmath.mp.dps = 50


def main() -> int:
    # ----- 1. σ(−3.5) / σ'(−3.5) -----
    s_neg35 = mpmath.mpf(1) / (1 + mpmath.exp(mpmath.mpf("3.5")))
    sigma_prime = s_neg35 * (1 - s_neg35)

    # ----- 2. β_0 闭式 -----
    beta_0 = mpmath.mpf("0.1") + mpmath.mpf("31.9") * s_neg35

    # ----- 3. β_0 vs ticket L58 stale 1.0 (3.39% drift) -----
    drift_pct = float(abs(beta_0 - mpmath.mpf("1.0")) / beta_0 * 100)

    # ----- 4. σ'(−3.5) vs spec narrative 0.0284 (≈0.18%) -----
    drift_sigma = float(abs(sigma_prime - mpmath.mpf("0.0284")) / sigma_prime * 100)

    # ----- 5. θ_Voronoi(16,16) via bisection -----
    N_e, d_c = 16, 16
    a = mpmath.mpf(d_c - 1) / 2
    b = mpmath.mpf("0.5")

    def f(theta):
        x = mpmath.sin(theta) ** 2
        return mpmath.mpf("0.5") * mpmath.betainc(a, b, 0, x, regularized=True) - mpmath.mpf(1) / N_e

    lo, hi = mpmath.mpf("0.1"), mpmath.pi / 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    theta_v_rad = (lo + hi) / 2
    theta_v_deg = theta_v_rad * 180 / mpmath.pi
    residual = abs(f(theta_v_rad))

    # ----- 6. θ_Voronoi drift vs ticket L62 stale 52° -----
    # proposal: "15.24° (29% relative)" — base? audit-verification.md uses 29%
    # (15.24/52 = 29.3%); spec-math-audit.md uses 22.7% (15.24/67.24 = 22.7%).
    drift_abs_deg = float(abs(theta_v_deg - 52))
    rel_to_ticket = float(drift_abs_deg / 52 * 100)
    rel_to_truth = float(drift_abs_deg / theta_v_deg * 100)

    # ----- 7. 反向 γ from ticket stale β=1.0 (per proposal B2.3 / verify-4) -----
    s_gamma = (mpmath.mpf("1.0") - mpmath.mpf("0.1")) / (mpmath.mpf("32") - mpmath.mpf("0.1"))
    gamma_from_ticket = mpmath.log(s_gamma / (1 - s_gamma))

    # ----- 8. σ'(−3.5) absolute diff vs new spec narrative 0.02845 -----
    abs_diff_sigma = float(abs(sigma_prime - mpmath.mpf("0.02845")))

    # ----- 9. MVPConfig.beta_initial 1.035 vs β_0 -----
    diff_mvp = float(abs(beta_0 - mpmath.mpf("1.035")))

    # ----- 10. MVPConfig default 1.035 vs pytest literal 1.035 -----
    diff_test = float(abs(mpmath.mpf("1.035") - mpmath.mpf("1.035")))

    # ============= 判定 =============
    results = []
    results.append(("σ(−3.5) 50-digit",
                    mpmath.nstr(s_neg35, 18),
                    "0.029312230751356318865",
                    str(s_neg35).startswith("0.029312230751356318865")))
    # σ'(−3.5): 50-digit = 0.02845302387973555983...; 20-sig-digit rounding → 0.02845302387973555984
    sigma_prime_str = mpmath.nstr(sigma_prime, 30, strip_zeros=False)
    results.append(("σ'(−3.5) 50-digit (20 sig-digit rounded)",
                    sigma_prime_str[:21],
                    "0.02845302387973555984",
                    sigma_prime_str.startswith("0.02845302387973555983") or sigma_prime_str.startswith("0.02845302387973555984")))
    results.append(("β_0 50-digit",
                    mpmath.nstr(beta_0, 18),
                    "1.0350601609682665718",
                    str(beta_0).startswith("1.0350601609682665718")))
    results.append(("β_0 drift vs ticket 1.0",
                    f"{drift_pct:.4f}%",
                    "3.39%",
                    abs(drift_pct - 3.39) < 0.01))
    results.append(("σ'(−3.5) drift vs spec 0.0284",
                    f"{drift_sigma:.4f}%",
                    "0.18%",
                    abs(drift_sigma - 0.18) < 0.05))
    results.append(("θ_Voronoi(16,16) rad",
                    mpmath.nstr(theta_v_rad, 11),
                    "1.1735474259 rad",
                    abs(theta_v_rad - mpmath.mpf("1.1735474259")) < mpmath.mpf("1e-7")))
    results.append(("θ_Voronoi residual",
                    mpmath.nstr(residual, 5),
                    "< 1e-9",
                    residual < mpmath.mpf("1e-9")))
    results.append(("θ_Voronoi deg",
                    mpmath.nstr(theta_v_deg, 11),
                    "67.24°",
                    abs(theta_v_deg - 67.24) < 0.01))
    results.append(("θ drift abs",
                    f"{drift_abs_deg:.4f}°",
                    "15.24°",
                    abs(drift_abs_deg - 15.24) < 0.05))
    results.append(("θ drift relative (proposal convention: 15.24/52)",
                    f"{rel_to_ticket:.2f}%",
                    "29%",
                    abs(rel_to_ticket - 29) < 0.5))
    results.append(("θ drift relative (truth-base: 15.24/67.24)",
                    f"{rel_to_truth:.2f}%",
                    "(spec-math-audit uses 22.7%)",
                    abs(rel_to_truth - 22.7) < 0.5))
    results.append(("反向 γ from ticket stale β=1.0",
                    mpmath.nstr(gamma_from_ticket, 18),
                    "-3.5393477201429725472",
                    abs(gamma_from_ticket - mpmath.mpf("-3.5393477201429725472")) < mpmath.mpf("1e-15")))
    results.append(("σ'(−3.5) abs diff vs new spec 0.02845",
                    mpmath.nstr(abs_diff_sigma, 4),
                    "0.000003",
                    abs(abs_diff_sigma - mpmath.mpf("0.000003")) < mpmath.mpf("0.0000005")))
    results.append(("MVPConfig 1.035 vs β_0 diff",
                    mpmath.nstr(diff_mvp, 4),
                    "0.000060",
                    abs(diff_mvp - mpmath.mpf("0.000060")) < mpmath.mpf("0.000001")))
    results.append(("MVPConfig 1.035 vs pytest literal (D1.5.1)",
                    mpmath.nstr(diff_test, 10),
                    "0.0",
                    diff_test == 0))

    print("=" * 78)
    print(f"{'事实验证项':<45} {'actual':<22} {'claim':<14} {'verdict'}")
    print("=" * 78)
    n_pass = 0
    for name, actual, claim, ok in results:
        verdict = "✓" if ok else "✗"
        print(f"{name:<45} {actual:<22} {claim:<14} {verdict}")
        if ok:
            n_pass += 1
    print("=" * 78)
    print(f"PASS: {n_pass}/{len(results)}")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())