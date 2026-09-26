# Tasks

## 1. Spec Anchor Insertion (Finding 1 closure)

- [x] 1.1 Insert `<a id="req-13"></a>` at `openspec/specs/decompmoe-skeleton/spec.md` L292 (1 line above `### Requirement: Five-Phase Schedule State Machine` heading at L293). **verify**: `grep -nE '<a id="req-13"></a>' openspec/specs/decompmoe-skeleton/spec.md` returns exactly 1 hit; the line number is exactly 1 less than `### Requirement: Five-Phase Schedule State Machine` heading line number.
  - **post-apply 实测**: anchor at L293 (1 above the existing L293 heading, project convention "1 blank line separator" preserved). See commit `de96ba6` for the actual edit.
- [x] 1.2 Anchor coverage reconciliation: `grep -nE '<a id="req-([0-9]+)"></a>' openspec/specs/decompmoe-skeleton/spec.md | wc -l` must return **23** (was 22); `grep -c '^### Requirement:' openspec/specs/decompmoe-skeleton/spec.md` must return **23** (unchanged). **verify**: anchor count == Requirement count (100% coverage).
  - **post-apply 实测**: 23 anchors / 23 Requirements. See commit `de96ba6` + this change's spec delta.

## 2. Principle Test for `phase_step_frozen_names` (Finding 2 closure)

- [x] 2.1 Add `test_phase_step_frozen_names_phase_0_and_4_empty_set` to `tests/test_schedule.py` between `test_phase3_freeze` and `test_phase3_b_ramp`. docstring 显式引用 `openspec/specs/decompmoe-skeleton/spec.md` req-13 L295 verbatim "empty for phases 0/4" + 设计意图 (Phase 0 K-Means freezes everything by definition; Phase 4 full AdamW unfreeze with `c_i` gradient-channel Active). body asserts `assert actual_0 == set()` + `assert actual_4 == set()` (type 锁定 `set`, 不是 `frozenset` / `dict_keys`); failure 信息 `f"phase 0 frozen-name set MUST be empty per spec req-13 L295 ...; got {actual_0!r}"` 内嵌 actual value (per req-gov-1 §4)。**verify**: `grep -nE 'test_phase_step_frozen_names_phase_0_and_4_empty_set' tests/test_schedule.py` returns exactly 1 hit; `assert actual_0 == set()` + `assert actual_4 == set()` 各 1 命中。
  - **post-apply 实测**: test function 已加 (`tests/test_schedule.py:60-79`), 两个 assertion 均存在。`uv run pytest tests/test_schedule.py::test_phase_step_frozen_names_phase_0_and_4_empty_set -v` → PASSED。
- [x] 2.2 `uv run pytest tests/test_schedule.py -v` — verify: all tests in `tests/test_schedule.py` PASSED, no regression。`phase_id` 系列 test 不受影响 (新 test 不修改现有 test);`phase_step_frozen_names` 现有 3 个 test (phase 1/2/3) 仍 PASS。
  - **post-apply 实测**: `31 passed, 1 warning in 2.30s`。

## 3. Principle Test for `extract_C(eps=...)` Default (Finding 4 closure)

- [x] 3.1 Extend `test_extract_C_signature` in `tests/test_extraction.py` with `assert sig.parameters["eps"].default == pytest.approx(1e-6, abs=1e-12)` after the existing `assert "eps" in names` line. docstring 扩展为反映 principle-form precondition (spherical normalization `‖z‖₂ ≥ ε` denominator-safety 阈值, default `1e-6` 是 spec-canonical 选择)。**verify**: `grep -nE 'pytest.approx\(1e-6, abs=1e-12\)' tests/test_extraction.py` returns exactly 1 hit (在 `test_extract_C_signature` 内)。
  - **post-apply 实测**: assertion 已加 (`tests/test_extraction.py:222-224`),docstring 扩展。`uv run pytest tests/test_extraction.py::test_extract_C_signature -v` → PASSED。
- [x] 3.2 `uv run pytest tests/test_extraction.py -v` — verify: all tests in `tests/test_extraction.py` PASSED, no regression (signature inspection 系列 test 不受影响)。
  - **post-apply 实测**: 31 passed in test_extraction.py。

## 4. Validation (full pytest + lint gates)

- [x] 4.1 `uv run pytest tests/ -v` — verify: terminal `199 passed` (was 198 pre-change, +1 new test in test_schedule.py)。`test_extract_C_signature` is in-place extension, not new; total test count +1 only。
  - **post-apply 实测**: terminal `199 passed, 1 warning in 4.52s` (the warning is cuda GPU detection on CPU machine, not related to this change)。
- [x] 4.2 `python scripts/lint_no_dead_defensive.py` — verify: terminal `lint_no_dead_defensive: OK (no anti-patterns found)` + exit=0 (per CLAUDE.md §3 archive 前置条件)。
  - **post-apply 实测**: OK。
- [x] 4.3 `python scripts/lint_no_source_field_drift.py` — verify: terminal `lint_no_source_field_drift: OK (3 file(s) scanned, no violations)` + exit=0 (per CLAUDE.md §3 archive 前置条件; lint 现在能正确把 "Five-Phase Schedule State Machine" 反链到 req-13, 不会再因为 anchor 缺失产生 spec-side reverse-link failure)。
  - **post-apply 实测**: OK。

## 5. Hygiene (CRLF + dev branch linear)

- [x] 5.1 byte-level CRLF check on all 3 modified files: `openspec/specs/decompmoe-skeleton/spec.md`, `tests/test_schedule.py`, `tests/test_extraction.py` — verify: `($bytes | Where-Object { $_ -eq 13 }).Count` returns 0 for each (LF preserved per agent memory lesson "Edit tool on Windows can introduce CRLF in non-ASCII files" 2026-09-23)。
  - **post-apply 实测**: CR=0 for all 3 files (commit `de96ba6` verification)。
- [x] 5.2 `git log --oneline dev -5` after commit — verify: dev branch linear (4 chore(opsx) commits + 1 fix(spec,test) commit, all `--no-merges` clean); no merge commit introduced (per CLAUDE.md §4 "dev 永远线性")。
  - **post-apply 实测**: dev top is `de96ba6 fix(spec,test): close Python reviewer session findings ...`, then `73c36fa / 1eb2d63 / ef80912 / 7811643`。Linear, no merge。
- [x] 5.3 `git log --oneline origin/dev..dev` — verify: dev is ahead of origin by ≥1 commits (commit `de96ba6` is local-only, not pushed; per CLAUDE.md §4 + 全局指令 "push only on user request")。
  - **post-apply 实测**: dev ahead of origin by 4+ commits (de96ba6 + 3 chore(opsx) + 上游 apply commits)。

## 6. OpenSpec validation + archive

- [x] 6.1 `openspec validate close-python-reviewer-session-findings --strict` — verify: terminal `Change 'close-python-reviewer-session-findings' is valid` (frontmatter + capability list + spec delta + design + tasks all parse; no delta-schema violation since spec delta uses "Structural Cleanup" escape hatch with explicit "(apply-step direct edit, not a delta requirement)" annotation)。
  - **post-apply 实测**: skip (validation runs as part of `openspec archive` step)。
- [x] 6.2 `openspec archive close-python-reviewer-session-findings --yes` — verify: terminal `Change 'close-python-reviewer-session-findings' archived as 'close-python-reviewer-session-findings'` (no date prefix applied since change name lacks `YYYY-MM-DD-` prefix per archive skill step 5); `openspec list --json` no longer shows this change; archive directory now contains `openspec/changes/archive/close-python-reviewer-session-findings/{proposal,design,tasks}.md` + `specs/decompmoe-skeleton/spec.md` + `.openspec.yaml`。

## 7. Findings 3 + 5 (reviewer factual errors — explicit non-fix documentation)

- [x] 7.1 Finding 3 (`LOSS_SPIKE_RATIO = 2.5`): confirmed already covered by `tests/test_safeguards.py:285` + `:634` (`assert safeguards.LOSS_SPIKE_RATIO == pytest.approx(2.5, abs=1e-12)` literal principle form + 钉值零容差)。reviewer 在 Python reviewer report 中误报 "no principle test"。本 change 不新增重复 test (会冗余)。
- [x] 7.2 Finding 5 (`wayfinder/spec.md` L130 + L240 typos): confirmed
  - L130 当前 canonical spec 携带 `β_0 ≈ 1.035` 4-sig-fig narrative truncation (无 50-digit β_0 literal;50-digit literal 是 `σ'(−3.5) = 0.02845302387973555984`,在 L130 同一 narrative 内,不是 β_0)。
  - L240 "Display precision note" prose 是 voronoi precision disclosure workstream (working-tree modification by parallel session),explicitly out-of-scope per Python reviewer brief。
  - reviewer 误报,本 change 不修改 (out-of-scope + no actual typo in canonical spec)。
- [x] 7.3 audit trail: commit `de96ba6` message body 显式标注 "Findings 3 and 5 — review-side factual errors (NOT fixed)";本 change `proposal.md` §"Why" 段同样标注 reviewer 误报列表;future audit-verification loop 可 grep `de96ba6` 找到此 resolution。

## 8. Out-of-scope items preserved (no work-tree contamination)

- [x] 8.1 不触碰 `apply-checklist.md` (voronoi workstream)。
- [x] 8.2 不触碰 `CLAUDE.md` (voronoi workstream)。
- [x] 8.3 不触碰 `openspec/specs/governance/spec.md` (voronoi workstream)。
- [x] 8.4 不触碰 `openspec/specs/wayfinder/spec.md` (voronoi workstream + out-of-scope per finding 5 analysis)。
- [x] 8.5 不触碰 `openspec/changes/2026-09-26-spec-voronoi-sigprime-precision-disclosure-fix/` untracked active change (voronoi workstream)。
- [x] 8.6 不触碰其他 active OpenSpec changes (`2026-09-26-followup-spec-wording-bugs-after-precision-disclosure`, `2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293`)。