# Tasks — 统一门禁与检测器的豁免路径，并修正一处引文漂移

## 1. 复核结论的独立复现

- [x] 1.1 F1：`lint_no_line_pointers.py:299` 是整行豁免；`classify_pointer` 从不读 `s.historical`。门禁与检测器对规范形态给出相反裁决。
- [x] 1.2 F2：`superseded:`、`原理`/`原子`/`还原`、引文内的 lead —— 逐条复现。
- [x] 1.3 F4：D6 的 `85/80` 未测；`189` 是第三轮检测器的值。
- [x] 1.4 F5：`req-8`（L181-196）不含 `Voronoi`/`67.24`；`req-11`（L247-302）三者全含。
- [x] 1.5 F9：`当时为` 是不可达条目。
- [x] 1.6 F10：`724 / 636 / 80`，差值 88 中 8 个由 `SELF_EXCLUDE` 排除，D6 归因错误。

## 2. 门禁与检测器统一（D1）

- [x] 2.1 `classify_pointer` 返回 `(nums, weak, all_historical)`。
- [x] 2.2 C1 改为仅在 `all_historical` 为真时跳过；`has_historical_marker` 不再参与门禁判定。
- [x] 2.3 守护测试 `test_gate_and_detector_agree_on_the_canonical_supersede_form` 直接断言两者一致。
- [x] 2.4 守护测试 `test_gate_exempts_only_when_every_site_is_historical` 守住反方向。

## 3. 检测器

- [x] 3.1 `RE_SUPERSEDE_LEAD` 计入 `superseded:` 冒号形。
- [x] 3.2 lead 尊重 `code_span_mask`（此前是唯一不查掩码的规则）。
- [x] 3.3 `原` 收窄为必须带过去态复合词；`旧` 同。
- [x] 3.4 删除不可达条目 `当时为`。
- [x] 3.5 标记不得跨越同行另一定位符（D4）。
- [x] 3.6 `governance:145` 改指 `req-11`；替换文本不含行号。

## 4. 普查范围（D5）

- [x] 4.1 14 个文件钉在范围内（含 6 个票据）。
- [x] 4.2 4 个文件钉在范围外（检测器 + 两个 lint + 守护测试）。
- [x] 4.3 守护测试 `test_census_scope_pins_known_files_in_and_out`。
- [x] 4.4 总量断言保留但不作为正确性依据。

## 5. 门禁自检

- [x] 5.1 `MIN_CHECKS` 45 → 80：对症删除（6 项）后 77 < 80 被抓。
- [x] 5.2 注释明确其为绊线，真正承重的是 `len(found) > 0`。

## 6. change 制品

- [x] 6.1 `.openspec.yaml` / `proposal.md` / `design.md`（D1–D8）。
- [x] 6.2 一份 delta（`governance` `req-gov-3`），由 `cec3b08` 与工作树 diff 生成，回环验证通过。
- [x] 6.3 errata 表每格标注测量所用的检测器版本（D8 新规则）。
- [x] 6.4 `openspec validate <change> --strict` 通过。
- [x] 6.5 `run_gates.py` GATE OK（4 lint / 422 passed / stable worktree）。

## 7. 已知残留

- [ ] 7.1 短距离跨子句（`now spec.md L453`、`was X) - but see spec.md L453`、`formerly X; current value: spec.md L453`）仍豁免；无结构线索，泛化会与规范注解冲突。复核确认活树 0 例。
- [ ] 7.2 普查召回 `path … prose … L###`：43 个 token 中 13 个被覆盖，14 个未覆盖全在 `governance/spec.md`，9 个指向 gitignored 的 `.audit/`。
- [ ] 7.3 `before` 作介词、`original` 关于活文件，仍被当作标记。
- [ ] 7.4 `.audit/` gitignored，指向它的定位符无法由 `git` 校验。
- [ ] 7.5 `run_gates.py` 的两条工具缺陷属并行 session，不碰。
