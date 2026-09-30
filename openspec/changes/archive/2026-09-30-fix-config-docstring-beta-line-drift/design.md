# Design — B14 stale spec 行号（`L122` / `L115`）

## Decision 1：`L508` 的落点是 L123，不是 L130

**Choice**：`decompmoe-skeleton/spec.md:508` 的 `per spec req-7 L115 Sigmoid 闭式` → `per spec req-7 L123 Sigmoid 闭式`。

**Rationale**：L508 的语义诉求是「Sigmoid 闭式」。`wayfinder` req-7 中：

- **L123**（req-7 规范性正文）：`β^param(γ) = β_min + (β_max − β_min) · Sigmoid(γ)`，`β_min = 0.1`、`β_max = 32` —— **这才是 Sigmoid 闭式**
- **L130**：`γ_init ≈ −3.5` gives `β_0 ≈ 1.035` 的 narrative 与 50-digit 精度披露 —— 这是 **β_0 数值 narrative**

两者内容不同。若把 L508 也统一改成 L130，会把「Sigmoid 参数化闭式」的错误指向「β_0 数值说明」——**用一个 stale 引用换另一个错误引用**，比不改更糟。

**Alternatives**：

- **(a) 统一改成 L130** —— 拒绝。理由同上。
- **(b) 删掉行号只留 `spec req-7 Sigmoid 闭式`** —— 拒绝。与本 change 已落地的兄弟修复（`b23f0e5` 的 `L122→L130`）口径不一致；line-drift 抗性改造另立 change（见 Decision 3）。

## Decision 2：delta 由主 spec 程序化构造

**Choice**：用脚本从 `git show HEAD:openspec/specs/decompmoe-skeleton/spec.md` 读取 req-21 整块（按 `<a id=` 边界切分，L479–L511），逐条执行 3 个替换后整体写出 delta，而非手写重建。

**Rationale**：手写 MODIFIED delta 有两类漂移风险 —— ① 漏抄原文导致 archive 时静默丢失正文；② delta 与主 spec 不一致而校验未发现。程序化构造保证「delta ≡ 主 spec + 我声明的 3 处改动」这一不变量可被机械验证（构造时即断言每条 old 恰好出现 1 次）。

**Verification built into the constructor**：delta 的 CRLF 计数 = 0、anchor 数 = 1、heading 数 = 1、残留 `L122`/`L115` = 0。

## Decision 3：不引入 line-drift 抗性形式

**Choice**：沿用 `L122 → L130` / `L115 → L123` 的行号形式。

**Rationale**：`b23f0e5` 已在本仓为同一批 stale 引用落地了行号修正形式。本 change 若改用「capability 路径 + anchor id」的无行号形式，会与已落地的兄弟修复产生两种并存口径，增加后续审计成本。

**Deferred**：全仓行号引用的 line-drift 抗性改造（含本 change 的 4 处）需独立评估，届时应统一处理 `wayfinder` / `decompmoe-skeleton` / `src/` / `tests/` 全部表面。

## Decision 4：archive 三重防护

本 change 是本轮三个 change 中**唯一触碰 spec、唯一需要 archive** 的，因此防护必须完整。本仓已两次实测 `openspec archive` 损坏 spec（MODIFIED block 尾部边界判定吞掉紧随其后的 anchor 行），且 **`archive` 的 exit code 与 `~ N modified` 计数都不能证明 spec 未被破坏**。

| 阶段 | 动作 | 目的 |
|---|---|---|
| 前置 | 两 lint 门禁 exit 0 | CLAUDE.md §3 archive 前置条件 |
| 前置 | `openspec validate --specs` 全绿 | delta 结构合法 |
| 前置 | 主 spec 逐字节 SHA256 快照（`ee75cef8…`） | 损坏后可判定是否变化 |
| 前置 | `git status --short -- 主 spec` 为空 | **恢复前提**：无未提交改动，`git checkout --` 才能完整还原 |
| 后置 | anchor 逐行复算 wayfinder 36 / skeleton 23 / governance 4 | 唯一能发现 anchor 丢失的检查 |
| 后置 | 复算基准取 commit object | 避免工作树基准漂移 |
| 后置 | SHA256 比对 | 判定 spec 是否被改动 |
| 后置 | 若损坏 → `git checkout --` 完整恢复 → 重跑 lint + validate + 全量 pytest | 回到已知良好基线 |

**Note**：本 change 的 delta 只改 3 行文本（L483 / L485 / L508），预期 archive 报告 `~ 1 modified`。但**该计数不作为正确性证据** —— 前例中一次「0 插 4 删」的 archive 同样报告了成功。

## Risk

- **[Risk] `wayfinder/tickets/A4-1.md:59` 仍为 `L122`** —— 已知且已 defer。但需注意：本次修完后，仓库内 `L122` 引用将**只剩 ticket 一处**。归档 `fix-review-findings-voronoi-precision-and-lineage` 时应一并处理其 `tasks.md:19` 的假勾。
- **[Risk] 未来 spec 继续增长致 L123/L130 再次漂移** —— 本 change 不解决，已在 Decision 3 登记为 deferred 的系统性改造项。
- **[Non-Risk] `MVPConfig.beta_initial` 值未变** —— `1.035` 正确；本 change 只动注释与 spec 文本中的行号指针，req-21 的三个 Scenario 断言内容与 tolerance 均未触碰。
