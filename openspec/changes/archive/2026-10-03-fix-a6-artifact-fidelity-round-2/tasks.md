# Tasks

## 1. 建 change 骨架

- [x] 1.1 `.openspec.yaml`（`skip_specs: true`）+ `proposal.md` + `design.md` + `tasks.md`
      → verify: `openspec validate <name> --type change --strict` 无 ERROR
- [x] 1.2 design.md 记录 D1（F-1 驳回证据）、D5（F-9 预先裁决 + F-8 耦合）、D7（import 自伤）
      → verify: 逐条 grep 到 D1 / D5 / D7 标题

## 2. F-2 — `self_check()` 报告键集差异

- [x] 2.1 把 `build_pin_drift.py` 复制到本 change `evidence/`，改用 `__file__` 自定位 + 结构化找仓库根
      → verify: 从本 change 目录内直接跑 `--self-check` 可跑
- [x] 2.2 键集差异单独计算并**全量打印**三类键（`only-in-original` / `only-in-mine` / `shared`），不截断
      → verify: 输出逐条列出 12 个仅我方存在的路径（实测 count=12）
- [x] 2.3 新增硬断言：`only-in-mine` 的键若携带**非空**区间 ⇒ 报红返回 1
      → verify: `verify_artifacts.py` 的 NEGATIVE PROBE 2（多余非空键被拒）
      与 NEGATIVE PROBE 3（原表有、我方丢失的键被拒）；PROBE 1 确认空区间键仍被接受且**被记录**
- [x] 2.4 PASSED 措辞拆成「区间逐键相等」与「键集」两句；键集不等时显式写明
      → verify: 输出中 `files=` 一词消失；`KEY SETS ARE NOT IDENTICAL` 在位
- [x] 2.5 断言**区间逐键相等**这一原有不变量未被削弱
      → verify: 输出显式给出 `105 intervals across 48 shared keys`

## 3. F-3 — 产物命名

- [x] 3.1 `--out` 默认值改为 `drift_<pin[:7]>..<head[:7]>.json`
      → verify: 跑一次默认输出，文件名含双端点
- [x] 3.2 重新生成 `evidence/drift_6593a06..95718cf.json`，与归档的 `pin_drift_95718cf.json`
      逐键比对 `drift` / `inserted` / `modified`（归档那份的 head 就是 `95718cf`，
      不是 `--self-check` 用的 `188b9fb`，两者不可混用）
      → verify: 三张表逐键相等（277 键 / 570·283·269 区间，两侧一致）
- [x] 3.3 新产物的 `pin` / `head` 字段与文件名一一对应，且 `head` 用**完整 40 位 SHA**
      → verify: `verify_artifacts.py` 断言文件名 == `drift_<pin>..<head>.json`
      且与归档表的 pin/head 逐字相等

## 4. 生成器 `ANNOT` 重复键

- [x] 4.1 `AC-28` 两段文本合并为单条（`[边界保留]` + `[溯源缺口]` 都保留）
      → verify: 合并后文本同时含两段的关键句
- [x] 4.2 `AC-29` 两段文本合并为单条（`[分桶存疑]` + `[溯源缺口已消 + 位置已更正]` 都保留）
      → verify: 同上
- [x] 4.3 新增 `ast`-based 模块级自校验：解析 `__file__`，`ANNOT` 有重复键即 `raise`
      → verify: NEGATIVE PROBE —— 把守卫 `exec` 到 `__file__` 指向损坏副本的命名空间，
      必须抛 `AssertionError` 且消息指名 `AC-28`；同时守卫在真生成器上返回 19
- [x] 4.4 `ANNOT` 总键数不变（19），证明是合并而非丢弃
      → verify: `verify_artifacts.py` 断言 19 且无重复键

## 5. 产物回填与清单措辞

- [x] 5.1 `AC-28` 丢失的 `[边界保留]` 段回到 `lists/opsx-changes.md`
      → verify: 该关键句在清单中恰好出现 1 次
- [x] 5.2 `AC-29` 的 `[分桶存疑]` 段**只校验不重复写**（产物中已存在）
      → verify: 该关键句在清单中出现于 4 个**不同上下文**（条目标题 / 角标本体 /
      汇总表行 / 对账口径段），逐处核对确认无重复注入
- [x] 5.3 口径段复述的「60 文件 / 105 区间 / 0 差异」改为**分两项**如实陈述
      → verify: 正文（首个 `## Errata` 之前）不再把旧数字当作现状；
      旧措辞作为「被修正的对象」在 Errata 中仍被引述（属应保留的历史记录）
- [x] 5.4 追加 `## Errata (A-6 制品复验 侧)`，记录 F-2 / F-3 / ANNOT / F-1 驳回 /
      F-8·F-9 待办 / INCIDENT 六节
      → verify: 清单 `## Errata` 小节数由 4 变 5；`A-6` 前缀小节有 2 个
- [x] 5.5 口径段改动**手术式同步**进 live 清单（生成器与产物都改，二者不会失步）
      → verify: `sync_caveat_wording.py` 幂等；写入前后 Errata / `基线` / 条目数均不变

## 6. 回验

- [x] 6.1 `evidence/verify_artifacts.py` **回读已写出的产物**做结构校验：重算键集、
      逐键比三张表、回读清单数 Errata 小节与 `基线` 三态、用 `ast` 读生成器
      → verify: **46 项 / 0 失败**
- [x] 6.2 自校验脚本**先断言计数再断言内容**（避免「对空列表 `all()` 真空为真」）
      → verify: `基线` 先断言 108 再断言 23/72/13 分项；Errata 先断言 5 再断言各段
- [x] 6.3 `python scripts/run_gates.py --change <name>` 全绿
      → verify: exit 0，0 findings

## 7. 本 change 造成的自伤与恢复（见 design D7）

- [x] 7.1 验证脚本 `import` 生成器 → 清单 1931 行被覆盖成 1495 行，4 个 Errata 全丢
- [x] 7.2 从 A-6 快照按结构边界恢复 369 行尾巴，逐字节校验
- [x] 7.3 用 A-6 自带幂等写入器补回第 4 个 Errata 小节
- [x] 7.4 A-6 自带验证器 `verify_a6_errata.py` **65/65 全绿**
- [x] 7.5 生成器加拒绝逻辑：显式写 live 清单 → `exit 2`（实测，且 live 毫发无损）
- [x] 7.6 `verify_artifacts.py` 改用 `ast` 读生成器，**永不 import**
- [x] 7.7 拼接产物这一性质写进生成器 docstring 与拒绝提示

## 8. 明确不做

- **不改** `openspec/changes/archive/**` 下任何文件（修正一律走 Errata，见 design D6）
- **不改** `openspec/specs/**`、`src/**`、`tests/**`
- **不重跑** `openspec archive`（本 change 归档前不得自行归档，等用户指示）
- **不重生成** `opsx-changes.md` 全文（该文件是「生成前缀 + 手写尾巴」的拼接产物；
  生成器现已拒绝写 live 清单，见 D7）
- **不修** review 第二部分的 F-4 / F-5 / F-6 / F-7 / F-8 / F-9 / C-5
  （用户裁定本 change 只修 Part 1；F-9 的修法已预先裁决并记入 D5）
