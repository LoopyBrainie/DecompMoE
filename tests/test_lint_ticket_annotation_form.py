"""Tests for `scripts.lint_ticket_annotation_form`: ticket supersede-annotation form.

Governance `req-gov-2` declares the canonical ticket annotation form:

    (historical, <original reading>; superseded by spec req-N <Requirement title> (`#req-N`) via <change> Decision M)

and the Scenario added by change 2026-10-10 states that `scripts/lint_ticket_annotation_form.py`
enforces it over `wayfinder/tickets/*.md`. No pre-existing lint reads a ticket body:
`lint_no_line_pointers.py` `SCAN_ROOTS` is `("openspec/specs", "src", "tests")`.

Scope is FORM ONLY: given that an annotation exists, is it canonical? Existence ("every ticket must
carry one") and drift ("a spec-superseded value must have a matching annotation") are deliberately
out of scope - see design.md Decision 2.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

# Mirrors tests/test_lint_no_source_field_drift.py: the lint lives in `scripts/`
# (not `src/`), so it is not on the pyproject-managed pythonpath. Load via
# importlib rather than the import system to avoid making `scripts/` a
# sys.path entry.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_LINT_SCRIPT_PATH = _REPO_ROOT / "scripts" / "lint_ticket_annotation_form.py"
_spec = importlib.util.spec_from_file_location(
    "_lint_ticket_annotation_form_under_test", _LINT_SCRIPT_PATH
)
assert _spec is not None and _spec.loader is not None, "Could not load lint script spec"
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)
del _spec


CANONICAL = (
    "Resurrection `< 1/128` *(historical, threshold 1/128 at N_e=64; superseded by "
    "spec req-13 Numerical Safeguards (#req-13) `f_threshold = 1/(2*N_e)` via "
    "`fix-openspec-doc-bugs` design.md Decision 7)*"
)
NO_ANCHOR = (
    "Resurrection `< 1/128` *(historical, threshold 1/128; superseded by "
    "spec req-13 Numerical Safeguards `f_threshold = 1/(2*N_e)` via "
    "`fix-openspec-doc-bugs` design.md Decision 7)*"
)
NO_DECISION = (
    "Resurrection `< 1/128` *(historical, threshold 1/128; superseded by "
    "spec req-13 Numerical Safeguards (#req-13) `f_threshold = 1/(2*N_e)` via "
    "`fix-openspec-doc-bugs`)*"
)
# `fix-openspec-doc-bugs` is a real archived change
# (`openspec/changes/archive/2026-08-21-fix-openspec-doc-bugs`).
CITES_REAL_CHANGE = (
    "Resurrection *(historical, threshold 1/128; superseded by spec req-13 "
    "Numerical Safeguards (#req-13) via `fix-openspec-doc-bugs` design.md "
    "Decision 7)*"
)
# A Decision number attached to a change that does not exist: the real failure
# mode this clause exists to catch.
CITES_FABRICATED_CHANGE = (
    "Resurrection *(historical, threshold 1/128; superseded by spec req-13 "
    "Numerical Safeguards (#req-13) via `fix-never-existed-change` design.md "
    "Decision 7)*"
)
# A8-2.md:70 verbatim shape: the quoted interval `(1/d_c, 1]` closes with a
# square bracket, so a naive paren counter never balances and the whole
# annotation goes unchecked.
UNBALANCED_MATH_IN_CODE_SPAN = (
    "λ_j *(historical, centered-covariance reading; superseded by spec "
    "req-20-mci (#req-20-mci) uncentered second moment via "
    "`fix-openspec-doc-bugs` design.md Decision 8 — centered reading has "
    "`(1/d_c, 1]` upper endpoint unreachable at `|T| = d_c`)*"
)


# --- Annotation span extraction ---------------------------------------------


def test_annotation_span_balances_nested_parenthesis():
    """The `(#req-N)` anchor puts a paren inside the annotation; span must not stop there."""
    start = CANONICAL.index("(historical,")
    begin, end = L.annotation_span(CANONICAL, start)
    extracted = CANONICAL[begin:end]
    assert extracted.startswith("(historical,")
    assert extracted.endswith(")")
    assert "#req-13" in extracted
    assert "design.md Decision 7" in extracted


def test_annotation_span_returns_none_without_closing_paren():
    assert L.annotation_span("(historical, unterminated", 0) is None


def test_find_annotations_locates_every_marker_on_a_line():
    """A line may carry more than one annotation (e.g. A5-3.md)."""
    line = f"{CANONICAL} and {CANONICAL}"
    assert len(L.find_annotations(line)) == 2


# --- Violation codes ---------------------------------------------------------


def test_canonical_form_reports_no_violation():
    assert L.check_line(CANONICAL) == []


def test_missing_anchor_reports_v_anchor():
    reasons = L.check_line(NO_ANCHOR)
    assert any("V-ANCHOR" in r for r in reasons)


def test_missing_decision_citation_is_reported_not_enforced():
    """An annotation that cites nothing is not a failure.

    Reconstructing provenance for the corpus turned out to be unsound, so
    demanding a Decision number would ratify a citation style already known to
    carry mis-attributions (see the lint docstring). Absence of a citation is
    not fabrication.
    """
    assert L.check_line(NO_DECISION) == []
    assert L.cited_changes(NO_DECISION.split("(historical,", 1)[1]) == []


def test_cited_real_change_is_not_a_violation():
    assert L.check_line(CITES_REAL_CHANGE) == []


def test_cited_nonexistent_change_reports_v_decision():
    reasons = L.check_line(CITES_FABRICATED_CHANGE)
    assert any("V-DECISION" in r for r in reasons)
    assert any("fix-never-existed-change" in r for r in reasons)


def test_known_change_slugs_strip_date_prefix():
    """Annotations cite the bare slug; archive dirs are date-prefixed."""
    known = L.known_change_slugs()
    assert "fix-openspec-doc-bugs" in known
    assert "2026-08-21-fix-openspec-doc-bugs" in known


def test_annotation_with_unbalanced_math_in_code_span_is_still_found():
    """Regression: A8-2.md:70 quotes `(1/d_c, 1]`, closed with a square bracket.

    A naive paren counter never returns to depth 0, so the annotation was
    silently dropped and went unchecked — the one failure a form gate must not
    have. Parens inside code spans must not count.
    """
    spans = L.find_annotations(UNBALANCED_MATH_IN_CODE_SPAN)
    assert len(spans) == 1
    body = spans[0][2]
    assert body.endswith(")")
    assert "design.md Decision 8" in body
    assert L.check_line(UNBALANCED_MATH_IN_CODE_SPAN) == []


def test_missing_anchor_in_annotation_with_code_span_math_is_still_caught():
    """The code-span fix must not also blind V-ANCHOR."""
    text = UNBALANCED_MATH_IN_CODE_SPAN.replace("(#req-20-mci)", "req-20-mci")
    assert any("V-ANCHOR" in r for r in L.check_line(text))


def test_legacy_line_addressed_form_is_not_a_violation():
    """`req-gov-2` makes the line-addressed form LEGACY: it stays as written."""
    legacy = (
        "*(historical, was 1/128; superseded by spec req-13 L500 via "
        "`fix-openspec-doc-bugs` design.md Decision 7)*"
    )
    assert L.check_line(legacy) == []


def test_line_without_annotation_is_silent():
    assert L.check_line("just an ordinary ticket sentence, no annotation here") == []


# --- Self-test exclusion -----------------------------------------------------


@pytest.mark.parametrize(
    "rel",
    ["scripts/lint_ticket_annotation_form.py", "tests/test_lint_ticket_annotation_form.py"],
)
def test_is_self_test_covers_lint_infrastructure(rel):
    assert L.is_self_test(_REPO_ROOT / rel)


@pytest.mark.parametrize("rel", ["wayfinder/tickets/A6a-2.md", "openspec/specs/governance/spec.md"])
def test_is_self_test_excludes_real_artifacts(rel):
    assert not L.is_self_test(_REPO_ROOT / rel)


# --- Live corpus -------------------------------------------------------------


def test_live_ticket_corpus_is_form_clean():
    """Every existing annotation in `wayfinder/tickets/*.md` satisfies the canonical form.

    This is the regression guard: the change normalizes the corpus in the same
    commit that lands the gate, so a later edit that reintroduces a non-canonical
    annotation turns this red.
    """
    files = sorted((_REPO_ROOT / "wayfinder" / "tickets").glob("*.md"))
    assert files, "no ticket files found - the lint would pass vacuously"
    found = [(p, v) for p in files for v in L.lint_file(p)]
    assert found == [], f"non-canonical annotations: {[(str(p), v[2]) for p, v in found]}"


def test_live_corpus_actually_contains_annotations():
    """Guards against the previous test passing because there was nothing to check."""
    total = sum(len(L.find_annotations(p.read_text(encoding="utf-8"))) for p in
                sorted((_REPO_ROOT / "wayfinder" / "tickets").glob("*.md")))
    assert total > 0


def test_lint_file_returns_empty_list_for_clean_text(tmp_path):
    f = tmp_path / "T-1.md"
    f.write_text(CANONICAL + "\n", encoding="utf-8")
    assert L.lint_file(f) == []


# --- Enforcement path: lint_text / lint_file / main --------------------------
#
# Added after a review found `lint_file` walked line-by-line while `main`
# counted over the whole document. An annotation split by a hard wrap matched
# neither line, so it went unchecked while `main` still counted it and printed
# "N annotation(s), no violations" with exit 0. Counting and enforcement must
# read the SAME spans, and that invariant needs tests on BOTH sides.


def test_cross_line_annotation_is_still_found(tmp_path):
    """A hard-wrapped annotation must not fall between the two code paths."""
    f = tmp_path / "T-1.md"
    f.write_text(
        "value *(historical, was 1/128; superseded by\n"
        "spec req-13 Numerical Safeguards (#req-13) via\n"
        "`fix-openspec-doc-bugs` design.md Decision 7)*\n",
        encoding="utf-8",
    )
    text = f.read_text(encoding="utf-8")
    assert len(L.find_annotations(text)) == 1
    assert L.lint_file(f) == []


def test_cross_line_fabricated_change_is_reported(tmp_path):
    """The exact case that used to escape: a wrapped annotation naming a
    change that does not exist. Previously counted but never checked."""
    f = tmp_path / "T-1.md"
    f.write_text(
        "value *(historical, was 1/128; superseded by\n"
        "spec req-13 Numerical Safeguards (#req-13) via\n"
        "`totally-invented-change` design.md Decision 7)*\n",
        encoding="utf-8",
    )
    reasons = [r for _, _, _, r in L.lint_file(f)]
    assert any("V-DECISION" in r for r in reasons)
    assert any("totally-invented-change" in r for r in reasons)


def test_lint_file_reports_violations(tmp_path):
    """Kills the mutation that empties the enforcement loop: without this the
    whole `lint_file` body could return [] and every test stayed green."""
    f = tmp_path / "T-1.md"
    f.write_text(NO_ANCHOR + "\n", encoding="utf-8")
    out = L.lint_file(f)
    assert out, "lint_file reported nothing for a violating annotation"
    assert any("V-ANCHOR" in r for _, _, _, r in out)


def test_main_returns_zero_on_clean_input(tmp_path, capsys):
    f = tmp_path / "T-1.md"
    f.write_text(CANONICAL + "\n", encoding="utf-8")
    assert L.main([str(f)]) == 0
    assert "no violations" in capsys.readouterr().out


def test_main_returns_one_on_violating_input(tmp_path, capsys):
    f = tmp_path / "T-1.md"
    f.write_text(CITES_FABRICATED_CHANGE + "\n", encoding="utf-8")
    assert L.main([str(f)]) == 1
    assert "V-DECISION" in capsys.readouterr().out


def test_main_reported_count_matches_what_it_enforced(tmp_path, capsys):
    """The report must never describe annotations the gate did not examine."""
    f = tmp_path / "T-1.md"
    f.write_text(
        "a *(historical, x; superseded by spec req-13 T (#req-13)\n"
        "via `totally-invented-change` design.md Decision 1)*\n"
        "b *(historical, y; superseded by spec req-14 U (#req-14)\n"
        "via `also-invented` design.md Decision 2)*\n",
        encoding="utf-8",
    )
    assert L.main([str(f)]) == 1
    out = capsys.readouterr().out
    assert "annotations scanned: 2" in out
    assert "2 violation(s) found" in out


def test_main_aborts_on_empty_tree(monkeypatch, capsys):
    """Anti-vacuous-pass guard, mirroring `lint_no_line_pointers`."""
    monkeypatch.setattr(L, "collect_paths", lambda args: [])
    assert L.main([]) == 1
    assert "ABORT" in capsys.readouterr().out


# --- Code spans and self-test matching --------------------------------------


def test_double_backtick_span_with_unbalanced_paren_is_still_found():
    """A DOUBLE-backtick span contributes four backticks, so a hand-rolled
    `in_code = not in_code` toggle read its contents as OUTSIDE a span."""
    text = (
        "v *(historical, x; superseded by spec req-13 T (#req-13) via "
        "``change-with-(unbalanced`` design.md Decision 3)*"
    )
    spans = L.find_annotations(text)
    assert len(spans) == 1
    assert L.check_line(text) == []


def test_is_self_test_is_prefix_not_substring():
    """`pointer_scan.py:790-793` records a substring test swallowing
    `docs/scripts/lint_notes.md`; a substring match would exempt it again."""
    assert not L.is_self_test(_REPO_ROOT / "docs" / "scripts" / "lint_notes.md")
    assert not L.is_self_test(
        _REPO_ROOT / "openspec" / "specs" / "wayfinder" / "scripts" / "lint_x.md"
    )


def test_lint_file_exempts_its_own_fixtures(tmp_path, monkeypatch):
    """The self-test exemption must be reachable THROUGH `lint_file`.

    Testing `is_self_test` alone left the call inside `lint_file` uncovered:
    deleting the exemption there left every test green.
    """
    fake_root = tmp_path / "repo"
    fixture = fake_root / "tests" / "test_lint_fake.md"
    fixture.parent.mkdir(parents=True)
    fixture.write_text(NO_ANCHOR + "\n", encoding="utf-8")
    monkeypatch.setattr(L, "_REPO_ROOT", fake_root)

    assert L.is_self_test(fixture), "fixture path was not recognised as a self test"
    assert L.lint_file(fixture) == [], "lint_file reported its own deliberately malformed fixture"


def test_reported_line_number_points_at_the_annotation(tmp_path):
    """The line must come from the annotation's own offset, not line 1."""
    f = tmp_path / "T-1.md"
    f.write_text(
        "# heading\n\nsome prose\n\nvalue " + NO_ANCHOR + "\n\ntrailing prose\n",
        encoding="utf-8",
    )
    out = L.lint_file(f)
    assert out, "expected a violation on line 5"
    assert {line_no for _, line_no, _, _ in out} == {5}


def test_reported_line_number_is_the_start_of_a_wrapped_annotation(tmp_path):
    f = tmp_path / "T-1.md"
    f.write_text(
        "# heading\n\nprose\n\nvalue *(historical, x; superseded by spec req-13 T\n"
        "(#req-13) via `totally-invented-change` design.md Decision 1)*\n",
        encoding="utf-8",
    )
    out = L.lint_file(f)
    assert out, "expected the wrapped annotation to be reported"
    # The annotation OPENS on line 5 and wraps onto line 6; the reported line
    # must be where it opens, not where it closes and not line 1.
    assert {line_no for _, line_no, _, _ in out} == {5}


# --- Decision-citation shape heuristic ---------------------------------------


def test_prose_before_decision_is_not_a_citation():
    assert L.cited_changes("(historical, x; see Decision 3 for context)") == []


def test_continuation_citation_without_second_via_is_seen():
    """A8-2 cites two changes, the second after `+` with no second `via`."""
    text = (
        "(historical, x; superseded by spec req-20-mci (#req-20-mci) Y via "
        "`fix-openspec-doc-bugs` design.md Decision 8 + "
        "`fix-math-consistency-audit-2026-08` design.md Decision 5)"
    )
    cited = L.cited_changes(text)
    assert "fix-openspec-doc-bugs" in cited
    assert "fix-math-consistency-audit-2026-08" in cited


def test_every_real_change_slug_contains_a_hyphen():
    """The hyphen shape test in `cited_changes` is only sound because every
    real slug has one. Assert the invariant instead of assuming it, so the
    documented residual (a fabricated hyphen-free slug) stays unreachable."""
    slugs = L.known_change_slugs()
    assert slugs
    bad = sorted(s for s in slugs if "-" not in s)
    assert bad == [], f"change slugs without a hyphen weaken cited_changes: {bad}"
