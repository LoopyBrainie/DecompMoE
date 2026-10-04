# Design: 2026-10-04-fix-wayfinder-advisory-drift-a7

本 design 的主要产出不是修复方案（那在 `proposal.md`），而是 **4 条裁决记录**。A-7 清单锁在 2026-10-01 pin 态且已过期 3 个 commit，其中 1 条已修、1 条方向反了、1 条引文不存在。裁决不落进版本化制品，下一轮审计就会原样再报一次。

---

## D1 — AC-55 已被 `a1f0caa` 修复，不再是 finding

**清单主张**：`wayfinder/spec.md:879` 的 req-36 逐字引用 ticket A8-2 的 annotation 为「spec req-20 L413」共 5 处，ticket 侧实为「spec req-20 L453」共 2 处，两者真值都是 L460。定级 MEDIUM。

**实测**：

- `openspec/specs/wayfinder/spec.md` 现状 915 行，numbered anchor 36 个 + 2 个块级 anchor，**36 Requirement / 103 Scenario**。anchor 集合为 1–35 + 38，**`req-36` 与 `req-37` 均不存在**。L879 现落在 req-34 的 Scenario「reverse-link must be wrapped in backticks」内。
- `grep 'L4[0-9][0-9]' openspec/specs/wayfinder/spec.md` → **0 命中**。
- 修复者是 `a1f0caa fix(pointer-drift): re-anchor the A-4 cross-reference family, tasks 1-6`（2026-10-03），同族另有 `5c49037` / `d61190d`。
- 清单的 5 处 / 2 处计数在 `git show a1f0caa^:…` 的**近似 pin 态**上可复现（`L413` 14 行命中中含该字面量者 5 行；A8-2 侧精确 2 行），故**计数方法论正确，问题纯粹是基线过期**。
- 新指针未断链：`<a id="req-20-mci">` 真实存在于 spec，`decompmoe-skeleton/spec.md` 4 处 + `governance/spec.md` 3 处以 `#req-20-mci` 引用，跨 capability 完整。

**裁决**：NO_LONGER_REAL / ALREADY_FIXED。**本 change 不改任何文件。**

**流程教训**：任何标「（pin 态）」的 finding 位置，在复核前必须先跑一次 `git log --oneline --since=<pin> -- <paths>`。本例 7/8 条位置零漂移（map / ticket 侧行号 pin 后未动），唯独 spec 侧动了——**这个不对称本身就是诊断信号**：它说明漂移集中在被 remediation commit 触碰过的那一侧。

---

## D2 — AC-97 是方向性误报：spec 采纳了 ticket，不是证否

**清单主张**：A6a-2 的供体克隆语义 `c_i ← Normalize(c_{j*} + ε)` 在 openspec 内无任何 API 落点；spec req-13 的「clones j*」措辞被自家 req-28/32 的 canonical API 与已落地代码**证否**；无 Decision 记录该删除。并称这是 `CLAUDE.md` §8 第 (iii) 通道（reader-ticket-not-spec 复制）的源头。

**实测——四层全部同向**：

| 层 | 位置 | 原文 |
|---|---|---|
| req-13 | `wayfinder/spec.md:333` | `clones j* = argmax f_j^avg, perturbs with ε ~ N(0, 0.05² I)` |
| req-28 | `wayfinder/spec.md:735` | the perturbed quantity is the donor's centroid per req-13's "clones j*" |
| req-32 | `wayfinder/spec.md:794` | **The clone source is row j_star (the donor), not row i** |
| req-32 Scenario | `wayfinder/spec.md:830` | the clone is taken from `c_centroids[j_star]` (the donor) and NOT from `c_centroids[i]` |
| 代码 | `src/decompmoe/safeguards.py:301` | `c_perturbed = spherical_l2_normalize(c_centroids[j_star] + ε)` |

`req-32` 的 Source（spec.md:796）记录了 `fix-math-consistency-audit-2026-08 design.md (Decision 4 — per-expert perturbation contract)`。

**裁决**：CONTRADICTED。**本 change 不改 A6a-2 的 L67**。

**要点**：该条的后果恰好是 §8 第 (iii) 通道的**反向**——此处的 reader-ticket-not-spec 复现**恰好是安全的**。同文件 L63 已有 `(historical, threshold 1/128; …)` 标注，说明该文件部分使用了规范格式，因此 L67 裸奔只是**选择性缺口**而非全文件失守。

---

## D3 — Voronoi 闭式没有 off-by-one（清单外，曾被报为潜在 MAJOR）

复核过程中出现一条**清单未收录**的候选：「spec 的 `½·I_{sin²θ}((d_c−1)/2, ½)` 应为 `d_c/2`，少覆盖 9.8%」，并跨 capability 一致承袭（spec + `sphere.py` + skeleton req-6），一度被视为唯一可能是 MAJOR 的候选。

**该主张为假。**

**推导**：设球面为 `S^{n-1} ⊂ R^n`，`n = d_c`。极角 `φ` 处的面元为 `sin^{n-2} φ`，故单极 cap 的面积占比是

```
fraction(θ) = ∫_0^θ sin^{n-2} t dt  /  ∫_0^π sin^{n-2} t dt
```

由 `∫_0^θ sin^m t dt = ½·B_{sin²θ}((m+1)/2, ½)`，取 `m = d_c − 2`，得被积指数 **`d_c − 2`**、beta 参数 **`(d_c − 1)/2`** —— 正是 spec 的写法。自洽性检查：θ = π/2 时该式恒为 ½。

误报的来源是把 `∫_0^θ sin^{d−1} t dt`（那是 `S^d ⊂ R^{d+1}` 的面元，即**大一个维度**的球）当成了 `S^{d_c−1}` 的面元。

**数值对照**（直接积分 vs spec 字面 θ）：

| N_e | θ (rad) | 指数 d_c−2 = 14（真 S^15） | 指数 d−1 = 15（S^16，被拒变体） | 目标 1/N_e |
|---|---|---|---|---|
| 16 | 1.1735474259196821 | **0.06249999999998269** | 0.05636317176230738（0.9018×） | 0.0625 |
| 64 | 1.0205068247837297 | **0.015625** | 0.012981637459521413（0.8308×） | 0.015625 |

即 spec 的两个表值**恰好是真 cap 面积占比 = 1/N_e 的根**；「`d_c/2`」变体不是「少覆盖」，而是**欠覆盖**——它属于另一颗球上的另一个量。

**处置**：**不改 spec、不改 `src/`**。改为在 `tests/test_sphere.py` 加两个用例，把这件事从「一次性证伪」升级为**永久防护**：

- `test_cap_area_fraction_matches_direct_quadrature` 用 composite Simpson 直接积分定义式，**不复用** `_betainc_regularized` / `mpmath.betainc`——同源实现无法证伪自己的参数化；
- `test_cap_area_fraction_rejects_off_by_one_sphere_dimension` 把 `exponent_offset=1` 变体连同 0.9018× 的欠覆盖量一起钉成**已知被拒形态**。

**apply when**：任何「等面积胞 / cap 面积 / beta 函数参数」的审计主张。先问一句**这是哪颗球**：`S^{d−1}` 的面元指数是 `d−2`。

---

## D4 — 治理依据是 wayfinder req-34，不是 governance req-gov-4 clause 4(a)

清单把 AC-98 的缺口写成「违反 governance req-gov-4 clause 4(a)」，复验者据此把定级降到 NONE。

**该降级不成立，理由也要换。**

- `governance/spec.md:172` clause 4 的前置条件逐字是「when ticket stale is detected **propagating to `src/`**」。本 change 的 6 条漂移**全部 0 src 传染**（`MVPConfig.beta_initial = 1.035` 已对齐 spec req-7 闭式；`tests/test_beta.py` 已用 `pytest.approx(expected, abs=1e-3)`；`_dead_expert_threshold(N_e)` 已参数化），故 (b)(c) 两步无对象，**4(a) 整体未被触发**。
- clause 189 的 Scenario 还要求「partial closure MUST NOT be considered fully-closed」——但那条 Scenario 同样以「propagating to `src/`」为 WHEN 条件。
- **真正生效的义务在 `wayfinder/spec.md:844`（req-34）**：「Naked ticket references that omit the annotation but imply current-value parity with the spec are NOT permitted for tickets whose recorded value has been superseded.」`req-28` / `req-32` 的 Source 写的是 `wayfinder/tickets/A6a-2.md`（initial A6a-2 design intent），裸引用，暗示现行等值——而 A6a-2 的 `W_i` 克隆步已被 canonical API 范围排除。

**剩余真实缺口**：(i) req-34 要求的 `(historical, …)` 标注缺失；(ii) 无 Decision 记录「专家权重克隆步被 canonical API 范围排除」这一**决定**。

**分类**：按 `CLAUDE.md` §2 真相源层级，这属**决策 trail 缺口**而非行为缺口（wrapper 返回类型在结构上已排除 `W`，但没人写下「删除」这个决定）。故 MINOR 定级维持。

---

## 遗留项（不在本 change 范围）

| 项 | 说明 |
|---|---|
| `g_boundary 0.205`（map.md L54） | 无 spec 规范值可依，v1 ticket 值孤证。**不动**，避免在无真相源处造值 |
| map.md L3 / L69 / L72 / L95 的状态措辞 | `CHARTING (step 3 完成)` / `CHART COMPLETE` / `下一步…执行 A8 baseline 矩阵` 均停在 WF 工单当时快照。map.md 整体未维护是 AC-93/94/95 的共同根因，建议单独一个 change 收口 |
| `A6b-1.md:101` / `:133` 的 provenance | N_e 64→16 与 γ' 闭式**无可核实的 change Decision**（req-11 的 Source 未列 N_e 决策来源；req-7 的 Source 只有 3 个 ticket 反链、零 change 引用）。本 change **只加 anchor 链接，不编造 provenance** |
| AC-95 的 arena 口径 | map.md 无显式 arena 列表，`10 个 arena` 由 A0–A8（A6 拆 a/b）推出；若口径改为「WF 也算」则为 11。L95 保持不动 |
| 审计清单回写 | `.audit/` 被 `.gitignore` 忽略、非版本化。裁决只进本 design.md（`CLAUDE.md` §3：Design decision made → design.md） |
