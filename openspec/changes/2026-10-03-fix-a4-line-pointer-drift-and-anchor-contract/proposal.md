# Proposal

## Why

本仓把**行号当成交叉引用的身份**：`L413`、`req-11 L245`、`safeguards.py:211` 这类指针散布在 spec / src / tests 三层，用来定位真相源。行号不是稳定身份——任何一次编辑都会让它们失效，而当前没有任何规则或 lint 拦截。A-4 审计段记录了 15 条此类缺陷，实测 `STALE_FIXED = 0`：**自 pin commit `6593a06` 以来一条都没被修过**。

根因是 `wayfinder` req-36：它自称「钉死真相源」，却整条 Requirement 与 5 个 Scenario 全部以行号写就，**自相矛盾**（正文说 MCI 在 L453，Scenario 说在 L413），逐字复制 req-20 的闭式全文制造第二份可漂移副本，并在散文里直接写 `<a id="req-20"></a>` 字面量——后者正是 `wayfinder` spec 当前 `39 anchors / 37 Requirements` 反向失配的原因。它的 Scenario 甚至**强制**「spec L413 … unchanged by this change」，即 spec 在命令自己的行号不许动。任何对 req-20 的编辑都会使 req-36 失效，而修 req-36 又要编辑 spec ⇒ 自我维持的漂移。

这一族已被 **5 个归档 change 逐条打补丁，每次都漏兄弟点**（`2026-09-12-replace-literal-wayfinder-l249-with-anchor-ref` 显式排除 tests/，导致 AC-67 的 10 处指针至今仍在；`2026-10-01-fix-f1-f2-f3-f8-precision-and-pointer-drift` 修了 `tests/test_schedule.py` 的 `line 495` 却漏了 `src/decompmoe/schedule.py` 的同款）。**按 finding 列表施工已连续失败五次**，因此本次不做第 6 次打补丁，而是关闭整族并加机检 gate。

## What Changes

- **BREAKING（引用形式）**：活体 `openspec/specs/**`、`src/**`、`tests/**` 中所有行号引用改用稳定标识。普查实测 **117 行指针**（20 行带历史标记豁免，**97 行待迁移**），分布 14 个文件；计划阶段 §1.1 的 237 是宽松正则上界，**含 `d_c[L2-step2]` 这类「L2 = 第 2 层」的技术标签误报**，精确口径为 117。
- **新增块级 anchor 粒度**：全库此前**只有** `<a id="req-N">` 一种 anchor。按「入向引用 ≥ 2 才铸」规则新增块级 anchor（`req-18` 18 处、`req-7` 13、`req-11` 13、`req-20` 12、`req-9` 12 等 10 个目标），其余改用 `Req 号 + 标题 + 逐字引文`。
- **移除 `req-36`**（`## REMOVED Requirements`）：它整条 Requirement 与 5 个 Scenario 全部以行号写就，**自相矛盾**（正文说 MCI 在 L453，Scenario 说在 L413），逐字复制 req-20 全文制造第二份可漂移副本，并在散文里直接写 `<a id="req-20"></a>` 字面量——后者正是 `wayfinder` spec 当前 `39 anchors / 37 Requirements` 反向失配的原因。它的 Scenario 甚至**强制**「spec L413 … unchanged by this change」，即 spec 在命令自己的行号不许动。任何对 req-20 的编辑都会使 req-36 失效，而修 req-36 又要编辑 spec ⇒ 自我维持的漂移。**该族是最大单一簇：`spec L413` 有 18 处入向引用**（占可迁移指针约 19%）。四条保障全部并入真正拥有它们的 Requirement：(a) MCI 规范形式 → `req-20` 新 Scenario；(b)(c)(d) 两条 A8-2 票据注解及其联合覆盖 → `governance` `req-gov-2`。
  *为何是移除而非改写*：`openspec validate` 拒绝「重命名了现存 Scenario」的 `MODIFIED` block（archive 拒绝丢弃），而 req-36 的 Scenario **标题本身就含行号**（`Spec L413 is the unchanging canonical closed-form for MCI`），因此既不能原名保留、也不能就地改写。移除是唯一同时满足两个约束的形态。
- **清除 anchor 字面量污染**：`req-17` / `req-20` 重复 anchor 归零，wayfinder 恢复 `anchors == headings == 37`。
- **新增 lint `scripts/lint_no_line_pointers.py`**（4 项检查：无行号引用 / anchor 唯一性 / anchor 字面量禁入散文 / 引用可解）+ 配套测试，并接入 `CLAUDE.md` §3 archive 前置 gate。
- **governance 前置修改**：现 governance 两处**强制** ticket supersede 注解使用 `req-N L###` 形式，若不同步修改则 lint 永远绿不了。改为 anchor 形式并声明行号为 legacy。
- **AC-63 补齐守护**：`decompmoe-skeleton` req-15 声称 arctan 不变式「已在 req-16 由具名 test 强制执行」，但 req-16 无此不变式、tests/src 实测零命中。补 req-16 Scenario + 数值对账测试。实测：代入 `arctan(π/√d_c)` 会使 6dp 字面量守卫偏离 **5.08e5 倍容差**，现有字面量钉**能**判别，缺的只是「点名被禁形式」的守护。
- **订正 A-4 清单记账错误**：6 条「真实位置」是 0-based 而同段另 5 条是 1-based；`基线` 字段 15 条全标 `unchanged-since-pin`，按文件读法 14/15 错。

**不改变任何数学或数值语义**；不碰 A-1/A-2/A-3 段条目；不修现存 2 个 `openspec validate` failed（属另两个陈旧 no-tasks change）；`openspec/changes/archive/**` 不在扫描范围（governance 既有「Archive copies are not retro-edited」原则）。

## Capabilities

### New Capabilities

无。引用锚点契约作为 governance capability 的一条新 Requirement 承载（governance 已是既有 peer capability，其 Purpose 明确收纳 `CLAUDE.md` amendment 来源的治理条款），不新开 capability 以免产生近重复名。

### Modified Capabilities

- `wayfinder`: **REMOVED** req-36（四条保障迁移至 `req-20` 与 `governance` `req-gov-2`）；MODIFIED req-2 / req-6 / req-13 / req-20 / req-32 的行号与代码指针改锚点/符号形式；req-20 新增块级 anchor `#req-20-mci` / `#req-20-source` 与「唯一真相源」Scenario。
- `decompmoe-skeleton`: MODIFIED req-16 / req-18 / req-21 / req-23 的行号改符号/锚点形式；req-16 新增 arctan 守护 Scenario。
- `governance`: ADDED `req-gov-6`「Cross-Reference Anchor Contract」（注意：**不是 `req-gov-5`**，该编号已被 "Numeric Literal Provenance in Specs" 占用，撞号会重新制造重复 anchor）；MODIFIED req-gov-2 / req-gov-4 的 ticket 注解规范形式由 `L###` 改为 anchor 形式（行号降级 legacy），并接收 req-36 迁移来的三条票据注解保障。

## Impact

- **spec**：`openspec/specs/{wayfinder,decompmoe-skeleton,governance}/spec.md`，涉及 anchor 增删与 Requirement 正文改写；anchor 覆盖率必须维持 100%。
- **src**：`decompmoe/{config,schedule,metrics,sphere,extraction,beta,safeguards}.py` —— **仅注释/docstring/断言消息文本**，不改任何可执行逻辑、签名、常量或数值。
- **tests**：`test_{safeguards,metrics,extraction,sphere,beta,config,schedule}.py` —— 注释与 docstring 改写；新增 1 个测试（AC-63 守护）；新增 lint 自测文件。**不修改任何既有断言的数值或期望值。**
- **新增文件**：`scripts/lint_no_line_pointers.py`、`tests/test_lint_no_line_pointers.py`、本 change 的 `evidence/`（普查脚本与 JSON、AC-63 数值复核脚本）。
- **gate**：archive 前置条件从 2 个 lint 增至 3 个。
- **无破坏性 API 变更**，无依赖变更，不触碰训练执行（`CLAUDE.md` §7 out of scope）。
