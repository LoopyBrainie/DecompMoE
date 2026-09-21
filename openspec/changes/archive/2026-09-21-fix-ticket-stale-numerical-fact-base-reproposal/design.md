# Design: Fix Ticket Stale Numerical — Fact-Base Re-proposal

## Context

The original change `01-fix-ticket-stale-numerical-4file-batch` closed three MEDIUM findings (cycle-5 θ_Voronoi 估算 15.24° drift, cycle-6 MVPConfig.beta_initial 3.39% drift, cycle-7 A4-1 ticket β_0 ≈ 1.0 3.39% drift) plus two LOW spec deltas (cycle-7 σ' precision + Source-field补齐). The actual ground-truth state lives in git commits:

```
adf41ef fix(spec,ticket,code): close cycle-5/6/7 MEDIUM findings — 6-file batch
2d7e85a fix(spec,test): amend verifier cycle-09 F1 CRITICAL + F2 HIGH + F3 HIGH
        — test_beta_param_init_default closed-form rewrite +
        test_sigma_prime_gamma_init_health_check + skeleton spec req-21 narrative sync
229016f sync(specs): merge change 01 delta specs into live main specs
11bebc6 chore(opsx): archive 01-fix-ticket-stale-numerical-4file-batch
```

The audit-verification snapshot at `.audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/` is the propose-phase artifact. Three drift dimensions versus the final live state:

| 维度 | snapshot 现状 | 实际终态 |
|---|---|---|
| `audit-verification.md` 行号引用 | L132（4 处） | L36 |
| wayfinder spec.md 新增 Scenarios | 3 个 | 5 个（+2 verifier F1 CRITICAL） |
| 批次命名口径 | 目录"4-file" / 正文"5-file" | commit "6-file batch" |

This re-proposal captures the verified ground truth as a fresh OpenSpec change so the canonical artifacts (proposal/design/specs/tasks) reflect the actual final state. Apply phase is **no-op** (files already match).

## Goals / Non-Goals

**Goals:**
- Establish canonical OpenSpec artifacts for the original 01 fix that reflect the verified ground truth
- All numeric anchors (β_0 = 1.0350601609682665718, σ'(−3.5) = 0.02845302387973555984, θ_Voronoi(16,16) = 67.24°) match 50-digit mpmath
- Lazy decay-safe: spec/test pair guards against self-referential literal trap (verifier F1 CRITICAL root cause)
- Archive-durable: σ' guard test lives in `tests/` (durable), not `.audit/` (drop-on-archive)

**Non-Goals:**
- 不动 `src/decompmoe/beta.py` 模块级常量（`BETA_MIN` / `BETA_MAX` 保持 `Final[float]` 不变）
- 不引入新 cfg 形参或新 MVPConfig 字段
- 不修改 `tests/test_sphere.py` / `tests/test_config.py`
- 不动 wayfinder ticket 其他文件（仅 A5-3 + A4-1 + A1-1 三处加 supersede annotation）
- 不重写 ticket 原 stale 数字（仅追加注释）
- 不写 spec.md L536 req-24 σ' precision（同型 finding 但 cycle-7 finding 2 范围外；后续 audit cycle 单独立项）
- 不动 .audit/audit-verification/ 目录本身（snapshot 保留作为变更历史 trail）
- 不修复 snapshot 残留的 L132 错引（属 audit 流程级问题，需独立 lint gate 改善，非本 change scope）

## Decisions

### Decision 1: Apply 阶段为 no-op（re-sync 而非 re-apply）

**Choice**: Apply 阶段只重新对齐 OpenSpec 制品与 repo 现状，不写新代码。

**Rationale**: 实际 repo state 已经包含 fix（git `adf41ef` + `2d7e85a` + `229016f` 已 merge 到 `dev`）。apply 写代码会产生 conflict-on-apply 错误（value 已匹配）。OpenSpec 重新 propose 的价值在于：让 canonical artifacts（spec/task/可机读）记录的是 ground truth，不是 snapshot drift。

**Alternatives considered**:
- (a) Apply 实际重写文件 —— 拒绝：会产生 conflict；ground truth 已匹配
- (b) 不走 apply 直接 archive —— 拒绝：违反 opsx 标准流程（archive 要求 apply 完成）
- (c) 走 apply 验证但不改 —— 选；`git apply --check` 应 no-op，archive 走标准流程

### Decision 2: spec delta 包含 cycle-09 verifier F1 CRITICAL 增补的 2 个 Scenarios

**Choice**: spec delta 不仅含 snapshot 描述的 3 个 Scenarios，还含 cycle-09 verifier F1 CRITICAL 增补的 2 个：
- "MVPConfig.beta_initial default derives from spec closed-form β_min + (β_max−β_min)·σ(γ_init), NOT self-referential literal"（防 self-referential literal trap）
- "σ'(−3.5) is guarded by a 50-digit mpmath pytest assertion (durable across archive of `.audit/`)"（archive-durable guard）

**Rationale**: 这 2 个 Scenario 是 cycle-09 amend `2d7e85a` 落地的核心；snapshot 因是 propose-phase 快照，未含 amend。re-proposal 必须 capture amend 终态，否则失去"事实基础"承诺。archive 完成后，`openspec/specs/wayfinder/spec.md` L140/145 即这 2 个 Scenario 的落地位置。

**Alternatives considered**:
- (a) 只含 snapshot 描述的 3 个 Scenarios —— 拒绝：失去 amend 后 ground truth
- (b) 含 5 个但显式标注哪些是 amend —— 选；spec delta 文件正文简洁标注即可

### Decision 3: 行号引用统一改 L36（snapshot drift 修复）

**Choice**: proposal.md / design.md / tasks.md 中 4 处 `audit-verification.md L132` 全部改 `L36`。

**Rationale**: 实际 verbatim 字符串 `ticket A5-3 L62 + A1-1 L97 θ_Voronoi 估算漂移 15.24°` 在 `audit-verification.md` L36（cycle-5 finding 一句话复核 blockquote）。L132 是 follow-up 段，不是 verbatim 持有者。archive 终态已修；本 re-proposal 同步修。

**Alternatives considered**:
- (a) 保留 L132 错引 —— 拒绝：fact-verification 报告已锁定为事实错误
- (b) 改 L36 —— 选；与 archive 一致

### Decision 4: 不在 spec.md 中展开 spec L536 req-24 σ' precision

**Choice**: 本 change 不修改 req-24 L536（仍 `σ'(−3.5) ≈ 0.0284`）。

**Rationale**: req-24 L536 是与 cycle-7 finding 2 同型但**跨 Requirement** 的 drift（cycle-7 finding 2 报告的 scope 是 req-7 L122）。本 change scope 锁定 cycle-7 finding 2 原始范围（req-7 L122）；req-24 L536 应在后续 audit cycle 中作为同型 finding 单独提案修复。

**Alternatives considered**:
- (a) 同时修 req-7 L122 + req-24 L536 —— 拒绝：scope 蔓延；spec L536 应走独立 audit cycle
- (b) 只修 req-7 L122 —— 选；与 cycle-7 finding 2 原始 scope 对齐

### Decision 5: ticket supersede annotation 格式沿用 cycle-9 fix `fix-openspec-doc-bugs` Decision 7 canonical

**Choice**: 3 处 ticket supersede annotation 格式：`> (historical, <原值> estimate; superseded by spec req-<N> L<line> <spec truth> via change <change-name> Decision N)`。

**Rationale**: 与 cycle-9 fix `fix-openspec-doc-bugs` Decision 7 处理的 ticket A6a-2 L63 1/128 stale annotation 形式一致；lineage 可读性 + future reader 一眼能区分 stale vs current。

**Alternatives considered**:
- (a) 删除原 stale 数字改 spec 真相 —— 拒绝：破坏 ticket 决策 trail（reader 无法追溯当时为何写 ~52° / ≈ 1.0）
- (b) 仅追加不删除 + 加 annotation —— 选；与 cycle-9 canonical 对齐

## Risks / Trade-offs

- **[Risk]** Apply 阶段写文件与 git 已 merge 内容产生冲突。**Mitigation**: 先 `git apply --check` 验证无 diff；如产生 conflict，apply 阶段用 `--3way` merge 解决
- **[Risk]** spec delta 5 个 Scenarios 的篇幅超出 cycle-5/6/7 原始 cycle-09 verifier amend 范围，被审 reviewer 质疑 scope 蔓延。**Mitigation**: proposal.md "Why" 段已显式说明本 change 是 re-proposal 而非新增 scope；spec delta 严格 match live spec.md L136-L153 现状
- **[Risk]** 4 处行号改 L36 与 snapshot 漂移历史冲突，未来 reader 难以追溯"snapshot 当时为何用 L132"。**Mitigation**: 此风险由 snapshot 自身保留承担；re-proposal 不承担"snapshot drift 历史注释"职责
- **[Risk]** test_beta.py 双断言（50-digit + narrative）与 governance req-gov-1 第 2 条 "浮点闭式 MUST pytest.approx" 可能误读。**Mitigation**: 双断言的语义不同 — `0.02845302387973555984 abs=1e-30` 是 FP-exact 50-digit mpmath literal 钉值（`diff = 0.0` 因 float64 round-trip 验证）；`0.02845 abs=1e-5` 是 L122 narrative 5-sig-fig 精度披露；两者互补而非冗余

## Migration Plan

Apply 阶段步骤：

1. `openspec validate fix-ticket-stale-numerical-fact-base-reproposal --strict` —— lint gate
2. `git apply --check` 验证 OpenSpec-generated patch 与 repo state 无 diff
3. 如 `git apply --check` 0 命中 → apply no-op（仅 archive 走流程）
4. 如 `git apply --check` 有 diff → `--3way` merge；merge 后必须 `git diff` 复核无意外变更
5. `uv run pytest tests/ -v` 全绿（验证 live state 196 passed 不退化）
6. `python scripts/lint_no_dead_defensive.py` + `python scripts/lint_no_source_field_drift.py` 双 lint gate exit=0
7. 单 commit on dev: `chore(opsx): re-propose fix-ticket-stale-numerical-fact-base-reproposal`（仅 opsx metadata，无 src 变更）

Archive 阶段：`/opsx:archive` 走标准流程，lint gate 必须 `exit=0`。

## Open Questions

- **Future audit**: cycle-9/12/13 也有 MEDIUM ticket stale findings。cycle-9 f_threshold 1/128 stale 已被 spec L245 supersede（实际不是 stale，是 cycle-9 finding 错判），但 spec L245 supersede 本身需独立审计确认。cycle-12 (ticket A8-2 covariance) + cycle-13 (ticket A6b-1 N_e=64) 同源 pattern 是否也需 batch re-proposal？本 change 明确只 re-propose cycle-5/6/7 + cycle-7 finding 2/3 + cycle-09 amend；不预先承诺 follow-up 范围
- **snapshot drift 治理**: 本 re-proposal 修 L36 但不修"audit snapshot 流程未 lint L132 错引"——后者需独立 audit-tooling change（建议 audit verification loop 加 `grep -F "L132" .audit/audit-verification/opsx-changes/*/proposal.md` 应 0 命中 的 lint gate）
- **OpenSpec change 名冲突**: 原 `01-fix-ticket-stale-numerical-4file-batch` 已 archived，本 change 取名 `fix-ticket-stale-numerical-fact-base-reproposal`。若 opsx 后续 rename archived changes，需复核 name 语义是否仍合理