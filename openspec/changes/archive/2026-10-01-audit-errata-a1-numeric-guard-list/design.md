# Design

## Context

See `proposal.md` — Why。本节只补充**约束勘误工作本身的**事实。

**审计基线与漂移**：

| 项 | 值 |
|---|---|
| 审计基线（pin） | `6593a06` |
| 当前 HEAD | `188b9fb` |
| 两者之间 | 9 个 commit |

`openspec/changes/` 下 3 份 spec 在这段区间**全部被改动**；`src/` + `tests/` 有 8 个文件被改动。因此 `lists/opsx-changes.md` 中的每个 `file:line` 都只对 pin 态有效，且归档自身已声明「动手前必须按 `context/07-baseline-drift.md` 的漂移表重新定位」。

**漂移归因（实测，非推断）**：

```
git log --oneline 6593a06..188b9fb -- src/decompmoe/sphere.py tests/test_sphere.py
→ e50cc02 chore(inflight): checkpoint parallel session's in-flight work   （唯一）
```

翻转 AC-08 / AC-09 / AC-18 / AC-48 四条裁决的代码（`sphere.py` +110、`test_sphere.py` +312）全部来自 `e50cc02`，其 commit 标题表明这是一次**并行 session 的在制品 checkpoint**，不是评审过的改动。`5a7e48d fix(f1,f2,f3,f8)` 只碰了 `tests/test_beta.py` 与 `tests/test_schedule.py`。

**复核方法约束**：工作树存在并行 session 的未提交内容（`openspec/changes/` 下 2 个目录被删、`wayfinder/tickets/WF-1.md` 被改、约 30 个 `_tmp_*.py` 未跟踪）。因此下列每条勘误都以 commit object（`git show <rev>:<path>` / `git grep <pat> <rev> --`）为唯一依据，**不读工作树文件**。

## Goals / Non-Goals

**Goals:**

- 让 12 处错误在归档内**就地可查**，并附带可复现命令，使后续实施者不需要重跑复核就能定位到正确文件与行号。
- 记录每条勘误的**证据类型**（实测 / 推导），使读者能判断该结论的强度。
- 登记与未归档 change `fix-review-findings-voronoi-precision-and-lineage` 的重叠面。

**Non-Goals:**

- ❌ 不改写归档正文的任何既有结论、严重性或裁决（`STILL_REAL` / `baseline_status` 等一律保留原样）。
- ❌ 不修复 24 条中的任何一条——那是三个后续 change 的范围。
- ❌ 不重新判定任何 verdict，不重跑任何变异测试。
- ❌ 不动 `openspec/specs/**`、`src/**`、`tests/**`、`wayfinder/**`。

## Decisions

### D1 — 追加勘误节，不改写正文

**选择**：在 `lists/opsx-changes.md` 末尾追加 `## Errata`，原文一字不动。

**理由**：归档 README 的「本议题未做的事」第 3 条明写「**没有重新计算数学**」、第 4 条「没有重跑变异测试」、第 2 条「没有重新 review」。它是**一次已完成 review run 的记录**，改写它会伪造历史。若直接改正文，后来者无法区分「当时认为的」与「后来发现的」。

**备选与否决理由**：
- *就地改写错误的行号* → 否决。会销毁错误本身，且看不出曾有错误。
- *另建一份勘误文件* → 否决。清单是唯一待办入口，勘误放在别处必然漏读。追加到同一文件、置于读者必然经过的位置更可靠。

### D2 — 勘误锚定 HEAD 行号，同时标注 pin 行号

**选择**：每条勘误同时给出 pin 态与 HEAD 态坐标。

**理由**：清单的行号体系是 pin 态坐标台账，而实施发生在 HEAD。两者都给出，实施者既能理解原意、也能直接施工。

### D3 — 每条勘误标注证据类型

| 标记 | 含义 |
|---|---|
| `实测` | 由 `git show` / `git grep` 直接读出 |
| `实测（数值）` | 由本轮独立计算得出（附计算方法） |

**理由**：本轮复核中出现过两类不同强度的结论——「某定位指错」是纯读取事实，而「AC-18 的跳变是单侧而非两侧」是数值推导。混在一起会让读者无法判断可信度。

### D4 — 勘误对照表（E2 / E4 已撤回；E13 为 review 后新增）

> **复核修订记录**：本表初稿含 12 条，其中 **E2、E4 两条在逐条复核后被撤回**——它们不是错误。撤回理由见 D4.1。**E13 是后续 `/code-review` 阶段新发现的数值守卫缺陷**，其结论在 review 后被自己的实测推翻过一次，最终结论与初稿相反，见 D4.2。**有效勘误为 11 条**。

| # | 状态 | 条目 | 清单声称 | 实测 | 证据类型 |
|---|---|---|---|---|---|
| E1 | 生效 | AC-03 | 位置 `tests/test_beta.py:184` | 该行是 `test_logit_range` 体内 `logits = beta_val * (inner - 1.0)`；所称的 `test_logit_no_w_i` 在 **`tests/test_distance.py:53`**（pin = HEAD，未漂移） | 实测 |
| E2 | **撤回** | AC-08 | 位置 `src/decompmoe/sphere.py:197` | `git show 6593a06:src/decompmoe/sphere.py` 的 `:197` **正是** `def canonical_voronoi_angle(...)`。清单的 pin 定位**正确** | 实测 |
| E3 | 生效 | AC-01 | 位置 `src/decompmoe/distance.py:24` | `:24` 落在 `def squared_chord` 附近；真正 `return beta * (inner - 1.0)` 在 **`:33`**（文件零漂移） | 实测 |
| E4 | **撤回** | AC-83 | 位置 `openspec/specs/wayfinder/spec.md:251`(pin) | pin `:251` **正是**含 `131_584` / `32_896` 的 Router term 行（`:252` 才是空行）。清单的 pin 定位**正确** | 实测 |
| E5 | 生效 | AC-61 | wayfinder req-33 Scenario 逐字点名 **5** 个 `phase_beta_max` 精确值 | 该 Scenario（`wayfinder/spec.md:665`，THEN 行在 `:666`）逐字只点名 **4** 个：`(2,6_000)→1.0`、`(2,16_000)→2.5`、`(3,26_000)→4.0`、`(3,41_000)→10.0`。第 5 个 `3.99985`（`test_sphere.py:184`）来自**相邻** Scenario，不在点名范围内 | 实测 |
| E6 | 生效 | AC-77 | `β_p3 = 1.0` 在 Phase 3 **可达**（据「Phase-1 全 5000 步固定 β = 1.0」） | `phase_beta_box(3)` 返回 **`(4.0, 16.0)`**，Phase-3 的 `β_max` 下界恒 ≥ 4.0；其 docstring 明写 `(1.0, 32.0)` fallback 适用于「Phase 1 `β^eff = 1.0` fixed」，即 Phase-1 的 1.0 语义上不是 P3 退出值；`gamma_reset_for_phase4` 的全部调用点只传 `16.0` → **不可达**。缺域声明本身仍成立，**严重性应下调** | 实测 |
| E7 | 生效 | AC-10 / AC-33 | UR 在 `tests/` **零调用、零断言** | `metrics.UR(` 作为调用在 pin 与 HEAD 均 **0 次**（核心主张成立）；但裸 token `UR` 有 **4 处**：`test_metrics.py:65`（集合成员断言）、`:71`、`test_safeguards.py:458`（docstring）、`:466`（`torch.randn(100, cfg.N_e)  # per metrics.UR stacked history`，**模仿输入形状却不调用**）。准确表述为「无**数值**守卫」 | 实测 |
| E8 | 生效 | AC-10 / AC-33 | 其余 7 个指标调用计数「1–23 次」 | **三个不同口径都成立，不可混用**：①**AST 调用点**（`ast.Call` 且 `func.attr == 名字`）= `L_sep` 1 / `R_H` 2 / `S_load` 5 / `SP` 5 / `D_chord` 2 / `MCI` 6 / `CG` 17，区间 **1–17**；②**文本匹配行数**（`git grep -c`，**会命中 docstring 里的示例调用**）区间 2–16；③清单给的是 instrumented **运行期**计数（计参数化展开）= 1–23。**以 ①为准** | 实测 |
| E9 | 生效 | AC-40 | `1_000_000` 与 `20260929` 在 `tests/` **零命中** | `20260929` 确为 **0 命中**；`1_000_000` 有 **1 处**——`test_sphere.py:240`，位于 docstring 引用 `VORONOI_AREA_SAMPLES = 1_000_000`。另 `test_safeguards.py:94` 的 `0.10000001` 是子串误配。**断言体内命中数仍为 0**，故实质主张成立。另：常量名是 `VORONOI_AREA_SAMPLES`，清单写 `SAMPLES` | 实测 |
| E10 | 生效 | AC-18 | `_cap_area` 在 `θ=π/2` 处「左极限与右极限相差 `5.239884e-2` / `7.870852e-2` / `1.158112e-1`」 | 三个数是 **单侧**跳变 `\|G(π/2) − G(π/2−h)\|`。真正的左右极限间距是 **2 倍**：`1.047977e-1` / `1.574170e-1` / `2.316223e-1`（d_c = 8 / 16 / 32，h=1e-7） | 实测（数值） |
| E11 | 生效 | AC-91 | req-24 的三个 γ/β 中间量「无任何测试钉住」 | γ-space 间隙 **有两条真断言**：`test_beta.py:154` `round(float(gamma_full), 4) == -6.7835` 与 `:164` `gamma_full == pytest.approx(-6.7835, abs=1e-4)`，后者带 `f"actual="`。β-space 残差 `1.5899599e-6` 在 `:160`、斜率 `0.0350220952386` 在 `:161`，二者**均只在注释里** | 实测 |
| E13 | 生效 | AC-08 / AC-09 | 清单认为 6dp 字面量 `1.173548` / `1.165848` 已被有效守护 | **该字面量必须与「求积器是否已修」联读才有意义，但其本身是标准 red→green 判别式。** obligation 3 的 `abs=1e-6` 恰好 ≥ 新旧字面量之差（相差 **恰为 `1.000e-06`**），故现字面量对修前 impl 与修后真值**都 PASS**（`2.747e-07` / `5.741e-07`）；但新字面量 `1.173547` 对修前 impl `1.1735482746999482` 为 **`1.275e-06` FAIL**、对修后真值 `1.1735474259197174` 为 `4.259e-07` PASS ⇒ **修前红、修后绿**。⇒ **Change 2 只改字面量即产生可观察测试，无需动容差**；且 6dp 字面量固有截断误差上界 `5e-07`，**任何 `< 1e-6` 的容差都会在真值上失败** ⇒ obligation 3 的 `abs=1e-6` 对 6dp 字面量是**必需**而非宽松，维持不变。详见 D4.2 | 实测（数值） |
| E12 | 生效 | AC-48 | 单向界被一个**不存在的阈值** `theta_conv` 门控 | `e50cc02` 已把该门控**整体删除**，Jensen 前置条件改为无阈值的 `∀i: A_i < 0.5`，由 `test_voronoi_angle_precondition_is_area_below_half`(`test_sphere.py:551`) 守。HEAD 的 `theta_conv` 仅剩 1 处命中（`:580` 的 f-string 报错文案，说明其「已退役」）。**该具体指控不成立**；但「单向性只有方向约束、无幅度」仍成立 | 实测 |

### D4.1 — E2 / E4 撤回理由

两条最初被判为「定位指错」，逐条复核后不成立：

- **E2**：`git show 6593a06:src/decompmoe/sphere.py` 的第 197 行**正是** `def canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float:`。清单的 pin 定位准确。
- **E4**：`git show 6593a06:openspec/specs/wayfinder/spec.md` 的第 251 行**正是**含 `P_router/layer = … = 32_896` 与 `P_router = … = 131_584` 的 Router term 行；第 252 行才是空行。清单的 pin 定位准确。

**更根本的理由**：归档 README 已声明「本议题所有 `file:line` 均为 pinned commit `6593a06` 的行号……**动手前必须按 `context/07-baseline-drift.md` 的漂移表重新定位**」。**pin 坐标在 pin 态成立是归档的既定契约，不是缺陷**。E2 / E4 的真实情况只是漂移（`sphere.py:197 → :210`，+13 行；`wayfinder/spec.md:251 → :252`，+1 行），而漂移已被归档自身覆盖，不构成勘误。

因此**「定位指错」类勘误实际只有 2 条（E1、E3）**，而非初稿所称的 6 条。加入 review 后新发现的 E13，**有效勘误总数为 11 条**。

**教训**：E2 / E4 最初采信了复核子 agent 的结论而未自行实测。派发 brief 里的归因必须先跑 `git log <range> -- <path>` / `git show <rev>:<path>` 确认，子 agent 报告 ≠ 实测。


**勘误的复现命令**（全部只读，锚定 commit object）：

```bash
# E1
git show 6593a06:tests/test_beta.py | sed -n '184p'
git grep -n 'def test_logit_no_w_i' 6593a06 -- tests/
# E2（已撤回 —— 下列命令用于确认「清单 pin 定位其实是对的」）
git show 6593a06:src/decompmoe/sphere.py | sed -n '197p'      # → def canonical_voronoi_angle(...)
git grep -n 'def canonical_voronoi_angle' 188b9fb -- src/      # → sphere.py:210（+13 行漂移）
# E3
git show 188b9fb:src/decompmoe/distance.py | sed -n '33p'
# E4（已撤回 —— 下列命令用于确认「清单 pin 定位其实是对的」）
git show 6593a06:openspec/specs/wayfinder/spec.md | sed -n '251p'   # → Router term 行（含 131_584）
git grep -n '131_584' 188b9fb -- openspec/specs/wayfinder/spec.md   # → :252（+1 行漂移）
# E5
git grep -n 'Scenario.*phase_beta_max' 188b9fb -- openspec/specs/wayfinder/spec.md
# E6
git show 188b9fb:src/decompmoe/schedule.py | grep -A16 'def phase_beta_box'
# E7
git grep -n '\bUR\b' 188b9fb -- tests/
git grep -nE 'metrics\.UR\s*\(' 188b9fb -- tests/      # → 0
# E8
git grep -cE 'metrics\.(L_sep|R_H|S_load|SP|D_chord|MCI|CG)\s*\(' 188b9fb -- tests/
# E9
git grep -n '20260929' 188b9fb -- tests/                # → 0
git grep -n '1_000_000' 188b9fb -- tests/
# E10
# 见 design 下方「E10 的数值推导」
# E11
git show 188b9fb:tests/test_beta.py | sed -n '152,166p'
# E12
git grep -n 'theta_conv' 188b9fb -- src tests
git grep -n 'def test_voronoi_angle_precondition_is_area_below_half' 188b9fb -- tests/
```

### D4.2 — E13：6dp 字面量的容差**必须**是 `1e-6`（review 阶段新增，已两次修正）

**本节结论在 review 后被自己的实测推翻过一次，最终结论与初稿相反。** 保留推导过程是因为「只改字面量是否可观察」这个问题的答案会决定 Change 2 能否被测试守护。

#### 初稿结论（**错误**）

初稿称：`abs=1e-6` 恰好 ≥ 新旧字面量之差（两者相差 **恰为 `1.000e-06`**），因此现字面量对 impl 与真值都 PASS，**Change 2 对测试不可观察**，故必须把容差收紧到 `1e-9`。

#### 推翻它的实测

「可观察性」的正确判据不是「新字面量对两侧都过」，而是**新字面量是否在修复前失败、修复后通过**。实测：

| 字面量 | 对 impl（未修） | 对真值（修后） | 判据 |
|---|---|---|---|
| 现 `1.173548` | `2.747e-07` PASS | `5.741e-07` PASS | 旧值，两侧皆过（预期如此） |
| **新 `1.173547`** | **`1.275e-06` FAIL** | `4.259e-07` PASS | ✅ **标准 red→green** |

N_e=17 同构：新字面量 `1.165847` 对 impl `1.1658482974306132` 为 `1.297e-06` **FAIL**，对真值 `1.1658476215516009` 为 `6.216e-07` PASS。

⇒ **Change 2 只改字面量就已经产生一条可观察的红→绿测试，不需要动容差。** 初稿的核心推论作废。

#### 收紧到 `1e-9` 不但没必要，而且会**直接让测试失败**

6dp 字面量对真值的固有误差是**截断/舍入误差**，量级达 `1e-6`（上界 `5e-07`）：

| 项 | 值 |
|---|---|
| 真值（N_e=16） | `1.1735474259197174` |
| 6dp 字面量 | `1.173547` |
| 固有误差 | `4.259e-07` = **`1e-9` 的 426 倍** |

所以任何 `< 1e-6` 的容差**在真值上就会失败**。`governance` obligation 3 规定的 `abs=1e-6` 对 6dp 字面量不是「可接受的宽松」，而是**必需的**——它恰好是 6dp 精度的固有误差上界。

⇒ obligation 3 自洽，**不改**。Change 2 只需改 spec 与测试的字面量，容差保持 `1e-6`。

#### 两种口径并存（此部分不变，仍然成立）

- bisection **角度** 6dp 字面量 → **截断**（obligation 3）：`1.173548 → 1.173547`、`1.165848 → 1.165847`
- **versine** 4dp 字面量 → **`round(v, 4)` 精确 `==`**（obligation 2 的 4 位小数显示例外）：`0.6131`、`0.4771` **均不变**。实测 `round(0.4770659854126468, 4) == 0.4771` 为 `True` ⇒ 批准计划「爆炸半径」表中 versine 那一行改 `0.4770` 的方向是错的。

#### 附：N_e=64 不是判别点（预期如此）

`1.020506` 对 impl `1.0205068335735599` 为 `8.336e-07`、对真值 `1.0205068247837132` 为 `8.248e-07`，两侧皆 PASS，且**修前修后字面量不变**（真值两种状态都截断到 `1.020506`）。N_e=64 本就不承担判别职责，不应被算作「E13 的反例」。

### D4.3 — `/code-review` 阶段的非勘误发现（不入 Errata，留痕）

`/code-review` 产出 6 节报告。其中两项**不是对清单的更正**，因此不进入 `## Errata`（生效勘误仍为 11 条），但必须留痕。

#### F5（CONFIRMED，已独立复算）—— `CLAUDE.md` §5 的「球面几何自洽」是**过宽**陈述

reviewer 的反例成立。用**独立 mpmath oracle**（dps=50，**不调用 `src/decompmoe/sphere.py`**，故不构成「用被测实现自证」）解 `cap_fraction(θ) = 1/N_e`，其中 `cap_fraction(θ) = A_{d_c-1}·∫₀^θ sin^{d_c-2}φ dφ / A_{d_c}`：

| (N_e, d_c) | θ_Voronoi | θ_{1/e}(β=16) | 结论 |
|---|---|---|---|
| (16, 16) | 67.2393° | 20.3641° | 成立，余量 **3.3×** |
| (16, 64) | 58.47° | 20.3641° | 成立 |
| (16384, 8) | **19.0992°** | 20.3641° | **违反** |
| (128, 4) | **19.2°** | 20.3641° | **违反** |

边界扫描（β=16）：`d_c=4` 在 `N_e=128` 失守，`d_c=8` 在 `N_e=16384` 失守；`d_c ≥ 16` 到 `N_e = 4M` 仍成立。

**但必须修正 reviewer 的定性**：它把整条声明判为假。实际上该括注在 **MVP 自身超参（`N_e=16, d_c=16, β=16`）上逐字成立且余量巨大**（67.24° vs 20.36°）。缺陷是**陈述缺少适用范围**（读起来像对任意 `N_e, d_c` 的充分条件），**不是** MVP 配置下算错。

⇒ 严重性 **低**；且 `CLAUDE.md` §5 既不属于三份 spec capability，也不在 A-1 桶 24 条内，**不在本 change 施工范围**。登记为待办，**需用户裁决是否单独开 change**；本 change 不动它。

#### F1（REFUTED，父 session 已证伪）

reviewer 称 `decompmoe-skeleton/spec.md:161` 把 logit 范围写成 `[−β, 0]`。**该行逐字是** `the output range of logit SHALL be [−2β, 0]` —— 与 `CLAUDE.md` §9 不变量 2（`logit ∈ [−2β_max, 0]`）一致，reviewer 读漏了系数 `2`。**无需处理**，此处仅记录以免后续重复提出。

#### 归档正文不可验证性（本 change 自身的验证缺口）

`.audit/` 被 `.gitignore:37` 忽略且**从未被 git 追踪**（`git ls-files .audit` = 0 行；`git log --all -- <该路径>` 为空）。因此 D1 承诺的「归档正文逐字未动」**无法事后用 commit object 验证**——而这正是本 change 对其他一切核验所依赖的手段。

实测对照：apply 阶段记录的前置大小为 **146935 字节 / 1472 行**；当前按同样 1472 行重建得 **146934 字节**。**差 1 字节，且无基线可判定哪一侧为准。**

⇒ D1 的不变量在本 change 中状态为 **UNVERIFIED**，**不得当作已验结论引用**。补救：固化当前前缀哈希作为**前向防篡改基线**，使后续任何改动可检出。

```
lines[:1472]  bytes=146934  sha256=8e66c0f2c7a5df2ed3a799349c9205c6eec7ac69bde8d4760d24110a1a77d276
lines[:1475]  bytes=146940  sha256=ba42ddfc0510baace8423a9d04a64d4907045ad2f078945e05f28981f3be1403
```

（1473–1475 为追加时的分隔行 `''` / `'---'` / `''`；`## Errata` 起于 1476；全文件 156068 字节。）

⚠️ 这暴露一个**跨切面流程缺陷**：本仓把「锚定 commit object，不读工作树」当作核验纪律，但该纪律**对 gitignored 的制品不成立**。后续若继续对 `.audit/` 归档做勘误类变更，应先决定 un-ignore，或把权威副本迁到被追踪路径。

### D4.4 — `/code-review` 全量 findings 台账与父 session 独立裁决

D4.3 只留痕了 3 项。review 实际产出 6 组 finding，其中 **F2 / F3-oracle / F4 / F6 / A4 此前在 Change 0 内没有任何落点**，会在 review 与后续 change 之间丢失。本节补齐。

**复核纪律**：下表每一行的裁决都由**本 change 自己**重跑 `git show 188b9fb:<path>` / 独立 oracle 得到，**不转抄 review 结论**。review 的 3 项裁决未被采信，逐条列在「未采信」列。

| # | review 裁决 | **父 session 独立裁决** | 证据 | 去向 |
|---|---|---|---|---|
| **F1** logit 范围 | CONFIRMED (CRITICAL) | ❌ **REFUTED（第 2 次）** | `skeleton:161` 逐字 `the output range of logit SHALL be [−2β, 0]`；计数 `[−2β`=1 / `[−β`=0。`distance.py:27` docstring 同为 `[−2β, 0]`。`test_beta.py:192` 断言 `>= -2 * beta_val`。**spec / src / test 三者一致，无矛盾** | 无需动作 |
| **F2** 16 位 canonical 字面量 | CONFIRMED (CRITICAL) | ✅ **CONFIRMED** | `skeleton:113` 与 `:98`、`governance:20` 三处冻结 `1.1735482746999482`；真值 `1.173547425919717470035`，**第 7 位小数起分歧** | **Change 2** |
| **F3a** `abs=1e-6` 不可观察 | CONFIRMED (CRITICAL) | ❌ **REFUTED** | 新字面量 `1.173547` 对未修 impl `1.275e-06` **FAIL**、对修后真值 `4.259e-07` PASS ⇒ 标准 red→green。详见 D4.2 | 无需动作 |
| **F3b** 自身作 oracle（循环论证） | CONFIRMED | ✅ **CONFIRMED（且已有 spec 依据）** | `skeleton:114` 明写 `< 1e-9` 由 `test_voronoi_residual_below_1e_minus_9` 钉住，而该测试用 `sphere._betainc_regularized`（**被怀疑对象本身**）度量。impl 内部残差 `1.16e-14` vs 真值 `4.15e-7` ⇒ 差 `4.2e5` 倍。而 `governance:19-22` 的 **obligation 4 本就强制**「Spec MUST clarify which frame」⇒ **是测试违反治理，不是治理缺失** | **Change 1 + 2** |
| **F4** 量纲混用 | CONFIRMED (MAJOR) | ✅ **CONFIRMED** | `skeleton:115` 把面积分数残差 `4.15e-7`（N_e=16）与**角度**容差 `1e-6` 直接比较；N_e=64 的 `1.43e-9` 同样跨量纲。正确表述是 θ 偏差 `8.49e-7 rad < 1e-6 rad`，且已占 **85% 预算** | **Change 2** |
| **F5** CLAUDE.md §5 自洽性 | CONFIRMED (MAJOR) | ⚠️ **CONFIRMED 但降格** | 见 D4.3：MVP 点成立且余量 3.3×；反例在 `d_c=4`(`N_e=128`) / `d_c=8`(`N_e=16384`)。缺的是**适用范围声明** | 单独 change（仅 `CLAUDE.md`） |
| **F6** 死防御代码 | CONFIRMED (MINOR) | ⚠️ **CONFIRMED，但位置错** | reviewer 指 `sphere.py:36-44`（该处是 import 区）。**实际在 `gating.py:36-40`**：`torch.where(isinf(x) & (x<0), full_like(-inf), x)` 选中的正是已为 `-inf` 的项再赋 `-inf` ⇒ 纯 no-op。同文件 `:41-43`（全掩码行）与 `:46-50`（-inf→0）**不是** no-op。`lint_no_dead_defensive.py` 未捕获 | **Change 2** |
| **A1** E10 单侧/双侧 | CONFIRMED | ✅ CONFIRMED | 左右逐位对称，双侧恰为单侧 2.000000 倍 | 已记入 E10 |
| **A2** 1-ULP 悬崖 | CONFIRMED + 精化 | ✅ CONFIRMED | 解析佐证：`2/B(7.5,½) = 3.03915453102`，与 d_c=16 的 `span/h` 常数吻合到 9 位 | 已记入 E10 根因 |
| **A3** 真值表 / versine | 数值 CONFIRMED，versine REFUTED | ✅ 一致 | versine 走 `round(v,4)` 精确 `==`，`0.4771` 修后仍成立 | 已记入 D4.2 |
| **A4** obligation 4 五数值 | CONFIRMED + 建议 retire | ✅ 数值 CONFIRMED；**retire 建议未采信为定论** | 五数值自洽；但「修好求积器后两帧重合 ⇒ 整段失效」是**条件性推论**，取决于 Change 2 是否真去修 | **Change 2 决策** |
| **D** 测试数学约束覆盖 | CONFIRMED | ✅ CONFIRMED | 217 test functions / 191 model-facing；数学 128 (67.0%) / 伪守卫 38 (19.9%) / 功能 25 (13.1%)。三高危模式（内联重算 / 词法代替数值 / 自身作 oracle）全部成立 | **Change 1** |

#### 未采信的 review 裁决（3 项）

1. **F1**（CRITICAL）：把一个**写对了**的规范判为错误，且 spec/src/test 三处一致。已第二次证伪。
2. **F3a**（CRITICAL）：判据选错——问的是「新值两侧是否都过」而非「新值是否修前红修后绿」，据此推出的「必须收紧到 `1e-9`」会**直接让测试失败**（6dp 字面量固有截断误差 `4.259e-07` = `1e-9` 的 426 倍）。
3. **F6 位置**：`sphere.py:36-44` → 实为 `gating.py:36-40`。发现本身成立，坐标错误（与本 change 勘误的 E1/E3 同类，且**都指向 review 的行号需重定位**）。

⚠️ **共同教训**：review 报告的行号**必须**按 `context/07-baseline-drift.md` 重定位后才能施工——这与勘误正文 E1/E3 是同一条纪律。F6 提供了第三个实例。

#### 去向汇总

- **Change 1**（纯测试守护）：D 的 38 个伪守卫、F3b 的 oracle 循环
- **Change 2**（spec + src 语义）：F2 字面量、F3b 治理对齐、F4 量纲、F6 no-op、A4 retire-or-update 决策
- **单独 change**：F5（仅动 `CLAUDE.md` §5）
- **不做**：F1、F3a（review 裁决错误，改动它们会引入缺陷）

### D5 — E10 的数值推导（供复核）

`_cap_area(θ, d_c) = ½·I_{sin²θ}((d_c−1)/2, ½)`，当 `θ > π/2` 走 `1 − ½·I` 反射分支。`_betainc_regularized` 开头有 `if x >= 1.0: return 1.0`。

在 float64 下 `sin²(π/2)` **精确等于 1.0**，命中早退 → `G(π/2) = 0.5`（精确）。而 `x = nextafter(1.0, 0)` 时同一函数返回 `0.8425829560490325`（单片 8 点 Gauss–Legendre 面板在 `x→1` 的平方根奇点上崩溃）→ `G` 掉到 `0.421291`。

因此跳变在 `θ=π/2` **两侧对称**，各为 `|G(π/2) − G(π/2∓h)|`，合计 `2×`。**精确数学在此连续**（跳幅随 h 线性趋零）⇒ 该不连续是实现伪影，其根因是求积器在 `x→1` 的失效加上 `x >= 1.0` 早退，二者叠加。

### D6 — Dedup 登记：与未归档 change 的重叠

`fix-review-findings-voronoi-precision-and-lineage` 的 `tasks.md` 全部标记 `[x]`，但该 change **没有 `specs/` delta 目录**（仅有 `proposal.md` + `tasks.md`）。其范围与本批 24 条重叠：

| 该 change 条目 | 目标位置 | 对应本批 |
|---|---|---|
| L4 | `tests/test_distance.py:25-26,87` 缺 `f"actual="` | AC-03 / AC-61 |
| L5 | `tests/test_gating.py:42` `Σp=1` 缺 `f"actual="` | AC-38 |
| H2 / H2b / L7 | `tests/test_sphere.py` Voronoi 字面量恢复与收紧 | AC-08 / AC-12 |
| M4 | `openspec/specs/decompmoe-skeleton/spec.md:98` `abs=1e-4 → 1e-6` | AC-40（同一行） |
| G1 / G5 | `tests/test_schedule.py` | AC-77 / AC-61 |

**本 change 只登记，不处置。** 处置需要在动手施工前确认该 change 处于「已应用未归档」还是「停滞」两种状态中的哪一种——这会影响是否要避免重复施加同一处改动。

### D7 — 并行 session 与共享工作树：本 change 的验证方法修正

本 change 全程锚定 commit object（`git show 188b9fb:<path>`）而非工作树，**这一点救了本 change**。但有一次 `git status` 检查给出了错误结论，必须记录。

**事件**：本 change 末段验收时，`git status --porcelain -- src tests openspec/specs wayfinder` 从「仅 `wayfinder/tickets/WF-1.md`」变为 **8 个文件 modified**（`sphere.py` +67、两份 spec、四个测试文件，合计 `+691 / −48`），`pytest --collect-only` 从 **217 → 227 tests**。这些**全部不是本 change 的产物**——本 change 的 10 处编辑脚本只写 `openspec/changes/2026-10-01-*` 与 gitignored 的 `.audit/`。

**已独立核实**（避免误判成「我改坏了」或「并行 session 改坏了数值」）：

| 断言 | 验证方法 | 结果 |
|---|---|---|
| `sphere.py` 的并行改动是否改了功能 | 剥掉全部 docstring 后比对 `ast.dump` | **AST 完全相同** ⇒ **纯 docstring 改动**，不可能改变任何数值 |
| 本 change 的数值结论是否仍成立 | 工作树实跑 `cva(16,16)` 等 | `1.1735482746999482` / `1.1658482974306132` / `1.0205068335735599`，与 `188b9fb` **逐位一致**；E10 跳变仍为 `7.870852e-02` |

**并行 session 的 spec 改动未触及本 change 台账中的 F2 / F4**：`1.1735482746999482` 仍在 `skeleton:113`，量纲错误 `4.15e-7` 仍在 `:115`。⇒ **F2、F4 仍存活**，见 D4.4。

**修正的纪律**：任何用 `git status` 空/非空来证明「我没改 X」的检查，在共享工作树里**不成立**。归属必须按**显式路径**判定（本 change = 两个路径），而非按目录聚合状态。已据此重写 `tasks.md` 5.3。

**附带观察**：并行 session 独立地在 `sphere.py` docstring 里记录了与本 change 相同的伪影（π/2 不连续、90-ulp 与 1-ulp 之别、`_betainc_regularized` 在 `x→1` 的五阶误差增长），并在 `skeleton` spec 里把 `spherical_l2_normalize` 的输出范数从 `== 1.0` 改为 `approx(abs=1e-6)`（实测最坏偏差 `6.6613e-16`）。**独立收敛的同向发现**互为佐证，但两者都不构成对 F2/F4 的修复。

### D8 — 归档协议、anchor 基线与并发裁决

#### D8.1 已知的 archive 陷阱（来自并发 change 的实测）

`2026-10-02-audit-a2-errata-and-spec-math-fixes` 的 task 9.2 记录：**`openspec archive` 确实会吞掉 `<a id="req-N"></a>` 锚点**（wayfinder 36 → 35、decompmoe-skeleton 23 → 22），其 task 9.3 从 `git cat-file blob 188b9fb` 逐字节恢复后才复原。

本 change 风险较低但非零：`.openspec.yaml` 已声明 `skip_specs: true` 且**无 `specs/` 目录**（零 delta），archive 无 spec 可改写。但**不把「大概率没事」当保证**——归档时显式加 `--skip-specs` 双保险，并按 `CLAUDE.md` §3「archive 后必须复算 anchor 覆盖」逐份核对。

**恢复协议（若锚点被吞）**：从 `git cat-file blob 188b9fb:<path>` 取**原始字节**写回，`sha256` 与 D8.2 基线比对。**绝不重跑 archive**（重跑会再次应用 delta 并二次损坏）。

#### D8.2 归档前 anchor 基线（已复算，**code span 已剔除**）

| spec | 真实 anchor | code span 内提及 | Requirement | 覆盖 | 重复 id |
|---|---|---|---|---|---|
| `wayfinder/spec.md` | **36** | 2 | 36 | **100%** | 无 |
| `decompmoe-skeleton/spec.md` | **23** | 0 | 23 | **100%** | 无 |
| `governance/spec.md` | **4** | 0 | 4 | **100%** | 无 |

⚠️ **本 change 自己的计数器缺陷（记录以免复发）**：首次普查用裸正则 `<a id="(req-[^"]+)"></a>` 得出「wayfinder 38 anchors / 36 Requirements，`req-17` 与 `req-20` 重复」，**这是一个假发现**。逐行查上下文后发现多出的 2 处位于**反引号 code span 内**——`L432` 是 Cross-req consistency note 对 anchor 文本的**引用**（``Req 17 (anchored `<a id="req-17"></a>`)``），`L850` 是对 Requirement 的 prose 引用。二者都**不是 anchor 元素**。

⇒ 剔除 code span 后：**三份 spec 全部 100% 覆盖、零重复**，`CLAUDE.md` §6 的 anchor 纪律当前**满足**。

**判据纪律**：与本 change 早前的 AST `Compare` vs `Call`、PowerShell 反引号吞字符**同族**——**naive matcher 报出的"缺陷"必须先看匹配处的上下文再采信**。本次若直接把「重复 anchor」写进制品，就是一条与事实相反的发现。

#### D8.3 并发 change 已裁决 `fix-review-findings-voronoi-precision-and-lineage`

本 change 的 D6 / 勘误节 4.3 原把该 change 状态记为「未裁决，施工前必须先裁决」。**该问题已被并发 change 的 task 1.0 裁决**：

> 裁决 = **「已 inline 应用未归档」（非停滞）**。实测依据：`git ls-tree -r --name-only HEAD` 下该 change 仅有 `proposal.md` + `tasks.md`、**无 `specs/` delta**，故无规范效力；但其工作**已 inline 落地**——G1 `test_schedule.py:204` `round(g_reset, 5) == -0.06454` 带 `f"actual="`、G5 `:236-245`、`H2` `test_sphere.py:94-95`（`θ(16,16)≈1.173548` / `θ(17,16)≈1.165848`，`abs=1e-6`）、H2b `:117,142`（`round(degrees(θ),2) == 67.24 / 58.47`）、L5 `test_gating.py:42-43`。

⇒ **对 Change 1/2 的直接影响**：D4.4 台账中 L4/L5/H2/H2b/G1/G5 这几项**已有守卫在位**，Change 1 不应重复施加；真正缺守卫的是 H2b 之外的其余项。台账「与未归档 change 的重叠」登记据此更新。

⚠️ **遗留状态异常（不在本 change 修复范围，仅登记）**：该 change 的 `proposal.md` / `tasks.md` 在**工作树中已被删除**（`git status` 显示 ` D`），而 `HEAD` 仍追踪它们 ⇒ 目录在工作树中为空。若后续有人 `git add -A`，会把这次删除一并提交，等于静默丢弃该 change 的制品。**需人工裁决是恢复制品还是正式废弃**，本 change 不代为处置。

## Risks / Trade-offs

**[勘误本身会再次过期]** → 勘误的 HEAD 坐标以 `188b9fb` 为准并显式写出该 commit。任何后续 commit 都会使 HEAD 坐标失效，但 **pin 坐标与「错误本身」永久有效**。后续修复 change 若发现坐标又漂了，应**追加**新的勘误条目而非改写本节——保持勘误表只增不减。

**[归档被误当作活文档而整篇改写]** → 本 change 的 `## Errata` 节首行显式声明「原文结论一律不改写」，并写明理由（归档记录的是当时那轮 review run）。若后续仍有人改写正文，本节即是判定依据。

**[勘误缺一，导致实施者按错坐标/错数字施工]** → 验收要求逐条 `git show` 复核；`tasks.md` 按生效的 11 条（E1、E3、E5–E13）逐条列出检查项，缺一不算完成。

**[勘误本身采信了未经实测的转述]** → 已发生：E2 / E4 最初采信复核子 agent 的结论而未自行实测，导致两条无效勘误进入初稿。已在 apply 阶段逐条实测并撤回（D4.1）。**规则**：每条勘误的坐标必须由本 change 自己跑一次 `git show` / `git grep` 确认后才可写入，**不得从任何报告或对话记录转抄**。

**[E6（AC-77 不可达）被当作缺陷已消失而跳过修复]** → 勘误明确区分两件事：`β_p3` **域声明缺失**（仍成立，须修）与「域错误会兑现」（不成立，严重性下调）。后续 change 不得据此跳过 spec 域声明。

**[与未归档 change 重复施加]** → 见 D6。已登记为 open question，施工前必须裁决。

**[勘误表与 `context/` 归档不一致]** → 本勘误是**对清单的**更正，不修改 `context/00`–`07`（它们是 review run 的原始上下文）。二者会不一致，这是有意的：勘误反映后续复核的增量。

## Migration Plan

不适用（纯文档变更，无部署 / 无数据迁移）。

**回滚策略**：删除 `lists/opsx-changes.md` 末尾的 `## Errata` 节与本 change 目录即可，无残留状态。

## Open Questions

以下可安全延后，不影响本 change 的 spec、方案或任务拆分：

- **`fix-review-findings-voronoi-precision-and-lineage` 处于何种状态？** tasks 全 `[x]` 但无 delta，可能是「spec 已被 inline 修改、未走 delta 流程」，也可能是「停滞」。**该项在开始任何修复 change 的施工前必须裁决**——若为前者，本批 24 条中与它重叠的部分可能已被部分解决，需要在施工前重新定位。

- **E10 的修复归属哪个 change？** 该不连续是 `src/decompmoe/sphere.py` 的实现问题，按已批准的修复计划归属「spec + src 语义」那一个 change；本 change 只负责记录，不在此处裁决实施细节。
