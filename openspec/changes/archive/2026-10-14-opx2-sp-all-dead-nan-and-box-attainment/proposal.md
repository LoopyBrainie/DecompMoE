# Proposal

## Why

审计台账 OPX-2 桶 4 条中，本轮实测确认 2 条成立（基线 `3c64cdc`）。它们有一个共同形状：**规范侧从未规定某状态，或条文侧写了一个在定义域内恰好为真的错误公式，于是缺陷既躲过了 review，也躲过了全部测试。**

- **FIX-006（`wayfinder` req-20 / `decompmoe-skeleton` req-22 · 全死 SP 哨兵）**：两份 spec 只规定了**单个**死专家的 `SP_i` 行为（`SP_i` 报告为 `undefined`，MUST NOT 报 `0`），**从未规定全体皆死时聚合 `SP` 的行为**——而 `SP = mean({SP_i : ‖T_i‖₁ > 0})` 在全集为空时是 `mean(∅)`，未定义。规范空白之下，`src/decompmoe/metrics.py` 的两条早退（`:140` 的 `C_t.numel() == 0`、`:153` 的 `not per_expert_means`）都返回同一个模块级 `_ZERO = torch.zeros(())`，与一次合法的活测量 `SP = 0.0` 在**位层面完全相同**（实测 `torch.equal` 为 `True`，repr 同为 `'tensor(0.)'`）。唯一可分辨点是对象身份 `live is _ZERO`，而 `_ZERO` 不在 `__all__`、全仓 `is _ZERO` **零命中**——即「可分辨」本身没有任何调用者。所以这不是一个稀有的浮点巧合（20000 组随机活配置中 `|SP| ≤ 1e-8` 命中 **0** 组），而是一个**语义上本就无出口的状态**，靠对抗式构造即可稳定触发。
- **FIX-007（`wayfinder` req-30 · β 盒界取等措辞）**：`:778` 单行内含三处缺陷。派生式写成 `∂logit/∂C = β · c / ‖C‖`，而真实导数是 `β · c`（`logit = β(C^T c − 1)` 对 `C` 线性，**无 `‖C‖` 分母**）——在定义域 `‖C‖ = 1` 上二者恒等，故该式恒等成立、测试永不失败；`‖C‖ = 2` 处它给出 16 而 autograd 给出 32。同时 `MUST be attained` 把 `β = 0.1 + 31.9·σ(γ)` 的**上确界**（对一切有限 `γ` 严格小于 32）断言成了可达最大值，`:783-784` 的 Scenario 又以符号值 `β = β_max` 继承了这同一处错误。`c_i` 侧零覆盖：全仓 10 处 `autograd.grad` 调用无一以 `c_i` 为求导变量。

另两条（FIX-034、FIX-042）经**反向锚定复核**判定不成立，零 spec delta，证伪证据记入 `design.md`（见该文件 D-4）。

## What Changes

- **为「全体皆死时的聚合 `SP`」补一条规范**（`wayfinder` + `decompmoe-skeleton` 成对 ADDED，两侧逐字镜像以维持 `#req-22` 对 `#req-20` 的既有镜像义务）：规定聚合 `SP` 返回 `NaN`（`undefined` 编码，与既有单死场景的 `e.g. … NaN … or omitted` 候选项一致），MUST NOT 报 `0.0`；并声明 `NaN` 按约定位于 `SP ∈ [-1,1]` **之外**，`SP range bound` 场景的 `-1 - 1e-6 ≤ SP ≤ 1 + 1e-6` 只对有限结果断言，`NaN` MUST NOT 参与任何聚合。
- **纠正 `wayfinder` req-30 的盒界条文**（MODIFIED）：把见证条件从「在最坏配置 `c ⟂ C` 处取到」改为陈述 `‖∂logit/∂C‖₂ = β‖c‖₂` **与夹角无关**（正交只是一个见证）；把派生式改为 `∂logit/∂C = β · c` 并标注旧式 `β · c / ‖C‖` 仅在 `‖C‖ = 1` 上成立；把 `MUST be attained` 改为上确界措辞。`:783-784` 的 Scenario 一并改为极限/闭包措辞，消除 Requirement 与 Scenario 互相拆台。**同行 γ 侧 `|∂logit/∂γ| ≤ 15.95` 及 `:787-788` Scenario 经 ARC-009 复算正确，逐字保留。**
- **让实现与新契约一致**：`src/decompmoe/metrics.py` 中属于 `SP` 的两条早退（`:140` 的 `T = 0`、`:153`）改为返回 `NaN`，位层面不可区分性随之消失，且不引入新哨兵。**`_ZERO` 常量与其余 3 处 return（`:103` / `:165` / `:228`）原样保留**（基线 `3c64cdc`，复算 `grep -n _ZERO src/decompmoe/metrics.py`）——那 3 处属 CG / D_chord / R_H / MCI 退化分支，即台账 FIX-025，落 DIR-2 桶，不在本 change 范围（见 `design.md` D-2）。
- **补齐两处零覆盖**（覆盖缺口正是这两个缺陷得以长期潜伏的原因，不补即部分闭合）：SP 全死路径（实测插桩：5 次 `SP` 调用中全死 **0** 次）含**判别性断言**——复用台账的决定性对抗构造，断言全死结果与一次合法的活测量 `SP = 0.0` 不 `torch.equal`；`c_i` 侧梯度守护（0°–180° 角度扫描下 `‖∂logit/∂C‖₂ == β·‖c‖₂` 逐点成立，且 `‖C‖ = 2` 处修正后的公式与 autograd 对账一致）。（基线 `3c64cdc`）
- **范围边界**：FIX-034（`A_i` 的 seeded-Monte-Carlo 性质「未在任何一份 spec 中说明」）、FIX-042（`SOURCE_EXEMPTIONS` 20/70 豁免）经复核**判定不成立**，零 spec delta，其证伪证据与可复现命令记入 `design.md`。`tests/` 层的 32 条 DIR 桶与 `.audit/**` 的 DIR-5 桶均不在本 change。（基线 `3c64cdc`）

## Capabilities

### New Capabilities

（无。本 change 不引入新 capability。）

### Modified Capabilities

- `wayfinder`: Requirement `#req-20`（Eight Geometric Quantification Metrics）新增一条承载「全体皆死时聚合 `SP` 的行为」的 Requirement（`NaN` 编码 + 值域 carve-out + 不参与聚合）；Requirement `#req-30`（Closed-Form Gradient Bound Worst Case）的取等见证条件、导数派生式与量词措辞三者被纠正。
- `decompmoe-skeleton`: Requirement `#req-22`（Eight Metrics And Classification — CG Type Guard）新增与 `wayfinder` `#req-20` **逐字镜像**的同一条 Requirement，以维持 `#req-23` 确立的镜像义务。

## Impact

- **spec**：`openspec/specs/wayfinder/spec.md`（新增 1 个 Requirement anchor + `#req-30` 正文重写）、`openspec/specs/decompmoe-skeleton/spec.md`（新增 1 个镜像 Requirement anchor）。**anchor 总数由 74 变为 76**——原因与取舍见 `design.md` D-7。
- **src**：`src/decompmoe/metrics.py`（仅 `SP` 的两条早退 `:140` / `:153`；`_ZERO` 定义与另 3 处 return 不动）。基线 `3c64cdc`，复算 `grep -n _ZERO src/decompmoe/metrics.py`。
- **tests**：`tests/test_metrics.py`（SP 全死路径 + 判别性断言）、`tests/test_beta.py`（`c_i` 侧梯度守护）。均为**新增**，不改既有 5 处 SP 断言的期望值——`SP` 的活路径返回值不受本 change 影响。
- **门禁**：不新增 lint。归档前须走 `req-gov-10` 的 anchor 四步协议（写账本 → 归档 → 比对 → 手术式补回 → 复测），且**禁止重跑 archive**。
- **工作树**：本 change 不触碰既有的 3 处未提交修改（`.gitignore`、`src/decompmoe/gating.py`、`wayfinder/tickets/WF-1.md`）；门禁输出中的 `dirty_entries=3` 属既有基线，不作为本 change 的失败判据。
