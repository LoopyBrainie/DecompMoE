## 1. Spec Text Refinement (MEDIUM 3 — 字符串精度对齐)

- [x] 1.1 `openspec/specs/decompmoe-skeleton/spec.md` L98：`SHALL return ≈ 1.1736 rad (≈ 67.24°)` → `SHALL return ≈ 1.1735 rad (≈ 67.24°)`（验证：`Select-String -Path spec.md -Pattern "1\.1736"` 应 0 命中 L98，且 `Select-String -Pattern "1\.1735 rad"` 应在 L98 命中） — 已落地（2026-09-16）
- [x] 1.2 `openspec/specs/decompmoe-skeleton/spec.md` L102：`AND equals ≈ 1.1736 rad (≈ 67.24°)` → `AND equals ≈ 1.1735 rad (≈ 67.24°)`（验证：同上，剩余的 `1.1736` 命中应只来自非 skeleton / 非 wayfinder 的 spec 文件，例如 metadata 历史引用） — 已落地（2026-09-16）
- [x] 1.3 `openspec/specs/wayfinder/spec.md` L185：`≈ 67.24° (1.1736 rad)` → `≈ 67.24° (1.1735 rad)`（验证：`Select-String -Path wayfinder/spec.md -Pattern "1\.1736 rad"` 应 0 命中） — 已落地（2026-09-16）

## 2. Test (verification of precision guard — already in place)

- [x] 2.1 `tests/test_sphere.py::test_voronoi_monotone_in_ne` (L77) 已使用 `pytest.approx(1.173548, abs=1e-6)` pin `canonical_voronoi_angle(16, 16)`，等同/优于 proposal 原描述的 identity-form 精度守护；`test_voronoi_canonical_mvp_value` (L95) 用 residual `< 1e-9` 验证 bisection 闭式根。无需新增 `test_voronoi_rad_precision_alignment` 函数（该函数名在当前 code 中不存在，亦未由任何 archive change 创建）。

## 3. Note (intentionally out of scope — HIGH 1 已由后续 archive change 消化)

- [x] 3.1 `openspec/specs/decompmoe-skeleton/spec.md` L446 已显式包含 `σ'(0) · 2 · 31 = 0.25 · 2 · 31 = 15.5` 推导链 + cite `src/decompmoe/beta.py:50`（`MAX_GRAD_PER_GAMMA_PHASE4: Final[float] = 0.5 * 31.0`），由 `fix-skeleton-spec-duplicate-and-completeness-2026-09-15` 及其前置 D1 Module-Level Constants 重构完成。本 change 不再触及 HIGH 1 的 spec 端修复。
- [x] 3.2 `src/decompmoe/beta.py` docstring L38/L43/L48-L50 推导链完整，code 端无修改需求；`tests/test_beta.py::test_max_grad_per_gamma_phase4` (L132-153) 已有 autograd 闭式对账。

## 4. Validate & Archive

- [x] 4.1 `openspec validate 2026-09-05-follow-up-review-fixes` 验证 schema 合规（frontmatter `skip_specs: true` + zero delta 已声明 OK）
- [x] 4.2 spec 改动完成后跑 `uv run pytest tests/ -v` 全过 — 验证：终端输出 `188 passed`，且无 `1.1736 rad` 相关 assert 失败 — 已落地（2026-09-16，188 passed in 5.34s）
- [x] 4.3 `openspec archive 2026-09-05-follow-up-review-fixes --yes` — 验证：`openspec list --json` 中该 change 不再出现，且 `openspec/changes/archive/2026-09-05-follow-up-review-fixes/` 由 CLI 写入而非手工 mv — 已落地（2026-09-16，CLI exit 0，change 不再出现在 `openspec list --json`）