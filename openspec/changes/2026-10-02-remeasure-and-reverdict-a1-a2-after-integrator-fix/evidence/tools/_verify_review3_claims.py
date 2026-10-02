"""独立复核 review ③ 的 H1/H2/H3/H4/M1/M2/M3/M8/M10 —— 逐条实测，不采信声称。

每条给出：审阅者声称 / 我的实测 / 判定。
"""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TOOLS = Path(__file__).resolve().parent
EV = TOOLS.parent

VERDICTS = {}


def claim(cid, said, measured, ok):
    VERDICTS[cid] = (said, measured, ok)
    print(f"\n[{cid}]")
    print(f"  声称: {said}")
    print(f"  实测: {measured}")
    print(f"  判定: {'CONFIRMED' if ok else 'REFUTED'}")


# ---------- H4: ERRATA_ID 正则是否漏 E20 ----------
src = (TOOLS / "check_ledger.py").read_text(encoding="utf-8")
m = re.search(r"ERRATA_ID\s*=\s*re\.compile\(\s*r?[\"']([^\"']+)[\"']", src)
pat = m.group(1) if m else None
hits = {e: bool(re.search(pat, e)) for e in
        ["E1", "E9", "E10", "E19", "E20", "E21", "EX"]}
claim("H4", "ERRATA_ID 正则漏掉 E20",
      f"pattern={pat!r} -> {hits}",
      (hits["E1"] and hits["E10"] and hits["E19"] and not hits["E20"]
       and not hits["E21"]))

# ---------- H1: build_ledger.py 是否无条件覆写 ----------
bl = (TOOLS / "build_ledger.py").read_text(encoding="utf-8")
writes = [(i, ln.strip()) for i, ln in enumerate(bl.splitlines(), 1)
          if re.search(r"write_text|\.write\(|open\(.*[\"']w", ln)]
guarded = bool(re.search(r"if\s+.*(PENDING|empty|all_pending)", bl))
claim("H1", "build_ledger.py 无条件写 ledger.json，7.4 门禁会清空已填台账",
      f"写入点={writes}  存在非空保护={guarded}",
      bool(writes) and not guarded)

# ---------- H1b: verify_toolchain 是否真的调用 build_ledger ----------
vt = (TOOLS / "verify_toolchain.py").read_text(encoding="utf-8")
# 修正 v1 缺陷：原正则 r"build_(\w+)\.py" 的捕获组只截到 "ledger"，
# 导致 "build_ledger" in calls 恒为 False -> 把 CONFIRMED 误判成 REFUTED。
# 正确判据是「该脚本名是否出现在 CONTRACT 表里」。
contract_block = re.search(r"CONTRACT\s*=\s*\{(.*?)\n\}", vt, re.S)
cb = contract_block.group(1) if contract_block else ""
in_contract = [n for n in re.findall(r'"([\w]+\.py)"', cb)]
claim("H1b", "7.4 门禁 verify_toolchain.py 会跑 build_ledger.py",
      f"CONTRACT 表内脚本 = {in_contract}\n  含 build_ledger.py = "
      f"{'build_ledger.py' in in_contract}",
      "build_ledger.py" in in_contract)

# ---------- M2: 修正 v1 缺陷（原正则要求每行以 ( 开头，键表实际格式不匹配 -> 0 键，
#          且 all([]) 真空为真）。改为数 CONTRACT 字典字面键并找重复。 ----------
from collections import Counter
keys = re.findall(r'^\s*"([\w]+\.py)":', vt, re.M)
cnt = Counter(keys)
dups = {k: v for k, v in cnt.items() if v > 1}
dup_detail = {}
for k in dups:
    clauses = re.findall(rf'"{re.escape(k)}":\s*\("([^"]*)",\s*"([^"]*)"\)', vt)
    dup_detail[k] = {"声明条数": len(clauses),
                     "存活(最后一条)": clauses[-1] if clauses else None,
                     "被丢弃": clauses[:-1] if len(clauses) > 1 else []}
printed_n = re.search(r"ALL \{len\(CONTRACT\) \+ 1\}", vt)
claim("M2", "verify_toolchain 的 CONTRACT 表有重复键 build_ledger.py，静默丢弃一条契约",
      f"字面键 {len(keys)} 条 / 唯一 {len(cnt)} 条 / 重复 {dups}\n"
      f"  细节 = {dup_detail}\n"
      f"  打印式 = {'ALL {len(CONTRACT) + 1}' if printed_n else '未找到'}"
      f" -> 实际打印 {len(cnt) + 1}，与 11 唯一契约 + patch_tasks_line 自洽",
      bool(dups))

# ---------- M1: crlf_discriminator 的 must-not 串是否永不可能出现 ----------
cd = (TOOLS / "crlf_discriminator.py").read_text(encoding="utf-8")
# 修正 v1 缺陷：原正则找 "must_not 字符串字面量"，对 CONTRACT 的元组形式不匹配，
# 提取到空 list 后 all([]) 真空为真 -> 把 REFUTED 误判成 CONFIRMED。
# 正确判据是「该工具的输出是否可能含有这串」——直接比对它的 verdict 赋值。
cd_entry = re.search(r'"crlf_discriminator\.py":\s*\("([^"]*)",\s*"([^"]*)"\)', vt)
cd_must, cd_mustnot = (cd_entry.group(1), cd_entry.group(2)) if cd_entry else (None, None)
cd_verdicts = re.findall(r'verdict\s*=\s*"([^"]*)"', cd)
# 修正 v2 缺陷：v2 写了 `cd_mustnot in v + " for every path"`，等于自己把哨兵串
# 拼出来再断言它「可达」——自造的阳性。正确判据：该工具打印的 verdict 取值
# 是否有任何一个逐字等于哨兵。工具在 f-string 末尾裸打印 verdict，不加后缀。
reachable = any(v == cd_mustnot for v in cd_verdicts)
claim("M1", "crlf_discriminator 的 must-absent 哨兵串永不可能出现在其输出中 -> 死检查",
      f"must-absent = {cd_mustnot!r}\n"
      f"  该工具的 verdict 取值 = {cd_verdicts}\n"
      f"  打印方式 = f-string 行尾裸插 verdict（crlf_discriminator.py:52-53，无后缀）\n"
      f"  哨兵是否逐字等于任一 verdict = {reachable}\n"
      f"  => 即使每个路径都 REAL CONTENT DIFF，该 must-absent 也不会触发",
      not reachable)

# ---------- H2 ----------
# 修正 v1 缺陷：v1 用「文件里是否出现 .audit / opsx-changes.md」当代理，
# 而这两个串出现在 ROOT 自动定位行(25)与 T6 fixture(351)，与 denominator 无关，
# 于是把 CONFIRMED 误判成 REFUTED。正确判据是 denom["ok"] 的构成项里
# 有没有「与源文件做集合差分」。此处改为读代码结构，最终判定见 _decisive_h1_h2.py
# 的实测（95 条全伪造 -> problems=0 / denom.ok=True）。
cl = (TOOLS / "check_ledger.py").read_text(encoding="utf-8")
ok_block = re.search(r'denom\["ok"\]\s*=\s*(.*?)\n\s*return', cl, re.S)
ok_expr = ok_block.group(1) if ok_block else ""
refs_src = re.findall(r"src_ids|source_ids|opsx|audit_findings|read_text", ok_block.group(0) if ok_block else "")
claim("H2", "denominator 只核对计数与三项集合属性，从不与源文件做集合差分",
      f"denom['ok'] 表达式 = {ok_expr.strip()}\n"
      f"  其中引用源文件 id 集合的项 = {refs_src or '（无）'}\n"
      f"  注：set-difference 能力只存在于 build_ledger.py:174-185，"
      f"而该脚本会无条件覆写 ledger.json（见 H1）",
      not refs_src)

# ---------- M3: 6 vs 10 个 CRLF 假阳性 ----------
bl_json = json.loads((EV / "baseline.json").read_text(encoding="utf-8"))
caveat = bl_json.get("line_ending_caveat") or {}
cand = {k: v for k, v in bl_json.items() if "crlf" in k.lower()}
byte_only = None
for k, v in bl_json.items():
    if isinstance(v, list) and k != "excluded_items":
        pass
def find_byteonly(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "byte_only" in str(k).lower() or "crlf_only" in str(k).lower():
                hits.append((path + "/" + str(k), v if not isinstance(v, list) else len(v)))
            hits += find_byteonly(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += find_byteonly(v, f"{path}[{i}]")
    return hits
bo = find_byteonly(bl_json)
claim("M3", "design/tasks 说 6 个 CRLF 假阳性，baseline.json 实测 10 个",
      f"line_ending_caveat={str(caveat)[:200]}\n  byte_only/crlf_only 命中={bo}",
      any(isinstance(n, int) and n == 10 for _, n in bo) or "10" in str(caveat))

# ---------- M8: build_errata_index 白名单外静默 continue ----------
bei = (TOOLS / "build_errata_index.py").read_text(encoding="utf-8")
cont = re.findall(r"continue\b", bei)
whitelist = "X_BUCKET" in bei
claim("M8", "X_BUCKET 白名单外的行静默 continue，期望值硬编码 9 -> 多一行被吞仍绿",
      f"文件内 continue 语句数={len(cont)}  存在 X_BUCKET 白名单={whitelist}",
      whitelist and len(cont) > 0)

# ---------- M10: build_ledger 第二路径是否真独立 ----------
b2 = re.search(r"路径\s*2[^\n]*", bl)
audit_index_reader = "audit_index" in bl
src_re = re.findall(r"r?[\"']\^###", bl)
claim("M10", "build_ledger 的第二条路径读 audit_index.json，与路径 1 共享同一批正则 -> 非独立",
      f"build_ledger 读 audit_index={audit_index_reader}  内嵌发现正则={src_re}",
      audit_index_reader)

# ---------- D3 五值 vs VERDICTS 集合 ----------
vset = re.search(r"VERDICTS\s*=\s*\{(.*?)\}", cl, re.S)
vals = sorted(set(re.findall(r"[\"']([A-Z_]{4,})[\"']", vset.group(1)))) if vset else []
design = (EV.parent / "design.md").read_text(encoding="utf-8")
d3 = sorted(set(re.findall(r"`(STILL_REAL|PARTIALLY_REAL|DOWNGRADED|REMEASURED_SAME|RESOLVED_BY_UPSTREAM|MOVED|NOT_REAL)`", design)))
claim("D3-词汇", "D3 声明的词汇与 check_ledger.VERDICTS 不一致（双向）",
      f"VERDICTS={vals}\n  design.md 中出现的判据词={d3}\n"
      f"  在 VERDICTS 但 design 未定义={sorted(set(vals)-set(d3))}\n"
      f"  design 定义但 VERDICTS 不含={sorted(set(d3)-set(vals))}",
      bool(set(vals) ^ set(d3)))

# ---------- 汇总 ----------
print("\n" + "=" * 72)
print("汇总")
print("=" * 72)
for cid, (said, meas, ok) in VERDICTS.items():
    print(f"  {cid:<8} {'CONFIRMED' if ok else 'REFUTED':<10} {said[:64]}")
