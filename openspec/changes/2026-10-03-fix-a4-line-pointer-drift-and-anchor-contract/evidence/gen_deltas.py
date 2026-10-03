#!/usr/bin/env python3
"""Generate the three spec deltas for change
2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract.

WHY A GENERATOR: this repo has Requirement bodies that are a single line of
thousands of characters (decompmoe-skeleton req-6 body measured 15_413 chars,
longest line 6_691). `openspec instructions specs` requires a MODIFIED block to
carry the ENTIRE Requirement, so hand-transcription is both impractical and
unsafe: a substring edit leaves a dangling tail while every grep keyword still
matches, producing text that looks fine and is semantically broken.

Method (plan section 0):
  1. extract the target block from the LIVE spec by `<a id="...">` anchor
  2. apply WHOLE-LINE replacements, each asserted to match exactly one line
  3. emit the delta
  4. verify by difflib-unifying the delta block against the live block and
     reporting every changed line

Re-run is idempotent: it always reads the live spec, never a previous delta.
"""
from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _repo import REPO  # noqa: E402

REPO = REPO
CHANGE = REPO / "openspec" / "changes" / (
    "2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract"
)


# --------------------------------------------------------------------------
# block extraction
# --------------------------------------------------------------------------
def load_spec(cap: str) -> list[str]:
    return (REPO / "openspec" / "specs" / cap / "spec.md").read_text(
        encoding="utf-8"
    ).splitlines()


def anchor_starts(lines: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for i, l in enumerate(lines):
        m = re.match(r'<a id="([\w-]+)"></a>', l.strip())
        if m:
            # Only a REQUIREMENT anchor delimits a Requirement block. A block
            # anchor such as <a id="req-20-mci"> sits inside a Requirement and
            # must not truncate it. Accept the anchor as a boundary only when
            # the next non-empty line is the Requirement heading.
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].strip():
                    if lines[j].startswith("### Requirement:"):
                        out.setdefault(m.group(1), i)
                    break
    return out


def block_range(lines: list[str], starts: dict[str, int], req: str) -> tuple[int, int]:
    if req not in starts:
        raise KeyError("no anchor %s" % req)
    s = starts[req]
    e = len(lines)
    for _r, si in starts.items():
        if si > s:
            e = min(e, si)
    return s, e


def get_block(lines: list[str], req: str) -> list[str]:
    starts = anchor_starts(lines)
    s, e = block_range(lines, starts, req)
    return lines[s:e]


# --------------------------------------------------------------------------
# whole-line replacement
# --------------------------------------------------------------------------
def replace_line(block: list[str], needle: str, new: str, label: str) -> list[str]:
    """Replace the single line containing `needle` with `new`.

    Whole-line, never substring: a substring edit would leave the original
    line's tail dangling. Exactly-one match is asserted, because "0 matches"
    means the plan's coordinates went stale and "2 matches" means the needle is
    not discriminating.
    """
    hits = [i for i, l in enumerate(block) if needle in l]
    if len(hits) != 1:
        raise SystemExit(
            "REPLACE %s: expected exactly 1 line containing %r, found %d"
            % (label, needle, len(hits))
        )
    out = list(block)
    out[hits[0]] = new
    return out


def substitute_line(block: list[str], token: str, repl: str, label: str) -> list[str]:
    """Replace ONE self-contained pointer `token` inside its line, keeping the rest.

    Preferred over replace_line whenever the change is a pointer rewrite: the
    surrounding prose is carried over verbatim, so content cannot be lost.
    `token` must occur exactly once in exactly one line.
    """
    hits = [(i, l.count(token)) for i, l in enumerate(block) if token in l]
    total = sum(c for _i, c in hits)
    if len(hits) != 1 or total != 1:
        raise SystemExit(
            "SUBSTITUTE %s: token %r expected in exactly 1 line/1 occurrence, "
            "found %d line(s)/%d occurrence(s)" % (label, token, len(hits), total)
        )
    out = list(block)
    i = hits[0][0]
    out[i] = out[i].replace(token, repl)
    return out


def build(cap: str, reqs: dict[str, list[str]], added: list[str] | None = None,
          removed: list[str] | None = None) -> str:
    parts = ["# Spec Delta — `%s`\n" % cap]
    if added:
        parts.append("\n## ADDED Requirements\n")
        parts.extend(added)
    if removed:
        parts.append("\n## REMOVED Requirements\n")
        parts.extend(removed)
    parts.append("\n## MODIFIED Requirements\n")
    for req, block in reqs.items():
        parts.append("\n")
        parts.append("\n".join(block))
        parts.append("\n")
    return "".join(parts)


def verify(cap: str, req: str, live: list[str], delta: list[str]) -> int:
    """Report every line that differs between live and delta block."""
    diff = list(difflib.unified_diff(live, delta, "live/" + req, "delta/" + req, n=0, lineterm=""))
    changed = [l for l in diff if (l.startswith("+") or l.startswith("-")) and not l.startswith(("+++", "---"))]
    if changed:
        print("  --- %s / %s : %d changed lines" % (cap, req, len(changed)))
        for l in changed:
            print("      " + l[:200])
    return len(changed)

# --------------------------------------------------------------------------
# wayfinder
# --------------------------------------------------------------------------
WF = "wayfinder"
wf = load_spec(WF)

# --- req-2: AC-90, `per req-11 L211` lands inside req-10 Territory Seeding ---
WF_REQ2 = substitute_line(
    get_block(wf, "req-2"),
    "per req-11 L211",
    "per `Req 11` \"4070 MVP Hyperparameter Set\" (`#req-11`)",
    "wf/req-2",
)


# --- req-6: `src/decompmoe/extraction.py:119-120` code pointer ---
b = get_block(wf, "req-6")
b = replace_line(
    b,
    "src/decompmoe/extraction.py:119-120",
    "- **Phase 0** \u2014 Spherical K-Means seeding (no gradient, no EMA): `c_i^(t+1) = KMeans(C)` "
    "initialization. **Phase 0 K-Means implementation is deferred to the training-time caller** "
    "(MVP scope per `CLAUDE.md \u00a77 \"Out of Scope\"` \u2014 training execution out-of-scope). The "
    "canonical contract name in the codebase is `territory_seeding(C_batch, N_e, *, d_c)` (per req-2 "
    "\"Formal Symbols And Code Naming\" identifier map), which currently raises `NotImplementedError` "
    "with a verbatim pointer to this clause. Drivers and inference-time callers MUST NOT call "
    "`territory_seeding` at inference time; `CentroidDriver.step` Phase 0 (`Phase.SEEDING`) returns "
    "the input centroids detached as a no-op (see `extraction.py::CentroidDriver.step`, Phase 0 branch).",
    "wf/req-6",
)
WF_REQ6 = b

# --- req-13: `src/decompmoe/safeguards.py:98-102` code pointer ---
b = get_block(wf, "req-13")
b = replace_line(
    b,
    "src/decompmoe/safeguards.py:98-102",
    "- **THEN** the call is **deferred** \u2014 it returns `set()` at the rate-limit guard \u2014 **if "
    "and only if `\u0394 < R`**. The window edge is **exclusive**: `\u0394 = R` is **not** deferred and "
    "the call proceeds to the dead-expert trigger. The normative formalization (monotone single-jump "
    "predicate, the per-pair window equivalence, and the `R`-aligned counterexample that fixes the "
    "edge) is `openspec/specs/decompmoe-skeleton/spec.md` req-12 Scenario \"Resurrection rate-limited\"; "
    "guarded by `tests/test_safeguards.py::test_should_resurrect_rate_limit_boundary`. **Scope "
    "correction**: the prior wording \u2014 \"two experts meet the dead-expert trigger within the same "
    "1000-step window \u2026 only one resurrection event executes; the second is deferred\" \u2014 "
    "described a **per-window quota of one resurrection**, which `should_resurrect` does **not** "
    "implement: it returns **every** expert satisfying the per-step trigger in the call "
    "(`safeguards.py::should_resurrect`, no one-per-window clipping). The rate limit is a **per-call "
    "deferral gate** only, and this Scenario is restated to match the implemented contract; the "
    "superseded reading is recorded here rather than silently dropped.",
    "wf/req-13",
)
WF_REQ13 = b

# --- req-32: `src/decompmoe/loss.py:88` code pointer ---
b = get_block(wf, "req-32")
b = replace_line(
    b,
    "src/decompmoe/loss.py:88",
    "- **WHEN** `resurrection_perturb_distribution(f_per_expert, target_idx=3, eps_std=0.05, dim=16)` "
    "is called with `f_per_expert.shape == (B, N, N_e)` (e.g. `(4, 3, 16)` at MVP \u2014 matches the "
    "`L_lb` hot-path shape per `loss.py::LossComposition`)",
    "wf/req-32",
)
WF_REQ32 = b

# --- req-20: mint block anchors for the two repeatedly-referenced targets ---
b = get_block(wf, "req-20")
hits = [i for i, l in enumerate(b) if l.strip().startswith("| `MCI`")]
if len(hits) != 1:
    raise SystemExit("wf/req-20: expected 1 MCI table row, found %d" % len(hits))
b[hits[0]] = '<a id="req-20-mci"></a>\n' + b[hits[0]]
hits = [i for i, l in enumerate(b) if l.startswith("**Source:**")]
if len(hits) != 1:
    raise SystemExit("wf/req-20: expected 1 Source line, found %d" % len(hits))
b[hits[0]] = '<a id="req-20-source"></a>\n' + b[hits[0]]
WF_REQ20 = b
WF_REQ20 += [
    "",
    "#### Scenario: req-20 is the single canonical source for the MCI closed form",
    "",
    "- **WHEN** `MCI(token_signatures)` is implemented per `#req-20-mci`",
    "- **THEN** the implementation uses `M = (1/|T|) \u00b7 \u03a3 C_t C_t^T` uncentered second "
    "moment (NOT centered covariance, NOT convex hull radius), with eigenvalues `\u03bb_j` extracted "
    "from `M`, normalized to `\u03bb\u0303_j = \u03bb_j / \u03a3_r \u03bb_r`, and the result is "
    "`1 / (d_c \u00b7 \u03a3 \u03bb\u0303_j\u00b2)`",
    "- **AND** the result lies in `MCI \u2208 [1/d_c, 1]` closed range with both endpoints attainable, "
    "guarded by the two `MCI closed-form` Scenarios above at `abs=1e-12`",
    "- **AND** no other Requirement restates this closed form: a Requirement that points at this one "
    "MUST reference `#req-20-mci` rather than a line number or a verbatim copy, so that editing this "
    "Requirement cannot invalidate a pointer elsewhere",
]

# --- req-36: thin-pointer rewrite (removes verbatim duplication + contradiction) ---
WF_REQ36 = [
    '<a id="req-36"></a>',
    '',
    '### Requirement: Eight Geometric Quantification Metrics \u2014 Ticket A8-2 L70/L74 Supersede Annotation Closure',
    '',
    'The system SHALL treat `Req 20` "Eight Geometric Quantification Metrics" (`#req-20`) as the '
    '**single canonical truth source** for the closed-form `uncentered second moment` definition of '
    '`MCI`, and for the supersede argument that replaces the historical centered-covariance and '
    'CV / convex-hull-radius readings.',
    '',
    'This Requirement is a **pointer, not a copy**. It MUST NOT restate the closed form, its Reason '
    'narrative, or the Source field: a verbatim copy is a second instance that drifts independently '
    'of the original, and it is what previously made this Requirement self-contradicting (it named '
    'two different line numbers for the same `MCI` row). Every reference below resolves through an '
    'anchor, so editing `#req-20` cannot invalidate this Requirement.',
    '',
    '**The canonical definitions this Requirement points at** (all in `#req-20`):',
    '',
    '- `#req-20-mci` \u2014 the `MCI` table row carrying the `uncentered second moment` closed form, '
    'its Reason supersede narrative, and its `MCI \u2208 [1/d_c, 1]` range declaration.',
    '- `#req-20-source` \u2014 the Source field carrying the 3 reverse-links.',
    '- The two `MCI closed-form on uniform token distribution` / `rank-1 token distribution` '
    'Scenarios under `#req-20`, which guard the `MCI = 1.0` upper and `MCI = 1/d_c` lower endpoints '
    'at `abs=1e-12`.',
    '',
    '**Ticket-side supersede annotations** live on the ticket, not here: '
    '`wayfinder/tickets/A8-2.md` \u00a7`\u03bb_j = C \u5206\u5e03\u534f\u65b9\u5dee\u77e9\u9635\u7684\u7279\u5f81\u503c` '
    '(centered-covariance reading) and \u00a7`\u5173\u952e\u4fee\u6b63` (geometric convex hull radius CV '
    'reading) each carry an italic `(historical, <original reading>; superseded by spec req-20 '
    'uncentered second moment ...)` annotation that retains the original stale wording verbatim. '
    'Those annotations are historical lineage records and are **not** restated or line-addressed here.',
    '',
    '**Source:** `wayfinder/tickets/A8-2.md`, change `fix-openspec-doc-bugs` design.md (Decision 8), '
    'change `fix-math-consistency-audit-2026-08` design.md (Decision 5)',
    '',
    '#### Scenario: req-20 is the single canonical source for the MCI closed form',
    '',
    '- **WHEN** `MCI(token_signatures)` is implemented per `#req-20-mci`',
    '- **THEN** the implementation uses `M = (1/|T|) \u00b7 \u03a3 C_t C_t^T` uncentered second moment '
    '(NOT centered covariance, NOT convex hull radius), with eigenvalues `\u03bb_j` extracted from '
    '`M`, normalized to `\u03bb\u0303_j = \u03bb_j / \u03a3_r \u03bb_r`, and the result is '
    '`1 / (d_c \u00b7 \u03a3 \u03bb\u0303_j\u00b2)` \u2014 all per `#req-20-mci`',
    '- **AND** the result lies in `MCI \u2208 [1/d_c, 1]` closed range, with both endpoints attainable '
    '(uniform distribution \u21d2 `MCI = 1.0`; rank-1 distribution \u21d2 `MCI = 1/d_c`), guarded by the '
    'two `MCI closed-form` Scenarios under `#req-20` at `abs=1e-12`',
    '- **AND** this Requirement contains **no** line-number pointer and **no** verbatim copy of the '
    'closed form, so an edit to `#req-20` cannot invalidate it',
    '',
    '#### Scenario: ticket A8-2 supersede annotations are preserved as historical records',
    '',
    '- **WHEN** the A8-2 centered-covariance annotation and the A8-2 convex-hull-radius CV annotation '
    'are read',
    '- **THEN** each preserves its original stale wording verbatim AND is immediately followed by an '
    'italic `(historical, <original reading>; superseded by spec req-20 uncentered second moment via '
    'fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 design.md '
    'Decision 5 \u2014 <why the original reading is unreachable>)` annotation',
    '- **AND** the two annotations jointly cover both clauses of the `#req-20-mci` Reason supersede '
    'argument (the `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c` for the centered reading, '
    'and the `1/d_c` lower bound on `S^{d_c\u22121}` making the original `< 0.05` health target '
    'unreachable for the CV reading), and both name the **same** supersession target and the **same** '
    'chain of authority',
]


# --- req-36 is REMOVED. It existed only to point at req-20 while doing so
# --- with line numbers, and it contradicted itself (body said L453, Scenarios
# --- said L413). `openspec validate` additionally refuses a MODIFIED block
# --- that renames a Scenario, and req-36's Scenario TITLES carry the very
# --- line pointers this change removes — so the titles cannot be kept and the
# --- body cannot be rewritten in place. Removal is the only shape that clears
# --- both constraints.
WF_REMOVED = """### Requirement: Eight Geometric Quantification Metrics \u2014 Ticket A8-2 L70/L74 Supersede Annotation Closure

**Reason**: this Requirement was a *pointer* to `req-20` expressed as raw line
numbers, and it was the drift amplifier for the whole A-4 family. It verbatim
duplicated `req-20`'s closed form (a second instance that drifts independently),
it named two different line numbers for the same `MCI` row within a single
Requirement (body `L453`, Scenarios `L413`), and its Scenarios MANDATED that the
spec's own line numbers not change \u2014 so editing `req-20` invalidated it while
repairing it required editing the spec. It additionally wrote the anchor literal
`<a id="req-20"></a>` into its prose, which is the direct cause of the duplicate
`req-20` anchor in this capability (39 anchors against 37 Requirements).

**Migration**: all four guarantees are redistributed to the Requirements that
actually own them, none of them weakened:

- Guarantee (a) "the `MCI` closed form is the canonical, unchanging truth" is
  now asserted on `req-20` itself, in a new Scenario, addressing `#req-20-mci`
  and `#req-20-source` by anchor.
- Guarantees (b) and (c) "each A8-2 supersede annotation is preserved verbatim
  and immediately followed by its italic `(historical, ...)` annotation" move to
  `governance` `req-gov-2`, which is the capability that owns the ticket
  supersede-annotation pattern.
- Guarantee (d) "the two A8-2 annotations jointly cover both clauses of the
  `req-20` Reason argument" also moves to `governance` `req-gov-2`, which
  already registers the annotation's Source lineage.

`openspec validate` cannot express this as a `MODIFIED` block: it rejects a
modified Requirement whose Scenario titles differ from the live ones, and
`req-36`'s titles are themselves the defect. The two ticket-annotation Scenario
titles are kept verbatim in `governance` `req-gov-2` because that is where the
guard now lives and because they carry their own historical marker, so the new
C1 check exempts them by marker rather than by an exemption registry.
"""

# --------------------------------------------------------------------------
# decompmoe-skeleton
# --------------------------------------------------------------------------
SK = "decompmoe-skeleton"
sk = load_spec(SK)
sk_starts = anchor_starts(sk)


def owner_of(lines, starts, lineno):
    best = None
    for r, si in starts.items():
        if si < lineno and (best is None or si > best[1]):
            best = (r, si)
    return best[0] if best else None


# L505 / L507 / L530 -> `req-7` closed-form / MVPConfig beta literal references
def sk_fix(lines, needle, new, label):
    return replace_line(lines, needle, new, label)


SK_REQ21 = sk_fix(
    get_block(sk, "req-21"),
    "per wayfinder spec req-7 L130 closed-form",
    "The package SHALL provide a `MVPConfig` frozen dataclass whose locked constants equal: "
    "`d_model == 1024`, `N_e == 16`, `k == 2`, `d_ffn == 2048`, `L == 4`, `d_ffn_dense == 4096`, "
    "`d_c == 16`, `H_kv == 8`, `d_k == 128`, `\u03b2_initial \u2248 1.035` (per wayfinder `Req 7` "
    "\"Isotropic Squared-Chord Distance And Bounded Beta\" (`#req-7`) closed-form "
    "`\u03b2_0 = 0.1 + 31.9\u00b7\u03c3(\u03b3_init)` with `\u03b3_init \u2248 \u22123.5`; 50-digit mpmath "
    "`\u03b2_0 = 1.0350601609682665718`). Attempting to mutate any field SHALL raise "
    "`dataclasses.FrozenInstanceError`. A factory function `MVPConfig()` SHALL return an instance "
    "with all default values.",
    "sk/req-21-l505",
)
SK_REQ21 = sk_fix(
    SK_REQ21,
    "spec req-7 L130 closed-form anchor",
    "**MVPConfig carries only GEOMETRIC constants** (model shape: `d_model`, `N_e`, `k`, `d_ffn`, "
    "`L`, `d_ffn_dense`, `d_c`, `H_kv`, `d_k`, `vocab_size`) **plus the specific initial value "
    "`\u03b2_initial \u2248 1.035`** (narrative 4-sig-fig; wayfinder `Req 7` "
    "\"Isotropic Squared-Chord Distance And Bounded Beta\" (`#req-7`) closed-form anchor). The "
    "algorithmic range constants `\u03b2_min = 0.1` and `\u03b2_max = 32` live as module-level "
    "`Final[float]` in `decompmoe/beta.py` (NOT in MVPConfig), per `design.md` Decision 1: "
    "\"Algorithmic constants live with their usage site\". MVPConfig does not carry `\u03b2_min` or "
    "`\u03b2_max` fields, and the canonical sources for those constants are `decompmoe.beta.BETA_MIN` "
    "and `decompmoe.beta.BETA_MAX`.",
    "sk/req-21-l507",
)
SK_REQ21 = sk_fix(
    SK_REQ21,
    "per spec req-7 L123 Sigmoid",
    "- **AND** the test does NOT degenerate to a self-referential check (i.e., "
    "`MVPConfig().beta_initial \u2248 literal_value`); the closed form MUST be derived from "
    "`\u03b2_min + (\u03b2_max\u2212\u03b2_min)\u00b7\u03c3(\u03b3_init)` per wayfinder `#req-7` Sigmoid "
    "\u95ed\u5f0f",
    "sk/req-21-l530",
)

# req-18: Source field code pointer `src/decompmoe/safeguards.py:71-80`
SK_REQ18 = sk_fix(
    get_block(sk, "req-18"),
    "signature mirrors `src/decompmoe/safeguards.py:71-80` at commit `d3689a1`",
    "**Source:** `wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent); change `fix-openspec-doc-bugs` design.md (Decision 7 \u2014 threshold parameterization `1/(2\u00b7N_e)`); signature mirrors `safeguards.py::clip_global_grad_norm_` as of commit `d3689a1`.",
    "sk/req-18-l434",
)

# req-23: the `L504` / `L394-466` / `L560-563` / `L450` cross-mirror pointers
SK_REQ23 = sk_fix(
    get_block(sk, "req-23"),
    "L504 enumerates",
    "  - The closed-form table enumerates `L_sep`, `R_H`, `S_load`, `UR`, `SP`, `D_chord`, "
    "`MCI`, `CG` — the same 8 metric names wayfinder `Req 20` \"Eight Geometric Quantification "
    "Metrics\" (`#req-20`) defines",
    "sk/req-23-l630",
)
SK_REQ23 = sk_fix(
    SK_REQ23,
    "L500-518 each closed-form matches",
    "  - Each closed-form matches the corresponding wayfinder `#req-20` row verbatim (post-229016fe "
    "+ 09-22 line-drift correction)",
    "sk/req-23-l631",
)
SK_REQ23 = sk_fix(
    SK_REQ23,
    "(L560-563, abs=1e-12)",
    "- `decompmoe-skeleton` Requirement `<a id=\"req-22\">` also defines "
    "`MCI closed-form on uniform token distribution` and "
    "`MCI closed-form on rank-1 token distribution` Scenarios (both `abs=1e-12`) — these mirror "
    "the two corresponding Scenarios under wayfinder `#req-20` verbatim",
    "sk/req-23-l633",
)
SK_REQ23 = sk_fix(
    SK_REQ23,
    "wayfinder spec.md L413 owns the MCI closed-form",
    "**Source:** `wayfinder/tickets/A8-2.md` (cycle-12 finding 1 evidence — wayfinder `#req-20` "
    "owns the MCI closed-form; this capability's metric table is a verbatim mirror and is already "
    "flagged as a drift hazard)",
    "sk/req-23-l637",
)
SK_REQ23 = sk_fix(
    SK_REQ23,
    "- **AND** L560-563 `MCI closed-form on uniform",
    "- **AND** the `MCI closed-form on uniform token distribution` and `MCI closed-form on rank-1 "
    "token distribution` Scenarios use `abs=1e-12` (mirroring the two corresponding Scenarios under "
    "wayfinder `#req-20`) — both endpoints of the declared `[1/d_c, 1]` range are guarded",
    "sk/req-23-l643",
)

# req-16: add the AC-63 named guard Scenario
SK_REQ16 = get_block(sk, "req-16")
SK_REQ16 = substitute_line(
    SK_REQ16,
    "These are the **semantic counterpart** to Requirement \"Hard-Constraint Grep Invariants\"",
    "These are the **semantic counterpart** to Requirement \"Hard-Constraint Grep Invariants\" "
    "and are the landing site for the two invariants that req-15 removed from grep scope",
    "sk/req-16-intro",
)

SK_REQ16.append("")
SK_REQ16.append("#### Scenario: Voronoi closed form is not the arctan shortcut")
SK_REQ16.append("")
SK_REQ16.append(
    "- **WHEN** `canonical_voronoi_angle(N_e, d_c)` is evaluated at the MVP point "
    "`(N_e = 16, d_c = 16)`"
)
SK_REQ16.append(
    "- **THEN** it returns the root of the defining equation "
    "`\u00bd \u00b7 I_{sin\u00b2\u03b8}((d_c \u2212 1)/2, 1/2) = 1/N_e`, which is "
    "`0.665773750028 rad` **NOT** \u2014 the forbidden token "
    "`arctan(pi / sqrt(d_c))` evaluates to `0.665773750028 rad` at `d_c = 16`, i.e. "
    "`38.146026\u00b0`, and MUST NOT be the implementation's closed form"
)
SK_REQ16.append(
    "- **AND** the returned value MUST satisfy "
    "`pytest.approx(1.173547, abs=1e-6)` (the 6dp spec literal, per governance req-gov-1 "
    "obligation 3) with the actual value embedded in the failure message as `f\"actual={...}\"`"
)
SK_REQ16.append(
    "- **AND** a substitution of the forbidden token MUST move the result outside that tolerance by "
    "at least `1e5` times (measured: `5.078e-01` absolute error at `N_e = 16`, i.e. "
    "`507_773\u00d7` the `abs=1e-6` tolerance), so the guard discriminates rather than merely passing"
)
SK_REQ16.append(
    "- **AND** the residual frame is named: "
    "`|\u00bd\u00b7I_{sin\u00b2\u03b8}(7.5, 1/2) \u2212 1/16| < 1e-9` measured against the "
    "implementation-internal reference `src/decompmoe/sphere.py::_betainc_regularized`"
)
SK_REQ16.append(
    "- **AND** this Scenario is the guard that Requirement \"Hard-Constraint Grep Invariants\" "
    "refers to when it states the removed invariants are enforced here; the referenced name MUST be "
    "`test_canonical_voronoi_angle_not_arctan_shortcut`"
)

# --------------------------------------------------------------------------
# governance
# --------------------------------------------------------------------------

# --- req-36: restore the two per-annotation ticket Scenarios that the thin
# --- pointer initially merged away. Each A8-2 annotation is verified
# --- independently today, so merging them would drop a guard.
SK_TICKET_SCENARIOS = [
    "#### Scenario: ticket A8-2 centered-covariance supersede annotation preserved",
    "",
    "- **WHEN** the A8-2 section carrying the `\u03bb_j = C \u5206\u5e03\u534f\u65b9\u5dee\u77e9\u9635\u7684\u7279\u5f81\u503c` "
    "historical definition attempt is read",
    "- **THEN** that section preserves its original wording verbatim AND is immediately followed by an "
    "italic `(historical, centered-covariance reading; superseded by spec req-20 uncentered second "
    "moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 "
    "design.md Decision 5 \u2014 the centered reading has a `(1/d_c, 1]` upper endpoint that is "
    "unreachable at `|T| = d_c`)` annotation",
    "",
    "#### Scenario: ticket A8-2 convex-hull-radius supersede annotation preserved",
    "",
    "- **WHEN** the A8-2 section carrying the `\u539f CV\uff08C \u5206\u5e03\u51f8\u5305\u534a\u5f84\uff09` historical "
    "reading is read",
    "- **THEN** that section preserves its original wording verbatim AND is immediately followed by an "
    "italic `(historical, geometric convex hull radius CV reading; superseded by spec req-20 "
    "uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + "
    "fix-math-consistency-audit-2026-08 design.md Decision 5 \u2014 the `1/d_c` lower bound of CV on "
    "`S^{d_c\u22121}` makes the original `< 0.05` health target unreachable)` annotation",
    "",
    "#### Scenario: the two ticket annotations jointly cover the req-20 Reason argument",
    "",
    "- **WHEN** both A8-2 supersede annotations are read together",
    "- **THEN** they jointly cover both clauses of the `#req-20-mci` Reason supersede argument, and "
    "both name the **same** supersession target and the **same** chain of authority",
]
for _l in SK_TICKET_SCENARIOS:
    WF_REQ36.append(_l)


GV = "governance"
gv = load_spec(GV)

# --- MODIFIED: the ticket supersede annotation pattern (drop the mandated L###) ---
GV_TICKET = get_block(gv, "req-gov-2")
GV_TICKET = replace_line(
    GV_TICKET,
    "The system SHALL treat the ticket `(historical,",
    "The system SHALL treat the ticket `(historical, <original reading>; superseded by spec req-N "
    "<Requirement title> (`#req-N`) via <change> Decision M)` annotation pattern, when appended to "
    "`wayfinder/tickets/A8-2.md` (or any other wayfinder ticket lineage entry), as a **CLAUDE.md \u00a73 "
    "source-field rules application** \u2014 the annotation verbatim references the spec requirement "
    "anchor (`req-N` plus its `#req-N` anchor and title), the wayfinder ticket (`<ID>.md`), and the "
    "spec-end chain-of-authority decisions (`<change> Decision M`). The line-addressed form "
    "`(historical, <original reading>; superseded by spec req-N L### via <change> Decision M)` is "
    "**legacy**: annotations already carrying it stay as written (they are historical lineage "
    "records and rewriting them would corrupt the audit trail), but no NEW annotation may use it. "
    "This pattern is enforced by `scripts/lint_no_source_field_drift.py` (per CLAUDE.md \u00a73 "
    "\"Source reverse-link\" rules) and, for the line-addressed form, rejected by "
    "`scripts/lint_no_line_pointers.py` check C1 on any NEW annotation. It matches the existing "
    "source-field convention established by `req-gov-1` Policy lineage.",
    "gov/req-gov-2",
)
GV_TICKET = sk_fix(
    GV_TICKET,
    "each annotation contains the canonical pattern verbatim",
    "- **THEN** each annotation contains the canonical pattern verbatim: `(historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)` \u2014 3 reverse-links complete (ticket + spec anchor + change Decision), backtick-wrapped, with the spec anchor (`wayfinder/tickets/A6a-2.md` for the wayfinder ticket-side lineage); the line-addressed variant `req-N L###` is legacy and MUST NOT appear in a NEW annotation",
    "gov/req-gov-2-scenario",
)
for _l in [
    "",
    "#### Scenario: Ticket A8-2 centered-covariance supersede annotation preserved",
    "",
    "- **WHEN** the A8-2 section carrying the `\u03bb_j = C \u5206\u5e03\u534f\u65b9\u5dee\u77e9\u9635\u7684\u7279\u5f81\u503c` "
    "historical definition attempt is read",
    "- **THEN** that section preserves its original wording verbatim AND is immediately followed by "
    "an italic `(historical, centered-covariance reading; superseded by spec req-20 uncentered second "
    "moment via fix-openspec-doc-bugs design.md Decision 8 + fix-math-consistency-audit-2026-08 "
    "design.md Decision 5 \u2014 the centered reading has a `(1/d_c, 1]` upper endpoint that is "
    "unreachable at `|T| = d_c`)` annotation",
    "",
    "#### Scenario: Ticket A8-2 convex-hull-radius supersede annotation preserved",
    "",
    "- **WHEN** the A8-2 section carrying the `\u539f CV\uff08C \u5206\u5e03\u51f8\u5305\u534a\u5f84\uff09` historical reading is read",
    "- **THEN** that section preserves its original wording verbatim AND is immediately followed by an "
    "italic `(historical, geometric convex hull radius CV reading; superseded by spec req-20 "
    "uncentered second moment via fix-openspec-doc-bugs design.md Decision 8 + "
    "fix-math-consistency-audit-2026-08 design.md Decision 5 \u2014 the `1/d_c` lower bound of CV on "
    "`S^{d_c\u22121}` makes the original `< 0.05` health target unreachable)` annotation",
    "",
    "#### Scenario: the two A8-2 annotations jointly cover the req-20 Reason argument",
    "",
    "- **WHEN** both A8-2 supersede annotations are read together",
    "- **THEN** they jointly cover both clauses of the `wayfinder` `#req-20-mci` Reason supersede "
    "argument \u2014 the `(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c` for the centered "
    "reading, and the `1/d_c` lower bound on `S^{d_c\u22121}` making the original `< 0.05` health "
    "target unreachable for the CV reading",
    "- **AND** both name the **same** supersession target and the **same** chain of authority",
]:
    GV_TICKET.append(_l)


# --- MODIFIED: req-gov-4 clause 4(a) ---
GV_ADVISORY = get_block(gv, "req-gov-4")
GV_ADVISORY = replace_line(
    GV_ADVISORY,
    "superseded by spec req-N L### via <change> Decision M)",
    "4. **Drift remediation protocol** \u2014 when ticket stale is detected propagating to `src/`: "
    "(a) ticket MUST receive a `(historical, <original reading>; superseded by spec req-N "
    "<Requirement title> (`#req-N`) via <change> Decision M)` annotation preserving the decision "
    "chain (canonical form per `openspec/specs/wayfinder/spec.md` req-34 \"Source Field Format "
    "Invariant for OpenSpec Specs\" Scenario \"every Source field contains a wayfinder ticket "
    "reference\"; the line-addressed `req-N L###` variant is legacy and MUST NOT be newly written); "
    "(b) `src/` default values MUST be updated to spec canonical values; (c) tests using "
    "`assert == stale_value` MUST migrate to `pytest.approx(spec_value, abs=...)` per "
    "`CLAUDE.md` \u00a76 \u7b2c 8 \u6761 float closed-form convention (formalized by `req-gov-1`).",
    "gov/req-gov-4",
)

# --- ADDED: the cross-reference anchor contract itself ---
GV_ADDED = """<a id="req-gov-6"></a>

### Requirement: Cross-Reference Anchor Contract

The system MUST NOT use raw line numbers as the identity of a cross-reference in any peer spec
under `openspec/specs/**`, in `src/**`, or in `tests/**`. A reference MUST resolve through a
mechanically checkable identifier instead. This Requirement exists because the absence of such a
rule let the same defect family be "fixed" five times by hand, each pass leaving siblings behind.

1. **Permitted reference forms.**

   | Target | Required form | Example |
   |---|---|---|
   | a whole Requirement | `Req N` / `req-N` / `` `#req-N` `` plus the Requirement title | `` `Req 13` Numerical Safeguards (`#req-13`) `` |
   | a table row or field block | a block-level `<a id="req-N-slug"></a>` anchor, referenced as `` `#req-N-slug` `` | `` `#req-20-mci` `` |
   | a code symbol | `module.py::symbol` | `` `safeguards.py::beta_saturation_warning` `` |
   | a test | `file::test_name` | `` `test_sphere.py::test_voronoi_canonical_N_e_dependence` `` |
   | a prose passage | Requirement number + title + a verbatim quotation of at least 8 characters | the quotation itself is greppable |

2. **Block-anchor minting rule.** A block-level anchor MUST be minted only for a target with **at
   least 2 inbound references**, established by a recorded inbound-reference census rather than by
   judgement. A target with a single inbound reference MUST instead use the Requirement number plus
   a row label or symbol name. This bounds anchor growth: each anchor is a maintenance obligation
   that must be re-checked on every rename of the thing it labels.

3. **Anchor uniqueness and namespace hygiene.** Within a single spec file every `id` MUST be
   unique, and every `### Requirement:` heading MUST be immediately preceded by its
   `<a id="req-N"></a>` anchor. An anchor literal quoted inside prose or inside a code span MUST NOT
   appear in a Requirement body \u2014 a quoted literal still occupies the id namespace when the
   document is parsed, and two Requirements sharing an id makes every anchor reference ambiguous.

4. **Resolvability.** Every `req-N`, `#req-N`, and `#req-N-slug` reference in a peer spec, in
   `src/**`, or in `tests/**` MUST resolve to an anchor that exists in the named capability.

5. **Enforcement.** `scripts/lint_no_line_pointers.py` MUST implement checks C1 (no line-number
   reference), C2 (anchor uniqueness and coverage), C3 (no anchor literal inside a code span), and
   C4 (reference resolvability), and MUST exit non-zero on any violation. It MUST be run as part
   of the `/opsx:archive` precondition alongside the existing two lint gates, per `CLAUDE.md` \u00a73.

6. **Historical-citation exemption.** A line-number reference that records history \u2014 a
   superseded coordinate, a pre-change location, or a prior-commit citation \u2014 is exempt from
   C1 when the line carries an explicit historical marker (`pre-this-change`, `histor`, the
   original-language marker, a prior commit id, `was`, `before`, or an explicit move arrow). The
   exemption is by marker, not by a registry of exempted files, so that the exemption surface
   stays visible in the document itself.

7. **Archive copies are out of scope.** `openspec/changes/**` is NOT scanned. An archived change is
   the historical record of what a past change did; retro-editing it would falsify that record. A
   pointer introduced by a change is corrected in the live spec by the change that closes it.

**Source:** `CLAUDE.md` \u00a73 (source reverse-link rules and archive preconditions), `CLAUDE.md` \u00a76
(anchor coverage requirement), change
`2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract` design.md (Decisions D1-D8)

#### Scenario: a line-number reference is rejected

- **WHEN** a peer spec, `src/**` file, or `tests/**` file contains a line-number cross-reference
  such as `<capability> L<line>`, `req-<N> L<line>`, `<capability> L<first>-L<last>`, `line <number>`, or
  `<module>.py:<line>` that is not an exempt historical citation
- **THEN** `scripts/lint_no_line_pointers.py` MUST report a violation naming the file, the line,
  and the matched reference
- **AND** the lint MUST exit non-zero
- **AND** the reference MUST be rewritten to one of the permitted forms in clause (1)

#### Scenario: a technical label is not a line reference

- **WHEN** a document uses `L` followed by a digit as a technical label, for example `d_c[L2-step2]`
  or `L4-postmean`, where the digits denote a layer or step rather than a line
- **THEN** `scripts/lint_no_line_pointers.py` MUST NOT report it
- **AND** the label MUST remain greppable as its own token

#### Scenario: a single-reference target does not earn a block anchor

- **WHEN** the inbound-reference census reports exactly 1 inbound reference for a target
- **THEN** no block-level anchor MUST be minted for it
- **AND** the referring site MUST name the Requirement plus a row label or symbol name instead

#### Scenario: a quoted anchor literal is rejected

- **WHEN** a Requirement body contains an anchor literal inside prose or inside a code span, for
  example `` `<a id="req-20"></a>` ``
- **THEN** `scripts/lint_no_line_pointers.py` MUST report a C3 violation
- **AND** the id namespace of that spec MUST remain free of the duplicate
- **AND** the body MUST reference the target by `` `#req-20` `` plus its title instead

#### Scenario: the lint discriminates against the pre-change tree

- **WHEN** `scripts/lint_no_line_pointers.py` is evaluated against the repository state before this
  change
- **THEN** it MUST report C1 violations and exit non-zero
- **AND** it MUST report green only against the post-change state, so that a silently-passing
  check is itself detectable
"""


def main() -> None:
    out = {
        "wayfinder": build(
            WF,
            removed=[WF_REMOVED],
            reqs={
                "req-2": WF_REQ2,
                "req-6": WF_REQ6,
                "req-13": WF_REQ13,
                "req-20": WF_REQ20,
                "req-32": WF_REQ32,
            },
        ),
        "decompmoe-skeleton": build(
            SK,
            {"req-16": SK_REQ16, "req-18": SK_REQ18, "req-21": SK_REQ21, "req-23": SK_REQ23},
        ),
        "governance": build(
            GV,
            {"req-gov-2": GV_TICKET, "req-gov-4": GV_ADVISORY},
            added=[GV_ADDED],
        ),
    }

    total = 0
    for cap, text in out.items():
        p = CHANGE / "specs" / cap / "spec.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print("wrote %s (%d chars)" % (p.relative_to(REPO), len(text)))

    print()
    print("=== block-level diff verification (delta vs live spec) ===")
    live = {WF: wf, SK: sk, GV: gv}
    for cap, reqs in (
        (WF, ["req-2", "req-6", "req-13", "req-20", "req-32"]),
        (SK, ["req-16", "req-18", "req-21", "req-23"]),
        (GV, ["req-gov-2", "req-gov-4"]),
    ):
        for r in reqs:
            total += verify(cap, r, get_block(live[cap], r), out[cap].split("\n"))
    print()
    print("total changed lines across all blocks =", total)


if __name__ == "__main__":
    main()
