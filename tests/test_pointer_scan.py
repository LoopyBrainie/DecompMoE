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


def test_canonical_ticket_annotation_is_still_exempt():
    """``(historical, X; superseded by spec req-N L###)`` is ONE annotation.

    Treating ``;`` as a clause boundary cut the marker off from the locator
    it annotates, and nine historical annotations were reported as live.
    """
    line = ("- lambda_j eigenvalue  "
            "*(historical, centered-covariance reading; superseded by spec "
            "req-20 L453 uncentered second moment via " + BT
            + "fix-openspec-doc-bugs" + BT + " design.md Decision 8)*")
    assert any(s.historical for s in ps.scan_line("a.md", 70, line)), \
        "the repository's own annotation format stopped being recognised"


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
