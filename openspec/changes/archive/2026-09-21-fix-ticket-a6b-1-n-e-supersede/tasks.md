# Tasks

## 1. wayfinder spec delta

- [x] 1.1 Edit `openspec/specs/wayfinder/spec.md` Requirement "4070 MVP Hyperparameter Set" — verify the new Scenario `MVP N_e=16 pinned for Phase 0 K-Means seeding (dormant bug warning)` is inserted between existing Scenario `Voronoi angle is N_e- and d_c-dependent` and existing Scenario `Voronoi closed-form residual is bounded`; verify existing 4 Scenarios remain verbatim unchanged
- [x] 1.2 Verify spec req-11 main closed-form (`N_e = 16`) + Voronoi tabulated values + canonical API + parameter accounting + Source field all remain verbatim unchanged (`**Source:**` MUST still start with `wayfinder/tickets/A5-3.md` as primary reverse-link)
- [x] 1.3 Verify spec req-11 Scenario count is now 5 (was 4); verify grep `grep -c "^#### Scenario:" openspec/specs/wayfinder/spec.md` returns 5 matches within req-11 range
- [x] 1.4 Verify spec req-11 anchor `<a id="req-11"></a>` remains at the start of the Requirement (lint req-33 anchor coverage unchanged)
- [x] 1.5 Run `python scripts/lint_no_source_field_drift.py` and verify exit=0 (no Source field changes; new Scenario introduces no new Source reverse-link)

## 2. ticket supersede annotation

- [x] 2.1 Edit `wayfinder/tickets/A6b-1.md` L100 — append (do NOT delete) annotation `> (historical, N_e = 64 K-Means design from N_e=64 时代; superseded by spec req-11 MVP N_e = 16 — any future Phase 0 K-Means implementation MUST use spec N_e = 16 to avoid 48 orphan clusters fatal drift)` immediately after the line `- Spherical k-means 聚 N_e = 64 类`
- [x] 2.2 Verify ticket A6b-1 L100 verbatim `Spherical k-means 聚 N_e = 64 类` is preserved (lineage not destroyed); verify `grep -nE "N_e = 64|N_e=64" wayfinder/tickets/A6b-1.md` returns ≥ 2 hits (verbatim L100 + annotation L101)
- [x] 2.3 Edit `wayfinder/tickets/A6b-1.md` L131 — append (do NOT delete, NOT a supersede) annotation `> (historical, narrative-only; closed-form γ' = ln((β_{p3} − 1) / (32 − β_{p3})) lives in spec req-7 — ticket deliberately omits explicit formula as design-prose; supersede path: spec req-7 + req-14 "Five-Phase Time-Driven Schedule" Phase 4 transition Scenario)` immediately after the line `- **Phase 4 切换瞬间重置 Adam 动量状态**（EMA 状态对 Projected SGD 无效）`
- [x] 2.4 Verify ticket A6b-1 L131 verbatim `**Phase 4 切换瞬间重置 Adam 动量状态**（EMA 状态对 Projected SGD 无效）` is preserved; verify `grep -nF "Phase 4 切换瞬间重置 Adam 动量状态" wayfinder/tickets/A6b-1.md` returns exactly 1 hit (L131 verbatim)
- [x] 2.5 Verify annotation format consistency with prior change: ticket A5-3 L62-63 supersede annotation pattern (compare against `grep -nF "(historical," wayfinder/tickets/A5-3.md`)

## 3. Verification

- [x] 3.1 Run `uv run pytest tests/ -v` and verify all 196 tests pass (no regression; no new tests since cycle-13 finding #1 is dormant)
- [x] 3.2 Run `python scripts/lint_no_dead_defensive.py` and verify exit=0 (no src/ edits in this change)
- [x] 3.3 Run `python scripts/lint_no_source_field_drift.py` and verify exit=0 (no Source field drift; new Scenario uses inline-code-span `territory_seeding` reference only)
- [x] 3.4 Run `git diff --stat` to verify line counts match design.md Migration Plan step 8 (ticket A6b-1.md +2 -0, spec/wayfinder/spec.md +8 -0 approximately); verify no CRLF contamination via `git diff --check` (per [[windows-edit-crlf-pitfall]] memory)
- [x] 3.5 Run integer closed-form reconciliation in Python REPL (bare `==` per governance/spec.md req-gov-1 第 1 条): `assert 16 == 16` (spec) and `assert 64 == 64` (ticket L100) and `assert (64 // 16) == 4` (ratio) and `assert (64 - 16) == 48` (orphan clusters); all four MUST pass with zero tolerance
- [x] 3.6 Verify spec ↔ ticket text alignment via grep: `grep -nF "MVP N_e=16 pinned for Phase 0 K-Means seeding" openspec/changes/fix-ticket-a6b-1-n-e-supersede/specs/wayfinder/spec.md` returns 1 hit (delta); `grep -nF "Voronoi angle is N_e- and d_c-dependent" openspec/specs/wayfinder/spec.md` returns 1 hit (original preserved); `grep -nF "Voronoi closed-form residual is bounded" openspec/specs/wayfinder/spec.md` returns 1 hit (original preserved)
- [x] 3.7 Verify ticket supersede annotations via grep: `grep -nF "N_e = 64 K-Means design from N_e=64 时代" wayfinder/tickets/A6b-1.md` returns 1 hit; `grep -nF "narrative-only; closed-form γ' = ln((β_{p3} − 1) / (32 − β_{p3}))" wayfinder/tickets/A6b-1.md` returns 1 hit

## 4. Commit

- [x] 4.1 Stage changes: `git add openspec/specs/wayfinder/spec.md wayfinder/tickets/A6b-1.md`
- [x] 4.2 Commit on `dev`: `git commit -m "fix(spec,ticket): close cycle-13 MEDIUM finding #1 (A6b-1 L100 N_e=64 stale + dormant bug warning) + LOW finding #2 (L131 γ' formula coverage gap)"`
- [x] 4.3 Verify commit is on `dev` branch and dev HEAD is linear (no merge commits per CLAUDE.md §4 dev 永远线性); do NOT push

## 5. Archive preparation

- [x] 5.1 Run `openspec validate fix-ticket-a6b-1-n-e-supersede --type change --strict` and verify PASS (no "Unknown item" or MODIFIED-but-not-found warnings)
- [x] 5.2 Run lint gates one more time (per CLAUDE.md §3 "`/opsx:archive` 前置条件" hard gate): `python scripts/lint_no_dead_defensive.py` and `python scripts/lint_no_source_field_drift.py` both exit=0
- [x] 5.3 Confirm no edits to: `openspec/specs/decompmoe-skeleton/spec.md`, `openspec/specs/governance/spec.md`, `src/decompmoe/extraction.py`, `tests/test_extraction.py`, MVPConfig fields (11 fields unchanged), `decompmoe/beta.py` module-level constants