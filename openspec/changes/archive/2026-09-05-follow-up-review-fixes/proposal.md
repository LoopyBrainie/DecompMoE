## Why

`/code-review max` 对 3 个 archived change（`2026-09-05-fix-skeleton-0-5-31-2-formula`、`2026-09-05-fix-metrics-cg-closed-form`、`2026-09-05-fix-p1-audit-batch`）的 post-archive review 发现 2 个未修复问题：

1. **HIGH 1 — 推导链不忠实**：`openspec/specs/decompmoe-skeleton/spec.md` 当时的 L434 写 `0.5 · 31 = 15.5`，字面算对但 `0.5` 不对应 σ'(0)=0.25（实际是 σ(0)=0.5），推导链隐藏数学原理。违反 CLAUDE.md §6 第 8 条「spec/code 中每个含具体数值的算式都必须有 `pytest.approx` 直接对账，且公式须反映数学原理」。
2. **MEDIUM 3 — 度/弧度内部不自洽**：`openspec/specs/wayfinder/spec.md` L185 写 `θ_Voronoi(16, 16) ≈ 67.24° (1.1736 rad)`；独立验证发现 `decompmoe-skeleton/spec.md` L98 + L102 同样写 `1.1736 rad`（三处不一致）。Bisection 实测 `1.1735482747 rad` 4dp round 为 `1.1735`；`67.24°` 通过 degree-rad identity `67.24° × π/180 = 1.17348236 rad` 4dp round 也是 `1.1735`。两个数各自独立 round bisection 输出得到 `67.24° (1.1735 rad)` ——这是 spec 字面自洽的唯一正确组合，`1.1736` 字符串无法从 bisection 输出复算。

**Reality check（2026-09-16 重核事实）**：

- **HIGH 1 spec 端已被消化**：当前 `decompmoe-skeleton/spec.md` L446 已显式写出 `σ'(0) · 2 · 31 = 0.25 · 2 · 31 = 15.5` 推导链 + cite `src/decompmoe/beta.py:50`（`MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0`），由后续 archive change（`fix-skeleton-spec-duplicate-and-completeness-2026-09-15` 及更早的 D1 Module-Level Constants 重构）完成。本 change **不再触及 HIGH 1 的 spec 端修复**。
- **MEDIUM 3 三处 `1.1736 rad` 仍未改**：`decompmoe-skeleton/spec.md` L98 + L102 + `wayfinder/spec.md` L185 三处仍是 `1.1736 rad`，与 bisection 输出 round `1.1735` 字符串不自洽。
- **测试函数名 mismatch**：原 proposal §"Test" 描述"重写 `tests/test_sphere.py::test_voronoi_rad_precision_alignment`"，但**该函数在当前 code 中不存在**；等价精度守护由 `test_voronoi_monotone_in_ne` (L77, `pytest.approx(1.173548, abs=1e-6)`) + `test_voronoi_canonical_mvp_value` (L95, residual `< 1e-9`) 共同承担，已通过 188 测试。
- **acceptance baseline**：spec 文本精度修正纯字面变化（不影响行为），重跑 `uv run pytest tests/ -v` 应保持 188 passed。

## What Changes

- **`openspec/specs/decompmoe-skeleton/spec.md` L98**：`SHALL return ≈ 1.1736 rad (≈ 67.24°)` → `SHALL return ≈ 1.1735 rad (≈ 67.24°)`（medround 一致性：67.24° × π/180 = 1.17348236 rad → 4dp round 1.1735）
- **`openspec/specs/decompmoe-skeleton/spec.md` L102**：`AND equals ≈ 1.1736 rad (≈ 67.24°)` → `AND equals ≈ 1.1735 rad (≈ 67.24°)`（与 L98 同步）
- **`openspec/specs/wayfinder/spec.md` L185**：`≈ 67.24° (1.1736 rad)` → `≈ 67.24° (1.1735 rad)`（与 skeleton spec 同步）

## What Does NOT Change (intentionally out of scope)

- **`openspec/specs/decompmoe-skeleton/spec.md` L446**：`σ'(0) · 2 · 31 = 0.25 · 2 · 31 = 15.5` 推导链 + `MAX_GRAD_PER_GAMMA_PHASE4` cite `beta.py:50` 已由后续 archive change 固化，本 change 不重做
- **`openspec/specs/decompmoe-skeleton/spec.md` L186 / L210**：`θ_Voronoi(64, 16) ≈ 58.47° (1.0205 rad)` 已是字符串自洽值（bisection 实测 1.0205068335 rad → 4dp round 1.0205），本 change 不重做
- **`src/decompmoe/beta.py`**：docstring 推导链完整（L38 `31·σ'(γ') ≤ 31·σ'(0) = 31·0.25 = 7.75`、L43 `31·σ'(0)·2 = 15.5`、L48 `|∂logit/∂γ'| ≤ 7.75 · 2 = 15.5`、L49 antipodal extreme 说明、L50 `MAX_GRAD_PER_GAMMA_PHASE4 = 0.5 * 31.0 # = 7.75·2 = 15.5`），本 change 不重做
- **`tests/test_sphere.py`**：`test_voronoi_monotone_in_ne` (L77, `pytest.approx(1.173548, abs=1e-6)`) + `test_voronoi_canonical_mvp_value` (L95, residual `< 1e-9`) 已达成同等精度守护，本 change 不新增测试函数（proposal 原描述的 `test_voronoi_rad_precision_alignment` 不存在于当前 code 中）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 — frontmatter `skip_specs: true`；本 change 的 spec 改动是文本精度修正，不改变 Requirement 的行为语义，无需 delta spec 文件）

## Impact

- 反链：code-review agent 报告（agent `ac71bd6d0ea696acc`，HIGH 1 + MEDIUM 3）；上游 change `2026-09-05-fix-skeleton-0-5-31-2-formula`；后续 archive change `2026-09-15-fix-skeleton-spec-duplicate-and-completeness-2026-09-15`（已消化 HIGH 1 spec 端修复）
- 验收基线：`uv run pytest tests/ -v` 全过（spec 改动纯字面，行为不变）
- 无破坏性变更（仅 spec 文本精度对齐）