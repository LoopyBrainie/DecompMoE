# Proposal

## Why

`.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` A-5 段（18 条）在 pin
commit `6593a06` 上整理了「OpenSpec 制品格式、门禁与归档流程」这一层的问题。逐条在
HEAD `940b27c` 上重新定位与事实验证后，**11 条仍成立、4 条已修、3 条部分成立**。
其中 7 条集中在同一件事：**`CLAUDE.md` §3 那段归档前置条件，在它声称要防的损坏上
返回 exit 0**。

三个独立的失败方式，各自都被实测复现：

1. **门禁清单是唯一的执行面，而它覆盖不到它要防的东西。** §3 规定的两道 lint 加
   `openspec validate --specs`，在 anchor 已被 `openspec archive` 吞掉的 spec 树上
   **三项全部 exit 0**。`CLAUDE.md` §6 把「spec anchor 100% 覆盖」写成硬约束，归档
   这一步却没有任何可执行形式去核对它（AC-20）。`scripts/` 下也没有任何 CI 配置，
   两个 lint 与全部测试只在人工触发的会话里跑（AC-21）。§3 同样不含
   `openspec validate <change> --type change --strict`，于是两个既无 delta 也无
   `skip_specs` 的 change 一路走到 100% 完成、已落库、已归档，制品始终非法（AC-49）。

2. **门禁在并发写入的工作树上跑，结论不可复现。** 同一轮门禁的两次 `git status`
   采样之间，`tests/test_loss.py` 从干净变为已修改，两次 pytest 都返回全绿 —— 但
   第二次的 pass 对应的文件内容已经不是第一次采样时的那份（AC-25）。本 change 写作
   期间该状态复现：`openspec/specs/**` 三份 spec 在一分钟内向 +12 / +13 行漂移。
   **「通过」与「不知道」被压成同一个 exit 0**，这正是假绿的机制。

3. **`openspec archive` 静默吞掉后继 Requirement 的 anchor，而没有任何东西会发现。**
   pin 之后复发两次（`4f3e752`、`16b2f46`），openspec 升到 1.14.0 仍复现（AC-19）。
   关键在于**点态计数查不出它**：archive 吞掉被改 Requirement **之后那一个**的
   `<a id>` 与其后一行空行，于是 `anchors == headings` 依然成立。只有归档前后的
   **账本比对**能把损失指名。`scripts/` 下没有任何 anchor 覆盖检查（AC-80），唯一的
   anchor 逻辑在 `merge_spec_deltas.py` 里，而它是应用器不是检查器。

此外 **AC-24** 独立成立：`lint_no_source_field_drift.py` 的必需要子串只硬编码到
目录前缀 `wayfinder/tickets/`，裸目录形式与不带 `.md` 的 ticket id 形式都能三项全过，
与规范形式不可区分 —— 反链 lineage 不可追溯可以合法通过门禁。读 `wayfinder` `req-34`
可见责任面更宽也更矛盾：它正文要求带文件名的 MUST，紧接着自己的执行细则第 1 条
降级为只要求含目录前缀。

## What Changes

- **新增 `scripts/run_gates.py`** 作为唯一门禁入口。**lint 以 `scripts/lint_*.py`
  通配发现，不逐条枚举** —— 这是让清单与实际门禁不可能失步的结构性修复，也使
  并行 change 后续新增的 lint 无需改本文件即被吸收。
- **门禁结果可复现（AC-25）**：运行前后各采样 `git rev-parse HEAD` 与
  `git status --porcelain` 的 SHA-256；不一致时输出 `GATE RESULT INVALID` 并
  **exit 2**，与 lint 报红的 exit 1 区分开。
- **change 级校验只校验正在归档的那个（AC-49）**，不遍历全部未归档 change。
- **anchor 账本（AC-19 / AC-80）**：`anchor-ledger --write` / `--verify`，把
  `lost`（基线有、现在没了）与 `never_added`（change 声明新增、实际没加）**分列**，
  因为两者在原始计数上不可分辨。
- **零检查不是通过**：门禁发现数为 0 时直接报 FAIL，不允许 `all([])` 真空为真。
- **AC-24 收紧**：新增检查 ①b，要求 backtick 内出现 `wayfinder/tickets/<ID>.md`
  完整文件名；`wayfinder` `req-34` 执行细则第 1 条同步订正，解除 spec 内部自相矛盾。
- **改写 `CLAUDE.md` §3** 为指向单一入口，不再逐条枚举 lint 脚本。

## Capabilities

### New Capabilities

无。三条新 Requirement 由既有 peer capability `governance` 承载（其 Purpose 明确
收纳 `CLAUDE.md` amendment 来源的治理条款）。

### Modified Capabilities

- `governance`: **ADDED** `req-gov-7`「Archive Gate Must Be Executable」、
  `req-gov-8`「Gate Result Must Be Reproducible」、
  `req-gov-9`「Spec Anchor Ledger Across Archive」。
  ⚠️ 编号从 `req-gov-7` 起：`req-gov-6` 已被并行 change
  `2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract` 认领为
  「Cross-Reference Anchor Contract」，撞号会重新制造重复 anchor。
- `wayfinder`: **MODIFIED** `req-34` —— 执行细则第 1 条由「目录前缀」收紧为
  「含 `.md` 的完整 ticket 文件名」，与正文 L838 及相应 Scenario 同步。

## Impact

- **新增文件**：`scripts/run_gates.py`、`tests/test_run_gates.py`、本 change 的
  `evidence/`（delta 生成与回验脚本）。
- **修改文件**：`scripts/lint_no_source_field_drift.py`（新增检查 ①b +
  `REQUIRED_FORM_PATTERNS` + `_code_spans` + `required_form_pattern_for`）、
  `tests/test_lint_no_source_field_drift.py`（追加 6 个测试；`test_one_line_multiple_independent_violations`
  的期望计数由 2 改为 3，因新检查 ①b 独立触发）、
  `CLAUDE.md` §3、`openspec/specs/{governance,wayfinder}/spec.md`。
- **不改变任何数学或数值语义**；不碰 `src/`；不碰 `tests/` 的任何断言数值或期望值。
- **不新建** `scripts/lint_no_line_pointers.py`（归并行 change 所有）；本 change 的
  glob 会自动吸收它。
- **不 retro-edit** `openspec/changes/archive/**`（遵守既有「Archive copies are not
  retro-edited」原则）。
- **不碰** 两个陈旧无 delta 的 change（`2026-09-26-followup-…` 与
  `fix-review-findings-…`）：其文件正被并行 session 处于删除中的未提交状态。
- 门禁由 2 个 lint 增至通配发现的全部门禁 + `openspec validate` + `pytest`。
