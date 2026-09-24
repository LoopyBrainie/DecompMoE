# Proposal

## Why

`openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` L12 claims: "The new `Test Guard Precision for Closed-Form Numerical Claims` Requirement **(Req 32)** added to `wayfinder` is new test-side policy text — it does NOT modify the Req 11 closed-form values themselves." That claim is wrong on two counts:

1. **Live spec Req 32 is already occupied**. `openspec/specs/wayfinder/spec.md` L702 carries `<a id="req-32">` → `### Requirement: Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper` (introduced by `fix-spec-resurrection-math-direction` archived at `archive/2026-09-12-fix-spec-resurrection-math-direction-2026-09-12/`). Adding a new Req 32 to wayfinder would create an `<a id="req-32">` anchor collision — the lint invariant `CLAUDE.md §6 第 8 条 "spec anchor 不全"` forbids duplicate anchors.
2. **The actual delta was anchored at req-33, not req-32**. The original apply commit `6f22278` (2026-09-08, "archive: tighten-closed-form-eq-integer-checks — **req-33** Test Guard Precision appended to main spec") and its delta file `<a id="req-33"></a>` were the real anchor; L12's "(Req 32)" was a writing error in the `e437c2d` archive commit (2026-09-17) that persisted through `889d81c` post-archive drift closure (which fixed the rad literal but preserved the wrong number).

Furthermore, the requirement has since migrated: commit `34b37be` (2026-09-12, "archive: migrate-l678-source — split L678 governance into governance capability + atomic gate wiring") moved the Requirement body from `wayfinder/spec.md` `<a id="req-33">` to the new `governance/spec.md` as `<a id="req-gov-1">`, and commit `24118d6` (2026-09-24, "fix(spec,archive): req-33 orphan anchor cleanup + 2026-09-06 archive lineage annotation") closed the now-orphan `<a id="req-33">` in wayfinder. So the canonical home today is `governance/spec.md` `req-gov-1`, not wayfinder Req 32 or Req 33.

This change closes the prose drift in `archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` and the spec-delta file's prepended annotation block — both with surgical edits, mirroring the documented precedent set by `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/` (closed by the active change `fix-archive-ground-cg-n-eq-1-test-stale-anchor` on 2026-09-24). No live spec change, no Requirement semantics change, no code change, no test change.

## What Changes

This is a **narrow 2-line prose fix in one archive file** — verified by cross-check across all 4 archive text files:

- **`archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` L12**: replace the inaccurate "(Req 32) added to `wayfinder`" phrasing with an acknowledgment that the canonical anchor migrated: `Requirement (originally added to wayfinder as req-33 in commit 6f22278; superseded by governance/req-gov-1 via commit 34b37be migrate-l678-source)` — preserves the L12 paragraph's other intent (test-side policy text, no Req 11 modification) and adds one inline historical supersede parenthetical. The `(Req 32)` writing error is corrected; the L12 number anchor is replaced with a substantive lineage note.

- **`archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` L22** (`### Modified Capabilities`): replace the description "adds Requirement `Test Guard Precision for Closed-Form Numerical Claims` (3 Scenarios) to the `wayfinder` capability" with the lineage-correct description: "(historical: added to wayfinder as req-33 by commit 6f22278; current authoritative home is `governance/spec.md` `req-gov-1` after migration in commit 34b37be; orphan req-33 anchor in wayfinder cleaned up by 24118d6)". The `(3 Scenarios)` claim is preserved (matches the actual delta body, which carried 3 Scenarios). The destination capability is corrected from `wayfinder` → `governance`.

- **`archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` Impact section**: add a reverse-link bullet `\`openspec/specs/governance/spec.md\` \`req-gov-1\` (Test Guard Precision for Closed-Form Numerical Claims — current authoritative home, migrated from wayfinder/req-33 by commit 34b37be)` so future audit cycles grepping for the Requirement's lineage land on the proposal's reverse-link without depending on the annotation block in `specs/wayfinder/spec.md`.

**Cross-check results** (verified via `grep -nE 'Req 32|req-32|req-33|Test Guard Precision|added to .wayfinder' openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/` on 2026-09-24):

- `archive/2026-09-06-tighten-test-precision-tolerance/design.md` L84 and L104 reference the new `Test Guard Precision for Closed-Form Numerical Claims` requirement generically (e.g. "the new requirement applies prospectively") but do NOT claim `Req 32` or `added to wayfinder`. **No edit needed.**
- `archive/2026-09-06-tighten-test-precision-tolerance/tasks.md` does NOT reference the new requirement's anchor at all; tasks describe test-side edits only (`tests/test_config.py`, `tests/test_sphere.py`). **No edit needed.**
- `archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` L1-16 already carries the comprehensive 3-section HTML-comment annotation block added by commit `24118d6` (2026-09-24, "fix(spec,archive): req-33 orphan anchor cleanup + 2026-09-06 archive lineage annotation") — records (i) "original proposal superseded; req-33 finally landed as governance/req-gov-1 via migrate-l678-source commit 34b37be", (ii) the integer/binary exemption reversal via `bec147d + 83a0503`, (iii) the canonical landing via `6f22278 + 34b37be`. **No edit needed** — that file is the deliverable of a separate change (`fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian`), not this change's scope.

No source-code changes. No test changes. No ticket changes (per `CLAUDE.md §8` "wayfinder tickets are advisory non-binding"). No change to live `openspec/specs/wayfinder/spec.md` (already authoritative at `<a id="req-32">` L702 Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper, and `<a id="req-33">` does not exist post-24118d6 cleanup). No change to live `openspec/specs/governance/spec.md` (already authoritative at `<a id="req-gov-1">` L9 Test Guard Precision for Closed-Form Numerical Claims).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none — see `skip_specs: true` rationale in `.openspec.yaml`)

### `skip_specs` rationale

This change is **pure archive-prose hygiene** with **no observable behavior change**:

- The 3 surgical edits in `archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` (L12 + L22) are **descriptive references** to a Requirement that already lives canonically at `governance/spec.md` `req-gov-1`. Updating them is prose accuracy, not Requirement text modification. The Requirement body, 3 Scenarios, and lint-compliant `**Source:**` field in the archive spec delta file are preserved unchanged.
- The prepended annotation block on `archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` mirrors the precedent from `archive/2026-09-16-ground-cg-n-eq-1-test/specs/wayfinder/spec.md` L1-L16 (added by `fix-wayfinder-spec-req-33-orphan-anchor-and-archive-historian` 2026-09-24) — an HTML-comment block that records (i) original claim was wrong, (ii) what actually happened via 6f22278, (iii) where the canonical home is today. The annotation does not modify any Requirement body, anchor, scenario, or `**Source:**` field.

Per the OpenSpec spec-driven workflow rule "Use `skip_specs: true` only when no spec-level behavior changes (pure refactor, tooling, docs) — specs describe behavior, so if behavior does not change, no spec should change either. Do not invent a requirement just to satisfy validation.", this change sets `skip_specs: true`. The `apply` phase directly edits the 2-3 archive text files without producing a `specs/<capability>/spec.md` delta.

## Impact

- **Affected files** (all under `openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/`):
  - `proposal.md` (L12 + L22 wording corrections + Impact reverse-link to `governance/spec.md req-gov-1`)
  - `specs/wayfinder/spec.md` (~15-20 line HTML-comment annotation block prepended, before `## ADDED Requirements` header)
  - `design.md` and `tasks.md` (conditional, only if stale references to "Req 32 / added to wayfinder / Test Guard Precision" are found in initial cross-check)

- **Affected code/APIs/dependencies**: none.

- **Lint**: `python scripts/lint_no_source_field_drift.py` exit=0 (no governance reverse-link violation; archive files are not in the live lint scan set, but re-run for hygiene confirmation).

- **OpenSpec validate**: `openspec validate --specs` and `openspec validate --change fix-archive-tighten-test-precision-tolerance-req-claim-drift` both pass post-change.

- **Downstream grep**: after this change, `grep -nE 'Req 32|req-32' openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/proposal.md` returns 0 hits for "(Req 32) added to wayfinder" prose (was previously 1 hit at L12 with incorrect claim); `grep -nE 'governance/req-gov-1' openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/*.md` returns ≥2 hits (L12 + L22 lineage note + Impact reverse-link) for traceability. `grep -n '<!--' openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` returns 1 hit (the new annotation block opener) — matches precedent format from `archive/2026-09-06-tighten-test-precision-tolerance/specs/wayfinder/spec.md` L1.

- **Audit trail**: future cycles can `grep -nE 'governance/req-gov-1|req-33|6f22278|34b37be|24118d6' openspec/changes/archive/2026-09-06-tighten-test-precision-tolerance/` and reconstruct the full lineage: 6f22278 (req-33 original) → 34b37be (migrated to governance/req-gov-1) → 24118d6 (orphan cleanup) → this change (prose correction in archive). The mis-claim "(Req 32) added to wayfinder" is replaced with the canonical-ground-truth lineage, eliminating a category of future-audit confusion where the archived proposal would have suggested an anchor that never existed in live spec.

- **Source**: commit `e437c2d` (2026-09-17, "spec(opsx): archive tighten-test-precision-tolerance") — body already notes "delta for the original **req-33**; current authoritative home is governance/req-gov-1 (migrated by commits bec147d + 83a0503 and the later migrate-l678-source archive)", confirming the commit author's awareness that "(Req 32)" was a writing error. `889d81c` (2026-09-24) post-archive drift closure preserved the writing error while fixing related prose. Precedent: `openspec/changes/archive/2026-09-16-ground-cg-n-eq-1-test/` (closed by active change `fix-archive-ground-cg-n-eq-1-test-stale-anchor`).