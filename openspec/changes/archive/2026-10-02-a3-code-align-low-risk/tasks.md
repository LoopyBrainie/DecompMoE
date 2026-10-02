# Tasks

- [x] 1.1 AC-73 删死分支。验证：`clip_grad_norm_` 运行时 `dim()==0`；删后返回 `float(pre_norm)`。**→ 完成。新测试同时钉「返回裁剪前范数」与「裁剪确实生效」。**
- [x] 1.2 AC-75 重命名投影参数为 `proj_W_K/proj_W_V/proj_b`。验证：按 req-7 写法**关键字**调用成功并反传梯度。**→ 完成。**
- [x] 1.3 AC-78 离线普查后再接线。验证：① AST 普查得并集 **75** / 求和 **76** / 冲突 `flops_per_token∈{config,metrics}`；② 13 个子模块逐个 `importlib` 全部可导入（无循环）；③ 并集 75 个名字在其声明模块上全部可解析。**→ 3/3 阶段完成后才改 `__init__.py`（design.md D1）。**
- [x] 1.4 AC-78 接线。验证：`__all__` 长度 **78**、无重复、每项 `hasattr` 可解析、`from decompmoe import *` 绑定 75 个名字。**→ 完成（`tests/test_a3_contract_alignment.py` 4 条）。**
- [x] 1.5 AC-78 `flops_per_token` 显式再绑定到 `config`。**→ 完成。首次生成时实测绑定到了 `metrics`（字母序覆盖），已按 design.md D2 改为 import 块后显式再绑定；`metrics` 镜像仍可达且仍是独立对象（有测试钉住）。**
- [x] 1.6 AC-79 探针加 `device=centroids.device`。**→ 完成。审计的治理理由已证伪，未据此改动 `d_c < 2` 的 `ValueError`。**
- [x] 1.7 AC-44 `total_steps` 贯通。验证：`_lambda_at` / `L_total` / `beta_effective` 签名均含 `total_steps`（默认 100_000）；`beta_effective` 实际转发给 `phase_beta_max`。**→ 完成。**
- [x] 1.8 AC-44 删除孤儿 `_PHASE_BOUNDS`。验证：核对 `phase_boundaries(100_000) == (1_000, 6_000, 26_000, 56_000, 100_000)`（**bare `==`**，整数闭式）。**→ 完成（design.md D4：该常量恰为 `phase_boundaries(100_000)`，属重复真相）。**
- [x] 1.9 更新被修复打破的既有测试。**→ `test_extract_C_signature` 跟随 req-7 新签名并加旧拼写必须消失的反向断言；`test_no_other_module_defines_should_resurrect` 改为比较对象身份以区分再导出与二次定义，并补包级可达性正向断言（design.md D3）。两条都**不是**简单改期望值。**
- [x] 1.10 门禁。验证：`pytest tests/` **242 passed**（227 + 新增 15）✅；`lint_no_dead_defensive.py` exit=0 ✅；`lint_no_source_field_drift.py` exit=0 ✅；三份 spec 形状 OK（本 change 不改 spec）✅；`check_ledger.py` 自测 T1–T7 exit=0 ✅。
  > **本任务自造并修正的两个缺陷**（design.md D5）：① 新测试断言 `clip_global_grad_norm_` 返回 ≈1.0，实测 3.22——该函数返回的是**裁剪前**范数，测试期望写错而非代码有错；② 新测试取 `step=3_000` 时两个预算的 Phase-2 进度都被 clamp 到 0，cap 恒为 1.0、断言恒假——改用 `step=16_000`。两次都是数值断言未独立复算，与 A-3 台账记录的问题同源。
