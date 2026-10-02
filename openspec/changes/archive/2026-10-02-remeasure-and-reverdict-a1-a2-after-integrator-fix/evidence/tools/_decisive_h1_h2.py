"""决定性实测：H2（伪造 ac_id 报 CLEAN）、M1（must-not 永不可能失败）、M2 精确化。

零写入：只用 importlib 载入 check_ledger 模块并对内存中的 list 调用 check()。
不碰 ledger.json，不跑 build_ledger.py。
"""
import copy
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
EV = TOOLS.parent
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))

print("=" * 74)
print("H2  决定性实测：把真实 ac_id 换成伪造的，检查器是否仍报 CLEAN+COMPLETE")
print("=" * 74)

spec = importlib.util.spec_from_file_location("cl_probe", TOOLS / "check_ledger.py")
cl = importlib.util.module_from_spec(spec)
_stdout = sys.stdout
sys.stdout = open(__import__("os").devnull, "w", encoding="utf-8")   # 静音自测输出
try:
    spec.loader.exec_module(cl)          # 顶层自测会 sys.exit，必须吞掉
except SystemExit as exc:
    _code = exc.code
else:
    _code = None
finally:
    sys.stdout = _stdout
print(f"  check_ledger 模块已载入（自测 SystemExit={_code}，输出已静音），LEDGER =", cl.LEDGER)
assert cl.LEDGER == EV / "ledger.json", "LEDGER 定位异常，拒绝继续"

real = json.loads(cl.LEDGER.read_text(encoding="utf-8"))["entries"]
base = cl.check(copy.deepcopy(real))
print(f"\n  基线（未改）      : problems={len(base['problems'])} "
      f"outstanding={len(base['outstanding'])} denom.ok={base['denominator']['ok']}")

# --- 变异 1：把一个真实的源内 id 换成不存在的伪造 id（数量不变） ---
victim = next(e for e in real if e["ac_id"] == "AC-01")
m1 = copy.deepcopy(real)
next(e for e in m1 if e["ac_id"] == "AC-01")["ac_id"] = "AC-199"
r1 = cl.check(m1)
print(f"  变异1 AC-01->AC-199: problems={len(r1['problems'])} "
      f"outstanding={len(r1['outstanding'])} denom.ok={r1['denominator']['ok']}"
      f"  <- denom.in_source={r1['denominator']['in_source']}")

# --- 变异 2：一次换两个 ---
m2 = copy.deepcopy(real)
for old, new in (("AC-01", "AC-199"), ("AC-02", "AC-198")):
    next(e for e in m2 if e["ac_id"] == old)["ac_id"] = new
r2 = cl.check(m2)
print(f"  变异2 换两个        : problems={len(r2['problems'])} "
      f"outstanding={len(r2['outstanding'])} denom.ok={r2['denominator']['ok']}")

# --- 变异 3：把 95 条全换成 95 个伪造 id ---
m3 = copy.deepcopy(real)
n = 0
for e in m3:
    if e["ac_id"].startswith("AC-"):
        n += 1
        e["ac_id"] = f"AC-9{n:02d}"
r3 = cl.check(m3)
print(f"  变异3 全 95 条伪造  : 替换 {n} 条 -> problems={len(r3['problems'])} "
      f"outstanding={len(r3['outstanding'])} denom.ok={r3['denominator']['ok']}")

h2 = (not r1["problems"]) and r1["denominator"]["ok"] and r3["denominator"]["ok"]
print(f"\n  >>> H2 判定: {'CONFIRMED —— 伪造 id 完全不触发任何检查' if h2 else 'REFUTED'}")

# --- 源文件真实 id 集合，供对照 ---
src = ROOT / ".audit/wayfinder-opsx-code-review/lists/opsx-changes.md"
src_ids = set(re.findall(r"^###\s+((?:AC|UD)-\d+)", src.read_text(encoding="utf-8"), re.M))
led_ids = {e["ac_id"] for e in real if e["ac_id"].startswith("AC-")}
print(f"  对照: 源文件 AC-/UD- 标题 {len(src_ids)} 个；台账源内 AC- {len(led_ids)} 个")
print(f"        两者是否可互校: 台账未持有 src_ids（check_ledger 里无此集合）="
      f"{'src_ids' not in Path(TOOLS / 'check_ledger.py').read_text(encoding='utf-8')}")

print()
print("=" * 74)
print("M1  crlf_discriminator 的 must-not 串是否真的永不可能出现")
print("=" * 74)
vt = (TOOLS / "verify_toolchain.py").read_text(encoding="utf-8")
cd_entry = re.search(r'"crlf_discriminator\.py":\s*\("([^"]*)",\s*"([^"]*)"\)', vt)
must, mustnot = cd_entry.group(1), cd_entry.group(2)
print(f"  must-appear = {must!r}")
print(f"  must-absent = {mustnot!r}")
hits = []
for pat in (mustnot,):
    r = subprocess.run(["git", "grep", "-n", "-F", pat, "HEAD", "--"],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    hits.append(("HEAD 全仓", r.stdout.strip() or "(0 hits)"))
    r2 = subprocess.run(["git", "grep", "-n", "-F", pat, "--",
                         "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix"],
                        cwd=ROOT, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    hits.append(("change 目录", r2.stdout.strip() or "(0 hits)"))
    # 也看工作树未跟踪部分
    direct = [p.name for p in TOOLS.rglob("*")
              if p.is_file() and p.suffix in (".py", ".txt")
              and pat in p.read_text(encoding="utf-8", errors="replace")]
    hits.append(("tools/ 目录内", str(direct)))
for where, res in hits:
    print(f"    {where:<16}: {res}")
m1_conf = all("(0 hits)" in r or r == "[]" for _, r in hits)
print(f"\n  >>> M1 判定: {'CONFIRMED —— 该 must-absent 永不可能被违反（死检查）' if m1_conf else 'REFUTED'}")

print()
print("=" * 74)
print("M2  精确化：重复键丢掉了哪条契约")
print("=" * 74)
keys = re.findall(r'^\s*"([^"]+\.py)":', vt, re.M)
from collections import Counter
c = Counter(keys)
dups = {k: v for k, v in c.items() if v > 1}
print(f"  CONTRACT 字面行数 = {len(keys)}   唯一键 = {len(c)}   重复 = {dups}")
for k in dups:
    clauses = re.findall(rf'"{re.escape(k)}":\s*\("([^"]*)",\s*"([^"]*)"\)', vt)
    print(f"  {k} 的两条 must-appear:")
    for i, (a, b) in enumerate(clauses, 1):
        alive = "生效" if (a, b) == clauses[-1] else "被覆盖丢弃"
        print(f"    [{i}] {a!r}  <- {alive}")
    print(f"  生效值 = {clauses[-1][0]!r}")
bl = (TOOLS / "build_ledger.py").read_text(encoding="utf-8")
for variant in ("all status PENDING: True", "all status PENDING : True"):
    print(f"  build_ledger.py 源码含 {variant!r} ? "
          f"{'是（该子句硬编码在脚本里，非运行输出）' if variant in bl else '否'}")
print(f"  => 'ALL {{len(CONTRACT)+1}}' 打印值 = {len(c) + 1}；"
      f"工具实数 = {len(c)} + patch_tasks_line.py = {len(c) + 1}  -> 计数自洽")
print(f"  >>> M2 判定: 真实缺陷是重复键静默丢弃一条契约；'12' 这个数本身正确")
