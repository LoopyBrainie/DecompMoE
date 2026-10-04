# Design

## 1. 为什么必须落到两个地方（产物 + 上游）

`lists/opsx-changes.md` 由 `_work/classified.json` 经 `_work/_gen_listA2.py` 生成。字段的真相在
`classified.json`，`交叉核查` 角标、`位置` 渲染、附录文案则硬编码在生成器里。

只改 `.md` 的话，下一次重生成会把已知错误值原样写回；只改上游的话，读者看到的仍是错的。
因此两条都改，并用 `evidence/a6_expected.json` + 生成器写出前的断言把「不回退」变成硬失败。

## 2. 顺序：先改位置，再算基线

`基线` 是「该条位置是否落在漂移区间内」的查表结果。AC-30 的原位置 `schedule.py` 解析不到任何行号，
如果先算基线再改位置，那次重算就是基于一个错误位置做的。

实测确认了这一点：第一轮重算把 AC-30 判成 `unverifiable (no pin line)`（因为 `location_line` 是 0）；
改完位置后它变成 `src/decompmoe/extraction.py:90` 并落到 `unchanged-since-pin`。

**故流水线固定为：更正位置 → 重算基线 → 写回**。

## 3. 口径：只加一态，不重定义

审计已明确不重定义 `基线`。所以：

- 判定仍用**旧的 merged `drift` 区间**（`build_pin_drift.py` 的 `drift` 字段与原表逐键相等，保证口径未漂移）。
- 新增的 `inserted` / `modified` 只是**数据视图**，不参与判定。
- 只增加第三态 `unverifiable (no pin line)`，用于「没有可用行号」与「`location_file` 不是现存的仓库内文件」。

第三态不是新口径，而是把清单 B 的 DF-02 早已写明的警告（「漂移表对仓库外路径无覆盖能力……不是该目录已稳定的证据」）
编码进字段值。对这些条目给出 touched/unchanged 才是虚假精度。

## 4. 已知缺陷：声明而不修

`drift` 区间是 **HEAD 侧**坐标，`位置` 是 **pin 态**行号。用前者判后者，不构成「这一行被动过」的可靠判据——
一个已经漂移的 pin 行会被拿去和 head 侧区间比。

全部 123 个字段都在这个比较下产生（含本 change 之前）。修它等于同时改写 123 条，
属于「重定义口径」，本轮被明确排除。**选择：保持行为、在口径小节与 `evidence/baseline_basis.md` 里显式声明**，
把「把 pin 行映射过 diff」的正确修法留给决定重基线全表的那一轮。

这条同时解释了 AC-27：122 是 33f7cc9 插入块首行，而那次插入发生在 pin **之前**，
所以在 pin→冻结区间内它就是一条普通未改动行——查表说 unchanged 是对的。

## 5. 该文件不是生成器的完整产物（三个 Errata 节的由来）

A-1 / A-2 / A-4 三个 change 各自在生成之后**追加**了 `## Errata` 小节。实测：改前 1842 行，
直接重跑生成器只有 1473 行——**差 369 行是人工内容**。

所以写入方式必须是「重跑生成器 + 拼回尾巴」：

```
evidence/_pre_edit_opsx-changes.md   （改前快照，是尾巴的唯一可信来源）
        │
        ├─ 生成器输出 ──────────────┐
        └─ 快照中第一个 `## Errata` 之前的 `---` 起全部内容 ──┤
                                                     ↓
                                          新文件 = 生成前缀 + 原尾巴
```

边界**结构化定位**（首个 `## Errata` 往前找最近的 `---`），不写死行号；写完回读校验
「前缀逐行相等 + 尾巴逐行相等 + 总行数相等」。

这条也写进了口径小节，因为它是下一轮最容易踩的坑：**直接重跑生成器会删掉 370 行已评审内容**。

## 6. 行号基准的裁决方法

清单历史上混用过 0-based 与 1-based。裁决输入选**语义无歧义的构造**：
pin 态 `tests/test_config.py` 的 `router_per_layer == 32_896` 断言——1-based 读 L69 逐字命中，
0-based 读 L70 是空行。**基准是 1-based。**

本轮自己踩了一次同族坑：第一版更正用 PowerShell 的 `Select-Object -Skip N` 标行号，
它**静默丢了一个空行**，导致每个标号偏移 1，于是把 AC-26 锚到 177（实为 178），
并误判 AC-50 的 `spec.md:383` 是空行而「更正」到 382（原值其实正确）。

`evidence/verify_a6_errata.py` 的 `B-AC26-anchor` / `B-AC50-anchor` 当场抓到，改正后 65 项全绿。
**因此验收脚本必须从 git 独立重推，而不是复用任何中间产物的行号。**

## 7. 行内替换的边界

清单里出现过「同一条目正文与「位置」字段自相矛盾」（AC-51 正文写 `test_config.py:69`，
「位置」字段写 `tests/test_config.py:69`）。修这类不一致时：

- 用**块内有界替换**（限定 `### <ID>` 块 + 断言旧值 + 替换后回读），不用「整行给片段」。
- 清单 B 的 `基线` 是**行内**字段（跟在严重性/裁决后面），不是独立行，正则必须匹配行内形式。
- 断言失败即中止，不猜测。

## 8. 并发与所有权

`.audit/**` 在 `.gitignore:37` 内，**不受版本控制**：

- git 无法提供 before/after，必须自建快照（`evidence/_pre_edit_*.md`）。
- `run_gates.py` 的工作树采样不覆盖被忽略文件，因此本 change 的写入不会让 gate 结果作废。
- 在飞的 A-4 change 曾声明 task 9.4 要写同一文件；它**已归档**，故所有权落本 change，
  且必须逐字保留它的 Errata 小节（§5）。

根目录另有并行 session 的未跟踪脚本（`_numdrift_*.py` 等），做的是数值/数学对账，与本 change 范围不重叠；
**不动、不删、不提交**。

## 9. 门禁与 archive

- `skip_specs: true`：本 change 不改任何 requirement，因此无 spec delta。
  副作用之一：结构上不可能触发带 delta 的 change 在 archive 时吞 anchor 的那一类缺陷。
- `run_gates.py` 的 `GATE RESULT INVALID`（exit 2）表示 HEAD 或工作树在 gate 期间被改动，
  **重跑，不解读其输出**。
