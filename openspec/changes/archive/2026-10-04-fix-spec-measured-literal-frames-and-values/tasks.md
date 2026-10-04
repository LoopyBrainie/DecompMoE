# Tasks: 2026-10-04-fix-spec-measured-literal-frames-and-values

1 spec delta（`decompmoe-skeleton` req-6），0 `src/`、0 `tests/` 改动。

## 1. 事实核验（先测后写）

- [x] 1.1 确认 `voronoi_angle` 的确定性来源：`sphere.py:245 VORONOI_AREA_SAMPLES = 1_000_000` + `sphere.py:259 VORONOI_AREA_SEED = 20260929` 均为模块常量 ⇒ spec 里的 `measured …` 是**可逐位复现的事实**，不是随机样本。
- [x] 1.2 重测 equal-area 三个 gap（`crosspolytope32` / `greatcircle16` / `greatcircle8`），**使用 `tests/test_sphere.py` 自己的 fixture 构造函数**（`importlib` 载入测试模块，不重新实现构造）⇒ `6.4561e-5` / `2.4817e-5` / `2.2667e-5` 度。
- [x] 1.3 重测单侧性三个 gap + σ 倍数 + 两个 separation ⇒ `26.8528` / `11.3373` / `2.5047` 度，`3.67e5` / `1.55e5` / `3.43e4` 倍，separations `26.85°` / `2.50°`。
- [x] 1.4 重测 `d_c=2` 的 b1（同参数求积残差）与 b2（跨参数化相对/绝对偏差），**参考量与 `tests/test_sphere.py::test_cap_area_dc2_affine_degeneration` 的 (b1)/(b2) 完全一致**（同一 9 点 sweep、同一 `x = sin²θ` 参考）⇒ b1 sweep max `3.2294e-16` @81.34°、稠密 sweep `3.3798e-16` @81.855°；b2 @89.99999° 绝对 `3.7976e-11` / 相对 `7.5952e-11`；`N_e=2` 绝对 `1.0537e-8` / 相对 `6.7079e-9`。
- [x] 1.5 核验 `≈ 4.46e-14`（absolute）与 `rel_dev / N_e = 1.42e-14`：实测 `4.4631e-14`–`4.4645e-14` 与 `1.4206e-14`–`1.4211e-14` ⇒ **与文字相符，不改**。
- [x] 1.6 **驳回审计的一条**：`≤ 3.23e-16` 在 spec 自己声明的 9 点 sweep 上精确成立；审计的「低估 3%」来自 2001 点稠密 sweep。⇒ 该数字**不改**，改为把 sweep 点位写进 spec 以消除歧义。

## 2. spec delta

- [x] 2.1 delta 由**实况 spec 逐字复制** req-6 块（脚本 `gen_delta.py`，从 `<a id="req-6">` 到 `<a id="req-7">`），避免手抄那条超长 body 引入误差。
- [x] 2.2 施加 3 处修改（`:125` equal-area gaps / `:132`+`:133` 单侧性与 separation / `:140` frame 标注 + sweep 点位）。
- [x] 2.3 **delta 完整性校验**（脚本 `check_delta.py`）：delta 与实况 req-6 块的 `difflib` 比对 = **恰好 3 个 hunk，分别落在 live L125 / L132 / L140**；块长 47 = 47；尾部无多余内容。⇒ delta 未引入任何非预期改动。
- [x] 2.4 换行符：delta 为 LF、无 BOM、单尾换行。

## 3. 验证

- [x] 3.1 `openspec validate 2026-10-04-fix-spec-measured-literal-frames-and-values --type change --strict` ⇒ PASS。
- [x] 3.2 `openspec validate --specs --strict` ⇒ PASS（delta 尚未 apply，实况 spec 不变）。
- [x] 3.3 `git diff openspec/specs/` ⇒ **0 行**（本 change 只提交 delta，实况 spec 由 `openspec archive` 在归档时改写）。
- [x] 3.4 门禁 `uv run python scripts/run_gates.py --change 2026-10-04-fix-spec-measured-literal-frames-and-values` ⇒ GATE OK。
- [x] 3.5 换行符全量复核：改动文件全部 LF、无 BOM、单尾换行。
- [x] 3.6 门禁期间零编辑（`req-gov-8`：HEAD 与工作树摘要前后不一致即 `GATE RESULT INVALID` + exit 2）。
- [x] 3.7 单 commit on `dev`，**显式路径选择性暂存**，不使用 `--amend`（共享 index），不暂存并行 session 的脏项。

## 4. 归档（不在本 commit 内）

- [ ] 4.1 `openspec archive` 后断言 delta 已被 apply：实况 `openspec/specs/decompmoe-skeleton/spec.md` 的 L125/L132/L140 出现新字面量，且 req-6 块行数不变（47）。
- [ ] 4.2 归档后 `uv run python scripts/run_gates.py --change <archived>` + `pytest tests/test_sphere.py -q` 复跑。
- [ ] 4.3 归档件不可写回：4.1/4.2 的结果在**下一个 commit message** 里报告，不回填本文件。
