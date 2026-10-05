# Proposal

## Why

`.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` 的清单 A（A-1 桶「数值守卫缺口」，24 条）是后续三个修复 change 的**唯一待办输入**。归档 README 明写「动手前必须按 `context/07-baseline-drift.md` 的漂移表重新定位」。

独立复核（基线 pinned commit `6593a06` vs HEAD `188b9fb`，全部锚定 commit object 实测，未读工作树）发现该清单有 **2 处定位指错、6 处数字/措辞失准、3 处推理不成立**（E1/E3 = 定位；E5/E7/E8/E9/E10/E11 = 数字措辞；E6/E12/E13 = 推理；合计 11 条）。其中两处会直接导致改错文件：

- **AC-03** 标注位置 `tests/test_beta.py:184`——该行实际是 `test_logit_range` 体内的一行；清单所称的 `test_logit_no_w_i` 真实位于 `tests/test_distance.py:53`。
- **AC-01** 标注位置 `src/decompmoe/distance.py:24`——真正 `return beta * (inner - 1.0)` 在 `:33`，该文件 pin→HEAD 零漂移，故 9 行偏差是清单错而非漂移。
- **AC-08 / AC-09** 的 6dp 角度字面量与容差的关系需要被写清：现字面量 `1.173548` 对修复前后**都 PASS**（`2.747e-07` / `5.741e-07`），必须改字面量才能成为判别式；而 6dp 字面量对真值的固有截断误差上界为 `5e-07`，**任何 `< 1e-6` 的容差都会失败**（见 `design.md` D4.2）。

若不先勘误，实施者按清单行号施工会修改错误的文件，而清单本身不会给出任何提示：这类错误不会报错，只会在 review 时被当作「改了个不相关的地方」。

## What Changes

- 在 `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` 追加一节 `## Errata`，列出 **11** 条更正并指向本 change 的 `design.md`。
- 归档**正文的既有结论一律不改写**。它是当时那轮 review run 的历史记录，不是可修订的活文档；本 change 只增补勘误。
- 登记与未归档 change `fix-review-findings-voronoi-precision-and-lineage` 的范围重叠（该 change 的 tasks 已全部 `[x]` 但无 `specs/` delta），避免同一处改动被两批工作重复施加。

**不涉及**：`openspec/specs/**`、`src/**`、`tests/**`、`wayfinder/**` 一行未动。24 条的修复本身在后续 change 中进行。

## Capabilities

### New Capabilities

（none）

### Modified Capabilities

（none —— 本 change 不改任何 spec body，在 `.openspec.yaml` 声明 `skip_specs: true`。归档勘误是文档事实修正，不构成 spec 级行为变更。）

## Impact

| 文件 | 操作 |
|---|---|
| `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md` | 追加 `## Errata` 节 |
| `openspec/changes/2026-10-01-audit-errata-a1-numeric-guard-list/proposal.md` | 本文档 |
| `openspec/changes/2026-10-01-audit-errata-a1-numeric-guard-list/design.md` | **11** 条勘误对照表 + 复现命令 + E13 推导 |
| `openspec/changes/2026-10-01-audit-errata-a1-numeric-guard-list/tasks.md` | 任务清单 |

- **测试基线**：无影响（本 change 不动任何测试）。当前 `pytest` 收集 **217** tests 全绿。
- **Lint**：无影响。两个 gate（`lint_no_dead_defensive.py` / `lint_no_source_field_drift.py`）当前均 `exit=0`；本 change 不触碰它们检查的路径。
- **下游依赖**：本 change 是三个修复 change 的事实基线。勘误表必须先落地，否则后续实施者会以错误坐标施工。
- **已知重叠风险**：`fix-review-findings-voronoi-precision-and-lineage`（未归档，tasks 全 `[x]`，无 delta）的 L4 / L5 / H2 / H2b / L7 / M4 / G1 / G5 与本批 24 条中的 AC-03、AC-38、AC-08、AC-12、AC-40、AC-77、AC-61 指向同一批位置。处置见 `design.md`。
