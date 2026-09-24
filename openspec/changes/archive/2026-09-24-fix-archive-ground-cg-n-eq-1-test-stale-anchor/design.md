# Design

## Context

See `proposal.md` Why for motivation. Current state of the defect being closed:

`openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/` was committed by `b842a53` (2026-09-16, `spec(opsx): archive ground-cg-n-eq-1-test post-apply no-op audit record`) and contains 5 files (`.openspec.yaml`, `proposal.md`, `design.md`, `tasks.md`, `specs/wayfinder/spec.md`). All 4 textual files reference the "CG n=1 boundary behavior" Requirement with anchor `req-34` — the historical state at apply-time (commit `b8c149c`, 2026-09-16) when live spec carried `<a id="req-34">` for that Requirement.

A later change `2026-09-16-fix-cg-n-1-test-anchor-collision-and-math-coverage` (commit `f16cb12`, 2026-09-16) **renumbered** the anchor by recognizing that `req-34` historically belonged to "Source Field Format Invariant for OpenSpec Specs" (which `f033d2e` 2026-09-15 had synced to live `wayfinder/spec.md` L659+ WITHOUT its anchor). The fix moved `<a id="req-34">` to L740 (Source Field Format Invariant position) and relabeled the CG n=1 boundary anchor to `<a id="req-35">` at L496. Live spec has carried this state ever since.

Post-archive drift closures by commit `889d81c` (2026-09-24, `fix(archive): post-archive drift closure — 10 surgical prose/test fixes`) patched one line of `archive/2026-09-16-ground-cg-n-eq-1-test/proposal.md` (line 19 in §Capabilities, "anchor renumbered in fix-cg-n-1-test-anchor-collision-and-math-coverage") but left 9 other stale `req-34` references in the folder untouched, including the spec delta file's `<a id="req-34">` anchor itself.

The 9 stale references compose as: `specs/wayfinder/spec.md:5` (anchor line) + `tasks.md:3,4` (2 instances) + `design.md:7,12,76,88` (4 instances) + `proposal.md:7,24` (2 instances, with `proposal.md:19` already updated to `req-35` by `889d81c`). Intra-document inconsistency is present in `proposal.md` (line 19 says `req-35`, lines 7+24 say `req-34`).

Constraints:
- **Archive immutability convention**: archive files are audit-trail records. Single-line textual edits are allowed for drift annotations (precedent: `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` was annotated by `fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` on 2026-09-24, archived same day). Deletion of archive folders or wholesale rewrite is NOT allowed.
- **`(historical, ...; superseded by ...)` canonical pattern**: per `wayfinder/tickets/A8-2.md` L70 + L74 and `governance/spec.md` req-gov-2 ("Ticket `(historical, ...)` supersede annotation pattern"), the cross-link annotation format is the audit-trail standard for DecompMoE. Reuse it for the archive annotation.
- **`lint_no_source_field_drift.py`**: per-capability reverse-link rule (introduced by `34b37be`); the archive spec delta's `**Source:**` field (line 10) is lint-clean (primary reverse-link `wayfinder/tickets/A8-2.md` per "first item MUST be per-capability primary ticket lineage"). The drift fix MUST NOT break this rule.
- **CLAUDE.md §6 第 8 条**: `<a id="req-N"></a>` MUST precede every Requirement (100% coverage). The drift relabel preserves this invariant — `<a id="req-35">` precedes "CG n=1 boundary behavior" Requirement in both live and archive spec delta after the fix.
- **CLAUDE.md §3 / §6 第 7-8**: wayfinder tickets are advisory non-binding; `wayfinder/tickets/A8-2.md` carries the Eight Metrics design lineage but does not require modification for this fix.

## Goals / Non-Goals

**Goals:**
- Relabel the anchor at `archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md` L5 from `<a id="req-34">` to `<a id="req-35">` to match live `openspec/specs/wayfinder/spec.md` L496 anchor for the same "CG n=1 boundary behavior" Requirement.
- Prepend a `(historical, ...; superseded by ...)` annotation block to the same archive spec delta file, mirroring the format from the precedent `archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` annotation. The annotation must record: (i) original anchor was `req-34` at L442 of live spec at archive apply-time (commit `b8c149c`), (ii) commit `f16cb12` reordered to `req-35` and moved `req-34` anchor to live L740 (Source Field Format Invariant Requirement), (iii) this archive corrective change (2026-09-24) edits anchor text to match post-reorder live spec.
- Update 8 prose references in `tasks.md` (L3, L4), `design.md` (L7, L12, L76, L88), `proposal.md` (L7, L24) to replace stale `req-34` with `req-35` when those references denote the "CG n=1 boundary behavior" Requirement. (`proposal.md` L19 already says `req-35`, preserved.)
- Ensure `python scripts/lint_no_source_field_drift.py` exit=0 post-change (archive is not in the live lint scan set, but re-run for hygiene confirmation).
- Ensure `openspec validate --specs` and `openspec validate --change fix-archive-ground-cg-n-eq-1-test-stale-anchor` both pass post-change.

**Non-Goals:**
- **Not** modifying `openspec/specs/wayfinder/spec.md` (already authoritative at L496 `<a id="req-35">`).
- **Not** modifying `openspec/changes/archive/2026-09-16-fix-cg-n-1-test-anchor-collision-and-math-coverage/` — that change is already archived and lint-clean; its actions are the supersession events recorded in our annotation block.
- **Not** modifying `wayfinder/tickets/A8-2.md` — tickets are advisory non-binding per `CLAUDE.md §8`. The Eight Metrics design lineage applies to Req 20 in live spec (already lint-compliant) and does not need a per-change audit-trail update.
- **Not** modifying any line-number references (e.g., `L442` in `design.md`, `tasks.md`, `proposal.md`) — those describe the apply-time state, NOT the anchor relabel. Updating line numbers would create a different kind of drift (anchors-only, not line-numbers) and is out of scope for this anchor-relabel change. (Line-number drift is a separate concern that would require git history archaeology; not in scope here.)
- **Not** modifying any `src/` code or `tests/` test — no production or test behavior change.
- **Not** modifying `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/.openspec.yaml` — it's the standard scaffold (`schema: spec-driven`, `created: 2026-09-24`); not part of the textual artifacts being edited.
- **Not** checking whether other archive folders in `openspec/changes/archive/` carry similar stale-anchor drift (e.g., the `req-21` / `req-16` / `req-33` gaps observed in live spec during this audit). Those would be separate changes if determined in scope; this change is scoped exclusively to `2026-09-16-ground-cg-n-eq-1-test/`.

## Decisions

### Decision 1: Surgical 4-file archive edit, no live spec delta, `skip_specs: true`

**Choice**: This change uses `skip_specs: true` (`.openspec.yaml`) and modifies 4 archive text files directly in the apply phase. No `specs/<capability>/spec.md` delta is created in the change directory.

**Rationale**: Per the OpenSpec spec-driven workflow rule "Use `skip_specs: true` only when no spec-level behavior changes (pure refactor, tooling, docs) — specs describe behavior, so if behavior does not change, no spec should change either. Do not invent a requirement just to satisfy validation.":
- The anchor relabel in archive spec delta does not change any Requirement semantics — the Requirement body (verbatim copy of live spec L498-518), 4 Scenarios, and lint-compliant `**Source:**` field remain identical. The `<a id="req-35">` anchor was the live spec state at the time of `f16cb12`; the archive was simply not re-synced.
- The 8 prose updates in archive `tasks.md` / `design.md` / `proposal.md` are descriptive references, not Requirements. They were SPECIFICALLY historical state-snapshots at archive-apply-time, and updating them only changes metadata (audit-trail clarity), not Requirements.

**Alternatives considered**:
- (a) Create a `specs/wayfinder/spec.md` delta in the change directory with `## MODIFIED Requirements` containing a relabeled `### Requirement: CG n=1 boundary behavior` block with the new anchor. **Rejected**: the apply phase would attempt to write the same body text that's already in live spec (anchor now matches live spec perfectly after our surgical edit); the delta would be a no-op MODIFIED against itself and confuse `openspec validate`.
- (b) Create a custom `## ARCHIVE_DRIFT_NOTE` section. **Rejected**: spec-driven schema enforces `ADDED` / `MODIFIED` / `REMOVED` / `RENAMED` headers; custom headers are not part of the schema. Annotation blocks live outside the delta.
- (c) Touch only the archive spec delta file's anchor, leave the 8 prose references stale. **Rejected** by user decision during scoping (2026-09-24 ask_user Q2 option A): the intra-doc inconsistency in `proposal.md` (line 19 vs lines 7+24) and the wide-spread prose drift would re-surface in future audit cycles.

### Decision 2: Annotation block format mirrors the ticket `(historical, ...)` supersede pattern

**Choice**: Use the `(historical, <original-state>; superseded by spec/change Decision N)` pattern adapted for an archive delta file context. Specific template:

```
<!-- archive corrective (2026-09-24): (historical, anchor was <a id="req-34"> at L442 of live wayfinder/spec.md
     when this change was archived by commit b842a53 on 2026-09-16; superseded by
     fix-cg-n-1-test-anchor-collision-and-math-coverage commit f16cb12 which
     relabeled CG n=1 boundary behavior's anchor to <a id="req-35"> and moved
     req-34 anchor to live L740 Source Field Format Invariant Requirement).
     This archive spec delta was edited to <a id="req-35"> for grep consistency
     with live spec; the original req-34 anchor identity is preserved in this
     annotation block. -->
```

The annotation block is placed at line 1 of the archive spec delta file (after any leading blank lines), before the existing `# wayfinder Specification (delta)` heading.

**Rationale**: Per `wayfinder/tickets/A8-2.md` L70 + L74 (existing ticket-side `(historical, <value>; superseded by spec req-N L###)` pattern) and `governance/spec.md` req-gov-2 ("Ticket `(historical, ...)` supersede annotation pattern — CLAUDE.md §3 source-field rules application"), the annotation format is the canonical cross-link annotation for DecompMoE. Reusing it for the archive delta keeps the audit-trail format consistent with ticket-side annotations. The annotation appears as an HTML-comment block (rather than bare prose) so it renders visibly in markdown viewers but does not affect `openspec validate` parsing (validate looks for `## ADDED Requirements` etc, not HTML comments).

**Alternatives considered**:
- (a) Use a free-form prose annotation. **Rejected**: the `(historical, ...)` pattern is recognized by `scripts/lint_no_source_field_drift.py` for ticket-side annotations and recorded in `governance/spec.md` req-gov-2 as the canonical format. Free-form would not benefit from grep-based audit-trail queries.
- (b) Use a YAML front-matter block. **Rejected**: the precedent uses inline annotations; YAML front-matter would conflict with future `openspec parse` schema considerations and adds metadata-parsing complexity that this single archive fix doesn't need.
- (c) Delete the archive spec delta file entirely. **Rejected**: archive files are immutable audit-trail records per OpenSpec convention; deleting would lose the historical record of the original `b8c149c` apply-time content. The annotation is the correct way to mark historical context.

### Decision 3: 4-file scope includes tasks.md / design.md / proposal.md prose, not just spec delta anchor

**Choice**: Update the 8 prose references across `tasks.md` (2), `design.md` (4), `proposal.md` (2) in addition to the 1 anchor-line edit in `specs/wayfinder/spec.md`. Total of 9 textual edits + 1 annotation prepend, all surgical.

**Rationale**: User decision during ask_user Q2 (2026-09-24, option A "全部 4 个文件 9 处一致化"). The justification beyond user preference: the `proposal.md` already exhibits intra-doc inconsistency (line 19 says `req-35` from `889d81c`, lines 7+24 still say `req-34`). Any future audit cycle grepping "what does this archive say about CG n=1's anchor?" will get mixed results; same applies for `tasks.md` (which has 2 instances) and `design.md` (4 instances). Closes the drift in one pass.

**Alternatives considered**:
- (a) Surgical 1-file-only fix (just the anchor in spec delta, no prose updates). **Rejected** by user decision and by audit trail symmetry: 9 instances of "CG n=1 boundary behavior" + `req-34` in the same folder would still match in grep, perpetuating drift.
- (b) 4-file scope but only edit anchor/numbers, do not prepend annotation block. **Rejected**: without an annotation block recording the original anchor was `req-34` at apply-time, future readers would have no audit trail explaining why the archive's anchor differs from what `b8c149c` apply was supposed to leave. The annotation block is the documentation.

### Decision 4: Post-review scope expansion — address MINOR-1 and INFO-1 from Python reviewer

**Choice**: Expand change scope post-review to address the 2 findings raised by the Python reviewer agent (`agent-b1a39f2827bf`):
- **MINOR-1** (1 file edit): rewrite misleading comment at `tests/test_metrics.py:350-364`. The comment falsely claims the bare `==` assertion "pins the implementation path: any rewrite to sum/max identity would break here"; empirically at numel==1 L2/abs(sum)/abs(max) all coincidentally return `abs(value)`, so the assertion evaluates to `5.0 == 5.0` regardless of implementation. Fix: rewrite comment to acknowledge numel==1 coincidence + reference `test_cg_l2_norm_closed_form` (req-20 sibling test) as the actual L2-vs-other-norms discriminator at numel≥2 (`CG([3,4])==5.0` is uniquely L2). Keep the bare `==` assertion itself — it remains a FP-exact documentation claim and would catch numerical regressions.
- **INFO-1** (1 file edit, 5 assertion lines): tighten `pytest.approx(abs=1e-12)` to `pytest.approx(abs=1e-15)` for the 5 boundary assertions at `tests/test_metrics.py` L327, L332, L337, L344, L348. Reviewer noted `sqrt(x²)` is bitwise-exact in IEEE-754 binary64 for `|value| ≤ 2^26` (verified `math.sqrt(25.0) == 5.0` bit-equal), so `abs=1e-15` is achievable.

**Rationale**: User explicit directive at 2026-09-24 23:21: "修复本change内所有findings". Both findings were classified by reviewer as "out-of-scope for this change" (MINOR-1 since `tests/test_metrics.py` was not in the originally declared 4 archive files; INFO-1 as "conservative and safe", "Optional future-cycle cleanup") but the user overrides the out-of-scope callouts. CLAUDE.md §3 "Surgical Changes" caveat ("Touch only what you must") is overridable by explicit user decision per the precedent of multiple past archive corrective changes (`fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` task 6 prioritized precision over scope).

**Alternatives considered**:
- (a) Skip both findings per reviewer's out-of-scope disclaimer. **Rejected** by user directive.
- (b) Expand scope to also tighten `abs=1e-12` → `abs=1e-15` in archive spec.md body 4 Scenarios + live spec.md 4 Scenarios for spec/test consistency. **Rejected**: would diverge archive from live spec body until a separate change updates live; the verbatim-equivalence invariant established by this change is more valuable than the cosmetic precision tightening, and a future `tighten-cg-n1-fp-precision` change can update both simultaneously.
- (c) Expand scope to live spec.md to maintain lock-step precision tightening. **Rejected**: live spec.md edits would create new drift trail requiring explanatory annotation; the surgical reduction (test-only tightening) is cleaner. **Documented Future Work**: a follow-up change should tighten both live and archive spec body + test to `abs=1e-15` simultaneously.

**Scope boundary** for INFO-1: ONLY the 5 assertions in `test_cg_n_eq_1_returns_magnitude` (out of 12 total `abs=1e-12` instances in `tests/test_metrics.py`). Other tests' tolerance choices (e.g., MCI tests at L103-262, `test_cg_zero_grad_exact_zero` at L273-275 / L304, `test_safe_apply_cache_matches_runtime` at L461) are unrelated to the reviewer's finding and remain out of scope.

## Risks / Trade-offs

- **[R1] Annotation block content may diverge from the precedent** → **Mitigation**: copy the annotation block structure verbatim from `archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` (line 1-10 region) and adapt only the substantive content. Verify by reading both annotation blocks side-by-side after writing.
- **[R2] Line-number references (L442, L676) become increasingly stale** → **Mitigation**: out of scope per Decision 1 / non-goals. Captured as separate concern; future cycles may audit `git blame` of each archive line for accurate line-number provenance.
- **[R3] Edit tool on Windows may introduce CRLF in non-ASCII content** → **Mitigation**: per CLAUDE.md hygiene lesson (2026-09-23), every modified file gets a byte-level CRLF check: `python -c "import sys; data=open(sys.argv[1],'rb').read(); print(data.count(b'\\r\\n'))" <file>` returns `0`. If non-zero, run strip-CRLF PowerShell snippet before commit.
- **[R4] Multiple `### Requirement: <title>` columns across the 4 files become drift-prone again if a later change alters the live spec** → **Mitigation**: out of scope to design a permanent sync mechanism here. Documented as a known limitation; future archive-corrective changes would handle recurring drifts.
- **[R5] `openspec validate --change` may reject if spec delta body doesn't exactly match live spec** → **Mitigation**: the archive spec delta body is verbatim from live `openspec/specs/wayfinder/spec.md` L498-518 (per `b8c149c` apply state). Since this change runs in `skip_specs: true` mode and has NO `specs/<capability>/spec.md` delta, `openspec validate --change` validates only proposal + design + tasks (not the archive spec delta body directly). Confirm by running validation post-write.

## Migration Plan

Single-pass apply via Edit tool on 4 archive text files (no shell script, no live-spec edits, no archive-folder creation/deletion). The 4 files are all under `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/`. After apply, run lint + validate hygiene checks.

**Rollback** (if lint/validate fails post-apply): `git checkout HEAD -- openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/` to restore pre-apply state. Archive folder contents are git-tracked, so a clean rollback exists.

## Open Questions

(none — all decisions resolved via ask_user 2026-09-24)
