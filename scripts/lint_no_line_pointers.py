#!/usr/bin/env python3
"""Lint gate: reject cross-references whose identity is a raw line number.

Background (`openspec/changes/2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract`):
    The same defect family was "fixed" by hand five times in this repository, each
    pass leaving siblings behind, because no check could say whether the fix was
    complete. A pointer census over `openspec/specs/**`, `src/**` and `tests/**`
    found 97 actionable line-number references across 14 files, while the audit
    list that motivated the work recorded only part of them.

    Line numbers are not a durable identity: a spec edit renumbers every
    coordinate after it, silently turning a correct citation into a wrong one.
    This script makes the replacement checkable.

Four independent checks:

  C1 — **No line-number reference.** A reference such as `<capability> L<line>`,
       `req-N L<line>`, `<module>.py:<line>` or `line <n>` is rejected unless the
       line carries an explicit historical marker. Technical labels where `L`
       means *layer* or *step* (`d_c[L2-step2]`, `L4-postmean`) are NOT pointers
       and are never reported. A bare `line <n>` with no capability token on the
       same line is reported but tagged `weak`, because the recall bias is
       deliberate: over-inclusion costs a line of triage, under-inclusion is how
       this family returned five times.

  C2 — **Anchor uniqueness and Requirement coverage.** Within a spec file every
       anchor `id` MUST be unique, and every `### Requirement:` heading MUST be
       immediately preceded — on the nearest non-empty line above it — by its
       anchor element. Judged on the nearest non-empty line rather than the
       literal previous line because the live specs place a blank line between
       the two for most Requirements.

  C3 — **No anchor element inside prose.** An anchor element quoted in a
       Requirement body still occupies the id namespace when the document is
       parsed, and two Requirements sharing an id makes every anchor reference
       ambiguous. The rule is stated as "an `<a id=` token on a line that is not
       a standalone anchor element" rather than as a specific element form,
       because the live tree contained a quoted anchor with NO closing tag that a
       well-formed-element pattern does not match.

  C4 — **Reference resolvability.** Every `req-N`, `#req-N` and `#req-N-slug`
       reference MUST resolve to an anchor that exists in the capability the
       reference names. The capability is taken from the capability word NEAREST
       the reference on the same line, falling back to the spec's own capability
       when the reference appears inside a spec file. A reference whose
       capability cannot be determined is counted and reported in the summary
       rather than silently skipped, so the uncovered surface stays visible.

Design constraints (mirroring `scripts/lint_no_source_field_drift.py`):
  - NO exemption table (not `JUSTIFIED_EXEMPTIONS`, not per-line `# noqa`, not
    env var, not CLI flag). The historical exemption is by *marker on the line*,
    so the reason stays visible in the document itself.
  - Self-contained: the C1 detector is a copy of the census classifier, not an
    import. The census lives under a change's `evidence/` directory, which
    `openspec archive` MOVES; an import across that boundary would break the gate
    on the very commit that archives it.
  - Content-based rules, so they survive line shifts without exemption rot.
  - `openspec/changes/**` is NOT scanned: an archived change is the historical
    record of what a past change did, and retro-editing it would falsify that
    record. A pointer introduced by a change is corrected in the live spec by
    the change that closes it.
  - Output goes to stdout; exit code 0 iff no violation, 1 otherwise.

Run as an archive precondition alongside the other two gates, per `CLAUDE.md` §3:
    python scripts/lint_no_line_pointers.py [PATH ...]
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

# C1's detector is shared with the census. `scripts/` is this file's own
# directory, so a plain import resolves whether the gate is run as a script,
# from the repo root, or imported by a test.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pointer_scan as _ps  # noqa: E402

SCAN_ROOTS = ("openspec/specs", "src", "tests")
SCAN_SUFFIX = (".md", ".py")
CAPABILITIES = ("wayfinder", "decompmoe-skeleton", "governance")

# The gates' own test suites assert on deliberately malformed text — a C1
# test must contain a real line-number reference for there to be anything to
# assert. Unlike `lint_no_source_field_drift.py`, which does not scan
# `tests/**` at all and so never met the problem, this gate must scan
# `tests/**`. So the exclusion is one rule about one class of file, stated
# here and pinned by a test, rather than a per-site exemption table:
# a lint never reports its own fixtures. The check is applied inside C1 and
# C4, not only during discovery, so it holds however the paths are spelled.
#
# Derived from the detector's own list rather than restated: the two tools
# once kept separate copies, they drifted, and the census then reported the
# detector and its guard tests as 43 actionable pointers. One definition.
SELF_TEST_PATTERNS = _ps.SELF_EXCLUDE

# --- C1 detector -------------------------------------------------------------
# C1 delegates to `scripts/pointer_scan.py`. The inline regexes that used to
# live here required whitespace immediately after the capability word:
#
#     \b(wayfinder|skeleton|decompmoe-skeleton|spec)\s+(?:spec\s+)?L?(\d{1,4})
#
# so `wayfinder/spec.md L83` (next char `/`) and
# ``` `wayfinder/tickets/A8-2.md` L70 ``` (next char a backtick) never
# matched, and this gate reported a clean tree over 75 live pointers. The
# module is shared with the census on purpose: a gate carrying its own
# detector will drift from the evidence again, and a gate importing one
# cannot. `pointer_scan.HISTORICAL_MARKERS` also refuses to fire on a token
# inside a code span, which is what stopped `governance/spec.md` from
# self-exemptifying on the word `historical` inside the template it
# documents.
#
# `RE_CAP_MENTION` stays local: C4's capability resolver needs it and it is
# not part of C1's semantics.
RE_CAP_MENTION = re.compile(
    r"\b(wayfinder|decompmoe-skeleton|skeleton|governance|spec)\b", re.IGNORECASE
)

# --- C2 / C3 -----------------------------------------------------------------
RE_ANCHOR = re.compile(r'<a id="([^"]+)"')
RE_HEADING = re.compile(r"^### Requirement:")

# --- C4 ----------------------------------------------------------------------
RE_REF_HASH = re.compile(r"#(req-[A-Za-z0-9_-]+)")
# `req-13` / `req-gov-1` keep their prefix verbatim. Capturing only the digits
# and rebuilding the id collapsed `req-gov-1` into `req-1`, which reported 34
# false violations in files that merely mention a governance Requirement.
RE_REF_PLAIN = re.compile(r"\b(req-(?:gov-)?\d+)\b")
# The prose form `Req 20` names a numeric Requirement, so its id is `req-<n>`.
RE_REF_WORD = re.compile(r"\bReq\.?\s*(\d+)\b")

CAPABILITY_WORDS = (
    ("decompmoe-skeleton", "decompmoe-skeleton"),
    ("skeleton", "decompmoe-skeleton"),
    ("wayfinder", "wayfinder"),
    ("governance", "governance"),
)

# A capability is most often named by a PATH, not a bare word:
# `openspec/specs/governance/spec.md req-gov-1 §4`. A path beats a bare word,
# because a bare word can be an ordinary adjective — `req-34 "governance-origin
# requirements trigger lint failure"` names wayfinder via the path that precedes
# it, while the nearest bare `governance` sits AFTER the reference inside the
# Scenario's own title.
RE_PATH_CAPABILITY = re.compile(r"(?:openspec/specs/)?([A-Za-z_][\w-]*)/spec\.md")

# Only the governance capability mints `req-gov-*` ids, so the id itself
# determines the capability. Structural, not an exemption list.
ID_PREFIX_CAPABILITY = {"req-gov-": "governance"}

# A qualifier (a capability word or a spec path) only qualifies the reference it
# IMMEDIATELY precedes. These delimiters end the reach of a qualifier.
QUALIFIER_BREAK = re.compile(r";|\breq-\w+\b|\bReq\.?\s*\d+\b|#req-[\w-]+")


def _qualifies(segment: str, rid: str = "") -> bool:
    """True when nothing in `segment` separates a qualifier from its reference.

    Without this, the path `governance/spec.md` reached 20 characters backwards
    across a clause boundary to qualify a `Req 11` that a nearer `` `wayfinder` ``
    word already owned: `... in openspec/specs/governance/spec.md req-gov-1 §3;
    `wayfinder` Req 11 states ...`. The path qualifies `req-gov-1`, not `Req 11`.

    `rid` is exempt from the break test: a citation routinely spells the same
    Requirement twice, as `wayfinder Req 13 Numerical Safeguards (#req-13)`, and
    the `Req 13` there is the same reference, not a boundary that ends the
    qualifier's reach.
    """
    if rid:
        num = re.fullmatch(r"req-(?:gov-)?(\d+)", rid)
        if num:
            same = rf"#?{re.escape(rid)}\b|\bReq\.?\s*{num.group(1)}\b"
        else:
            same = rf"#?{re.escape(rid)}\b"
        segment = re.sub(same, " ", segment, flags=re.IGNORECASE)
    return QUALIFIER_BREAK.search(segment) is None


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


_REPO_ROOT = _repo_root()


def has_historical_marker(text: str) -> bool:
    """True when `text` explicitly records history rather than pointing at live code.

    Delegates to the shared detector. The earlier version here carried its own
    copy of the marker list, and the two copies disagreed: `governance/spec.md`
    line 78 self-exemptified on the literal word `historical` occurring inside
    the very annotation template that line documents. One implementation, one
    behaviour.
    """
    return _ps.has_marker_anywhere(text)


def classify_pointer(line: str) -> tuple[list[int], bool] | None:
    """Return `(line_numbers, weak)` if `line` carries a line-number reference.

    Delegates to `scripts/pointer_scan.py`, which is the same module the
    census uses. The inline regexes this replaced required whitespace
    immediately after the capability word, so `wayfinder/spec.md L83` (next
    char `/`) and ``` `wayfinder/tickets/A8-2.md` L70 ``` (next char a
    backtick) never matched -- and the gate reported a clean tree over 75
    live pointers. A gate that carries its own detector will drift from the
    evidence again; a gate that imports one cannot.
    """
    sites = _ps.scan_line("<lint>", 1, line)
    if not sites:
        return None
    nums = []
    weak = True
    for s in sites:
        m = _ps.RE_NUM.search(s.detail)
        if m:
            nums.append(int(m.group(1)))
        if not s.weak:
            weak = False
    if not nums:
        return None
    return (sorted(set(nums)), weak)


def capability_of_spec(path: Path) -> str | None:
    """Return the capability name if `path` is one of the peer spec files.

    `openspec/specs/<capability>/spec.md` is FOUR path parts, and the capability
    is `parts[2]`. An earlier version compared against 3 and returned `parts[1]`,
    which made `capability_of_spec` return None for every spec file: the anchor
    inventory came out empty, so C4 rejected every reference in the tree, and C2
    and C3 were handed an empty spec list and passed vacuously. `main` now
    asserts the spec count, so that failure mode cannot be silent.
    """
    try:
        rel = path.resolve().relative_to(_REPO_ROOT)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) == 4 and parts[0] == "openspec" and parts[1] == "specs" \
            and parts[3] == "spec.md" and parts[2] in CAPABILITIES:
        return parts[2]
    return None


def spec_paths() -> list[Path]:
    return [_REPO_ROOT / "openspec" / "specs" / cap / "spec.md" for cap in CAPABILITIES]


def is_self_test(path: Path) -> bool:
    """True for the gates' own test suites, whose content is synthetic by design."""
    try:
        rel = path.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        rel = path.as_posix().replace("\\", "/")
    return any(pat in rel for pat in SELF_TEST_PATTERNS)


def collect_paths(args: list[str]) -> list[Path]:
    """Resolve CLI positional args to scanned files; walk the scan roots if empty."""
    if args:
        return [Path(a) for a in args]
    out: list[Path] = []
    for root in SCAN_ROOTS:
        base = _REPO_ROOT / root
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in SCAN_SUFFIX and not is_self_test(p):
                out.append(p)
    return out


def iter_lines(paths: Iterable[Path]) -> Iterator[tuple[Path, int, str]]:
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                yield path, line_no, line.rstrip("\n")


# --- C1 ----------------------------------------------------------------------
def check_c1(paths: Iterable[Path]) -> list[tuple[Path, int, str, str]]:
    out: list[tuple[Path, int, str, str]] = []
    for path, line_no, line in iter_lines(paths):
        # The self-test exclusion is an invariant of the CHECK, not of path
        # discovery. It used to live only in collect_paths, so running the
        # gate with explicit paths reported this file's own synthetic
        # fixtures -- 13 violations that exist only because of how the
        # paths were spelled.
        if is_self_test(path):
            continue
        if "http" in line:
            continue
        hit = classify_pointer(line)
        if hit is None:
            continue
        if has_historical_marker(line):
            continue
        nums, weak = hit
        tag = "weak " if weak else ""
        out.append((
            path, line_no, line.strip(),
            f"C1 {tag}line-number reference {nums} — cite a Requirement, "
            f"`module.py::symbol`, or a test as `file::test_name`",
        ))
    return out


# --- C2 / C3 -----------------------------------------------------------------
def check_spec_structure(specs: Iterable[Path]) -> list[tuple[Path, int, str, str]]:
    out: list[tuple[Path, int, str, str]] = []
    for path in specs:
        lines = path.read_text(encoding="utf-8").splitlines()
        ids: list[str] = []
        for i, line in enumerate(lines, start=1):
            for m in RE_ANCHOR.finditer(line):
                rid = m.group(1)
                ids.append(rid)
                stripped = line.strip()
                standalone = stripped.startswith(f'<a id="{rid}"') and stripped.endswith("</a>")
                if not standalone:
                    out.append((
                        path, i, stripped[:120],
                        f"C3 anchor element for id {rid!r} quoted in prose — a quoted "
                        f"element still occupies the id namespace; reference the "
                        f"target as `#{rid}` plus its title instead",
                    ))
        seen: dict[str, int] = {}
        for i, line in enumerate(lines, start=1):
            for m in RE_ANCHOR.finditer(line):
                rid = m.group(1)
                if rid in seen:
                    out.append((
                        path, i, line.strip()[:120],
                        f"C2 duplicate anchor id {rid!r} (first seen at line {seen[rid]})",
                    ))
                else:
                    seen[rid] = i
        for i, line in enumerate(lines):
            if not RE_HEADING.match(line):
                continue
            k = i - 1
            while k >= 0 and not lines[k].strip():
                k -= 1
            near = lines[k].strip() if k >= 0 else ""
            if not near.startswith('<a id="'):
                out.append((
                    path, i + 1, line.strip()[:120],
                    "C2 Requirement heading is not preceded by its anchor element "
                    "on the nearest non-empty line above",
                ))
    return out


# --- C4 ----------------------------------------------------------------------
def anchor_inventory(specs: Iterable[Path]) -> dict[str, set[str]]:
    inv: dict[str, set[str]] = {}
    for path in specs:
        cap = capability_of_spec(path)
        if cap is None:
            continue
        inv[cap] = set(RE_ANCHOR.findall(path.read_text(encoding="utf-8")))
    return inv


def nearest_capability(line: str, pos: int, rid: str = "", window: int = 48) -> str | None:
    """Capability named ADJACENT to the reference at `pos`, or None.

    Adjacency, not "anywhere on the line". A spec line routinely mentions a peer
    capability far from the reference — `... (#req-11), see wayfinder/spec.md` —
    and resolving on the first word found on the line attributed skeleton
    Requirements to wayfinder, producing hundreds of false C4 violations. Only a
    capability word inside the window immediately around the reference counts as
    a qualifier.
    """
    lo, hi = max(0, pos - window), min(len(line), pos + window)
    best: tuple[int, str] | None = None
    for m in RE_CAP_MENTION.finditer(line, lo, hi):
        # A qualifier qualifies what FOLLOWS it. A capability word after the
        # reference is not a candidate at all: in
        # `wayfinder spec req-20 and also governance req-gov-2` the trailing
        # `governance` is closer by signed distance than the `wayfinder` that
        # actually owns `req-20`.
        if m.end() > pos:
            continue
        low = m.group(1).lower()
        cap = None
        for word, name in CAPABILITY_WORDS:
            if word in low:
                cap = name
                break
        if cap is None:
            continue
        if not _qualifies(line[m.end():pos], rid):
            continue
        dist = pos - m.end()
        if best is None or dist < best[0]:
            best = (dist, cap)
    return best[1] if best else None


def capability_from_path(line: str, pos: int, rid: str = "", window: int = 48) -> str | None:
    """Capability named by a `<capability>/spec.md` path immediately before `pos`."""
    lo = max(0, pos - window)
    best: tuple[int, str] | None = None
    for m in RE_PATH_CAPABILITY.finditer(line):
        if m.end() > pos:
            continue
        cap = m.group(1)
        if cap not in CAPABILITIES:
            continue
        if not _qualifies(line[m.end():pos], rid):
            continue
        dist = pos - m.end()
        if best is None or dist < best[0]:
            best = (dist, cap)
    return best[1] if best else None


def resolve_capability(rid: str, line: str, pos: int, own: str | None,
                       inventory: dict[str, set[str]]) -> tuple[str | None, str]:
    """Resolve `rid` to a capability. Returns `(capability, outcome)`.

    `outcome` is one of:

      ``resolved``     — an unambiguous capability owns this id.
      ``placeholder``  — the id is a placeholder (`req-N`, `req-N-slug`), not a
                          real Requirement. A Requirement number that is not
                          all digits cannot name an anchor, and the contract
                          Requirement states its permitted forms using exactly
                          that notation; reporting it would make the contract
                          violate itself.
      ``ambiguous``    — the id exists in more than one capability and the line
                          does not say which.
      ``unresolved``   — no capability has this id.

    Precedence: the id's own prefix, then an adjacent `<capability>/spec.md`
    path, then an adjacent capability word, then the enclosing spec's own
    capability, then a capability that is the sole owner of the id.

    Placeholder detection looks at whether a SEGMENT is the stand-in letter, not
    at whether the last segment is numeric: `req-N` and `req-N-slug` use `N` as
    a placeholder for the Requirement number, while `req-20-mci` is a real block
    anchor whose trailing segment is a slug. Testing the last segment against
    `isdigit()` classified every block anchor as a placeholder and silently
    skipped C4 for all of them.
    """
    if any(seg == "N" for seg in rid.split("-")):
        return None, "placeholder"

    for prefix, cap in ID_PREFIX_CAPABILITY.items():
        if rid.startswith(prefix):
            return cap, "resolved"

    by_path = capability_from_path(line, pos, rid)
    if by_path is not None:
        return by_path, "resolved"
    adjacent = nearest_capability(line, pos, rid)
    if adjacent is not None:
        return adjacent, "resolved"
    if own is not None and rid in inventory.get(own, set()):
        return own, "resolved"
    owners = [cap for cap, ids in inventory.items() if rid in ids]
    if len(owners) == 1:
        return owners[0], "resolved"
    if len(owners) > 1:
        return None, "ambiguous"
    return None, "unresolved"


def check_c4(paths: Iterable[Path], inventory: dict[str, set[str]]) -> tuple[list, int, int]:
    out: list[tuple[Path, int, str, str]] = []
    placeholders = 0
    ambiguous = 0
    for path, line_no, line in iter_lines(paths):
        # Same invariant as C1: this gate's own fixtures use synthetic ids
        # (`req-999`) that resolve nowhere by construction, and that must be
        # true regardless of how the caller spelled the paths.
        if is_self_test(path):
            continue
        own = capability_of_spec(path)
        refs: list[tuple[str, int]] = []
        for m in RE_REF_HASH.finditer(line):
            refs.append((m.group(1), m.start()))
        for m in RE_REF_PLAIN.finditer(line):
            refs.append((m.group(1), m.start()))
        for m in RE_REF_WORD.finditer(line):
            refs.append((f"req-{m.group(1)}", m.start()))
        for rid, pos in refs:
            cap, outcome = resolve_capability(rid, line, pos, own, inventory)
            if outcome == "placeholder":
                placeholders += 1
                continue
            if outcome == "ambiguous":
                # The id exists in more than one capability and the line names
                # none. Not a broken reference — an under-specified one. Req-gov-6
                # clause 4 scopes resolvability to "an anchor that exists in the
                # NAMED capability", and most Requirements DO share a number
                # across wayfinder and decompmoe-skeleton, so reporting these
                # would bury the real findings. Counted and reported in the
                # summary so the surface stays visible.
                ambiguous += 1
                continue
            if cap is not None and rid in inventory.get(cap, set()):
                continue
            out.append((
                path, line_no, line.strip()[:120],
                f"C4 reference {rid!r} does not resolve in capability {cap!r}",
            ))
    return out, placeholders, ambiguous


def main(argv: list[str] | None = None) -> int:
    # Spec bodies carry `=>`, `∈` and similar glyphs; a GBK console would abort
    # mid-report, turning a violation list into a crash. Degrade the glyph
    # instead of the report.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    args = list(sys.argv[1:] if argv is None else argv)
    paths = collect_paths(args)
    specs = [p for p in paths if capability_of_spec(p)]

    # C2, C3 and C4 are all spec-driven. If no spec file was recognised, they
    # would each pass on an empty input and the run would report OK having
    # checked nothing — so the count is asserted before any check runs.
    if not specs:
        print("lint_no_line_pointers: ABORT — no capability spec file was "
              "recognised, so C2/C3/C4 would pass vacuously.")
        print(f"  roots: {list(SCAN_ROOTS)}")
        print(f"  scanned: {len(paths)} file(s)")
        return 1

    violations: list[tuple[Path, int, str, str]] = []
    violations += check_c1(paths)
    violations += check_spec_structure(specs)
    inventory = anchor_inventory(specs)
    c4, placeholders, ambiguous = check_c4(paths, inventory)
    violations += c4
    unresolved_c4 = [v for v in c4 if "does not resolve" in v[3]]

    if not violations:
        print(
            f"lint_no_line_pointers: OK ({len(paths)} file(s) scanned, "
            f"{len(inventory)} capability spec(s), no violations)"
        )
        print(f"  C4 placeholders skipped: {placeholders}; "
              f"unqualified references skipped: {ambiguous}")
        return 0

    print(f"lint_no_line_pointers: {len(violations)} violation(s) found")
    print()
    for path, line_no, content, reason in violations:
        print(f"  {path}:{line_no}: {reason}")
        print(f"    {content}")
    print(f"\n  C4 placeholders skipped: {placeholders} "
          f"(non-numeric Requirement numbers are notation, not references)")
    print(f"  C4 unqualified references skipped: {ambiguous} "
          f"(id shared by several capabilities, line names none)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
