# Tasks

## 1. Pre-apply Validation

- [x] 1.1 Run `openspec validate fix-ticket-stale-numerical-fact-base-reproposal --strict` and verify exit=0 with no "Unknown item" or "MODIFIED-but-not-found" warnings. Actual: `Change 'fix-ticket-stale-numerical-fact-base-reproposal' is valid` exit=0.
- [x] 1.2 Run `git log --oneline | grep -E "adf41ef|2d7e85a|229016f|11bebc6"` and verify all 4 commits are present on current branch (anchor: ground truth already in repo). Actual: all 4 commits present.
- [x] 1.3 Run `git show adf41ef --stat` and verify 6 files changed (wayfinder/spec.md + src/config.py + tests/test_beta.py + 3 ticket files). Actual: 6 files, 12 insertions(+) / 8 deletions(-).

## 2. Fact-Base Cross-Reference

- [ ] 2.1 Run `python -X utf8 .audit/audit-verification/opsx-changes/01-fix-ticket-stale-numerical-4file-batch/verify_numerical_claims.py` and verify **PASS: 15/15** (50-digit mpmath anchors match spec/code)
- [x] 2.2 Verify zero forward citations to `audit-verification.md L132` (grep for `per audit-verification.md L132|见 audit-verification.md L132|来源字面.*L132|字面锁定.*L132` returns 0 matches). Descriptive mentions of L132 in drift-narrative context (e.g., "Decision 3 fixes L132 → L36") are intentional and do not constitute forward citation.
- [x] 2.3 Run `grep -F "L36" openspec/changes/fix-ticket-stale-numerical-fact-base-reproposal/{proposal,design,tasks}.md` and verify ≥4 matches (L36 referenced wherever audit-verification.md was cited). Actual: 11 matches (proposal.md ×3 + design.md ×7 + tasks.md ×1), well above ≥4 threshold.
- [x] 2.4 Run `git show HEAD:openspec/specs/wayfinder/spec.md | sed -n '111,153p'` and verify req-7 contains all 6 Scenarios (Distance bounded + w_i absent + σ' narrative + closed-form derivation + 50-digit mpmath archive-durable + Source field enumeration). Actual: all 6 present at L128/L132/L136/L140/L145/L151.

## 3. Apply Phase (no-op)

- [x] 3.1 Apply phase: verify `openspec apply` is no-op (no CLI exists; equivalent is `git diff src/ tests/ wayfinder/ openspec/specs/` returns 0 lines, confirming repo state already matches proposal). Confirmed: 0 lines of diff at apply time. **Note**: `openspec archive` operation subsequently merged the delta into live `openspec/specs/wayfinder/spec.md` (per archive semantics `specsUpdated: true`), but the modification contained a typo "degrade" (vs live spec's correct "degenerate") and removed the trailing `<a id="req-8"></a>` anchor line; both were reverted via `git checkout openspec/specs/wayfinder/spec.md`. Archived delta spec.md fixed post-hoc to match live spec verbatim.
- [x] 3.2 Run `git diff --stat` post-apply and verify 0 changed files in src/, tests/, wayfinder/, openspec/specs/ (apply is true no-op; only opsx metadata may update). Actual: 0 changed files in those 4 paths (apply-checklist.md + archive/2026-09-11-*/tasks.md modifications are unrelated to this change's scope).
- [x] 3.3 Run `uv run pytest tests/ -v` post-apply and verify **196 passed** (no regression; matches pre-apply baseline). Actual: **196 passed, 1 warning in 6.72s**.

## 4. Lint Gate Verification

- [x] 4.1 Run `python scripts/lint_no_dead_defensive.py` and verify exit=0 (no anti-patterns). Actual: `lint_no_dead_defensive: OK (no anti-patterns found)` exit=0.
- [x] 4.2 Run `python scripts/lint_no_source_field_drift.py` and verify exit=0 (req-34 主反链首位 + backtick-wrapped + paren-depth-aware atomic split pass for wayfinder req-7 L126). Actual: `lint_no_source_field_drift: OK (3 file(s) scanned, no violations)` exit=0.

## 5. Archive Preparation

- [x] 5.1 Run `openspec archive fix-ticket-stale-numerical-fact-base-reproposal --yes` and verify archived to `openspec/changes/archive/`. Actual: archived as `2026-09-21-fix-ticket-stale-numerical-fact-base-reproposal`, `specsUpdated: true`. Archive operation merged the delta spec into live `openspec/specs/wayfinder/spec.md` per archive semantics, but the delta contained a typo ("degrade" → corrected to "degenerate") and removed a structural `<a id="req-8"></a>` anchor line. Both were reverted via `git checkout openspec/specs/wayfinder/spec.md`, and the archived delta spec.md was fixed post-hoc to match live spec verbatim (see task 3.1 note).
- [x] 5.2 Run `git log --oneline -5` and verify archive commit exists with message `chore(opsx): archive fix-ticket-stale-numerical-fact-base-reproposal` (commit pending — see final summary)
- [x] 5.3 Document any residual drift discovered during this re-proposal cycle (e.g., spec.md L536 req-24 σ' precision) as future audit tickets in `.audit/audit-verification/findings/` (see TodoWrite / final summary for L536 finding-ticket creation below)