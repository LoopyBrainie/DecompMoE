# Spec Delta — `wayfinder`

## MODIFIED Requirements

<a id="req-32"></a>

### Requirement: Resurrection Perturbation Per-Expert Contract — Single-Event Wrapper

The Dead Expert Splitting Resurrection pathway (Req 13) MUST perturb the **single cloned expert** (centroid and/or expert weights) — not the per-expert routing frequency vector `f_per_expert`. The perturbation API `resurrection_perturb_distribution(f_per_expert, target_idx, eps_std=0.05, *, dim: int | None = None)` MUST accept `f_per_expert` as the leading positional argument with **shape `(..., N_e)`** — the trailing axis MUST equal `N_e` and leading dims are arbitrary (canonical call sites pass `(N_e,)`, `(T, N_e)`, or `(B, N, N_e)`). Layer 2 shape enforcement (wrapper-side, at this wrapper): `f_per_expert.shape[-1] == cfg.N_e` pair-check. The vacuous self-check `f_per_expert.shape[-1] == β_per_expert.shape[0]` (which is identically true given `f_per_expert = β_per_expert.detach()` inside this wrapper, where `shape[-1] == shape[0]`) was an earlier draft and was corrected by commit `0b2202e` to anchor on the spec-defined `cfg.N_e`. Layer 1 primitive-side enforcement (`ndim ≥ 1`) is described in Req 28. `target_idx` is a positional integer, `eps_std=0.05` is a positional-or-keyword perturbation scale, and `dim` is a **keyword-only** parameter sourcing the per-expert dimensionality. `dim=None` MUST raise `TypeError`. The returned tensor MUST have leading dimension `dim` — corresponding to a single expert slot — NOT the `(N_e,)` shape of `f_per_expert`. The β double-write semantic (`β_i ← 0.85 · β_{j*}` and `β_{j*} ← 0.85 · β_{j*}`) is defined in Req 13; this wrapper additionally guarantees same-call-stack execution (see wrapper contract paragraph below). (References Req 13.)

**The canonical single-event API is `resurrect_expert(i, j_star, β_per_expert, c_centroids, cfg) -> tuple[Tensor, Tensor]`** which returns `(c_perturbed, β_per_expert_new)` and guarantees that the centroid perturbation and the β double-write happen in the **same Python call stack** — no `yield` / `await` / background-task scheduling between the two operations. Callers MUST use `resurrect_expert` for the resurrection pathway; the two primitives `resurrection_perturb_distribution` and `apply_resurrection_beta_decay` remain available for low-level composition but their separate invocation does NOT satisfy the "same resurrection event" contract above. The wrapper signature takes `cfg: MVPConfig` so the per-expert dimensionality `cfg.d_c` is sourced from the canonical config rather than re-derived from `β_per_expert.shape` (which would conflate centroid dimension with the `N_e` routing dimension — the very bug the per-expert contract exists to prevent). It additionally takes `c_centroids: Tensor` of shape `(N_e, d_c)` as a **required per-call argument**, because Req 28's "perturb the single cloned expert" is unsatisfiable without it: neither `MVPConfig` nor `β_per_expert` carries a centroid, and a per-call parameter is the correct home for it because the donor differs on every resurrection event, whereas `MVPConfig` is a frozen configuration singleton. **The clone source is row `j_star` (the donor), not row `i`** — `i` is the dead expert whose own centroid is exactly the degenerate quantity the resurrection exists to replace, and this matches the β double-write, which likewise reads its pre-write value from `β_per_expert[j_star]`. A wrapper that cloned row `i` would be a no-op dressed as a resurrection.

**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-math-consistency-audit-2026-08` design.md (Decision 4 — per-expert perturbation contract); signature mirrors the `resurrect_expert` function in `src/decompmoe/safeguards.py` at commit `263ac19 feat(safeguards): per-expert resurrection perturb shape + same-event beta decay` (Layer 2 wrapper-side anchor `cfg.N_e` per commit `0b2202e fix(safeguards): replace vacuous β-length self-check with cfg.N_e meaningful guard` at the `cfg.N_e` guard inside `resurrect_expert`)

#### Scenario: perturbation accepts 1-D (N_e,) f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called with `f_per_expert.shape == (N_e,)` (e.g. `(16,)` at MVP)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

#### Scenario: perturbation accepts batched (B, N, N_e) f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called with `f_per_expert.shape == (B, N, N_e)` (e.g. `(4, 3, 16)` at MVP — matches the `L_lb` hot-path shape per `loss.py::LossComposition`)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

#### Scenario: perturbation accepts history-stacked (T, ..., N_e) f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` is called with `f_per_expert.shape == (T, ..., N_e)` (e.g. `(100, N_e)` history stacked by `metrics.UR` per `src/decompmoe/metrics.py::UR`)
- **THEN** the returned tensor has shape `(d_c,)` or `(d_model · d_ffn,)` (single expert), NOT `(N_e,)` (whole routing distribution)

#### Scenario: perturbation rejects 0-D scalar f_per_expert
- **WHEN** `resurrection_perturb_distribution(f_per_expert=(), target_idx=3, dim=16)` is called with `f_per_expert.ndim == 0`
- **THEN** the primitive raises `ValueError` (Layer 1 guard: ndim ≥ 1)

#### Scenario: wrapper pair-checks f_per_expert trailing axis vs cfg.N_e
- **WHEN** `resurrect_expert(i=3, j_star=0, β_per_expert, c_centroids, cfg)` is called with `β_per_expert.detach()` (the wrapper's internal `f_per_expert = β_per_expert.detach()`) whose trailing axis length `!= cfg.N_e` (the canonical N_e sourced from `cfg.MVPConfig`, **NOT** `β_per_expert.shape[0]` — the latter would be a vacuous self-check given `f_per_expert = β_per_expert.detach()`, where `shape[-1] == shape[0]` identically)
- **THEN** the wrapper raises `ValueError` (Layer 2 guard: trailing-axis = N_e pair-check, anchored on `cfg.N_e`)

#### Scenario: same-event beta decay
- **WHEN** `resurrect_expert(i, j_star, β_per_expert, c_centroids, cfg)` is called with any valid `MVPConfig cfg` and a `c_centroids` of shape `(N_e, d_c)` with unit-norm rows, valid expert indices `i` and `j_star` (`0 ≤ i, j_star < N_e`, `i ≠ j_star`), and a valid `β_per_expert ∈ R^{N_e}` (positive finite values)
- **THEN** the returned `c_perturbed` is `L2Normalize(c_centroids[j_star] + ε)` where `ε` is the output of `resurrection_perturb_distribution(β_per_expert.detach(), j_star, eps_std=0.05, dim=cfg.d_c)`, and the returned `β_per_expert_new` is the output of `apply_resurrection_beta_decay(β_per_expert, j_star, i)`, with both calls executed in the **same call stack** (no `await` / `yield` / `spawn` between them — verifiable by inspecting the wrapper's linear code path which is a synchronous function composition)
- **AND** `β_per_expert_new[i] == 0.85 · β_per_expert[j_star].item()` within `abs=1e-6` (donor value is read from `β_per_expert[j_star]` BEFORE either write, per the immutability clause; this matches the canonical pattern in `apply_resurrection_beta_decay`)
- **AND** `β_per_expert_new[j_star] == 0.85 · β_per_expert[j_star].item()` within `abs=1e-6` (the donor's own β is also decayed by the same factor)
- **AND** `c_perturbed.shape == (cfg.d_c,)` (single-expert slot shape, consistent with the perturbation output shape scenario above)
- **AND** `‖c_perturbed‖₂ == 1.0` within `abs=1e-6` — the resurrection MUST return a point on the unit sphere `S^{d_c−1}`. This is the invariant the bare-ε behaviour broke: `ε ~ N(0, eps_std²·I)` has RMS norm `eps_std·sqrt(d_c) = 0.2` at `d_c = 16, eps_std = 0.05`, so assigning it to `c_i` violated the sphere constraint before any other invariant could be checked. The **mean** norm is strictly smaller and has the exact closed form `E‖ε‖₂ = eps_std · √2 · Γ((d_c+1)/2) / Γ(d_c/2) = 0.196901` at these values (the `eps_std·sqrt(d_c)` figure is the RMS, i.e. `√(E‖ε‖₂²)`, and overstates the mean by 1.58% at `d_c = 16`; measured 0.196838 over 200 000 samples). This is a **float** closed form and MUST be pinned with `pytest.approx(0.196901, abs=1e-3)` against a Monte-Carlo mean, not with the RMS literal. This is a **float** closed form and MUST be pinned with `pytest.approx(1.0, abs=1e-6)`, never with a bare `==`
- **AND** `cos(c_perturbed, c_centroids[j_star]) > 0` — the returned point is a perturbation **of the donor**, not an independent random direction. Measured over 200 000 samples at `d_c = 16, eps_std = 0.05` the mean cosine is `0.981666` and the mean angle `10.8054°`; the bare-ε behaviour gave `−0.000289` and `90.0177°`, i.e. an 8.33× angle gap and a vector that was orthogonal to the donor
- **AND** `β_per_expert_new is not β_per_expert` (immutability: the input tensor is never mutated in-place; `apply_resurrection_beta_decay` clones internally)

#### Scenario: clone source is the donor row, not the dead expert
- **WHEN** `resurrect_expert(i, j_star, β_per_expert, c_centroids, cfg)` is called with `i != j_star` and `c_centroids` of shape `(N_e, d_c)` with unit-norm rows
- **THEN** the clone is taken from `c_centroids[j_star]` (the donor) and NOT from `c_centroids[i]`; with `eps_std → 0` the returned `c_perturbed` converges to `c_centroids[j_star]`
- **AND** an implementation that cloned row `i` MUST be rejected: `i` is the dead expert, so its centroid is the degenerate quantity the resurrection is meant to replace, and cloning it would return a perturbed copy of the very state being repaired


<a id="req-34"></a>

### Requirement: Source Field Format Invariant for OpenSpec Specs

Every `**Source:**` field in `openspec/specs/**/spec.md` MUST carry a **primary reverse-link** to its design lineage as the **first top-level item** of the field, with each reverse-link token **wrapped in backticks** (inline code span). The required primary reverse-link is per-capability:

- `openspec/specs/governance/spec.md` — primary reverse-link MUST be a backtick-wrapped `CLAUDE.md` reference (governance-origin lineage).
- All other `openspec/specs/**/spec.md` (wayfinder-ticketed, decompmoe-skeleton, future peers that cite wayfinder tickets) — primary reverse-link MUST be a backtick-wrapped `wayfinder/tickets/<ID>.md` reference.

A `change <name> design.md (Decision N)` reference MAY appear additionally as a **secondary** link after the primary reverse-link, but its presence does NOT substitute for the primary ticket / governance reverse-link. The primary reverse-link MUST NOT be preceded by any `change \`foo\` design.md (Decision N)` clause or other secondary reference.

When the ticket's value at the time of writing differs from the current spec value (e.g. a threshold changed by a later change), the primary ticket reference MUST use the `(historical, <original-value>; superseded by <change> Decision N)` annotation format — preserving the ticket's original value, marking it as historical, and naming the superseding change explicitly. Naked ticket references that omit the annotation but imply current-value parity with the spec are NOT permitted for tickets whose recorded value has been superseded.

This invariant MUST be enforced at archive time by `scripts/lint_no_source_field_drift.py`. The lint script performs three structural checks on every `**Source:**` line:

1. **Capability-aware presence, two independent parts** — the line MUST contain the per-capability required primary reverse-link marker (`CLAUDE.md` for governance, `wayfinder/tickets/` for all others), AND at least one backtick-wrapped code span MUST name a concrete file in the per-capability required form: `wayfinder/tickets/<ID>.md` for ticket lineage (where `<ID>` is the ticket file's stem, e.g. `A4-1`), or the literal `CLAUDE.md` for governance, which has no file to name. The bare directory form `wayfinder/tickets/` and the extension-less form `wayfinder/tickets/<ID>` MUST each be reported as violations: neither resolves to a file, and at the gate they are indistinguishable from the canonical form, so an untraceable reverse-link could pass.
2. **Backtick wrapping** — every occurrence of the per-capability required primary reverse-link substring MUST appear inside a backtick-delimited code span; a reverse-link that appears outside a code span is a violation regardless of substring presence.
3. **Primary-first ordering** — the first top-level item (the substring from the `**Source:**` marker up to the first `,` or `;` at paren-depth 0, with code-span atomicity so a delimiter inside a backtick pair does NOT split) MUST be a backtick-wrapped code span whose contents include the per-capability required primary reverse-link substring.

The three checks are independent — a line may fail ① while passing ②③ (substring present, backticked, first item is the backticked primary), or fail ②③ while passing ① (substring present in plain text), or fail all three. The lint script reports each violation with a distinct reason code so a developer can fix the right thing.

The rules are content-based (not line-number based) so they survive spec edits without producing chronic exemption-table rot. The rules are zero-exemption: NO lines are permitted to bypass them, including governance-level requirements whose design origin is a `CLAUDE.md` amendment rather than a ticket (governance is honored by the per-capability substring dispatch, NOT by a carve-out).

#### Scenario: every Source field contains a wayfinder ticket reference

- **WHEN** `scripts/lint_no_source_field_drift.py` is run against `openspec/specs/**/spec.md`
- **THEN** the script enumerates every line beginning with `**Source:**` and verifies (a) the line contains the per-capability marker substring `wayfinder/tickets/` (or `CLAUDE.md` for the governance capability), and (b) at least one backtick-wrapped code span matches the per-capability form (`wayfinder/tickets/<ID>.md`, or the literal `CLAUDE.md` for governance)
- **AND** the script exits with code `0` if and only if every such line satisfies the substring check
- **AND** the script outputs a per-line violation report (file path, line number, the violating line content) when any violation exists, with no aggregate-only summary that hides which line failed

#### Scenario: superseded values use the historical annotation format

- **WHEN** a spec Requirement's value differs from the corresponding `wayfinder/tickets/<ID>.md` original value
- **THEN** the Source field MUST be written as `**Source:** \`wayfinder/tickets/<ID>.md\` (historical, <original-value>; superseded by <change-name> Decision <N>), change \`<change-name>\` design.md (Decision <N>)`
- **AND** the `(historical, ...)` annotation MUST include the original value (e.g. a threshold, a constant, a formula term) so a reader can reconstruct the design history without leaving the spec

#### Scenario: governance-origin requirements trigger lint failure

- **WHEN** a spec Requirement's design origin is a `CLAUDE.md` amendment (or a commit amending `CLAUDE.md`) rather than any `wayfinder/tickets/*.md` ticket
- **THEN** the Source field is **required** to still contain a per-capability required reverse-link (`CLAUDE.md` for the governance capability; for wayfinder-ticketed capabilities, a `wayfinder/tickets/<ID>.md` reference with an honest `(historical, ...)` annotation)
- **AND** any such requirement whose honest annotation cannot be written (because no A* ticket is its legitimate design predecessor) MUST be migrated to a separate governance capability (e.g. `openspec/specs/governance/spec.md`) before archive, so the wayfinder main spec never carries Source fields the lint rule cannot validate
- **AND** until such migration occurs, the lint failure on that specific line is the **intended design signal** that the change owning that line is incomplete — it MUST NOT be silently suppressed by an exemption table

#### Scenario: reverse-link must be wrapped in backticks

- **WHEN** a `**Source:**` line in `openspec/specs/**/spec.md` contains the per-capability required primary reverse-link marker (`wayfinder/tickets/` for wayfinder-ticketed / decompmoe-skeleton specs, `CLAUDE.md` for governance specs) OUTSIDE a backtick-delimited code span
- **THEN** `scripts/lint_no_source_field_drift.py` MUST report a violation with reason `"unbackticked reverse-link: <substring>"` for that line
- **AND** the lint script's check is structural: it MUST strip code spans from the line body and verify that the remaining (unbackticked) text does NOT contain the required substring
- **AND** a backtick-wrapped reverse-link on the same line that satisfies ① still passes (multiple backticked reverse-links on a single line are permitted, e.g. `**Source:** \`wayfinder/tickets/A2-1.md\`, \`wayfinder/tickets/A2-2.md\``)
- **AND** the scenario is verified by `tests/test_lint_no_source_field_drift.py::test_unbackticked_refs_flags_bare_substring` and `::test_unbackticked_refs_ignores_backticked_substring`

#### Scenario: primary reverse-link must be the first top-level item

- **WHEN** a `**Source:**` line in `openspec/specs/**/spec.md` is split by `,` or `;` at paren-depth 0 (with code-span atomicity: a backtick toggles an atomic flag so a delimiter inside a code span does NOT split)
- **THEN** the first top-level item MUST be a backtick-wrapped code span whose contents include the per-capability required primary reverse-link substring
- **AND** `scripts/lint_no_source_field_drift.py` MUST report a violation with reason `"first item is not the primary reverse-link (first code span = <...>, required substring = <required>)"` for any line whose first top-level item is not the primary reverse-link
- **AND** the lint script's split is paren-depth aware: a comma inside `(...)` does NOT split (e.g. `**Source:** \`wayfinder/tickets/A6a-2.md\` (initial A6a-2 design intent), change \`fix-openspec-doc-bugs\` design.md (Decision 1, 2)` has only TWO top-level items, not four)
- **AND** the lint script's split is code-span atomic: a comma inside `` `...` `` does NOT split (e.g. `**Source:** \`wayfinder/tickets/A2-1.md\`, change \`foo, bar, baz\` design.md (Decision 1)` has only TWO top-level items, not four)
- **AND** the scenario is verified by `tests/test_lint_no_source_field_drift.py::test_split_top_level_items_paren_depth` and `::test_first_item_must_be_primary_reverse_link`

#### Scenario: secondary references in parenthetical annotations use bare ticket IDs

- **WHEN** a `**Source:**` line's primary reverse-link is backtick-wrapped as the first top-level item, and a parenthetical annotation immediately following the primary contains a ticket reference (e.g. a `supersedes` or `compare with` clause)
- **THEN** the annotation's ticket reference MUST be written as a bare ticket ID (e.g. `A6a-2.md`), NOT as a backtick-prefixed full path (e.g. `` `wayfinder/tickets/A6a-2.md` ``)
- **AND** the reason is: a bare full-path reference inside a paren annotation would (under the strict reading of check ② "every occurrence of the per-capability required primary reverse-link substring MUST appear inside a backtick-delimited code span") trigger an `unbackticked reverse-link` violation on the secondary occurrence — because `wayfinder/tickets/` is a substring prefix that appears in any full-path ticket reference
- **AND** the canonical live example is `openspec/specs/wayfinder/spec.md` `req-13` 的 `**Source:**` 字段: ``**Source:** `wayfinder/tickets/A6a-2.md` (historical, threshold `1/128`), change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold superseded by `1/(2·N_e)`)`` — the paren annotation uses bare `1/128` (the value), bare `1/(2·N_e)` (the superseding formula), and bare ticket IDs in change-decision clauses; it MUST NOT use `` `wayfinder/tickets/...` `` in any non-first-item paren annotation
- **AND** the scenario is verified by `tests/test_lint_no_source_field_drift.py::test_first_item_is_primary_with_historical_annotation`

#### Scenario: tokenizer handles single-backtick code spans only

- **WHEN** a `**Source:**` line uses Markdown constructs that the lint script's hand-rolled tokenizer does NOT support — namely double-backtick code spans (`` ``...`` ``), backslash-escaped backticks (`\\\``), or multi-line Source fields whose `,` / `;` delimiters appear on subsequent lines
- **THEN** the lint script MUST report a violation for the line (rather than silently passing or raising an unhandled exception)
- **AND** the canonical double-backtick behavior: a `` `` `` toggles `in_code_span` to False immediately, so all subsequent text is treated as outside code span. A Source line written with double-backtick spans will be parsed by the lint as if it used single-backtick spans — which will likely produce a false-positive `unbackticked reverse-link` violation on the second half of the double-backtick span content
- **AND** the canonical backslash-escape behavior: `\`` is treated as a regular character (the escape is not recognized), so the next backtick will toggle `in_code_span` normally — producing unpredictable parse state
- **AND** the canonical multi-line behavior: the lint script reads `**Source:**` lines one line at a time; a Source field whose content continues onto subsequent lines is NOT concatenated — the subsequent lines are scanned as separate `**Source:**` lines (none of which will match the regex), and the original line's body is processed as a self-contained single-line Source field, almost certainly failing check ① because the body is incomplete
- **AND** the convention enforced by this Scenario is: Source fields MUST use single-backtick code spans exclusively, MUST NOT use backslash-escapes inside backticks, and MUST be written on a single line. Any violation of these conventions MUST be fixed by rewriting the line, not by expecting the lint script to handle the edge case
#### Scenario: Bare-directory and extension-less reverse-link forms are violations

- **WHEN** a `**Source:**` line's only ticket reverse-link is the bare directory form `` `wayfinder/tickets/` `` or the extension-less form `` `wayfinder/tickets/A4-1` ``
- **THEN** the script MUST report a violation stating that the reverse-link does not name a concrete file
- **AND** it MUST NOT be reported as passing merely because the marker substring is present, backtick-wrapped, and first
- **AND** the canonical form `` `wayfinder/tickets/A4-1.md` `` MUST pass unchanged
- **AND** the governance form `` `CLAUDE.md` `` MUST pass unchanged, since governance lineage names a file already and the tightened form check MUST NOT be asymmetric between capabilities
