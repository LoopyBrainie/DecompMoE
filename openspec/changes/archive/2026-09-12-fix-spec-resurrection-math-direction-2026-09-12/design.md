## Context

`openspec/specs/decompmoe-skeleton/spec.md` 是 DecompMoE skeleton 的真相源（22 Requirements × 76 Scenarios），`tests/test_safeguards.py` 是对应实现层的守护测试。本次 change 针对 `should_resurrect semantic interpretation (per-step vs avg-window)` 场景的"Mathematical equivalence disambiguation"段落的数学命题方向错误、"Beta Parameterization Operational Domain"需求的常量行号陈旧、以及 `test_safeguards.py` 中对应守护测试的函数名方向反向，三处独立但同因（数学事实 = `per-step ⊊ avg-window`）的错处。

具体证据（已事实验证）：

1. **spec L248** 写"`flag_step ⟹ flag_avg` is **not** universally true (counterexample below)"——初等代数可直接证伪（`∀j: H[j][i] < T ⇒ Σ H[j][i] < consec·T ⇒ mean < T`）。spec 自带的 counterexample（`H = [0.005]*199 + [0.99]`）反而证明的是**反向**（`flag_avg = TRUE ∧ flag_step = FALSE`，所以 `flag_avg ⟹ flag_step` 不普遍成立）。
2. **spec L248** 同段又说"they are not nested by inclusion"——与下文 L703 的 "per-step ⊊ avg-window (per-step more conservative)" 自相矛盾。正确嵌套：`per-step ⊊ avg-window`（per-step 触发历史 ⊊ avg-window 触发历史）。
3. **spec L423** 引用 `src/decompmoe/beta.py:46 MAX_GRAD_PER_GAMMA_PHASE4`，实际 `:46` 行是 `_MAX_GRAD_BETA_PHASE4_INTERNAL = 31·0.25 = 7.75`（带下划线前缀的 INTERNAL 常量，不在 `__all__`）；公开导出的 `MAX_GRAD_PER_GAMMA_PHASE4 = 0.5·31.0 = 15.5` 在 `:50` 行。
4. **`tests/test_safeguards.py` L677** 函数名 `test_should_resurrect_per_step_is_strict_superset_of_avg_window_for_monotonic_history` 写"superset"方向，与 docstring L678/L703/L745 三处的 `per-step ⊊ avg-window` 相反；这是 spec 错误传染到测试的二次产物。

约束（继承自项目 CLAUDE.md §6、§10、wayfinder spec `Source:` 反链规范、archive 前 lint gate）：

- 数学命题必须可直接闭式对账（`pytest.approx(value, abs=...)`）。
- 不得新增/删除 Requirement 或 Scenario，纯文本校正。
- spec 改完后，lint 必须 `exit=0`（`scripts/lint_no_dead_defensive.py` + `scripts/lint_no_source_field_drift.py`），其中 Source 反链需含 `wayfinder/tickets/<ID>.md`（按 capability 区分规则，decompmoe-skeleton 默认需 wayfinder/tickets 反链）。
- 不得为本次修改引入训练或 baseline 跑动（formalize-only）。

## Goals / Non-Goals

**Goals:**

- spec L248 的命题方向从"`flag_step ⟹ flag_avg` is **not** universally true" 改为"`flag_step ⟹ flag_avg` **IS** universally true (proved by elementary algebra...)"；同段"they are not nested by inclusion"改为"`per-step ⊊ avg-window` (per-step triggers only on histories that also trigger avg-window, but not conversely)"；删除 "only when the avg-window condition holds on the same history" 的矛盾修饰。
- spec L423 的 `src/decompmoe/beta.py:46` 改为 `:50`。
- `tests/test_safeguards.py` L677 函数名中的 `strict_superset` 改为 `strict_subset`。
- 修复后 spec ↔ code ↔ test 三方在"per-step ⊊ avg-window"这一数学事实上自洽。

**Non-Goals:**

- 不修改 `src/decompmoe/` 下任何源代码（行为不变；纯文本/命名校正）。
- 不修改 `openspec/specs/wayfinder/spec.md`（L249 的 `f_i^avg` 措辞已与本次修正完全自洽）。
- 不修改 `tests/test_safeguards.py` 的运行行为（docstring 已正确，仅函数名方向反；闭式断言 `pytest.approx(0.009925, abs=1e-6)` 等不变）。
- 不重新打开 `flag_step` / `flag_avg` 哪一个是"正确"语义的辩论（spec 明确 per-step 是 current code 解读，保留 per-step 解读不变；本次仅修正"per-step ⊊ avg-window"嵌套方向的描述正确性，不切换实现）。
- 不引入新的测试场景（如 avg-window 实现的语义测试仍属 future ticket，本次 OpenSpec 的"Open follow-up"段已标注）。

## Decisions

### Decision 1：在 spec 中写出"flag_step ⟹ flag_avg IS universally true"的代数证明，而非仅写结论

**理由**：spec 之前的错误版本直接断言 `flag_step ⟹ flag_avg` "is not universally true"，但没写出为何"不普遍"的代数证明——事实证明该断言本身就是错的。仅把文字从"is not universally true"改成"IS universally true"会让下一个 reader 重新陷入"为何不普遍成立"的疑问，缺少上下文。**显式写出 `∀j: H[j][i] < T ⇒ Σ H[j][i] < consec·T ⇒ mean < T` 三步代数证明**让该命题成为可独立验证的闭式事实，并避免日后再次反转。

**替代方案 A**：仅删掉矛盾段，不写证明——失败，因为留空会让"为何 per-step 触发 ⇒ avg-window 也触发"这件事失去可追溯的代数链。

**替代方案 B**：写完整数学证明 + counterexample 同步迁移到 spec 附录——超出本次范围，counterexample 已在原段（L250-252）保留，无需迁移。

### Decision 2：spec L423 行号从 `:46` 改为 `:50`，不改 `:46` 行的语义

**理由**：`:46` 是 `_MAX_GRAD_BETA_PHASE4_INTERNAL = 31·0.25 = 7.75`（带下划线前缀、不在 `__all__`、注释明确写"INTERNAL intermediate value (NOT in `__all__`)"）；`:50` 才是公开导出的 `MAX_GRAD_PER_GAMMA_PHASE4 = 0.5 * 31.0 = 7.75·2 = 15.5`。spec 引用的语义目标是后者（"operational-domain Phase 4 worst case is `σ'(0) · 2 · 31 = ... 15.5`"），行号应当指向真正承载该值的行。

**替代方案 A**：把 spec 引用改成"`:46` (INTERNAL) 或 `:50` (公开)"双引用——过度复杂化；spec 引用的目标是公开常量，单一引用即可。

### Decision 3：test 函数名 `strict_superset` → `strict_subset`，不改测试断言

**理由**：docstring L678/L703/L745 已经写 `per-step ⊊ avg-window`，断言（counterexample A avg-window TRIGGER / per-step NO TRIGGER）已经体现 `per-step` 是 `avg-window` 的严格子集。函数名只是命名方向反了，无任何断言或运行行为需要改。改名后 `tests/` grep 关键词 `strict_superset` 不再命中，但 docstring 仍可被 `per-step ⊊ avg-window` 命中——符号搜索的关键词保留向后兼容。

**替代方案 A**：保留函数名 + 在 docstring 加 "⚠️ 函数名历史遗留"警告——会留下文档与命名长期不一致的债务，反而制造新的混淆风险。

**替代方案 B**：同时把 `superset` 改成 `strict_subset_of` 后再 adjust docstring——超出本次范围，docstring 当前已正确。

### Decision 4：本次只改一个 test 函数名；不动 `test_should_resurrect_current_per_step_semantic_pinned`

**理由**：后者（L634）是 spec 中提到的"guard test"——它当前 pin 的就是 per-step 解读（与 spec L249 wayfinder 措辞一致），没有方向错误，不需要改动。

## Risks / Trade-offs

- **[Risk] Spec 文本修改可能引入新的 lint 报错** → Mitigation：archive 前跑 `python scripts/lint_no_dead_defensive.py` 与 `python scripts/lint_no_source_field_drift.py` 双 gate；本次只动 scenario 内散文与一行数字引用，不动 `Source:` 反链字段（已含 `wayfinder/tickets/A6a-2.md` + `change fix-openspec-doc-bugs design.md (Decision 7)`，按 decompmoe-skeleton capability 规则走 wayfinder/tickets 反链，满足 lint 期望）。
- **[Risk] Test 函数名改名后，`grep -r strict_superset` 类外部脚本可能失效** → Mitigation：本次搜索面在仓库内（`tests/`），无外部脚本依赖 `strict_superset` 字符串；CI 跑的是 `pytest tests/test_safeguards.py`（按函数全名查找，对改名无感），不会触发回归。
- **[Risk] "per-step ⊊ avg-window" 这条数学事实若被下一个 change 误读为"avg-window 才是正解，应切换实现"** → Mitigation：spec 段尾保留"Open follow-up"句（"a future ticket adopting avg-window semantics would re-evaluate..."），显式锚定"per-step 仍是 current code 解读"；本次 change 不切换实现，仅修正描述方向。
- **[Trade-off] 显式代数证明占据 L248 约 60 token，会让该段变得更长** → Accepted：信息密度提升（之前那段的"不普遍成立"是错误的，写出证明比写错命题更经济）。该段本身是 spec 中最有教育价值的段落，多 60 token 不构成冗余。
- **[Risk] `tests/test_safeguards.py` 函数名 rename 改变了 pytest -k 过滤关键词 `strict_superset`** → Mitigation：仓库内无 `-k strict_superset` 显式调用；唯一关联的是 spec 段尾 `test_should_resurrect_current_per_step_semantic_pinned`（未改名）；pytest 自动收集靠 import + decorator，不依赖 `-k` 关键词过滤。

## Migration Plan

无运行时/部署面变更——纯 spec 文本 + 测试函数名改名。落地步骤（顺序敏感）：

1. `openspec/changes/.../proposal.md` ✓（已写）
2. `openspec/changes/.../specs/decompmoe-skeleton/spec.md` ✓（已写）
3. `openspec/changes/.../design.md` ← 当前步骤
4. `openspec/changes/.../tasks.md`（待写）
5. **Apply 阶段**：
   a. 编辑 `openspec/specs/decompmoe-skeleton/spec.md`：把 L248 段落替换为含"flag_step ⟹ flag_avg IS universally true"代数证明的新段落；把 L423 的 `:46` 改为 `:50`。
   b. 编辑 `tests/test_safeguards.py` L677 函数名：`strict_superset` → `strict_subset`。
   c. `uv run pytest tests/test_safeguards.py -v` 跑全部，确认 `test_should_resurrect_per_step_is_strict_subset_of_avg_window_for_monotonic_history` 与其它测试都过。
   d. 跑 `python scripts/lint_no_dead_defensive.py` 与 `python scripts/lint_no_source_field_drift.py`，确认 `exit=0`。
6. **Archive 阶段**：`/opsx:archive`（spec delta 同步到主 spec，归档 change）。

回滚策略：若 apply 阶段 lint 失败，回滚 `spec.md` 与 `tests/test_safeguards.py` 的两处文本即可——变更范围极小（spec 改 2 处 / test 改 1 处），回滚成本低于 5 分钟。

## Open Questions

无。所有可在 apply 阶段前解决的歧义已在 Decisions 节锁定：

- math 方向：代数证明 + 反向 counterexample 已固化（无需在 apply 时再决定）。
- 行号：`:50` 已与 code 现状对齐（无需在 apply 时再决定）。
- test 函数名：`strict_subset` 已选（无需在 apply 时再决定）。
- 是否切换实现语义：明确 non-goal（不动 per-step 解读）。