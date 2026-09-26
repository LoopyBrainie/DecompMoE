# Design

## Context

Python reviewer Agent (`agent-b1a39f2827bf`) audited DecompMoE post-A3 archive cycle (2026-09-26 15:00) and reported 5 findings:

| # | Finding | Reviewer Severity | In-Scope? | Real? |
|---|---|---|---|---|
| 1 | decompmoe-skeleton/spec.md 缺 `<a id="req-13">` anchor (CLAUDE.md §6 第 8 条 violation) | MEDIUM | ✅ | ✅ |
| 2 | `phase_step_frozen_names(0)/(4) == set()` 缺 principle test | LOW | ✅ | ✅ |
| 3 | `LOSS_SPIKE_RATIO = 2.5` 缺钉值 test | LOW | ✅ | ❌ (reviewer 漏报:已由 `tests/test_safeguards.py:285` + `:634` 覆盖) |
| 4 | `extract_C(eps=...)` 默认值 1e-6 缺钉值 test | TRIVIAL | ✅ | ✅ |
| 5 | `wayfinder/spec.md` L130 + L240 spec typo | OUT-OF-SCOPE | ❌ | ❌ (reviewer 误报:L130 无 50-digit β_0 literal;L240 属 voronoi workstream) |

This change closes findings 1, 2, 4 (the 3 in-scope real findings). Findings 3, 5 documented as review-side factual errors in commit `de96ba6` for audit trail.

## Goals / Non-Goals

**Goals:**

- Closing finding 1: insert `<a id="req-13"></a>` at canonical spec.md L292 (1 line above `### Requirement: Five-Phase Schedule State Machine`), so decompmoe-skeleton spec has 23/23 anchor coverage (was 22/23 = 96%; wayfinder already 36/36 = 100%).
- Closing finding 2: add `test_phase_step_frozen_names_phase_0_and_4_empty_set` to `tests/test_schedule.py`. Pins the empty-set contract for `phase_step_frozen_names(0)` and `phase_step_frozen_names(4)` per spec req-13 L295 verbatim phrasing "empty for phases 0/4".
- Closing finding 4: extend `test_extract_C_signature` in `tests/test_extraction.py` with `pytest.approx(1e-6, abs=1e-12)` assertion on the `eps` parameter default. Pins the closed-form precondition `‖z‖₂ ≥ ε` for safe spherical normalization per spec req-7 L100.
- Test count: 198 → 199 (1 new test added; `test_extract_C_signature` extended in-place, not new).
- Lint gates exit=0; dev branch linear; not pushed (per CLAUDE.md §4, push only on user request).

**Non-Goals:**

- 不修改 `src/decompmoe/**` 任何文件 (所有改动在 spec.md anchor + pytest test 形式层,无 behavioral change).
- 不修改 `openspec/specs/wayfinder/spec.md` 或 `openspec/specs/governance/spec.md` (anchor 已 100% 覆盖).
- 不修改任何 `wayfinder/tickets/**` (ticket 数值已 lock principle form per req-gov-4 ticket advisory boundary).
- 不修 voronoi precision disclosure workstream (out-of-scope per plan §"Out-of-Scope 但相邻").
- 不 push (per CLAUDE.md §4 + 全局指令).
- 不改 finding 3 + 5 (reviewer 误报;已在 commit `de96ba6` message 中显式标注,无需后续修正).

## Decisions

### Decision 1: 改用 `### Requirement:` 现有 anchor 编号体系, 不重新编号

**选择**: 在 L292 插入 `<a id="req-13"></a>` (filling the existing schema gap between req-12 L226 and req-14 L313). 不重新编号 (避免 cascade).

**理由**: schema 演化遗留 anchor 空洞应 fill (per agent memory "spec 文件的 anchor 序列是 schema 演化的残留(每次 change 增/删/合并都会留下空洞)")。重新编号会 cascade 推所有后续 anchor (req-14 → req-15, ..., req-23 → req-24),触发广泛的反链失效 (所有引用 req-14 到 req-23 的 `**Source:**` 字段、ticket 注释、test docstring 都需要同步更新)。**Mitigation**: fill gap by inserting req-13 at L293; minimum-blast-radius fix per agent memory "Multi-surface spec line-number references drift together" (cascade-free selection).

**alternatives considered**:

- **Renumber req-14..23 → req-15..24**: cascade ~10 downstream references. Rejected by minimum-blast-radius principle.
- **Delete "Five-Phase Schedule State Machine" Requirement entirely**: violates spec promise. Rejected.
- **Skip 100% anchor coverage enforcement**: violates CLAUDE.md §6 第 8 条 hard constraint. Rejected.

### Decision 2: principle-form test vs functional-only test for `extract_C` eps default

**选择**: `assert sig.parameters["eps"].default == pytest.approx(1e-6, abs=1e-12)` (principle form, 钉值零容差).

**理由**: spec req-7 L100 closed-form precondition 是 `‖z‖₂ ≥ ε`,其中 `ε` 是 spherical normalization 的 denominator-safety 阈值。default value `1e-6` 是这个阈值的 spec-canonical 选择,必须钉死,不能依赖 reader source 推断。`abs=1e-12` 是 FP-exact 容差 (无 autograd FP 累积路径,纯 `inspect.signature(...).parameters["eps"].default` 读 Python int literal 转 float),符合 `governance/spec.md req-gov-1` §2 浮点闭式 `pytest.approx(value, abs=...)` 钉值零容差。

**alternatives considered**:

- **bare `==` with float literal `1e-6`**: req-gov-1 §1 整数闭式用 `==`,但 `1e-6` 是浮点,应走 §2 `pytest.approx(abs=...)` 路径。rejected by req-gov-1 二分法。
- **`abs=1e-6` 宽松容差**: 与 `test_safeguards.py:285` + `:634` 风格一致 (literal principle form + `abs=1e-12`)。本 assertion 是 module-attribute-vs-literal 比较 (FP-exact),`abs=1e-6` 错位——会掩盖 silent drift (`default = 1.001e-6` 仍 pass)。rejected by design。
- **functional-only `assert "eps" in sig.parameters`**: 已存在 (test L217);不 pin default value。这是 finding 4 的本质——补钉值。

### Decision 3: phase 0/4 empty-set test 命名 + body 风格

**选择**: `test_phase_step_frozen_names_phase_0_and_4_empty_set` (单一 test function 覆盖 phase 0 + phase 4 两个 assertion)。docstring 显式引用 spec req-13 L295 verbatim "empty for phases 0/4" + 设计意图 (Phase 0 K-Means freezes everything by definition; Phase 4 full AdamW unfreeze with c_i gradient-channel Active)。

**理由**: 两个 phase 共用一个 test function 符合 convention (`test_phase1_freeze_router` / `test_phase2_freeze_experts` / `test_phase3_freeze` 各自独立,但 phase 0 + 4 是同一类 "empty set" contract,可合并)。`assert actual_0 == set()` 比 `assert actual_0 == frozenset()` 或 `assert not actual_0` 更严格(显式 type 锁定 `set`);`f"phase 0 frozen-name set MUST be empty per spec req-13 L295; got {actual_0!r}"` 失败信息内嵌 actual value (per req-gov-1 §4)。

**alternatives considered**:

- **拆 `test_phase0_frozen_set_empty` + `test_phase4_frozen_set_empty`**: 两个 test function 覆盖一个 contract,scope 膨胀,违反 CLAUDE.md §3 "Surgical Changes"。
- **Functional-only `assert not schedule.phase_step_frozen_names(0)`**: 不 pin type (`set` vs `frozenset` vs `dict_keys`),regression 不易追踪。
- **Skip test**: 维持 finding 2 不关闭。rejected。

## Risks / Trade-offs

- **[Risk] anchor 位置错位导致 orphan anchor**: spec delta 必须 `<a id="req-13"></a>` 1 行 above `### Requirement: Five-Phase Schedule State Machine`,精确 1 blank line 间隔(per agent memory lesson "Spec migration leaves orphan anchor in source capability":双向配对 anchor + Requirement title;漏一个 = orphan anchor 缺陷)。**Mitigation**: apply 后立即 `grep -nE '<a id="req-13"></a>|### Requirement: Five-Phase Schedule State Machine' openspec/specs/decompmoe-skeleton/spec.md` 验证 anchor + heading 配对,line distance ≤ 3 (项目约定)。
- **[Risk] Windows Edit tool CRLF contamination**: Edit tool on Windows + 中文 spec.md 经 Edit tool 写入可能引入 CRLF (per agent memory lesson "Edit tool on Windows can introduce CRLF in non-ASCII files" 2026-09-23)。**Mitigation**: post-apply byte-level CRLF 检查 `$bytes = [System.IO.File]::ReadAllBytes('openspec/specs/decompmoe-skeleton/spec.md'); ($bytes | Where-Object { $_ -eq 13 }).Count == 0`. commit `de96ba6` post-apply 已 PASS (CR=0)。
- **[Risk] `phase_step_frozen_names(4)` 在 docstring + 注释中不一致**: 当前 docstring (schedule.py:66-75) 仅描述 phase 1-3, 不显式描述 phase 0/4 返回 `set()`。**Mitigation**: 本 change 不动 docstring (Surgical Changes principle);test docstring 中显式引用 spec L295 verbatim 作 spec-canonical source-of-truth;若 future reader 误读,test failure 信息会指向 spec L295。
- **[Risk] `test_extract_C_signature` 已存在, 扩展后 docstring 长 3 倍**: 当前 docstring 8 行, 扩展后 18 行。**Mitigation**: 仍是单一 test function, 不引入新增;reader 仍能从 `test_extract_C_signature` 名字进入。
- **[Risk] `LOSS_SPIKE_RATIO` finding 3 在 audit 中被 reopen**: 若有人读了 Python reviewer report 但没看到 commit message 中的 "reviewer 漏报" 标注, 可能误以为 finding 3 待修。**Mitigation**: commit message 中显式标注 "Findings 3 and 5 — review-side factual errors (NOT fixed)",并在 `tasks.md` 4.1 段引用此标注;本 change 的 `proposal.md` §"Why" 段同样标注 reviewer 误报列表。

## Trade-off 接受记录

- **literal-form vs module-attribute-form assertion (Finding 4)**: 选择 literal `1e-6` 是基于 FP-exact 比较 (无 autograd 累积);若未来 default 改为 `1.001e-6` (code-side silent drift),`abs=1e-12` 仍能 catch (`1.001e-6 - 1e-6 = 1e-9 >> 1e-12`)。接受此 trade-off。
- **phase 0/4 合并 test (Finding 2)**: 两个 assertion 共用 test function, 测试 count +1; reader 进入 test 时可一次看完 phase 0 + 4 contract。接受此 trade-off。