#!/usr/bin/env python3
r"""Lint gate: a count in evidence prose must name the baseline it was measured at.

Background (`openspec/changes/2026-10-04-archive-evidence-provenance`):

    A count is a claim about a *state*, and states drift. A figure written without
    the state it was measured at silently changes truth when the thing it counts
    changes, and nothing in the document says so. This repository has already named
    the family in its own audit record: "该计数本身会漂，故必须记基准 ... 一个不带
    基准的计数，会在被测对象自身变化后静默改变真值" — and then the count recurred
    anyway, because writing the rule down is not a gate. This script is the gate.

    It is the second half of one defect family, not a separate issue. The first half
    is in `scripts/run_gates.py`: an anchor-ledger entry recorded the head it was
    written at while carrying the *working tree's* anchors, so the two facts in the
    file were both correct and the entry still read as self-contradictory. Same shape:
    an artifact whose stated identity and actual content are decoupled, and the
    decoupling is not decidable from the artifact. `worktree_digest` makes the
    ledger's baseline explicit; this script makes a prose count's baseline explicit.

Scope — the change under the knife (`design.md` D4):

    * scoped mode (`GATE_CHANGE` set by `run_gates.py`): that change's
      `proposal.md` / `design.md` / `tasks.md`, plus `docs/**`
    * repo-wide mode (`GATE_CHANGE` unset): every unarchived change, plus
      `docs/**`
    * NOT scanned: `openspec/changes/archive/**` — the archive is read-only
      (`req-gov-5` "Archive copies are not retro-edited"), so a report against
      an archived file would be a report demanding an edit that is forbidden
    * NOT scanned: `openspec/specs/**` — counts inside a spec are governed by
      `req-gov-5`'s provenance obligation, a different mechanism; scanning them
      here would produce a second, inconsistent verdict about the same text
    * NOT scanned: `.audit/**` — `.gitignore:37` excludes it, `git ls-files
      .audit` returns 0 tracked, and it belongs to no change. A gate over an
      unversioned path would pass without ever having been red, which is
      `req-gov-7`'s "a gate that cannot fail is not a gate"

    An earlier draft justified this scope as "the **version-controlled** evidence
    layer". That was wrong on its own terms: the change under review is untracked
    by construction until it is committed, so version-control status is a predicate
    that excludes the very change the gate is judging. See `design.md` D4.

Defect pattern (structural, not keyword):

    A COUNT token, in a block that contains no BASELINE token, is reported.

    A **block** is one of two shapes, because the two ways a count is written are
    different shapes:

    * a table row's block is the whole contiguous `|` run, INCLUDING its header.
      The header is where a baseline would be named if it were named at all, and a
      count table with no revision column is a natural place for this family to hide
    * otherwise the block is the line plus the contiguous non-blank, non-heading
      lines around it. A heading ends it, because a count under one heading is a
      different claim from a count under the next three lines down

    One report per offending BLOCK, not per count line: five unbaselined counts in
    one paragraph are one defect, and reporting them five times inflates the number
    the triage pass reads first.

WHAT COUNTS AS A COUNT (exhaustive — anything not listed is not a count):

    1. ratio        `65/68`, `48 / 48`
    2. paired       `strict 48 / loose 48` — two figures a word apart
    3. transition   `65 → 67` — a ledger migration; the form the motivating
       defect actually took
    4. arithmetic   `65 + 3`, the other half of that same sentence
    5. percentage   `12%`, `1.5%`
    6. CJK counter  `23 条`, `5 项`, `82 个`, `7 次`, `110 行`, `3 处`, `2 份`,
       `4 篇`, `9 字符`
    7. table cell   a cell in a data table that is exactly a number

    A bare integer in **prose** is deliberately NOT a count. It collides with line
    numbers, anchors, version numbers and hash fragments; matching it would bury
    the real signal. In a **table cell** it is one, because a numeric cell in a
    data table is a measurement by construction, and a count table with no
    revision column is the most natural place for this family to hide.

    Lines that are never a count site, in every mode:

    * **headings** — a heading is a label, not a claim
    * **fenced code** — a count inside a fence belongs to the quoted text, which
      has its own provenance rules. The fence toggle keys on a line *starting*
      with ```; a line that merely contains ``` mid-sentence is NOT a fence
    * **a clause reference** — `第 8 条` cites a clause, it does not measure one.
      Stripped before matching, because a lookbehind cannot span `第\s*`

WHAT COUNTS AS A BASELINE (exhaustive — the enumeration is the gate's contract):

    1. commit hash          `\b[0-9a-f]{7,40}\b`
    2. `HEAD`
    3. change name          `\d{4}-\d{2}-\d{2}-<slug>`
    4. Requirement anchor   `req-N` / `req-gov-N`
    5. a named reproducible command that yields the figure
       (`git ...`, `grep`, `pytest`, `openspec validate`, `Select-String`,
       `wc -l`, ...)
    5b. a named test that pins the value (`test_<name>`) — a test that asserts
       the figure is a re-derivation pointer, exactly as a command is. Counted
       separately from (5) because the two are different kinds of reference:
       one re-runs, the other re-asserts
    6. the counting rule itself (`block_starts`, `裸 <a id=`)
    7. the words `revision` / `基线`

    A count is baselined by a *revision* or by a *reproducible command*; those are
    the two ways a reader can actually re-derive it. This enumeration is stated
    here, in the docstring, on purpose: a gate whose criterion lives only in its
    code is a gate nobody can predict, and an unpredictable gate is one that gets
    disabled the first time it is inconvenient.

EXEMPTION MARKERS (exhaustive, in the document, not in a registry):

    `pre-this-change`, `histor`/`historical`, `superseded`,
    `not reconstructible`, `无法复算` / `不可复算`, `待独立裁决`, `不处置`

    Marker-based, per `req-gov-6` obligation 6: the exemption surface stays visible
    in the document itself. There is deliberately NO exemption registry here — that
    is the "registry silently grows" failure `req-gov-11` exists to prevent, and it
    does not become acceptable under a new name.

Recall bias (same stance as `lint_no_line_pointers.py` C1): over-inclusion costs one
line of triage; under-inclusion is how this family has come back before.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CHANGES_DIR = _REPO_ROOT / "openspec" / "changes"
_ARCHIVE_DIR = _CHANGES_DIR / "archive"
_DOCS_DIR = _REPO_ROOT / "docs"

EVIDENCE_GLOBS = ("proposal.md", "design.md", "tasks.md")

# --- 1. count tokens (exhaustive) --------------------------------------------
COUNT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b\d+\s*/\s*\d+\b", "ratio"),
    # `48 / loose 48` — two figures, one word apart. A bare `\d+/\d+` misses the
    # `strict N / loose N` spelling, which is how the motivating instance is written.
    (r"\b\d+\s*/\s*[A-Za-z]+\s*\d+\b", "paired counts"),
    (r"\d+(?:\.\d+)?\s*(?:→|->|⇒)\s*\d+", "transition"),
    (r"\b\d+\s*(?:\+|plus )\s*\d+\b", "arithmetic"),
    (r"\b\d+(?:\.\d+)?\s*%", "percentage"),
    # No trailing `\b`: `条`/`问` are both word characters, so a word boundary can
    # never fall between them and the pattern would silently never match.
    # `(?<!\d)` stops `16 条` matching as `6 条`; the clause form `第 8 条` is
    # removed up front by `_CLAUSE_REF_RE` because its lookbehind cannot span the
    # space between `第` and the digits.
    (r"(?<!\d)\d+\s*(?:条|项|个|处|次|份|篇|行|字符)", "CJK counter"),
)

# `第 8 条` is a clause reference into `CLAUDE.md`, not a measurement. Stripped
# before matching rather than guarded by a lookbehind, which cannot span `第\s*`.
_CLAUSE_REF_RE = re.compile(r"第\s*\d+\s*(?:条|项|个|处|次|款|章|节)")

# --- 2. baseline tokens (exhaustive) -----------------------------------------
BASELINE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b[0-9a-f]{7,40}\b", "commit hash"),
    (r"\bHEAD\b", "HEAD"),
    (r"\b\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*\b", "change name"),
    (r"\breq-(?:gov-)?\d+\b", "Requirement anchor"),
    (r"\b(?:git\s+[a-z-]+|grep\b|pytest\b|openspec\s+validate\b|Select-String\b|wc\s+-l\b)",
     "reproducible command"),
    (r"\btest_[a-z0-9_]+", "named test that pins the value"),
    (r"block_starts|裸\s*<a\s+id=", "counting rule"),
    (r"\brevision\b|基线", "explicit baseline word"),
)

# --- 3. exemption markers (exhaustive, in-document) --------------------------
EXEMPTION_MARKERS = (
    "pre-this-change",
    "histor",
    "superseded",
    "not reconstructible",
    "无法复算",
    "不可复算",
    "待独立裁决",
    "不处置",
)

_COUNT_RES = tuple(re.compile(p) for p, _ in COUNT_PATTERNS)
_BASELINE_RES = tuple(re.compile(p) for p, _ in BASELINE_PATTERNS)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")


def _table_cell_counts(line: str) -> bool:
    """True when a data-table row carries at least one purely numeric cell.

    Scoped to table rows on purpose. In prose a bare integer is ambiguous with a
    line number or an anchor; inside a data table a numeric cell is a measurement
    by construction, and the table is exactly where a count table with no
    revision column would otherwise slip through.
    """
    if not line.lstrip().startswith("|"):
        return False
    for cell in line.strip().strip("|").split("|"):
        if cell.strip().strip("`").replace(",", "").isdigit():
            return True
    return False


def _count_kinds(line: str) -> list[str]:
    """Return the count forms present in one line, clause references removed.

    Inline code spans are stripped first, by the same argument that governs
    fenced blocks: a count inside backticks is quoted material — usually a
    literal example of the *shape* a rule matches (`` `48 / loose 48` `` written
    to show what the pattern looks like), not a claim about this repository.

    The strip is local to count DETECTION. Baselines are still matched against
    the whole line, because the commonest baseline of all is a hash sitting
    inside a code span: ``at `ea802c8```.
    """
    cleaned = _CLAUSE_REF_RE.sub("第N", _INLINE_CODE_RE.sub("", line))
    kinds = [kind for res, (_, kind) in zip(_COUNT_RES, COUNT_PATTERNS) if res.search(cleaned)]
    if not kinds and _table_cell_counts(line):
        kinds.append("table cell")
    return kinds


def evidence_files() -> list[Path]:
    """Return the evidence files in scope, sorted, archive excluded.

    Two scopes, because the gate has two modes and conflating them was a real
    defect in the first draft:

    * **scoped** (`GATE_CHANGE` set, the gate is checking one change): that
      change's `proposal.md` / `design.md` / `tasks.md`, plus `docs/**`.
    * **repo-wide** (`GATE_CHANGE` unset): every unarchived change, plus
      `docs/**`.

    `req-gov-7` states why the scoped mode exists: the check MUST be scoped to
    the change being archived "so that unrelated stale changes in the same
    directory do not determine the result". Sweeping every sibling change makes
    the verdict a function of other people's in-flight work — which is also how
    a gate gets switched off, and how a green can be produced by someone else's
    commit rather than by this change.

    `docs/**` is in scope in BOTH modes on purpose: it is shared repository
    infrastructure rather than one change's work, and `docs/templates/
    post-review-remediation.md` is the file future changes copy. A problem
    there is worth reddening any gate.

    The archive is excluded in both modes — it is read-only (`req-gov-5`
    "Archive copies are not retro-edited"), so a report against an archived
    file would be a report demanding a forbidden edit.
    """
    out: list[Path] = []
    scoped = os.environ.get("GATE_CHANGE", "").strip()
    if scoped:
        change = _CHANGES_DIR / scoped
        if change.is_dir():
            for name in EVIDENCE_GLOBS:
                f = change / name
                if f.is_file():
                    out.append(f)
        else:
            # A gate scoped to a change that does not exist would otherwise
            # silently scan nothing and report OK — a green that means "I looked
            # at the wrong place". Say so instead.
            print(
                f"lint_no_baseline_counts: GATE_CHANGE={scoped!r} does not exist "
                f"under openspec/changes/ — nothing scanned, result is not a pass"
            )
    else:
        if _CHANGES_DIR.is_dir():
            for change in sorted(p for p in _CHANGES_DIR.iterdir() if p.is_dir()):
                if change.name == "archive" or change == _ARCHIVE_DIR:
                    continue
                for name in EVIDENCE_GLOBS:
                    f = change / name
                    if f.is_file():
                        out.append(f)
    if _DOCS_DIR.is_dir():
        out.extend(sorted(_DOCS_DIR.rglob("*.md")))
    return out


def _block_bounds(lines: list[str], idx: int) -> tuple[int, int]:
    """Return the half-open line range of the block containing `lines[idx]`.

    Two block shapes, because the two ways a count is written are different
    shapes:

    * a table row's block is the whole contiguous `|` run, INCLUDING its header.
      A count table is exactly where this family hides — a column of numbers with
      no revision anywhere in sight — and the header row is where the baseline
      would be named if it were named at all. Checking a table row as its own
      one-line block would report every correctly-sourced table.
    * otherwise the block is a maximal run of non-blank, non-heading lines. A
      heading terminates it because a count under one heading is a different
      claim from a count under the next, even three lines apart.
    """
    if lines[idx].lstrip().startswith("|"):
        lo = idx
        while lo > 0 and lines[lo - 1].lstrip().startswith("|"):
            lo -= 1
        hi = idx + 1
        while hi < len(lines) and lines[hi].lstrip().startswith("|"):
            hi += 1
        return lo, hi
    lo = idx
    while lo > 0 and lines[lo - 1].strip() and not lines[lo - 1].lstrip().startswith("#"):
        lo -= 1
    hi = idx + 1
    while hi < len(lines) and lines[hi].strip() and not lines[hi].lstrip().startswith("#"):
        hi += 1
    return lo, hi


def has_exemption(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in EXEMPTION_MARKERS)


def _table_cell_counts(line: str) -> bool:
    """True when a data-table row carries at least one purely numeric cell.

    Scoped to table rows on purpose. In prose a bare integer is ambiguous with a
    line number or an anchor; inside a data table a numeric cell is a measurement
    by construction, and the table is exactly where a count table with no
    revision column would otherwise slip through.
    """
    if not line.lstrip().startswith("|"):
        return False
    for cell in line.strip().strip("|").split("|"):
        if cell.strip().strip("`").replace(",", "").isdigit():
            return True
    return False


def find_unbaselined_counts(lines: list[str]) -> list[tuple[int, str, str]]:
    """Return `(lineno, count_kind, line)` for every count lacking a baseline.

    One report per offending BLOCK, not per count line. A paragraph that states
    five counts and names no baseline is one defect, and reporting it five times
    inflates the number the triage pass has to read.
    """
    findings: list[tuple[int, str, str]] = []
    reported_blocks: set[tuple[int, int]] = set()
    in_fence = False
    for i, line in enumerate(lines):
        # A fenced block is quoted material: a count inside it belongs to whatever
        # is being quoted, and that text has its own provenance rules.
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line.lstrip().startswith("#"):
            continue
        kinds = _count_kinds(line)
        if not kinds:
            continue
        lo, hi = _block_bounds(lines, i)
        if (lo, hi) in reported_blocks:
            continue
        reported_blocks.add((lo, hi))
        block = "\n".join(lines[lo:hi])
        if has_exemption(block):
            continue
        if any(res.search(block) for res in _BASELINE_RES):
            continue
        first = next(
            (j for j in range(lo, hi) if _count_kinds(lines[j])),
            i,
        )
        findings.append((first + 1, "/".join(kinds), lines[first].strip()))
    return findings


def check_text(text: str) -> list[tuple[int, str, str]]:
    """Public entry point so tests can exercise the rules without touching disk."""
    return find_unbaselined_counts(text.splitlines())


def main() -> int:
    # Evidence prose carries `−`, `∈`, `⇒` and similar glyphs; a GBK console would
    # abort mid-report, turning a violation list into a crash — and a crashed gate
    # is indistinguishable from a green one. Degrade the glyph, not the report.
    # Same convention as `lint_no_line_pointers.main`.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    violations: list[tuple[Path, int, str, str]] = []
    scanned = 0
    for path in evidence_files():
        scanned += 1
        rel = path.relative_to(_REPO_ROOT)
        for lineno, kind, line in find_unbaselined_counts(
            path.read_text(encoding="utf-8").splitlines()
        ):
            violations.append((rel, lineno, line, kind))

    if not violations:
        print(
            f"lint_no_baseline_counts: OK "
            f"({scanned} evidence file(s) scanned, no baseline-less counts)"
        )
        return 0

    print(f"lint_no_baseline_counts: {len(violations)} count(s) without a baseline")
    print()
    for rel, lineno, line, kind in violations:
        print(f"  {rel}:{lineno}: {kind} with no baseline in its block")
        print(f"    {line}")
    print()
    print("Each of these states a number whose value depends on a state that moves.")
    print("Either name the baseline — a commit hash, a change name, a Requirement")
    print("anchor, or a command that reproduces the figure (e.g. `git ls-files`,")
    print("`grep -c`) — or, if no version-controlled object can rebuild it, mark it")
    print("in place with `not reconstructible` / `不可复算` so a later reader can")
    print("tell it apart from the figures that do recompute.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
