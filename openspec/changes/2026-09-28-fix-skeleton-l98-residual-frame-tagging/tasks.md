# Tasks: 2026-09-28-fix-skeleton-l98-residual-frame-tagging

## 1. Delta 构造（程序化，禁止手抄）

- [x] 1.1 从 `openspec/specs/decompmoe-skeleton/spec.md` 抽取 req-6 block（`### Requirement:` 起，至下一个 `### Requirement:` 或 `<a id=` 之前，剥离尾部空行）
- [x] 1.2 对 2 处 target 施加**全文件唯一性**断言（`count == 1`）后再替换
- [x] 1.3 往返验证：按 header 整体**逆序**反向替换，与原文逐字节相等
- [x] 1.4 结构检查：反引号配平（164，偶）、`#### Scenario:` 仍为 4、无 `<a id=>` 混入、frame 标注增量 `+2`、删除行数 `0`
- [x] 1.5 写出 `specs/decompmoe-skeleton/spec.md`，`## MODIFIED Requirements` 下**不含** `<a id="req-6">` 锚点（沿用仓库既有惯例）

## 2. 写入 live spec

- [x] 2.1 provenance 断言：delta block 反向替换后 == 改前 live block（证明 delta 未夹带额外编辑）
- [x] 2.2 以 delta block 覆写 live req-6 block
- [x] 2.3 **保留块尾空行分隔**（剥离式 block 覆盖会吃掉 `<a id="req-7">` 前的空行；已按 `git diff --numstat == 1 1` 收口）

## 3. 验收断言

- [x] 3.1 L98 恰有 **2 处被标注的 `< 1e-9` claim site**（`count("< 1e-9")` 为 3：2 个 claim + occurrence 1 否定从句内自引 1 次）
- [x] 3.2 `impl-internal frame per` 出现 2 次
- [x] 3.3 `req-gov-1 §4` 引用出现 2 次
- [x] 3.4 L98 反引号配平
- [x] 3.5 live block == delta block

## 4. 数值独立复算（**不采信任何旧报告**）

> 真值参考系定义：`I_x(a,b) = betainc(a, b, 0, x) / beta(a, b)`。
> **不得**使用 `betainc(a, b, x)`（3 参）或 `betainc(a, b, x, regularized=True)`（返回上尾）。

- [x] 4.1 impl-internal（`_betainc_regularized`）残差：`N_e=16 → 1.1643e-14`、`N_e=64 → 1.9429e-15` —— 与 `governance:20` / skeleton L114 一致
- [x] 4.2 true closed-form（mpmath 精确）残差：`N_e=16 → 4.1457e-7`、`N_e=64 → 1.4273e-9` —— 与 `governance:21` / skeleton L115 一致
- [x] 4.3 新措辞的**否定结论**在两个 `N_e` 上均成立：impl-internal `< 1e-9` = True；true closed-form `< 1e-9` = **False**
- [x] 4.4 旁证：`round(θ, 4)` = `1.1735` / `1.0205`，与 `CLAUDE.md` §5 冻结形式一致（A1 契约未被破坏）

## 5. Gate（archive 前置）

- [x] 5.1 `uv run pytest -q` → **`206 passed`**。本 change **零新增 / 零修改测试**（未触碰任何 `tests/` 文件）。基线由 `204` 变为 `206` 系**并发 session 的未提交**改动所致：`tests/test_beta.py`（+41/-2）与 `tests/test_sphere.py`（+43/-0）在 gate 运行前已被另一 session 写入工作树。**本 change 对该数字无贡献**（见 `design.md` Risks 并发条目）。
- [x] 5.2 `python scripts/lint_no_dead_defensive.py` → `exit=0`
- [x] 5.3 `python scripts/lint_no_source_field_drift.py` → `exit=0`
- [x] 5.4 anchor coverage 不变：wayfinder 36/36、decompmoe-skeleton 23/23、governance 4/4（按 `^<a id="req-[^"]*"></a>$` 计数；宽松 pattern 会命中行内引用产生假 mismatch）
- [x] 5.5 `openspec validate "<name>" --type change --no-interactive` 通过
- [x] 5.6 `openspec validate --specs` → 3/3 通过
- [x] 5.7 `governance/spec.md` 与 `wayfinder/spec.md` 的 **本 change 零 diff**。注：gate 运行时工作树中二者**已被并发 session 改动**（governance +4/-5、wayfinder +17/-5，未提交），故 `git diff e5fec3a` 不再显示二者 identical。**该漂移不属本 change**，验证方式为：本 change 的 commit 只包含 `openspec/specs/decompmoe-skeleton/spec.md` 与本 change 目录（见 §5.9），并以 `git show --stat HEAD` 确认二者不在其中
- [x] 5.8 `src/` `tests/` `scripts/` `CLAUDE.md` **本 change 零改动**（同上：工作树中 `CLAUDE.md` 与两个测试文件由并发 session 改动，不进本 commit）
- [x] 5.9 单 commit on `dev`；HEAD 非 merge commit（`git log -1 --pretty=%P` 单 parent）

## 6. Post-archive audit（**持久、可重复执行**）

> 本任务**故意不勾选**。它不是一次性步骤，而是留给未来任一 change 归档**之后**重跑的守护：
> 当 `a2-a3-a4` 或 `a7` 归档时，若其陈旧 delta 覆写了 req-11，本检查立即报红。

```powershell
Select-String -Path openspec/specs/wayfinder/spec.md -Pattern '1e-4 rad|permitted by .*req-gov-1 §2'
# PASS  = 零匹配  → A5 修复完好
# FAIL  = 有匹配  → A5 被 peer archive 静默回退
#                从 openspec/changes/archive/2026-09-28-fix-a1-a5-voronoi-literal-tolerance-binding/ 重施
```

- [ ] 6.1 A5 存活审计（命令见上；每次 `a2-a3-a4` / `a7` 归档后重跑）

## 7. Deferred register（**不属于本 change**，留档供后继 change 机械接手）

> 以下全部因 delta contention 阻塞（`design.md` Decision 2）。替换措辞已预先核实，
> 但**必须在** `a2-a3-a4` 与 `a7` 均归档、且 §6.1 报 PASS 之后，才能开新 change 动手。

| ID | 位置 | 缺陷 | 阻塞者 |
|---|---|---|---|
| **A** | `governance/spec.md:20` | `Gauss–Legendre 8-point, 60 subintervals` 描述了从未存在的分段求积（实为单 8 点 panel，无分段） | `a2-a3-a4` |
| **A** | `governance/spec.md:21` | `bounded to < 1 ppm` 字面读法为假（函数自身相对误差 `6.63 ppm`，超 6.6×）；θ 偏差读法 `0.7233` / `0.0086 ppm` 才成立 | `a2-a3-a4` |
| **B** | `wayfinder/spec.md:233` | 未标参考系的 `< 1e-9`；true closed-form 下实为 `4.1457e-7`，**为假** | `a2-a3-a4` + `a7` |
| **B** | `wayfinder/spec.md:274-276` | Scenario 同款未标注声明，同样为假 | `a2-a3-a4` + `a7` |

**合并规则（重要）**：`governance` + `wayfinder` **必须同一个 change 出两份 delta**。
拆成两个 change 会在 archive 时产生第三份争抢。

**注意**：`governance:20` 的 `1.16e-14` 与 `governance:21` 的 `4.15e-7` 两个数字经本次复算**正确**，
后继 change **不得**顺手改动它们，只换求积描述与 `< 1 ppm` 的归属措辞。

## 8. Out of scope（复述 `proposal.md`，防止后续误扩）

- 不改 `governance/spec.md` / `wayfinder/spec.md`（见 §7）
- 不改任何并行 session 的 change 目录（含 `a2-a3-a4` 的陈旧 delta）
- 不新增测试、lint 规则、Scenario
- 不改 `src/` 任何实现；不重新调参 `canonical_voronoi_angle` / `_betainc_regularized`
- 不解冻 `CLAUDE.md` §5 的 4dp prose 形式，不触碰 A1 确立的双层 literal 契约
