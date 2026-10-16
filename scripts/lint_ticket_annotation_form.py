#!/usr/bin/env python3
"""Gate the FORM of `(historical, ...)` supersede annotations in wayfinder tickets.

Why this exists
---------------
`openspec/specs/governance/spec.md` `req-gov-2` declares a canonical form for
the ticket annotation

    (historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)

and `req-gov-4` clause (4)(a) makes that annotation MANDATORY whenever a ticket
value is superseded and the staleness propagates to `src/`. The obligation had
no machine check: `scripts/lint_no_line_pointers.py` declares

    SCAN_ROOTS = ("openspec/specs", "src", "tests")

so `wayfinder/tickets` was never scanned by any lint. The capability existed in
`scripts/pointer_scan.py` (`RE_TICKET_L`, the clause-level historical-marker
rules); it was simply never pointed at the ticket tree. This lint closes that
gap, reusing pointer_scan rather than reimplementing marker semantics.

Scope: FORM ONLY (change 2026-10-10 design.md Decision 2)
---------------------------------------------------------
Given that an annotation exists, is it canonical? Two codes, with DIFFERENT
force - see "Two-tier enforcement" below:

  V-ANCHOR    the `superseded by spec req-N` clause lacks its `(#req-N)` anchor
  V-DECISION  a `... Decision N` citation names a change that does not exist

Deliberately NOT asserted:

  * EXISTENCE - "every ticket must carry at least one annotation". 18
    annotations live across 7 of 23 tickets and nothing states which tickets
    *should* have one, so an existence rule would encode a judgment call as a
    red gate.
  * DRIFT - "a value superseded in spec must have a matching annotation here".
    That needs a spec<->ticket association key that does not exist.
  * WHICH Decision - whether the cited Decision number is the one that
    actually produced the supersession. See below; it is unsound.

Two-tier enforcement
---------------------
V-ANCHOR blocks. V-DECISION as originally drafted ("the annotation MUST name
`<change> Decision M`") does NOT, and the reason is evidence, not caution.

Reconstructing provenance for the 9 corpus annotations that carry no decision
citation was attempted and failed: the beta_0 closed form was written by 19
archived deltas, `req-22`'s anchor is duplicated across two capabilities, and
`req-32` was touched by 5 changes. Worse, one citation that ALREADY passes
this shape is provably wrong - `wayfinder/tickets/A4-1.md` cites
`fix-math-consistency-audit-2026-08 Decision 1` for the beta_0 supersession,
and that Decision's body contains no beta term at all (it is the Voronoi
52 deg -> 67.24 deg decision). Demanding a Decision number as a red gate
would ratify a citation style already known to carry mis-attributions.

So V-DECISION is narrowed to what is objectively checkable: **a cited change
must name a change that actually exists**. That catches invented provenance,
which is the real failure mode, and asks for nothing the artifacts cannot
support. An annotation with no citation at all is reported in the summary
count but does not fail the gate.

Legacy grandfathering
----------------------
`req-gov-2` makes the line-addressed form
`(historical, ...; superseded by spec req-N L### via <change> Decision M)`
LEGACY: "annotations already carrying it stay as written (they are historical
lineage records and rewriting them would corrupt the audit trail)". Such an
annotation is therefore exempt from V-ANCHOR. It is still checked for its
Decision chain, because the legacy definition itself names one. Measured in the
live tree: 0 legacy annotations.

NO exemption table
------------------
Mirrors `pointer_scan.py`: no `JUSTIFIED_EXEMPTIONS`, no per-line `# noqa`, no
env var, no CLI flag. A grandfather list would rot as lines drift. The corpus is
normalized in the same change that lands the gate, so it is green on arrival.

Like `lint_no_line_pointers.py`, this lint never reports its own fixtures.
"""
from __future__ import annotations

import contextlib
import re
import sys
from pathlib import Path
from typing import Iterable, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pointer_scan as _ps  # noqa: E402

SCAN_ROOT = "wayfinder/tickets"
SCAN_SUFFIX = (".md",)

#: Opening token of a supersede annotation. `historical` is the canonical
#: marker; `pointer_scan.HISTORICAL_MARKERS` also admits `historically`,
#: `formerly`, `pre-edit` etc., but only `historical` opens a ticket
#: supersede annotation under `req-gov-2`.
RE_ANNOTATION_START = re.compile(r"\(historical,")

#: `(#req-13)` / `(#req-20-mci)` - the anchor the canonical form requires.
RE_ANCHOR = re.compile(r"\(#req-[0-9A-Za-z][0-9A-Za-z-]*\)")

#: A chain-of-authority citation, in any of the three spellings the corpus uses:
#:
#:   via `change-name` design.md Decision 8
#:   via `change-name` design.md (Decision 2)
#:   via change change-name Decision 1
#:   `prior-change` design.md Decision 5 + `later-change` design.md Decision 6
#:        (a continuation citation after `+`, with no second `via` — see A8-2)
#:
#: The captured group is a candidate CHANGE NAME. The `via ... ` prefix is
#: OPTIONAL so a continuation citation is still seen; the shape test that
#: separates a real slug from prose ("see Decision 3") lives in
#: `cited_changes`, which consults `known_change_slugs()` rather than guessing
#: from the token alone.
RE_DECISION_CITATION = re.compile(
    r"(?:via\s+(?:change\s+)?)?`?([A-Za-z0-9][\w.]*(?:-[\w.]+)*)`?\s*"
    r"(?:design\.md\s*)?\(?\s*Decision\s+\d+"
)

#: The grandfathered line-addressed form, e.g. `superseded by spec req-13 L500`.
RE_LEGACY_LINE_FORM = re.compile(r"superseded by spec req-[0-9A-Za-z-]+\s+L\d{1,4}\b")

SELF_TEST_PATTERNS = _ps.SELF_EXCLUDE

#: Archive directories carry a `YYYY-MM-DD-` prefix; annotations cite the bare
#: slug. Normalised away before comparing the two.
_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "openspec").is_dir() and (parent / "wayfinder").is_dir():
            return parent
    return Path(__file__).resolve().parent.parent


_REPO_ROOT = _repo_root()


def is_self_test(path: Path) -> bool:
    """True for the gates' own test suites, whose content is synthetic by design.

    Prefix-matched, NOT substring-matched. `pointer_scan.py:790-793` records
    that a substring test once swallowed `docs/scripts/lint_notes.md` and
    `openspec/specs/wayfinder/scripts/lint_x.md`; every `SELF_EXCLUDE` entry is
    prefix-shaped, so `startswith` is both sufficient and strictly safer.
    """
    try:
        rel = path.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        rel = path.as_posix().replace("\\", "/")
    return any(rel.startswith(pat) for pat in SELF_TEST_PATTERNS)


def annotation_span(text: str, start: int, mask: bytearray | None = None) -> tuple[int, int] | None:
    """Return `(begin, end)` of the annotation opening at `start`.

    Parens are BALANCED rather than matched by a non-greedy regex, because the
    canonical anchor `(#req-N)` nests a paren inside the annotation: a
    `\\(.*?\\)` pattern would cut the annotation off at the anchor and the
    Decision citation would fall outside the extracted span.

    Parens inside Markdown code spans are NOT counted, via
    `pointer_scan.code_span_mask`. Real annotations quote math that is
    deliberately unbalanced - `wayfinder/tickets/A8-2.md:70` carries
    `` `(1/d_c, 1]` ``, an interval closed with a square bracket. A naive depth
    counter never returns to 0 there, so the whole annotation is silently
    dropped and goes unchecked, which is the one failure a form gate must not
    have. Quoted material is not structure.

    The mask handles runs of N backticks rather than counting single
    backticks, which is what a hand-rolled `in_code = not in_code` toggle gets
    wrong: a double-backtick span contributes four backticks, so its contents
    read as OUTSIDE a span and a second unbalanced paren escapes detection.

    `mask` is the output of `code_span_mask(text)`; pass it in to avoid
    recomputing once per annotation.

    Returns `None` when the closing paren never arrives.
    """
    if not text.startswith("(historical,", start):
        return None
    if mask is None:
        mask = _ps.code_span_mask(text)
    depth = 0
    for idx in range(start, len(text)):
        if mask[idx]:
            continue
        ch = text[idx]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return start, idx + 1
    return None


def find_annotations(text: str) -> list[tuple[int, int, str]]:
    """Every `(historical, ...)` annotation in `text`, as `(begin, end, body)`.

    Scans the WHOLE text, not line by line, so an annotation that a hard wrap
    split across two lines is still located. `lint_text` derives line numbers
    from these offsets, so counting and enforcement read the same spans.
    """
    mask = _ps.code_span_mask(text)
    out: list[tuple[int, int, str]] = []
    for match in RE_ANNOTATION_START.finditer(text):
        span = annotation_span(text, match.start(), mask)
        if span is None:
            continue
        out.append((span[0], span[1], text[span[0]:span[1]]))
    return out


def known_change_slugs() -> set[str]:
    """Change slugs that exist, with any `YYYY-MM-DD-` date prefix stripped.

    Archive directories are date-prefixed (`2026-08-23-fix-openspec-doc-bugs`)
    while annotations cite the bare slug (`fix-openspec-doc-bugs`), so the
    prefix is normalised away on both sides before comparison.
    """
    slugs: set[str] = set()
    for base in (_REPO_ROOT / "openspec" / "changes" / "archive",
                 _REPO_ROOT / "openspec" / "changes"):
        if not base.is_dir():
            continue
        for entry in base.iterdir():
            if not entry.is_dir() or entry.name == "archive":
                continue
            slugs.add(_DATE_PREFIX.sub("", entry.name))
            slugs.add(entry.name)
    return slugs


def cited_changes(annotation: str, known: set[str] | None = None) -> list[str]:
    """Change names the annotation attributes its supersession to.

    A captured token is treated as a citation when it either resolves to a
    real change slug, or is slug-SHAPED (contains a hyphen) but resolves to
    nothing - the latter is a fabricated provenance and must be reported. A
    hyphen-free token that is not a known slug is prose (`see Decision 3`) and
    is ignored.

    KNOWN RESIDUAL: a fabricated change name without a hyphen would not be
    reported. That is unreachable for this repository — every slug under
    `openspec/changes/` contains a hyphen, which
    `test_every_real_change_slug_contains_a_hyphen` asserts rather than
    assumes, so the invariant cannot silently rot.
    """
    if known is None:
        known = known_change_slugs()
    out: list[str] = []
    for m in RE_DECISION_CITATION.finditer(annotation):
        name = m.group(1)
        if name in known or "-" in name:
            out.append(name)
    return out


def check_annotation(annotation: str, known: set[str] | None = None) -> list[str]:
    """Violation reasons for one annotation body."""
    if known is None:
        known = known_change_slugs()
    reasons: list[str] = []

    # `req-gov-2` grandfathers the line-addressed form verbatim, so an
    # annotation in that shape is not asked for the `(#req-N)` anchor.
    legacy = RE_LEGACY_LINE_FORM.search(annotation) is not None
    if not legacy and RE_ANCHOR.search(annotation) is None:
        reasons.append(
            "V-ANCHOR: the `superseded by spec req-N` clause carries no "
            "`(#req-N)` anchor (req-gov-2 canonical form)"
        )

    # Only the EXISTENCE of a cited change is asserted. Which Decision produced
    # the supersession is not checkable from the artifacts - see the module
    # docstring's "Two-tier enforcement".
    for name in cited_changes(annotation):
        if name not in known:
            reasons.append(
                f"V-DECISION: cites change `{name}`, which is not an existing "
                f"change under `openspec/changes/archive/`"
            )
    return reasons


def check_line(line: str, known: set[str] | None = None) -> list[str]:
    """Violation reasons for a single line."""
    reasons: list[str] = []
    for _, _, body in find_annotations(line):
        reasons.extend(check_annotation(body, known))
    return reasons


def iter_lines(paths: Iterable[Path]) -> Iterator[tuple[Path, int, str]]:
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                yield path, line_no, line.rstrip("\n")


def _line_of(text: str, offset: int) -> tuple[int, str]:
    """1-based line number and the stripped line containing `offset`."""
    line_no = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset) + 1
    line_end = text.find("\n", offset)
    if line_end == -1:
        line_end = len(text)
    return line_no, text[line_start:line_end].strip()


def lint_text(path: Path, text: str, known: set[str] | None = None) -> list[tuple[Path, int, str, str]]:
    """Violations in `text`, as `(path, line_no, content, reason)`.

    THE single enforcement path. `lint_file` and `main` both route through here
    so that the annotation count reported by `main` and the violations actually
    enforced always describe the same span set.

    This previously walked line by line while `main` counted over the whole
    document. An annotation split by a hard wrap matched neither line, so it
    was silently unchecked, yet `main` still counted it and printed
    "N annotation(s), no violations" with exit 0 - a fabricated change name
    inside a wrapped annotation escaped the gate while the report claimed the
    annotation had been examined.
    """
    out: list[tuple[Path, int, str, str]] = []
    for begin, _, body in find_annotations(text):
        line_no, line = _line_of(text, begin)
        for reason in check_annotation(body, known):
            out.append((path, line_no, line, reason))
    return out


def lint_file(path: Path, known: set[str] | None = None) -> list[tuple[Path, int, str, str]]:
    """Violations in one file, as `(path, line_no, content, reason)`."""
    if is_self_test(path):
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    return lint_text(path, text, known)


def collect_paths(args: list[str]) -> list[Path]:
    """Resolve CLI positional args to scanned files; walk the ticket root if empty."""
    if args:
        return [Path(a) for a in args if not is_self_test(Path(a))]
    base = _REPO_ROOT / SCAN_ROOT
    if not base.exists():
        return []
    return [
        p for p in sorted(base.rglob("*"))
        if p.is_file() and p.suffix in SCAN_SUFFIX and not is_self_test(p)
    ]


def main(argv: list[str] | None = None) -> int:
    # Ticket prose carries `−`, `∈`, `⇒`, `≡` and similar glyphs; a GBK console
    # would abort mid-report, turning a violation list into a crash — and a
    # crashed gate is indistinguishable from a green one. Degrade the glyph, not
    # the report. Same convention as `lint_no_line_pointers.main` and
    # `lint_no_baseline_counts.main`.
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8", errors="replace")

    args = list(sys.argv[1:] if argv is None else argv)
    paths = collect_paths(args)

    # Without this the run would report OK having examined nothing - the same
    # vacuous pass `lint_no_line_pointers.py` guards against.
    if not paths:
        print("lint_ticket_annotation_form: ABORT - no ticket file was found, "
              "so every check would pass vacuously.")
        print(f"  root: {SCAN_ROOT}")
        return 1

    violations: list[tuple[Path, int, str, str]] = []
    known = known_change_slugs()
    annotations = 0
    uncited = 0
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        # Counted and enforced from the SAME text through the SAME span set, so
        # the reported annotation count can never describe annotations the gate
        # did not look at.
        spans = find_annotations(text)
        annotations += len(spans)
        for _, _, body in spans:
            if not cited_changes(body, known):
                uncited += 1
        violations += lint_text(path, text, known)

    if not violations:
        print(
            f"lint_ticket_annotation_form: OK ({len(paths)} ticket file(s) "
            f"scanned, {annotations} annotation(s), no violations)"
        )
        # Reported, not enforced: see "Two-tier enforcement" in the docstring.
        print(f"  annotations citing no change/Decision (reported, not a gate): {uncited}")
        return 0

    print(f"lint_ticket_annotation_form: {len(violations)} violation(s) found")
    print()
    for path, line_no, content, reason in violations:
        print(f"  {path}:{line_no}: {reason}")
        print(f"    {content}")
    print(f"\n  annotations scanned: {annotations}")
    print(f"  annotations citing no change/Decision (reported, not a gate): {uncited}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
