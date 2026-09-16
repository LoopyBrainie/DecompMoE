## Context

`openspec/specs/decompmoe-skeleton/spec.md` carries 22 Requirement headings but only 5 leading anchors. The 5 existing anchors (`req-1` through `req-5` at L349, L385, L405, L430, L455) are positioned immediately before the *last* 5 Requirements by document order, leaving the first 17 Requirements (L8–L331) un-anchored.

`openspec/specs/wayfinder/spec.md` is the canonical reference for anchor placement: 33 Requirements, every one with a leading `<a id="req-N"></a>` whose `N` matches document order (1..33). The skeleton's anchor numbering diverges from this convention.

The only `#req-N` reference embedded inside `openspec/specs/decompmoe-skeleton/spec.md` is at L220 — it points to **wayfinder** Req 13, not to any skeleton anchor. A repo-wide grep for `decompmoe-skeleton/spec.md#req-` returns zero matches. The 5 existing skeleton anchors (`req-1`..`req-5`) are unreferenced stubs; renumbering them is safe.

See `proposal.md - Why` for the motivation.

## Goals / Non-Goals

**Goals:**
- Establish a 1-to-1 mapping between the 22 Requirement headings in `openspec/specs/decompmoe-skeleton/spec.md` and 22 leading anchors `<a id="req-N"></a>` where `N` matches the Requirement's position in the document.
- Make every Requirement in skeleton spec linkable using the same relative-path Markdown link form already in use for wayfinder (`../specs/decompmoe-skeleton/spec.md#req-N`).
- Bring skeleton's anchor coverage (22/22) up to wayfinder's coverage (33/33).

**Non-Goals:**
- Changing Requirement text, Scenario text, or `**Source:**` annotations.
- Renaming any existing Requirement title.
- Modifying any code under `src/decompmoe/`.
- Touching `openspec/specs/wayfinder/spec.md` or `openspec/specs/governance/spec.md`.

## Decisions

### Decision 1: Anchor numbering = document order (req-1 through req-22)

Numbering follows the position of each Requirement heading in the file, in reading order:

| Heading line | Title (abbrev) | Anchor |
|---|---|---|
| L8   | Canonical Package And Version Identifier      | `req-1`  |
| L20  | Total And Active Parameter Estimator          | `req-2`  |
| L36  | Active FLOPs Parity Against Dense Baseline     | `req-3`  |
| L56  | Wire-Level Contracts                            | `req-4`  |
| L64  | Inverse-Temperature Sigmoid With Gradient Bounds| `req-5`  |
| L84  | Voronoi Self-Consistency Threshold             | `req-6`  |
| L100 | C Extraction Four-Step Pipeline                 | `req-7`  |
| L120 | Isotropic Squared-Chord Distance And Logit      | `req-8`  |
| L136 | Top-K Sparse Mask With Local Softmax            | `req-9`  |
| L152 | Standard SwiGLU Expert With No Shared Branch    | `req-10` |
| L176 | Loss Composition With Staged Lambda             | `req-11` |
| L204 | Five Numerical Safeguard Helpers                | `req-12` |
| L264 | Five-Phase Schedule State Machine               | `req-13` |
| L284 | Six Visualization Module Protocol Stubs         | `req-14` |
| L300 | Hard-Constraint Grep Invariants                 | `req-15` |
| L315 | Centroid Driver Semantic Invariants             | `req-16` |
| L331 | Centroid Driver Invariant Test Scenarios        | `req-17` |
| L351 | Centroid Four-Phase Lifecycle Driver (P4 SGD)   | `req-18` |
| L387 | Spherical L2 Normalization                       | `req-19` |
| L407 | Beta Parameterization Operational Domain         | `req-20` |
| L432 | Frozen MVP Hyperparameter Set                    | `req-21` |
| L457 | Eight Metrics And Classification                 | `req-22` |

**Why document order:** Matches the established wayfinder convention (`openspec/specs/wayfinder/spec.md` anchors 1..33 in document order). Reviewers and tooling that scan spec files expect `req-N` to mean "Nth Requirement from the top".

**Alternatives considered:**
- *Keep existing `req-1`..`req-5` numbering for the last 5 Requirements; number the first 17 as `req-6`..`req-22`.* — rejected: produces a non-monotonic, non-contiguous numbering where `req-3` (Beta Parameterization, mid-file) appears in the middle of `req-6`..`req-22`, confusing readers and breaking the wayfinder convention.
- *Slug-based anchors (`req-canonical-package-and-version-identifier`).* — rejected: 22 long slugs add visual noise; not used in wayfinder; harder to maintain (renames require slug updates).
- *Ticket-id-based anchors (`req-a0-1`, etc.).* — rejected: skeleton Requirements do not map 1-to-1 to wayfinder tickets (see `2026-08-18-polish-wayfinder-spec/design.md` Decision 1 rejection rationale).

### Decision 2: Anchor insertion = literal `<a id="req-N"></a>` on its own line + 1 blank line before each `### Requirement:` heading

Mirrors the wayfinder line-for-line convention. Example for the L387 Requirement after the change:

```
<a id="req-19"></a>

### Requirement: Spherical L2 Normalization — max(…z…, ε) Formula
```

**Alternatives considered:**
- *HTML heading attributes `<a id="req-N"></a>` inline within the heading text* — rejected: wayfinder uses a separate line; staying in lock-step matters for visual diffing across specs.
- *GitHub-style anchor auto-generation (`## Spherical L2 Normalization...` → `#spherical-l2-normalization---maxz-ε-formula`)* — rejected: brittle (auto-ID rules vary by renderer); conflicts with the explicit wayfinder convention.

### Decision 3: Renumber the 5 existing anchors (req-1..req-5 → req-18..req-22)

The 5 currently-anchored Requirements (last 5 by document order) keep their anchors but receive new IDs matching document order.

**Why safe:** Repo-wide grep confirms zero references to `decompmoe-skeleton/spec.md#req-1`..`req-5`. The single `#req-13` reference inside skeleton spec (L220) points to **wayfinder** Req 13, not skeleton.

**Migration cost:** 5 lines get `req-1` → `req-18`, `req-2` → `req-19`, etc. No text changes, no other files affected.

## Risks / Trade-offs

- **[Risk] Anchor ID collision if a future spec edit reorders Requirements** → **Mitigation:** The numbering scheme is *defined* as "Nth `### Requirement:` heading from the top of the file"; any reorder must re-anchor in lock-step. A lint-style verification (grep `^### Requirement:` count == 22) catches dropped headings; a `grep '<a id="req-' count == 22` catches dropped anchors. Run both before commit.
- **[Trade-off] 17 new lines (and 5 renumbered lines) added to a 540-line spec file** — diff is small and localized; review burden is minimal. Net spec length grows by ~17 lines.
- **[Risk] External doc sites that mirror `openspec/specs/decompmoe-skeleton/spec.md` may cache the old anchor set** — **Mitigation:** None directly; document the change in the change archive so consumers know the anchor IDs changed. Out of scope to push notifications.
- **[Risk] A reader skimming only the table of contents sees 22 anchors but a previous archived version of the spec had 5** — **Mitigation:** This is the intended outcome; documented in proposal.md.
