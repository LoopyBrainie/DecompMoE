# Tasks

- [x] 1.1 spec 先行：脚本生成 `wayfinder` req-32 的 MODIFIED delta。验证：pre-flight 3/3 命中；块级 `difflib` 回验；4 项 stale-token 扫描全过。**→ 完成。** 改动点：声明签名加必填 `c_centroids: Tensor (N_e, d_c)`；明写 clone source 是 `j_star` 行；Scenario 的 `c_perturbed` 由「primitive 裸 ε」改为 `L2Normalize(c_centroids[j_star] + ε)`；新增 2 条断言 + 1 条 Scenario。
- [x] 1.2 AC-43 `resurrect_expert` 实现克隆-扰动。验证：`c_perturbed = spherical_l2_normalize(c_centroids[j_star] + ε)`；`resurrection_perturb_distribution` **保持**返回裸 ε（它是分布原语，克隆归事件包装器）。**→ 完成。**
- [x] 1.3 AC-76 重写 docstring。验证：docstring 不再出现 `torch.empty(0)`；点明 primitive 的第一实参是 `f_per_expert`、`dim` 为 keyword-only 必填、来源 `cfg.d_c`。**→ 完成（附反向断言，钉住旧错误描述不得复现）。**
- [x] 1.4 AC-43/76 契约测试。验证：签名参数表逐项比对；`c_centroids` 无默认值且不在 `MVPConfig` 字段里；`‖c_perturbed‖₂ ≈ 1.0`（`abs=1e-6`）；`cos(donor) > 0`；`eps_std=0` 极限下 `c_perturbed == c_centroids[j_star]` 且 `!= c_centroids[i]`（`abs=1e-6`）；错形状 `c_centroids` 抛 `ValueError`。**→ 完成。**
- [x] 1.5 AC-17 `mask` 改必填并删除替代分支。验证：签名位置参数恰为 `['self','centroids','X','mask']`；省略 → `TypeError`；显式 `None` → `TypeError` 且消息指回 req-18。**→ 完成（9 处调用点全部补参）。**
- [x] 1.6 AC-17 重写 3 个退化期望值。验证：期望值改由 one-hot mask + 布尔索引独立求 `m_i`，不与实现的 `mask.T @ X / n_i` 共享代码路径；并补一条「EMA 输出不得坍缩为单点」的断言。**→ 完成。**
- [x] 1.7 AC-17 坍缩回归闭式。验证：999 次 per-expert EMA 步后平均成对距离 `1.421196`、cos `-0.023137`（`abs=1e-4`），对照被删除路径同期的 `0.396100 / +0.916776`（5999 步后 `0.000291 / +1.000000`）。**→ 完成（数值自算，见 design.md D7）。**
- [x] 1.8 AC-41 `UR` 加 W=100 窗口。验证：200 步历史（前半 3 个专家、后半为其子集 2 个）给 `2/16 = 0.125`，且 `UR(200 步) == UR(trailing 100)`；单步闭式 `3/16`；空列表 `0.0`；0 维输入抛 `ValueError`。**→ 完成。**
- [x] 1.9 AC-41 口径裁决。验证：实测台账两个「spec 值」分属两种聚合规则（design.md D5 表），采纳与 spec 英文注解一致的并集读法并把冲突写进 design.md；`R_H` / `S_load` 记为 out-of-scope（spec 未给 W）。**→ 完成。**
- [x] 1.10 公共面未被破坏。验证：`_UR_WINDOW_STEPS` 不在 `metrics.__all__` 也不在 `decompmoe.__all__`；`len(decompmoe.__all__) == 78`（`== 75 + 3 dunder`）。**→ 完成。**
- [x] 1.11 门禁。验证：`pytest` **255 passed**（242 + 新增 13）✅；`lint_no_dead_defensive.py` exit=0 ✅；`lint_no_source_field_drift.py` exit=0 ✅；三份 spec 形状 OK（37/23/4 anchors，无重复）✅；`openspec validate --type change --strict` ✅。
  > **本任务自造并修正的 3 个缺陷**（design.md D8）：① 生成脚本的 `\\n` 转义被吃掉一级，在目标测试文件留下真实换行导致 `SyntaxError`；② AC-17 回归闭式从台账搬了不可搬运的数，且搬的那一行本身差一次调用（`1.419604` vs `1.421196`）；③ 断言包级 `__all__` 为 75，漏了 C2 钉死的 3 个 dunder（实测 78）。三次都是「断言值未独立复算」。
