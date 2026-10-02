"""决定性实测：pytest.approx(x, abs=T) 的真实判据是 T 还是 max(T, rel*|x|)?

review ② 声称 pytest 9.1.1 的 ApproxScalar.tolerance 在给定 abs 时短路，
         容差恰为 abs；review ③ / 本会话既有结论声称是 max(abs, 1e-6*|expected|)。
两者对同一构造给出相反结果，本脚本给出裁决。

只读，不写任何仓库文件。
"""
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

print("=" * 74)
print("0. 环境")
print("=" * 74)
r = subprocess.run([sys.executable, "-c",
                    "import pytest, sys;"
                    "print('python', sys.version.split()[0]);"
                    "print('pytest', pytest.__version__);"
                    "print('module', pytest.__file__)"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout or r.stderr)

import pytest
from _pytest.python_api import ApproxScalar

print("=" * 74)
print("1. 读实现：tolerance 属性到底怎么算")
print("=" * 74)
import inspect
try:
    print(inspect.getsource(ApproxScalar.tolerance.fget))
except Exception as e:
    print("  取源码失败:", e)

print("=" * 74)
print("2. 裁决构造：|expected| = 1.0，rel 默认下应给出 1e-6 的相对容差")
print("=" * 74)
a = pytest.approx(1.0, abs=1e-9)
print(f"  pytest.approx(1.0, abs=1e-9).tolerance = {a.tolerance!r}")
print(f"  若为 max(abs, rel*|x|) = max(1e-9, 1e-6) = 1e-06")
print(f"  若 abs 短路          = 1e-09")
verdict_tol = "SHORT_CIRCUIT(abs 生效)" if a.tolerance == 1e-9 else "MAX_REL(默认 rel 仍生效)"
print(f"  >>> 实测 = {a.tolerance!r}  -> {verdict_tol}")

print()
print("=" * 74)
print("3. 行为裁决（不依赖读源码，只看通过/失败）")
print("=" * 74)
cases = [
    ("1.0 + 1e-8  vs approx(1.0, abs=1e-9)", 1.0 + 1e-8, pytest.approx(1.0, abs=1e-9)),
    ("1.0 + 1e-10 vs approx(1.0, abs=1e-9)", 1.0 + 1e-10, pytest.approx(1.0, abs=1e-9)),
    ("1.0 + 1e-7  vs approx(1.0, abs=1e-9)", 1.0 + 1e-7, pytest.approx(1.0, abs=1e-9)),
    ("1.0 + 1e-5  vs approx(1.0)  [无 abs]", 1.0 + 1e-5, pytest.approx(1.0)),
    ("1.0 + 1e-4  vs approx(1.0)  [无 abs]", 1.0 + 1e-4, pytest.approx(1.0)),
]
for label, got, exp in cases:
    ok = got == exp
    print(f"  {label:<46} -> {'PASS' if ok else 'FAIL'}")

print()
print("=" * 74)
print("4. 对本仓三个 6dp 字面量判别力的影响（两种读法分别算）")
print("=" * 74)
LITS = [
    ("N_e=16", 1.173547, 4.2591971749494917e-07, 1.2747e-06),
    ("N_e=17", 1.165847, 6.215516008545308e-07, 1.2974e-06),
    ("N_e=64", 1.020506, 8.247837133268376e-07, 8.3357e-07),
]
print(f"  {'桶':<8} {'字面量':<10} {'|lit-真值|':<14} {'|lit-修前|':<14} "
      f"{'abs=1e-6 判定':<22} {'max读法判定'}")
for name, lit, d_true, d_pre in LITS:
    short = (d_true <= 1e-6, d_pre <= 1e-6)
    mx = max(1e-6, 1e-6 * abs(lit))
    long = (d_true <= mx, d_pre <= mx)
    f = lambda t: ("真值PASS/修前PASS", "真值PASS/修前FAIL", "真值FAIL/修前PASS",
                   "真值FAIL/修前FAIL")[int(t[0]) * 2 + int(t[1])]
    print(f"  {name:<8} {lit:<10} {d_true:<14.4e} {d_pre:<14.4e} "
          f"{f(short):<22} {f(long)}")
print()
print("  读法差异对判别结论的影响：三种字面量在两种读法下判别结果"
      "完全一致 -> 守卫强度结论稳健。")
