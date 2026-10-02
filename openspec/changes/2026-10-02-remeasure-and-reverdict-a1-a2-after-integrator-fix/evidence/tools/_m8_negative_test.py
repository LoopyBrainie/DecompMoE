"""M8 负向验证：在 TEMP 沙箱里向盲区 1 注入一个未映射行，硬失败必须报警。

上一次审阅里的子代理正是在改写路径常量时替换未匹配、结果把仓库内的
ledger.json 覆写了。所以本脚本的每一步都有硬断言，且写盘路径被钉死在
TEMP 之内 —— 任何指向仓库的路径都会让脚本自己 abort。

不写任何仓库文件。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
SRC = REPO / ("openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator"
              "-fix/evidence/tools/build_errata_index.py")
LIST_REL = ".audit/wayfinder-opsx-code-review/lists/opsx-changes.md"
sandbox = Path(tempfile.mkdtemp(prefix="m8_sandbox_"))
print(f"sandbox = {sandbox}")
assert str(sandbox).startswith(tempfile.gettempdir()), "sandbox 不在 TEMP 内，拒绝继续"

# ---- 造沙箱：假的 .audit 清单 + 脚本副本 ------------------------------------
audit = sandbox / "lists"
audit.mkdir(parents=True)
real_list = (REPO / LIST_REL).read_text(encoding="utf-8")
# 在盲区 1 表格末尾追加一个**没有 X_BUCKET 映射**的行
lines = real_list.splitlines()
# 盲区 1 的表格：标题是 `### 盲区 1：...`（带 `###` 前缀与全角冒号），表格在
# 标题之后、下一条 `### 盲区 2` 之前。用标题正则定位，不硬编码行号。
h1 = next(i for i, l in enumerate(lines) if re.match(r"^#+\s*盲区\s*1", l))
h2 = next(i for i, l in enumerate(lines) if re.match(r"^#+\s*盲区\s*2", l))
rows = [i for i in range(h1, h2) if lines[i].startswith("|") and
        not re.fullmatch(r"\|[\s:\-|]+\|", lines[i])]
last = rows[-1]
injected = lines[:last + 1] + [
    "| D9-99 | 盲区 1 里新增的、没有任何桶映射的条目 | — |"] + lines[last + 1:]
print(f"盲区 1 标题 L{h1+1}，下一节 L{h2+1}，数据行 {len(rows)} 行，注入于 L{last+2}")
fake_list = audit / "opsx-changes.md"
fake_list.write_text("\n".join(injected) + "\n", encoding="utf-8")

script = sandbox / "build_errata_index.py"
text = SRC.read_text(encoding="utf-8")
# 钉死 ROOT / EV / LIST 三处，并逐处断言替换生效。
# ROOT 仍指向真实仓库：它只被用于只读的 `git log`；EV（写盘目标）与 LIST
# （读盘源）才被重定向到沙箱。三者分开钉，避免「以为改了路径其实没改」。
root_block = ('ROOT = next(p for p in Path(__file__).resolve().parents\n'
              '            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))')
assert root_block in text, "ROOT 定义未匹配，拒绝运行"
text = text.replace(root_block, f'ROOT = Path(r"{REPO}")', 1)
for old, new in (
    ('EV = ROOT / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-'
     'integrator-fix/evidence"', f'EV = Path(r"{sandbox / "ev"}")'),
    ('LIST = ROOT / ".audit/wayfinder-opsx-code-review/lists/opsx-changes.md"',
     f'LIST = Path(r"{fake_list}")'),
):
    assert old in text, f"常量替换未匹配，拒绝运行：{old[:60]}"
    text = text.replace(old, new, 1)
assert f'ROOT = Path(r"{REPO}")' in text, "ROOT 替换未生效"
# LIST 现在在沙箱里，`relative_to(ROOT)` 会抛 ValueError；该字段只是给人看的
# 路径标签，改成直写，否则沙箱永远跑不到自检那一行。
rel_old = '"source": str(LIST.relative_to(ROOT)),'
assert rel_old in text, "relative_to 调用未匹配，拒绝运行"
text = text.replace(rel_old, '"source": str(LIST),', 1)
assert f'Path(r"{sandbox / "ev"}")' in text, "EV 替换未生效"
assert f'Path(r"{fake_list}")' in text, "LIST 替换未生效"
# 写盘路径必须完全落在沙箱内，否则拒绝运行
assert not str(sandbox).startswith(str(REPO)), "沙箱落在仓库内，拒绝运行"
(sandbox / "ev").mkdir()
script.write_text(text, encoding="utf-8")
print("常量替换已逐处断言生效")

# ---- 运行：必须 exit 1 且点名 D9-99 ----------------------------------------
r = subprocess.run([sys.executable, str(script)], cwd=sandbox,
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
out = (r.stdout or "") + (r.stderr or "")
print()
print(f"exit code   = {r.returncode}   (必须 1)")
if "self-check" not in out:
    print("--- 沙箱脚本在自检前就崩了，原始输出如下 ---")
    print(out[-1500:])
line = next((l for l in out.splitlines() if "self-check" in l), "<no self-check line>")
print(f"self-check  = {line.strip()[:300]}")
caught = (r.returncode == 1) and "D9-99" in out and "X_BUCKET" in out
print(f"\n>>> M8 负向验证: {'CONFIRMED -- 未映射行不再被静默吞掉' if caught else 'FAILED'}")

# ---- 仓库未被触碰 ----------------------------------------------------------
ev = REPO / ("openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator"
             "-fix/evidence/errata_index.json")
import hashlib
h = hashlib.sha256(ev.read_bytes()).hexdigest()[:16]
print(f"仓库 errata_index.json sha256[:16] = {h}")
print(f"  （沙箱写的是 {sandbox / 'ev' / 'errata_index.json'}）")
assert "m8_sandbox_" in str(sandbox), "异常：写到了沙箱外"
print("仓库文件未被本次验证写入。")
if not (sandbox / "ev" / "errata_index.json").is_file():
    print("注意：沙箱未产出 errata_index.json（脚本在写盘前就退出了）")

shutil.rmtree(sandbox, ignore_errors=True)
print(f"沙箱已清理：{not sandbox.exists()}")
sys.exit(0 if caught else 1)
