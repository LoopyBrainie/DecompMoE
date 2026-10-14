# Tasks

> 范围：`FIX-006` + `FIX-007`（OPX-2 桶 4 条中的 2 条成立项）。`FIX-034` / `FIX-042` 判定不成立，零 spec delta，证伪证据见 `design.md` D-4。（基线 `3c64cdc`）
> 基线：`HEAD 3c64cdc`（`dev`，264 commits），`run_gates.py` → `GATE OK` exit 0（7 lint / **74 anchor** / 541 passed 1 skipped）。
> **工作树约束**：`.gitignore`、`src/decompmoe/gating.py`、`wayfinder/tickets/WF-1.md` 三处既有未提交修改**完全不动**——不触碰、不暂存、不落定。门禁输出中的 `dirty_entries=3` 属既有基线，不作为失败判据。
> 解释器入口：一律 `uv run` / `uv run pytest`。`run_gates.py` **必须** `uv run python` 启动（裸 `python` 会让门禁在与代码无关的地方报红）。
> 决策依据：`design.md` D-1（NaN 契约）、D-2（`_ZERO` 窄读法）、D-3（req-30 三处修法）、D-7（MODIFIED 承载，**anchor 维持 74**）。
> **spec delta 由 `openspec archive` 自带同步**，故「第 2 组 spec 并入」与 anchor 四步协议同属归档阶段，列在 `## Workflow follow-up`，不在本 change 的 tracked task 内——apply 阶段不动主 spec。

## 1. 基线证据

- [x] 1.1 把 `FIX-006` 基线落盘到本 change 的 `evidence/`：`_ZERO` 的 5 处 `return` 行号表（`:103`/`:140`/`:153`/`:165`/`:228`）、`:153` 在合法输入下不可达的 `sys.settrace` 穷举记录（`N_e ≤ 5` × `T ≤ 8×200`，命中 0）、合法全死路径为 `:139-140` 的 `T = 0`、台账决定性构造下 `torch.equal(dead, live) == True` 且 repr 同为 `'tensor(0.)'`。验证：evidence 含上述行号与 HEAD sha，且行号与 `git show HEAD:src/decompmoe/metrics.py | grep -n _ZERO` 逐条一致。
- [x] 1.2 把 `FIX-007` 基线落盘到 `evidence/`：`‖∂logit/∂C‖₂ = β·‖c‖₂` 在 `0°–180°` 逐角度成立、`‖C‖ = 2` 处 autograd 给 `32.0` 而旧式给 `16.0`、`β = 0.1 + 31.9σ(γ)` 在 float64 下需 `γ ≳ 36.7368` 才饱和到 `1.0`、`tests/` 10 处 `autograd.grad` 无一以 `c_i` 为求导变量。验证：evidence 含上述四项数值与 `HEAD 3c64cdc`。
- [x] 1.3 落盘 delta 的机械提取校验：脚本按顶层 anchor 边界提取 `req-20`（`wayfinder` 462–573）与 `req-22`（`decompmoe-skeleton` 560–646）并断言与主 spec **逐字节相等**。验证：`req-20` 非空行 90 行、`req-22` 非空行 55 行，两项均报 BYTE-IDENTICAL。

## 2. `metrics.py` 的 SP 早退改 `NaN` + SP 全死路径测试

- [x] 2.1 把 `src/decompmoe/metrics.py` 中属于 `SP` 的两条早退改为返回 `NaN`：`:140`（`C_t.numel() == 0`，合法 `T = 0`）与 `:153`（`not per_expert_means`）。**`:103` / `:165` / `:228` 与 `:21` 的 `_ZERO` 定义不得改动**（`design.md` D-2）。验证：`grep -n 'return _ZERO' src/decompmoe/metrics.py` 命中行号恰为 103 / 165 / 228，且不含 140 / 153。
- [x] 2.2 在 `tests/test_metrics.py` 新增全死路径测试：`T = 0`（空签名集）与「全部专家 `‖T_i‖₁ = 0`」两种入口都返回 `NaN`，用 `torch.isnan` 断言，MUST NOT 为 `0.0`。验证：`uv run pytest tests/test_metrics.py -k "all_dead or dead"` 全 PASS。
- [x] 2.3 新增**判别性断言**：复用台账决定性构造（`d_c = 2`，centroids `[[1,0],[0,1]]`，signatures `[[0.6,0.8],[-0.6,0.8],[0.8,0.6],[0.8,-0.6]]`，assignments `[0,0,1,1]`；IEEE-754 保证 `0.6f + (-0.6f) == 0.0` 故两活专家 `SP` 均精确 `0.0`），断言全死结果 `torch.isnan(...)` 为真**且**与该活测量 `not torch.equal(...)`。验证：构造下活路径值仍精确为 `0.0`（逐位），判别性断言 PASS。
- [x] 2.4 既有 SP 行为零回归。验证：`uv run pytest tests/test_metrics.py` 全 PASS，且既有 5 处 SP 测试的期望值一字未改。

## 3. `c_i` 侧梯度守护测试（`#req-30` 的零覆盖补齐）

- [x] 3.1 在 `tests/test_beta.py` 新增**以 `C` 为求导变量**的守护：角度扫描 `θ ∈ [0°, 180°]`（`‖C‖₂ = ‖c‖₂ = 1`）下断言 `‖∂logit/∂C‖₂ == β·‖c‖₂` 逐点成立，正交**非必要**（角端点 `0°` 与 `180°` 必须覆盖）。验证：新测试在 mutant（导数换成 `β·c/‖C‖`）下 FAIL，在正确实现下 PASS。**范围限制**：本条及其 3.2/3.3 全部用单位质心，断言的 `β·‖c‖₂` 退化为 `β`，换任何单位质心结果不变——因此这三条**不能**单独建立 `c` 侧契约，由 3.5 补齐。
- [x] 3.2 新增离球面对账：`‖C‖₂ = 2` 处 autograd 值仍等于 `β·‖c‖₂`，**不等于** `β·‖c‖₂ / ‖C‖₂`。验证：该断言在 mutant 下 FAIL；实测 `β = 32` 时 autograd 给 `32.0` 而旧式给 `16.0`。
- [x] 3.3 上确界量化断言：有限 `γ` 下 `‖∂logit/∂C‖₂ < 32.0` 严格成立（不再以「`β = β_max` 时取到 `32.0 within abs=1e-4`」作可达性断言），并保留闭区间边界值 `β = β_max` 上等于 `32.0` 的求值。验证：新测试 PASS；`15.95` 的 γ 侧守护仍 PASS。
- [x] 3.4 `uv run pytest tests/test_beta.py` 全 PASS。
- [x] 3.5 新增**真正以质心为求导变量、且用非单位质心**的守护（`test_grad_bound_tracks_centroid_norm_with_centroid_as_grad_variable`）：`‖c‖₂ = s` 时 `‖∂logit/∂C‖₂` 恰为 `β·s`（`s ∈ {1.0, 1.5, 2.0, 3.25}`，且 `s=1` 与 `s=2` 结果必不相等）；并令质心 `requires_grad_(True)` 断言 `∂logit/∂c == β·C` 逐位相等。验证：实测在「`logit` 归一化 `c`」的变异体下，同批 9 条 grad 测试中 8 条通过、**仅本条失败**——即 3.1–3.3 结构上无法捕获的缺口，由本条捕获。

## 4. 整合门禁验证

- [x] 4.1 `uv run python scripts/run_gates.py` → `GATE OK` exit 0；7 个 `lint_*.py` 全 PASS；pytest 计数不低于 541 passed。验证：命令输出逐行检查。
- [x] 4.2 Source 反链门禁：`#req-20` / `#req-22` / `#req-30` 三块的 `**Source:**` 行在 delta 中原样保留，`lint_no_source_field_drift.py` PASS，且 `SOURCE_EXEMPTIONS` 登记表规模仍为 **20**（无新增、无失效条目）。验证：门禁 PASS + 登记表计数实测 20。
- [x] 4.3 anchor 计数不变：本 change 不新增 Requirement，apply 后 `run_gates.py` 的 `anchor coverage` 行应仍显示 **74 anchor(s) across 3 capabilit(ies)**。验证：实测等于 74；若不等，停止并回查。
- [x] 4.4 工作树零新增残留：`git status --porcelain` 的受追踪修改项恰为那 3 处既有改动。验证：`git status --porcelain | grep -v '^??'` 行数为 3 且路径一致。
- [x] 4.5 `dev` 保持线性：`git log --merges --first-parent dev -1` 无输出。验证：命令无输出。

## Workflow follow-up

以下须在 apply 完成后另起请求执行（`/opsx:archive`），**不在本 change 的 tracked task 内**：

- **第 2 组 · spec delta 并入主 spec**（`openspec archive` 自带同步，apply 阶段不动主 spec）：
  - wayfinder：`#req-20` 块尾追加 6 条 `SP` 全死 / `NaN` carve-out Scenario；`#req-30` 块整体替换（描述行改写 + 4 条 Scenario）。
  - decompmoe-skeleton：`#req-22` 块尾追加**同样 6 条逐字相同**的 Scenario，以维持 `#req-23` 的镜像义务。
  - 验证：并入后 `openspec validate --specs` exit 0；`grep -c 'MUST NOT be reported as `0.0`' openspec/specs/wayfinder/spec.md` ≥ 2；`wayfinder` 的 `#req-30` 行不含 `c / ‖C‖ = 32` 与 `MUST be attained (not merely bounded above)`，且 `15.95` 保留。
- 归档**前**执行 `uv run python scripts/run_gates.py anchor-ledger --write`。
- 执行 `/opsx:archive`。
- 归档**后**执行 `uv run python scripts/run_gates.py anchor-ledger --verify`；若非 0，**只做手术式补回并复测，禁止重跑 archive**（`req-gov-10`）。
- 归档后重跑 `uv run python scripts/run_gates.py` 确认 `GATE OK`，并核对 `anchor coverage` 仍为 **74**、`pytest` 计数不低于 541 passed。
- 归档后做 anchor 全集对账：74 个 `(capability, anchor_id)` 与归档前**完全相同**（无丢失 / 新增 / id 冲突）。（基线 `3c64cdc`）
