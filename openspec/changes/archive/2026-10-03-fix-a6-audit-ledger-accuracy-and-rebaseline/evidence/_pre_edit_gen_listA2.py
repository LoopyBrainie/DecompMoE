# -*- coding: utf-8 -*-
"""Generate lists/opsx-changes.md (清单 A) from _work/classified.json.
Pure transport: no new findings, no re-computation, no fix proposals."""
import json, io, os, collections

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(BASE, "..", "lists", "opsx-changes.md"))

d = json.load(io.open(os.path.join(BASE, "classified.json"), encoding="utf-8"))
items = {it["bucket_id"]: it for b in ("opsx-change", "user-decision") for it in d[b]}
order = [it["bucket_id"] for b in ("opsx-change", "user-decision") for it in d[b]]

# ---- problem-field de-contamination (check-contamination.json: AC-06, AC-29 borderline) ----
OVERRIDE = {
    "AC-06": (
        "裁决基线是 pin 6593a06，但 HEAD 188b9fb 已多出 9 个 commit。报告在 HEAD 上复测："
        "skeleton req-6 现在写「G is STRICTLY CONVEX on the whole of (0,π/2) … so G'' has NO interior zero」"
        "并附闭式，凸性边界测试已被 `test_voronoi_angle_precondition_is_area_below_half` 取代并把三个退役值转为反向回归钉"
        "——这是正确处置；但 `_betainc_regularized` 仍是单个 8 点 GL 面板零细分，`_cap_area` 的 π/2 跳变与 pin 逐位相同。"
        "结论是「不能因为凸性已修好就认为整条链已闭合」。本条的复测时点因此是 HEAD 而非 pin，其自身结论也不外推到 pin 态。"
    ),
    "AC-29": (
        "D3 明确记录其支撑线证明在 `μ=0.5, d_c=3` 处失败，因此只反驳 spec 给出的理由、不声称定理本身错误。"
        "报告采信「正确前置条件是面积条件」这一条（`G⁻¹` 在 `(0, ½)` 上凹 + 等面积 `A_i = 1/N_e < ½`），"
        "但明确不声称已独立证明该界对任意 `A_i < ½` 的 cell 组成立。"
        "本条的结论边界因此是：被证伪的是 spec 给出的理由陈述，不是 Jensen 单向界本身——两者是不同命题。"
    ),
}

# ---- per-item cross-check annotations ----
ANNOT = {
    "AC-23": "**[口径冲突]** 报告 §2.2 L56 判 main3 为 NEVER_EXISTED、§3.1 L318 判 STILL_REAL / MAJOR、"
             "§10 Batch D-2 L1641 明写「不入批」；本条采纳的是 §3.1 口径，三处裁定前该条的去留待定。",
    "AC-27": "**[基线存疑]** 本条 `baseline_status` 记 `touched-since-pin`，但 `openspec/specs/decompmoe-skeleton/spec.md:122` "
             "不落在该文件任何 drift 区间内（该文件区间为 [98,98] [132,132] [255,255] [270,271] [326,329] [340,340] "
             "[499,499] [501,501] [524,524]）；机械查表应为 `unchanged-since-pin`。以查表结果为准。",
    "AC-29": "**[分桶存疑]** 报告 §11 第 4 条是「D3 未能证明 Jensen 单向界本身」的弃权声明，"
             "check-completeness 判其应落 archive-only；Jensen 问题的可执行部分已由 AC-48（C-065）独立承载。",
    "AC-30": "**[分桶存疑 + 溯源存疑]** 报告 §11 第 5 条是「结论保留、证据废弃」声明，check-completeness 判其应落 archive-only；"
             "另本条 `origin_ids` 记 `rv:main20:math`，而其内容是 gap0，真实键为 `rv:gap0:math` / `rv:gap0:source`（见 AC-17）。",
    "AC-50": "**[分桶存疑 + 溯源存疑]** 报告 §11 第 6 条是「main42 的结论反转被明确驳回」，check-completeness 判其应落 archive-only；"
             "main42 的可执行部分已由 AC-52（W02）承载。本条 `origin_ids` 记 `rv:main18:source` / `rv:main17:source`，不含 `rv:main42:*`，指向与标题不符。",
    "AC-51": "**[分桶存疑]** 报告 §11 第 7 条是「main21/main22 的 violates 归因被三镜一致驳回」，check-completeness 判其应落 archive-only。",
    "AC-28": "**[边界保留]** check-completeness 将本条列为 borderline：内容本身是 spec 措辞需精确化项，"
             "与 AC-04 / AC-05 同一 locus，保留为行动项合理。",
    "AC-06": "**[已净化]** 原 problem 末句为祈使句（「所有 verdict 的时点必须随 pin 标注。」），"
             "check-contamination 判为 borderline 污染，此处已改写为纯时点陈述。",
    "AC-04": "**[溯源缺口]** 报告 §3 的 D1-03（req-6 凸性三条断言两条为假）、D1-04（Jensen 前置条件用了不存在的 `theta_conv`）、"
             "D3-02（spec L98 凹性数值是伪影）三条的实体都在本条，但三个 id 均未进入本条 `origin_ids`。",
    "AC-15": "**[溯源缺口]** 报告 §3 的 D1-03（req-6 凸性三条断言两条为假）由本条与 AC-04 / AC-28 共同承载，id 未进 `origin_ids`。",
    "AC-28": "**[溯源缺口]** 报告 §3 的 D1-03 由本条与 AC-04 / AC-15 共同承载，id 未进 `origin_ids`。",
    "AC-16": "**[溯源缺口]** 报告 §3 的 D1-05（`_cap_area` 在 π/2 的硬不连续）由本条承载，id 未进 `origin_ids`。",
    "AC-18": "**[溯源缺口]** 报告 §3 的 D1-05 由本条承载，id 未进 `origin_ids`。",
    "AC-48": "**[溯源缺口]** 报告 §3 的 D1-04（Jensen 前向界的前置条件用了不存在的角度阈值 `theta_conv`）由本条与 AC-04 / AC-29 共同承载，id 未进 `origin_ids`。",
    "AC-29": "**[溯源缺口]** 报告 §3 的 D1-04 由本条与 AC-04 / AC-48 共同承载，id 未进 `origin_ids`。",
    "AC-05": "**[溯源缺口]** 报告 §3 的 D3-03（凸性边界测试钉死求积伪影）即本条，id 未进 `origin_ids`。",
    "AC-10": "**[同实体未合并]** 本条与 AC-33（W11）、AC-41（C-026）指向同一 UR 闭式缺口的三面，"
             "`location_file` 同为 `tests/test_metrics.py:65` / `src/decompmoe/metrics.py:73`；classified.json 的合并规则要求同实体 + 同 location_file，"
             "本轮未合并。报告 §3 的 main37 由这三条共同承载。",
    "AC-33": "**[同实体未合并]** 见 AC-10。",
    "AC-41": "**[同实体未合并]** 见 AC-10。",
    "AC-58": "**[溯源缺口]** 报告 §3 的 main41（skeleton req-21 三处过期 wayfinder 行号）即本条，id 未进 `origin_ids`。",
}

THEMES = [
    ("A-1", "数值守卫缺口：spec 声明了数学闭式或不变量，tests/ 无原理级断言",
     "落点是「spec 声称的数学」与「测试实际断言的东西」之间的落差。修不修得动取决于 spec 侧是否把该闭式写成可验条款，"
     "因此属于 change 层而不是单纯的测试补强。"),
    ("A-2", "spec / 文档层的数学陈述与条款措辞缺陷",
     "缺陷就在 `openspec/specs/**` 的正文或源码 docstring 自身——它陈述了错误的数学，或写成了不构成可验条款的散文。"
     "spec 是唯一真相源，这类条目只能经 OpenSpec change 修订，不能在代码层绕过。"),
    ("A-3", "spec 与 src 实现之间的语义偏离",
     "实现做了 spec 没要求的、或没做 spec 要求的、或两者对同一个量的语义理解不同。归属 change 层是因为处置方向取决于"
     "spec 侧的契约要不要保留，代码层的「直接对齐」可能是错的。"),
    ("A-4", "交叉引用与行号指针失效",
     "spec / src / tests 三层互相用行号和逐字引文指向真相源，而指针已漂移。真相源不可被指针反向定义，"
     "所以修的是引用关系与反链约束，不是被指向的那一行本身。"),
    ("A-5", "OpenSpec 制品格式、门禁与归档流程",
     "落点是 change 制品（proposal / tasks / delta / 目录名 / 勾选账目）、anchor 声明机制或 `scripts/` 下的门禁脚本。"
     "这层的问题不体现为某个 Requirement 的数学对错，而体现为「真相源能不能被可靠地写下去和查出来」。"),
    ("A-6", "裁决口径、镜像分歧与先例争议",
     "落点是审计结论本身：verdict_class、裁决时点、镜像分歧、证据可复用性。这些不进代码，但必须与结论一起搬运，"
     "否则下游会重犯同一类误判。它们被放在本清单是因为它们改变的是 change 的输入（哪些 finding 可信），而不是因为要改代码。"),
    ("A-7", "wayfinder advisory 层（map.md / tickets）漂移",
     "按 `CLAUDE.md` §8，map.md 与 23 张 ticket 为参考性非约束性；但它们经 OpenSpec 制品的反链与逐字引用进入真相源的表述链，"
     "stale 值可沿三条通道传染到 `src/` 与 tests。故仍走 change（ticket 端标注 + spec 端对齐），而不走直接改代码。"),
    ("A-8", "需用户裁决（user-decision 桶）",
     "问题已定位、数学与逻辑依据已清楚，但「这条规则到底要什么」本身是未定的语义选择。"
     "任何自动处置都等于替用户做决定，故本清单只登记问题，不推进。"),
]

ASSIGN = {
    # A-1
    "AC-01": "A-1", "AC-02": "A-1", "AC-03": "A-1", "AC-07": "A-1", "AC-08": "A-1", "AC-09": "A-1",
    "AC-10": "A-1", "AC-11": "A-1", "AC-12": "A-1", "AC-13": "A-1", "AC-18": "A-1", "AC-33": "A-1",
    "AC-37": "A-1", "AC-38": "A-1", "AC-39": "A-1", "AC-40": "A-1", "AC-47": "A-1", "AC-48": "A-1",
    "AC-60": "A-1", "AC-61": "A-1", "AC-62": "A-1", "AC-77": "A-1", "AC-83": "A-1", "AC-91": "A-1",
    # A-2
    "AC-04": "A-2", "AC-05": "A-2", "AC-15": "A-2", "AC-16": "A-2", "AC-28": "A-2", "AC-42": "A-2",
    "AC-46": "A-2", "AC-52": "A-2", "AC-53": "A-2", "AC-64": "A-2", "AC-82": "A-2", "AC-84": "A-2",
    "AC-85": "A-2", "AC-86": "A-2", "AC-87": "A-2",
    # A-3
    "AC-14": "A-3", "AC-17": "A-3", "AC-32": "A-3", "AC-35": "A-3", "AC-41": "A-3", "AC-43": "A-3",
    "AC-44": "A-3", "AC-45": "A-3", "AC-56": "A-3", "AC-73": "A-3", "AC-74": "A-3", "AC-75": "A-3",
    "AC-76": "A-3", "AC-78": "A-3", "AC-79": "A-3",
    # A-4
    "AC-34": "A-4", "AC-54": "A-4", "AC-59": "A-4", "AC-63": "A-4", "AC-65": "A-4", "AC-66": "A-4",
    "AC-67": "A-4", "AC-68": "A-4", "AC-69": "A-4", "AC-70": "A-4", "AC-71": "A-4", "AC-72": "A-4",
    "AC-88": "A-4", "AC-89": "A-4", "AC-90": "A-4",
    # A-5
    "AC-19": "A-5", "AC-20": "A-5", "AC-21": "A-5", "AC-22": "A-5", "AC-23": "A-5", "AC-24": "A-5",
    "AC-25": "A-5", "AC-31": "A-5", "AC-36": "A-5", "AC-49": "A-5", "AC-57": "A-5", "AC-58": "A-5",
    "AC-80": "A-5", "AC-81": "A-5", "AC-92": "A-5", "AC-100": "A-5", "AC-101": "A-5", "AC-102": "A-5",
    # A-6
    "AC-06": "A-6", "AC-26": "A-6", "AC-27": "A-6", "AC-29": "A-6", "AC-30": "A-6", "AC-50": "A-6",
    "AC-51": "A-6",
    # A-7
    "AC-55": "A-7", "AC-93": "A-7", "AC-94": "A-7", "AC-95": "A-7", "AC-96": "A-7", "AC-97": "A-7",
    "AC-98": "A-7", "AC-99": "A-7",
}
for b in ("UD-01", "UD-02", "UD-03", "UD-04", "UD-05", "UD-06"):
    ASSIGN[b] = "A-8"

missing = [k for k in order if k not in ASSIGN]
assert not missing, missing
theme_by_id = {t[0]: t for t in THEMES}

# ---------------------------------------------------------------- header
L = []
w = L.append

w("# 清单 A：需走 OpenSpec change 的条目")
w("")
w("> 审计基线：pinned commit `6593a06`。本文件所有 `file:line` 均为 **pin 态行号**。")
w("> 源数据：`_work/classified.json` 的 `opsx-change`（102 条）与 `user-decision`（6 条）两个桶，共 108 条，本轮原样搬运，未重排 verdict、未重判严重性、未重算任何数学。")
w("> 本轮性质：**纯整理**。不含任何新发现。")
w("> 交叉核查来源：`_work/check-completeness.json`（完整性 / 分桶冲突 / 基线重算）、`_work/check-contamination.json`（方案污染扫描）。")
w("> 审计材料：`_final_report_full.md`（§1 L11 / §2 L23 / §3 L76 / §4 L1255 / §5 L1379 / §6 L1412 / §7 L1511 / §8 L1537 / §9 L1565 / §10 L1606 / §11 L1647）、")
w("> `_handoff_verdicts_all.json`（197 条 lens 裁决）、`_handoff_delta.json`（27 条 delta）、`_handoff_mutations.json`（8 组变异）、`_handoff_pin.json`（7 条 pin 基线）。")
w("")
w("---")
w("")
w("## 本文件的读法")
w("")
w("这一层的条目意味着：**问题的处置对象是 `openspec/specs/**` 里的真相源本身，或者它的解法取决于真相源写什么。**")
w("按 `CLAUDE.md` §2 的真相源优先级与 §3 的工作流约定，想改 DecompMoE 行为先改 spec、不直接动代码；")
w("反过来，**当缺陷落在 spec 的措辞、契约、交叉引用、change 制品或门禁流程上时，改代码就改不对**——")
w("代码只是把 spec 的错误语义固化了一遍。清单 A 就是这类条目的集合。")
w("")
w("它分成 8 个主题（A-1 ~ A-8），归属判据是**问题落在哪一层**，不是难易：")
w("")
for tid, tname, trate in THEMES:
    w("- **%s %s** —— %s" % (tid, tname, trate.split("。")[0] + "。"))
w("")
w("### 基线状态字段怎么读")
w("")
w("每条的 `基线` 是**机械查表**的结果，来自 `_pin_drift.json`（`git diff 6593a06..188b9fb` 的 hunk 行区间），")
w("只回答一个问题：**pin 之后这个文件的这一段行被动过没有。**")
w("")
w("- `unchanged-since-pin` = 该行区间不在任何 hunk 内。")
w("- `touched-since-pin` = 该行落在某个 hunk 内。")
w("")
w("**它不回答「问题是否已修复」或「问题是否仍存在」。** 本文件 108 条中 10 条记 `touched-since-pin`、98 条记 `unchanged-since-pin`，")
w("这只说明它们的位置在 pin 之后是否漂移，**不构成任何一条仍然成立的断言**。要判断现状必须回到 HEAD 重新定位。")
w("")
w("两条口径提醒：")
w("")
w("1. `_pin_drift.json` 的生成脚本未记录区间取的是 pin 侧还是 HEAD 侧坐标。classified.json 全表 193 条里 191 条在 pin 坐标下自洽，")
w("   故以 pin 坐标为工作假设；若口径相反，个别条目的 touched/unchanged 判定会翻转。")
w("2. 本文件对 108 条全部重算了一遍，**发现 1 条与记录不符（AC-27）**，已在该条下标注并以查表结果为准。")
w("")
w("### 与清单 B 的边界")
w("")
w("**user-decision 桶（UD-01 ~ UD-06）同时被清单 B（`lists/direct-fixes.md`）收录。**")
w("上游 classified.json 把这 6 条归入 user-decision，而本轮两份清单的取数范围在这一桶上重叠。")
w("本文件保留这 6 条（`§A-8`）是为不丢信息；**以哪一份为准由整理轮的组织者裁定**，本轮不替其决定。")
w("另有两条例外关系需要登记：")
w("")
w("- 清单 B 的 **DF-08**（main18：spec 浮点闭式 claim `~0.83%` 在 tests/ 全目录无 `pytest.approx` 对账，locus `openspec/specs/wayfinder/spec.md:382`）")
w("  按 classified.json 自己写下的分桶规则应落本清单 A-2，却落在清单 B。同 locus 的 **AC-52**（W02）在本清单。")
w("- 清单 B 的 **DF-09**（main13：`.gitignore:37` 对 wayfinder spec 重复副本的威胁）被报告 §10 Batch D-2 列进 opensx change 批次，")
w("  但 classified 落 direct-fix；按该批次执行时该条会漏。")
w("- **UD-04**（W44：CLAUDE.md 对 ticket 既声明非约束又要求维护）与本清单 A-7 的 7 条 map.md / ticket 漂移条目共享同一批 finding id，")
w("  会被两份清单分别计数。")
w("")
w("### 交叉核查角标的读法")
w("")
w("正文里出现的方括号角标来自两份交叉核查结果，**不是新发现**，只是把上游已知问题挂到对应条目上：")
w("")
w("- `[口径冲突]` —— 报告自身对同一 finding 给出互相矛盾的三处判断，裁定前该条去留待定。")
w("- `[分桶存疑]` —— check-completeness 判定该条实际应落 archive-only（它们是「证据不足 / 复验驳回」声明，不是行动项）。")
w("- `[基线存疑]` —— 记录的 `baseline_status` 与 `_pin_drift.json` 机械查表结果不符。")
w("- `[溯源存疑]` / `[溯源缺口]` —— `origin_ids` 指向与内容不符，或报告 §3 的 finding id 未进入该条溯源。")
w("- `[同实体未合并]` —— 两条指向同一实体的不同侧面，上游合并规则要求同实体 + 同 `location_file` 才合并，本轮未合并。")
w("- `[规则越界]` —— 该条按上游自己的分桶规则应在本清单，却落到了清单 B。")
w("- `[边界保留]` —— 交叉核查判为 borderline 但结论是保留。")
w("- `[已净化]` —— 原 problem 含祈使句，已改写为纯问题分析（详见「交叉核查」第 2 条）。")
w("")
w("### 关于「不含修复方案」")
w("")
w("本文件只写：位置、问题是什么、为什么是问题（数学或逻辑依据）、证据出处、严重性、归属理由。")
w("条目里出现的真值与真位置（例如「真 G'' 在 θ=82.6036° 处为 +2.4568，而 pin 实现中心差分给 +9.9920e-06」）是数学与逻辑依据，")
w("用来证明原值错在哪，删掉读者就无法复核，故保留；它们不是修法提案。")
w("上游 schema 层面已无 `suggested_fix` 字段可承载方案，三反引号代码块在 193 条上命中 0 次。")
w("")
w("---")
w("")
w("## 分类概览")
w("")
cnt = collections.Counter(ASSIGN[k] for k in order)
sev = collections.Counter(items[k]["severity"] for k in order)
w("| 主题 | 条目数 | CRITICAL | MAJOR | MEDIUM | MINOR |")
w("|---|---|---|---|---|---|")
for tid, tname, _ in THEMES:
    ks = [k for k in order if ASSIGN[k] == tid]
    c = collections.Counter(items[k]["severity"] for k in ks)
    w("| **%s** %s | %d | %d | %d | %d | %d |" % (tid, tname, len(ks), c["CRITICAL"], c["MAJOR"], c["MEDIUM"], c["MINOR"]))
w("| **合计** | %d | %d | %d | %d | %d |" % (len(order), sev["CRITICAL"], sev["MAJOR"], sev["MEDIUM"], sev["MINOR"]))
w("")
bl = collections.Counter(items[k]["baseline_status"] for k in order)
vc = collections.Counter(items[k]["verdict_class"] for k in order)
w("- 裁决分布：" + "、".join("%s %d" % (k, v) for k, v in vc.most_common()))
w("- 基线分布：" + "、".join("`%s` %d" % (k, v) for k, v in bl.most_common()))
w("")

# ---------------------------------------------------------------- body
for tid, tname, trate in THEMES:
    ks = [k for k in order if ASSIGN[k] == tid]
    w("---")
    w("")
    w("## %s %s（%d 条）" % (tid, tname, len(ks)))
    w("")
    w(trate)
    w("")
    for k in ks:
        it = items[k]
        prob = OVERRIDE.get(k, it["problem"])
        lf = it["location_file"]
        ln = it["location_line"]
        w("### %s — %s" % (k, it["title"]))
        w("")
        w("- **源 id**：`%s` ｜ **主桶**：%s ｜ **裁决**：%s ｜ **严重性**：%s" % (
            it["id"], it["classification_hint"], it["verdict_class"], it["severity"]))
        if ln and ln > 0:
            w("- **位置**：`%s:%d`（pin 态）" % (lf, ln))
        else:
            w("- **位置**：`%s`（pin 态 line=0，目录级/模块级定位，无有效行号）" % lf)
        w("- **Requirement**：%s" % it["requirement_ref"])
        w("- **溯源 id**（`origin_ids`）：%s" % ("、".join("`%s`" % x for x in it["origin_ids"]) if it["origin_ids"] else "（空数组）"))
        w("- **问题**：%s" % prob)
        w("- **证据**：%s" % it["evidence_ref"])
        w("- **基线**：`%s`" % it["baseline_status"])
        w("- **归属理由**：%s" % trate.split("。")[0] + "。")
        if k in ANNOT:
            w("- **交叉核查**：%s" % ANNOT[k])
        w("")

# ---------------------------------------------------------------- cross-check
w("---")
w("")
w("## 交叉核查")
w("")
w("本节把 `check-completeness.json` 与 `check-contamination.json` 指向本桶的 issues 原样登记，不重判。")
w("")
w("### 1. 分桶冲突（上游报告自身 / 上游规则不一致）")
w("")
w("| # | 条目 | 冲突 | 状态 |")
w("|---|---|---|---|")
w("| 1 | AC-23（O-10，main3） | 报告 §2.2 L56 判 NEVER_EXISTED（该 change 目录在 pin 态不存在）、§3.1 L318 判 STILL_REAL / MAJOR、"
  "§10 Batch D-2 L1641 明写「不入批」。classified.json 采纳 §3.1。 | **待裁定**，未消解 |")
w("| 2 | DF-08（main18，不在本桶） | 同一 locus `openspec/specs/wayfinder/spec.md:382`：AC-52（W02）在本桶，DF-08 落 direct-fix，"
  "违反 classified 自订规则「凡涉及 spec / governance spec / ticket annotation / change 制品 / archive 流程 / 门禁脚本的取 opsx-change」。 | **待改桶或登记为例外** |")
w("| 3 | UD-04（W44） | 同一实体同时支撑 user-decision（UD-04）与 A-7 的 7 条 map.md / ticket 漂移条目，跨桶共享 6 个 finding id，会被两份清单分别计数。 | **待收窄 `origin_ids` 或登记双桶归属** |")
w("| 4 | AC-10 / AC-33 / AC-41 | 同一 UR 闭式缺口被拆成三条；上游合并规则要求同实体 + 同 `location_file`，本轮未合并。 | **待合并或明确分列理由** |")
w("| 5 | AC-27（V-18） | 记录的 `baseline_status=touched-since-pin` 与机械查表结果（`unchanged-since-pin`）不符。 | **本文件以查表为准** |")
w("")
w("### 2. 方案污染处置（`check-contamination.json`）")
w("")
w("上游 193 条中 1 条判污染、7 条判 borderline。落到本桶的只有 2 条 borderline，均为**对审计记录本身的祈使/处置措辞**，不针对被审缺陷：")
w("")
w("- **AC-06**（V-34）原句「所有 verdict 的时点必须随 pin 标注。」——已改写为「本条的复测时点因此是 HEAD 而非 pin，其自身结论也不外推到 pin 态。」")
w("- **AC-29**（V-27）原句「归档时把「spec 理由错」写成「Jensen 界错」是越界。」——已改写为「本条的结论边界因此是：被证伪的是 spec 给出的理由陈述，不是 Jensen 单向界本身——两者是不同命题。」")
w("")
w("污染最重的一条（archive-only AO-31 / P20，带环境变量名的重跑补救）不在本桶。")
w("另需注意边界：`check-contamination` 明确把「零断言 / 缺对账 / 零覆盖」判为问题陈述而非修法提案，把「真值与真位置」判为数学依据，")
w("本文件两类都原样保留。")
w("")
w("### 3. 分桶存疑（`check-completeness.json` §11 misplacement）")
w("")
w("报告 §11 实际有 **15 条**编号项（不是任务文本说的 12 条）。其中 4 条被 classified 放进 opsx-change，但它们是")
w("**「证据不足 / 复验驳回」的声明**而非可执行行动项，check-completeness 判其应落 archive-only：")
w("")
w("| 条目 | 报告 §11 项 | 上游记的严重性 | 问题 |")
w("|---|---|---|---|")
w("| AC-29（V-27） | 第 4 条 | MAJOR | D3 未能证明 Jensen 单向界本身；可执行部分已由 AC-44 承载 |")
w("| AC-30（V-28） | 第 5 条 | MAJOR | gap0 结论成立但 finding 自身证据不可复用；`origin_ids` 另指错（`rv:main20:math` 应为 `rv:gap0:*`） |")
w("| AC-50（V-29） | 第 6 条 | MEDIUM | main42 的「结论反转」被明确驳回；`origin_ids` 另指错（不含 `rv:main42:*`） |")
w("| AC-51（V-30） | 第 7 条 | MEDIUM | main21 / main22 的 violates 归因被三镜一致驳回 |")
w("")
w("**这 4 条带 MAJOR / MEDIUM 定级留在本清单，有被当成行动项执行的风险。**本轮不删不迁，仅标注。")
w("")
w("### 4. 溯源缺口（报告 §3 finding id 未进入 `origin_ids`）")
w("")
w("7 条 §3 finding 的**实体在本桶内，但 id 未进 `origin_ids`**，导致按 id 查表会误判为「未覆盖」：")
w("")
w("| 报告 §3 id | 承载条目 | 主题 |")
w("|---|---|---|")
w("| D1-03 | AC-04 / AC-15 / AC-28 | A-2 |")
w("| D1-04 | AC-04 / AC-29 / AC-48 | A-2 / A-6 / A-1 |")
w("| D1-05 | AC-16 / AC-18 | A-2 / A-1 |")
w("| D3-02 | AC-04 | A-2 |")
w("| D3-03 | AC-05 | A-2 |")
w("| main37 | AC-10 / AC-33 / AC-41 | A-1 / A-1 / A-3 |")
w("| main41 | AC-58 | A-5 |")
w("")
w("### 5. 内容准确性标记（`check-completeness.json` content_accuracy_flags，落在本桶者）")
w("")
w("- **AC-30**：`origin_ids` 记 `rv:main20:math`，内容是 gap0，真实键为 `rv:gap0:math` / `rv:gap0:source`（见 AC-17）。")
w("- **AC-50**：`origin_ids` 记 `rv:main18:source` / `rv:main17:source`，标题说的是 main42，真实键为 `rv:main42:*`。")
w("- 另 4 条 flag 落在其他桶（archive-only C-028、direct-fix V-36 / P19、报告自身），不在本文件范围。")
w("- 报告自身另有一处计数笔误：§2.2 L60 写「其余 4 条」却列出 7 个 id（gap9 / gap11 / main14 / main35 / main2 / main5 / main8）。本轮不展开，仅记录。")
w("")

# ---------------------------------------------------------------- blind spots
w("---")
w("")
w("## 本文件的盲区")
w("")
w("### 盲区 1：9 条 §3 finding 在 classified.json 里完全没有实体（最严重）")
w("")
w("`check-completeness.json` 报 105/123 覆盖，18 条无落点，其中 9 条是**实体完全不存在**，不是本文件漏搬：")
w("")
w("| 报告 §3 id | 内容 | 最近的本桶条目 |")
w("|---|---|---|")
w("| **D1-02** | `_betainc_regularized` 用单个 8 点 Gauss–Legendre 面板、零细分；b=1/2 的平方根奇点使误差随 x=sin²θ→1 爆炸，MVP 工作点 67.24° 已越过 CF 对称性阈值 x*=0.85，89° 处相对误差 1.1e-1。报告 §4 环 1 判其为整条 Voronoi 数值主线的根因，§10 Batch A 列为首条。 | AC-09（C-006）同 locus `src/decompmoe/sphere.py:67`，但只谈守卫强度与 2/13 覆盖 |")
w("| **D1-07** | governance req-gov-1 §4 把 impl-internal frame（单个 8 点 GL 面板、无细分 + 逐位二分输出 1.1735482746999482 / 1.0205068335735599）钉成规范；积分器一旦正确，该 frame 与配套免责文本同时作废。 | 无（AC-62 / C-019 是同一 Requirement 的 obligation 4 零对账，不同问题） |")
w("| **D2-02 + gap4** | `voronoi_angle` 的 MC 容差 σ 建立在「各 cell 面积独立」这一可证伪的假设上；实际 cell 计数服从多项分布且 ΣA_i≡1，一阶 delta-method 方差相消。5σ=0.0355° 比实测 SE 大 10×（随机 16 站点）到 228×（crosspolytope）。 | AC-40（C-020）只谈采样数 / 种子常量零断言 |")
w("| **D2-05** | skeleton req-6 与 governance req-gov-1 Scenario 声称的三个实测 gap「6.5e-5 deg / 1.0e-4 deg / 0.0 deg」有两个错，第三个对采样估计量在原理上不可能；真值约 6.456e-5 / 2.481e-5 / 2.261e-5 deg。 | 无 |")
w("| **D3-01** | `canonical_voronoi_angle` 的反射分支被宣称为 totality 所必需且 `_cap_radius` 被 docstring 描述为 [0,1] 上的逆；实测 N_e=3 / d_c=16 下公开 API 返回 84.4738°，真值 83.4100°，误差为估计量 5σ 的 30 倍，[0.40,0.60] 的 2001 点采样中 1575 点不满足往返闭合。 | AC-16（只谈免责声明挂错侧）、AC-18（只谈测试不敏感），未覆盖公开 API 可达的超差输出本身 |")
w("| **main36** | wayfinder Req 23 整条 Requirement 由行号断言构成，实指 skeleton req-22 而非 req-23；报告 §3.1 判 STILL_REAL / 校准 MEDIUM，§10 Batch D-1 明确列入。 | 无。`rv:main36:math` 只作为 AC-29（V-03 的 12 个弃权键之一）出现 |")
w("| **main38** | skeleton Req 7 的 `‖C_t‖₂ = 1 for every token (within 1e-5)` 是无条件断言，与 Req 19 自己明文规定的 `0 < ‖z‖₂ < ε` 次单位范数区直接矛盾，且无测试走该分支。 | AC-46（C-060，同族但是 exact vs approx 表述的另一个问题） |")
w("| **main73** | wayfinder req-23 对 skeleton 的交叉引用全部写成行号且 Requirement 号错（req-23 实为 req-22）。 | A-4 的 AC-70 / AC-71 / AC-90 是不同 Requirement 的行号漂移 |")
w("| **main78** | governance req-gov-3 称 cycle-5 ticket 的 θ_Voronoi 52°→67.24° supersede 由「spec req-1 L184-L185」承载，但 wayfinder req-1 是 Naming And Alias Convention（L8-L18），L184 是空行、L185 落在 req-9 块内。 | 无 |")
w("")
w("**这 9 条里 main36 / main38 / main73 / main78 是 §3 判仍成立、§10 已入批的 spec 缺陷，但 classified.json 里没有落点。**")
w("D1-02 尤其关键：它是报告 §10 Batch A 的首条 finding，也是 A-1 / A-2 里 Voronoi 数值主线的根因，")
w("却只能靠 AC-09 的「2/13 覆盖」侧面读到，实体本身没被登记。**本文件不补写**（本轮是纯整理，不做新发现），此处只点名。")
w("")
w("### 盲区 2：AC-29 的结论边界")
w("")
w("AC-29（V-27）在本清单里以 MAJOR 出现，但它承载的是**「D3 未能证明 Jensen 单向界本身」这一弃权声明**。")
w("被证伪的是 spec 给出的理由陈述（用了不存在的 `theta_conv` 阈值），不是 Jensen 单向界。")
w("Jensen 问题的可执行部分是 AC-48（`test_voronoi_angle_one_sided_gap` 把单向性降格为方向检查）与 AC-18（反射分支测试声称守护该分支却通过）。")
w("读 AC-29 时不能读成「Jensen 界已证伪」。")
w("")
w("### 盲区 3：AC-06 是 HEAD 时点结论")
w("")
w("AC-06（V-34）自陈「裁决基线是 pin 6593a06，但 HEAD 188b9fb 已多出 9 个 commit」，其复测在 HEAD 上做。")
w("它同时是 A-6 里唯一的 `MOVED` + CRITICAL 条目，描述 e50cc02 已切断环 4→环 6 而环 1 / 环 2 未修。")
w("**这一条的坐标是 HEAD 的，不是 pin 的**——是 108 条里唯一打破本文件「file:line 一律 pin 态」通例的条目。")
w("")
w("### 盲区 4：4 条 §11 声明留在本清单")
w("")
w("AC-29 / AC-30 / AC-50 / AC-51 是「证据不足 / 复验驳回」声明，check-completeness 判其应落 archive-only（见「交叉核查」第 3 条）。")
w("本轮按「不删不迁」原则保留并标注，但**执行本清单时这 4 条不应被当作待修复项**。")
w("")
w("### 盲区 5：本文件未做的事")
w("")
w("- **未重算任何数学。** 所有真值、误差量级、σ 倍数都原样取自上游，未复核。")
w("- **未在 HEAD 上重新定位。** 所有 `file:line` 是 pin 态；`touched-since-pin` 的 10 条（AC-04 / AC-05 / AC-06 / AC-26 / AC-27 / AC-28 / AC-40 / AC-60 / AC-64 / AC-79）"
  " 位置已漂移，正文里的行内引用需回 pin 态读。")
w("- **未核对报告内部一致性。** 只搬运了 `check-completeness` 已经点出的矛盾（main3 三处口径、§2.2 L60 计数笔误），没有自查报告其余部分。")
w("- **未补 D1-02 / D2-02 / D3-01 等 9 条缺失实体。** 见盲区 1。")
w("- **未处理与清单 B 的 6 条重叠**（UD-01 ~ UD-06）。见「本文件的读法 · 与清单 B 的边界」。")
w("- **未处理变异副本残留（mut1 / mut4 / mut7）。** 上游拆成 6 条 direct-fix（DF-01 ~ DF-06），是同一实体，占 direct-fix 桶 9 条中的 6 条；"
  "其中 DF-01（P19）的 `origin_ids` 是空数组、DF-05（V-36）的 `origin_ids` 指向三个 test-guard finding 与内容无关。归 B 桶，不在本文件。")
w("- **未处理 P05 / UD-03 的 `origin_ids` 跨桶引用。** 它含 `rv:main45`，而 main45（LIFECYCLE-01）在 A-6 的 AC-26 且被判 FIXED_BY_COMMIT 排除在批外。")
w("")
w("### 盲区 6：本文件的权威边界")
w("")
w("本清单是**既有结论的搬运**，不是审计结论。真相源优先级不变：")
w("`openspec/specs/**/spec.md` > `openspec/changes/archive/` > `wayfinder/map.md` + 23 tickets（advisory）> 代码层。")
w("条目里的 verdict_class 与 severity 是 pin 态的判断，**引用时必须连同 pin 标注一起搬运**。")
w("")

out = "\n".join(L) + "\n"
io.open(OUT, "w", encoding="utf-8", newline="\n").write(out)
print("WROTE", OUT, len(out), "chars,", len(order), "items")
