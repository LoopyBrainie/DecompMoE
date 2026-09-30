# Tasks — F4/F5/F6/F7 loss 接线与守护保真度

## 1. 核验

- [x] 1.1 确认 `wayfinder` req-12 闭合式 `L_lb = N_e · Σ_i f_i.detach() · P_i` 中 `N_e` 为模型级常量
- [x] 1.2 确认 `loss.py:115` 乘子取 `f_per_expert.shape[-1]`（运行时观测），而签名已有权威 `cfg`
- [x] 1.3 确认 `compute_L_sep` 的 `N_e = G.shape[0]` 是定义性的 ⇒ 不需改
- [x] 1.4 逐条确认 F5 三处自指：`compute_L_sep` 直调绕过 `L_total`；`test_lambda_fixed_phase_4` 两边同源；`L_total` 三项组合无测试
- [x] 1.5 确认 F7 删除 `ref` 后 `c` 变 unused ⇒ 删除范围须含 L169

## 2. 代码

- [x] 2.1 `loss.py`：乘子改 `N_e = cfg.N_e if cfg is not None else f_per_expert.shape[-1]`
- [x] 2.2 `loss.py`：`cfg` docstring 由「reserved for future spec requirements」改为如实描述其唯一职责

## 3. 测试

- [x] 3.1 F5：新增 `test_sep_raw_wired_into_l_total` —— 由 `c` 独立重推 spec 闭合式，钉 `L_sep_raw`（`abs=1e-9`）
- [x] 3.2 F5：同测追加 `L_sep = λ·L_sep_raw` 段
- [x] 3.3 F5：同测追加 `L_total = L_CE + L_lb + L_sep` 三项组合段
- [x] 3.4 F5：setup 断言 `expected_sep_raw > 0`，避免退化质心使平凡断言静过
- [x] 3.5 F4：新增 `test_lb_N_e_comes_from_cfg_not_tensor_width`，以刻意的 cfg/宽度不一致钉 cfg 优先级
- [x] 3.6 F6：两条 `torch.allclose` 补 `actual=` 消息
- [x] 3.7 F7：删除 L169–173 死脚手架（`c` / `ref` / `assert ref > 0` / `del ref`）
- [x] 3.8 F7：同步改写 docstring 尾句（去掉已删脚手架的用途描述）

## 4. 负向变异验证

- [x] 4.1 `L_sep_raw` → `torch.zeros(())` ⇒ `test_sep_raw_wired_into_l_total` 转红（1 failed / 10 passed）
- [x] 4.2 `L_total_t` 去掉 `L_sep` ⇒ `test_sep_raw_wired_into_l_total` 转红（1 failed / 10 passed）
- [x] 4.3 `N_e` 改回 `f_per_expert.shape[-1]` ⇒ `test_lb_N_e_comes_from_cfg_not_tensor_width` 转红（1 failed / 10 passed）
- [x] 4.4 三次变异各自**恰好** 1 failed 且失败者即预期测试 ⇒ 新测试非偶然转红
- [x] 4.5 变异后按原始 bytes 还原并校验 `p.read_bytes() == orig`

## 5. 门禁

- [x] 5.1 `uv run pytest tests/test_loss.py` → 11 passed
- [x] 5.2 `uv run pytest -q` 全量 → 217 passed（基线 215 + 本 change 新增 2）
- [x] 5.3 `python scripts/lint_no_dead_defensive.py` → exit 0
- [x] 5.4 `python scripts/lint_no_source_field_drift.py` → exit 0
- [x] 5.5 `openspec validate 2026-10-01-fix-f4-f5-f6-f7-loss-guard-fidelity` → exit 0
- [x] 5.6 `openspec validate --specs` → 3 passed 0 failed

## 6. 归档

- [x] 6.1 `openspec archive <name> -y --skip-specs`（本 change 无 spec delta）
- [ ] 6.2 三份主 spec 的 anchor 覆盖计数例行复算
- [ ] 6.3 工作树 == commit object 核对
