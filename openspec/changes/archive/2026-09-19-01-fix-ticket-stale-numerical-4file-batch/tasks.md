## 1. wayfinder spec delta（2 处）

- [x] 1.1 Edit `openspec/specs/wayfinder/spec.md` L122 narrative: `σ'(−3.5) ≈ 0.0284` → `σ'(−3.5) ≈ 0.02845`（5 位有效数字与 β_0 ≈ 1.035 精度风格统一）；verify by `grep -F "σ'(−3.5) ≈ 0.02845" openspec/specs/wayfinder/spec.md` returns 1 hit at L122
- [x] 1.2 Edit `openspec/specs/wayfinder/spec.md` L122 narrative: append 50-digit mpmath precision declaration `verified at 50-digit mpmath precision \`σ'(−3.5) = 0.02845302387973555984\``；verify by `grep -F "0.02845302387973555984" openspec/specs/wayfinder/spec.md` returns 1 hit at L122
- [x] 1.3 Edit `openspec/specs/wayfinder/spec.md` L126 Source 字段: `` `wayfinder/tickets/A4-1.md` `` → `` `wayfinder/tickets/A4-1.md`, `wayfinder/tickets/A4-2.md`, `wayfinder/tickets/A6b-1.md` ``（主反链 A4-1 首位保持）；verify by `grep -F "A4-1.md" openspec/specs/wayfinder/spec.md` returns ≥1 hit and L126 contains all three ticket refs comma-separated
- [x] 1.4 Run `python scripts/lint_no_source_field_drift.py` and verify exit=0（req-34 主反链首位 + backtick-wrapped + code-span atomic split 三项独立报错检查 pass）
- [x] 1.5 Amended by verifier cycle-09 F1+F2: Add two new Scenarios to `specs/wayfinder/spec.md` MODIFIED delta (delta file `openspec/changes/01-fix-ticket-stale-numerical-4file-batch/specs/wayfinder/spec.md`): (a) `MVPConfig.beta_initial default derives from spec closed-form β_min + (β_max−β_min)·σ(γ_init), NOT self-referential literal` — 钉死 test 守护 spec 闭式推导链而非字段字面值； (b) `σ'(−3.5) is guarded by a 50-digit mpmath pytest assertion (durable across archive of .audit/)` — 钉死 archive 后 pytest 必须持续守护 σ'(−3.5) 50-digit 闭式 + narrative 5-sig-fig 双断言

## 2. ticket 端 supersede annotation（3 处）

- [x] 2.1 Edit `wayfinder/tickets/A5-3.md` L62: 在 `~52° (估算)` 行后追加 `> (historical, ~52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)`（**仅追加，不删原值**）；verify by `grep -F "(historical, ~52° estimate" wayfinder/tickets/A5-3.md` returns 1 hit
- [x] 2.2 Edit `wayfinder/tickets/A1-1.md` L97: 在 `θ_Voronoi≈52°` 行后追加 `> (historical, θ_Voronoi≈52° estimate; superseded by spec req-11 L185 bisection 67.24° via change fix-math-consistency-audit-2026-08 Decision 1)`（**仅追加，不删原值**）；verify by `grep -F "(historical, θ_Voronoi≈52° estimate" wayfinder/tickets/A1-1.md` returns 1 hit
- [x] 2.3 Edit `wayfinder/tickets/A4-1.md` L58: 在 `β_0 ≈ 1.0` 行后追加 `> (historical, β_0 ≈ 1.0 estimate; superseded by spec req-7 L122 closed-form β_0 = 1.035060 via change fix-math-consistency-audit-2026-08 Decision 1)`（**仅追加，不删原值**）；verify by `grep -F "(historical, β_0 ≈ 1.0 estimate" wayfinder/tickets/A4-1.md` returns 1 hit
- [x] 2.4 Verify 原 stale 数字保留（lineage 不破坏）— `grep -F "~52°" wayfinder/tickets/A5-3.md` returns 1 hit; `grep -F "θ_Voronoi≈52°" wayfinder/tickets/A1-1.md` returns 1 hit; `grep -F "β_0 ≈ 1.0" wayfinder/tickets/A4-1.md` returns 1 hit; historical supersede annotation 紧邻 stale 数字

## 3. src/ 边界修改（1 文件）

- [x] 3.1 Edit `src/decompmoe/config.py:54`: `beta_initial: float = 1.0` → `beta_initial: float = 1.035`；verify by `grep -F "beta_initial: float = 1.035" src/decompmoe/config.py` returns 1 hit at L54
- [x] 3.2 Edit `src/decompmoe/config.py:50-53` docstring: **移除**原 `tracked as \`★ TODO\` in the plan §ST-02` 追踪，改写为 4 行 `per spec req-7 L122 closed-form β_0 = 1.035060 (verified at 50-digit mpmath: σ(γ_init=−3.5) = 0.029312230751356318865, β_0 = 1.0350601609682665718). Stored here so downstream code can read the canonical default without reaching into the \`beta\` module.` 风格；verify by `grep -F "tracked as \`★ TODO\`" src/decompmoe/config.py` returns 0 hits (TODO 追踪已清除) and `grep -F "1.0350601609682665718" src/decompmoe/config.py` returns 1 hit at L51-52
- [x] 3.3 Verify MVPConfig 字段集合 11 个不变 — `python -c "import dataclasses; from decompmoe.config import MVPConfig; print(len(dataclasses.fields(MVPConfig)))"` 输出 11

## 4. tests/ 边界修改（1 文件 + 1 新增 test function，amended by verifier F1 CRITICAL + F2 HIGH）

- [x] 4.1 Amended F1: Edit `tests/test_beta.py:38`: 从自指字段字面值 `assert MVPConfig().beta_initial == pytest.approx(1.035, abs=1e-6)` 改**从 spec 闭式推导** `expected = 0.1 + 31.9 * float(torch.sigmoid(torch.tensor(-3.5))); assert MVPConfig().beta_initial == pytest.approx(expected, abs=1e-3), f"actual={MVPConfig().beta_initial}"`。`abs=1e-3` 涵盖 narrative 截断 + 闭式计算容差；test 真正守护 spec req-7 L122 closed-form `β_0 = 0.1 + 31.9·σ(γ_init)` 数学推导链而非字段字面值
- [x] 4.2 Edit `tests/test_beta.py:37` docstring: `MVPConfig().beta_initial ≈ 1.035 (per spec req-7 L122 closed-form derivation; expected = 0.1 + 31.9·σ(γ_init=−3.5); proxy for γ₀ ≈ −3.5)`；verify by `grep -F "MVPConfig().beta_initial ≈ 1.035" tests/test_beta.py` returns 1 hit at L37
- [x] 4.3 Amended F2: 新增 `tests/test_beta.py::test_sigma_prime_gamma_init_health_check` 守护 spec L122 `σ'(−3.5) ≈ 0.02845` narrative + 50-digit mpmath `0.02845302387973555984` 双断言；test 必须**仅用 `torch.sigmoid` 计算**σ 而不是 `beta.inverse_temperature`（避免循环依赖，验证 σ 闭式本身）；verify by `grep -F "test_sigma_prime_gamma_init_health_check" tests/test_beta.py` returns 1 hit AND `grep -F "0.02845302387973555984" tests/test_beta.py` returns ≥1 hit
- [x] 4.4 Run `uv run pytest tests/test_beta.py -v` and verify 全 `test_beta.py` tests passed（含 `test_beta_param_init_default` 改后 + `test_sigma_prime_gamma_init_health_check` 新增）

## 5. 验证与提交

- [x] 5.1 LF 校验：每个 Edit 后 `git diff --stat` 验证行数变化符合预期（spec/wayfinder/spec.md ≈ +3 −1；ticket A5-3.md +1；A1-1.md +1；A4-1.md +1；config.py ≈ +3 −3；test_beta.py ≈ +2 −2；spec/decompmoe-skeleton/spec.md ≈ +4 −2）；按 `[[windows-edit-crlf-pitfall]]` memory 必要时 `sed -i 's/\r$//'`
- [x] 5.2 Run `uv run pytest tests/ -v` and verify 142 passed（既有 141 + modified 1 `test_beta_param_init_default`）无 regression
- [x] 5.3 Run `python scripts/lint_no_dead_defensive.py` and verify exit=0；Run `python scripts/lint_no_source_field_drift.py` and verify exit=0
- [x] 5.4 spec/code consistency spot-check 7 项：
  - `MVPConfig().beta_initial == pytest.approx(1.035, abs=1e-6)` ✓
  - `MVPConfig().beta_initial != 1.0`（旧 stale 值已被替换）✓
  - `len([f.name for f in dataclasses.fields(MVPConfig)]) == 11` ✓
  - `wayfinder/tickets/A5-3.md` L62 含 `~52° (估算)` + historical supersede annotation ✓
  - `wayfinder/tickets/A4-1.md` L58 含 `β_0 ≈ 1.0` + historical supersede annotation ✓
  - `wayfinder/tickets/A1-1.md` L97 含 `θ_Voronoi≈52°` + historical supersede annotation ✓
  - `openspec/specs/wayfinder/spec.md` L122 narrative 含 `σ'(−3.5) ≈ 0.02845`（5 位有效数字）+ 50-digit mpmath 声明 ✓
  - `openspec/specs/wayfinder/spec.md` L126 Source 字段含 `A4-1`, `A4-2`, `A6b-1` 三个 backtick-wrapped ticket（A4-1 首位）✓
- [x] 5.5 50-digit mpmath 数值独立复核（重用 `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/verify_numerical_claims.py`）：运行 `uv run python <verify_numerical_claims_path>` and verify 15/15 PASS
- [x] 5.6 单 commit on `dev`: `git add openspec/specs/wayfinder/spec.md wayfinder/tickets/A5-3.md wayfinder/tickets/A1-1.md wayfinder/tickets/A4-1.md src/decompmoe/config.py tests/test_beta.py && git commit -m "fix(spec,ticket,code): close cycle-5/6/7 MEDIUM findings — ticket stale numerical 6-file batch (A5-3 L62 + A1-1 L97 + A4-1 L58 + MVPConfig L54 + test_beta L38 + req-7 L122/L126)"`
- [x] 5.7 archive 准备: Run `openspec validate 01-fix-ticket-stale-numerical-4file-batch --type change --strict` and verify PASS（无 "Unknown item" 或 MODIFIED-but-not-found warnings）；满足 CLAUDE.md §3 "`/opsx:archive` 前置条件"（lint gate exit=0）

## 6. verifier cycle-09 amendments（F1 CRITICAL + F2 HIGH + F3 HIGH）

- [x] 6.1 F3: Edit `openspec/specs/decompmoe-skeleton/spec.md:471,473`: narrative `β_initial == 1.0` / `β_initial = 1.0` → `β_initial ≈ 1.035`（4-sig-fig narrative；per wayfinder spec req-7 L122 closed-form `β_0 = 0.1 + 31.9·σ(γ_init)` with `γ_init ≈ −3.5`; 50-digit mpmath `β_0 = 1.0350601609682665718`）；verify by `grep -F "β_initial ≈ 1.035" openspec/specs/decompmoe-skeleton/spec.md` returns 2 hits (L471 + L473) AND `grep -F "β_initial == 1.0" openspec/specs/decompmoe-skeleton/spec.md` returns 0 hits (旧 stale 1.0 narrative 已清除)
- [x] 6.2 F1: Edit `tests/test_beta.py:38` `test_beta_param_init_default`: 从自指字段字面值改 closed-form 推导 `expected = 0.1 + 31.9 * float(torch.sigmoid(torch.tensor(-3.5))); assert MVPConfig().beta_initial == pytest.approx(expected, abs=1e-3), f"actual={MVPConfig().beta_initial}"`；verify by `grep -F "0.1 + 31.9 \* float(torch.sigmoid" tests/test_beta.py` returns 1 hit AND `grep -F "pytest.approx(1.035, abs=1e-6)" tests/test_beta.py` returns 0 hits (旧自指断言已清除)
- [x] 6.3 F2: 新增 `tests/test_beta.py::test_sigma_prime_gamma_init_health_check` 函数（位于 `test_grad_gamma_bound` 之前或合适位置）：用 `torch.sigmoid(−3.5) * (1 − torch.sigmoid(−3.5))` 计算 σ'(−3.5)，双断言 (a) `abs=1e-15` 钉 50-digit `0.02845302387973555984` + (b) `abs=1e-5` 钉 narrative `0.02845`；verify by `grep -F "test_sigma_prime_gamma_init_health_check" tests/test_beta.py` returns 1 hit AND `grep -F "0.02845302387973555984" tests/test_beta.py` returns ≥1 hit
- [x] 6.4 Run `uv run pytest tests/test_beta.py -v` and verify 9+ passed（`test_beta.py` 全部 tests passed，含 amended `test_beta_param_init_default` 改后 + 新增 `test_sigma_prime_gamma_init_health_check`）；verify by `uv run pytest tests/ -v` returns 全绿（含 skeleton spec L471/473 amendment 后所有 tests）
- [x] 6.5 Amended commit on `dev`: `git add openspec/specs/wayfinder/spec.md openspec/specs/decompmoe-skeleton/spec.md tests/test_beta.py && git commit -m "fix(spec,test): amend verifier cycle-09 F1 CRITICAL + F2 HIGH + F3 HIGH — test_beta_param_init_default closed-form rewrite + test_sigma_prime_gamma_init_health_check + skeleton spec req-21 narrative sync"`
- [x] 6.6 Amended planning artifact commit: `git add openspec/changes/01-fix-ticket-stale-numerical-4file-batch/proposal.md openspec/changes/01-fix-ticket-stale-numerical-4file-batch/design.md openspec/changes/01-fix-ticket-stale-numerical-4file-batch/tasks.md openspec/changes/01-fix-ticket-stale-numerical-4file-batch/specs/decompmoe-skeleton/spec.md openspec/changes/01-fix-ticket-stale-numerical-4file-batch/specs/wayfinder/spec.md && git commit -m "docs(openspec): amend 01 planning artifacts — verifier F1/F2/F3/F5/F6 amendments + Decision 6/7/8 + decompmoe-skeleton MODIFIED delta"`