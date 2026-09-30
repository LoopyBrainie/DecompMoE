# Design — F1/F2/F3/F8 精度与指针漂移

## Decision 1 — F1 用 `mpmath.mpf` 直比，而非放宽 `abs`

req-7 强制 `abs=1e-30`。三个候选：

| 方案 | 结果 | 否决理由 |
|---|---|---|
| (a) 把 `abs` 放宽到 `1e-21` | 可满足 | 直接废除该 Scenario 的存在理由 —— 它要的就是零容差钉值 |
| (b) 降低字面量精度声明到 20-dp | 可满足 | 与同 Requirement 的「50-digit mpmath」声明自相矛盾 |
| **(c) 31-dp 转写 + mpf 双侧比较** | **差 `3.93e-34` < `1e-30`** | **采纳** |

选 (c) 的关键在第二半：即使字面量写对 31 位，**经 `float()` 后两侧都塌缩到同一个 float64 格点**，比较恒等于「相等 vs 相等」，`1e-30` 彻底惰性（float64 在 `0.0284` 量级的分辨率 `≈6.3e-18`）。因此 Requirement 必须同时约束：

1. 字面量精度 ≥ 31 dp（否则容差不可满足）；
2. 比较双方均为 `mpmath.mpf`，**任一侧不得经 `float()`**（否则容差惰性）；
3. narrative 4-sig-fig 的披露由**独立的** `round(σ′, 5) == 0.02845` 钉住 —— 因为 4-sig-fig 字面量**在原理上不可能**被 `1e-30` 覆盖，两者是不同量级的承诺，混用一条断言必然有一方落空。

配套：`pytest.approx` 仍保留（满足 `governance` req-gov-1 obligation 2 对「浮点闭式须用 `pytest.approx(..., abs=...)`」的硬要求），只是容差与操作数都改用 `mpf`。已实测 `pytest.approx(mpf, abs=mpf)` 可用。

> 注：`round(mpf, 5)` 返回 **float**，与 `mpf('0.02845')` 比较恒 False。round 形态一侧必须用 **float 字面量** `0.02845`。

## Decision 2 — F2/F3 用 round 精确形态，而非收紧 `abs`

`governance` 对「display literal」已有成例裁决：Voronoi `versine` 的 4-dp 字面量被判定不得配宽容差，处置方式是**改钉显示精度本身**（round 形态），而非把 `abs` 收到 `5e-6`。理由：字面量声称的就是那 4/5 位，测试应当验证「显示精度正确」，而不是「误差小于某个与显示精度无关的数」。

| finding | 字面量 | 半单位 | 原 `abs` | 新形态 |
|---|---|---|---|---|
| F2 | `−0.06454`（5-dp） | `5e-6` | `1e-4`（20×） | `round(g_reset, 5) == -0.06454` |
| F3 | `15.9996`（4-dp） | `5e-5` | `1e-4`（2×） | `round(beta_max_last, 4) == 15.9996` |

`round(x, n) == literal` 恰好是「在自身显示精度上正确」的充要判据，且**没有可被放行的邻域**。

## Decision 3 — F8 一律改 Requirement 名，不追行号

见 proposal「为何不把行号改对」。本 change 的具体落法：

- 测试侧（4 处）：`req-13 L307` → `skeleton req-13 "Five-Phase Schedule State Machine"`；`(spec line 495)` → `wayfinder req-24 per-phase formula`。
- spec `**Source:**` 侧（2 处）：裸行号 → `src/decompmoe/safeguards.py` 内的**函数名** + **既有 commit SHA**。函数名与 SHA 都是稳定标识；行号不是。

## Decision 4 — 连带修复 F1 同块内的 `abs=1e-5`

req-7 同一 Scenario 内还有一条 paired 断言钉 narrative 值，配 `abs=1e-5`。5-dp 字面量半单位 `5e-6`，`1e-5` = **2 × 半单位** —— 与 F3 完全同型。

reviewer 报告未列此条。按 B13 教训（「修复时留下明知错误的同型引用」是 B13 的成因模式），本 change 一并改为 round 形态，不留「已知错误却未修」。

## 验证方法（负向变异，非仅绿灯）

绿灯不能证明守护有效。本 change 对每条新守护做了**变异测试** —— 故意把被守护的性质破坏，确认对应测试转红：

| 守护 | 变异 | 结果 |
|---|---|---|
| F1 的 `abs=1e-30` 有效性 | 给 `sp_mp` 加 `+1e-25` / `+1e-18` 扰动 | 均被拦下（旧 float 形态对 `+1e-18` **照样通过**） |
| F2 round 形态 | γ-reset 偏 `9e-5` | 旧 `abs=1e-4` **放行**，round 形态拦下（旧守护宽 20 倍） |
| F1/F2/F3 的 msg | — | 所有新断言带 `actual=` 内嵌值 |

## 归档风险与应对

4 个被 MODIFIED 的 Requirement（`req-7` / `req-26` / `req-28` / `req-32`）各自后面紧跟 `req-8` / `req-27` / `req-29` / `req-33`。`openspec archive` 的 block 边界判定会**吞掉紧随其后的那个 Requirement 的 anchor**（每个被改的恰好丢 1 个），且 exit code 仍为 0、lint 与 validate 全绿。

归档后**必须**复算 anchor 覆盖计数并核对 `req-8` / `req-27` / `req-29` / `req-33` 的 anchor 是否仍在。若丢失，按既有配方修复：**不重跑 archive**（会再吞一次），改为 `git show HEAD:<spec>` 还原 + 确定性字符串替换重放自己的定点编辑。
