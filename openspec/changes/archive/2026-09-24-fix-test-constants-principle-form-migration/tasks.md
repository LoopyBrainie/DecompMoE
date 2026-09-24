# Tasks

## 1. Test Refactor — Literal Principle Form + 钉值零容差

- [x] 1.1 `tests/test_beta.py:180-187` `test_constants_exported`:L187 `assert abs(beta.MAX_GRAD_PER_GAMMA - 15.95) < 1e-6` → `assert beta.MAX_GRAD_PER_GAMMA == pytest.approx(0.25 * 2 * 31.9, abs=1e-12)`(literal principle form `0.25 * 2 * 31.9` 钉值 + `abs=1e-12` 钉值零容差 per `governance/spec.md req-gov-1`)。docstring 从"beta module must export MAX_GRAD_PER_C and MAX_GRAD_PER_GAMMA as Final[float]"扩展为反映 principle-form factor guard,记录 derivation chain `σ'(0) · 2 · (β_max − β_min) = 0.25 · 2 · 31.9 = 15.95`。**verify**: `Select-String -Path tests/test_beta.py -Pattern "15\.95" | Measure-Object` 应返回 0 行(L187 一处迁移); `Select-String -Path tests/test_beta.py -Pattern "0\.25 \* 2 \* 31\.9" | Measure-Object` 应返回 1 行(L187 新 literal principle chain)
- [x] 1.2 `tests/test_beta.py:190-200` `test_max_grad_per_gamma_phase4_closed_form`:L200 `assert beta.MAX_GRAD_PER_GAMMA_PHASE4 == pytest.approx(15.5, abs=1e-6)` → `assert beta.MAX_GRAD_PER_GAMMA_PHASE4 == pytest.approx(0.25 * 2 * 31.0, abs=1e-12)`(literal principle form `0.25 * 2 * 31.0` 钉值 + `abs=1e-12`)。L190-199 docstring 已写 `31·0.25·2 = 15.5` derivation chain,隐含 principle form,无需大改。**verify**: `Select-String -Path tests/test_beta.py -Pattern "15\.5" | Measure-Object` 应返回 0 行(L200 一处迁移); `Select-String -Path tests/test_beta.py -Pattern "0\.25 \* 2 \* 31\.0" | Measure-Object` 应返回 1 行(L200 新 literal principle chain)

## 2. Validate (pytest + grep)

- [x] 2.1 `uv run pytest tests/test_beta.py::test_constants_exported tests/test_beta.py::test_max_grad_per_gamma_phase4_closed_form -v` — verify: terminal `PASSED` × 2,无 FP 累积偏差告警(per design.md Decision 1 / Risks §1 FP 累积路径不同风险,预期 1e-15 量级偏差 << 1e-12 容差)
- [x] 2.2 `uv run pytest tests/ -v` — verify: terminal `190 passed`(ad64063 baseline 测试数 + 本 change 不新增 test function,总量仍 190;若 `test_safeguards.py::test_max_grad_constants_principle_form` 已存在由 ad64063 加,本 change 不重复新增),无 principle-form 闭式对账失败
  - **post-apply 实测**: terminal `199 passed, 1 warning in 5.40s`(实际 baseline 是 199 测试,不是 ad64063 commit message 标的 190;本 change 不新增 test function,数量仍 199;1 warning 是 cuda GPU 检测 warning,与本 change 无关)
- [x] 2.3 `grep -rn "15\.95\|15\.5" tests/test_beta.py` — verify: 0 命中(scope-bound 验证本 change scope 内完全清理;scope 外 `tests/` 全集应仅 `tests/test_safeguards.py::test_max_grad_constants_principle_form` L658-659 docstring 提到 `= 15.95` 与 L661 `= 15.5` derivation chain 解释,属 scope 外 reference 文案,per design.md Decision 3 不动)
  - **post-apply 实测**: literal 断言 0 命中(`Select-String -Path tests/test_beta.py -Pattern "abs\(.*- 15\.95|pytest\.approx\(15\.5|pytest\.approx\(15\.95"` → 0 行);docstring derivation chain 引用 7 处命中(`15.95` 在 L140/L145/L183 docstring 解释 derivation;`15.5` 在 L203/L214/L218/L250 docstring 解释 derivation,与 ad64063 `test_grad_gamma_bound` L140-145 docstring 保留 `15.95` derivation 数字的风格一致;ad64063 commit message 显式说明"replace misleading expression with principle form ... = 15.95",保留 derivation 数字是配套,非 literal 钉值)

## 3. Hygiene — CRLF Check (per memory 2026-09-23 lesson)

- [x] 3.1 byte-level CRLF check on `tests/test_beta.py` — verify: PowerShell `$bytes = [System.IO.File]::ReadAllBytes("tests/test_beta.py"); ($bytes | Where-Object { $_ -eq 13 }).Count` 应返回 0(全 LF,无 CRLF 污染);`git diff --stat` 不报 `CRLF will be replaced by LF the next time Git touches it` warning
  - **post-apply 实测**: ($bytes | Where-Object { $_ -eq 13 }).Count = 0(全 LF);git diff 12 +/3 -,无 CRLF warning;Edit tool on Windows + 中文/数学符号 触发 CRLF contamination 风险已规避(per memory 2026-09-23 lesson)

## 4. Archive

- [x] 4.1 `openspec validate 2026-09-24-fix-test-constants-principle-form-migration` — verify: frontmatter `skip_specs: true` 接受 0 spec delta
  - **post-apply 实测**: terminal `Change '2026-09-24-fix-test-constants-principle-form-migration' is valid` + info `skip_specs is set in .openspec.yaml: change declares no spec-level behavior changes, zero deltas accepted`
- [x] 4.2 `uv run python scripts/lint_no_dead_defensive.py` + `uv run python scripts/lint_no_source_field_drift.py` — verify: 两 lint gate `exit=0`(per CLAUDE.md §3 archive 前置条件)
  - **post-apply 实测**: `lint_no_dead_defensive: OK (no anti-patterns found)`;`lint_no_source_field_drift: OK (3 file(s) scanned, no violations)`
- [x] 4.3 `openspec archive 2026-09-24-fix-test-constants-principle-form-migration --yes` — verify: `openspec list --json` 不再出现该 change;archive 目录由 CLI 写入
  - **post-apply 实测**: terminal `Change '2026-09-24-fix-test-constants-principle-form-migration' archived as '2026-09-24-fix-test-constants-principle-form-migration'`;CLI 已写入 archive 目录;non-blocking warnings: (i) Why section 字符数 1000+ (proposal 详细论证需要,non-blocking);(ii) archive 时 4.3 自身尚未 mark (chicken-and-egg, archive 完才能 mark, post-archive mark 已补)