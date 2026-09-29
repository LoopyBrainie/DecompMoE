# 修复 B.3 stale spec 行号 B14 —— `L122` / `L115` 行号漂移

## Why

Python reviewer 批次 B.3 报出 `src/decompmoe/config.py:50` 的注释引用 `spec req-7 L122`，而 β_0 闭式实际在 `wayfinder/spec.md` L130。

commit `b23f0e5`（`b23f0e5d86740433d7b5b486129f65072fc42596`，2026-09-27 18:58:09 +0800）已清理过同批 stale 引用，改了 `wayfinder/spec.md:150,156` + `tests/test_beta.py` 5 处，**但漏了 `src/` 与 `decompmoe-skeleton` spec**。

本 change 复用仓库**已登记两次**的具名 follow-up：

- `archive/2026-09-25-fix-wayfinder-spec-anchor-coverage-l195-l351/proposal.md` —— `fix-config-docstring-beta-line-drift`（L2-F1 finding）
- `archive/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/proposal.md` —— 同一 follow-up 再次登记

change 目录从未创建，本 change 予以落地。

## 核验事实

| 引用位置 | 原文 | 实际指向 | 判定 |
|---|---|---|---|
| `src/decompmoe/config.py:50` | `per spec req-7 L122 closed-form` | `wayfinder/spec.md` L122 是**空行**（req-7 heading 在 L121，正文从 L123 开始） | stale，同 Requirement 内指空处 |
| `decompmoe-skeleton/spec.md:483` | `per wayfinder spec req-7 L122 closed-form` | 同上 | stale |
| `decompmoe-skeleton/spec.md:485` | `spec req-7 L122 closed-form anchor` | 同上 | stale |
| **`decompmoe-skeleton/spec.md:508`** | `per spec req-7 L115 Sigmoid 闭式` | **L115 是另一个 Requirement 的 Scenario 行**（`territory_seeding` / req-2 的 "Phase 0 K-Means deferred to caller"） | **stale，且指到无关 Requirement** |

**β_0 闭式的正确落点是 L130**：

> `β_min = 0.1` exists to keep `σ'(γ)` non-degenerate in the parameterization space (e.g., `γ_init ≈ −3.5` gives `β_0 ≈ 1.035` with healthy gradient `σ'(−3.5) ≈ 0.02845`, verified at 50-digit mpmath precision `σ'(−3.5) = 0.02845302387973555984`)

### 计划外发现：`L115` 与本 finding 同类，但原报告与计划均未列

skeleton spec L508 的 `spec req-7 L115 Sigmoid 闭式` **不是** `L122` 的复制品 —— 它指向的是**完全无关的 Requirement** 的 Scenario 行，性质与本次 change 1 的 B16（`Req 32 L644` 指向 γ 参数化 Requirement）**完全同型**。

原 reviewer 清单未列，本次核验时顺带查出。**若只修 L122 而留下 L115，本 change 会交付一个「已知错误却未修」的指针** —— 这正是 B13 的成因模式（修复时留下明知错误的引用）。

**修正落点与 L122 不同**：`L115` 声称指向「Sigmoid 闭式」，而 `wayfinder` req-7 的 Sigmoid 闭式 `β^param(γ) = β_min + (β_max − β_min) · Sigmoid(γ)`（`β_min = 0.1`, `β_max = 32`）在 **L123**（req-7 的规范性正文），不在 L130。L130 是 `β_0 ≈ 1.035` 的 narrative。因此 L508 → **L123**，L483/L485 与 config.py → **L130**。

## 为什么不统一改成「无行号」引用

`archive/2026-09-23-fix-claude-md-ticket-advisory-boundary/design.md` 确立了「新 Requirement 的 body 与 `Source:` 字段不引用 spec line number，仅引 capability 路径 + commit SHA」的先例。

本 change **不**采用该形式，理由：同批兄弟修复（`b23f0e5` 对 `wayfinder/spec.md:150,156` 与 `tests/test_beta.py`）均已采用 `L122 → L130` 形式。同一批清理若一半用行号、一半去行号，会让「哪些引用可信」失去统一口径。line-drift 抗性改造记为 deferred，不在本 change 范围。

## What changes

| 文件 | 改动 |
|---|---|
| `src/decompmoe/config.py:50` | `L122` → `L130`（仅行号指针；数值 `1.035` 本身正确） |
| `decompmoe-skeleton/spec.md:483` | `L122` → `L130` |
| `decompmoe-skeleton/spec.md:485` | `L122` → `L130` |
| `decompmoe-skeleton/spec.md:508` | `L115` → `L123`（计划外发现） |

`specs/decompmoe-skeleton/spec.md` delta 由**主 spec 当前内容程序化构造**（从 `git show HEAD:…` 读取 req-21 块，逐条替换后整体输出），不手写重建，避免 delta 与主 spec 漂移。

## 明确不做（Non-goals）

- **不修 `wayfinder/tickets/A4-1.md:59`** 的 `req-7 L122` —— 用户裁决：等 `fix-review-findings-voronoi-precision-and-lineage` 归档后由其归属处理。该 change 的 `tasks.md:19` 已把「1.4.3 A4-1.md:59」打上 `[x]`，但该 edit **从未进入 commit**（`b23f0e5 --name-only` 无 `A4-1.md`，工作树亦未修改），属假勾，一并登记为 deferred。
- **不改 `wayfinder` spec** —— `:150,:156` 已由 `b23f0e5` 修为 `L130`，无残留
- 不改 `MVPConfig.beta_initial` 的值（`1.035` 正确，与 4-sig-fig narrative 一致）
- 不改 `tests/test_beta.py`（已由 `b23f0e5` 修为 `L130`）
