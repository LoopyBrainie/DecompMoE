# -*- coding: utf-8 -*-
"""Apply the A-6 ledger corrections to _work/classified.json.

Every mutation asserts the CURRENT value first, so a drifted input aborts instead
of silently overwriting something a later round may have changed. Nothing is
rewritten wholesale: text fields that are still valid get a dated append block,
because the audit's value is that it preserves why a verdict was reached.

See ../../../../.audit/.../lists/opsx-changes.md and evidence/rebaseline_diff.md
for the derivation of every claim written here.
"""
import io
import json
import os
import sys

CLASSIFIED = (
    r"D:/myProject/DecompMoE/.audit/wayfinder-opsx-code-review/_work/classified.json"
)
BUCKETS = ("opsx-change", "user-decision")

STAMP = "【2026-10-03 复验】"

# ---------------------------------------------------------------- corrections
# scalar fields: field -> (expected_old, new_value)
SCALAR = {
    "AC-06": {
        "verdict_class": ("MOVED", "FIXED_BY_COMMIT"),
        "severity": ("CRITICAL", "MEDIUM"),
        "location_line": (137, 67),
    },
    "AC-26": {
        "verdict_class": ("STILL_REAL", "FIXED_BY_COMMIT"),
        "location_line": (166, 177),
    },
    "AC-27": {},
    "AC-29": {
        "location_line": (1367, 1336),
    },
    "AC-30": {
        "verdict_class": ("STILL_REAL", "FIXED_BY_COMMIT"),
        "location_file": ("src/decompmoe/schedule.py", "src/decompmoe/extraction.py"),
        "location_line": (0, 90),
    },
    "AC-50": {
        "location_line": (383, 382),
    },
    "AC-51": {},
}

# new keys to add
ADD = {
    "AC-06": {"fixing_commit": "f6461d7"},
    "AC-26": {"fixing_commit": "315065e"},
    "AC-30": {"fixing_commit": "a97e3a7"},
}

# origin_ids: (expected_old, new_value)
ORIGINS = {
    "AC-29": (["rv:main18:math", "rv:main48:math"], ["rv:main48:math"]),
    "AC-30": (["rv:main20:math"], ["grv:gap0:math"]),
    "AC-50": (
        ["rv:main18:source", "rv:main17:source"],
        ["rv:main42:source", "rv:main42:math", "rv:main42:impact", "rv:main17:source"],
    ),
    "AC-51": (["rv:grv:gap25:math", "rv:main22:math"], ["grv:gap25:math", "rv:main22:math"]),
}

# whole replacement of `problem` (the rendered claim itself is now false)
REPLACE_PROBLEM = {
    "AC-06": (
        "裁决基线是 pin 6593a06。本条所指的子缺陷——`_betainc_regularized` 用单个 8 点 GL 面板零细分——"
        "**已由 `f6461d7` 关闭**（已归档 change `2026-10-02-a2-round2-spec-math-fixes`，post-pin）。"
        "冻结 commit `95718cf` 的实现已改为自适应 8/16 点 Gauss–Legendre，双阶一致到 `_QUAD_RTOL`；"
        "其 docstring 的 HISTORY 段**逐字记录了本条引用的 pre-fix 数值**（`8.29e-07`(6.633 ppm) @ MVP 点、"
        "`1.57e-01` @ x→1⁻），即本条描述的是 pin 态而非现状。原结论「不能因为凸性已修好就认为整条链已闭合」"
        "在 pin 态仍然成立（凸性处置正确这点不变：skeleton req-6 的 STRICTLY CONVEX 陈述与闭式、"
        "`test_voronoi_angle_precondition_is_area_below_half` 取代原凸性边界测试、三个退役值转反向回归钉），"
        "但**在冻结 commit 上整条链已闭合**，本条不再指向未修缺陷。"
    ),
}

# dated appends to fields that remain valid
APPEND = {
    "AC-06": {
        "evidence_ref": (
            "pin `src/decompmoe/sphere.py:67` 的 docstring 记「via Gauss–Legendre 8-point」，"
            "即审计所指状态；冻结 commit 的 `src/decompmoe/sphere.py:141` 已为自适应规则。"
            "原证据仍可核：报告 §4 环 8 跳变 5.239884e-2 / 7.870852e-2 / 1.158112e-1（另见报告 L1280-1282 覆盖率表）；"
            "§10 Batch A「不在本批（已被 post-pin e50cc02 处理）」，测试文件行 519-525 落在漂移区间内；"
            "`e50cc02` message 逐字为 `chore(inflight): checkpoint parallel session's in-flight work`。"
        )
    },
    "AC-26": {
        "problem": (
            "本条记录的是一个**误合**，其方法论价值仍需保留。三镜的 verdict 字段实测一致为 `FIXED_BY_COMMIT`"
            "（`fixingCommit=315065e`），合并成 `STILL_REAL` 与源数据不符；合并所依赖的两条事实同样不成立。"
            "(1)「pin 态 `actual=` 计数为 0」——pin `tests/test_loss.py` 实测 **10 处**"
            "（L33/36/74/156/177/180/183/213/234/246），冻结 commit 为 16 处，obligation 5 载体完好。"
            "(2)「`e50cc02` 回退掉 `b272787` 的修复」——`e50cc02` 是 pin 的**后代**（在 `6593a06..95718cf` 内），"
            "无法影响 pin 态；pin 态 blob 与 `b272787:tests/test_loss.py` 逐字节相同（`6ddbdef`），"
            "且 **pin 的父提交同为 `6ddbdef`**，而 `8f50659` 的 blob 是 `7a88c63`、从未出现在 pin 态。"
            "**教训**：镜像分歧必须按 lens 采样时点裁决、不得按 pin 态——`rv:main45:impact` 原文"
            "「HEAD-at-that-moment was byte-identical to the pre-fix blob 8f50659」描述的正是采样时刻，"
            "而它被读成了 pin 态。"
        ),
        "evidence_ref": (
            "pin blob `6593a06:tests/test_loss.py` == `b272787:tests/test_loss.py` == `6ddbdef`，"
            "且 `6593a06~1` 同为 `6ddbdef`；`8f50659:tests/test_loss.py` = `7a88c63`，从未出现在 pin 态。"
            "`rv:main45:{source,math,impact}` 三键 verdict 均为 `FIXED_BY_COMMIT`（`fixingCommit=315065e`）。"
            "原记位置 `tests/test_loss.py:166` 是 `test_lambda_cosine_ramp_phase_3` docstring 的续行，"
            "已改锚到该函数内实际承载 `actual=` 的断言行 pin L177。"
        ),
    },
    "AC-27": {
        "evidence_ref": (
            "`+1/+13/+8` 经 `git diff --numstat` 与真实行数双口径互证**成立**"
            "（33f7cc9 单独为 3/2、14/1、9/1；真实行数 wayfinder 892→893、skeleton 623→636、governance 165→173），"
            "且 `33f7cc9` 是 `7bf77af..6593a06` 内唯一触及三份 spec 的 commit。"
            "`spec.md:122` 是 `@@ -121,0 +122,13 @@` 插入块首行，在 pin→冻结 commit 区间内不属于任何 hunk，"
            "故机械查表为 `unchanged-since-pin`，原记 `touched-since-pin` 已按查表结果更正。"
        )
    },
    "AC-29": {
        "problem": (
            "D3 明确记录其支撑线证明在 `μ=0.5, d_c=3` 处失败，因此只反驳 spec 给出的理由、不声称定理本身错误。"
            "报告采信「正确前置条件是面积条件」这一条（`G⁻¹` 在 `(0, ½)` 上凹 + 等面积 `A_i = 1/N_e < ½`），"
            "但明确不声称已独立证明该界对任意 `A_i < ½` 的 cell 组成立。归档时把「spec 理由错」写成「Jensen 界错」是越界。"
            "本条位置指向**仓库外**的审计报告 `_final_report_full.md`（1676 行，随审计会话变动，不受 pin 约束），"
            "因此「pin 态」标注对本条无对应基准；原记 1367 实为报告「环 7 修复顺序」表的一行，"
            "「诚实边界」段实际在 **L1336**。"
        ),
        "evidence_ref": (
            "`origin_ids` 中的 `rv:main18:math` 在 `_handoff_verdicts_all.json` 的 197 个 key 中**不存在**"
            "（该 finding id 只有 `rv:main18:source`），已删除；`rv:main48:math` 存在。"
            "D3 边界、700+ 配置经验证据与 `-4.0e-12` / `-2.1e-17` 二分噪声均可逐字核。"
        ),
    },
    "AC-30": {
        "problem": (
            "gap0 的 finding 自陈六行数值在其声明的设置下都无法复现；math 镜重算得到更严重的坍缩"
            "（step ~1000 完成而非 5000，Phase-1 结束时的坍缩比报告值严重约 850×），"
            "并推翻了 finding 的 α 序与 frozen-vs-fresh 节奏叙述。缺陷本身仍判成立，"
            "但支撑它的数值证据整体作废，需要用可复现代码重新立项。这是本轮唯一被点名的「结论保留、证据废弃」条目。"
            "**该缺陷已由 `a97e3a7` 关闭**（已归档 change `2026-10-02-a3-resurrection-clone-and-phase0-mask`，post-pin）："
            "冻结 commit 的 `src/decompmoe/extraction.py:104` 中 `mask: Tensor` 为**必填位置参数、无默认值**，"
            "L118 逐字记录「the previous `mask: Tensor | None = None` default…」，L137-141 缺 mask 即抛错。"
            "原记位置 `src/decompmoe/schedule.py` 有误——`CentroidDriver` 类定义在 `src/decompmoe/extraction.py`"
            "（pin L90 / 冻结 commit L98），`schedule.py` 全文仅 1 处散提及。"
        ),
        "evidence_ref": (
            "§8 表第 2 行的五个数值 1.7528 → 4.54e-01 → 3.26e-07 → 2.52e-07 与 +1.000000 仍可逐字核。"
            "`origin_ids` 更正为 `grv:gap0:math`：全库 54 个治理类 key 一律 `grv:` 前缀，"
            "**零个** `rv:grv:` 或 `rv:gap0:`；原记 `rv:main20:math` 的 verdict 是 `UNVERIFIABLE` "
            "且其 finding 是 `territory_collapse`，与 gap0 不是同一条。"
        ),
    },
    "AC-50": {
        "problem": (
            "finding 声称 extract_C 漏算第 (3) 步 128 MACs 会让 req-19 的「0.3% allowance」结论反转。"
            "该推论被 impact 镜与 source 镜一致驳回：该 allowance 在 wayfinder L428 是对着 active-core 分母 33_554_432 定义的，"
            "恢复第 (3) 步后 66_336/33_554_432 = 0.1977%，与原值 0.1968% 一样在界内。"
            "**finding 的 0.436% 有了来源**：`66_336/66_048 − 1 = 0.4361%`——它取的是「相对原值的增幅」，"
            "却去比一个「占 33_554_432 分母的 allowance」，属**量纲错配**；这才是驳回成立的真理由，"
            "比原记「用的是另一个分母」更准确。CLAUDE.md 明确禁止用「结论反转」这类别名关闭数学语义选择，"
            "因此这次驳回是硬约束而非可选裁量。原记位置 `spec.md:383` 是空行，Req 17 正文在 L382（标题 L380）。"
        ),
        "evidence_ref": (
            "`origin_ids` 补入确实存在却未收录的 `rv:main42:{source,math,impact}`（三键 verdict 均 `STILL_REAL`）。"
            "算术复算：`32_896+128+128+16 = 33_168` MACs、`66_336/33_554_432 = 0.197697%`、"
            "原值 `66_048/33_554_432 = 0.196838%`。"
        ),
    },
    "AC-51": {
        "problem": (
            "两条 finding 都以「违反 CLAUDE.md §6 第 8 条」立论，复验认定归因错误：CLAUDE.md 规范的是断言形式而非隐式契约；"
            "`WB` 在仓库里根本没有闭式，`pytest.approx(0.0476)` 只能是常量对自身的同义反复；"
            "main22 的中心断言被 `tests/test_config.py:69` 的 `router_per_layer == 32_896` bare `==` 直接推翻"
            "（原记漏 `tests/` 前缀，与本条「位置」字段自相矛盾，已补全）。"
            "残留缺陷在 spec 措辞层，不构成 CLAUDE.md 违规。"
        ),
        "evidence_ref": (
            "`origin_ids` 更正为 `grv:gap25:math`（真键无 `rv:` 前缀）；其 verdict 是 `UNVERIFIABLE`，"
            "支撑「WB 无闭式」的是该键的 evidence 文本而非 verdict 字段。"
            "pin 态 `grep -rn 0.0476 src tests` 唯一命中 `tests/test_schedule.py:127` 的一处 docstring，"
            "`src/` 0 命中；冻结 commit 唯一命中移至 `tests/test_schedule.py:135`，`src/` 仍 0 命中。"
        ),
    },
}


def main():
    with io.open(CLASSIFIED, encoding="utf-8") as handle:
        data = json.load(handle)

    index = {}
    for bucket in BUCKETS:
        for item in data[bucket]:
            index.setdefault(item.get("bucket_id"), []).append((bucket, item))

    problems = []
    applied = []

    for bid in sorted(set(list(SCALAR) + list(ADD) + list(ORIGINS) + list(APPEND))):
        entries = index.get(bid, [])
        if len(entries) != 1:
            problems.append("%s: expected exactly 1 entry, found %d" % (bid, len(entries)))
            continue
        bucket, item = entries[0]

        for field, (want, new) in SCALAR.get(bid, {}).items():
            got = item.get(field)
            if got != want:
                problems.append("%s.%s: expected %r, found %r" % (bid, field, want, got))
            else:
                item[field] = new
                applied.append("%s.%s %r -> %r" % (bid, field, want, new))

        for field, new in ADD.get(bid, {}).items():
            if field in item:
                problems.append("%s.%s: key already exists" % (bid, field))
            else:
                item[field] = new
                applied.append("%s.%s added = %r" % (bid, field, new))

        if bid in ORIGINS:
            want, new = ORIGINS[bid]
            got = item.get("origin_ids")
            if got != want:
                problems.append("%s.origin_ids: expected %r, found %r" % (bid, want, got))
            else:
                item["origin_ids"] = new
                applied.append("%s.origin_ids %r -> %r" % (bid, want, new))

        for field, text in APPEND.get(bid, {}).items():
            if bid in REPLACE_PROBLEM and field == "problem":
                continue
            current = item.get(field) or ""
            if STAMP in current:
                problems.append("%s.%s: already stamped" % (bid, field))
                continue
            item[field] = current + STAMP + text
            applied.append("%s.%s appended (%d chars)" % (bid, field, len(text)))

        if bid in REPLACE_PROBLEM:
            new_text = REPLACE_PROBLEM[bid]
            if STAMP in (item.get("problem") or ""):
                problems.append("%s.problem: already stamped" % bid)
            else:
                item["problem"] = new_text
                applied.append("%s.problem replaced (%d chars)" % (bid, len(new_text)))

    if problems:
        print("ABORTED -- %d problem(s); classified.json NOT written" % len(problems))
        for line in problems:
            print("  " + line)
        return 1

    with io.open(CLASSIFIED, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=1)
        handle.write("\n")

    # read back and confirm every intended change is on disk
    with io.open(CLASSIFIED, encoding="utf-8") as handle:
        reread = json.load(handle)
    verify_fail = []
    for bid, entries in index.items():
        item = entries[0][1]
        reread_item = None
        for bucket in BUCKETS:
            for candidate in reread[bucket]:
                if candidate.get("bucket_id") == bid:
                    reread_item = candidate
        if reread_item is None:
            verify_fail.append("%s vanished after write" % bid)
            continue
        for field, (_want, new) in SCALAR.get(bid, {}).items():
            if reread_item.get(field) != new:
                verify_fail.append("%s.%s = %r (want %r)" % (
                    bid, field, reread_item.get(field), new))
        for field, new in ADD.get(bid, {}).items():
            if reread_item.get(field) != new:
                verify_fail.append("%s.%s = %r (want %r)" % (
                    bid, field, reread_item.get(field), new))
        if bid in ORIGINS:
            if reread_item.get("origin_ids") != ORIGINS[bid][1]:
                verify_fail.append("%s.origin_ids = %r" % (bid, reread_item.get("origin_ids")))
        for field in APPEND.get(bid, {}):
            if STAMP not in (reread_item.get(field) or ""):
                verify_fail.append("%s.%s lost its stamp" % (bid, field))

    if verify_fail:
        print("READ-BACK FAILED -- %d problem(s)" % len(verify_fail))
        for line in verify_fail:
            print("  " + line)
        return 1

    print("applied %d change(s) and verified read-back:" % len(applied))
    for line in applied:
        print("  " + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
