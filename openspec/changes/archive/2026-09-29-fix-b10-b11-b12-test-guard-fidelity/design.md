# Design — B10 / B11 / B12

> **Rev 3**：本 session 内 review 提出的**全部** finding 均已处置。Rev 1 的两处数学论证被证伪并修正（Rev 2）；Rev 2 遗留登记为 hand-off 的 **HIGH-1**（wayfinder 层二义 + 主语语义不符）与 **MEDIUM-4**（phases 0/4 无 Scenario）在本轮**关闭**（Decision 4 / Decision 5）。逐条留档见 §7、§8。

## Decision 1 — B10 限流边界的数学裁决：守卫 `⟺ Δ < R` 延后

`CLAUDE.md` §6 末条要求：数学语义选择必须给出**单调性蕴含链 + worked counterexample**，由数值闭式测试守护。

### 1.1 待裁决的命题

设 `Δ := current_step − last_resurrection_step`，`R := RESURRECTION_RATE_LIMIT_STEPS`（MVP `R = 1000`）。实现 `src/decompmoe/safeguards.py:93` 选读法 A（`<` 守卫），但 spec 措辞在 `Δ = R` 处二义，且无测试覆盖。

- **读法 A**：`D(Δ) ≡ [Δ < R]`
- **读法 B**：`D(Δ) ≡ [Δ ≤ R]`

### 1.2 单调性蕴含链

1. `D` 是 `Δ` 的**单调非增**函数：`Δ₁ ≤ Δ₂ ∧ D(Δ₂) ⟹ D(Δ₁)`。
2. `D` 恰有一个跳变点，故延后集 `{Δ : Δ < R}` 是**下开射线**、放行集 `{Δ : Δ ≥ R}` 是**上闭射线**，二者在 `Δ = R` 相接。

### 1.3 窗口读法的正确形式（Rev 1 假命题，已撤回）

Rev 1 论证「半开窗口族 `{[t, t+R) : t ∈ ℤ}` 把步数轴划分成互不相交的 `R` 长块，两事件同块 `⟺ Δ < R`」。**两半都不成立**，独立复算证伪：

- (a) 该族**不是划分**：实测 `|W₀ ∩ W₁| = |[0,1000) ∩ [1,1001)| = 999`，严重重叠。
- (b) 唯一真划分是 `R` 对齐块族 `{W_{kR}}`，但它**不满足** `Δ < R ⇒ 同块`：`t₁ = 999, t₂ = 1000` 有 `Δ = 1 < R` 却分属 block 0 / block 1（`(1,1000)`、`(500,1400)` 同样跨界）。

**成立的形式是逐对存在量词**，不含任何全局块结构：

```
两事件 t₁ < t₂ 同处某个 R 长半开窗 [t, t+R)  ⟺  ∃t. t ≤ t₁ < t₂ < t + R  ⟺  Δ < R
```

已在 `Δ = 1 / 999 / 1000 / 1001 / 2000` 五组取值上逐点复算通过。spec 内**显式记录窗口族非划分**及 `R` 对齐反例，防止后人再次误用。

### 1.4 反例：读法 B 被证伪

事件流 `0, R, 2R, 3R, …`（每个恰比前一个晚 `R`）。读法 B 下每个 `Δ = R` 事件被判延后，而延后的实现是**直接丢弃** —— `should_resurrect` 返回 `set()`，**不持待重试队列**。于是对任何「不比起放行更频繁地推进 `last_resurrection_step`」的调用方，**实际事件率严格低于每 `R` 步一次**，与 `wayfinder` Req 13 的 "once per 1000 steps" 矛盾。读法 A 下全部放行，周期恰为 `R`。⟹ 读法 B 证伪。

> **Rev 1 的 `2R = 2000` 已撤回。** 该周期只在「仅放行时推进」模型下成立（另一模型为 `∞`）；且 `git grep last_resurrection_step -- src tests` 显示**全仓无任何写入方**（唯一读取处 `safeguards.py:93`，`resurrect_expert` 内 `"step"` 零出现），故任何具体周期都源自仓内不存在的契约。反例改写为**对全部调用方模型成立**的表述。

### 1.5 守卫与其它空返回路径的区分（Rev 1 过度断言，已修正）

Rev 1 写「every `Δ ≥ R` is **emitted**」，为假：`safeguards.py:95-96`（`len(f_history) < consec`）与 `:100-101`（无 expert 满足逐 step 触发）是两条**与限流无关**的独立空返回路径。THEN 因此只断言**限流守卫本身**的语义，并显式声明另两条路径不是 deferral。

### 1.6 守护

`tests/test_safeguards.py::test_should_resurrect_rate_limit_boundary` 三个闭式断言：`Δ = R−1` → `set()`；`Δ = R` → 非空（**边界，本测试的存在理由**）；`Δ = R+1` → 非空。

**变异证明**：`safeguards.py:93` 的 `<` → `<=`，测试变红，消息 `Δ=R is the first NON-rate-limited step and MUST fire; R=1000, actual=set()`。独立 review 另以 8 个变异体（两方向 off-by-one、`<2R`、`<=0`、去守卫、永不超时、忽略 `last_resurrection_step`）复测，**8/8 全部被单独捕获**。全域扫描 `Δ ∈ [0,2003]`，实现延后集恰为 `{Δ : Δ < 1000}`。

## Decision 2 — B11 4dp 显示值用精确 `round()` 守护

### 2.1 仓内先例

`decompmoe-skeleton` req-6 L98 对 `θ` 的 4 位小数 spec 显示值明文规定「MUST NOT be paired with the `abs=1e-6` tolerance … **instead guarded by exact `round(θ, 4) == 1.1735`**」。versine 的 `0.6131` / `0.4771` 属同一类，适用同一规则。

### 2.2 数值依据（已由测试逐值对账）

| pin | 偏差（精确） | 6 位有效数字 | 4dp 半单位 | 余量 | `round(v,4)` |
|---|---|---|---|---|---|
| `0.6131` | `1.7840938828506125e-05` | `1.78409e-5` | `5e-5` | `2.80×` | `0.6131` ✓ |
| `0.4771` | `3.400709512374478e-05` | `3.40071e-5` | `5e-5` | `1.47×` | `0.4771` ✓ |

Step 2c 以 6 位有效数字 + `abs=1e-10` 钉住（`~1e-5` 量级第 6 位有效数字落在 `1e-10` 位），另加 `dev < 5e-5` 严格界 —— **后者才是 spec 的承重声明**。

> 该守护初版写 7 位有效数字配 `abs=1e-12` 时**立即变红**：7 位截断与精确值差 `1.17e-12 > 1e-12`。这证明「把数字写进 spec 却不加对账」会留下连作者都钉不住的声明。Rev 1 只在注释描述偏差、未构成可验条款，违反 `CLAUDE.md` §6。

### 2.3 旧容差的实测漏检

`abs=1e-4` 恰为 4dp 半单位的 2 倍。构造 `v(16,16)` 偏移 `+8.0e-5` → `0.6131978409388285`，距 `0.6131` 为 `9.784e-5 < 1e-4`：旧 `approx(abs=1e-4)` **接受**，`round(v,4) = 0.6132` **拒绝**，测试变红。

> 扰动量必须**叠加在基准已有的 `1.784e-5` 之上**才落在旧窗口内。若按 `+9.9e-5` 构造，总距 `1.168e-4 > 1e-4`，旧守卫**同样**会红，证明不了新旧差异。

### 2.4 为什么不采用 finding 建议的 `abs=5e-5`

`0.4771` 偏差 `3.400710e-5`，`abs=5e-5` 余量仅 `1.47×`（`0.6131` 为 `2.80×`），且仍与 req-6 的 4dp-display 原则不同构。

### 2.5 obligation 冲突及其处置

`req-gov-1` obligation 2（L15）要求 float 闭式「MUST use `pytest.approx(...)` … **NOT bare `==`**」，其举例本身就是 req-6 强制 `round(θ,4) == 1.1735` 的那一条 —— **该冲突在 Rev 1 之前就已存在于 req-gov-1 内部**。Rev 1 把 versine 塞进同一 Requirement 而未加豁免，使冲突加剧。

**Rev 1 一处成因分析是错的**：原称「versine 依赖末句 'on an **angle** claim' 限定才被 carve-out」。**不成立** —— versine 是 `1 − cos θ`，**不是 angle claim**，该限定从未覆盖过它。真正需要豁免的是 obligation 2 的「NOT bare `==`」。

**处置**：obligation 2 新增 **Exception — 4-decimal spec display literals**（4 位小数 spec 值是*显示形式*，用精确 `round(x,4) == literal` 守护，依 req-6；**不得**配超过 4dp 半单位 `5e-5` 的 `abs=`；底层更高精度声明若另行给出仍按 obligation 2 守护）；obligation 3 新增 scope 声明（其 `abs=1e-6` **只管 angle literal**，versine 归 obligation 2 豁免）。obligation 6 合规：显式记录旧 `abs=1e-4` blessing 被 supersede 的关系与实测依据。

### 2.6 `round()` 的检出能力边界

独立 review 复刻 bisection 逐档放宽测得：`round(v,4)` 守护**会**漏判「残差放宽到 1e-6」这一档（`|Δθ| = 2.04e-06`，破防阈值 `3.49e-5` rad @ N_e=16）。但 `test_voronoi_residual_below_1e_minus_9` 与 6dp `abs=1e-6` 角度 literal **先红**，套件整体不漏；且新带 `[lit−5e-5, lit+5e-5] ⊂` 旧带 `[lit−1e-4, lit+1e-4]`，**不构成回归**。

⟹ 正确定位：**`round()` 是「舍入语义上的」精确判定，漂移检出弱于既有的残差 / 6dp 角度守护，属第三道防线。** Rev 1 称其为「精确判定」易被误读为它承担漂移检测。

## Decision 3 — B12 修 docstring 而非断言

`test_phase_step_frozen_names_phase_0_and_4_empty_set` 的两个断言经核验**正确**：`phase_step_frozen_names` 返回「要冻结的 gradient-channel 名字集」（`src/decompmoe/schedule.py:65-82`，L82 `return set()` fallback）。

Phase 0 按 `wayfinder/spec.md:83`（req-6）「Spherical K-Means seeding (no gradient, no EMA)」及 phase 表 L617（req-27）`| 0 | K-Means seeding | Frozen (requires_grad=False) | N/A |`，**不存在被训练的 gradient channel**，冻结名集合必为空集。docstring 原写「freezes everything by K-Means definition」，按字面会推出**全集**，与所断言的 `set()` 自相矛盾 ⟹ 改 docstring，不改断言。Phase 4 理由（`wayfinder/spec.md:338`）正确，保留。

**Rev 1 在此引入了一处新的错误归属**：新 docstring 曾写 `wayfinder req-14`，而 `"no gradient"` / `"no EMA"` 实际在 **L83 / req-6**、phase 表在 **L617 / req-27**。已按实测改写 —— 与 B12 是同一缺陷类，只是换了位置。

`L295` 的过期归因：`git show de96ba6~1` 显示 anchor 原本不存在、heading 在 L293；`git show de96ba6` 显示 anchor L293、heading L295，而 docstring 同在该 commit 写下 ⟹ **`L295` 在作者当时准确**（指向 heading 行），是后续 spec 增长致其 stale，非出生即错。

## Decision 4 — wayfinder req-13 重述：边界钉死 + 主语语义纠正（关闭 HIGH-1）

`wayfinder` 是 init decision，优先级高于 skeleton。产生二义措辞的源头是 `wayfinder/spec.md:314`（"rate-limited to once per 1000 steps"）与 `:326-328` Scenario，Rev 2 只在 skeleton 侧钉边界，故二义在 init decision 层仍然存在。本轮补 wayfinder delta。

**问题一（边界二义）**：原 WHEN 写 "two experts meet the dead-expert trigger within the same 1000-step window"，未说明 `Δ = R` 归属。新 Scenario 改为显式的 `Δ` / `R` 表述，声明**窗口边缘是排他的**（`Δ = R` **不**延后），并指向 `decompmoe-skeleton` req-12 Scenario「Resurrection rate-limited」为规范形式化（避免两处推导漂移）。

**问题二（主语语义与实现不符）**：原 THEN 写 "only one resurrection event executes; the second is deferred"，描述的是**每窗口只复活一个的配额**。而 `should_resurrect` 在 `src/decompmoe/safeguards.py:98-102` 的循环中把**每个**满足逐 step 触发的 expert 都加入 `flagged` 并整体返回，**不做任何 one-per-window 裁剪**。实测该返回路径产出的是合格 expert 全集。

⟹ 新 Scenario 加入 **Scope correction** 段：明确限流是**每次调用的延后闸门**（per-call deferral gate），不是每窗口配额；被 supersede 的读法**明文记录**而非静默丢弃。这是对 init decision 语义的实质性更正，故在 delta 的 `**Source:**` 中显式标注 Decision 4 以便审计。

## Decision 5 — skeleton req-13 补 phases 0/4 Scenario（关闭 MEDIUM-4）

`skeleton/spec.md` req-13 正文 L307 规范句 "empty for phases 0/4" 此前**无对位 Scenario**（该 Requirement 下仅 4 个 Scenario：Phase boundaries / Phase-1 router freeze / Phase-2 expert freeze / Adam reset boundary）。B12 恰好把 `test_phase_step_frozen_names_phase_0_and_4_empty_set` 的引用改指这条正文句，等于**加固了一个无 Scenario 承载的规范句** —— 缺口与本次修的是同一类。

新增 `#### Scenario: Phase-0 and Phase-4 freeze-name set is empty`，紧接 Phase boundaries 之后（保持 phase 顺序），内容与 B12 修正后的理由一致：Phase 0 无 gradient channel ⇒ 集合真空为空（**不是**「全冻结」⇒ 全集）；Phase 4 解冻整个 gradient channel。断言 `set()` 的精确类型约束（NOT `frozenset()` / NOT `None` / 非空）一并写入规范。

**注意**：skeleton req-13 **没有 `**Source:**` 行**（既存状态，`lint_no_source_field_drift.py` 通过，说明非必需）。本 change **不凭空添加** Source 字段；该 Requirement 的变更血缘记在本 delta 与 `design.md`。

## Decision 6 — delta 的换行约定（LF），与「逐字节相等」的调和

`decompmoe-skeleton/spec.md` 文件本身是 **CRLF**（623 CRLF / 0 LF），`governance/spec.md` 是**纯 LF**。初版方案要求 delta「与主 spec 逐字节相等」且「无 CRLF」，二者在 skeleton 上直接冲突。实测：2026-09-08 之前 skeleton delta 多为 CRLF；**2026-09-08 及之后全部 23 个 skeleton delta 均为纯 LF**，含最近成功归档者，**即便主 spec 至今仍是 CRLF**。

⟹ **LF delta 作用于 CRLF 主 spec 是本仓既定且可行的约定。** 故三份 delta 一律 **LF、无 BOM**；「逐字节相等」按**行内容**（忽略行终止符）判定。

对账分两类：**替换型**（skeleton req-12 / governance req-gov-1 / wayfinder req-13）走逐行 diff，只允许定点行不同且 Source 为纯追加；**插入型**（skeleton req-13）走「移除插入段后必须逐行等于主 spec block」的证明式对账。

> 逐行对账曾当场抓到两个真实问题：① 初版用子串替换追加 provenance，**把 Source 行后半截（`fix-openspec-doc-bugs` Decision 7 等既有 lineage）整段截断** —— 改为定位 `**Source:**` 行整行追加后修复；② Rev 1 硬编码行号，而 `req-gov-2` 锚点在 archive 后由 L56 移至 L58 —— 改用**锚点定位**。

## 7. 独立 review 推翻的 Rev 1 结论（逐条留档）

| # | Rev 1 主张 | 裁决 | 处置 |
|---|---|---|---|
| 1 | 半开窗口族划分步数轴，两事件同块 `⟺ Δ<R` | **FALSE**（`|W₀∩W₁|=999`；`t₁=999,t₂=1000` 反例） | 撤回，改逐对存在量词 + 记录非划分（D1） |
| 2 | every `Δ ≥ R` is emitted | **FALSE**（两条独立空返回路径） | 收窄为守卫语义（D1.5） |
| 3 | versine 靠「on an **angle** claim」限定被 carve-out | **FALSE**（versine 非 angle claim，从未覆盖） | 改为在 obligation 2/3 加 4dp-display 豁免（D2.5） |
| 4 | `2R = 2000` 有效周期 | **PARTIALLY TRUE**（仅一种调用方模型；另一模型为 `∞`；仓内无调用方） | 改为对全部模型成立（D1.4） |
| 5 | 新 docstring 引用 `wayfinder req-14` | **FALSE**（属 req-6 L83 / req-27 L617） | 按实测改写（D3） |
| 6 | `test_sphere.py` Step 3 的 `spec L233` | **FALSE**（区分句在 L235） | 改为 `wayfinder/spec.md L235` |
| 7 | `round()` 是「精确判定」 | **措辞过强**（残差放宽到 1e-6 时漏判） | 改述为第三道防线（D2.6） |
| 8 | wayfinder 层二义（**HIGH-1**） | **TRUE** | **本轮关闭**（D4） |
| 9 | phases 0/4 无 Scenario（**MEDIUM-4**） | **TRUE** | **本轮关闭**（D5） |
| 10 | `L123 assert RATE_LIMIT == 1000` 可能恒真 | **FALSE**（变异 1000→200 变红；另 `test_named_constants_have_spec_values` 亦钉该常量） | 按 surgical 原则保留 |

**未被推翻的 Rev 1 结论**：全部 versine 数值（bit-identical、偏差 `1.784094e-5` / `3.400710e-5` 均 < `5e-5`）；`+8.0e-5` 变异体旧守卫接受 / 新守卫拒绝；M1 变异使新测试变红；删除 L143/L146 安全；`Δ = R` 结论方向正确；delta 对账与卫生。

## 8. 剩余 Hand-off（本 change 不修）

1. **`openspec validate --changes` 存在 4 个既存失败**：`2026-09-26-followup-spec-wording-bugs-after-precision-disclosure`、`fix-review-findings-voronoi-precision-and-lineage`，以及并行 session 的 `2026-09-29-fix-b13-b16-src-docstring-and-line-ref-drift`、`2026-09-29-fix-b15-test-loss-actual-embedding` —— 均为「Change must have at least one delta」。**本 change 自身校验通过**（`openspec validate 2026-09-29-fix-b10-b11-b12-test-guard-fidelity` → valid）。非本 change 引入。
2. **`2026-09-26-followup-.../tasks.md`** 表格行 `A2.2.1 | L293 | L303 | ✅ commit de96ba6` 与 git 实测不符（`de96ba6` 结束时 anchor L293 / heading L295）。该 change 已归档，仅记录。
3. **`governance` obligation 3 首句的宽口径表述**（「一切 `canonical_voronoi_angle` 派生值 MUST `abs=1e-6`」）未改写；本 change 已在 obligation 2/3 内加显式 exception，张力由「隐式 carve-out」转为「明文 exception」。若要把 4dp-display 提升为全局政策，需另开 change 统一收口。
4. **未清理的临时产物**：`_bk/`、`_patches/`、`_staged/`、`_tmp_verify_voronoi*.py` 等 —— 本 workspace 批量删除通道不可用，交由用户处理。
