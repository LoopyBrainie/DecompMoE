"""A-4 remediation: authoritative line-pointer detector.

This replaces the semantics in ``scripts/lint_no_line_pointers.py`` and
``evidence/pointer_census.py``, both of which shared one regex whose blind
spot caused the previous change to certify a false green:

    \\b(wayfinder|skeleton|decompmoe-skeleton|spec)\\s+(?:spec\\s+)?L?(\\d{1,4})

The ``\\s+`` requires whitespace immediately after the capability word, so
``wayfinder/spec.md L83`` (next char is ``/``) and
``` `wayfinder/tickets/A8-2.md` L70 ``` (next char is a backtick) never match.
Those two forms account for every census-invisible survivor.

## Design

A site is a LOCATOR preceded on the same line by a REFERENCE, where the only
characters between them are bridge characters (punctuation, whitespace,
backticks, brackets) or a small allowlist of connector words (``at``, ``in``,
``see``, ``per``, ``via``, ``on``). This is strictly more permissive than the
old regex, which required whitespace adjacency after a bare capability word.

REFERENCES are matched in two classes:

* **self-carrying** forms, where the reference is part of the match itself and
  therefore needs no adjacency search:
  ``<path>.<ext> L###``, ``<path>.<ext>:###``, ``req-N L###``,
  ``Ticket <ID> L###``, ``Decision <n> L###``
* **bare capability words** (``wayfinder``, ``spec``, ``skeleton``,
  ``governance``, ``CLAUDE``, ``LOOPS``, ``src``, ``tests``, ...), which do
  require the adjacency search.

## Honest stance on error direction

Recall is favoured over precision. A false positive costs a few minutes of
adjudication; a false negative silently certifies a broken tree, which is
precisely the failure this module exists to prevent. Every hit is dumped for
hand review rather than silently auto-fixed.

LOCATORS whose number is part of a layer or step name (``L2-step2``,
``L4-postmean``) are excluded by a following-hyphen rule.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Exclusions
# --------------------------------------------------------------------------

#: ``L2-step2`` / ``L4-postmean`` name a layer or a step, never a line.
#: The lookahead must be LOWERCASE. ``L236-L237`` is a range, and an
#: upper-case-only lookahead silently swallowed every range form.
RE_LABEL_L = re.compile(r"\bL\d{1,4}-(?=[a-z])")

#: 7-hex and 40-hex commit ids appear next to prose; never a line pointer.
RE_COMMIT = re.compile(r"\b[0-9a-f]{7,40}\b")

EXT = r"(?:md|py|yaml|yml|json|toml|txt|sh|ps1|cfg|ini)"

#: A path reference: one or more path segments ending in a known extension.
#: The lookbehind forbids a preceding WORD character only. A backtick is
#: deliberately allowed: in ``` `wayfinder/tickets/A8-2.md` L70 ``` the
#: backtick is the opening code-span delimiter, and the path starts right
#: after it. Excluding backticks here was the first bug this harness caught.
RE_PATH = re.compile(
    r"(?<!\w)"
    r"(?P<path>(?:[.\w-]+/)*\.?[A-Za-z_][\w.-]*\." + EXT + r")"
)

#: ``req-20 L413`` / ``Req 20 L394``. The COLON form is only a line
#: locator for the id form ``req-N:413``. ``Req 11: 4070 MVP
#: hyperparameters`` and ``Req 11: 452M / 100M`` are prose introducing a
#: quantity, and matching them was a false positive class.
RE_REQ_L = re.compile(
    r"\breq-(?P<a>\d+)(?:-\w+)*\s*[:L]\s*(?P<loc>\d{1,4})", re.IGNORECASE
)
RE_REQ_L_SPACED = re.compile(
    r"\bReq\.?\s*(?P<b>\d+)\s+L(?P<loc>\d{1,4})"
)

#: ``Ticket A8-2 L70 + L74`` — the ticket id is the reference. The literal
#: word "Ticket" is OPTIONAL: audit-log prose writes bare ``A5-3 L62`` and
#: ``A4-1 L58``, which are the same pointer.
RE_TICKET_L = re.compile(
    r"\b(?:Ticket\s+)?(?P<id>[A-Z]\d+[A-Za-z0-9]*(?:-\d+)?)\s+L(?P<loc>\d{1,4})"
)

#: ``Decision 3 L412``
RE_DECISION_L = re.compile(
    r"\bDecision\s+(?P<num>\d+)\s+L(?P<loc>\d{1,4})"
)

#: ``src/decompmoe/metrics.py:83`` — code-line form.
RE_PATH_COLON_L = re.compile(
    r"(?<!\w)"
    r"(?P<path>(?:[.\w-]+/)*\.?[A-Za-z_][\w.-]*\." + EXT + r")"
    r":(?P<loc>\d{1,4})"
)

#: ``... spec.md L500-518`` — the self-carrying markdown form. The gap
#: between the path and the locator may hold a CLOSING code-span delimiter
#: (``` `wayfinder/tickets/A8-2.md` L70 ```), so a bare ``\s+`` is not
#: enough and was the second blind spot this harness caught.
RE_PATH_L = re.compile(
    r"(?<!\w)"
    r"(?P<path>(?:[.\w-]+/)*\.?[A-Za-z_][\w.-]*\." + EXT + r")"
    r"[\s`\"'()\[\]{}]*"
    r"(?:[Rr]eq\.?\s*\d+|req-[A-Za-z0-9-]+)?"
    r"[\s`\"'()\[\]{}]*"
    r"L(?P<loc>\d{1,4})"
    r"(?P<dash>\s*[-\u2013\u2014]\s*L?(?P<loc2>\d{1,4}))?"
)

#: Bare capability words. Adjacency to the locator is REQUIRED.
RE_CAPABILITY = re.compile(
    r"\b(?P<cap>wayfinder|decompmoe-skeleton|skeleton|governance|specs|spec"
    r"|CLAUDE|LOOPS|tickets|tests|test|src|code|audit)\b",
    re.IGNORECASE,
)

#: A Requirement id used as a reference: ``req-20``, ``req-gov-4``,
#: ``req-20-mci``. Needs the adjacency search, because the pointer it
#: qualifies may sit several words later ("the existing `req-gov-1` anchor
#: at L7 unchanged").
RE_REQ_REF = re.compile(
    r"\breq-(?:gov-)?\d+(?:-[A-Za-z0-9]+)*\b", re.IGNORECASE
)

#: ``L413`` on its own, used only for the adjacency lookup.
RE_BARE_L = re.compile(r"(?<![0-9A-Za-z_./-])L(?P<loc>\d{1,4})")

#: The locator number inside a reported ``detail`` string, for dedup keying.
RE_NUM = re.compile(r"L?(\d{1,4})")

#: A symbol reference plus a line locator: ``MVPConfig L51``,
#: ``DEAD_EXPERT_CONSEC_STEPS L12``. The symbol must be a genuine identifier
#: — either CamelCase with an internal capital (``MVPConfig``) or
#: SCREAMING_SNAKE (``DEAD_EXPERT_CONSEC_STEPS``). Plain ``Phase L4`` is NOT
#: a match, which is why the internal-capital requirement exists.
RE_SYMBOL_L = re.compile(
    r"\b(?P<sym>[A-Z][a-z0-9]*[A-Z][A-Za-z0-9_]*"
    r"|[A-Z][A-Z0-9]*_[A-Z0-9_]+)\s+L(?P<loc>\d{1,4})"
)

#: A bare ``:100-101`` code-range shorthand that refers back to a path named
#: earlier in the same line, as in
#: ``... or none expert meeting the per-step trigger (`:100-101`)``.
#: The guard is deliberately narrow: the colon must sit IMMEDIATELY after a
#: closing backtick. A looser "some path appears earlier on this line" rule
#: fires on ordinary prose such as ``the ratio a:1 divides b:2``.
RE_BARE_COLON = re.compile(
    r"`:(?P<loc>\d{1,4})(?:\s*[-\u2013\u2014]\s*(?P<loc2>\d{1,4}))?`"
)

#: ``line 495`` / ``lines 71-80`` with no capability token: counted, but
#: tagged ``weak`` because prose legitimately says "line 495" about a
#: hypothetical rather than a repository location.
RE_WORD_LINE = re.compile(
    r"\blines?\s+(?P<loc>\d{1,4})(?P<dash>\s*[-\u2013\u2014]\s*(?P<loc2>\d{1,4}))?"
)

#: Bridge characters permitted between a reference and a bare locator.
_BRIDGE_CHARS = re.escape(
    "".join(chr(c) for c in (
        32, 9, 10,                      # space, tab, newline
    ))
    + "`" + "'" + '"'
    + "()[]{}<>*_.,:;=~|/" + chr(92) + "-"
)

#: The bridge may also contain up to three ordinary lowercase words, so that
#: "the existing `req-gov-1` anchor at L7 unchanged" resolves. A CAPITALISED
#: word blocks the bridge, which keeps "wayfinder ... Phase table L6" from
#: being joined across a sentence boundary.
RE_BRIDGE = re.compile(
    r"^[" + _BRIDGE_CHARS + r"]*"
    r"(?:[a-z]{1,14}[" + _BRIDGE_CHARS + r"]+){0,3}"
    r"[" + _BRIDGE_CHARS + r"]*$"
)

# --------------------------------------------------------------------------
# Historical markers
# --------------------------------------------------------------------------
#
# A marker exempts a line only when it marks a *specific recorded past state*.
# ``HISTORICAL_MARKERS`` deliberately excludes bare ``historical`` and the
# arrow glyph: the previous revision included them, which made
# ``governance/spec.md`` self-exemptify on the word ``historical`` occurring
# inside the very annotation template that the line documents.

HISTORICAL_MARKERS = (
    re.compile(r"\bpre-this-change\b", re.IGNORECASE),
    re.compile(r"\bhistor\w*", re.IGNORECASE),
    re.compile(r"\u539f", re.IGNORECASE),          # 原
    re.compile(r"\bwas\s+(?=[`\"'(])", re.IGNORECASE),
    re.compile(r"\bbefore\b", re.IGNORECASE),
    # A pin commit id. It MUST contain at least one hex LETTER, otherwise a
    # plain decimal number is accepted: the earlier ``[0-9a-f]{7,40}`` matched
    # the tail of the float ``0.0350601609682665718`` and silently exempted
    # four LOOPS.md log entries.
    re.compile(r"\b(?=[0-9a-f]{7,40}\b)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b",
               re.IGNORECASE),
)


@dataclass
class Site:
    path: str
    line: int
    kind: str
    detail: str
    text: str
    weak: bool = False
    historical: bool = False
    marker: str = ""
    notes: list = field(default_factory=list)
    #: How many raw matches this site absorbed during dedup. See dedupe().
    merged: int = 1


def _exempt(text: str):
    """Return the marker that exempts this line, or ``""``.

    A marker inside a code span is a *quoted* token, not a claim about the
    line. ``governance`` documents the ``(historical, ...)`` annotation format
    inside backticks; that documentation must not exempt itself.
    """
    for rx in HISTORICAL_MARKERS:
        for m in rx.finditer(text):
            stripped = _inside_code_span(text, m.start())
            if not stripped:
                return m.group(0)
    return ""


def _inside_code_span(text: str, pos: int) -> bool:
    """True when ``pos`` falls inside a `code span` or a (parenthetical quote)."""
    return text.count("`", 0, pos) % 2 == 1 or text.count('"', 0, pos) % 2 == 1


def _bridge_ok(text: str, ref_end: int, loc_start: int) -> bool:
    return bool(RE_BRIDGE.match(text[ref_end:loc_start]))


def scan_line(rel: str, lineno: int, line: str):
    """Return every pointer site on one line."""
    sites = []
    if RE_LABEL_L.search(line):
        return sites  # L2-step2 style label, not a locator

    # -- self-carrying forms: no adjacency search needed -------------------
    for rx, kind in (
        (RE_PATH_L, "path-space-L"),
        (RE_PATH_COLON_L, "path-colon-line"),
        (RE_REQ_L, "req-L"),
        (RE_REQ_L_SPACED, "req-L"),
        (RE_TICKET_L, "ticket-L"),
        (RE_DECISION_L, "decision-L"),
        (RE_SYMBOL_L, "symbol-L"),
    ):
        for m in rx.finditer(line):
            detail = m.group(0).strip()
            if rx is RE_PATH_L and m.group("loc2"):
                detail = m.group(0)[: m.start("dash") - m.start(0)].strip() + " ..."
            sites.append(Site(rel, lineno, kind, detail, line.strip()))

    # -- antecedent form: a bare ``:100-101`` whose path was named earlier in
    # the same line. The closing-backtick shorthand is how the skeleton spec
    # cites three code ranges on one line, so it has to be counted or the
    # third one survives the sweep.
    if RE_PATH.search(line):
        for m in RE_BARE_COLON.finditer(line):
            span = line[max(0, m.start() - 12): m.start()]
            if not any(c.isdigit() for c in span):
                sites.append(
                    Site(rel, lineno, "antecedent-colon-line",
                         m.group(0).strip(), line.strip())
                )

    # -- bare capability word + locator: adjacency REQUIRED ---------------
    for cm in list(RE_CAPABILITY.finditer(line)) + list(RE_REQ_REF.finditer(line)):
        rest_start = cm.end()
        for lm in RE_BARE_L.finditer(line, rest_start):
            if not _bridge_ok(line, cm.end(), lm.start()):
                continue
            detail = line[cm.start(): lm.end()].strip()
            sites.append(
                Site(rel, lineno, "capability-L", detail, line.strip())
            )
            break  # one site per capability word is enough

    # -- reversed order: ``L413 wayfinder`` -------------------------------
    for lm in RE_BARE_L.finditer(line):
        tail = line[lm.end():]
        for cm in RE_CAPABILITY.finditer(tail):
            if _bridge_ok(tail, 0, cm.start()):
                detail = line[lm.start(): cm.end()].strip()
                sites.append(
                    Site(rel, lineno, "L-then-capability", detail, line.strip())
                )
                break

    # -- "line 495" with no reference: weak -------------------------------
    if not any(not s.weak for s in sites):
        for m in RE_WORD_LINE.finditer(line):
            sites.append(
                Site(rel, lineno, "word-line", m.group(0).strip(),
                     line.strip(), weak=True)
            )

    for s in sites:
        s.marker = _exempt(line)
        s.historical = bool(s.marker)
    return sites


#: Files that describe pointer FORMS rather than containing pointers.
#:
#: Two families, for the same reason: a file that has to spell out
#: ``req-11 L245`` in order to test for it, or a change's own working notes
#: documenting the defect it is fixing, cannot also be required to be free
#: of it.
#:
#: Under an ACTIVE change, everything except ``specs/`` is a working note.
#: The ``specs/`` delta IS normative spec text and stays in scope.
SELF_EXCLUDE = (
    "scripts/lint_no_line_pointers.py",
    "tests/test_lint_",
)


def _is_working_note(rel: str) -> bool:
    if "openspec/changes/archive/" in rel:
        return True                      # already excluded upstream
    if not rel.startswith("openspec/changes/"):
        return False
    rest = rel[len("openspec/changes/"):]
    if "/" not in rest:
        return False
    return not rest.split("/", 1)[1].startswith("specs/")

#: When several forms match the same locator on the same line, keep the most
#: specific. ``wayfinder/spec.md` L83`` is otherwise reported three times
#: (path-space-L, capability-L, L-then-capability), which inflates the count
#: and makes the total meaningless as a work item.
_KIND_RANK = {
    "path-colon-line": 0,
    "path-space-L": 1,
    "ticket-L": 2,
    "decision-L": 3,
    "req-L": 4,
    "capability-L": 5,
    "L-then-capability": 6,
    "word-line": 7,
}


def _loc_key(site: "Site"):
    m = RE_NUM.search(site.detail)
    return (site.path, site.line, m.group(1) if m else site.detail)


def dedupe(sites):
    """Collapse sites that name the same locator, and RECORD how many raw
    matches were collapsed.

    Dedup is correct for COUNTING but wrong for LOCATING: `skeleton` spec
    line 277 cites `src/decompmoe/safeguards.py:93-94` once and
    `src/decompmoe/safeguards.py:93` again, 1400 characters later. Both are
    real and both need editing, but they are one locator number, so dedup
    reports one site. Without ``merged`` the fix table silently fixes the
    first and leaves the second.
    """
    best: dict = {}
    counts: dict = {}
    for s in sites:
        k = _loc_key(s)
        counts[k] = counts.get(k, 0) + 1
        cur = best.get(k)
        if cur is None or _KIND_RANK.get(s.kind, 9) < _KIND_RANK.get(cur.kind, 9):
            best[k] = s
    for k, s in best.items():
        s.merged = counts[k]
    return sorted(best.values(), key=lambda s: (s.path, s.line, s.detail))


def tracked_files(root: Path):
    out = subprocess.run(
        ["git", "ls-files", "*.md", "*.py"],
        cwd=root, capture_output=True, text=True, encoding="utf-8",
    ).stdout.splitlines()
    return [
        f for f in out
        if "openspec/changes/archive/" not in f
        and not any(x in f for x in SELF_EXCLUDE)
        and not _is_working_note(f)
    ]


def scan(root: Path, files=None):
    sites = []
    for rel in (files if files is not None else tracked_files(root)):
        p = root / rel.replace("/", "\\")
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            sites.extend(scan_line(rel, n, line))
    return dedupe(sites)


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\myProject\DecompMoE")
    found = scan(root)
    actionable = [s for s in found if not s.historical]
    historical = [s for s in found if s.historical]
    weak = [s for s in actionable if s.weak]
    print("root      : %s" % root)
    print("sites     : %d across %d file(s)"
          % (len(found), len({s.path for s in found})))
    print("actionable: %d" % len(actionable))
    print("historical: %d" % len(historical))
    print("  of which weak (no reference token): %d" % len(weak))
