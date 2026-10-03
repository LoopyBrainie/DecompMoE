# Tasks — `pytest.approx` 语义勘误

## 0. 门禁（apply 开工前）

- [ ] 0.1 **先裁决，不得先改文本**。跑 `evidence/_pytest_approx_semantics.py`，确认：(a) 打印 pytest 版本与模块路径；(b) 读出 `ApproxScalar.tolerance` 源码并定位 `if self.rel is None: if self.abs is not None: return absolute_tolerance` 短路；(c) 行为裁决 `approx(1.0, abs=1e-9).tolerance == 1e-09` 且 `1.0 + 1e-8` **FAIL**。验证：三条断言全过；**若行为裁决与源码读取不一致，停止**——那意味着换了一种读法而不是换了一个数字。
- [ ] 0.2 反向确认判别构造**有牙**。用 `1.0 + 1e-7`（两种读法都 FAIL）确认它**不能**区分，从而证明 0.1 选的 `1e-8` 是必要的。验证：脚本同时打印两个构造的结果，且明确标注后者无判别力。**只用一个构造就宣称裁决成立，是本仓反复栽过的「守卫没有牙」。**

## 1. 真相源更正（`governance/spec.md` req-gov-1）

- [ ] 1.1 义务 1（L13）：**保留规则，更换理由**。删去「有效容差公式是 `max(abs, rel·|expected|)`」与「`rel` 留在 pytest 默认 `1e-12`」，改为版本无关的理由（`approx` 对整数做浮点比较，容差语义随 pytest 版本变化；裸 `==` 在所有量级上给出可判定的零容差）。验证：规则句仍在；理由句已换；`1e-12` 不再被称作 pytest 的 `rel` 默认值。
- [ ] 1.2 义务 3（L17）：把「保留 pytest 默认 `rel=1e-6`…实际判据是 `max(1e-6, 1e-6·|expected|)` — `1.17e-6`」改为「给定 `abs` 时容差**恰为** `abs`，实测于 pytest 9.1.1」。验证：`1.17e-6` 与该 `max(...)` 表述在 L17 内归零。
- [ ] 1.3 义务 3（L17）：把「6dp 截断误差以 `5e-7` 为界 ⇒ 任何 `< 1e-6` 的容差都不满足 ⇒ `1e-6` 是显示格式允许的最小值」改为「6dp **截断**误差恒 `< 1e-6`（`5e-7` 是四舍五入半单位，非截断界）」，并删去「最小值」断言。验证：给出反例 `trunc6(0.9999999) = 0.999999`（误差 `9e-7 > 5e-7`）；给出实测「`abs=4.3e-7` 对 `1.173547` 通过」。
- [ ] 1.4 L22 与 L17 同步（同一 `max(...)` 判据）。
- [ ] 1.5 Scenario（L37 / L42）的 `abs=0` 括注：改为「`abs=0` 不引入任何相对容差（实测 pytest 9.1.1 容差恰为 0）；采用裸 `==` 的理由见义务 1」。**规则句「MUST NOT appear」保留不变。**
- [ ] 1.6 **判别力结论必须原样保留**：`1.275e-6` / `1.297e-6` 在两种读法下都 FAIL、`8.34e-7` 两种读法下都 PASS。验证：三个实测差 `4.259e-7` / `6.216e-7` / `8.248e-7` 与「只有两条字面量有鉴别力」的结论逐字未变。**若这几处被顺手改掉，本次是「修理由」变成了「改结论」，必须退回。**

## 2. 副本同步

- [ ] 2.1 `tests/test_sphere.py:98-99` docstring 同步 L17 的更正。验证：`git diff --stat -- tests/test_sphere.py` 显示**只改注释行**；`pytest -q` 的**测试数量不变**。
- [ ] 2.2 逐处复核 B5 的副本清单全部处置完毕，并确认三处**有意不改**（Change α 的 `req-gov-5` C3、Change 3 `design.md` D8 注记、归档副本）确实未动。验证：三条各有一次显式确认，不以「已检查」含糊带过。

## 3. 回归与交付

- [ ] 3.1 `pytest -q` 全绿且**测试数与修改前完全相同**（本 change 只改散文与 docstring）。验证：记录修改前后的 collected 数并逐位比对。
- [ ] 3.2 `openspec validate <change> --type change --strict` exit 0；`scripts/lint_no_source_field_drift.py` exit 0（req-gov-1 的 Source 反链不得因改写正文而丢失）。
- [ ] 3.3 archive 后复算 `governance` 的 anchor **覆盖**（本 change 不新增 anchor，覆盖应保持 4/4 不变）。验证：覆盖 100%、0 重复、绝对计数无漂移。
- [ ] 3.4 交付说明：登记**未做**的两项——`pyproject.toml` 未 pin pytest 版本（因此本论断带环境标注而非被当作普遍事实）；`abs=1e-6` 未收紧到 `4.3e-7`（属独立数值决策，见 design B3）。
