# Tasks: fix-spec-anchor-coverage-l524-l588-l627-l293

## 1. Pre-flight verify (idempotent guard)

- [x] 1.1 Verify current state via `grep -nE '<a id="req-(25|27|33)"></a>' openspec/specs/wayfinder/spec.md` returns **0 matches**
- [x] 1.2 Verify current state via `grep -nE '<a id="req-13"></a>' openspec/specs/decompmoe-skeleton/spec.md` returns **0 matches**
- [x] 1.3 Verify byte-level CRLF on target files: `($bytes | Where-Object { $_ -eq 13 }).Count` MUST be **0** on both `wayfinder/spec.md` and `decompmoe-skeleton/spec.md` before edits
- [x] 1.4 Verify current Requirement heading positions:
  - wayfinder/spec.md L530 = Six-Module Visualization Toolchain
  - wayfinder/spec.md L594 = CentroidDriver Dual-Channel Architecture Contract
  - wayfinder/spec.md L633 = Phase 2 β Box Equality
  - decompmoe-skeleton/spec.md L303 = Five-Phase Schedule State Machine
- [x] 1.5 Verify post-plan snapshot drift: plan used L524/L588/L627/L293, current state is L530/L594/L633/L303 (drift +6/+6/+6/+10). Plan explicitly notes "实测当前行号而非 plan 行号作为 anchor" — drift is non-blocking.

## 2. Create OpenSpec change directory

- [x] 2.1 Create `openspec/changes/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/proposal.md`
- [x] 2.2 Create `openspec/changes/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/design.md`
- [x] 2.3 Create `openspec/changes/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/tasks.md` (this file)
- [x] 2.4 Create `openspec/changes/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/.openspec.yaml` with `skip_specs: true`

## 3. Apply spec edits

### 3.1 wayfinder/spec.md — insert req-25 before L530

- [x] 3.1.1 Edit `openspec/specs/wayfinder/spec.md` to insert `<a id="req-25"></a>` before `### Requirement: Six-Module Visualization Toolchain` at L530
  - **Edit tool**: `old_string` MUST end at the blank line preceding the `### Requirement:` heading (NOT include the `### Requirement:` line itself — per Memory lesson "Edit tool `old_string` boundary is greedy")
  - Proposed `old_string`:
    ```
    - **THEN** the result equals the absolute value of the sole element (`5.0` or `-5.0` → `5.0`) exactly within `abs=1e-12` (L2 norm is dimension-agnostic when `numel()==1`)

    ### Requirement: Six-Module Visualization Toolchain
    ```
  - Proposed `new_string`:
    ```
    - **THEN** the result equals the absolute value of the sole element (`5.0` or `-5.0` → `5.0`) exactly within `abs=1e-12` (L2 norm is dimension-agnostic when `numel()==1`)

    <a id="req-25"></a>

    ### Requirement: Six-Module Visualization Toolchain
    ```
- [x] 3.1.2 Post-edit grep: `grep -nF 'Six-Module Visualization Toolchain' openspec/specs/wayfinder/spec.md` MUST return ≥1 hit

### 3.2 wayfinder/spec.md — insert req-27 before L594

- [x] 3.2.1 Edit `openspec/specs/wayfinder/spec.md` to insert `<a id="req-27"></a>` before `### Requirement: CentroidDriver Dual-Channel Architecture Contract` at L594
  - Same boundary discipline
  - Proposed `old_string`:
    ```
    - **THEN** `γ' = ln(15/16) ≈ −0.0645385...` is set, AdamW momentum for `γ` is reset, and `β^eff(Phase 4, t=0) = 16.0` exactly (continuity)

    ### Requirement: CentroidDriver Dual-Channel Architecture Contract
    ```
  - Proposed `new_string`:
    ```
    - **THEN** `γ' = ln(15/16) ≈ −0.0645385...` is set, AdamW momentum for `γ` is reset, and `β^eff(Phase 4, t=0) = 16.0` exactly (continuity)

    <a id="req-27"></a>

    ### Requirement: CentroidDriver Dual-Channel Architecture Contract
    ```
- [x] 3.2.2 Post-edit grep: `grep -nF 'CentroidDriver Dual-Channel Architecture Contract' openspec/specs/wayfinder/spec.md` MUST return ≥1 hit

### 3.3 wayfinder/spec.md — insert req-33 before L633

- [x] 3.3.1 Edit `openspec/specs/wayfinder/spec.md` to insert `<a id="req-33"></a>` before `### Requirement: Phase 2 β Box Equality` at L633
  - Same boundary discipline
  - Proposed `old_string`:
    ```
    - **THEN** `γ' = ln((16 − 1) / (32 − 16)) = ln(15/16) ≈ −0.0645385...` and the resulting `β^eff(Phase 4, t=0) = 1 + 31 · σ(γ') = 16.0` exactly (continuity at the boundary)

    ### Requirement: Phase 2 β Box Equality
    ```
  - Proposed `new_string`:
    ```
    - **THEN** `γ' = ln((16 − 1) / (32 − 16)) = ln(15/16) ≈ −0.0645385...` and the resulting `β^eff(Phase 4, t=0) = 1 + 31 · σ(γ') = 16.0` exactly (continuity at the boundary)

    <a id="req-33"></a>

    ### Requirement: Phase 2 β Box Equality
    ```
- [x] 3.3.2 Post-edit grep: `grep -nF 'Phase 2 β Box Equality' openspec/specs/wayfinder/spec.md` MUST return ≥1 hit
- [x] 3.3.3 Lineage note: req-33 was previously deleted by archived change `2026-09-24-fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` (commit `24118d6`) at historical L740. This commit revives req-33 to anchor L633 Phase 2 β Box Equality — different Requirement from the original orphan (which was `Test Guard Precision for Closed-Form Numerical Claims`, migrated to governance/req-gov-1).

### 3.4 decompmoe-skeleton/spec.md — insert req-13 before L303

- [x] 3.4.1 Edit `openspec/specs/decompmoe-skeleton/spec.md` to insert `<a id="req-13"></a>` before `### Requirement: Five-Phase Schedule State Machine` at L303
  - Same boundary discipline
  - Proposed `old_string`:
    ```
    **Open follow-up**: a future ticket adopting avg-window semantics would re-evaluate the trigger condition as `flag_avg(i)` above, and MUST update spec + code + the `test_should_resurrect_current_per_step_semantic_pinned` guard test atomically; the existing guard test in `tests/test_safeguards.py` continues to pin the current per-step behavior.

    ### Requirement: Five-Phase Schedule State Machine
    ```
  - Proposed `new_string`:
    ```
    **Open follow-up**: a future ticket adopting avg-window semantics would re-evaluate the trigger condition as `flag_avg(i)` above, and MUST update spec + code + the `test_should_resurrect_current_per_step_semantic_pinned` guard test atomically; the existing guard test in `tests/test_safeguards.py` continues to pin the current per-step behavior.

    <a id="req-13"></a>

    ### Requirement: Five-Phase Schedule State Machine
    ```
- [x] 3.4.2 Post-edit grep: `grep -nF 'Five-Phase Schedule State Machine' openspec/specs/decompmoe-skeleton/spec.md` MUST return ≥1 hit

## 4. Post-edit verify

- [x] 4.1 Byte-level CRLF guard: re-run `($bytes | Where-Object { $_ -eq 13 }).Count` on both edited files; MUST remain **0**
- [x] 4.2 Anchor uniqueness check (wayfinder): `grep -nE '<a id="req-(25|27|33)"></a>' openspec/specs/wayfinder/spec.md` MUST return exactly **3 matches** (one each)
- [x] 4.3 Anchor uniqueness check (decompmoe-skeleton): `grep -nE '<a id="req-13"></a>' openspec/specs/decompmoe-skeleton/spec.md` MUST return exactly **1 match**
- [x] 4.4 Anchor 100% coverage check (wayfinder): `grep -c '^### Requirement: ' openspec/specs/wayfinder/spec.md` returns N; `grep -c '<a id="req-' openspec/specs/wayfinder/spec.md` MUST return **N+1** (L824 narrative back-link to req-20 counts as additional occurrence)
- [x] 4.5 Anchor 100% coverage check (decompmoe-skeleton): `grep -c '^### Requirement: ' openspec/specs/decompmoe-skeleton/spec.md` returns **23**; `grep -c '<a id="req-' openspec/specs/decompmoe-skeleton/spec.md` MUST return **23** (no narrative back-links)
- [x] 4.6 Requirement body preservation: 4 个标题 grep 全部 ≥1 hit (per 3.1.2, 3.2.2, 3.3.2, 3.4.2)
- [x] 4.7 Source reverse-link preservation:
  - `grep -nF '**Source:** `wayfinder/tickets/A8-3.md`' openspec/specs/wayfinder/spec.md` → 1 match (post-edit L534 — 数字 +1 因 anchor 插入)
  - `grep -nF '**Source:** `wayfinder/tickets/A6b-1.md' openspec/specs/wayfinder/spec.md` → ≥1 match (post-edit L637)
  - L594 CentroidDriver Dual-Channel 的 Source field 由 Edit tool 边界保证不变
  - L303 Five-Phase Schedule State Machine 的 Source field 由 Edit tool 边界保证不变
- [x] 4.8 Blast radius reverse-grep: 
  - `grep -rn 'req-25\b' src/ tests/ wayfinder/` → 0 hit in src/ + 1 hit in `tests/test_merge_spec_deltas.py:120` (synthetic fixture) + 0 hit in wayfinder/
  - `grep -rn 'req-27\b' src/ tests/ wayfinder/` → 0 hit
  - `grep -rn 'req-33\b' src/ tests/ wayfinder/` → 0 hit
  - `grep -rn 'req-13\b' src/ tests/ wayfinder/` → 0 hit in src/ + 0 hit in tests/ + 1 hit in wayfinder/tickets/A6a-2.md (wayfinder req-13 = Numerical Safeguards, independent capability namespace)

## 5. Lint + test integrity

- [x] 5.1 `python scripts/lint_no_source_field_drift.py` returns **exit 0** (Source field unchanged by this change)
- [x] 5.2 `python scripts/lint_no_dead_defensive.py` returns **exit 0** (defensive code pattern check unaffected)
- [x] 5.3 `uv run pytest tests/ -q --tb=short` returns **199 passed** (no behavior change, all pre-existing tests green)

## 6. Commit on dev

- [x] 6.1 `git checkout dev` (verify HEAD on dev, branch not dirty beyond intended changes)
- [x] 6.2 `git status --short` to confirm only `(a) openspec/specs/wayfinder/spec.md modified`, `(b) openspec/specs/decompmoe-skeleton/spec.md modified`, `(c) openspec/changes/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/ untracked`
- [x] 6.3 `git add openspec/specs/wayfinder/spec.md openspec/specs/decompmoe-skeleton/spec.md openspec/changes/2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293/`
- [x] 6.4 `git commit -m "fix(spec): close L4-F1 anchor coverage gap — req-25 (L530 Six-Module Visualization Toolchain) + req-27 (L594 CentroidDriver Dual-Channel Architecture Contract) + req-33 (L633 Phase 2 β Box Equality, resuscitated from orphan slot @ historical L740 deleted by commit 24118d6) for wayfinder + req-13 (L303 Five-Phase Schedule State Machine) for decompmoe-skeleton"`
- [x] 6.5 **NOT** do: `git push`, `git merge dev → main`, `git merge dev → release` (per CLAUDE.md §4 + agent memory offshore-git-workflow)

## 7. (User-driven, not in this change) Optional follow-up

- [ ] 7.1 `/opsx:archive 2026-09-26-fix-spec-anchor-coverage-l524-l588-l627-l293` — only when user confirms ready
- [ ] 7.2 Independent follow-up `fix-config-docstring-beta-line-drift` change (L2-F1 finding) — out of this change scope
- [ ] 7.3 Independent follow-up `fix-wayfinder-flops-routing-pytest-coverage` change (R-4 finding) — out of this change scope