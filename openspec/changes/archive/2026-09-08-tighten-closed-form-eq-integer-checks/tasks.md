## 1. Surgical Test Edits

- [x] 1.1 Tighten `tests/test_config.py:86` (inside function `test_flops_per_layer_exact_33554432`, NOT inside `test_flops_total_exact_134217728` which is at L94): replace `assert flops_actual == 134_217_728, f"actual={flops_actual}"` with `assert flops_actual == pytest.approx(134_217_728, abs=0), f"actual={flops_actual}"` (verbatim edit, single-line; message already conforms to `f"actual={...}"` form). **Note (post-audit 2026-09-07):** this edit closed the LOW-2 site from `archive/2026-09-06` but **did NOT close** the Decision 4 carve-out at `test_flops_total_exact_134217728` L94 — that remains a deferred follow-up (see §5.1).

  **§8 supersession note**: per commit `bec147d` (2026-09-07 21:21:31) + commit `83a0503` (2026-09-07 22:02:52), `pytest.approx(..., abs=0)` for integer closed-form was **reversed** to bare `==` per `CLAUDE.md` §6 第 8 条's integer-vs-float binary exemption (see `specs/wayfinder/spec.md` Policy lineage). All integer sites tightened by §1.1, §1.2, §1.3, §5.1, §5.2, §6.1 were reverted to bare `==` by `83a0503`. The present spec delta has been re-aligned (MODIFIED → ADDED; obligation 1 flipped to require bare `==` for integer closed-form) to match this policy.

- [x] 1.2 Tighten `tests/test_extraction.py:103` (inside function `test_complexity_budget`, NOT `test_per_head_mac_count` which does not exist — spec delta scenario was renamed in this `/opsx:update` per Finding #4): replace `assert expected == 33_040, f"closed form must equal 33_040; got {expected}"` with `assert expected == pytest.approx(33_040, abs=0), f"actual={expected}"` (single-line; also normalizes message form to `f"actual={...}"` per design Decision 3). **Note:** required adding `import pytest` to file header (was missing pre-edit); original assertion line is now at L104 due to +1 header insertion. CRLF restoration was applied (`sed -i 's/\r$//'` per [[windows-edit-crlf-pitfall]]) before import was added.

  **§8 supersession note**: per `83a0503`, this site reverted to bare `==` (`assert expected == 33_040, f"actual={expected}"`); the `import pytest` header line remains as orphaned F401 (Finding #3 in audit #3) — see §8.1 lint gate task.

- [x] 1.3 Tighten `tests/test_experts.py:100`: replace `assert total == 100_663_296` with `assert total == pytest.approx(100_663_296, abs=0), f"actual={total}"` (single-line; adds `f"actual={...}"` message form which was missing per design Decision 3). **Note (anticipated):** required adding `import pytest` to file header (verified absent via grep before edit); applied, file LF restored via `sed -i 's/\r$//'` per [[windows-edit-crlf-pitfall]].

  **§8 supersession note**: per `83a0503`, both L100 and L101 reverted to bare `==`; `import pytest` remains as orphaned F401 — see §8.1.

## 2. Verification

- [x] 2.1 Run `uv run pytest tests/test_config.py::test_flops_total_exact_134217728 tests/test_extraction.py::test_complexity_budget tests/test_experts.py::test_expert_pool_param_count -v` and verify all 3 target tests PASS. **Note:** corrected invocation from `test_per_head_mac_count` (the originally-named test that does not exist) to `test_complexity_budget` (the actual function name containing L103's `assert expected == 33_040`). Result: **3 passed in 11.87s**.
- [x] 2.2 Run `uv run pytest tests/ -v`. Result: **141 passed in 10.18s** (1 warning = pre-existing CUDA driver warning, unrelated to this change). No regressions. **Note (post-audit 2026-09-07 Finding #7):** the originally-recorded "143 passed" was an overcount; `uv run pytest tests/ --collect-only -q` confirms **141 tests collected**.
- [x] 2.3 Run `git diff --stat`. Result: **`3 files changed, 5 insertions(+), 3 deletions(-)`**. The 2 extra insertions beyond the surgical 3 are the `import pytest` lines added to `test_extraction.py` and `test_experts.py` headers (required to make `pytest.approx(...)` resolvable; see 1.2/1.3 notes). `test_config.py` was already importing pytest (L14). CRLF restoration applied twice (`sed -i 's/\r$//'` on both `test_extraction.py` and `test_experts.py`) per [[windows-edit-crlf-pitfall]].
- [x] 2.4 Run `git diff` per file. Result: each file's diff is **only the assertion line change + (where required) one `import pytest` line**; no adjacent whitespace/comment/docstring changes — surgical per `CLAUDE.md` §3.

## 3. Commit

- [x] 3.1 Stage the 3 modified files: `git add tests/test_config.py tests/test_extraction.py tests/test_experts.py`
- [x] 3.2 Commit on `dev` branch with conventional-commit message. Result: **commit `19d901e` on `dev` HEAD** (`git branch --show-current` = `dev`; `git log --oneline -3` shows `19d901e → 5416f93 → 78f08f6`, no main/release movement).

## 4. Post-Commit Handoff

- [x] 4.1 Confirm `git status` is clean (no unstaged changes from this change). Result: the 3 modified test files are no longer in dirty area; remaining 10 dirty files (`7 .claude/* + 2 spec.md + tests/test_sphere.py`) and 6 untracked paths are pre-existing residuals from prior sessions, unrelated to this change. The `openspec/changes/tighten-closed-form-eq-integer-checks/` directory itself is untracked by design (OpenSpec convention: change directory lives outside git until archive).
- [x] 4.2 Run `openspec validate tighten-closed-form-eq-integer-checks`. Result: **Change 'tighten-closed-form-eq-integer-checks' is valid**.
- [x] 4.3 Report completion to user (see Implementation Complete section above).

## 5. Post-Review Audit Follow-ups (added 2026-09-07 via `/opsx:update` after post-apply audit)

**Why added**: post-apply audit (run 2026-09-07 with `code-review max`) revealed 8 findings. Of those, **5 are in scope** for this change (Finding #4 spec naming already fixed via Revision B; Findings #1/#2/#6/#7 still actionable). **2 are pre-existing and out of scope** (Finding #3 L83 structural identity; Finding #8 L88 cosmetic comment style) — explicitly excluded per `CLAUDE.md` §3 "Touch only what you must". This section captures the actionable in-scope findings so a future `/opsx:apply` on this change can land a follow-up commit that fully closes the `archive/2026-09-06 design.md Decision 4` carve-out.

- [x] 5.1 (HIGH, Finding #2) Tighten `tests/test_config.py:94`. Result: applied (multi-line form: `assert ... == pytest.approx(134_217_728, abs=0), f"actual=..."`) — file changed: 3 insertions + 1 deletion; LF preserved.

  **§8 supersession note**: per `83a0503`, this site reverted to bare `==` (the `pytest.approx(..., abs=0)` form was the source of Finding #7's "implicit rel=1e-6 magnitude-scaling" concern that motivated the policy reversal).

- [x] 5.2 (MEDIUM, Finding #1) Tighten `tests/test_config.py:87`. Result: applied (single-line, `assert per_layer == pytest.approx(33_554_432, abs=0), f"actual={per_layer}"`) — file changed cumulative: 4 insertions + 2 deletions.

  **§8 supersession note**: per `83a0503`, this site reverted to bare `==`.

- [x] 5.3 (LOW, Finding #6) Update docstring at `tests/test_config.py:57-58`. Result: applied (prose `==` replaced with `≈` + appended `pytest.approx(value, abs=0)` per §6 第 8 条 note) — file changed cumulative: 8 insertions + 5 deletions.

  **§8 supersession note**: per `83a0503`, docstring wording sync-ed to match the bare-`==` migration (`tests/test_config.py:60` per `83a0503` commit summary).
- [x] 5.4 Verify all 3 §5 edits. Result: `uv run pytest tests/test_config.py::test_flops_total_exact_134217728 tests/test_config.py::test_flops_per_layer_exact_33554432 tests/test_config.py::test_total_param_estimate -v` → **3 passed in 0.04s**. Total suite still **141 tests** (no regression).
- [x] 5.5 Verify `git diff --stat`. Result: `tests/test_config.py | 13 ++++++++-----` (1 file, 8 insertions, 5 deletions — 3 logical sites: L94 multi-line assertion, L87 single-line assertion, L57-58 docstring). LF preserved (no CRLF contamination this session).
- [x] 5.6 Commit §5 follow-ups on `dev` branch. Result: **commit `ae14868` on `dev` HEAD ahead of `19d901e`** (`git log --oneline -4` shows `ae14868 → 1601c87 → 78f08f6 → 7929770`; no main/release movement). `openspec validate tighten-closed-form-eq-integer-checks` PASS.

## 6. Post-Second-Review Follow-ups (added 2026-09-07 via second `/opsx:update` after post-apply audit #2)

**Why added**: post-apply audit #2 (run 2026-09-07 with `code-review max`, after commits `19d901e` + `ae14868`) surfaced 13 findings. Of those, **6 are in scope** for this change:
- **Finding #1-#5**: spec line drift (5 stale references in `specs/wayfinder/spec.md` + 1 internal proposal inconsistency) — already fixed via Revision A (proposal.md) + Revision B (spec.md).
- **Finding #7**: `tests/test_experts.py:100` redundant `assert total == expected` (raw `==`) — tracked in §6.1 below for code fix.

**2 are principle-level out-of-scope** (Finding #6 extract_C MAC count tautology; Finding #13 hardcoded `cfg_hkv` literals) — explicitly excluded per `CLAUDE.md` §3 "Touch only what you must" + design Decision 4 Addendum. Tracked in §6.2 / §6.3 below.

**5 are pre-existing and out of scope** (Finding #8 L34 raw `==`, Finding #9 L107 parity raw `==`, Finding #10 L135 scaling identity raw `==`, Finding #11 spec L13 narrow enumeration, Finding #12 spec L9 `3e-7` envelope) — explicitly excluded per proposal Non-Goals.

- [x] 6.1 (HIGH, Finding #7) Tighten `tests/test_experts.py:100`. Result: applied (`assert total == pytest.approx(expected, abs=0), f"actual={total}"`; L101 unchanged — preserved structural identity test in addition to closed-form constant test). File changed: 3 insertions + 2 deletions. LF preserved.

  **§8 supersession note**: per `83a0503`, both L100 and L101 reverted to bare `==`; the L101 site now reads `assert total == 100_663_296, f"actual={total}"` (per system-reminder Read 2026-09-08 confirming post-83a0503 state).

- [x] 6.2 (MEDIUM, Finding #13) Replace hardcoded literals at `tests/test_extraction.py:99` (was L98 before import). Result: applied (`from decompmoe.config import MVPConfig` added at L15; `cfg = MVPConfig()` + `cfg_hkv, cfg_dk, cfg_dc = cfg.H_kv, cfg.d_k, cfg.d_c` at L99-100). File changed cumulative: 5 insertions + 2 deletions. LF preserved.

  **§8 supersession note**: per `83a0503`, the L106 assertion line still uses `assert expected == 33_040, f"actual={expected}"` (bare `==`, matching policy). The `cfg = MVPConfig()` literal reference from §6.2 is **preserved** (a valuable single-source-of-truth improvement that survives the policy reversal) — this change's contribution survives independently of the integer-vs-float policy debate.
- [x] 6.3 (LOW, Finding #6 acknowledgment) **No code change** — Finding #6 (33_040 MAC tautology) is principle-level, requires architectural work beyond `CLAUDE.md` §3 "Touch only what you must". Tracked in design Decision 4 Addendum as future follow-up change.
- [x] 6.4 Verify all §6 code edits. Result: `uv run pytest tests/test_experts.py::test_expert_pool_param_count tests/test_extraction.py::test_complexity_budget -v` → **2 passed in 5.43s**.
- [x] 6.5 Verify `git diff --stat` after §6 edits. Result: cumulative `tests/test_experts.py | 5 +++--` (3 ins, 2 del across L11 import pytest + L100-101 pytest.approx) + `tests/test_extraction.py | 7 +++++--` (5 ins, 2 del across L11 import pytest + L15 import MVPConfig + L99-100 cfg/literals). LF preserved (no CRLF contamination).
- [x] 6.6 Commit §6 follow-ups on `dev` branch. Result: **commit `dd7fa62` on `dev` HEAD ahead of `ae14868`** (`git log --oneline -5` shows `dd7fa62 → 2bae9b7 → df9bfd7 → ae14868 → 1601c87`; no main/release movement). `openspec validate tighten-closed-form-eq-integer-checks` PASS (with 1 INFO: archive would refuse this delta because Requirement header in main spec doesn't match — see §7 below).

## 7. Archive-blocking issue (discovered post-§6 commit, RESOLVED)

**Issue (resolved)**: `openspec validate ... --strict --type change` reported:

> ℹ [INFO] wayfinder/spec.md: Archive would refuse this delta: wayfinder MODIFIED failed for header "### Requirement: Test Guard Precision for Closed-Form Numerical Claims" - not found

**Root cause**: Verification (`grep -n "^### Requirement:" openspec/specs/wayfinder/spec.md` returned 27 Requirements; `grep "Test Guard Precision" openspec/specs/wayfinder/spec.md` returned No matches) confirmed that the **main spec `openspec/specs/wayfinder/spec.md` does NOT contain any Requirement with header "Test Guard Precision for Closed-Form Numerical Claims"**. The proposing phase (and the upstream `archive/2026-09-06-tighten-test-precision-tolerance` archive) had used `## MODIFIED Requirements` for this delta, but MODIFIED requires the target Requirement to exist in the main spec — which it does not. The `archive/2026-09-06` archive step appears to have archived the change directory but **did not** merge the Requirement into the main spec (likely a bug in that archive run; verified by reading `openspec/specs/wayfinder/spec.md` directly — no "Test Guard Precision" header).

**Resolution** (applied via this `/opsx:update` round):
1. `openspec/changes/tighten-closed-form-eq-integer-checks/specs/wayfinder/spec.md`: change `## MODIFIED Requirements` → `## ADDED Requirements`. This makes the delta APPEND the new Requirement to `wayfinder/spec.md` during archive, rather than failing the header lookup.
2. `openspec/changes/tighten-closed-form-eq-integer-checks/proposal.md` Capabilities section: clarify "Modified Capabilities: （无）" + new "Added Requirements to Existing Capability: wayfinder — ADDED Requirement 'Test Guard Precision for Closed-Form Numerical Claims'" section with the §7 root cause explanation.

**Validation after fix**:
```
$ openspec validate tighten-closed-form-eq-integer-checks --type change --strict
Change 'tighten-closed-form-eq-integer-checks' is valid
```
(NO archive-blocking INFO warning)

**Archive should now proceed without header-not-found rejection.** The appended Requirement will become part of main `openspec/specs/wayfinder/spec.md` going forward.

## 8. Policy reversal supersession (added 2026-09-08 via `/opsx:update` after audit #3 + user review)

**Why added**: post-apply audit #3 (run 2026-09-08 with `code-review max`, after commit `83a0503`) surfaced 15 findings including the critical observation that **commits `bec147d` and `83a0503` reversed the integer-closed-form pytest.approx policy established by this change**. The new requirement text was rewritten to align with `CLAUDE.md` §6 第 8 条's amended "integer-vs-float binary exemption" policy; the present §8 records the reversal lineage so future auditors can trace the policy evolution:

- `archive/2026-09-06` (proposing) — original "raw `==` integer MUST NOT appear" prohibition
- `19d901e` (this change §1-§4) — partially implemented `pytest.approx(..., abs=0)` at 3 sites
- `ae14868` (this change §5) — closed the `archive/2026-09-06 design.md Decision 4` carve-out at L94 + L87 + docstring hygiene
- `dd7fa62` (this change §6) — fixed `tests/test_experts.py:100` + `tests/test_extraction.py:98` literals
- `bec147d` (2026-09-07 21:21:31) — **policy amendment** to `CLAUDE.md` §6 第 8 条 introducing integer-vs-float binary exemption; migrated `tests/test_config.py` L88/L90/L96 from `pytest.approx(..., abs=0)` to bare `==`
- `83a0503` (2026-09-07 22:02:52, dev HEAD) — **policy sync-amendment** to `CLAUDE.md` §3 + migrated remaining integer sites (`tests/test_config.py` L65/L66/L69 + `tests/test_extraction.py` L106 + `tests/test_experts.py` L100/L101) to bare `==`. The commit message states: "Per §6 第 8 条: integer closed-form uses bare '==' instead of pytest.approx(..., abs=0)."
- All changes 19d901e + ae14868 + dd7fa62 site-level commits are **superseded** by `83a0503` for the integer-vs-float question; the `MVPConfig`-based literal fix from §6.2 (`cfg = MVPConfig()` + `cfg.H_kv` etc.) survives independently as a useful single-source-of-truth improvement.

### §8 Tasks (calibration with `CLAUDE.md` §6 第 8 条 amended policy)

- [ ] 8.1 **Lint gate** (per user pitfall #1): add a lint rule that enforces the **binary (integer vs float) policy** — not a single-sided rule. The rule MUST allow both forms:
  - **Float closed-form** → MUST `pytest.approx(..., abs=... or rel=...)` with explicit tolerance
  - **Integer closed-form** → MUST bare `==` (钉值零容差); `pytest.approx(..., abs=0)` for integers would be flagged as wrong-direction (introduces implicit `rel=1e-6`)
  - Gate dry-run BEFORE commit: launch the lint gate against the current working tree and confirm all 9 integer sites use bare `==` (green) and all float sites use `pytest.approx(..., abs=...)` (green). If any site is in the wrong form (integer with pytest.approx or float with bare ==), fix that site first.
  - Suggested implementation: a custom Python script (e.g., `tools/lint_closed_form.py`) or a ruff plugin; gate invocation `uv run python tools/lint_closed_form.py tests/` exits 0 on all-green, 1 with file:line citations on any violation. Output MUST include per-site flag (`int → ==` vs `float → pytest.approx`).

- [ ] 8.2 Re-validate `openspec validate tighten-closed-form-eq-integer-checks --strict`. Confirm PASS with no "Unknown item" warnings. Result: see Implementation Complete (last command).

- [ ] 8.3 (If 8.1 and 8.2 PASS) Run `/opsx:archive tighten-closed-form-eq-integer-checks`. The archive will merge the new ADDED Requirement "Test Guard Precision for Closed-Form Numerical Claims" (binary-policy version) into `openspec/specs/wayfinder/spec.md` and move the change directory to `openspec/changes/archive/2026-09-07-tighten-closed-form-eq-integer-checks/`.