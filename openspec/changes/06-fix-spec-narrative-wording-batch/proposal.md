# Proposal: Fix Spec Narrative Wording Batch (NAR-1/2 + NAR-3 verify)

## Why

`.audit/audit-verification/` 元审计循环 (2026-09-18/19) 完成 8+1+1 finding 的三轴 (α+β+γ) 复核后, 锁定 3 条**叙事层 wording drift** finding 同源 pattern (per `change 06` entry in `.audit/audit-verification/opsx-changes/README.md`). 本 change 关闭这 3 条 LOW 评级 finding, 是 cycle-1/2/7 三 cycle 叙事层 wording 微调的最终 closure.

事实基础 (per 2026-09-22 事实验证):
- **NAR-1** (cycle-1 finding 1, LOW, verify-22/23/24 三轴 fully-verified, audit file `audit-verification/audit-verification.md` L1624 `verify-22 finding cycle-1-finding-1 axis-α` 起): spec L12 `MUST preserve **GeoMoE**` 与 ticket `A0-1.md` L29 叙事略有不一致 — spec "preserve" 暗示 GeoMoE 曾是规范名、后被降级, ticket 真实记录 GeoMoE 从未被选为规范名 (CLAUDE.md §1 amendment 行为升格为 alias). fact 三方一致, 仅 wording 略有不精确.
- **NAR-2** (cycle-2 finding 1, LOW, verify-25/26/27 三轴 fully-verified, audit file L1849 `verify-25 finding cycle-2-finding-1 axis-α` 起): spec L24 `subscript convention (i, l, h, t)` 的 `h` 取值域未显式声明. ticket A1-1 L42 显式 `h ∈ 1..H`, spec req-5 L64 实际归一化用 `H_kv` (per-KV-head). MVP 当前 `H_kv = H = 8` 不咬人 (req-11 L211), 但**未来启用 GQA 时 h 域歧义点**.
- **NAR-3** (cycle-7 finding 3, LOW, verify-8 axis-β `audit-verification.md` L455-463 段): spec L126 Source 字段需含 A4-2 + A6b-1 反链 (当前 live spec L126 **已含 3 ticket**, 实证 baseline 已满足, 本 change NAR-3 决议降级为 "lint gate verify-only", 不再 modify live spec).

## What Changes

### wayfinder spec delta（2 项 wording 微调 + 1 项 verify-only）

1. **NAR-1** (cycle-1 finding 1 closure) —— 编辑 `openspec/specs/wayfinder/spec.md` Requirement "Naming And Alias Convention" L12 主体: `MUST preserve **GeoMoE**` 改 `MUST adopt **GeoMoE** as a documented alias (per CLAUDE.md §1 project-level amendment; GeoMoE was never previously a canonical name — it is a deliberate alias upgrade, not a downgrade)`. **不变**: (a) DecompMoE canonical; (b) Scenario L16-18 verbatim; (c) Source 字段 L14; (d) `<a id="req-1"></a>` 锚点.

2. **NAR-2** (cycle-2 finding 1 closure + cross-cycle closure 加固) —— 编辑 `openspec/specs/wayfinder/spec.md` Requirement "Formal Symbols And Code Naming" L24 主体: 在 `subscript convention (i, l, h, t)` 之后追加域声明 `(i ∈ 1..N_e, l ∈ 1..L, h ∈ 1..H_kv, t ∈ 1..S)` + 解释 `h` 枚举 KV-head 轴 (per req-5 cross-head mean), MVP 阶段 `H_kv = H = 8` (GQA 退化 MHA per req-11 L211), 未来启用真 GQA 时约定仍守 `H_kv`. **不变**: (a) elide h 规则 (L24 后段); (b) Source 字段 L26; (c) `<a id="req-2"></a>` 锚点.

3. **NAR-3** (cycle-7 finding 3 closure, **verify-only**) —— 不 modify spec.md L126 Source 字段 (live spec **已含** 3 ticket: A4-1 + A4-2 + A6b-1, per `Select-String` 实测 2026-09-22). NAR-3 决议降级为: `openspec validate 06-fix-spec-narrative-wording-batch --type change --strict` PASS + lint gate `python scripts/lint_no_source_field_drift.py` PASS + grep 实证 L126 已含 3 backtick-wrapped ticket. **不变**: (a) spec L126 当前状态; (b) `<a id="req-7"></a>` 锚点; (c) ticket A4-2 + A6b-1 (CLAUDE.md §6 第 7 条 + §8 tickets reference-only).

### 其它 spec delta（无）

skeleton spec.md + governance spec.md 不涉及本批 finding 改动范围 (CLAUDE.md §3 governance 反链 `CLAUDE.md` 而非 `wayfinder/tickets/<ID>.md`).

### src/ 边界修改（无）

纯 wording 微调 (NAR-1/2) + verify-only (NAR-3), 不动 src/ 任何文件. 现有 197 tests (per `uv run pytest tests/ --collect-only -q` 2026-09-22 实测) 全绿即证明无回归.

### tests/ 边界修改（无）

不新增 test, 不重写既有 test (wording 微调不触发 spec Scenarios 变化).

### nothing else

不动 wayfinder tickets; 不动 MVPConfig / src/ 任何模块; 不动 contracts.py / gating.py / loss.py / experts.py / viz.py / sphere.py / extraction.py / beta.py / schedule.py / safeguards.py / metrics.py; 不动 `<a id="req-1">` / `<a id="req-2">` / `<a id="req-7">` 3 处锚点; 不动其它 6 锚点 (req-3 ~ req-9).

## Capabilities

### Modified Capabilities

- `wayfinder` (2 处 wording delta + 1 处 verify-only):
  - **MODIFIED** Requirement "Naming And Alias Convention" (L12): `preserve` → `adopt (per CLAUDE.md §1 ...; not previously a canonical name)` (NAR-1)
  - **MODIFIED** Requirement "Formal Symbols And Code Naming" (L24): 追加 `(i ∈ 1..N_e, l ∈ 1..L, h ∈ 1..H_kv, t ∈ 1..S)` 域声明 + KV-head 轴 cross-reference (NAR-2)
  - **(no spec delta)** Requirement "Beta Parameterization And Numerical Stability" Source 字段: 已满足 cycle-7 finding 3 closure (NAR-3 verify-only)

## Impact

- **Affected code**: 无 (surgical no-op per CLAUDE.md §3)
- **Affected tests**: 无
- **Affected APIs / dependencies**: 无
- **Risk**:
  - **NAR-1 wording 微调**: doc-level, 不引入新约束. Mitigation: spec L18 Scenario "Canonical reference resolution" 仍 verbatim 钉死 DecompMoE primary + GeoMoE secondary alias
  - **NAR-2 h 域声明**: 与 ticket A1-1 L42 `1..H` wording 不完全 verbatim, 但**不冲突** (ticket pre-A2-2 阶段, spec post-A2-2 阶段, req-5 L64 已用 H_kv 钉死). Mitigation: 显式 cross-reference 解释 H_kv vs H 关系
  - **NAR-3 verify-only**: live spec L126 已满足, lint gate 应 PASS. Mitigation: `grep "A4-2.md\|A6b-1.md" openspec/specs/wayfinder/spec.md` 实证
  - **anchor 100% 覆盖**: 2 锚点 (req-1, req-2) 不动 + req-7 不动. Mitigation: lint + grep 实证
- **Source**: 3 条 finding 来自 `.audit/audit-verification/audit-verification.md` 三轴 fully-verified 闭环:
  - NAR-1: verify-22/23/24 cycle-1 LOW (audit file L1624+ section)
  - NAR-2: verify-25/26/27 cycle-2 LOW (audit file L1849+ section)
  - NAR-3: verify-8 cycle-7 LOW finding 3 (audit file L455-463 section) — 已通过 live spec 状态满足
- **并行 change 隔离**: 与 `01-fix-ticket-stale-numerical-4file-batch/` (cycle-5/6/7 数值层 finding) 与 `09-fix-claude-md-ticket-advisory-boundary/` (CLAUDE.md §8 amendment) 隔离无重叠