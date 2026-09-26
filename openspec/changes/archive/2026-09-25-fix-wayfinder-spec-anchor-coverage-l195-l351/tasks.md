# Tasks: fix-wayfinder-spec-anchor-coverage-l195-l351

## 1. Pre-flight verify (idempotent guard)

- [ ] 1.1 Verify current state via `grep -nE 'req-(16|21)"><\/a>' openspec/specs/wayfinder/spec.md` returns **0 matches** for both req-16 and req-21 (anchor not yet present)
- [ ] 1.2 Verify current state via `grep -nE '^### Requirement: (No Shared Expert|Prefill And Decode)' openspec/specs/wayfinder/spec.md` returns exactly 2 matches at L195 and L351 (the two unanchored Requirements)
- [ ] 1.3 Verify byte-level CRLF on target file: `($bytes | Where-Object { $_ -eq 13 }).Count` MUST be **0** before edit

## 2. Apply spec edits

- [ ] 2.1 Edit `openspec/specs/wayfinder/spec.md` to insert `<a id="req-21"></a>` before `### Requirement: No Shared Expert (Pure Geometric Routing)` at L195
  - **Edit tool**: `old_string` MUST end at the blank line preceding the `### Requirement:` heading (NOT include the `### Requirement:` line itself — per Memory lesson "Edit tool `old_string` boundary is greedy")
  - Proposed `old_string`: 
    ```
    with no custom CUDA / / retargeting replacement
    
    ### Requirement: No Shared Expert
    ```
    Proposed `new_string`:
    ```
    with no custom CUDA / / retargeting replacement
    
    <a id="req-21"></a>
    
    ### Requirement: No Shared Expert
    ```
- [ ] 2.2 Edit `openspec/specs/wayfinder/spec.md` to insert `<a id="req-16"></a>` before `### Requirement: Prefill And Decode Share The Same Algorithm` at L351
  - Same boundary discipline; `old_string` ends at the blank line preceding the heading
  - Proposed `old_string`:
    ```
    does NOT advance the phase
    
    ### Requirement: Prefill And Decode Share
    ```
    Proposed `new_string`:
    ```
    does NOT advance the phase
    
    <a id="req-16"></a>
    
    ### Requirement: Prefill And Decode Share
    ```

## 3. Post-edit verify

- [ ] 3.1 Byte-level CRLF guard: re-run `($bytes | Where-Object { $_ -eq 13 }).Count` on the edited file; MUST remain **0**
- [ ] 3.2 Anchor uniqueness check: `grep -nE '<a id="req-(16|21)"></a>' openspec/specs/wayfinder/spec.md` MUST return **exactly 1 match for req-16** (at L351 + 1 = L351 after line insertion) and **exactly 1 match for req-21** (at L195 + 1)
- [ ] 3.3 Anchor 100% coverage check: `grep -c '^### Requirement: ' openspec/specs/wayfinder/spec.md` returns N; `grep -c '<a id="req-' openspec/specs/wayfinder/spec.md` MUST return N as well (i.e., all Requirements have anchors)
- [ ] 3.4 Requirement body preservation: `grep -nF 'No Shared Expert (Pure Geometric Routing)' openspec/specs/wayfinder/spec.md` MUST return ≥1 hit (the heading itself); `grep -nF 'Prefill And Decode Share The Same Algorithm' openspec/specs/wayfinder/spec.md` MUST return ≥1 hit — confirms Edit did not consume the headings
- [ ] 3.5 Source reverse-link preservation: `grep -nF '**Source:** `wayfinder/tickets/A5-2.md`' openspec/specs/wayfinder/spec.md` returns 1 match (L199 unaffected); `grep -nF '**Source:** `wayfinder/tickets/A7-1.md`' openspec/specs/wayfinder/spec.md` returns 1 match (L355 unaffected)
- [ ] 3.6 Blast radius reverse-grep: `grep -rn 'req-16\b\|req-21\b' -- openspec/src/ tests/ wayfinder/` returns the **expected** set (decompmoe-skeleton req-16 + verify_fixes.py req-21/req-34 tracking only — no unintended cross-references)

## 4. Lint + test integrity

- [ ] 4.1 `python scripts/lint_no_source_field_drift.py` returns **exit 0** (Source field unchanged by this change)
- [ ] 4.2 `python scripts/lint_no_dead_defensive.py` returns **exit 0** (defensive code pattern check unaffected)
- [ ] 4.3 `uv run pytest tests/ -q --tb=short` returns **199 passed** (no behavior change, all pre-existing tests green)

## 5. Commit on dev

- [ ] 5.1 `git checkout dev` (verify HEAD on dev, branch not dirty beyond intended changes)
- [ ] 5.2 `git status --short` to confirm only `(a) openspec/specs/wayfinder/spec.md modified`, `(b) openspec/changes/2026-09-25-fix-wayfinder-spec-anchor-coverage-l195-l351/ untracked`
- [ ] 5.3 `git add openspec/specs/wayfinder/spec.py openspec/changes/2026-09-25-fix-wayfinder-spec-anchor-coverage-l195-l351/` (note: `.py` typo intentional? — NO, correct path is `spec.md`; double-check before staging)
- [ ] 5.4 `git commit -m "fix(spec): close L4-F1 anchor coverage gap — req-21 for No Shared Expert (L195) + req-16 for Prefill And Decode (L351)"`
- [ ] 5.5 **NOT** do: `git push`, `git merge dev → main`, `git merge dev → release` (per CLAUDE.md §4 + agent memory offshore-git-workflow)

## 6. (User-driven, not in this change) Optional follow-up

- [ ] 6.1 `/opsx:archive 2026-09-25-fix-wayfinder-spec-anchor-coverage-l195-l351` — only when user confirms ready (per agent memory "Spec migration leaves orphan anchor in source capability" → archive historian discipline)
- [ ] 6.2 Independent follow-up `fix-config-docstring-beta-line-drift` change (L2-F1 finding) — out of this change scope
- [ ] 6.3 Independent follow-up `fix-wayfinder-flops-routing-pytest-coverage` change (R-4 finding) — out of this change scope