## Context

`archive/2026-09-06-tighten-test-precision-tolerance` was a 4-LOW-severity audit-driven change. It deliberately left `tests/test_config.py::test_flops_total_exact_134217728` (L86) out of scope per its `Decision 4` ("to keep the change scope bounded per `CLAUDE.md` §3 'Touch only what you must'"), and explicitly acknowledged the resulting `CLAUDE.md` §6 第 8 条 violation as future work. Change `tighten-closed-form-eq-integer-checks` is that follow-up.

A second audit pass (清单 2 P2, 2026-09-07) found two more sites in the same violation pattern outside the original 2026-09-06 audit envelope:
- `tests/test_extraction.py:103` (`assert expected == 33_040` for per-head extraction MACs)
- `tests/test_experts.py:100` (`assert total == 100_663_296` for `N_e·3·d_model·d_ffn`)

Together with L86 (already flagged by 2026-09-06 Decision 4 as future work), all 3 sites share the identical violation: raw `==` integer comparison against a spec-anchored closed-form integer claim, where `pytest.approx(value, abs=0)` would express the same mathematical check (verified equivalent per `archive/2026-09-06 design.md Decision 1` rationale) but conform to `CLAUDE.md` §6 第 8 条's `pytest.approx(..., abs=...)` mandate.

The conversion is mechanical (no algorithmic change to production code, no test logic change beyond the assertion form); the only design-level decisions are about scope (which sites) and message form (whether to normalize `f"actual={...}"` per CLAUDE.md §3 alongside the assertion form change).

## Goals / Non-Goals

**Goals:**
- Convert 3 raw `== <int literal>` integer assertions to `pytest.approx(<int literal>, abs=0)`:
  - `tests/test_config.py:86` — `flops_per_token(cfg, "MOE") == 134_217_728` → `pytest.approx(134_217_728, abs=0)`
  - `tests/test_extraction.py:103` — `expected == 33_040` → `pytest.approx(33_040, abs=0)`
  - `tests/test_experts.py:100` — `total == 100_663_296` → `pytest.approx(100_663_296, abs=0)`
- Normalize the failure message convention to `f"actual={...}"` per `CLAUDE.md` §3 across the 3 sites (consistent with `archive/2026-09-06 design.md Decision 3` for LOW-1/LOW-2 integer assertions).
- Verify all 3 changes pass `uv run pytest tests/test_config.py::test_flops_total_exact_134217728 tests/test_extraction.py::test_per_head_mac_count tests/test_experts.py::test_expert_pool_param_count -v` AND full regression `uv run pytest tests/ -v` returns the same pass count as pre-change baseline.
- Confirm `git diff --stat` shows exactly 3 files changed, 1 insertion + 1 deletion per file (surgical single-line edit per site, no CRLF conversion per [[windows-edit-crlf-pitfall]]).

**Non-Goals:**
- Not touching the LOW-1/LOW-2 sites (L64, L65, L67, L80, L81) — already tightened in `archive/2026-09-06-tighten-test-precision-tolerance`; would re-tighten what is already tight.
- Not touching the LOW-3/LOW-4 bisection sites (L90, L91, L141, L148) — already tightened to `abs=1e-6` in `archive/2026-09-06-tighten-test-precision-tolerance`; out of audit envelope.
- Not touching `tests/test_config.py:83` (`flops_actual == cfg.L * per_layer` — structural identity, not numeric constant pinning).
- Not touching `tests/test_extraction.py:122` (`m2 == 2 * m1` — d_c-scaling property, not closed-form constant pinning).
- Not touching `tests/test_experts.py:99` (`expected = cfg.N_e * 3 * cfg.d_model * cfg.d_ffn` — assignment, not assertion).
- Not changing production arithmetic in `src/decompmoe/config.py`, `src/decompmoe/extraction.py`, or `src/decompmoe/experts.py` — this is a test-side convention change only.
- Not opening a follow-up audit for other pre-existing `==` integer checks across the test suite (e.g., `tests/test_loss.py` already uses `pytest.approx`; any remaining `==` integer sites in `tests/test_safeguards.py`, `tests/test_metrics.py`, etc., are out of scope until a future audit enumerates them).
- Not modifying wayfinder tickets (CLAUDE.md §6 第 7 + §8 — tickets are reference-only).

## Decisions

### Decision 1: Close the 3 OUT-OF-SCOPE carve-outs from `archive/2026-09-06 design.md Decision 4`

**Choice**: Restore full `CLAUDE.md` §6 第 8 条 compliance for integer closed-form by tightening 3 specific sites (L86 in `test_config.py`, L103 in `test_extraction.py`, L100 in `test_experts.py`).

**Rationale**: The 2026-09-06 change was correctly bounded at the time (low-severity audit findings ×4, surgical scope per `CLAUDE.md` §3). It also correctly **acknowledged** the resulting `CLAUDE.md` §6 第 8 条 tension (its `design.md` Decision 4 L84 is explicit: "this decision is in tension with `CLAUDE.md` §6 第 8 条 acknowledged ... A future change should be opened to systematically tighten all remaining `==` integer checks across `tests/test_config.py`"). This follow-up change **is** that future change, scoped to the 3 sites surfaced by the second audit pass. The closure is justified now because:
1. The conversion `== X` → `pytest.approx(X, abs=0)` is mathematically equivalent for integers (verified in `archive/2026-09-06 design.md Decision 1`) — zero risk of test-meaning change.
2. `CLAUDE.md` §6 第 8 条 explicitly mandates `pytest.approx(..., abs=...)` for every spec-anchored closed-form numerical claim; the 3 sites all pin spec-anchored integer constants (`134_217_728 = 4 × per_layer_MoE_FLOPs`, `33_040 = macs(8, 128, 16)`, `100_663_296 = N_e·3·d_model·d_ffn`).
3. `archive/2026-09-06 design.md Decision 4` L84 records the future-work intent verbatim: "A future change should be opened to systematically tighten all remaining `==` integer checks across `tests/test_config.py` (and other test modules) for full §6 第 8 条 compliance — this is recorded as `tasks.md` §4.1 follow-up."

**Alternatives considered**:
- (a) Leave the 3 sites as raw `==` — rejected: violates `CLAUDE.md` §6 第 8 条; the carve-out was always explicit future work, not permanent.
- (b) Bundle the 3-site tightening into a follow-up `archive/2026-09-06-tighten-test-precision-tolerance` apply cycle — rejected: that change is already archived; mixing future work into an archived change would muddy the audit trail and violate the "one change, one scope" OpenSpec convention.
- (c) Open a broader sweep auditing all remaining `==` integer checks across `tests/` — rejected for this change (would expand scope beyond the 3 audit-named sites, violating `CLAUDE.md` §3 "Touch only what you must"); recorded as open question below for a future dedicated audit change.

### Decision 2: Use `abs=0` (not `abs=1e-9` or wider) for the 3 sites

**Choice**: `pytest.approx(<int_literal>, abs=0)`.

**Rationale**: Inherited from `archive/2026-09-06 design.md Decision 1`. The 3 constants are exact integer products (`134_217_728 = 4 × 33_554_432`, `33_040 = macs(8, 128, 16)`, `100_663_296 = 16 × 3 × 1024 × 2048`); no floating-point arithmetic is involved. `abs=0` is mathematically equivalent to `==` for `int == int` comparisons (verified empirically in `archive/2026-09-06 design.md Decision 1`) and expresses the "spec says this exact value" contract most precisely. `abs=1e-9` would be needlessly loose; `rel=...` would over-engineer (closed-form integer claims don't need relative tolerance).

**Alternatives considered**:
- (a) `==` — rejected: violates `CLAUDE.md` §6 第 8 条.
- (b) `abs=1` — too loose, accepts wrong answers (any integer within ±1 of the spec value would pass).
- (c) `abs=1e-9` — too loose, masks FP rounding bugs that don't apply here (the constants are integer products).

### Decision 3: Normalize failure message to `f"actual={...}"` for the 3 sites

**Choice**: Each of the 3 assertions embeds `f"actual={...}"` (or for L103, replace the existing `f"closed form must equal 33_040; got {expected}"` with `f"actual={expected}"` to match the canonical form).

**Rationale**: `CLAUDE.md` §3 establishes `f"actual={...}"` as the standing convention. `archive/2026-09-06 design.md Decision 3` justified this for LOW-1/LOW-2 integer assertions: "`pytest.approx(int_value, abs=0)` failures on `int` vs `float` mismatches benefit most from an explicit `actual=` marker (otherwise pytest's diff shows `<class 'float'> 452329984.0 != 452329984`, which is harder to grep than `actual=452329984.0`)." The same reasoning applies to L86/L103/L100 — they are integer assertions where `f"actual={...}"` is most useful for debugging.

**Alternatives considered**:
- (a) Leave existing failure message form (`f"actual={flops_actual}"` at L86 — already conforms; `f"closed form must equal 33_040; got {expected}"` at L103 — does not conform; nothing at L100 — does not conform) — rejected for L103 and L100; partial uniformity is harder to grep than full uniformity.
- (b) Replace `assert` with `pytest.fail(f"actual={...}")` — rejected: loses pytest's auto-diff; over-engineered.

### Decision 4: Implementation scope drift acknowledgment (added 2026-09-07 via `/opsx:update` after post-apply audit)

**Choice**: Acknowledge that commit `19d901e` tightened **3 of the 3 named Goals sites** (proposal.md Goals L17-19) but **missed `tests/test_config.py:94`** — the **core carve-out site** (`test_flops_total_exact_134217728` L94 with `assert config.flops_per_token(config.MVPConfig(), "MOE") == 134_217_728`). A 4th site (the carve-out close) was **added by §5 follow-up tasks** (commit `ae14868`) to complete the change's stated purpose ("closes archive/2026-09-06 design.md Decision 4 carve-out"). Defer related audit findings (LOW-2 L87, docstring L57-58 hygiene) to a new `tasks.md` §5 follow-up section, to be addressed by a future `/opsx:apply` invocation (either re-applying this change or in a dedicated follow-up change).

**Rationale**: Post-apply `code-review max` audit 2026-09-07 surfaced 8 findings. Verification confirmed (via `git diff 5416f93 19d901e -- tests/test_config.py` showing diff anchor `@@ -86,7 +86,7 @@ def test_flops_per_layer_exact_33554432`) that the tightened L86 sits **inside `test_flops_per_layer_exact_33554432`** (the LOW-2 site that was already tightened by `archive/2026-09-06-tighten-test-precision-tolerance`), **not** inside `test_flops_total_exact_134217728` (the archive/2026-09-06 Decision 4 carve-out core target). The constant `134_217_728` appears in both functions:
- `test_flops_per_layer_exact_33554432` L86 (now L89 post-§5 commits, since L87 was also tightened by `ae14868`): `assert flops_actual == 134_217_728, f"actual={flops_actual}"` — `flops_actual = config.flops_per_token(cfg, "MOE")` (cfg from L78)
- `test_flops_total_exact_134217728` L94 (originally targeted carve-out, closed by `ae14868`): `assert config.flops_per_token(config.MVPConfig(), "MOE") == 134_217_728` — fresh `MVPConfig()` instance, same constant

This is a **scope drift between proposal intent and actual git diff** — caused by line-number confusion during Edit (the Edit tool's `old_string` matched the LOW-2 L86 in `test_flops_per_layer_exact_33554432` because it precedes the carve-out L94 in the file, but the change's stated purpose — "closes archive/2026-09-06 design.md Decision 4 carve-out" — explicitly targets the carve-out L94, not the LOW-2 L86). The carve-out **remained open** after `19d901e` landed; the §5 follow-up commit `ae14868` closes it.

**Mitigation**:
1. `proposal.md` What Changes now explicitly says "partially closes the Decision 4 carve-out" (no longer over-claims "closes").
2. `tasks.md` §5 (added by this revision) lists 6 unchecked follow-up tasks: §5.1 L94 tighten (HIGH); §5.2 L87 tighten (MEDIUM); §5.3 docstring L57-58 align (LOW); §5.4 pytest verify; §5.5 git diff verify; §5.6 commit.
3. Future `/opsx:apply` on this change will walk through §5 tasks and land a second commit (`19d901e+1` = `ae14868`) on `dev` HEAD that completes the carve-out. **Status**: `ae14868` landed 2026-09-07, closing L94 + L87 + docstring hygiene; `tasks.md` §5 now shows all 6 follow-ups `[x]`.
4. The 2 out-of-scope findings (#3 L83 structural identity, #8 L88 cosmetic comment style) are explicitly **not** in this change per `CLAUDE.md` §3 "Touch only what you must"; they remain pre-existing artifacts to be addressed by a future dedicated audit change.

**Alternatives considered**:
- (a) Open a new follow-up OpenSpec change (`opsx:propose audit-followup-...`) for L94 + L87 — rejected for this update: keeps the carve-out's lifecycle atomic in one change (the carve-out was opened in `archive/2026-09-06` and should be closed in this same change's lineage); a follow-up change would muddy the audit trail. The §5 tasks path preserves this lineage.
- (b) Reset `19d901e` and re-implement from scratch — rejected: violates `CLAUDE.md` §4 "git history preservation"; the partial tightening in `19d901e` (LOW-2 L86, test_extraction L103, test_experts L100) is valid progress and should not be undone.

### Decision 4 Addendum: Principle-level audit findings (added 2026-09-07 via second `/opsx:update` after post-apply audit #2)

**Choice**: Acknowledge two additional **principle-level** findings (Finding #6 + Finding #13) as **out-of-scope for this change** but **in-scope for future follow-up changes**, and capture them explicitly so they don't get silently lost when this change is archived.

**Findings deferred to follow-up**:

1. **Finding #6** (`tests/test_extraction.py:104` tautology): `assert expected == pytest.approx(33_040, abs=0)` only verifies the test's own `macs()` helper formula matches `33_040`, **not** that `extract_C`'s actual implementation incurs 33_040 MACs. The spec claim "33_040 MACs per extract_C" (Requirement 17) is **decoupled** from the production code — if `extract_C` is refactored to add operations (e.g., double einsum), the test still passes. This violates `CLAUDE.md` §6 第 8 条's **spirit** ("directly verify the math", "算式必须直接对账" — formalized in §6 第 8 条's preamble against "文字断言不构成可验条款") even though the assertion form `pytest.approx(..., abs=0)` is technically compliant. **Mitigation requires architectural work**: add MAC-counting instrumentation (e.g., `torch.profiler` hooks or instrumented einsum counting) — out of scope for this surgical test-only change per `CLAUDE.md` §3 "Touch only what you must". Tracked in tasks.md §6.3 (acknowledgment only; no code change required for this change).

2. **Finding #13** (`tests/test_extraction.py:98` hardcoded literals): `cfg_hkv, cfg_dk, cfg_dc = 8, 128, 16` duplicates `MVPConfig.H_kv`, `MVPConfig.d_k`, `MVPConfig.d_c` as Python literals. If MVPConfig changes (e.g., `H_kv` updated to 16 for GQA), the test silently continues to use `8` and verifies the wrong MAC count. Single-source-of-truth violation. Tracked in tasks.md §6.2 for code-level fix.

**Rationale**: This change's purpose is to formalize §6 第 8 条's "raw `==` MUST NOT appear" obligation and tighten **form compliance** across the 3 (now 4 with carve-out) named integer closed-form sites. Principle-level compliance (where the spec claim must be **causally connected** to the production code via instrumented measurement, not just structural identity with a helper function) is a deeper architectural question that requires decisions about profiling infrastructure, test fixture design, and MAC-counting methodology. Bundling these into this change would expand scope beyond `CLAUDE.md` §3 "Touch only what you must" and risk re-opening the entire test architecture (which has just been stabilized by `1601c87` F3+F4 refactors).

**Alternatives considered**:
- (a) Bundle Finding #6 + #13 into this change via expanded scope — rejected: violates `CLAUDE.md` §3; Finding #6 requires architectural work beyond test edits, and Finding #13 (while small) is best handled alongside any future `extract_C` test refactor that switches to `MVPConfig`-based fixtures.
- (b) Mark both as `won't fix` — rejected: they are real principle violations that future audit (e.g., `audit-integer-eq-violations` open question in Decision 4 Open Questions) would re-surface; explicit tracking prevents silent loss.
- (c) Open a new follow-up OpenSpec change `audit-extract-c-mac-count` for Finding #6 — deferred: the user's choice in this session was to keep the carve-out lifecycle atomic in this change (per Decision 4 alternative (a)); a future dedicated change can be opened when the user prioritizes Finding #6 work.

## Risks / Trade-offs

- **[Risk]** A future production-code refactor of `flops_per_token` or `extraction.extract_C` or `experts.ExpertPool` returns `float` instead of `int` (e.g., via `(... + ...) / 1.0` — a common FP-coercion anti-pattern). → `pytest.approx(value, abs=0)` correctly catches this with a clear `actual=452329984.0 != 452329984 (abs=0)` failure message, whereas raw `==` would either fail with a generic assertion error or coerce silently. This is the intended guard, not a bug.
- **[Risk]** `pytest.approx(int_value, abs=0)` raises `TypeError` if a non-numeric is passed (e.g., `None`). → Same risk as `==`; desirable behavior in both cases (catches broken `compute_*` implementations early).
- **[Risk]** Other pre-existing `==` integer checks exist across `tests/` outside the 3 audit-named sites (e.g., `tests/test_safeguards.py`, `tests/test_metrics.py` may have similar violations). → Out of scope per `CLAUDE.md` §3 "Touch only what you must"; recorded as Open Question for a future dedicated audit change.
- **[Risk]** Windows Edit tool CRLF conversion ([[windows-edit-crlf-pitfall]]) could expand the diff from `3 files, 3 insertions, 3 deletions` to `3 files, 100+ lines changed`. → Mitigation: tasks.md §5 mandates `git diff --stat` verification before reporting completion; `sed -i 's/\r$//' <file>` if needed.
- **[Risk]** Test failure regression: if the production arithmetic has actually drifted (e.g., `flops_per_token` returns `134_217_728.0` instead of `134_217_728`), the conversion to `pytest.approx(..., abs=0)` would now fail with a clear `actual=134217728.0 != 134217728 (abs=0)` message where the old `==` silently coerced. → This would be a **useful signal** of a real production-code regression, not a false positive; the user would see it on the first test run and decide whether to widen to `abs=1e-6` (the natural relaxation point per `archive/2026-09-06 design.md Decision 1`) or fix the production code.

## Migration Plan

N/A — no deployment, no rollback, no migration. This is a 3-file, 3-line surgical test-only change. The "migration" is the atomic commit: `git add tests/test_config.py tests/test_extraction.py tests/test_experts.py && git commit -m "test(precision): tighten 3 closed-form == to pytest.approx(..., abs=0)"` on `dev` branch.

## Open Questions

- **Future audit**: Should a follow-up audit change be opened to enumerate and tighten all remaining pre-existing `==` integer checks across `tests/` (e.g., `tests/test_safeguards.py`, `tests/test_metrics.py`)? This change explicitly does NOT enumerate them; the second audit pass found the 3 sites named in proposal, but a broader sweep is out of scope. A future dedicated `audit-integer-eq-violations` change could enumerate all `tests/**/test_*.py` for `== <int literal>` patterns matching `0|<digits>(_<digits>)*` against closed-form spec constants and propose per-site tightening.
- **Future enhancement**: Should `pytest.approx(..., abs=0)` integer sites be further hardened by also asserting `isinstance(actual, int)` to catch the `int → float` silent-coercion risk at the assertion layer (rather than relying on `abs=0` to fail with a clear message)? Not needed now (the `abs=0` message is sufficient per `archive/2026-09-06 design.md Decision 1`); deferred until a real refactor regression surfaces.