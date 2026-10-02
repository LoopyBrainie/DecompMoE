# Proposal

## Why

审计台账 `.audit/wayfinder-opsx-code-review/`（108 条，跨 A-1..A-8）是在**缺陷求积器**上测得的。change `2026-10-02-fix-canonical-literal-residual-frame-and-dead-guard` 把 `sphere._betainc_regularized` 的误差从 `1.57e-01` 量级降到 `6e-16`，`canonical_voronoi_angle` 及其 16 位输出整体位移约 7 个数量级，并重写了三份 spec 的大块正文。凡测量值、行号指针或 verdict 依赖该路径的条目，现在都不能被直接引用；同一轮里 archive 静默吞 anchor 的事故被原样复现。不重建台账，后续任何以它为输入的修复 change 都会在错误事实上开工。

该修复**已提交在 HEAD**（不是「只在工作树」），因此第三方在 HEAD 重测可复现本台账，而非审计的修前数字。漂移向量已换形：真正的风险不再是「未提交」，而是「HEAD 会被并行 session 推进」，故台账记录**生成时的 HEAD commit**。

清单还带有两层此前未被纳入的制品：**11 + 20 条勘误**（A-2 桶被 15 条全覆盖，全部锚定 `188b9fb`、且测于修复之前）与 **6 条盲区**。盲区 1 登记了 9 条在 `classified.json` 里**完全没有实体**的上游 finding，其中 `D1-02` 正是本次求积器缺陷的**根因本体**。

## What Changes

- **逐条判定传递依赖性**：对 A-1..A-5 + A-7 共 **95** 条，每条判定其结论是否传递依赖 `_betainc_regularized` / `canonical_voronoi_angle` / 球面求积路径。判定必须写出**可复算的推导**（哪一行代码 → 哪个量 → 哪条 finding），不接受「看起来相关」。
- **纳入 9 条无实体 finding**：把「盲区 1」登记的 9 条（`X-D1-02` … `X-main78`）正式纳入台账逐条判定，使台账为 **104 条**。这 9 条不是源文件的 `###` 标题而是表格行，故无 `ac_id`、无桶、无 pin 坐标，id 用 `X-` 命名空间，坐标须从零建立。纳入的理由是 `X-D1-02` 即本次求积器缺陷的根因本体——只重判症状、不判根因是更坏的缺陷。
- **勘误层只作线索，不作依据**：清单的 11 + 20 条勘误与 6 条盲区可用于**定位**，**不得**作为 verdict 来源，也不得无独立锚点地出现在 `verdict_evidence` 中。全部 verdict 从零重判。
- **依赖者重测并重判 verdict**：重新测量并给出新裁决（`STILL_REAL` / `PARTIALLY_REAL` / 已消失 / 降格），附新旧数值对照与失效方向。
- **非依赖者记录依据**：同样写出判定依据（为什么不依赖），使「未纳入重测」成为**可证伪的结论**而不是沉默的省略。
- **A-4 行号指针重算**：位移来自 pin→HEAD 之间**5 个改过 `openspec/specs/` 的 commit**（`e50cc02` / `315065e` / `4f3e752` / `188b9fb` / `f6461d7`），不只 Change 2；且漂移不限于指向 spec 的指针，`touched-since-pin` 的 10 条里有 **7 条在范围内**（AC-04 / AC-05 / AC-28 / AC-40 / AC-60 / AC-64 / AC-79）。需按当前 HEAD 重算而非沿用 pin 态。
- **A-5 归档事故重判**：`design.md` D7 已把「archive 每份 spec 吞掉恰好 1 个 anchor」**降级为待验假设**（原写作既定事实，与 tasks 5.1「必须独立复现」冲突）。AC-19 / AC-20 / AC-80 一律待 5.1 复现后才可重判。
- **A-7 漂移重判**：`map.md` 与 ticket 中的 `θ_Voronoi` 叙述随实现改变而 stale。
- **不修改 `.audit/**`**：沿用 change `2026-10-01-audit-errata-a1-numeric-guard-list` 已裁决的策略——`.audit/` 保持现状，**权威副本是本 change 目录的 `design.md`**。补记：`.audit/` 本身被 `.gitignore:37` 忽略、从未进入版本控制，故本 change 的制品是这些结论唯一可恢复的副本。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——本 change 只产出记录性台账，不改变任何 spec 级行为。`.openspec.yaml` 已设 `skip_specs: true`，与 Change 0 同类。）

## Impact

- **产出**：`evidence/ledger.json` 是 104 条的机器可读主体（schema 见 `tasks.md` 0.3）；`design.md` 承载决策、逐桶小结与交付说明（**不做 104 条全量镜像**）；`tasks.md` 承载执行顺序；证据脚本与 JSON 落盘 `evidence/`，工具落盘 `evidence/tools/`。
- **不改动**：`src/**`、`tests/**`、`openspec/specs/**`、`wayfinder/**`、`.audit/**`。
- **下游影响**：台账是后续修复 change 的输入。若重判发现某条缺陷已不存在，后续对应修复 change 的范围需相应收缩；若发现新缺陷，需另开 change——本 change 不实施任何修复。
- **自身入库义务**：本 change 的 `evidence/**` 与被它重判的 Change 2 归档目录**必须入库**才算交付（`design.md` D11）。「change 制品完成却未入库」正是本 change 要重判的 AC-23 / AC-100 主题，带着未入库的证据归档等于复制一遍被测缺陷。提交必须走选择性暂存——`git add -A` 会静默删除 4 个 HEAD 追踪但工作树已失的文件。
- **既有未决项**：`fix-review-findings-voronoi-precision-and-lineage` 的状态**已由 A-2 Errata 的 Dedup 登记裁决为「已 inline 应用未归档」**（其声称改动实测均在工作树生效）。本 change 不重新开启该裁决，只在 `tasks.md` 7.3 **复核其在当前 HEAD 仍成立**并登记证据；其 `proposal.md` / `tasks.md` 在工作树被删而 HEAD 仍追踪这一事实仍需实测记录。
