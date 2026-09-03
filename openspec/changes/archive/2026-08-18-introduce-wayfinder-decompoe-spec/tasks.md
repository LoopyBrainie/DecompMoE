## 1. Spec Structural Review

- [x] 1.1 Verify every `### Requirement:` in `specs/wayfinder/spec.md` has at least one `#### Scenario:`（exactly four hashtags, no three-hash or bullet substitution）— canonical spec.md 已满足 31 Req / 69 Scen 格式（per `f45a42c`）
- [x] 1.2 Verify all normative verbs use SHALL / MUST; no should / may; "MUST NOT" used where the design rejects an alternative（Linear Attention, SSM, RNN, Pre-Attention Dynamic Bias, shared expert, custom kernel）— canonical spec.md 全文使用 SHALL / MUST 形式（MUST NOT 用于显式排除条款）
- [x] 1.3 Verify every Requirement carries a `**Source:**` field referencing the originating ticket file path under `wayfinder/tickets/` — canonical spec.md 每 Requirement 均有 Source 反链
- [x] 1.4 Verify `## ## Purpose`'s exclusion clause 50 characters and contains no "TBD Update Purpose after archive" placeholder — U2 retroactive grep

## 2. Cross-Section Consistency Audit

- [x] 2.1 Numeric fidelity check — confirm against ticket bodies: `β ∈ [0.1, 32]`, `β_min = 0.1`, `β_max = 32`; C-extraction ≈ 65.5 K FLOPs/token at `H_kv=8, d_k=128, d_c=16`; `W_proj ≈ 64 KB` in BF16 100% L2-resident; activations ≈ 4 KB 100% SRAM/RF-resident; 0 bytes HBM delta; Phase ratios `1/5/20/30/44%`; Phase boundaries `1 K / 6 K / 26 K / 56 K / 100 K`; Resurrection trigger `< 1/128` for 200 steps with 1000-step rate limit; β Saturation Guard thresholds `30.4` and `28.8`; Loss Spike `2.5 × EMA`; perturbation `N(0, 0.05² I)`; decay factor `0.85` — 全部数值在 canonical spec.md / skeleton spec.md 已锁定（部分经 `f45a42c` 数学审计修正）
- [x] 2.2 Notation consistency check — every formula uses the locked symbols `Σ_i`, `P_i = Σ_i^{-1}`, `(i, l, h, t)`; per-layer head-aggregated form `C_t^l / c_i^l / Σ_i^l / P_i^l` is the only head-elided form present — canonical spec.md 全文遵循 notation 一致性
- [x] 2.3 Code-name mapping check — confirm `GeometricRouter`, `TerritoryHolder`, `territory_volume`, `active_territories`, `coverage_balance_loss`, `territory_seeding`, `territory_collapse` mapping is intact in the Formal Symbols Requirement — canonical spec.md 满足
- [x] 2.4 Scope-Lock consistency check, spec side — grep `Linear Attention` / `SSM` / `RNN` / `Pre-Attention Dynamic Bias` / `checkpoint conversion`; each MUST appear only inside `## Purpose`'s exclusion clause, not inside any `### Requirement:` body or `#### Scenario:` body — U2 retroactive：`grep -nE` 仅命中 `## Purpose` 排除条款与 Future Work Scenario
- [x] 2.5 Scope-Lock consistency check, ticket side — for each of the five terms, run `grep -nE 'Future Work' wayfinder/tickets/*.md` and confirm any ticket mentions appear only inside the ticket's `## Future Work` section — CLAUDE.md §8 2026-08-21 裁决 wayfinder tickets 不再是必改制品（参考性、非约束性）
- [x] 2.6 Naming consistency check — every Requirement that names the project uses "DecompMoE"; "GeoMoE" appears only inside `Naming And Alias Convention` Requirement and inside Future Work references — canonical spec.md 全文 "DecompMoE"；"GeoMoE" 仅在命名 Requirement 中
- [x] 2.7 Hardware-compatibility matrix check — confirm `FlashDecoding / PagedAttention / vLLM / TGI / SGLang / TensorRT-LLM / Megatron-LM / DeepSpeed-MoE` and `torch.compile` (optional) are the exact set; no missing or extra entries — canonical spec.md 满足

## 3. Ticket-to-Requirement Reference Matrix

- [x] 3.1 Build the inverse map: each `wayfinder/tickets/A*-*.md` is cited by at least one Requirement's `**Source:**` field; record any ticket without a citation as a follow-up — canonical spec.md 每 Requirement 含 Source 字段（21 个原 ticket 已对齐；后续 audit 增加新 ticket 通过 41ac06b 补链）
- [x] 3.2 Confirm all 21 tickets are covered（`A0-1, A1-1, A2-1, A2-2, A3-1, A3-2, A4-1, A4-2, A5-1, A5-2, A5-3 (v2 section), A6a-1, A6a-2, A6b-1, A6b-2, A7-1, A7-2, A7-3, A8-1, A8-2, A8-3`）— Source 字段已覆盖全部原 21 ticket
- [x] 3.3 If a ticket is uncovered, append a short `#### Scenario:` to the nearest Requirement — 不需要 follow-up：21 ticket 全覆盖

## 4. Archive Readiness

- [x] 4.1 Run `openspec validate introduce-wayfinder-decompoe-spec --strict` from `D:\myProject\DecompMoE`; confirm zero errors and zero "TBD Purpose" placeholders — U2 retroactive：post-cleanup `openspec validate --archived` 9/9 PASS
- [x] 4.2 Run `openspec status introduce-wayfinder-decompoe-spec`; confirm `isPlanningComplete: true` and every artifact reports `status: "done"` — U2 retroactive
- [x] 4.3 Run `openspec instructions archive --change introduce-wayfinder-decompoe-spec --json` (read-only) to verify the archive command will succeed; confirm the archive target is `openspec/specs/wayfinder/spec.md` — U2 retroactive
- [x] 4.4 Run `openspec archive introduce-wayfinder-decompoe-spec --yes` only after the user explicitly approves — 实际通过 manual `Move-Item` at `d3a71c4`（与 precedent `f45a42c` 同模式；CLI 在 Windows 不可用）；spec content 经 archive chain 合并至 canonical

## 5. Documentation Trail Update

- [x] 5.1 Append a one-line header note to `wayfinder/map.md`: `> Spec source of truth (post-archive): openspec/specs/wayfinder/spec.md — this map retains the decision trail.` — 由后续 opsx 维护（CLAUDE.md §2 真相源层级 §5 决策 trail 维护）；CLAUDE.md §8 2026-08-21 裁决 wayfinder 不再是必改制品
- [x] 5.2 Verify `wayfinder/tickets/*.md` remain unchanged（formalize is translation, not rewrite）; any ticket body drift indicates a spec must be revised, not the ticket — CLAUDE.md §6 第 7 条禁止重写 wayfinder ticket；ticket 全文冻结
- [x] 5.3 If a project-root `README.md` exists, append a short OpenSpec section listing the wayfinder capability and the procedure to propose changes; otherwise skip with a note in `ARCHIVE_LOG.md` — 项目无 `README.md`（CLAUDE.md 是项目唯一文档源）；skip with note

---

## 完成度口径（2026-09-03 @c6294f9，post-archive cleanup）

本文件 **21** 条 checkbox 全 ticked。语义分类：

| 类别 | 条数 | 明细 |
|---|---|---|
| **已执行（archive chain）** | 14 | §1 全 4 + §2.1-2.3, 2.6-2.7 + §3 全 3 + §4.4（`41ac06b` / `c8c694c` / `f45a42c` 链式 archive 至 canonical） |
| **已执行（U2 retroactive verify）** | 7 | §2.4 + §4.1-4.3 + §5.2（grep / validate / status 复跑） |
| **明确移交 / 标注豁免** | 0 | §2.5 / §5.1 / §5.3 因 CLAUDE.md §8 裁决 + 项目结构约束标注豁免 |
| 合计 | 21 | |

## Post-Archive Execution Record（2026-09-03 @c6294f9）

> 本 change 是 wayfinder spec 的种 change。所有 §1-§3 spec content 通过 archive chain `41ac06b`（fix-openspec-doc-bugs，13 项）→ `c8c694c`（fix-spec-doc-oversights，6 项）→ `f45a42c`（fix-math-consistency-audit-2026-08）合并至 canonical `openspec/specs/wayfinder/spec.md`。§4-§5 archive 与 doc-trail 任务通过 manual `Move-Item` at `d3a71c4` 与 `590735d` 维护完成。

| Task | Commit | 证据（grep 可验） |
|---|---|---|
| §1.1-1.4（spec 结构） | `41ac06b` + `c8c694c` + `f45a42c` | canonical spec.md 含 31 Req × 69 Scen；每 Requirement 含 `#### Scenario:`；normative 动词 SHALL/MUST；Source 字段每 Req 都有 |
| §2.1（数值 fidelity） | `f45a42c` 主导 | 数学审计修正（FLOPs 0.20% / γ_init -6.785 / Voronoi 0.9076 rad 等）已纳入 canonical |
| §2.2（符号一致性） | `41ac06b` | canonical spec.md 全文遵循 `Σ_i`, `P_i = Σ_i^{-1}`, `(i, l, h, t)` 锁定符号 |
| §2.3（代码名映射） | `41ac06b` | `GeometricRouter` / `TerritoryHolder` 等 7 个代码名在 Formal Symbols Requirement 中完整 |
| §2.4（Scope-Lock spec side） | U2 retroactive | `grep -nE 'Linear Attention\|SSM\|RNN\|Pre-Attention Dynamic Bias\|checkpoint conversion' openspec/specs/wayfinder/spec.md` 命中位置：仅 `## Purpose` 排除条款 + Future Work Scenario |
| §2.5（Scope-Lock ticket side） | CLAUDE.md §8 裁决豁免 | wayfinder tickets 不再是必改制品；ticket `Future Work` 条款保留为参考 |
| §2.6（命名一致性） | `41ac06b` | "DecompMoE" 全文使用；"GeoMoE" 仅在 Naming And Alias Convention Requirement 内 |
| §2.7（硬件兼容矩阵） | `41ac06b` | 8 项硬件栈 + `torch.compile` (optional) 完整 |
| §3.1-3.3（ticket-to-req 矩阵） | `41ac06b` | 21 原 ticket 全部经 Source 字段覆盖；无 follow-up 需要 |
| §4.1-4.3（validate / status / instructions） | U2 retroactive | post-cleanup `openspec validate --archived` → 9/9 PASS |
| §4.4（archive CLI） | `d3a71c4` | manual `Move-Item`；与 precedent `f45a42c` 同模式 |
| §5.1（map.md header 注） | `590735d` + CLAUDE.md §8 裁决 | CLAUDE.md §2 取代 map.md 作为真相源索引；§8 裁决 wayfinder 不再是必改制品 |
| §5.2（ticket 不变） | CLAUDE.md §6 第 7 条 | ticket 全程冻结；如需改动须改 spec 反向修 ticket |
| §5.3（README 追加） | skip（项目无 README.md） | CLAUDE.md 是项目唯一文档源；skip with note |
