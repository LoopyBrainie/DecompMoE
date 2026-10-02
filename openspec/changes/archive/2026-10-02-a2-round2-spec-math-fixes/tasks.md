# Tasks

`design.md` D1–D7 是本轮决策依据。spec 正文本轮**不直接编辑**，只经 §3 的确定性重放落地（理由见 D6）。

## 1. 测试（先于 spec，保证测试钉的是数学事实而非旧文本）

- [x] 1.1 **F1 / D2**：`tests/test_sphere.py` 把 `test_spherical_l2_normalize_float64_residual_bounded` 重写为 `test_spherical_l2_normalize_residual_dimension_dependent_bound` —— 断言改为维度相关界 `worst ≤ d·eps`，扫描维数由 `{8,16,32,128}` 扩到 `{8,16,32,128,512,1024,4096}`，`4·eps` 包络**仅**在 `d = d_c = 16` 断言。验证：**实证新守卫会红** —— 把断言换回 `worst ≤ 4·eps`，`d=1024`（`9.992007e-16`）与 `d=4096`（`1.554312e-15`）立即越界，而新形式在全部 7 个维数上成立
- [x] 1.2 **F5 / D4**：`tests/test_sphere.py::test_cap_area_dc2_affine_degeneration` 的偏差带由 `0.03..0.07` 收紧到 `0.036..0.0652`，扫描角由 `(1,20,37,60,89,89.9)` 扩到 `(1,20,37,60,81.34,89,89.9,89.999,89.99999)`；canonical 角由 `N_e ≤ 32` 扩到 `N_e ≤ 64`、上界由 `0.06` 收紧到 `0.054`，并**新增 `N_e` 单调性断言**。验证：`pytest tests/test_sphere.py -q` → 27 passed
- [x] 1.3 **F7 / D7**：`tests/test_extraction.py::test_complexity_budget` 的 `flops_routing` / `active_core` 全部改从 `cfg` 派生（`4*cfg_dc*cfg_hkv*cfg_dk + 2*cfg.N_e*cfg_dc`、`8*cfg.d_model**2 + cfg.k*6*cfg.d_model*cfg.d_ffn`），并补 `active_core == 33_554_432` 闭式断言。**注**：`FLOPs_Routing` 无 spec 闭式，其分解式是测试自造，已在注释中显式标注。验证：`pytest tests/test_extraction.py -q` → 14 passed

## 2. Delta 生成

- [x] 2.1 单一编辑表驱动：`$env:TEMP\round2.py` 的 `EDITS` 表承载全部 11 条编辑（capability / req-id / line_hint / old_sub / new_sub），`emit` 与 `apply` 两个模式共用同一张表，杜绝「delta 与落地不一致」。验证：`python round2.py emit` → `PROBLEMS: none`
- [x] 2.2 每条编辑断言 `old_sub` 在其 `line_hint` 定位到的行内**恰好命中 1 次**。**实施期修正了脚本自身的一个 bug**：req-6 的 `line_hint` 原写成 Scenario 标题 `d_c = 2 affine degeneration`，而 `old_sub` 在正文行里，导致 `old_sub occurs 0 times`；改为 `Measured implementation deviation` 后通过。**教训**：`line_hint` 必须定位**含 `old_sub` 的那一行**，不是同一 Requirement 内的任意行
- [x] 2.3 三份 delta 覆盖 6 个 block：`decompmoe-skeleton` req-6（2 行）/ req-19（2 行），`wayfinder` req-11（2）/ req-17（2）/ req-18（4）/ req-19（2）、`governance` req-gov-1（8），合计 **24 行**。验证：脚本报告的 del+ins 与上表逐 block 一致

## 3. 门禁

- [x] 3.1 `openspec validate 2026-10-02-a2-round2-spec-math-fixes --type change --strict` → 退出码 0。验证：输出 `Change '…' is valid`，`exit=0`。**注**：首轮 `exit=1` —— validator 按**标题**匹配 MODIFIED block 内的场景集合，把 Scenario 改名读成「删旧增新」并拒绝。因此 Scenario 标题**保持逐字不变**，改在 THEN 首句显式声明「标题的 "equals 1.0" 是显示形式、规范性主张是下面的界」；标题重命名登记为残留项，不强推
- [x] 3.2 `python -m pytest -q` 全绿、零既有测试被改红。验证：**227 passed**，与本轮改测试前的收集数一致（本轮改的是既有 3 个测试的断言，未增删测试函数）

## 4. 落地（D6：确定性重放，**不跑 archive 的 spec-update**）

- [x] 4.1 记录落地前的三份 spec 指纹与完整 anchor 清单作为对照基线。验证：`git show 188b9fb:openspec/specs/<cap>/spec.md` 全部可读；基线为 decompmoe-skeleton `23 anchors / 23 headings`、wayfinder `36 / 36`、governance `4 / 4`，三者均**无重复 id、无孤儿 anchor、CRLF=0、无 BOM**；`git status -- openspec/specs/` 在 apply 前为空
- [x] 4.2 `python round2.py apply` 按区间重放，每条编辑仍断言 `old_sub` 在其目标行内唯一命中、每个目标 anchor 恰好出现 1 次。验证：输出 `APPLIED … ×3` + `PROBLEMS: none`
- [x] 4.3 `python round2.py verify` 做**块级逐行 diff**：主 spec 的每个 MODIFIED block 必须与 delta 同名 block 逐行相同。验证：7 个 block 全部 `MAIN == DELTA OK`，末行 `VERIFY: PASS`、`PROBLEMS: none`
- [x] 4.4 **变更行数对账** → **22 == 22 精确吻合**。**这里修正了本任务初稿的一个方法错误**：初稿打算用 `git diff --numstat` 对账，但 numstat 的基准是 **HEAD**，而第一轮的 37 行同样未提交，实测得 45，既不等于 22 也无法归因。改用**重建 apply 前状态**（同一张编辑表反向应用 `new_sub → old_sub`）再与当前逐行 diff，得 decompmoe-skeleton `del=2 ins=2`、wayfinder `del=5 ins=5`、governance `del=3 ins=3`，**合计 20**；修正反向定位的 bug 后（见下）为 **22**，与 §2.3 声明一致
- [x] 4.5 **anchor 复算** → 三份 spec 全部通过。验证：decompmoe-skeleton `23 / 23`、wayfinder `36 / 36`、governance `4 / 4`，无重复 id、无孤儿 anchor；更关键的是**重建的 apply 前状态与当前状态的 anchor→heading 映射逐条相同**（23 / 36 / 4 全等），即本轮**只移动行号、不动任何 Requirement 的身份**。**`exit code` 与 `~ N modified` 计数均未作为证据**
- [x] 4.6 换行风格未被统一改写。验证：apply 前后三份 spec 的 CRLF 计数均为 **0**、无 BOM；重建的 apply 前状态与当前逐行 diff 只命中 §2.3 声明的 22 行，**无整文件伪 diff**。**补充更正（提交时实测）**：commit 前发现三份 spec 的**工作树**已变为 CRLF（645 / 895 / 172 行），该转换发生在 apply 之后、来自本 change 脚本之外的过程。因仓库 `.gitattributes` 声明 `*.md text eol=lf`，`git add` 会归一化，已实测**三份 spec 的「CRLF→LF 归一化工作树」与暂存 blob 逐字节相同**（sha256 `0dbe8018…` / `fd43b805…` / `92aaa180…`），且**暂存内容**的 anchor 仍为 23/23、36/36、4/4 无重复 —— 即**入库内容就是本 change 验证过的内容**，工作树的 CRLF 是被仓库策略吸收的瞬态

## 5. 归档与终验

- [x] 5.1 `openspec archive 2026-10-02-a2-round2-spec-math-fixes -y --skip-specs` → `exit=0`，报告 `"specsUpdated": false`，change 已移入 `openspec/changes/archive/2026-10-02-a2-round2-spec-math-fixes/`。**落地后再跑一次对账**：`ROUND-2 TOTAL CHANGED LINES = 22`、`PROBLEMS: none`，证明 `--skip-specs` 确实没有二次触碰 spec（D6 的核心验证）
- [x] 5.2 `python scripts/lint_no_dead_defensive.py` → `exit=0`；`python scripts/lint_no_source_field_drift.py` → `exit=0`，输出 `OK (3 file(s) scanned, no violations)`。**重点已验**：req-gov-1 的 `**Source:**` 首项仍是 `` `CLAUDE.md` ``，本轮只在行尾追加了 `change 2026-10-02-a2-round2-spec-math-fixes` 的 Decision D1 引用
- [x] 5.3 `openspec validate --specs --strict` → `exit=0`。验证：汇总行 `Totals: 3 passed, 0 failed (3 items)`；输出中的 `requirements[N] text is very long` 为 INFO 级提示，非失败
- [x] 5.4 `python -m pytest -q` 全绿。验证：**227 passed**
- [x] 5.5 **全仓 `req-N L###` 裸行号引用复扫** → **本轮造成的引用回归 = 0**。方法：同一份引用文本分别对 **HEAD 版 spec** 与**当前 spec** 的 anchor 做区间校验 `anchor_L ≤ ref_L < next_anchor_L`，取差集归因。扫描面为 `src/` `tests/` `openspec/specs/` `wayfinder/` `scripts/`（不含 `archive/`）。结果：`req-N L###` 引用共 21 条，当前越界 14 条，**其中 14 条在 HEAD 就已越界（即早于第一轮），本轮新增越界 0 条**。**修正了本任务初稿扫描器的两个缺陷**：①`req-N` 在不同 capability 间**编号碰撞**（wayfinder 与 decompmoe-skeleton 都有 `req-20`），初稿对所有 capability 逐一试匹配，会把 wayfinder 的引用「验证」到 skeleton 的同名 anchor 上 —— 改为按**文件归属**解析唯一 capability；②PowerShell 承载含反引号的 Unicode pattern 会解析失败，改为 Python。**这 14 条属既有债，不在本 change 范围**（多数位于 `wayfinder/tickets/`，按 `CLAUDE.md` §8 为非约束性制品），仅登记
- [x] 5.6 `openspec archive` 吞 anchor 登记为上游 issue 候选（`design.md` Open Question 3）。证据已在 `design.md` D6 完整记录：8 个 MODIFIED block 丢 5 个 anchor、注入 3 个外来 anchor 造成 3 个重复 id，全程 `exit 0` + `validate` 全绿 + 两条 lint 全绿。**本仓规避手段已落地并验证**：确定性重放 + `archive --skip-specs`

## 6. 不在本轮范围

- `d_c=2` 与 `x→1` 的求积精度修复（只声明，不修）
- 第一轮 20 条勘误条目的任何改动
- `src/` 任何可执行代码
