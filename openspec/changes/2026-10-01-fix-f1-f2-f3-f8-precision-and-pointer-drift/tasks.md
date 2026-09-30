# Tasks — F1/F2/F3/F8 精度与指针漂移

## 1. 核验（mpmath 独立复算，不转述 review 结论）

- [x] 1.1 `σ'(−3.5)` 真值复算至 31 dp —— `0.0284530238797355598396878271273`
- [x] 1.2 量化 20-dp 转写与真值之差 = `3.12e-22`，相对 `abs=1e-30` 为 `3.12e8 ×` ⇒ 原 Requirement 不可满足
- [x] 1.3 量化 31-dp 转写与真值之差 = `3.93e-34` ⇒ `0.39 ×`，可满足
- [x] 1.4 量化 float64 在该量级的分辨率 `≈6.3e-18`，比 `abs=1e-30` 粗 11 个数量级 ⇒ 经 `float()` 的比较使容差惰性
- [x] 1.5 `γ' = ln(15/16) = −0.0645385211…`，5-dp 半单位 `5e-6`，原 `abs=1e-4` = `20 ×` 半单位
- [x] 1.6 `phase_beta_max(3, 55_999) = 15.9996`，4-dp 半单位 `5e-5`，原 `abs=1e-4` = `2 ×` 半单位
- [x] 1.7 逐条解析 F8 的 6 个指针（4 测试 + 2 spec `Source:`），确认归属；`test_schedule.py:64` / `:66` 经核验**正确**，保留

## 2. Spec delta

- [x] 2.1 由 `git show HEAD:` 程序化切块生成 `specs/wayfinder/spec.md` delta（4 anchor / 4 heading，残留全 0）
- [x] 2.2 req-7：31-dp 转写 + `mpf` 双侧比较强制 + 20-dp 反例入 THEN
- [x] 2.3 req-7：narrative 4-sig-fig 改由独立 `round(σ′, 5) == 0.02845` 钉住
- [x] 2.4 req-7：连带修复 paired 断言的 `abs=1e-5`（= 2 × 半单位）→ round 形态
- [x] 2.5 req-26：5-dp 字面量改 round 形态，删 `abs=1e-4`
- [x] 2.6 req-28 / req-32：`**Source:**` 裸行号 → 函数名 + 既有 commit SHA

## 3. 测试

- [x] 3.1 `tests/test_beta.py`：mpf 直比 `abs=mpf('1e-30')`，不经 `float()`
- [x] 3.2 `tests/test_beta.py`：新增 `round(sp_mp, 5) == 0.02845`（**必须 float 字面量**）
- [x] 3.3 `tests/test_beta.py`：docstring 重写为「两帧」+ 写入 float64 塌缩陷阱
- [x] 3.4 `tests/test_schedule.py`：`round(g_reset, 5) == -0.06454` + `actual=` msg
- [x] 3.5 `tests/test_schedule.py`：`round(beta_max_last, 4) == 15.9996` + `actual=` msg
- [x] 3.6 `tests/test_schedule.py`：`beta.phase4_inverse_temperature` 断言补 msg（返回 Tensor，需 `float()`）
- [x] 3.7 `tests/test_schedule.py`：F8 的 4 处指针改 Requirement 名
- [x] 3.8 `tests/test_schedule.py`：注释改引 `spec req-26` / `spec req-29 "…"`（不再用裸行号）

## 4. 负向变异验证（绿灯不等于守护有效）

- [x] 4.1 F1 守护捕获 `+1e-25` 扰动
- [x] 4.2 F1 守护捕获 `+1e-18` 扰动（旧 float 形态对该扰动**照样通过**，构成对照）
- [x] 4.3 F2 守护拦下偏 `9e-5` 的 γ-reset（旧 `abs=1e-4` 放行，构成对照）

## 5. 门禁

- [x] 5.1 `uv run pytest tests/test_beta.py` → 13 passed
- [x] 5.2 `uv run pytest tests/test_schedule.py` → 17 passed
- [x] 5.3 `uv run pytest -q` 全量
- [x] 5.4 `python scripts/lint_no_dead_defensive.py` → exit 0
- [x] 5.5 `python scripts/lint_no_source_field_drift.py` → exit 0
- [ ] 5.6 `openspec validate --specs` → 0 failed

## 6. 归档

- [ ] 6.1 `openspec archive <name> -y`
- [ ] 6.2 **anchor 覆盖复算**（`req-8` / `req-27` / `req-29` / `req-33` 逐个核对是否仍在）
- [ ] 6.3 工作树 == commit object 核对
