# Tasks — 关闭 `superseded by` 补语豁免与剩余的整行抑制盲区

## 1. 复核结论的独立复现

- [x] 1.1 H1：9 处 `req-N L###` 全部过期（`req-11 L204`/`req-20 L453` 指向空行，`req-13 L268` 偏 61 行），由 `superseded` 跨分号豁免。
- [x] 1.2 H2：`if found:` 使 `scan_commit` 返回 `[]` 时门禁 exit 0。
- [x] 1.3 M1a：`RE_LABEL_L` 命中即抑制整行。
- [x] 1.4 M1b：未闭合反引号 / fence 的 body 漏给标记器。
- [x] 1.5 M2：`dedupe` 让 `hist` 实例遮蔽同键 `live` 实例。
- [x] 1.6 L3：`EXEMPT_BREAK = "。\n"` 对英文行空转。
- [x] 1.7 L4：`旧` / `之前` 缺失，`原` 单字不对称。
- [x] 1.8 L5：`defaced` / `effaced` / `deadbeef` 各豁免一处活指针。
- [x] 1.9 M3：复核报告的 `628d5c5 = 102/86/81/16/17` 与我自己的 `104/88/83/16/17` 不符；以我的重算为准并如实记录分歧。

## 2. 检测器

- [x] 2.1 `RE_SUPERSEDE_LEAD` + `_exempt` 的补语判定：站点落在 `superseded by` 补语内则不豁免。
- [x] 2.2 `RE_LABEL_L` 改为等长空格抹除标签，保留字符偏移。
- [x] 2.3 `code_span_mask` 未闭合段标记到行尾。
- [x] 2.4 `dedupe` 活优先：同一 locator 任一处为活即报活。
- [x] 2.5 `EXEMPT_BREAK` 改正则 `[。！？]|[.!?](?=\s|$)`；窗口只保留包含站点的一段。
- [x] 2.6 移除裸 hex 标记；`has_marker_anywhere` 改查 `RE_PIN_COMMIT`。
- [x] 2.7 中文旧时态补齐 `旧`/`之前`/`曾`/`当时`。

## 3. 门禁

- [x] 3.1 空基线判负，不再由 `if found:` 包裹。
- [x] 3.2 打印并断言已执行检查数（`MIN_CHECKS = 45`，实际 64）。
- [x] 3.3 普查范围断言改为构成而非总数；`> 500` 是把排除项当正确性要求的坏断言，正确数字是 80。
- [x] 3.4 3e 拆成「`by` 补语不豁免」与「同一行的真历史定位符仍豁免」两条，正反都断言。

## 4. 清扫

- [x] 4.1 替换表带**期望命中数**（`A6b-1`/`A8-2` 各 2 处），唯一性断言在第一版把这两条拦下。
- [x] 4.2 9 处 `req-N L###` → Requirement 锚点；`req-20 L453` → `req-20-mci`。
- [x] 4.3 `governance:145` 的 `req-1 L184-L185` 实际落在 `req-8` 内；替换保留原 id。
- [x] 4.4 `git diff --numstat` 严格等增等删（1/1 ×4、2/2 ×2、1/1）。
- [x] 4.5 活树 14 站点 → 5 站点，actionable 0，5 个豁免各带正当标记。

## 5. 守护测试

- [x] 5.1 `test_label_mention_does_not_suppress_the_whole_line`
- [x] 5.2 `test_label_blanking_preserves_character_offsets`
- [x] 5.3 `test_unterminated_code_span_masks_to_end_of_line`
- [x] 5.4 `test_unclosed_fence_body_is_code`
- [x] 5.5 `test_dedupe_does_not_let_a_historical_instance_shadow_a_live_one`
- [x] 5.6 `test_english_sentence_boundary_breaks_the_exemption`
- [x] 5.7 `test_a_dot_in_a_path_is_not_a_sentence_boundary`
- [x] 5.8 `test_bare_hex_word_is_not_a_pin`
- [x] 5.9 `test_chinese_past_state_vocabulary_is_symmetric`
- [x] 5.10 `test_empty_baseline_is_not_a_pass`
- [x] 5.11 改写 `test_canonical_ticket_annotation_*`：断言拆成正反两条。
- [x] 5.12 修 `test_prior_commit_id_exempts`：`has_marker_anywhere` 改查 `RE_PIN_COMMIT`。
- [x] 5.13 `pytest` 全绿：415 passed, 1 skipped。

## 6. change 制品

- [x] 6.1 `.openspec.yaml` / `proposal.md` / `design.md`（D1–D9，含对上一轮 D7 的 errata）。
- [x] 6.2 一份 delta（`governance` `req-gov-3`），由 `08b5dbb` 与工作树 diff 生成，回环验证通过。
- [x] 6.3 `openspec validate <change> --strict` 通过。
- [x] 6.4 `run_gates.py` GATE OK（4 lint / 415 tests / stable worktree）。

## 7. 已知遗留（不在本轮范围）

- [ ] 7.1 M4 普查召回：`path … prose … L###` 结构性不可见（43 个 `L<2+digits>` token 中 13 个被覆盖），14 个未覆盖 token 全在 `governance/spec.md`，其中 9 个指向 gitignored 的 `.audit/`。门禁目前看不到这一类。
- [ ] 7.2 `before` 作介词（"the value before clipping"）与 `original`（"the original entry point"）仍会被当作标记。二者与 `before the change` 词法上无法区分，属已知的过豁免方向。
- [ ] 7.3 `governance:135` 的 `pre-edit` Note 仍含行号且已过期（`## 修改记录` 实际在 L180）。它自述为 pre-edit 位置，改它需独立决策。
- [ ] 7.4 `.audit/` 被 gitignore，指向它的定位符无法由 `git` 校验。结构性解耦未做。
- [ ] 7.5 `run_gates.py` 归档后 `validate` 报 ERROR、GBK 控制台崩 `UnicodeEncodeError` —— 属并行 session，不碰，只报告。
