# Proposal

## Why

`.audit/wayfinder-opsx-code-review/lists/direct-fixes.md` 的 B-1「DF 段」列出 9 条可直接修的 finding。这些 finding 全部带 `STILL_REAL` / `PARTIALLY_REAL` 裁决与 `unchanged-since-pin` 基线。逐条在 HEAD 实测后，9 条里 **2 条被推翻**、**6 条部分成立但带具体错误**、**仅 DF-06 干净成立**。

若照原清单执行，会同时产生三类错误动作：删除 3 棵而漏掉 10 棵、照抄一条会丢工作（但丢的是空内容）的 `suggested_fix`、为一条已被上游根除的缺陷重新补测试。清单本身也带一个会让读者误判的成因：**报告 §11 第 9 条写「清理已完成」而磁盘上从未清理**。

两条系统性成因，都不是逐条疏漏：

1. **pin 漂移**。`_pin_drift.json` 的 `head` 记录为 `188b9fb`，落后实测 HEAD 5 个提交。`STILL_REAL` / `MOVED` 这类裁决**只在 pin 那一刻成立**；pin 之后的提交既可能修掉缺陷，也可能反过来把「已修」说成「缺陷仍在」。本例的漂移表恰好错过了从源头根除 DF-08 的那个提交。
2. **范围低报**。清单按报告正文的枚举收尾，而报告正文本身低报——磁盘上的实际对象数是清单数的数倍。报数量时未做枚举，是这类残留漏网的共同原因。

DF-08 与 DF-09 的额外发现：两者断言的实体在 HEAD 已不存在（前者是被取代的 prior 数值，后者是早已删除的目录）。这不是「位置漂移」，是**实体本身已不存在**。

## What Changes

- 新建本 change，把 9 条 DF 的实测裁决、修正后的定位与证伪依据固化进**已提交**的 OpenSpec 制品，使校正轨迹进入版本控制
- 不改任何 Requirement 规范内容：`wayfinder` req-17 的 live 闭式本就正确且已有守护，本 change 只记录「清单对它的描述已失效」这一事实
- 把阶段 3/4/5 的落盘动作（外部审计目录清理、分支与 worktree 卫生、`.gitignore` 补模式）写成 `tasks.md` 的可勾选项

**不涉及**：`openspec/specs/**`、`src/**`、`tests/**`、`wayfinder/**` 的实质内容。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。`skip_specs: true`。

## Impact

- 真相源不变：三条 live spec 的 anchor 计数在 change 前后必须完全一致
- 唯一的新增制品是本 change 目录本身
- 外部审计目录（仓库外）会减少 13 棵仓库副本树，保留审计基线与变异复现入口
