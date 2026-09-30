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
- [x] 5.6 `openspec validate --specs` → 3 passed 0 failed

## 6. 归档

- [x] 6.1 `openspec archive <name> -y` → `~ 4 modified`，exit 0
- [x] 6.2 **anchor 覆盖复算** —— 见下方「归档实况」
- [x] 6.3 工作树 == commit object 核对

## 归档实况：archive 吞并 4 个 anchor（已修复）

归档前基座对账（tripwire）：delta 的 4 个 anchor 在主 spec 中各出现 1 次，scenario
集合逐一相同，body 差异恰为声明的 15 行 ⇒ **基座未漂移**。

`openspec archive` 报 `~ 4 modified` + exit 0，但**静默损坏**了主 spec：

- 吞掉紧随被改 Requirement 之后的 anchor：**`req-8` / `req-29` / `req-33` / `req-34`**
- 产生错位：block 序列塌缩到 35 个，`req-26` / `req-28` / `req-32` 各重复出现一次
- 三个 lint / validate **全部报绿**（`openspec validate --specs` 当时也是 3 passed）

**修法（不重跑 archive —— 重跑会再吞一次）**：
1. `git show HEAD:openspec/specs/wayfinder/spec.md` 取归档前内容作骨架（36 个 block，anchor→heading 配对正确）
2. 以 **HEAD 的 block 序列**为顺序（非损坏后的工作树序列），逐 block 拼接；4 个目标 block 换用归档 delta 的内容
3. 补回首个 anchor 之前的前言（`# wayfinder Specification` / `## Purpose` / `## Requirements`）—— 重建脚本以首个 anchor 为起点，前言不属任何 block，曾被整体丢弃并使 `validate` 报「Spec must have a Purpose section」
4. 断言：block 顺序 == HEAD、`changed blocks == {req-7, req-26, req-28, req-32}`、逐 block 差异 9/2/2/2 = 15 行

修复后核验：wayfinder **36 anchor / 36 heading / 0 重复 / 0 孤儿**，4 个 at-risk anchor
（`req-8` / `req-27` / `req-29` / `req-33`）全部在位；skeleton 23/23、governance 4/4 干净；
`validate --specs` 3 passed 0 failed；全量 217 passed；双 lint exit 0。

> 附注：早先一次 anchor 审计报 `dup=['req-17','req-20']`，经查是**假阳性** —— 正则未做行锚定，
> 命中了正文里两处**既有的交叉引用**（HEAD 与修复后同为 38 次命中 / 36 个行锚定 anchor）。
> 计数分母钉死后才判定 spec 干净。
