# Proposal: close-python-reviewer-session-findings

## Why

Python reviewer Agent (`agent-b1a39f2827bf`, 2026-09-26) audited DecompMoE post-A3 archive cycle on 4 axes (spec math correctness, wayfinder ↔ spec alignment, code ↔ spec formalization, TDD principle coverage). Verdict: spec/code/TDD 三角自洽 = **PASS**, with 5 findings. Of the 5, 3 are in-scope real gaps (1 MEDIUM anchor coverage, 2 LOW principle tests missing), 2 are review-side factual errors (reviewer claimed `LOSS_SPIKE_RATIO` had no principle test — false positive, already covered at tests/test_safeguards.py L285 + L634; reviewer claimed wayfinder L130 had a 50-digit β_0 typo — false positive, current canonical spec carries `β_0 ≈ 1.035` 4-sig-fig, no such literal exists). This change closes the 3 in-scope findings; the 2 factual errors are documented in commit message `de96ba6` for audit trail.

## What Changes

- **`openspec/specs/decompmoe-skeleton/spec.md`**: insert `<a id="req-13"></a>` at L293 (above `### Requirement: Five-Phase Schedule State Machine`). Closes the 100% anchor coverage gap (CLAUDE.md §6 第 8 条 violation): 23 Requirements / 22 anchors (was) → 23/23 (now).
- **`tests/test_schedule.py`**: add `test_phase_step_frozen_names_phase_0_and_4_empty_set`. Pins the empty-set contract for `phase_step_frozen_names(0)` and `phase_step_frozen_names(4)` per spec req-13 L295 ("empty for phases 0/4"). Prevents silent regression of the dual-channel freeze contract.
- **`tests/test_extraction.py`**: extend `test_extract_C_signature` with `pytest.approx(1e-6, abs=1e-12)` assertion on the `eps` parameter default. Pins the closed-form precondition `‖z‖₂ ≥ ε` for safe spherical normalization (spec req-7 L100).

No breaking changes. No code changes. No src/ modifications. No ticket modifications. No canonical-spec content changes (only an anchor insertion on an existing Requirement heading).

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `decompmoe-skeleton`: add `<a id="req-13"></a>` anchor at L293 of `### Requirement: Five-Phase Schedule State Machine` (closes 100% anchor coverage gap per CLAUDE.md §6 第 8 条). The Requirement body itself is unchanged; only the reverse-linkable anchor is added.

## Impact

- **Affected code**: 无 (`src/decompmoe/` 0 文件改动; 所有变更在 spec.md anchor + pytest test)
- **Affected tests**: 2 文件 (`tests/test_schedule.py` +24 行 新 test; `tests/test_extraction.py` +13/-1 行 扩展 test_extract_C_signature)
- **Affected specs**: 1 文件 1 行 (`openspec/specs/decompmoe-skeleton/spec.md` +1 anchor)
- **Affected wayfinder tickets**: 无 (`wayfinder/tickets/` 0 文件改动)
- **Affected OpenSpec source 反链**: 无变化 (anchor 是 reverse-link target, source 引用方无变化)
- **Affected APIs / dependencies**: 无
- **Affected systems**: 无
- **Risk**:
  - **anchor 位置错位**: spec delta 必须 `<a id="req-13"></a>` 在 L293 `### Requirement: Five-Phase Schedule State Machine` 之上,精确 1 行间隔(per agent memory lesson "Spec migration leaves orphan anchor in source capability":双向配对 anchor + Requirement title;漏一个 = orphan anchor 缺陷). **Mitigation**: delta spec 用 `### REMOVED Requirements` 不适用(无删除);通过在 spec.md L293 +1 行 anchor 与周围 L226 req-12 / L313 req-14 形成 100% 链式覆盖,post-apply `grep -nE '<a id="req-([0-9]+)"></a>' openspec/specs/decompmoe-skeleton/spec.md | wc -l` = 23 验证。
  - **CLAUDE.md §6 第 8 条 "100% anchor 覆盖" violation 历史**: 同类 violation 在 decompmoe-skeleton 已发生过 (req-13 是 schema evolution 残留空洞,per agent memory "spec 文件的 anchor 序列是 schema 演化的残留(每次 change 增/删/合并都会留下空洞)"),本 change 是修复而非引入。**Mitigation**: 修复后 `tests/test_extraction.py::test_extract_C_signature` 等 principle test 不依赖 anchor,但所有反向 lint (`scripts/lint_no_source_field_drift.py` 的 per-capability primary reverse-link rule) 现在能正确把"Req X in decompmoe-skeleton"反链到 L293 (而非报错 "missing anchor")
  - **CRLF contamination on Edit tool**: Windows + non-ASCII 文件 (中文 spec) 经 Edit tool 写入可能引入 CRLF (per agent memory lesson "Edit tool on Windows can introduce CRLF in non-ASCII files" 2026-09-23). **Mitigation**: post-apply byte-level CRLF 检查 `$bytes = [System.IO.File]::ReadAllBytes('openspec/specs/decompmoe-skeleton/spec.md'); ($bytes | Where-Object { $_ -eq 13 }).Count == 0`. post-apply 实测已 PASS (commit de96ba6 验证 CR=0).
  - **pyproject.toml / dev dependencies 未变更**: 本 change 不引入新 pytest fixture 或新依赖。`pytest.approx` 已存在 (`tests/test_extraction.py:11 import pytest`).
- **Source**:
  - Python reviewer report (session mvs_c1970089aa9341cda22ce41910b792a1, 2026-09-26) Findings 1, 2, 4
  - `openspec/specs/decompmoe-skeleton/spec.md` L293 "Five-Phase Schedule State Machine" Requirement body (anchor missing)
  - `openspec/specs/decompmoe-skeleton/spec.md` L295 ("empty for phases 0/4" verbatim phrasing)
  - `openspec/specs/wayfinder/spec.md` L100 (closed-form precondition `‖z‖₂ ≥ ε` for safe spherical normalization, ε default = 1e-6)
  - `openspec/specs/governance/spec.md` `req-gov-1` (浮点闭式 `pytest.approx(value, abs=...)`; 钉值零容差 `abs=1e-12`)
  - `CLAUDE.md` §6 第 8 条 ("spec anchor 100% 覆盖" hard constraint)
  - `CLAUDE.md` §3 TDD 工作流 (per-test selection of `approx` vs `==` follows integer-vs-float binary exemption; principle-form test 优先于 functional-only test)
  - agent memory 2026-09-23 lesson "Edit tool on Windows can introduce CRLF in non-ASCII files" (CRLF hygiene 协议)
  - agent memory 2026-09-24 lesson "Spec migration leaves orphan anchor in source capability" (anchor + Requirement title 双向配对)
  - agent memory "spec 文件的 anchor 序列是 schema 演化的残留" (anchor 序列必须实测 grep 后再决定 next-free N)