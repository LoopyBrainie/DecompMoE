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

#: ``L2-step2`` / ``L4-postmean`` name a layer or a step; ``L2-F5`` names an
#: audit FINDING. Neither is a line locator. But ``L236-L237`` IS a range of
#: line locators, so the exemption is "hyphen followed by a letter that is
#: not the start of another line number".
RE_LABEL_L = re.compile(r"\bL\d{1,4}-(?=[A-Za-z])(?![Ll]\d)")

#: 7-hex and 40-hex commit ids appear next to prose; never a line pointer.
RE_COMMIT = re.compile(r"\b[0-9a-f]{7,40}\b")

EXT = r"(?:md|py|yaml|yml|json|toml|txt|sh|ps1|cfg|ini)"

#: The same extension set as a list, so the file census and the pointer
#: grammar can never disagree about what is scannable. Derived by stripping
#: the group delimiters, not by slicing: ``EXT[3:-2]`` silently turned ``ini``
#: into ``in`` and the census globbed a file type that does not exist.
EXT_EXTENSIONS = tuple(
    EXT.removeprefix("(?:").removesuffix(")").split("|")
)

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
# A marker exempts a locator only when it asserts a PAST STATE of the thing
# being pointed at. The test each entry has to pass: could this token appear
# in ordinary present-tense technical prose?
#
# Two revisions got this wrong in opposite directions.
#
#   ``\bhistor\w*`` accepted the technical NOUN ``history``, so the phrase
#   ``history stacked by metrics.UR per src/decompmoe/metrics.py:83`` -- a
#   pointer to the CURRENT docstring -- exempted itself.
#
#   The set was also too small: the repository's own canonical annotation
#   ``(historical, <value>; superseded by spec req-N L### via <change>)`` was
#   split at its ``;`` and then matched on nothing, so nine legitimate
#   historical annotations were reported as live pointers.
#
# The rule that resolves both: a marker is a past-state ASSERTION. Adjectives
# and participles qualify (``historical``, ``historically``, ``superseded``,
# ``formerly``, ``pre-edit``); a bare noun (``history``) does not.

HISTORICAL_MARKERS = (
    # ``pre-this-change`` / ``pre-migration`` / ``pre-edit`` / ``pre-sweep``
    re.compile(r"\bpre-(?:this-change|migration|edit|sweep|rebaseline)\b",
               re.IGNORECASE),
    # adjective and adverb only -- the bare noun ``history`` is a topic word,
    # not a past-state claim
    re.compile(r"\bhistor(?:ical|ically)\b", re.IGNORECASE),
    re.compile(r"\bsupersed(?:e|ed|ing)\b", re.IGNORECASE),
    re.compile(r"\bformer(?:ly)?\b", re.IGNORECASE),
    re.compile(r"\boriginal(?:ly)?\b", re.IGNORECASE),
    re.compile(r"\bno\s+longer\b", re.IGNORECASE),
    re.compile(r"\bdeprecated\b", re.IGNORECASE),
    re.compile(r"\bobsolete\b", re.IGNORECASE),
    # Chinese past-state vocabulary. The set carried ``原`` alone, which is
    # an inconsistency rather than a decision in a Chinese-primary
    # repository: ``旧实现见 x.py:222`` and ``之前的实现在 x.py:222`` were
    # both reported as live pointers while ``原值见 x.py:222`` was correctly
    # exempt.
    #
    # ``原`` is then a HOMOGRAPH, and a single-character marker has no way
    # to say which sense it found: 原理 (principle), 原子 (atom) and 还原
    # (restore) all contain it and each exempted a live pointer. Widening the
    # set with 旧 in the same change made this worse without addressing it.
    # So ``原`` is no longer a bare character -- it has to be a PAST-STATE
    # sense, i.e. carry one of the words it compounds with. This is a lexical
    # approximation and it is admitted to be one; the alternative was to keep
    # a one-character match that fires on ordinary technical vocabulary.
    re.compile(r"[\u539f\u65e7](?=\s*(?:\u503c|\u5b9e\u73b0|\u5b9a\u4e49|"
               r"\u5148|\u65b9\u6848|\u8bbe\u8ba1|\u6587\u6848|\u7248\u672c|"
               r"\u53e3\u5f84|\u63a8\u5f8b|\u7ed3\u8bba|\u89c4\u5219))"),
    re.compile(r"[\u65e7](?=\s*(?:\u5b9e\u73b0|\u503c|\u65b9\u6848|"
               r"\u8bbe\u8ba1|\u53e3\u5f84))"),
    re.compile(r"\u4e4b\u524d"),                        # 之前
    re.compile(r"\u66fe(?:\u7ecf|\u4e3a)"),              # 曾 / 曾经 / 曾为
    re.compile(r"\u5f53\u65f6"),                        # 当时 (当时为 is a
    #                                                        subset; a separate
    #                                                        longer entry is
    #                                                        unreachable
    #                                                        because the
    #                                                        tuple returns
    #                                                        the first match)
    re.compile(r"\bwas\s+(?=[`\"'(])", re.IGNORECASE),
    re.compile(r"\bbefore\b", re.IGNORECASE),
)

#: A bare 7-40 character all-``[0-9a-f]`` word is NOT a marker. Requiring a hex
#: LETTER kept a decimal float out -- the tail of ``0.0350601609682665718``
#: is legal hex -- but it still accepted ``defaced``, ``effaced`` and
#: ``deadbeef``, which exempted live pointers. A pin has to be STATED as one;
#: that is what :data:`RE_PIN_COMMIT` requires, and nothing else needs this.

#: A pin commit is a STRUCTURED token, not prose. ``at commit `d3689a1``` is
#: an explicit statement that the locator is read at that revision, and the
#: backticks around it are formatting rather than quotation. It is therefore
#: matched WITHOUT consulting the code-span mask. The hex-letter requirement
#: above is what keeps a decimal float out.
RE_PIN_COMMIT = re.compile(
    r"\bcommit\s+`?(?=[0-9a-f]{7,40}\b)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}`?",
    re.IGNORECASE,
)

#: ``superseded by X`` -- X is the NEW authoritative text, so the word that
#: introduces it must not exempt it. This is the repository's own canonical
#: annotation:
#:
#:     *(historical, centered-covariance reading; superseded by spec
#:       req-20 L453 uncentered second moment)*
#:
#: Here ``historical`` annotates the TICKET. ``req-20 L453`` names the spec,
#: and it is exactly the pointer that drifts. Letting the marker reach it
#: exempted nine sites that were 9 to 61 lines stale, two of them pointing at
#: a blank line -- the sweep replaced fourteen UNMARKED pointers and left
#: these, because the marker had already claimed them. A locator introduced by
#: ``superseded by`` is a statement about the present, not the past.
#:
#: The colon form counts too. ``superseded:`` is one character away and
#: exempts the identical locator.
RE_SUPERSEDE_LEAD = re.compile(
    r"\bsupersed\w*\s*(?:by\b|:)", re.IGNORECASE)


@dataclass
class Site:
    path: str
    line: int
    kind: str
    detail: str
    text: str
    #: Half-open character span of the locator inside the RAW line. Exemption
    #: is decided per site, not per line, so every site must know where it
    #: sits. ``(-1, -1)`` means "not tracked" and falls back to line scope.
    pos: tuple = (-1, -1)
    weak: bool = False
    historical: bool = False
    marker: str = ""
    notes: list = field(default_factory=list)
    #: How many raw matches this site absorbed during dedup. See dedupe().
    merged: int = 1


#: How far a historical marker may sit from a locator and still exempt it.
#:
#: A marker is a clause-level annotation, not a line-level one. The previous
#: rule exempted the whole LINE if a marker appeared anywhere on it, so on a
#: 2000-character ``**Source:**`` field a single ``原`` buried in one sub-clause
#: silently exempted every other locator on the line -- including pointers
#: that name the CURRENT state of a current file.
EXEMPT_WINDOW = 40

#: A marker separated from the locator by one of these is annotating a
#: DIFFERENT sentence, so it must not carry over.
#:
#: ``;`` is deliberately NOT a break. The repository's canonical annotation
#: ``(historical, <value>; superseded by spec req-N L###)`` is ONE unit split
#: Sentence boundaries. ``;`` is deliberately NOT one -- the repository's
#: canonical annotation
#: ``(historical, <value>; superseded by spec req-N L###)`` is ONE unit split
#: by a semicolon, and breaking there cut the marker off from the very
#: locator it is there to annotate.
#:
#: English terminators ARE included. The earlier value held only the CJK
#: full stop, and since ``scan_line`` is line-local a ``\n`` can never occur,
#: so the break rule was vacuous: ``was `1/128`. now spec-20 L453`` kept its
#: exemption across a full stop.
#:
#: It has to be a PATTERN, not a character set. Every path in this grammar
#: contains a dot -- ``safeguards.py:40``, ``1.128`` -- so a bare ``.`` in the
#: break set truncates the window at the first file extension it meets and
#: silently disables exemption for every path-shaped pointer.
RE_EXEMPT_BREAK = re.compile(r"[。！？]|[.!?](?=\s|$)")

#: Characters read PAST the window so a marker at the very edge is recognised
#: whole instead of sliced. The window still bounds where a marker may start.
MARKER_TAIL = 24


def code_span_mask(text: str):
    """Mark every position that lies inside a Markdown code span or a quoted
    run.

    A code span opens with a run of N backticks and closes with a run of
    exactly N, and the CONTENT between them is part of the span. The previous
    implementation counted single backticks and took the parity, which failed
    twice over: a DOUBLE-backtick span contributes four backticks, so its
    contents were reported as being OUTSIDE a code span, and even for a single
    backtick only the delimiters were ever marked, never the text between.

    An UNTERMINATED run marks to the end of the line. CommonMark treats an
    unmatched backtick as a literal, which is the stricter reading but the
    wrong direction for a gate: an unclosed fence is a formatting accident,
    and leaving its body unmarked let a word like ``HISTORICAL=True`` inside a
    Python fence act as a historical marker and exempt a live pointer.

    Both errors point the same way -- a token in backticks is a quotation, not
    a claim about the line, and must not act as a historical marker. That is
    how the word ``historical`` inside a quoted annotation example came to hide
    a live pointer 84 lines out of date.
    """
    mask = bytearray(len(text))
    n = len(text)
    i = 0
    in_quote = False
    while i < n:
        c = text[i]
        if c == "`":
            j = i
            while j < n and text[j] == "`":
                j += 1
            run = j - i
            # find a closing run of exactly the same length
            k, close = j, -1
            while k < n:
                if text[k] == "`":
                    m = k
                    while m < n and text[m] == "`":
                        m += 1
                    if m - k == run:
                        close = m
                        break
                    k = m
                else:
                    k += 1
            end = close if close >= 0 else len(text)
            for q in range(i, end):
                mask[q] = 1
            i = end
            continue
        if c == '"':
            # The opening quote opens the run, the closing quote does not
            # belong to it -- this matches the old parity rule exactly.
            mask[i] = 1 if not in_quote else 0
            in_quote = not in_quote
            i += 1
            continue
        if in_quote:
            mask[i] = 1
        i += 1
    return mask


def has_marker_anywhere(text: str) -> bool:
    """True when `text` carries a historical marker outside every code span.

    The whole-text question, with no locality requirement. The lint's
    ``has_historical_marker`` shim is a plain predicate over a sentence and has
    no locator to measure distance from; the windowed :func:`_exempt` is what
    decides a real site.
    """
    mask = code_span_mask(text)
    for rx in HISTORICAL_MARKERS:
        for m in rx.finditer(text):
            if not mask[m.start()]:
                return True
    return bool(RE_PIN_COMMIT.search(text))


def _exempt(text: str, start: int, end: int, others=()):
    """Return the marker that exempts THIS locator, or ``""``.

    A marker counts only when it is close to the locator (within
    ``EXEMPT_WINDOW`` characters, either side), not separated from it by a
    sentence break, and NOT inside a code span -- a token in backticks is a
    quotation, not a claim about this line. ``governance`` documents the
    ``(historical, ...)`` annotation format inside backticks; that
    documentation must not exempt itself.

    The window bounds where a marker may START. It is read with a tail margin
    so a marker sitting just outside is still RECOGNISED rather than cut in
    half: truncating first turned ``**pre-edit**`` into ``**pre``, which no
    pattern can match, and silently left the line actionable.

    ``others`` are the spans of the OTHER locators on this line. A marker
    annotates ONE recorded object, so a marker that has to reach ACROSS
    another locator on the same line is not annotating this one. Without
    that, ``(historical, was 1/128) spec.md L100 then spec.md L453 is
    current`` exempted the live `L453` with the marker that belongs to
    `L100`.

    The test is symmetric -- a locator between this one and a marker on its
    far side blocks the exemption just as one on its near side does.

    A crossing needs a tracked locator strictly BETWEEN the marker and the
    target, which means the marker has to come first:
    ``marker ... A ... B``. In the mirror order ``A (marker) ... B`` there is
    nothing between them, so ``others`` cannot fire and `B` is decided by
    ``EXEMPT_WINDOW`` and the sentence break alone. The older version of this
    docstring cited ``L100 (historical, was 1/128) - but see spec.md L453``
    as the defect ``others`` fixed; it does not, and it cannot -- a bare
    ``L100`` with no path or capability word in front of it is not a tracked
    locator, so the line offers nothing to reach across. That shape is
    recorded as a known residual in the round-5 change, not claimed as fixed.
    """
    if start < 0:
        start, end = 0, len(text)
    lo = max(0, start - EXEMPT_WINDOW)
    hi = min(len(text), end + EXEMPT_WINDOW)
    raw = text[lo:hi]
    # A sentence break matters only when it falls BETWEEN the marker and the
    # locator. Keeping the whole window and cutting it at the first break kept
    # the half in front of the break -- which is where the marker was -- so
    # `was `1/128`. now spec req-20 L453` stayed exempt across a full stop.
    # Keep the stretch that actually CONTAINS the locator.
    left = 0
    for brk in RE_EXEMPT_BREAK.finditer(raw):
        if brk.end() <= start - lo:
            left = brk.end()
        elif brk.start() >= end - lo:
            break
    right = len(raw)
    for brk in RE_EXEMPT_BREAK.finditer(raw):
        if brk.start() >= end - lo:
            right = brk.start()
            break
    window = text[lo + left: lo + right + MARKER_TAIL]
    mask = code_span_mask(text)

    def _admissible(abs_start: int) -> bool:
        return start - EXEMPT_WINDOW <= abs_start <= end + EXEMPT_WINDOW

    def _in_supersede_complement() -> bool:
        """True when this locator is the text introduced by ``superseded by``.

        The complement of ``superseded by`` is the superseding text, i.e. the
        present. A pointer that sits there is a statement about the current
        spec and no marker on the line may exempt it.

        The lead is skipped when it falls inside a code span or a quoted run:
        every other marker respects the mask, and a phrase someone wrote down
        in order to TALK ABOUT the convention is not itself an instance of it.
        """
        for lead in RE_SUPERSEDE_LEAD.finditer(text, lo, end + MARKER_TAIL):
            if mask[lead.start()]:
                continue
            if lead.end() <= start:
                return True            # the locator IS what `by` introduces
        return False

    new_target = _in_supersede_complement()

    def _crosses_another_locator(abs_start: int) -> bool:
        """True when a locator sits between this marker and this one.

        A marker annotates one recorded object. Reaching across a different
        locator to claim this one is how a ticket's ``historical`` came to
        exempt a live spec pointer written later on the same line.
        """
        for s2, e2 in others:
            if abs_start < e2 <= start or end <= s2 < abs_start:
                return True
        return False

    m = RE_PIN_COMMIT.search(window)
    if m and _admissible(lo + m.start()):
        return m.group(0)
    if new_target:
        return ""
    for rx in HISTORICAL_MARKERS:
        for m in rx.finditer(window):
            a = lo + m.start()
            if mask[a] or not _admissible(a):
                continue
            if _crosses_another_locator(a):
                continue
            return m.group(0)
    return ""


def _bridge_ok(text: str, ref_end: int, loc_start: int) -> bool:
    return bool(RE_BRIDGE.match(text[ref_end:loc_start]))


def scan_line(rel: str, lineno: int, line: str):
    """Return every pointer site on one line."""
    sites = []
    display = line
    if RE_LABEL_L.search(line):
        # Blank out the LABEL tokens, not the whole line. Returning early
        # meant that one `L2-step2` mention anywhere on a line suppressed
        # every pointer on it -- the same line-level suppression this change
        # exists to remove, one rule further down. The replacement is
        # space-padded so every character offset is preserved: `Site.pos`
        # indexes into this string and the exemption window is measured
        # from it.
        line = RE_LABEL_L.sub(lambda m: " " * len(m.group(0)), line)

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
            sites.append(
                Site(rel, lineno, kind, detail, display.strip(), (m.start(), m.end()))
            )

    # -- antecedent form: a bare ``:100-101`` whose path was named earlier in
    # the same line. The closing-backtick shorthand is how the skeleton spec
    # cites three code ranges on one line, so it has to be counted or the
    # third one survives the sweep.
    if RE_PATH.search(line):
        for m in RE_BARE_COLON.finditer(line):
            # The token must be a real code-span delimiter, not the tail of
            # a bare `word:12`. Checking only the IMMEDIATELY preceding
            # character matters: an earlier version looked back 12
            # characters for any digit, and the `4` of a neighbouring
            # `93-94` suppressed the very form this rule exists for.
            prev = line[m.start() - 1] if m.start() else ""
            if prev and (prev.isalnum() or prev in "_."):
                continue
            sites.append(
                Site(rel, lineno, "antecedent-colon-line",
                     m.group(0).strip(), display.strip(), (m.start(), m.end()))
            )

    # -- bare capability word + locator: adjacency REQUIRED ---------------
    for cm in list(RE_CAPABILITY.finditer(line)) + list(RE_REQ_REF.finditer(line)):
        rest_start = cm.end()
        for lm in RE_BARE_L.finditer(line, rest_start):
            if not _bridge_ok(line, cm.end(), lm.start()):
                continue
            detail = line[cm.start(): lm.end()].strip()
            sites.append(
                Site(rel, lineno, "capability-L", detail, display.strip(),
                     (cm.start(), lm.end()))
            )
            break  # one site per capability word is enough

    # -- reversed order: ``L413 wayfinder`` -------------------------------
    for lm in RE_BARE_L.finditer(line):
        tail = line[lm.end():]
        for cm in RE_CAPABILITY.finditer(tail):
            if _bridge_ok(tail, 0, cm.start()):
                # ``cm`` is a match inside ``tail``, so its offsets are
                # relative to the tail. The absolute end is
                # ``lm.end() + cm.end()``; slicing with the bare ``cm.end()``
                # produced an empty detail and a nonsense span.
                end = lm.end() + cm.end()
                detail = line[lm.start(): end].strip()
                sites.append(
                    Site(rel, lineno, "L-then-capability", detail, display.strip(),
                         (lm.start(), end))
                )
                break

    # -- "line 495" with no reference: weak -------------------------------
    if not any(not s.weak for s in sites):
        for m in RE_WORD_LINE.finditer(line):
            sites.append(
                Site(rel, lineno, "word-line", m.group(0).strip(),
                     display.strip(), (m.start(), m.end()), weak=True)
            )

    spans = [s.pos for s in sites if s.pos[0] >= 0]
    for s in sites:
        others = [sp for sp in spans if sp != s.pos]
        s.marker = _exempt(line, s.pos[0], s.pos[1], others)
        s.historical = bool(s.marker)
    return sites


#: Files that describe pointer FORMS rather than containing pointers.
#:
#: Three families, for the same reason: a file that has to spell out
#: ``req-11 L245`` in order to test for it, or a change's own working notes
#: documenting the defect it is fixing, cannot also be required to be free
#: of it.
#:
#: - the gate and the detector's own test suites;
#: - the detector itself and its guard tests;
#: - under an ACTIVE change, everything except ``specs/`` is a working
#:   note. The ``specs/`` delta IS normative spec text and stays in scope.
#:
#: This tuple is the SINGLE SOURCE OF TRUTH. `lint_no_line_pointers.py`
#: derives `SELF_TEST_PATTERNS` from it, and
#: `tests/test_pointer_scan.py` asserts the two agree. The two tools kept
#: separate copies of this list, they drifted, and the census reported 43
#: "actionable pointers" that were the detector and its own tests.
#:
#: The lint entries are PREFIXES, so a lint added later is covered without
#: anyone remembering to add it here -- the same drift, one directory over.
#: `in_scope` matches them with ``str.startswith``, which is what "prefix"
#: means; a substring test also swallowed `docs/scripts/lint_notes.md`.
SELF_EXCLUDE = (
    "scripts/lint_",
    "scripts/pointer_scan.py",
    "tests/test_lint_",
    "tests/test_pointer_scan.py",
)

#: The files the census MUST cover, named one by one.
#:
#: A total cannot catch a subtraction. Adding `wayfinder/tickets/` to the
#: exclusion list took the census from 80 files to 56, the baseline from 24 to
#: 18, and left every gate green and pytest green -- while the round-4 sweep it
#: had just performed had edited six of those tickets, and the zero this gate
#: certifies is computed over exactly that population. ``MIN_CHECKS`` and the
#: non-md/py count all stayed on the green side of their bounds.
#:
#: Single source of truth: `scripts/lint_pointer_detector.py` derives its checks
#: from here, and `tests/test_pointer_scan.py` asserts the same names against
#: the same `in_scope`. They used to be two literal lists -- the guard test
#: pinned 7 in / 3 out while the gate pinned 15 in / 4 out -- and a subset
#: cannot detect drift in the superset it shadows.
PINNED_IN_SCOPE = (
    "CLAUDE.md",
    "openspec/specs/wayfinder/spec.md",
    "openspec/specs/decompmoe-skeleton/spec.md",
    "openspec/specs/governance/spec.md",
    "wayfinder/tickets/A1-1.md",
    "wayfinder/tickets/A4-1.md",
    "wayfinder/tickets/A5-3.md",
    "wayfinder/tickets/A6a-2.md",
    "wayfinder/tickets/A6b-1.md",
    "wayfinder/tickets/A8-2.md",
    "LOOPS.md",
    "src/decompmoe/safeguards.py",
    "src/decompmoe/metrics.py",
    "src/decompmoe/gating.py",
    "tests/test_safeguards.py",
)

#: ...and the other direction. The detector and its own guard tests spell out
#: pointer forms by construction; if the census covered them it would report
#: its own fixtures as live pointers.
PINNED_OUT_OF_SCOPE = (
    "scripts/pointer_scan.py",
    "scripts/lint_no_line_pointers.py",
    "scripts/lint_pointer_detector.py",
    "tests/test_pointer_scan.py",
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
    live: dict = {}
    for s in sites:
        k = _loc_key(s)
        counts[k] = counts.get(k, 0) + 1
        live[k] = live.get(k, False) or not s.historical
        cur = best.get(k)
        if cur is None or _KIND_RANK.get(s.kind, 9) < _KIND_RANK.get(cur.kind, 9):
            best[k] = s
    for k, s in best.items():
        s.merged = counts[k]
        # A LIVE instance of the locator must never be shadowed by a
        # historical one of the same locator on the same line:
        # ``(historical: spec.md L83) -- but spec.md L83 is current`` used to
        # emit only the historical site, and the two live ones vanished from
        # the census. One locator, one verdict: if any mention of it is live,
        # it is reported.
        if live[k] and s.historical:
            s.historical = False
            s.marker = ""
    return sorted(best.values(), key=lambda s: (s.path, s.line, s.detail))


def in_scope(paths):
    """Drop everything the census is not allowed to report on.

    The single filter used by every entry point -- the worktree scan and the
    historical-commit scan alike -- so the two can never disagree about the
    population.

    ``SELF_EXCLUDE`` entries are tested as PREFIXES. A substring test looked
    equivalent and was not: it also matched ``docs/scripts/lint_notes.md`` and,
    worse, ``openspec/specs/wayfinder/scripts/lint_x.md`` -- a spec would have
    been dropped from the census because its path happened to contain a
    directory named after a lint. No tracked file diverges today (the entries
    all sit at the root of their directory), so this was a latent hazard, not
    a live miscount; it is pinned by
    ``tests/test_pointer_scan.py::test_self_exclude_is_a_prefix_not_a_substring``.
    """
    return [
        f for f in paths
        if "openspec/changes/archive/" not in f
        and not any(f.startswith(x) for x in SELF_EXCLUDE)
        and not _is_working_note(f)
    ]


def tracked_files(root: Path):
    """Every tracked file whose extension the pointer grammar can name.

    Derived from :data:`EXT` rather than hardcoded. The previous version globbed
    ``*.md`` and ``*.py`` only, while the path regexes accept ten more
    extensions -- so a pointer living in a ``.yaml`` / ``.txt`` / ``.json``
    file could never be reported, no matter how it was written.
    """
    out = subprocess.run(
        ["git", "ls-files", "--"] + [f"*.{e}" for e in EXT_EXTENSIONS],
        cwd=root, capture_output=True, text=True, encoding="utf-8",
    ).stdout.splitlines()
    return in_scope(out)


def _git(root: Path, *args, binary=False):
    r = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, **({} if binary else
                                               {"text": True, "encoding": "utf-8"}))
    if r.returncode != 0:
        raise RuntimeError("git %s failed: %s"
                           % (" ".join(args), r.stderr))
    return r.stdout


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


def scan_commit(root: Path, rev: str):
    """Scan the tree of ``rev`` straight out of the object store.

    Read-only by construction: it never creates a worktree, never touches the
    index, and leaves nothing behind. The previous harness materialised a
    baseline with ``git worktree add`` at a HARDCODED absolute path and
    printed ``SKIP`` when that path was absent -- so the one check that
    proved the detector is not vacuous at scale silently stopped running the
    moment the path went away, and the gate stayed green either way.
    """
    listing = _git(root, "ls-tree", "-r", "--name-only", rev).splitlines()
    files = [
        f for f in in_scope(listing)
        if Path(f).suffix.lstrip(".") in EXT_EXTENSIONS
    ]
    sites = []
    for rel in files:
        blob = _git(root, "show", f"{rev}:{rel}", binary=True).decode(
            "utf-8", errors="replace")
        for n, line in enumerate(blob.splitlines(), 1):
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
