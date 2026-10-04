# Tasks

## 1. CRITICAL — 门禁快照按内容哈希

- [x] 1.1 `worktree_snapshot` 拆为 `head` / `tracked_digest`（`sha256(git diff HEAD)`）/ `untracked_digest`（逐文件内容哈希）/ `status_lines`（诊断）→ verify: `test_porcelain_digest_collides_which_is_why_content_is_hashed` + `test_tracked_digest_detects_content_change_in_already_dirty_file` + `test_untracked_digest_detects_new_file_inside_untracked_dir`
- [x] 1.2 `_snapshot_differs` 对 digest 报 `CHANGED` 而非 64 位 hex → verify: `test_snapshot_differs_reports_digests_as_changed_not_as_hex`
- [x] 1.3 docstring 撤回「三个彼此独立的分量」过度声称 → verify: 读回 docstring

## 2. MAJOR — `req-gov-9` 假前提

- [x] 2.1 构造六种点态检测形态的实测用例 → verify: `tests/test_run_gates.py` 全部通过
- [x] 2.2 写出「吞 anchor 不可被新增掩蔽」的算术守卫（先写成反例，被测试判负后改正）→ verify: `test_a_swallow_cannot_be_masked_by_simultaneous_additions`
- [x] 2.3 `check_anchor_coverage` docstring 改为写实测结论 → verify: 读回
- [x] 2.4 delta：`## REMOVED Requirements`（req-gov-9）+ `## ADDED Requirements`（req-gov-10），`MODIFIED` req-gov-8 改正文 → verify: `verify_deltas.py` 15 项全过
- [x] 2.5 同步 `CLAUDE.md` §3 与 `run_gates.py` docstring 的 `req-gov-9` → `req-gov-10` → verify: grep 无残留

## 3. MAJOR — evidence 工具在归档位置失效

- [x] 3.1 新增 `evidence/_paths.py`：`find_repo_root`（按 `openspec/specs` 标记向上找）+ `find_change_dir`（live/archive 两处）+ `is_archived` + `refuse_if_archived`（exit 2）→ verify: `tests/test_a5_evidence_paths.py` 11 项
- [x] 3.2 旧 change 的两个脚本改用 `_paths` → verify: 归档位置实跑，输出解释性信息且 exit 2
- [x] 3.3 `test_depth_index_approach_is_wrong_in_the_archived_layout` 把原缺陷可执行地钉住 → verify: 该测试通过
- [x] 3.4 新 change 的 `evidence/gen_deltas.py` + `verify_deltas.py` 用同一套定位 → verify: 生成与回验均 exit 0

## 4. MINOR — Source 字段

- [x] 4.1 实测生成豁免登记表（不手打）→ verify: 20 条，与 review 实测的 19 skeleton + 1 wayfinder 吻合
- [x] 4.2 `requirement_blocks` + `check_source_presence` + `check_registry_stale` → verify: 11 项新测试
- [x] 4.3 把「整树陈旧检查」从「单文件检查」里拆出来 → verify: 第一版合并实现被自己的测试判负，拆分后通过
- [x] 4.4 `SOURCE_LINE_RE` 放宽（AC-81）+ `body` 改按 match 结束偏移切片 → verify: `test_prefixed_source_line_is_still_checked[3 前缀]` + `test_prefixed_but_canonical_source_line_is_accepted` + `test_source_body_is_sliced_at_the_match_end_not_a_fixed_length`
- [x] 4.5 `CLAUDE.md` §3 增列检查 ④ 与切片不变量 → verify: 读回

## 5. 校验脚本自身

- [x] 5.1 `declared_added_anchors` 只收 Requirement 级 anchor → verify: `test_declared_added_anchors_ignores_modified_and_sub_anchors`
- [x] 5.2 替换名不副实的 `test_..._ignores_modified_blocks`（原断言是恒真的）→ verify: 新测试用合成 change 树，真跑解析器
- [x] 5.3 修 `verify_deltas.py` 四条假红断言（列表 `in` 当子串 / 替换文本复用短语 / 前缀仍在 / MODIFIED anchor 必然碰撞）→ verify: 15 项全过
- [x] 5.4 生成器计数断言改行首锚定 → verify: `text.count` 虚增 2 已修

## 6. 记录但不修（用户裁决 / 超出本 change 范围）

- [x] 6.1 `decompmoe-skeleton` 19/23 缺 Source —— 已登记豁免，不造 lineage（design D4）
- [x] 6.2 三个失效 change（`2026-09-26-followup-…`、`fix-review-findings-…`、`2026-10-03-close-pointer-…`）不接管 → 见 design D7 与旧 change 的 Errata
- [x] 6.3 AC-57（归并行 change 的 `req-gov-2` 改写）、AC-100（落点在被排除的 change 目录）不接管

## 7. 记录为已知缺口（不在本 change 修）

- [ ] 7.1 `skeleton req-15` 指名 `tests/test_schedule.py::test_empty_cell_preserves_centroid`，实际在 `tests/test_extraction.py:438`（review 实测 43 处跨 Requirement 提名中 42 处可解）。属并行 change 的行号指针 sweep 范围，**不碰**，仅记录。
- [ ] 7.2 三个测试用变体 key 而非字面 `actual=`：`test_voronoi_residual_below_1e_minus_9`、`test_voronoi_angle_one_sided_gap`、`test_voronoi_measurement_layer`（均非本 change 的文件），违反 `CLAUDE.md` §6 第 8 条的失败信息要求。**不碰**，仅记录。
- [ ] 7.3 wayfinder `req-24/26/29/33` 有闭式但提名 0 个测试且无机检强制。**不碰**，仅记录。

## 8. 归档 —— **已完成（2026-10-03）**

起初因并行 session 的 `pointer_scan` 自指测试红而延后（用户裁决：等其修好检测器）。
该 session 在 `42d161b` 修好后门禁转 7/7 全绿，延后条件消失，遂继续归档。

**归档过程实测**：

- [x] 8.1 写 anchor 账本（68 anchor，3 capability，`expect_new` 自动派生为
      `['req-gov-10', 'req-gov-11']`）
- [x] 8.2 归档前门禁 `GATE OK`（7/7，稳定工作树）
- [x] 8.3 **归档再次吞掉 anchor**（第四次复现）：`req-gov-10` 的正文落地而
      `<a id="req-gov-10"></a>` 被吞。**未重跑 archive**，按协议手术式字节级补回。
- [x] 8.4 账本比对发现**本工具自身的新缺陷**：`--verify` 把 change 有意 REMOVE 掉的
      anchor 报成 LOST，并给出"手术式补回"指令——而补回一个被刻意删除的
      Requirement 的 anchor 本身就是错的。已修（新增 `removed_anchors()`，分列
      `removed` 与 `lost`），并补 3 项测试（含"不得因此漏报真实丢失"与
      "按 (capability, id) 定位"两条反向守卫）。见 design D8。
- [x] 8.5 归档后账本复核：`OK (69 anchor(s) intact, 2 declared-new present,
      1 deliberate removal(s))`
- [x] 8.6 归档后门禁全绿
- [x] 8.7 归档后独立复核（需非实现者）—— **2026-10-04 完成**

  由一个全新会话的 `verifier` agent 执行（我本人是实施者，不得自审）。任务书明确
  要求：**一切数字从 git 对象重算**，禁止运行或 import 本 change 的 `evidence/*.py`
  ——`gen_deltas.py` 正是 `verify_deltas.py` 所校验的那个 delta 的生成器，自证不成立。

  **裁决：已履行，但发现 2 个 HIGH 缺陷（按用户裁定本轮只记录、不修）。**

  **L1 delta 落地保真：通过。** 4 个块全部忠实落地；`req-gov-8` 的 Scenario 数
  4→4、`req-gov-10` 6→6、`req-gov-11` 3→3；`req-gov-9` 标题与 anchor 均已消失；
  三个 anchor 行与 delta 发出的**逐字节相同**（手术补回的不是手打变体）；
  `diff(B, L)` 恰好等于 delta 声明的变更集，无越界改动。

  **L2 spec ↔ 实现：35 条断言逐条核验，33 条代码满足且有测试守护。** 8 条无守卫
  MUST 记为 finding（#1 #2 #4 #8 #18 #19 #27 #35）。

  **L3 数字：21 条断言，19 条确认。** 关键确认：六形态表**六条全部复现**
  （第 5 形 retarget 为 GREEN，与我写的一致）；`SOURCE_EXEMPTIONS` = 20；骨架
  19/23、wayfinder 1/36；`> **Source:**` 在 `1526b98` 命中 L908、在其余 revision
  均 0 命中（且打印了 35 行宽松候选以证明文件存在）；D8 引用的 `anchor-ledger`
  输出在**修复前**的 `run_gates.py` 上**逐字节复现**。

  **推翻了我自己给复核方的两条线索**（这正是独立复核的价值）：
  - 「D5 的 48/48 是错的」——**错的是我的线索**。在 `d493ef6`（D5 描述的那个
    revision）与 `ea802c8` 上确实是 48/48；跳到 49/49 是本 change 自己的 delta
    加了两个带 `**Source:**` 的 Requirement。数字对，缺的是 revision。
  - 「两个 ledger JSON 逐字节相同」——**不准确**。它们在 `change` 字段上不同
    （4385 vs 4423 字节）。但结论成立：两者都是修复后快照，不夹逼归档动作。

  **HIGH 发现（只记录，待议）**：
  - **F1** `status_lines` 参与了 INVALID 判定，与**同一 commit 写下**的
    `req-gov-8` 新条款（「a derived count of changed entries MUST NOT be treated
    as an independent signal」）**直接冲突**，且 docstring 声称它「仅供人参考」。
    更糟：`test_snapshot_differs_names_every_moved_field` 断言 `len(moved) == 4`
    并把 `status_lines` 列入——**测试钉住了违规行为，改对反而会让测试红**。
    复核方未能构造出 `status_lines` 单独移动而三个 digest 全部不变的可达路径，
    即该违规目前是**潜伏**的。
  - **F2** `5739598` 新增的「removed on purpose」第三类报告**无任何 Requirement
    要求**（`req-gov-10` 只定义 `lost` 与 `never-added` 两类），违反 `CLAUDE.md` §2
    「先改 OpenSpec spec 再改代码」。且该行为有 **3 个测试强守护**——钉得死、无人
    要求，是最坏的组合。

  **其余**：F3（`CLAUDE.md` §3 把 `SOURCE_LINE_RE` / match-end 切片这条代码不变量
  归给了并不含该条款的 `req-gov-11`）、F5（D5 数字未记 revision）、F7（归档在 6 个
  声明范围外的 wayfinder 块间插了空行，纯空白、无语义影响）。

  **明确未能核验的项**（不记为通过）：Change A D3「重跑会得到 4 条红」与 D6
  「`verify_deltas.py` v1 的四个假红」——任务书禁止执行该脚本（自证），只读了代码；
  D1「48 个脏条目」与 D2「第四次复现」是**未提交工作树**的瞬时观测，无 revision，
  **不可从 git 重算**；摘要前缀 `97c0d2fd…` 因原始临时 repo 未保留而不可复现
  （但其**定性**结论「porcelain 对两种内容状态逐字节相同」被独立复现，成立）。

> 前一版本把「写 anchor 账本」打了 `[x]` 却并未真的写过任何账本文件——该勾选是假的，
> 已按实测更正。一个打了勾但没做过的步骤，比一个明确未勾选的步骤危险得多：前者会让
> 读者以为归档前置已就绪。
