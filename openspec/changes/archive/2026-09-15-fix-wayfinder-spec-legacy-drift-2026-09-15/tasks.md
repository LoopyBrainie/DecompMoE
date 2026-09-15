## 1. Spec Edits (apply wording fixes to `wayfinder/spec.md`)

- [x] 1.1 Replace `+ ε` normalization formula in Req 5 (L64) steps (2) and (4) with `max(‖·‖₂, ε)` and verify by `grep -n "max(||z" openspec/specs/wayfinder/spec.md` returning exactly the two step occurrences (steps (2) and (4)); verify `grep -n "||z|| + ε" openspec/specs/wayfinder/spec.md` returns zero matches
- [x] 1.2 Replace `activations per routed token` with `active parameters per routed token (Mixtral-style active-parameter accounting; aligned with Req 10 guarantee (3))` in Req 9 (L158) and verify by `grep -n "active parameters per routed token" openspec/specs/wayfinder/spec.md` returning exactly one match in Req 9; verify `grep -n "activations per routed token" openspec/specs/wayfinder/spec.md` returns zero matches
- [x] 1.3 Add inline glossary for `WB` in Req 15 (L293) Layer 2 advisory signals: insert ` (where \`WB = 0.0476\` is the natural baseline of the soft orthogonality loss, defined in \`wayfinder/tickets/A6b-2.md\` L52 and L89–L92 as the per-expert orthogonality baseline that the advisory ratio normalizes against; a ratio \`> 2.0\` indicates severe centroid clustering / territory overlap)` immediately after `L_sep / WB`, and verify by reading Req 15 (L289–L300) and confirming `WB = 0.0476` appears inline; verify `grep -n "L_sep / WB" openspec/specs/wayfinder/spec.md` still returns exactly one match (the symbol is preserved)
- [x] 1.4 Confirm `**Source:**` fields are unchanged in all three modified requirements (`A3-1.md`, `A5-1.md`, `A6b-2.md` references still present) by reading Req 5, Req 9, and Req 15 Source lines and verifying the three ticket identifiers still appear verbatim

## 2. Lint Gates (CLAUDE.md §3 archive prerequisite)

- [x] 2.1 Run `python scripts/lint_no_source_field_drift.py` and verify exit code is 0 and the report lists no failures for `wayfinder/` (the three existing Source fields `A3-1.md` / `A5-1.md` / `A6b-2.md` still satisfy the capability-aware Source rule)
- [x] 2.2 Run `python scripts/lint_no_dead_defensive.py` and verify exit code is 0 (no dead-defensive patterns introduced; the three edits are wording-only and do not add new defensive code paths)

## 3. Triple-Source Cross-Check (post-edit sanity)

- [x] 3.1 Read `openspec/specs/decompmoe-skeleton/spec.md` L401–L415 "Spherical L2 Normalization" Req and verify the wording of `z / max(‖z‖₂, ε)` matches the updated wayfinder Req 5 step (2)/(4) by manual side-by-side comparison (both use `max(·, ε)` form; both cite the same ε default)
- [x] 3.2 Read `src/decompmoe/sphere.py:40–50` `spherical_l2_normalize` and verify the implementation `z / torch.clamp(norm, min=eps)` is semantically equivalent to the updated Req 5 wording (`max(·, ε)` form) by manual inspection
- [x] 3.3 Read `src/decompmoe/experts.py:20–39` `SwiGLUExpert` and verify the three matrices `W_g, W_u ∈ R^{d_ffn × d_model}` and `W_d ∈ R^{d_model × d_ffn}` parameterize `3 · d_model · d_ffn` learnable weights per expert, matching the updated Req 9 "active parameters" terminology

## 4. Archive (OpenSpec workflow)

- [ ] 4.1 Run `openspec validate fix-wayfinder-spec-legacy-drift-2026-09-15 --strict --type change` and verify exit code is 0 (proposal + specs delta + design + tasks all valid)
- [ ] 4.2 Run `openspec archive fix-wayfinder-spec-legacy-drift-2026-09-15 --yes` to archive the change; verify the change directory is moved to `openspec/changes/archive/` and `openspec/specs/wayfinder/spec.md` is updated in place with the three wording fixes
- [ ] 4.3 Run `python scripts/lint_no_source_field_drift.py` and `python scripts/lint_no_dead_defensive.py` post-archive and verify both still exit 0 (per the archived `fix-openspec-doc-bugs` precedent — 12f673d bug — and CLAUDE.md §3)

## 5. Git Ops (per CLAUDE.md §4 dev / main / release)

- [ ] 5.1 Commit the spec edit on `dev` with message `fix(spec): align wayfinder spec wording with init decision + skeleton + code (legacy drift 2026-09-15)` — no merge commit, linear history preserved
- [ ] 5.2 (Optional, if user wants archival) `git checkout main && git merge --no-ff dev -m "archive: record wayfinder spec legacy-drift fix"` and push; immediately `git checkout dev` to keep dev HEAD on linear commit (per CLAUDE.md §4 "每次合并后立即 git checkout dev")
- [ ] 5.3 (Optional, only if user wants release) `git checkout release && git merge --no-ff dev -m "release: wayfinder spec legacy-drift fix"` and `git tag v<semver>` then `git checkout dev`