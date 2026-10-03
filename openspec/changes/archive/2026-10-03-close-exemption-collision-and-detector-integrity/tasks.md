# Tasks — 关闭豁免碰撞族与检测器完整性缺陷

## 1. 根因定位

- [x] 1.1 核实 HIGH-1：`wayfinder/spec.md:898` 的 `openspec/specs/wayfinder/spec.md` L251 是失效活指针（该 `**Source:**` 在 335 行，偏差 84），被引文示例内的 `historical` 豁免。
- [x] 1.2 核实 HIGH-2：`wayfinder/spec.md:807` 的 `metrics.py:83` 被技术名词 `history` 豁免，目标是**当前** `UR` docstring。
- [x] 1.3 确认根因在豁免而非检测：旧实现 `s.marker = _exempt(line)` 按整行判定。
- [x] 1.4 核实 MEDIUM-3：`git ls-tree -r 42d161b` 同含活跃与归档目录，删除仅存在于未暂存工作树。
- [x] 1.5 核实 LOW-7：`tracked_files()` 只 glob `*.md`/`*.py`，`EXT` 枚举 11 种扩展。
- [x] 1.6 独立复现 LOW-5 / LOW-6 的分歧落在 actionable/historical 切分上。

## 2. 清理

- [x] 2.1 移除 verifier 遗留的 5 个 detached worktree（4 个 `vrf_ptr_2210/*` + `D:/tmp/a4fix/base1526b98`），`git worktree prune`。
- [x] 2.2 移除临时目录 `vrf_ptr_2210`、`D:/tmp/a4recheck`、`D:/tmp/a4fix`（经 mavis-trash 可恢复通道）。

## 3. 归档补正（MEDIUM-3）

- [x] 3.1 核验归档副本与被替换活跃副本的 blob 同一性（`git rev-parse` vs `git hash-object`）。
- [x] 3.2 归档副本补 `.openspec.yaml`（92 个归档目录中 86 个带）。
- [x] 3.3 暂存 14 项删除并提交 `41e1663`；核验 HEAD 中活跃目录 0 项、归档目录 15 项。

## 4. 检测器

- [x] 4.1 `Site` 新增 `pos` 字段；全部构造点传入 locator 字符区间。
- [x] 4.2 重写 `code_span_mask`：扫描反引号连续段，N 开 N 闭，中间内容属于 span。
- [x] 4.3 `_exempt` 改为指针局部：`EXEMPT_WINDOW = 40`，`EXEMPT_BREAK = "。\n"`。
- [x] 4.4 窗口按 `MARKER_TAIL = 24` 尾部余量读取，`_admissible()` 约束标记起点。
- [x] 4.5 标记集重建：`histor(ical|ically)`、`supersed*`、`former(ly)`、`original(ly)`、`pre-*`；裸名词 `history` 移除。
- [x] 4.6 新增 `RE_PIN_COMMIT`，不查 code span 掩码。
- [x] 4.7 修 `L-then-capability` 的 `detail` 切片：`cm` 是 tail 上的匹配，`cm.end()` 是相对偏移。
- [x] 4.8 `EXT_EXTENSIONS` 由 `EXT` 剥离定界符派生；`tracked_files()` 改用之。
- [x] 4.9 `SELF_EXCLUDE` 的 lint 条目改为 `scripts/lint_` 前缀。
- [x] 4.10 新增 `in_scope()` 与 `scan_commit()`，工作树扫描与历史 revision 扫描共用同一过滤器。

## 5. 普查与清扫

- [x] 5.1 收紧后重普查：基线 `1526b98` = 189 strong actionable（旧检测器 100）。
- [x] 5.2 活树 actionable 24 → 15 → 14（标记集修正后释放 9 个正当历史注解）。
- [x] 5.3 15 条有界 token 替换表，每条在文件内恰好命中一次。
- [x] 5.4 修复替换造成的括号不平衡，并加逐行括号平衡断言。
- [x] 5.5 `git diff --numstat` 严格等增等删（1/1、1/1、3/3、2/2）。

## 6. harness 与门禁（MEDIUM-4）

- [x] 6.1 harness 迁至 `scripts/lint_pointer_detector.py`，`REPO` 由 `__file__` 派生。
- [x] 6.2 基线改为 `ps.scan_commit(REPO, "1526b98")`，不建 worktree、不碰 index。
- [x] 6.3 基线不可读由 `SKIP` 改为 `FAIL`。
- [x] 6.4 保留全部既有检查（19 positives / 14 negatives / 自豁免 / 回归 / 当前树）。
- [x] 6.5 新增 3b–3g：双反引号、指针局部、相邻标记仍豁免、跨分号 `superseded`、窗口边缘识别、反引号内的 commit pin。
- [x] 6.6 49 项全绿；`run_gates.py` 按 glob 自动发现，未改动该文件。

## 7. 守护测试

- [x] 7.1 `test_code_span_mask_marks_the_content_not_just_the_delimiters`
- [x] 7.2 `test_code_span_mask_handles_a_double_backtick_span`
- [x] 7.3 `test_marker_far_from_the_locator_does_not_exempt_it`
- [x] 7.4 `test_adjacent_marker_still_exempts`
- [x] 7.5 `test_canonical_ticket_annotation_is_still_exempt`
- [x] 7.6 `test_marker_at_the_window_edge_is_recognised_whole`
- [x] 7.7 `test_technical_noun_history_does_not_exempt`
- [x] 7.8 `test_pinned_commit_exempts_even_inside_backticks`
- [x] 7.9 `test_reversed_order_site_has_a_usable_span`
- [x] 7.10 `test_tracked_file_census_covers_every_extension_the_grammar_names`
- [x] 7.11 `test_scan_commit_reads_a_revision_without_a_worktree`
- [x] 7.12 `test_gate_and_census_exclude_the_same_files` 改为前缀语义
- [x] 7.13 `pytest` 全绿：405 passed, 1 skipped。

## 8. change 制品

- [x] 8.1 `.openspec.yaml` / `proposal.md` / `design.md`（D1–D9，含 LOW-5/LOW-6 errata）。
- [x] 8.2 三份 delta 由 `41e1663` 与工作树逐 Requirement diff 生成，不手抄。
- [x] 8.3 回环断言：delta 施加于 pre 逐行复现 post。该断言抓到漏文件头与 `rstrip()` 吃掉末尾空行两处。
- [x] 8.4 `openspec validate <change> --strict` 通过。

## 9. 已知遗留（不在本轮范围）

- [ ] 9.1 `governance:135` 的 `pre-edit` Note 仍含行号，且其记录的行号已过期（`## 修改记录` 实际在 L180）。它是关于 pre-edit 位置的历史陈述，改它需独立决策。
- [ ] 9.2 `run_gates.py` 归档后 `validate` 报 ERROR、GBK 控制台崩 `UnicodeEncodeError` —— 属并行 session，不碰，只报告。
- [ ] 9.3 `.audit/` 被 gitignore，指向它的定位符无法由 `git` 校验；本轮已把两处换成该目录自身使用的键（`verify-30`、cycle 标识），但结构性解耦（把 `.audit` 纳入版本化或改用可检引用）未做。
