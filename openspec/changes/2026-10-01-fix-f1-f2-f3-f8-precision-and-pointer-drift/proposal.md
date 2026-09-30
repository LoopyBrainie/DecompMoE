# 修复 F1/F2/F3/F8 — 数值守卫容差失真 + 残留 line-drift 指针

## Why

Python reviewer 对本 session 修复内容（commit `f0b3aa2` / `b272787` / `a036a15` / `315065e`）做全面 review 后判定**零回归**，另报 9 条 findings。本 change 处理其中 4 条，主题一致：**「spec 声称的数值精度」与「pytest 实际施加的容差」不相符**，以及**裸行号指针漂移**。

共同失败模式：spec 写「50 位 mpmath 验证」、测试写「`abs=1e-4`」。二者都不是错，但**放在一起就使守护失效** —— 声称的精度没有被测出来，而测出来的容差又远宽于字面量自身精度，于是任何「正确公式 + 略偏数值」的回归都能静通过。

## 核验事实

### F1 — `abs=1e-30` 不可满足 + 20-dp 字面量误标「50 位」

`wayfinder` req-7 Scenario「σ′(−3.5) narrative precision matches 50-digit mpmath within 4 significant figures」要求存在

```
σ'(−3.5) == pytest.approx(0.02845302387973555984, abs=1e-30)
```

真值（mpmath 31-dp）：`σ'(−3.5) = 0.0284530238797355598396878271273`。

| 转写精度 | 与真值之差 | 相对 `abs=1e-30` |
|---|---|---|
| 20-dp `0.02845302387973555984` | `3.12e-22` | **`3.12e8 ×`** → Requirement **不可满足** |
| 31-dp `0.0284530238797355598396878271273` | `3.93e-34` | `0.39 ×` → 可满足 |

即：该 Scenario 自设立起就**没有任何一条 pytest 断言能满足它**，「钉值零容差」是纸面声明。

第二重缺陷：`verified at 50-digit mpmath precision σ'(−3.5) = 0.02845302387973555984` —— 标称 50 位、实挂 20-dp 截断值（`...84` 是 20 位四舍五入结果，不是 50 位值的前缀）。同一 Scenario 的 THEN 句亦然。

第三重（连带）：float64 在该量级的分辨率 `≈6.3e-18`，比 `abs=1e-30` 粗 11 个数量级。**任何经 `float()` 的比较都会让 `1e-30` 变成惰性容差** —— 测试报绿而「零容差」并不存在。

### F2 — 5-dp 字面量配 `abs=1e-4`（半单位的 20 倍）

req-26「Operational Domain γ′ Reset Closed-Form Worked Example」：
`gamma_reset_for_phase4(16.0) ≈ −0.06454`，5 位小数显示精度，原守护 `abs=1e-4`。

5-dp 字面量的半单位 = `5e-6`。`1e-4` = **20 × 半单位**，放行任意相差 `0.15%`（相对）的 γ-reset。`governance` req-gov-1 obligation 2 在 display-literal 与 float-closed-form 两种读法下都禁止。

### F3 — 4-dp 字面量配 `abs=1e-4`（半单位的 2 倍）

`tests/test_schedule.py` 的 `phase_beta_max(3, 55_999) ≈ 15.9996`，4 位小数显示精度，原守护 `abs=1e-4`。
4-dp 半单位 = `5e-5`，`1e-4` = **2 × 半单位** —— 与 `governance` 已判过错的 Voronoi `versine` 4-dp 字面量（`archive/…fix-voronoi-…`）**完全同型**。

### F8 — 残留 line-drift（5 处）

| 位置 | 原文 | 实际指向 | 判定 |
|---|---|---|---|
| `test_schedule.py:62` | skeleton `req-13 …, anchor L303, body L307` | skeleton req-13 anchor = **L316**、heading = L318；L303/L307 属 **req-12** | 漂移 |
| `test_schedule.py:82` | `per spec req-13 L307` | L307 属 req-12 | 漂移 |
| `test_schedule.py:86` | `per spec req-13 L307` | 同上 | 漂移 |
| `test_schedule.py:254` | `Phase 1 β^eff == 1.0 for ANY γ (spec line 495)` | L495 在 **req-20** 的 D_chord/MCI/CG Scenario 内，**与 per-phase β 公式无关**；正确归属 req-24 | 漂移 + 错误归属 |
| wayfinder req-28 `**Source:**` | 裸行号 L676 | 改指 `resurrection_perturb_distribution` 函数 + 既有 commit SHA | 漂移 |
| wayfinder req-32 `**Source:**` | 裸行号 L736 | 改指 `resurrect_expert` 函数 + 既有 commit SHA | 漂移 |

`test_schedule.py:64`（`wayfinder L83, req-6`）与 `:66`（`L617, req-27`）经核验**正确**，保留不动。

## 为何不把行号「改对」而是删掉

B16（commit `f0b3aa2`，本 session 上一轮）已实证：把 stale 行号改成当次正确行号，只是把同一个错误推到下一次漂移。`archive/2026-09-23-fix-claude-md-ticket-advisory-boundary/design.md` 确立了「新 Requirement 的 `Source:` 字段不引用 spec 行号，仅用 capability 路径 + commit SHA」的先例。

本 change 沿用该形态：**Requirement 名 / 函数名 + anchor id**。行号只在「当次锚点即语义标识」且已用 Requirement 名兜底时才保留。

## What changes

| 文件 | 改动 |
|---|---|
| `specs/wayfinder/spec.md` delta — req-7 | 31-dp 转写；`abs=1e-30` 强制 `mpmath.mpf` 双侧比较、禁经 `float()`；20-dp 反例写入 THEN 作为不可满足性证据；新增 paired `round(σ′, 5) == 0.02845` 钉 narrative 4-sig-fig |
| delta — req-7（同 Scenario 的 paired 断言） | 连带修复 `abs=1e-5`（= 2 × 5-dp 半单位 `5e-6`），改 round 形态。**报告未列，同块同类** |
| delta — req-26 | 5-dp 字面量改 round 形态，删除 `abs=1e-4` |
| delta — req-28 / req-32 | `**Source:**` 裸行号 → 函数名 + 既有 commit SHA |
| `tests/test_beta.py` | mpf 直比 `abs=mpf('1e-30')` + 新增 `round(sp_mp, 5) == 0.02845`；docstring 重写为「两帧」并写明 float64 塌缩陷阱 |
| `tests/test_schedule.py` | F2/F3 改 round 形态 + 补 `actual=` message；F8 的 4 处指针改 Requirement 名 |

## 明确不做（non-goals）

- **不改任何真值数值**。`σ'(−3.5)`、`γ' = ln(15/16)`、`β_max(3, 55_999)` 的真值均由 mpmath 独立复算确认正确 —— 本 change 只修**精度声明与容差的不相符**，不修数学。
- **不降 `abs`**。F1 若把 `abs` 放宽到能容纳 20-dp 转写，Requirement 就退化为「20 位精度」且与「50 位 mpmath」的声明矛盾；选 31-dp 转写 + mpf 比较是唯一保住「零容差」语义的路径。
- **不动 `wayfinder/tickets/`**。ticket 是 advisory 非约束（CLAUDE.md §8），且 `A4-1.md:59` 的 stale 引用仍待 `fix-review-findings-voronoi-precision-and-lineage` 归档后归属处理，用户已裁决。
- **不动 `decompmoe-skeleton` spec**。本 change 的 4 个 delta 全部落在 `wayfinder`。
