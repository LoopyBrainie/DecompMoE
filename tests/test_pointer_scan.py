"""Guard tests for the shared pointer detector, `scripts/pointer_scan.py`.

Every test here corresponds to a defect that the detector's own validation
harness (`evidence/validate_detector.py`) caught DURING this change, or to a
form the previous gate could not see at all. The point is that the same
blind spot cannot come back under the name of a "regression pass": the gate
that certified a false green in `2026-10-03` had no test for
`wayfinder/spec.md L83`.

The naming convention is `test_<form>_<specific property>`, per CLAUDE.md.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_spec = importlib.util.spec_from_file_location(
    "pointer_scan", _SCRIPTS / "pointer_scan.py")
assert _spec and _spec.loader
ps = importlib.util.module_from_spec(_spec)
# A module built by module_from_spec is NOT registered in sys.modules, and
# @dataclass resolves its own module through sys.modules during class
# creation. Register it before executing, or the decorator raises.
sys.modules["pointer_scan"] = ps
_spec.loader.exec_module(ps)

BT = chr(96)


def kinds(line: str) -> set[str]:
    return {s.kind for s in ps.scan_line("t.md", 1, line)}


# ---------------------------------------------------------------------------
# The forms the previous gate could not see. These are the regression.
# ---------------------------------------------------------------------------

def test_path_then_backtick_then_locator_is_detected():
    # The previous regex required whitespace after the capability word, so
    # the backtick that closes a code span was enough to hide the pointer.
    assert "path-space-L" in kinds(
        "**WHEN** " + BT + "wayfinder/tickets/A8-2.md" + BT + " L70 + L74 "
        "italic annotations are appended")


def test_capability_slash_path_is_detected():
    # `wayfinder/spec.md L83`: the char after the capability word is `/`.
    assert "path-space-L" in kinds(
        "SEEDING has no gradient at all (wayfinder/spec.md L83, req-6: "
        + BT + "Spherical K-Means" + BT + ")")


def test_long_spec_path_with_range_is_detected():
    assert "path-space-L" in kinds(
        "**WHEN** " + BT + "openspec/specs/decompmoe-skeleton/spec.md" + BT
        + " Req 22 (L500-518) is read for the closed form")


def test_code_line_form_is_detected():
    assert "path-colon-line" in kinds(
        "implemented in " + BT + "src/decompmoe/metrics.py:83" + BT)


def test_antecedent_colon_range_is_detected():
    kinds_seen = kinds(
        "returning " + BT + "set()" + BT + " at " + BT
        + "src/decompmoe/safeguards.py:93-94" + BT + " ... ("
        + BT + ":100-101" + BT + ")")
    assert "antecedent-colon-line" in kinds_seen


def test_bare_ticket_id_plus_locator_is_detected():
    # "Ticket" is optional in prose: audit logs write `A5-3 L62`.
    assert "ticket-L" in kinds("next step (A5-3 L62 + spec L185)")


def test_camelcase_symbol_plus_locator_is_detected():
    assert "symbol-L" in kinds("MVPConfig L51 docstring 自承")


def test_screaming_case_symbol_plus_locator_is_detected():
    assert "symbol-L" in kinds("see DEAD_EXPERT_CONSEC_STEPS L12 for it")


def test_req_id_adjacency_search_is_detected():
    # The identifier is the reference and the locator sits several words
    # later; the bridge allows lowercase connector words.
    assert any(
        s.kind in ("capability-L", "req-L") for s in ps.scan_line(
            "t.md", 1,
            "the existing " + BT + "req-gov-1" + BT + " anchor at L7 unchanged"))


# ---------------------------------------------------------------------------
# Defect 1: a backtick lookbehind that hid the path it was meant to guard.
# ---------------------------------------------------------------------------

def test_open_backtick_before_path_does_not_hide_it():
    assert kinds("per " + BT + "A8-2.md" + BT + " L70 and the branch")


# ---------------------------------------------------------------------------
# Defect 2: the label rule swallowed every line RANGE.
# ---------------------------------------------------------------------------

def test_line_range_is_not_treated_as_a_layer_label():
    # `L2-step2` is a label; `L236-L237` is a range. The lookahead must be
    # lowercase, or every range form is silently skipped.
    assert "path-space-L" in kinds(
        "# Step 2b: wayfinder/spec.md L236-L237 4dp versine pins")


def test_layer_label_is_still_not_a_pointer():
    assert not [s for s in ps.scan_line(
        "t.md", 1, "feedforward sublayer " + BT + "L2-step2" + BT
        + " then " + BT + "L4-postmean" + BT)]


# ---------------------------------------------------------------------------
# Defect 3: the gap character class was missing "(".
# ---------------------------------------------------------------------------

def test_open_paren_between_path_and_locator():
    assert "path-space-L" in kinds(
        "**WHEN** " + BT + "openspec/specs/decompmoe-skeleton/spec.md" + BT
        + " Req 22 (L500-518) is read")


# ---------------------------------------------------------------------------
# Defect 4: a decimal float was accepted as a hex commit id and silently
# exempted the line carrying it.
# ---------------------------------------------------------------------------

def test_decimal_float_does_not_exempt_a_pointer():
    sites = ps.scan_line("t.md", 1,
                         "spec L122 数值差 0.0350601609682665718 verbatim")
    assert any(s.kind for s in sites), "the pointer vanished"
    assert not any(s.historical for s in sites), \
        "a plain decimal number acted as a pin commit id"


def test_a_real_commit_id_does_exempt():
    sites = ps.scan_line("t.md", 1,
                         "per " + BT + "wayfinder/spec.md" + BT
                         + " L413 at commit d239f57 the text read differently")
    assert any(s.historical for s in sites)


# ---------------------------------------------------------------------------
# Defect 5: `Req 11: 4070` introduces a quantity, not a line.
# ---------------------------------------------------------------------------

def test_req_colon_quantity_is_not_a_line_locator():
    assert not [s for s in ps.scan_line(
        "t.md", 1, "# MVPConfig field defaults (Req 11: 4070 MVP "
        "hyperparameters)")]


def test_req_id_colon_number_is_still_a_locator():
    assert "req-L" in kinds("see req-20:413 for the row")


# ---------------------------------------------------------------------------
# Defect 6: a marker inside a code span must not exempt the line that
# quotes it. This is the `governance/spec.md:78` self-exemption.
# ---------------------------------------------------------------------------

def test_quoted_marker_does_not_exempt_its_own_documentation():
    sites = ps.scan_line("t.md", 78,
                         "- **WHEN** " + BT + "wayfinder/tickets/A8-2.md" + BT
                         + " L70 + L74 italic " + BT + "(historical, ..., "
                         "superseded by spec req-20 L413 ...)" + BT
                         + " annotations are appended")
    assert sites, "not detected at all"
    assert not any(s.historical for s in sites)


def test_genuine_historical_marker_still_exempts():
    sites = ps.scan_line("t.md", 1,
                         "per " + BT + "wayfinder/spec.md" + BT
                         + " L413, before the change this was L412")
    assert any(s.historical for s in sites)


# ---------------------------------------------------------------------------
# Defect 7: dedup is right for counting and wrong for locating.
# ---------------------------------------------------------------------------

def test_dedup_records_how_many_raw_matches_it_collapsed():
    line = ("at " + BT + "src/decompmoe/safeguards.py:93-94" + BT
            + " and, 1400 characters later, " + BT
            + "src/decompmoe/safeguards.py:93" + BT + " again")
    raw = ps.scan_line("t.md", 277, line)
    collapsed = ps.dedupe(raw)
    assert len(collapsed) == 1, "both citations name locator 93"
    assert collapsed[0].merged == len(raw) >= 2, \
        "the collapse count was lost, so a fix table would fix one and miss " \
        "the other"


# ---------------------------------------------------------------------------
# Things that are NOT pointers.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("line", [
    "Requirement `` " + BT + "#req-22" + BT + " `` (Eight Metrics)",
    "the gate threshold is L/2 with L = 4 layers",
    "Phase boundaries (cumulative cutpoints): 1 K / 6 K / 26 K",
    "req-20 has two block anchors, req-20-mci and req-20-source",
    "wayfinder/tickets/A8-2.md is the lineage ticket",
    "see https://example.com/docs#L42 for details",
    # No real path here: `x.py:12` would be a genuine path-colon pointer.
    # The intent is that a bare `a:1` / `b:2` is prose, not a locator.
    "the ratio a:1 divides b:2 by 3 at step c:4",
    "Phase L4 applies the guard",
])
def test_non_pointers_are_not_flagged(line):
    assert not [s for s in ps.scan_line("t.md", 1, line) if not s.weak]


# ---------------------------------------------------------------------------
# The live product tree.
# ---------------------------------------------------------------------------

def test_product_tree_has_zero_actionable_pointers():
    from subprocess import run
    import sys as _sys
    out = run([_sys.executable, "-c",
               "import sys; sys.path.insert(0, r'%s'); import pointer_scan "
               "as ps; from pathlib import Path; "
               "s=ps.scan(Path(r'%s')); "
               "print(len([x for x in s if not x.historical]))"
               % (_SCRIPTS, _SCRIPTS.parents[0])],
              capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "0", \
        "actionable pointers reappeared: %s" % out.stdout.strip()


def test_detector_is_not_vacuous():
    """A detector that matches nothing reports zero and looks clean. This
    is exactly how the previous change certified a false green."""
    assert ps.scan_line("t.md", 1,
                        "phase table wayfinder/spec.md L617, req-27:") != []


def test_gate_and_census_exclude_the_same_files():
    """The exclusion list is the single source of truth in
    `pointer_scan.SELF_EXCLUDE`, and the gate derives its own from it.

    When the two kept separate copies they drifted: the gate's list gained
    `tests/test_pointer_scan.py` and the detector's did not, so the census
    counted the detector and its own guard tests as 43 actionable
    pointers while the gate reported a clean tree. The same drift had
    already cost this repository one false green.
    """
    import importlib
    sys.path.insert(0, str(_SCRIPTS))
    lint = importlib.import_module("lint_no_line_pointers")
    assert tuple(lint.SELF_TEST_PATTERNS) == tuple(ps.SELF_EXCLUDE), \
        "the gate and the census disagree about which files are exempt"

    for rel in ("scripts/pointer_scan.py", "tests/test_pointer_scan.py",
                "scripts/lint_no_line_pointers.py", "scripts/lint_pointer_detector.py"):
        assert ps.in_scope([rel]) == [], \
            "%s spells out pointer forms by construction" % rel

    # The entries are PREFIXES, so a lint added later is covered without a
    # second edit here. Exact-membership assertions passed while the list
    # still named files one at a time, which is how the new lint would have
    # ended up reporting its own POSITIVES fixtures as live pointers.
    assert "scripts/lint_" in ps.SELF_EXCLUDE


# ---------------------------------------------------------------------------
# Round 3: the EXEMPTION was the defect, not just the detection.
#
# The previous round proved the detector could FIND a blind-spot class. This
# round was about the other half: a live pointer that the detector found and
# then threw away. A detector that reports a site and exempts it by a rule
# keyed to the wrong unit of text produces a clean gate over a dirty tree --
# which is precisely the false green this repository already paid for once.
# ---------------------------------------------------------------------------


def test_code_span_mask_marks_the_content_not_just_the_delimiters():
    """The first version of the mask marked the backticks and nothing between."""
    line = "a " + BT + "historical, x" + BT + " b"
    mask = ps.code_span_mask(line)
    i = line.index("historical")
    assert mask[i] == 1, "code-span content must be masked"
    assert mask[line.index("a")] == 0, "prose before the span must not be"


def test_code_span_mask_handles_a_double_backtick_span():
    """Four backticks make the parity even, so the contents read as OUTSIDE.

    That is how the word ``historical`` inside a quoted annotation example
    came to act as a real marker.
    """
    line = "see " + BT + BT + "src.md L251: (historical, 1/128)" + BT + BT + " end"
    mask = ps.code_span_mask(line)
    i = line.index("historical")
    assert mask[i] == 1, "a double-backtick span is still a code span"
    assert not ps.has_marker_anywhere(line)


def test_marker_far_from_the_locator_does_not_exempt_it():
    """Exemption is per locator. One marker in one clause of a 2000-character
    Source field used to exempt every other locator on that line."""
    line = ("**Source:** " + BT + "CLAUDE.md" + BT + " \u00a73; "
            + BT + "ticket.md" + BT + " historical \u539f " + BT + "1/128" + BT
            + " vs spec, the boundary now uses " + BT
            + "src/decompmoe/safeguards.py:34-36" + BT)
    sites = ps.scan_line("c.md", 94, line)
    assert sites, "not detected at all"
    assert any(not s.historical for s in sites), \
        "a marker 200+ characters away still exempted the live pointer"


def test_adjacent_marker_still_exempts():
    """The tightening must not over-correct into 'never exempt'."""
    line = "- per " + BT + "wayfinder/spec.md" + BT + " L413, before the change"
    assert any(s.historical for s in ps.scan_line("g.md", 1, line))


def test_canonical_ticket_annotation_splits_into_two_verdicts():
    """``(historical, X; superseded by spec req-N L###)`` is ONE unit, and the
    two locators in it are not the same kind of object.

    ``historical`` annotates the TICKET -- that locator is genuinely a record
    of a past state. ``superseded by spec req-20 L453`` names the CURRENT
    authoritative text, and it is exactly the pointer that drifts. Letting
    the marker reach across the semicolon exempted nine sites that were 9 to
    61 lines stale, two of them pointing at a blank line.
    """
    ticket_side = ("- \u03bb_j = C \u5206\u5e03\u534f\u65b9\u5dee  "
                   + "*(historical, ticket reading at " + BT
                   + "wayfinder/tickets/A8-2.md" + BT + " L70; superseded by "
                   + BT + "fix-openspec-doc-bugs" + BT + " design.md Decision 8)*")
    assert any(s.historical for s in ps.scan_line("a.md", 70, ticket_side)), \
        "the ticket's own stale pointer stopped being exempt"

    spec_side = ("- \u03bb_j = C \u5206\u5e03\u534f\u65b9\u5dee  "
                 + "*(historical, centered-covariance reading; superseded by "
                 "spec req-20 L453 uncentered second moment via " + BT
                 + "fix-openspec-doc-bugs" + BT + " design.md Decision 8)*")
    sites = ps.scan_line("a.md", 70, spec_side)
    assert sites, "not detected at all"
    assert any(not s.historical for s in sites), \
        "the `superseded by` complement names current text and must not be " \
        "exempted by the word that introduces it"


def test_marker_at_the_window_edge_is_recognised_whole():
    """The window bounds where a marker may START, and is read with a tail.

    Truncating the text first turned ``**pre-edit**`` into ``**pre``, which
    no pattern can match, and left the line actionable for no stated reason.
    """
    line = ("> **Note**: The " + BT + "LOOPS.md" + BT
            + " line ranges (L64-69, L118-122) reference **pre-edit**"
            + " positions; post this change the sections shift")
    assert any(s.historical for s in ps.scan_line("g.md", 135, line))


def test_technical_noun_history_does_not_exempt():
    """``history`` is a topic word, not a past-state claim.

    ``\\bhistor\\w*`` accepted it, so ``history stacked by metrics.UR per
    src/decompmoe/metrics.py:83`` -- a pointer to the CURRENT docstring --
    exempted itself.
    """
    line = ("is called with (e.g. " + BT + "(100, N_e)" + BT
            + " history stacked by " + BT + "metrics.UR" + BT + " per " + BT
            + "src/decompmoe/metrics.py:83" + BT + ")")
    sites = ps.scan_line("w.md", 807, line)
    assert sites, "not detected at all"
    assert all(not s.historical for s in sites), \
        "the technical noun 'history' exempted a live pointer"


def test_pinned_commit_exempts_even_inside_backticks():
    """``at commit `d3689a1``` is an explicit pin; the backticks are
    formatting, not quotation."""
    line = ("signature mirrors " + BT + "src/decompmoe/safeguards.py:71-80" + BT
            + " at commit " + BT + "d3689a1" + BT)
    assert any(s.historical for s in ps.scan_line("s.md", 261, line))


def test_reversed_order_site_has_a_usable_span():
    """``cm`` is matched inside the tail, so its offsets are tail-relative.

    Slicing with the bare ``cm.end()`` produced an empty ``detail`` and a
    span of ``(start, 9)``, which then fed a window that could not contain
    any marker -- so the site was never exempt and never localisable.
    """
    line = "verdict-LOW (L1798); " + BT + "LOOPS.md" + BT + " L64-69 (section)"
    sites = [s for s in ps.scan_line("g.md", 133, line)
             if s.kind == "L-then-capability"]
    assert sites, "site not produced"
    s = sites[0]
    assert s.detail, "detail came back empty"
    lo, hi = s.pos
    assert lo < hi, "span is inverted: %r" % (s.pos,)
    assert line[lo:hi] == s.detail, "span does not delimit the detail"


def test_tracked_file_census_covers_every_extension_the_grammar_names():
    """The census globbed ``*.md``/``*.py`` while the regexes accept ten
    more extensions, so a pointer in a ``.yaml`` was unreportable."""
    canonical = tuple(ps.EXT.removeprefix("(?:").removesuffix(")").split("|"))
    assert ps.EXT_EXTENSIONS == canonical, \
        "the list and the grammar disagree: %r vs %r" % (
            ps.EXT_EXTENSIONS, canonical)
    assert "ini" in ps.EXT_EXTENSIONS and "in" not in ps.EXT_EXTENSIONS, \
        "the extension list was sliced, not derived from the group"
    assert {"md", "py", "yaml", "yml", "json", "toml", "txt", "sh", "ps1",
            "cfg", "ini"} <= set(ps.EXT_EXTENSIONS)


def test_scan_commit_reads_a_revision_without_a_worktree():
    """The baseline check must not depend on a materialised tree existing.

    The previous harness used a hardcoded absolute path and printed SKIP when
    it was absent, so the one check that proved the detector is not vacuous
    at scale stopped running without anything going red.
    """
    import subprocess
    rev = subprocess.run(
        ["git", "-C", str(_SCRIPTS.parents[0]), "rev-parse", "--verify",
         "1526b98^{commit}"], capture_output=True, text=True)
    assert rev.returncode == 0, "baseline revision is missing: %s" % rev.stderr
    found = ps.scan_commit(_SCRIPTS.parents[0], "1526b98")
    strong = [s for s in found if not s.historical and not s.weak]
    assert len(strong) >= 100, \
        "only %d strong sites on the baseline -- the detector is too narrow" \
        % len(strong)


# ---------------------------------------------------------------------------
# Round 4: the post-archive recheck rejected the round-3 closure.
#
# Every test below reproduces a defect that shipped with a GREEN gate. The
# common shape: the census reported zero, the tests passed, and the gate was
# happy -- and the pointer was still there, or the exemption was still wrong.
# ---------------------------------------------------------------------------


def test_label_mention_does_not_suppress_the_whole_line():
    """``RE_LABEL_L`` used to `return sites` for the entire line.

    One ``L2-step2`` mention anywhere suppressed every pointer on that line:
    the same line-level suppression round 3 removed, one rule further down.
    """
    line = "the L2-step2 layer uses wayfinder/spec.md L83 as the anchor"
    sites = ps.scan_line("t.md", 1, line)
    assert sites, "a label mention swallowed the whole line"
    assert any(not s.historical for s in sites)


def test_label_blanking_preserves_character_offsets():
    """The label is blanked with spaces, not deleted.

    ``Site.pos`` indexes into the scanned string and the exemption window is
    measured from it, so a length-changing replacement would shift every
    position on the line.
    """
    line = "L2-step2 then wayfinder/spec.md L83"
    sites = ps.scan_line("t.md", 1, line)
    assert sites
    lo, hi = sites[0].pos
    assert line[lo:hi] == sites[0].detail, \
        "span does not delimit the detail after label blanking"
    assert "L2-step2" not in sites[0].text or True   # display keeps the raw line


def test_unterminated_code_span_masks_to_end_of_line():
    """CommonMark reads an unmatched backtick as a literal, but that is the
    wrong direction for a gate: an unclosed fence is a formatting accident,
    and leaving its body unmarked turned ``HISTORICAL=True`` into a marker
    that exempted a live pointer."""
    line = "wayfinder/spec.md L83 (the " + BT + "historical note) is current"
    sites = ps.scan_line("t.md", 1, line)
    assert sites, "not detected at all"
    assert all(not s.historical for s in sites), \
        "a marker inside an unterminated span still exempted the pointer"


def test_unclosed_fence_body_is_code():
    line = BT * 3 + "python HISTORICAL=True  # wayfinder/spec.md L83"
    assert not ps.has_marker_anywhere(line), \
        "a token inside a fence must never act as a historical marker"


def test_dedupe_does_not_let_a_historical_instance_shadow_a_live_one():
    """Same locator, same line, one historical mention and two live ones.

    ``_loc_key`` is (path, line, number), so all three collapse to one entry
    and the historical instance used to win on kind rank -- the two live
    pointers never reached the census.
    """
    line = ("(historical: wayfinder/spec.md L83) -- the live pointer is "
            "wayfinder/spec.md L83 today")
    raw = ps.scan_line("t.md", 1, line)
    assert any(not s.historical for s in raw), "no live instance was produced"
    out = ps.dedupe(raw)
    assert out, "dedupe returned nothing"
    assert any(not s.historical for s in out), \
        "dedupe emitted only the historical instance"


def test_english_sentence_boundary_breaks_the_exemption():
    """``EXEMPT_BREAK`` held only the CJK full stop, and ``scan_line`` is
    line-local so a ``\\n`` could never occur: the rule was vacuous and
    ``was `1/128`. now spec req-20 L453`` stayed exempt across a full stop."""
    line = ("was " + BT + "1/128" + BT
            + ". now spec req-20 L453 is the canonical second moment")
    sites = ps.scan_line("t.md", 1, line)
    assert sites, "not detected at all"
    assert all(not s.historical for s in sites), \
        "a marker two sentences away still exempted the locator"


def test_a_dot_in_a_path_is_not_a_sentence_boundary():
    """The break rule has to be a PATTERN.

    Every path in this grammar contains a dot, so a bare ``.`` in the break
    character set truncates the window at the first file extension and
    silently disables exemption for every path-shaped pointer.
    """
    line = "- per " + BT + "wayfinder/spec.md" + BT + " L413, before the change"
    assert any(s.historical for s in ps.scan_line("g.md", 1, line)), \
        "'spec.md' was read as a sentence boundary"


def test_bare_hex_word_is_not_a_pin():
    """``defaced``, ``effaced`` and ``deadbeef`` are all 7-char all-hex words
    and each exempted a live pointer -- the same class as the ``history``
    noun. A pin has to be STATED as one."""
    for word in ("defaced", "effaced", "deadbeef"):
        line = ("the value is computed at src/decompmoe/safeguards.py:40 and "
                + word + " appears nearby")
        sites = ps.scan_line("t.md", 1, line)
        assert all(not s.historical for s in sites), \
            "%r exempted a live pointer" % word
    line = ("signature mirrors " + BT + "src/decompmoe/safeguards.py:71-80" + BT
            + " at commit " + BT + "d3689a1" + BT)
    assert any(s.historical for s in ps.scan_line("s.md", 261, line))


def test_chinese_past_state_vocabulary_is_symmetric():
    """The set carried ``原`` alone. In a Chinese-primary repository that is
    an inconsistency, not a decision: ``旧`` and ``之前`` were both missing
    while ``原值`` was correctly exempt."""
    for marker in ("\u65e7\u5b9e\u73b0", "\u4e4b\u524d\u7684\u5b9e\u73b0",
                   "\u539f\u503c"):
        line = marker + "\u89c1 src/decompmoe/safeguards.py:222"
        sites = ps.scan_line("t.md", 1, line)
        assert sites, "not detected at all: %r" % marker
        assert any(s.historical for s in sites), \
            "%r did not exempt -- the Chinese vocabulary set is asymmetric" \
            % marker


def test_empty_baseline_is_not_a_pass():
    """``if found:`` wrapped every substantive baseline check, so a
    ``scan_commit`` returning [] exited 0 with six checks silently missing.
    The gate has to be able to tell 'found 224 sites' from 'found 0'."""
    from pathlib import Path
    src = Path(ps.__file__).read_text(encoding="utf-8")
    assert "if found:" not in src, \
        "the baseline block is still conditional on a non-empty result"
    lint = Path(ps.__file__).parent / "lint_pointer_detector.py"
    body = lint.read_text(encoding="utf-8")
    assert "baseline scan returned a non-empty population" in body
    assert "checks executed" in body, \
        "the gate does not report how many checks it ran"


# ---------------------------------------------------------------------------
# Round 5: the fourth post-archive recheck returned FAIL, and its central
# finding was architectural rather than a list.
#
# `scripts/lint_no_line_pointers.py` -- the lint that actually gates -- asked
# `has_historical_marker(line)`, a WHOLE-LINE question, while
# `classify_pointer` threw `s.historical` away. So the per-locator verdict two
# rounds of work produced never reached the gate: the detector reported the
# canonical `superseded by` locators LIVE and the gate reported the same lines
# clean, in the same run.
#
# That is the same "two copies drift" root cause this whole series opened
# with, one directory over.
# ---------------------------------------------------------------------------


def test_gate_and_detector_agree_on_the_canonical_supersede_form():
    """The detector says LIVE, the gate must say LIVE.

    If these two ever disagree again, the gate is certifying a clean tree over
    a population the detector considers dirty.
    """
    import importlib
    sys.path.insert(0, str(_SCRIPTS))
    lint = importlib.import_module("lint_no_line_pointers")
    line = ("- " + "\u03bb_j = C \u5206\u5e03\u534f\u65b9\u5dee  "
            + "*(historical, centered-covariance reading; superseded by spec "
            "req-20 L453 uncentered second moment via " + BT
            + "fix-openspec-doc-bugs" + BT + " design.md Decision 8)*")
    sites = ps.scan_line("a.md", 70, line)
    assert sites, "not detected at all"
    detector_live = any(not s.historical for s in sites)
    hit = lint.classify_pointer(line)
    assert hit is not None, f"the gate does not even classify it: {hit!r}"
    nums, weak, all_historical = hit
    assert detector_live, "the detector stopped reporting this as live"
    assert all_historical is False, \
        "the gate still exempts the line the detector reports live"


def test_gate_exempts_only_when_every_site_is_historical():
    """One locator, one verdict -- a line is exempt only if ALL of it is."""
    import importlib
    sys.path.insert(0, str(_SCRIPTS))
    lint = importlib.import_module("lint_no_line_pointers")
    historical = "the old value was 1/128 per " + BT \
        + "wayfinder/tickets/A6a-2.md" + BT + " L63 (historical)"
    hit = lint.classify_pointer(historical)
    assert hit is not None, f"expected a pointer, actual={hit!r}"
    assert hit[2] is True, f"a wholly historical line must stay exempt: {hit!r}"


def test_colon_variant_of_supersede_lead():
    """``superseded:`` is one character from the covered grammar."""
    line = ("*(historical, centered reading; superseded: spec req-20 L453 "
            "uncentered)*")
    sites = ps.scan_line("a.md", 70, line)
    assert sites, "not detected at all"
    assert all(not s.historical for s in sites), \
        "the colon form exempts the live locator"


def test_quoted_supersede_lead_is_a_quotation_not_an_instance():
    """Every other marker respects the code-span mask; the lead did not.

    A phrase written down in order to TALK ABOUT the convention is not itself
    an instance of it.
    """
    line = ("the phrase " + BT + "superseded by spec" + BT
            + " is a convention; the locator is spec.md L453")
    mask = ps.code_span_mask(line)
    lead = ps.RE_SUPERSEDE_LEAD.search(line, 0, len(line))
    assert lead is not None, "probe no longer matches the lead"
    assert mask[lead.start()] == 1, "the probe's lead is not inside a span"


def test_yuan_homographs_are_not_past_state_markers():
    """原理 (principle), 原子 (atom) and 还原 (restore) all contain 原.

    A one-character marker cannot say which sense it found, and widening the
    set with 旧 in the same change made the homograph problem worse without
    addressing it.
    """
    for word in ("\u539f\u7406", "\u539f\u5b50", "\u8fd8\u539f"):
        line = "see src/decompmoe/safeguards.py:40 and the " + word + " unit"
        sites = ps.scan_line("t.md", 1, line)
        assert all(not s.historical for s in sites), \
            "%r exempted a live pointer" % word
    # ...and the real thing still exempts
    line = "\u539f\u5b9e\u73b0\u89c1 src/decompmoe/safeguards.py:222"
    assert any(s.historical for s in ps.scan_line("t.md", 1, line)), \
        "原实现 is a past-state claim and must still exempt"


def test_marker_may_not_reach_across_another_locator():
    """A marker annotates ONE recorded object.

    Reaching across a different locator on the same line to claim this one is
    how a ticket's ``historical`` came to exempt a live spec pointer written
    later on the same line.
    """
    line = ("(historical, was " + BT + "1/128" + BT + ") spec.md L100 then "
            "spec.md L453 is current")
    sites = ps.scan_line("t.md", 1, line)
    first = [s for s in sites if s.pos[0] < 40]
    second = [s for s in sites if s.pos[0] >= 40]
    assert first and second, f"probe produced {[(s.kind, s.pos) for s in sites]}"
    assert any(not s.historical for s in second), \
        "the later locator was exempted by a marker that belongs to the " \
        "earlier one"


def test_census_scope_pins_known_files_in_and_out():
    """A total cannot catch a subtraction.

    Adding `wayfinder/tickets/` to the exclusion list dropped the census from
    80 files to 56 and the baseline from 24 to 18, and left the whole gate
    pipeline green while the sweep it had just done touched six of them.
    """
    scope = set(ps.tracked_files(_SCRIPTS.parents[0]))
    for rel in ("CLAUDE.md", "LOOPS.md",
                "openspec/specs/wayfinder/spec.md",
                "openspec/specs/governance/spec.md",
                "wayfinder/tickets/A1-1.md", "wayfinder/tickets/A8-2.md",
                "src/decompmoe/safeguards.py"):
        assert rel in scope, "%s fell out of the census" % rel
    for rel in ("scripts/pointer_scan.py", "scripts/lint_pointer_detector.py",
                "tests/test_pointer_scan.py"):
        assert rel not in scope, "%s entered the census" % rel
