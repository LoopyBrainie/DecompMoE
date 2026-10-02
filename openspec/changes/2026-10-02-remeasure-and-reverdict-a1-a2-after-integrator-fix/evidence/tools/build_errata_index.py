"""Change 3 / task 0.5 -- index the audit list's ERRATA and BLIND-SPOT layers.

Why this exists: the change's 95-item scope was built from the 108 `### AC-`/
`### UD-` findings only. The same file also carries 11 effective errata, 2
withdrawn ones, a second E1-E20 errata table, and 6 declared blind spots -- and
blind spot 1 registers 9 upstream findings that have NO entity in
classified.json at all, one of which (D1-02) is the root cause of the very
quadraturer defect this change re-measures. None of it was in scope.

The 9 are not `###` headings. They are table rows at L1424-1434. That has
concrete consequences downstream:
  * they have no ac_id, so they need a namespaced synthetic one (`X-`),
  * they have no bucket, so D9 assigns one,
  * they have NO pin coordinate, so D1 step 3 must build the locus from zero,
  * and the "95 ids == source `###` headings" assertion cannot be relaxed into
    a subset test -- it must gain a second, separately-checkable criterion.

This tool extracts those layers and records the anchoring rev, so the plan's
"errata are pointers, never evidence" rule (D8) has something to point at.

Read-only: reads .audit/ and the working tree, writes only under evidence/.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
EV = ROOT / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence"
LIST = ROOT / ".audit/wayfinder-opsx-code-review/lists/opsx-changes.md"

lines = LIST.read_text(encoding="utf-8").splitlines()
HEAD = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                      capture_output=True, text=True).stdout.strip()
PIN = "6593a06"

# ---------------------------------------------------------------- 1. headings
# h3 stores 0-BASED indices; `line` is the 1-based number for citation only.
# Getting this wrong silently shifts every extracted row by one line, which looks
# exactly like a correct extraction, so the two forms are kept distinct.
h3 = [(i, l[4:].strip()) for i, l in enumerate(lines) if l.startswith("### ")]
findings = [(i, t) for i, t in h3 if re.match(r"(AC|UD)-\d+", t)]
section_headings = [(i, t) for i, t in h3 if not re.match(r"(AC|UD)-\d+", t)]


def span(start_pred, stop_pred):
    """0-based [start, stop) for a `###` section."""
    s = next(i for i, t in h3 if start_pred(t))
    e = next((i for i, t in h3 if i > s and stop_pred(t)), len(lines))
    return s, e


def ref(i):
    return f".audit/wayfinder-opsx-code-review/lists/opsx-changes.md:{i + 1}"


# ------------------------------------------------- 2. blind spot 1: the 9 rows
# The table sits under "### 盲区 1" and has 3 columns:
#   | 报告 §3 id | 内容 | 最近的本桶条目 |
bs1, be1 = span(lambda t: t.startswith("盲区 1"), lambda t: t.startswith("盲区 2"))
X_BUCKET = {                      # D9: proposed bucket per item
    "D1-02": ("A-1", "求积器失效无有效守卫：单面板 GL 零细分，b=1/2 奇点"),
    "D2-02": ("A-1", "MC 容差 sigma 建立在可证伪的独立性假设上，无有效守卫"),
    "D1-07": ("A-2", "治理把 impl-internal frame（8 点 GL + 逐位二分输出）钉成规范"),
    "D2-05": ("A-2", "spec 声称的三个实测 gap 有两个错、第三个原理上不可能"),
    "D3-01": ("A-3", "公开 API 超出 spec 声称的 totality / 逆映射声明"),
    "main38": ("A-3", "spec 内部两条 Requirement 互相矛盾（无条件断言 vs 次单位范数区）"),
    "main36": ("A-4", "Requirement 整条由行号断言构成且指错 Requirement"),
    "main73": ("A-4", "跨 spec 交叉引用全部写成行号且 Requirement 号错"),
    "main78": ("A-4", "治理条款的行号指针指向错误的 Requirement 块"),
}

unregistered = []
unmapped = []
for i in range(bs1, be1):
    ln = lines[i]
    if not ln.startswith("|"):
        continue
    # A markdown table's separator row is structure, not data. `|---|---|`
    # parses to a first cell of `---`, which the id regex happily accepts
    # because `-` is in its class. Excluding it by shape keeps the unmapped-row
    # failure (M8) meaningful instead of firing on the table's own furniture.
    if re.fullmatch(r"\|[\s:\-|]+\|", ln):
        continue
    cells = [c.strip().strip("*") for c in ln.strip("|").split("|")]
    if len(cells) < 2:
        continue
    ident = cells[0]
    m = re.match(r"([A-Za-z0-9\-]+)(?:\s*\+\s*gap\d+)?$", ident)
    if not m:
        continue
    key = m.group(1)
    # M8: a blind-spot row whose id is not in X_BUCKET used to `continue`
    # silently. The self-check below hardcodes the expected count, so a tenth
    # row was swallowed and the self-check still printed OK -- a row that exists
    # in the source but not in the ledger is exactly the scope error this file
    # exists to prevent. Unmapped rows are now a hard failure, reported.
    if key not in X_BUCKET:
        unmapped.append(ident)
        continue
    bucket, why = X_BUCKET[key]
    unregistered.append({
        "ac_id": f"X-{key}",
        "upstream_id": ident,
        "bucket": bucket,
        "bucket_rationale": why,
        "in_source_as_heading": False,
        "source_ref": ref(i),
        "statement": cells[1],
        "nearest_existing_item": cells[2] if len(cells) > 2 else None,
        "pin_coordinate": None,
        "pin_coordinate_note": ("盲区 1 表格不提供 file:line；D1 推导第 3 步必须从零建立坐标，"
                                "不得借用任何勘误给出的行号"),
    })

# ------------------------------------------------------------ 3. errata rows
def errata_rows(start_pred, stop_pred, min_cells=4, require_eid=True):
    """Rows of a `###` section's markdown table.

    Two section shapes exist and conflating them silently loses data:
      * per-errata tables (header `| # | 条目 | 清单声称 | 实测 |`, 4 columns),
      * the E20 observation table (header `| 观测 | 值 |`, 2 columns, first cell
        is prose not an E-id).
    Hence min_cells and require_eid are parameters, and "E20 found 0" -- the
    exact shape a missed section takes -- is asserted against in the self-check.
    """
    s, e = span(start_pred, stop_pred)
    out = []
    for i in range(s, e):
        ln = lines[i]
        if not ln.startswith("|"):
            continue
        cells = [c.strip().strip("*") for c in ln.strip("|").split("|")]
        if len(cells) < min_cells or set("".join(cells)) <= set("-: "):
            continue
        if require_eid and not re.match(r"E\d+", cells[0]):
            continue
        row = {"id": cells[0] if require_eid else None, "source_ref": ref(i)}
        row.update({"items": cells[1], "claimed": cells[2], "measured": cells[3]}
                   if len(cells) >= 4 else {"observation": cells[0], "value": cells[1]})
        out.append(row)
    return out


errata_a1 = errata_rows(lambda t: t == "生效勘误（11 条）", lambda t: t.startswith("E10 的根因"))
withdrawn_a1 = errata_rows(lambda t: t.startswith("已撤回"),
                           lambda t: t.startswith("两条维护规则"), min_cells=3)
errata_a2 = errata_rows(lambda t: t.startswith("E1–E19"), lambda t: t.startswith("E20 追加勘误"))
errata_a2_e20 = errata_rows(lambda t: t.startswith("E20 追加勘误"),
                            lambda t: t.startswith("清单自身的"),
                            min_cells=2, require_eid=False)

blindspots = [{"title": t, "source_ref": ref(i)} for i, t in h3 if re.match(r"盲区 \d", t)]
other_sections = [{"title": t, "source_ref": ref(i)} for i, t in
                  [(i, t) for i, t in h3 if not re.match(r"(AC|UD)-", t)]
                  if not re.match(r"盲区 \d", t)]

# ------------------------------------------------- 4. anchoring-rev divergence
anchors = set()
for ln in lines:
    for m in re.finditer(r"\b(188b9fb|6593a06|f6461d7)\b", ln):
        anchors.add(m.group(1))
spec_commits = subprocess.run(
    ["git", "log", "--oneline", f"{PIN}..HEAD", "--", "openspec/specs/"],
    cwd=ROOT, capture_output=True, text=True).stdout.strip().splitlines()

# --------------------------------------------------------------- 5. self-check
ids = [u["ac_id"] for u in unregistered]
problems = []
if unmapped:
    problems.append(f"blind-spot 1 rows with no X_BUCKET mapping (M8 -- these were "
                    f"silently dropped, leaving the row in the source and out of the "
                    f"ledger): {unmapped}")
if len(unregistered) != 9:
    problems.append(f"expected 9 unregistered findings, extracted {len(unregistered)}: {ids}")
if len(set(ids)) != len(ids):
    problems.append(f"duplicate X- ids: {ids}")
if len(findings) != 108:
    problems.append(f"expected 108 AC-/UD- findings, got {len(findings)}")
if len(errata_a1) != 11:
    problems.append(f"expected 11 effective A-1 errata, got {len(errata_a1)}")
if len(withdrawn_a1) != 2:
    problems.append(f"expected 2 withdrawn A-1 errata, got {len(withdrawn_a1)}")
if len(errata_a2) != 19:
    problems.append(f"expected E1-E19 A-2 errata rows, got {len(errata_a2)}")
# E20 is ONE errata expressed as a 5-row observation table, so counting rows here
# would inflate the errata count from 20 to 24.
if len(errata_a2_e20) != 5:
    problems.append(f"expected 5 E20 observation rows, got {len(errata_a2_e20)}")
if len(blindspots) != 6:
    problems.append(f"expected 6 blind spots, got {len(blindspots)}")
if len(findings) + len(blindspots) + len(other_sections) != len(h3):
    problems.append("section-heading partition does not account for every `###`")

doc = {
    "source": str(LIST.relative_to(ROOT)),
    "head": HEAD,
    "pin": PIN,
    "layer_structure": {
        "h3_headings_total": len(h3),
        "ac_ud_findings": len(findings),
        "section_headings": len(section_headings),
        "note": ("`###` 标题总数 != 发现数。108 是 AC-/UD- 发现，其余 27 个是章节标题"
                 "（盲区 / 附录 / 勘误 / Dedup 等），后几层不进入 108 分母。"),
    },
    "unregistered_findings": {
        "count": len(unregistered),
        "origin": "盲区 1（classified.json 中无实体）",
        "id_namespace": "X-<upstream id>",
        "entries": unregistered,
    },
    "errata": {
        "policy": ("D8：勘误只可作为定位线索，不得作为 verdict 来源，也不得出现在 "
                   "verdict_evidence 中。本索引是「线索可查」的物证，也是「未引用」的对照。"),
        "anchoring_rev_stated_in_source": sorted(anchors),
        "anchoring_rev_note": (f"勘误正文自称锚定 {sorted(anchors)}；当前 HEAD = {HEAD}，"
                               f"两者相差 {len(spec_commits)} 个改过 openspec/specs 的 commit，"
                               "故勘误坐标与数值均已过期"),
        "spec_changing_commits_pin_to_head": spec_commits,
        "a1_effective": errata_a1,
        "a1_withdrawn": withdrawn_a1,
        "a2_effective": errata_a2,
        "a2_e20": {
            "errata_count": 1,
            "expressed_as_observation_rows": errata_a2_e20,
            "counting_note": ("E20 是 1 条勘误，用 5 行观测表表达。按行数计会把勘误总数"
                              "从 20 虚增到 24。"),
        },
        "a2_total_errata": len(errata_a2) + 1,
    },
    "blindspots": blindspots,
    "other_sections": other_sections,
    "self_check_problems": problems,
}

(EV / "errata_index.json").write_text(
    json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"### headings          : {len(h3)}  = {len(findings)} AC-/UD- + {len(section_headings)} section")
print(f"errata A-1 effective  : {len(errata_a1)}  withdrawn: {len(withdrawn_a1)}")
print(f"errata A-2 E1-E19     : {len(errata_a2)}   E20: {len(errata_a2_e20)}")
print(f"blind spots           : {len(blindspots)}   other sections: {len(other_sections)}")
print(f"anchoring revs seen   : {sorted(anchors)}   HEAD now: {HEAD}")
print(f"spec-changing commits : {len(spec_commits)}")
print()
print("9 unregistered findings -> bucket (D9):")
for u in unregistered:
    print(f"  {u['ac_id']:<12} {u['bucket']:<4} {u['upstream_id']}")
print()
print(f"self-check: {'OK' if not problems else problems}")
print(f"wrote evidence/errata_index.json ({(EV / 'errata_index.json').stat().st_size} B)")
sys.exit(1 if problems else 0)
