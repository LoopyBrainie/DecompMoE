## Why

`openspec/changes/introduce-wayfinder-decompoe-spec/` 在 WF-1 审计（`wayfinder/tickets/WF-1.md`）中通过 **PASS-WITH-WARNINGS**，确认 21 ticket 决策已 1:1 映射到 21 Requirement × 34 Scenario、`validate --strict` 通过、Source 反链完整，但留下 3 项 minor warnings 不阻塞 archive。本次 polish 把这 3 项 warning 收敛掉，再附加一项由 21 ticket 逐条 deep-check 发现的 precision drift（A4-1 γ 梯度上界 15.95 被 spec 简化成 32），让原 change 进入 archive 前的 clean 状态——**纯文档整改，零 system behavior 变化**（A4-1 drift 的 spec 修正仍由 32 收紧到 15.95 ⊂ 32，行为契约范围未扩张）。

## What Changes

- **修改 `openspec/changes/introduce-wayfinder-decompoe-spec/proposal.md`** 的 Impact 段：补充一行"21 Requirements × 34 Scenarios"明示数量（Warning 1）。
- **修改 `openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md`**：为每个 `### Requirement:` 标题补 `<a id="req-N"></a>` 锚点（N = 1..21），便于下游 design / docs 跨文档引用。
- **修改 `openspec/changes/introduce-wayfinder-decompoe-spec/design.md`** Risks / Decisions 段：把对 spec.md 的 Requirement 引用从自然语言（如 `Naming And Alias Convention`）改为相对锚点（如 `[Naming And Alias Convention](../specs/wayfinder/spec.md#req-1)`），避免章节顺序调整后的漂移（Warning 2）。
- **修改 `openspec/changes/introduce-wayfinder-decompoe-spec/tasks.md`** 第 2.4 项的描述：把 "appear only in `## Purpose` exclusion list or in `Source:` references to 'Future Work' sections" 改为"appear only in `## Purpose` exclusion list；Future Work references inside ticket bodies are accepted audit sources via grep"——让 reviewer 的判断路径无歧义（Warning 3）。
- **修改 `openspec/changes/introduce-wayfinder-decompoe-spec/specs/wayfinder/spec.md`** `Isotropic Squared-Chord Distance And Bounded Beta` Requirement 的"MUST bound all three gradient magnitudes by ≤ β_max = 32"句：按 `wayfinder/tickets/A4-1.md` 数学拆为 per-component 精确上界——`‖∂logit/∂C‖₂` 和 `‖∂logit/∂c_i‖₂` ≤ β_max = 32，`|∂logit/∂γ_i|` ≤ 0.5(β_max − β_min) = 15.95（A4-1 deep-check drift，by-product of WF-1 audit 后的 21 ticket 逐条比对）。

## Capabilities

### New Capabilities

无（`skip_specs: true`，本次 change 不新增 behavior）。

### Modified Capabilities

无（spec.md 仅补 anchor 与 A4-1 单点精度修正，不变更 Requirement 行为契约范围——A4-1 由"≤ 32"收紧到"≤ 15.95"是数学精度的文本提升，行为范围 15.95 ⊂ 32 不构成 capability modification；继续以 `skip_specs: true` 覆盖本次 change）。

## Impact

- **代码库**：本次 change 不编辑 `wayfinder/` 之外的任何 Python 代码；不动 `openspec/specs/` 主 spec。
- **依赖/外部系统**：无新增第三方依赖。
- **OpenSpec 制品**：本 change 修改的是前一个 change（`introduce-wayfinder-decompoe-spec`）的 proposal / spec / design / tasks 四个文件；修改在前 change 的 archive 之前完成，确保 archive 时拿到 polished 版本。
- **风险**：3 项 WF-1 warning + 1 项 A4-1 precision drift 都是文档级 polish / 数学精度修正，可由 apply 阶段的 grep + 长度校验兜底；不引入新风险。