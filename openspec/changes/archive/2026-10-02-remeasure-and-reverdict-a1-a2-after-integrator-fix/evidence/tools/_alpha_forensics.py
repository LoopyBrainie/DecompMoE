"""Change α 的取证：5.01e-52 / 2.92e-52 到底是什么，正确值又是多少。

只读。不写任何仓库文件。
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))

import mpmath as mp
mp.mp.dps = 60

# ---------------------------------------------------------------- 1. 定位假数值
print("=" * 76)
print("1. 假数值在 HEAD 的分布（真相源 + 副本）")
print("=" * 76)
for token in ("5.01e-52", "2.92e-52"):
    print(f"\n  token {token}:")
    r = subprocess.run(["git", "grep", "-n", "-F", token, "HEAD", "--"],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    for ln in r.stdout.strip().splitlines() or ["  (0 hits at HEAD)"]:
        print(f"    {ln}")
    r2 = subprocess.run(["git", "grep", "-n", "-F", token, "--", "openspec/changes"],
                        cwd=ROOT, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    n2 = len([x for x in r2.stdout.splitlines() if x])
    print(f"    (openspec/changes 工作树另有 {n2} 处提及)")

# ---------------------------------------------------- 2. 残差到底是什么
print()
print("=" * 76)
print("2. 残差 |0.5*I_{sin^2 θ}(a, 1/2) - 1/N_e| 在不同 θ 上的真值")
print("=" * 76)
print("  a = (d_c-1)/2 = 7.5 (d_c=16)")


def resid(theta, n_e, d_c=16):
    a = mp.mpf(d_c - 1) / 2
    x = mp.sin(theta) ** 2
    val = mp.mpf(1) / 2 * mp.betainc(a, mp.mpf(1) / 2, 0, x, regularized=True)
    return abs(val - mp.mpf(1) / n_e)


CANON = {16: mp.mpf("1.1735474259197175"), 64: mp.mpf("1.0205068247837132")}
print(f"\n  {'θ 来源':<44} {'N_e':>4} {'残差':>26}")
print(f"  {'spec 的 canonical 字面量（16 位十进制）':<44} {16:>4} "
      f"{mp.nstr(resid(CANON[16], 16), 26):>26}")
print(f"  {'spec 的 canonical 字面量（16 位十进制）':<44} {64:>4} "
      f"{mp.nstr(resid(CANON[64], 64), 26):>26}")

# 二分在 1e-13 收敛判据下实际停在哪
lo, hi = mp.mpf(0), mp.pi
for _ in range(200):
    mid = (lo + hi) / 2
    r = mp.mpf(1) / 2 * mp.betainc(mp.mpf(15) / 2, mp.mpf(1) / 2, 0,
                                  mp.sin(mid) ** 2, regularized=True) - mp.mpf(1) / 16
    if abs(r) < mp.mpf("1e-13"):
        break
    if r < 0:
        lo = mid
    else:
        hi = mid
print(f"\n  {'sphere._cap_radius 的二分停点（break<1e-13）':<44} {16:>4} "
      f"{mp.nstr(resid((lo + hi) / 2, 16), 26):>26}")
print(f"  {'spec 声称的 5.01e-52':<44} {16:>4} {'5.01e-52':>26}")

# 量纲论证：float64 只有 53 位尾数
print()
print("=" * 76)
print("3. 量纲自洽性：5.01e-52 在 float64 里可能吗")
print("=" * 76)
one = mp.mpf(1) / 16
print(f"  1/N_e                 = {mp.nstr(one, 20)}")
print(f"  若残差真为 5.01e-52，则 I_x 必须与 1/N_e 吻合到第 "
      f"{mp.nstr(mp.log10(one / mp.mpf('5.01e-52')), 6)} 位十进制")
print(f"  float64 尾数位数      = 53 位二进制 ≈ {mp.nstr(mp.log10(2) ** -1 * 53, 4)} 位十进制")
print("  => 单次浮点运算的舍入误差下界约 1e-16；1e-52 需要约 170 位尾数。")
print("     该值不可能是 float64 路径上的残差。")

# ---------------------------------------------------- 4. 正确的 provenance
print()
print("=" * 76)
print("4. 可以写进 spec 的可复算陈述")
print("=" * 76)
print("  (a) 二分收敛判据本身：`_cap_radius` 用 `break < 1e-13`，故返回值的残差")
print("      受二分判据而非浮点精度限制；实测残差恒为下表所列。")
print("  (b) 规范可以声称的上界：由判据反推，|G(θ) - 1/N_e| < 1e-13。")
for n_e, th in CANON.items():
    print(f"      N_e={n_e:<3} 在 canonical θ={mp.nstr(th, 17)} 处残差 = "
          f"{mp.nstr(resid(th, n_e), 6)}")
print("  (c) 规范可以声称的量级：残差由二分判据支配，量级 ~1e-14（不是 1e-52）。")
print("  (d) 规范化表述建议：把 '残差 5.01e-52' 改为")
print("      「二分在 |G-1/N_e| < 1e-13 处停止；在 canonical 值处的实测残差为 <X>，")
print("        该量由收敛判据决定，不是浮点精度下界」——并给出本脚本作为 provenance。")
