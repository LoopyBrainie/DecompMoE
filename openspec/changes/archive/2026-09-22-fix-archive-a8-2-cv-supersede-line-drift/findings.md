# Findings — 清单 03 主文事实验证（2026-09-22）

> 本文件记录 2026-09-22 独立事实验证（独立 grep / Select-String 校对）发现的清单 03 主文（`.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/`）4 处新事实错误。本文件**不修改**清单 03 主文 4 个文件（per `.audit/README.md` L3 .audit/ 不进 git 追踪 + L72 audit trail 完整性原则）。新 change `2026-09-22-fix-archive-a8-2-cv-supersede-line-drift` 的核心目的是修新 change 03 制品（archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/）自身 5+ 处事实错误；清单 03 主文错误作为本新 change 的 findings 段在 opsx 流程内记录，与 `.audit/.../KNOWN-DRIFT.md` 追加 Drift 3 子段并行。

---

## F1 — spec 行号偏差 ~24 行（清单 03 引用 L389/L426/L432/L392 等）

### 清单 03 主文引用

清单 03（`.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/`）4 个文件（proposal.md / design.md / tasks.md / specs/*/spec.md）反复引用：

- "spec L389 Reason verbatim"
- "spec L426 `MCI closed-form on uniform token distribution`"
- "spec L432 `MCI closed-form on rank-1 token distribution`"
- "spec L392 Source 3 反链齐"
- "spec L389 Range `MCI ∈ [1/d_c, 1]`"
- "spec L389 闭式 `uncentered second moment`"
- "spec req-20 L389"

### 当前真 spec 实际行号（2026-09-22 独立 grep 验证）

| 元素 | 清单 03 引用 | 真 spec 实际 | 偏差 |
|---|---|---|---|
| `<a id="req-20"></a>` anchor | L389 | **L394** | +5 |
| MCI row "L408" | L408 | **L413**（注：L408 实际是 SP_i 行，不是 MCI） | +5 |
| "replaces CV (whose lower bound..." Reason | L389 | **L413** | +24 |
| "**Source:** `wayfinder/tickets/A8-2.md` ..." Source field | L392 | **L416** | +24 |
| "MCI closed-form on uniform token distribution" Scenario | L426 | **L450** | +24 |
| "MCI closed-form on rank-1 token distribution" Scenario | L432 | **L454** | +22 |
| "abs=1e-12 守护" | L426/L432 | **L452/L456** | +24/+22 |
| "MCI ∈ [1/d_c, 1] (closed range)" | L389 Range | **L413** | +24 |
| Eight Geometric Quantification Metrics Req-20 范围 | L389-459 | **L394-466+** | +5~7 |

### 影响

清单 03 主文中所有 spec 行号引用**系统性偏差约 24 行**（anchor 行号偏差仅 +5，但 table 内的行号偏差 +24）。这种全文档性的行号偏差暗示清单 03 是基于一个**早期 spec 快照**（可能早于 sync commit）写的，未跟随 spec 演进做 line drift 校准。

---

## F2 — test 命名错引（清单 03 声称 `test_mci_closed_form_*` 不存在）

### 清单 03 主文引用

- proposal.md L32: "`test_mci_closed_form_*` 用 spec 闭式 + abs=1e-12 守护（无 test LOCKS stale）"
- design.md L103: "既有 `tests/test_metrics.py::test_mci_closed_form_*` 用 spec 闭式 abs=1e-12 守护，无 test LOCKS stale"
- tasks.md C.6: "`test_mci_closed_form_*` tests"
- design.md L177: "tests/ `test_mci_closed_form_*` 用 spec 闭式 abs=1e-12 守护 ✓"

### 真 tests 实际（2026-09-22 `tests/test_metrics.py` 独立 grep 验证）

```
tests/test_metrics.py:99:  def test_mci_uniform_token_distribution() -> None:
tests/test_metrics.py:110: def test_mci_rank1_token_distribution() -> None:
tests/test_metrics.py:121: def test_mci_range_bound() -> None:
tests/test_metrics.py:130: def test_mci_centered_covariance_upper_endpoint_unreachable() -> None:
tests/test_metrics.py:178: def test_mci_cv_convex_hull_lower_bound_unreachable() -> None:
tests/test_metrics.py:211: def test_mci_uncentered_both_endpoints_attainable_principle() -> None:
```

### 影响

清单 03 反复引用 `test_mci_closed_form_*` —— **该 test 名 pattern 在 `tests/` 下 0 命中**（独立 grep `grep -r -F "test_mci_closed_form" tests/` 应返回 0 行）。清单 03 引用的 test 名是**虚构**或基于早期 test 命名的 stale 引用。当前真 test 名是 `test_mci_uniform_token_distribution` + `test_mci_rank1_token_distribution` 等。

---

## F3 — 测试数错误（清单 03 声称 142 passed，实际 197 passed）

### 清单 03 主文引用

- design.md L96: "既有 142 tests 全绿（spec/code 三角不变）"
- tasks.md C.6: "`uv run pytest tests/ -v`，期望 **既有 142 passed 全绿**（无 regression）"

### 真 pytest 实测（2026-09-22 `uv run pytest tests/ -q` 验证）

```
197 passed, 1 warning in 4.58s
```

### 影响

清单 03 声称"142 passed"是 142 这个数**不准确**。当前实测 **197 passed**（清单 03 设计完成 → 当前 pass 数为 197，差 +55 个 test）。

---

## F4 — 清单 03 描述的"待微调"动作已 applied（事实过期）

### 清单 03 主文描述

清单 03 描述 B1.1：`.audit/spec-math-audit.md` L524 finding 1 evidence 段**待微调**（per 用户选项 A）—— 这是清单 03 planning 草案时认为需要 apply 的 action。

### 真 spec-math-audit.md L524 实际状态（2026-09-22 grep 验证）

`.audit/spec-math-audit.md` L524 实际**已经是**微调后版本，包含：

```
【MEDIUM】ticket A8-2 L74 MCI 定义 stale (covariance → uncentered second moment)：ticket L70 说 `λ_j = C 分布协方差矩阵的特征值`（centered covariance，statistical 量），ticket L74 说 `原 CV（C 分布凸包半径）`（geometric 量）... spec L389 显式 supersede 到 `λ_j = M = (1/|T|) · Σ C_t C_tᵀ` 的特征值（uncentered second moment）... 注：本 finding evidence 段经 audit-verification cycle-12 axis-β verify-14 CITE-MISALIGNED 复核后微调（选项 A applied）—— 原 evidence 段将 ticket L70 内容（协方差）错归到 L74，且把 L74（实际是凸包半径 CV）描述为"协方差矩阵"，现精确化区分两行为独立 stale 端（centered-covariance statistical 量 vs CV geometric 量）。
```

### 影响

清单 03 是 planning 草案（2026-09-19 阶段产物），但 `.audit/spec-math-audit.md` L524 **已经被 apply**（2026-09-20 archive change 03 已完成 finding 文字微调 action）。清单 03 描述的"待微调" action 实际**已 applied**——清单 03 主文对当前事实状态的描述已**过期**。

---

## Audit Trail 完整性说明

- 本 findings.md 是 2026-09-22 独立事实验证的 audit trail（新发现），**不修改**清单 03 主文 4 个文件（proposal.md / design.md / tasks.md / specs/*/spec.md）
- 清单 03 主文保留作为 audit-trail 历史记录（per `.audit/README.md` L72 audit trail 完整性原则）
- 事实正确的版本以新 change 制品（`openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/`）+ 新 change 制品（`openspec/changes/2026-09-22-fix-archive-a8-2-cv-supersede-line-drift/`）为准
- apply 阶段按新 change 制品落地；清单 03 在 `.audit/` 下继续保留作为 planning-draft 参照

---

## 关联制品

- 清单 03 主文: `.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/{proposal.md, design.md, tasks.md, specs/*/spec.md}`
- 清单 03 KNOWN-DRIFT: `.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/KNOWN-DRIFT.md`（追加 Drift 3 子段）
- 新 change 03 制品（archive）: `openspec/changes/archive/2026-09-20-fix-ticket-a8-2-cv-supersede-and-finding-text/`
- 新 change 03 制品 KNOWN-DRIFT: `.audit/audit-verification/opsx-changes/03-fix-ticket-a8-2-cv-supersede-and-finding-text/KNOWN-DRIFT.md`（Drift 1 + Drift 2 + Drift 3 并列）
- 本新 change 制品: `openspec/changes/2026-09-22-fix-archive-a8-2-cv-supersede-line-drift/{proposal.md, design.md, tasks.md, findings.md}`

---

**生成时间**: 2026-09-22
**生成者**: 2026-09-22 独立事实验证（独立 grep / Select-String 校对）
**关联制品**: `openspec/changes/2026-09-22-fix-archive-a8-2-cv-supersede-line-drift/`（proposal.md / design.md / tasks.md / findings.md）