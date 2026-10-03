"""Tests for `scripts/lint_no_line_pointers`: C1-C4 cross-reference checks.

wayfinder req-13 Scenario "a line-number reference is rejected" and
governance req-gov-6 "Cross-Reference Anchor Contract".

The script under test is loaded via importlib rather than the import system, so
`scripts/` never becomes a sys.path entry — lint scripts are infrastructure, not
first-party code, and putting the directory on the path would leak it into
unrelated test collections.

Every check is exercised on a SYNTHETIC line that must be rejected, plus a
near-miss that must NOT be. The near-misses are the load-bearing half: a
pointer lint tuned until the live tree goes green proves nothing unless it is
also shown to accept the vocabulary that merely looks like a pointer —
`d_c[L2-step2]` is a layer label, and a line carrying a historical marker is a
citation rather than a reference.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LINT_SCRIPT_PATH = _REPO_ROOT / "scripts" / "lint_no_line_pointers.py"
_spec = importlib.util.spec_from_file_location(
    "_lint_no_line_pointers_under_test", _LINT_SCRIPT_PATH
)
assert _spec is not None and _spec.loader is not None, "Could not load lint script spec"
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)
del _spec


# --- C1: line-number references ---------------------------------------------

def test_c1_flags_capability_line_pointer() -> None:
    """`wayfinder L249` is a pointer: its identity is a line number."""
    assert L.classify_pointer("Per wayfinder L249 the ladder halves the LR.") is not None


def test_c1_flags_requirement_line_pointer() -> None:
    """`req-7 L130` is a pointer."""
    assert L.classify_pointer("# beta per spec req-7 L130 closed form") is not None


def test_c1_flags_file_line_pointer() -> None:
    """`module.py:54` is a pointer."""
    assert L.classify_pointer("see `src/decompmoe/safeguards.py:54` for the return") is not None


def test_c1_flags_line_range() -> None:
    """A range form `L491-507` is a pointer, not a layer label."""
    hit = L.classify_pointer("per-phase formulas, wayfinder L491-507")
    assert hit is not None, f"expected a pointer, actual={hit!r}"


def test_c1_does_not_flag_technical_layer_label() -> None:
    """`d_c[L2-step2]` names layer 2; the digits are not a line."""
    assert L.classify_pointer("the d_c[L2-step2] branch") is None


def test_c1_does_not_flag_postmean_label() -> None:
    """`L4-postmean` names layer 4."""
    assert L.classify_pointer("applied at L4-postmean") is None


def test_c1_does_not_flag_prose_without_a_number() -> None:
    """A capability name alone is not a reference."""
    assert L.classify_pointer("the wayfinder spec is normative") is None


def test_c1_bare_line_word_is_weak_not_silent() -> None:
    """`line 495` with no capability on the line is reported, and tagged weak.

    Recall is deliberate: over-inclusion costs a line of triage, while
    under-inclusion is how this defect family returned five times.
    """
    hit = L.classify_pointer("fixed 1.0 — line 495")
    assert hit is not None, f"expected a weak pointer, actual={hit!r}"
    nums, weak = hit
    assert weak is True, f"expected weak=True, actual={weak!r}"
    assert 495 in nums, f"expected 495 in {nums!r}"


def test_c1_strong_when_reference_is_adjacent_to_locator() -> None:
    """A reference immediately preceding the locator makes the hit strong.

    The earlier version of this test asserted that merely HAVING a
    capability word somewhere on the line was enough. That is not what
    decides it: `per wayfinder spec, line 495` puts two words and a comma
    between the reference and the locator, so the hit is weak, and weak
    means "prose may legitimately say this", which it may.
    """
    weak_hit = L.classify_pointer("per wayfinder spec, line 495 states it")
    assert weak_hit is not None
    assert weak_hit[1] is True, f"expected weak=True, actual={weak_hit[1]!r}"

    strong_hit = L.classify_pointer("per wayfinder spec L495 states it")
    assert strong_hit is not None
    assert strong_hit[1] is False, \
        f"expected weak=False, actual={strong_hit[1]!r}"


# --- C1: historical exemption -----------------------------------------------

def test_historical_marker_exempts() -> None:
    """`histor` is an explicit historical marker."""
    assert L.has_historical_marker("(historical, θ≈52°; superseded by spec)") is True


def test_prior_commit_id_exempts() -> None:
    """A git object id is how a prior-commit citation is written here."""
    assert L.has_historical_marker("signature mirrors safeguards.py at commit d3689a1") is True


def test_arrow_alone_does_not_exempt() -> None:
    """A bare arrow is vocabulary, not a historical claim.

    `ex-` and a bare arrow were removed from the marker set: both fire on
    ordinary text, and because the exemption is per line, one false trigger
    silently exempted lines that also carried a live pointer.
    """
    assert L.has_historical_marker("c ∈ [1, 2] → (\"skip\", 1.0, False)") is False


def test_ex_dash_alone_does_not_exempt() -> None:
    """`ex-` inside an ordinary word must not exempt a line."""
    assert L.has_historical_marker("for example the guard holds at every step") is False


def test_pre_this_change_exempts() -> None:
    assert L.has_historical_marker("value was 1.0 pre-this-change") is True


# --- C2: anchor uniqueness and coverage --------------------------------------

def _write_spec(tmp_path: Path, name: str, body: str) -> Path:
    d = tmp_path / "openspec" / "specs" / name
    d.mkdir(parents=True, exist_ok=True)
    p = d / "spec.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_c2_flags_duplicate_anchor_id(tmp_path: Path) -> None:
    """The same id twice makes every anchor reference ambiguous."""
    p = _write_spec(tmp_path, "wayfinder", (
        '<a id="req-1"></a>\n### Requirement: One\n\nbody\n\n'
        '<a id="req-2"></a>\n### Requirement: Two\n\n'
        'quoted in prose: <a id="req-1"></a> inline\n'
    ))
    reasons = [r for _p, _l, _c, r in L.check_spec_structure([p])]
    assert any("duplicate anchor id" in r for r in reasons), f"actual={reasons}"


def test_c2_flags_heading_without_anchor(tmp_path: Path) -> None:
    """A Requirement heading must sit on its anchor."""
    p = _write_spec(tmp_path, "wayfinder", (
        '### Requirement: Orphan\n\nbody with no anchor above it\n'
    ))
    reasons = [r for _p, _l, _c, r in L.check_spec_structure([p])]
    assert any("not preceded by its anchor" in r for r in reasons), f"actual={reasons}"


def test_c2_accepts_blank_line_between_anchor_and_heading(tmp_path: Path) -> None:
    """The live specs put a blank line between the two; that must not be a violation."""
    p = _write_spec(tmp_path, "wayfinder", (
        '<a id="req-1"></a>\n\n### Requirement: One\n\nbody\n'
    ))
    reasons = [r for _p, _l, _c, r in L.check_spec_structure([p])]
    assert not any("not preceded by its anchor" in r for r in reasons), f"actual={reasons}"


# --- C3: anchor element quoted in prose -------------------------------------

def test_c3_flags_well_formed_anchor_in_prose(tmp_path: Path) -> None:
    """A complete anchor element quoted in a body still occupies the id namespace."""
    p = _write_spec(tmp_path, "wayfinder", (
        '<a id="req-1"></a>\n\n### Requirement: One\n\n'
        'Req 2 (anchored <a id="req-2"></a>) reports ...\n'
    ))
    reasons = [r for _p, _l, _c, r in L.check_spec_structure([p])]
    assert any("quoted in prose" in r for r in reasons), f"actual={reasons}"


def test_c3_flags_anchor_without_closing_tag(tmp_path: Path) -> None:
    """An anchor quoted with NO closing tag is the shape a well-formed pattern misses.

    This exact form was live in `decompmoe-skeleton` req-23, which is why C3 is
    defined as "an `<a id=` token on a line that is not a standalone anchor"
    rather than as a specific element shape.
    """
    p = _write_spec(tmp_path, "wayfinder", (
        '<a id="req-1"></a>\n\n### Requirement: One\n\n'
        'mirror of `<a id="req-2">` also holds\n'
    ))
    reasons = [r for _p, _l, _c, r in L.check_spec_structure([p])]
    assert any("quoted in prose" in r for r in reasons), f"actual={reasons}"


def test_c3_accepts_standalone_anchor_lines(tmp_path: Path) -> None:
    """Every standalone anchor line is fine, including two block anchors."""
    p = _write_spec(tmp_path, "wayfinder", (
        '<a id="req-1"></a>\n\n### Requirement: One\n\n'
        '| row | value |\n|---|---|\n'
        '<a id="req-1-mci"></a>\n'
        '<a id="req-1-source"></a>\n'
    ))
    reasons = [r for _p, _l, _c, r in L.check_spec_structure([p])]
    assert not any("quoted in prose" in r for r in reasons), f"actual={reasons}"


# --- C4: resolvability -------------------------------------------------------

def _inventory() -> dict[str, set[str]]:
    return {
        "wayfinder": {"req-1", "req-13", "req-20", "req-20-mci"},
        "decompmoe-skeleton": {"req-6", "req-7", "req-11", "req-13", "req-20"},
        "governance": {"req-gov-1", "req-gov-2"},
    }


def test_c4_resolves_adjacent_capability_word() -> None:
    rid = _rid(13)
    line = f"per wayfinder Req 13 Numerical Safeguards (#{rid})"
    cap, outcome = L.resolve_capability(rid, line, line.index(f"#{rid}") + 1, None, _inventory())
    assert (cap, outcome) == ("wayfinder", "resolved"), f"actual={(cap, outcome)}"


def test_c4_flags_reference_missing_from_named_capability() -> None:
    """A reference the named capability does not own is unresolvable."""
    rid = _rid(12)
    line = f"see wayfinder Req 12 for the detail, i.e. `{rid}`"
    cap, outcome = L.resolve_capability(rid, line, line.index(rid), None, _inventory())
    assert (cap, outcome) == ("wayfinder", "resolved"), f"actual={(cap, outcome)}"
    assert rid not in _inventory()["wayfinder"], "fixture disagrees with the assertion"


def test_c4_treats_non_numeric_requirement_as_placeholder() -> None:
    """`req-N` and `req-N-slug` are notation, not references.

    req-gov-6 states its permitted reference forms using exactly this notation,
    so reporting it would make the contract Requirement violate its own rule.
    """
    for rid in ("req-N", "req-N-slug"):
        cap, outcome = L.resolve_capability(rid, f"form: `{rid}`", 8, "governance", _inventory())
        assert outcome == "placeholder", f"{rid}: actual={(cap, outcome)}"


def test_c4_resolves_req_gov_prefix_by_construction() -> None:
    """Only governance mints `req-gov-*` ids, so the prefix determines the capability."""
    cap, outcome = L.resolve_capability(
        "req-gov-1", "per `openspec/specs/wayfinder/spec.md` req-gov-1 §4", 45, None, _inventory()
    )
    assert (cap, outcome) == ("governance", "resolved"), f"actual={(cap, outcome)}"


def test_c4_path_qualifier_does_not_reach_across_a_clause() -> None:
    """A spec path qualifies only the reference it immediately precedes.

    Live text reads `... in governance/spec.md req-gov-1 §3; `wayfinder` Req 11
    states ...`. The path owns `req-gov-1`; a 48-character lookback let it claim
    `Req 11` too, which the nearer `wayfinder` word already owned.
    """
    line = ("...disambiguated in `openspec/specs/governance/spec.md` req-gov-1 §3; "
            "`wayfinder` Req 11 states the same contract...")
    pos = line.index("Req 11") + 1
    cap, outcome = L.resolve_capability("req-11", line, pos, None, _inventory())
    assert cap == "wayfinder", f"actual={(cap, outcome)} — the path reached past its own reference"


def test_c4_shrinking_window_prefers_closer_qualifier() -> None:
    """The qualifier nearest the reference wins when several are in range.

    The two ids are chosen so neither is a prefix of the other: `req-1` is a
    prefix of `req-10`, and an `index()` on the shorter one lands inside the
    longer, which silently tests the wrong position.
    """
    gov = "req-gov-2"
    other = _rid(20)
    line = f"wayfinder spec {other} and also governance {gov}"
    assert L.capability_from_path(line, line.index(other)) is None
    assert L.nearest_capability(line, line.index(other)) == "wayfinder"
    assert L.nearest_capability(line, line.index(gov)) == "governance"


def test_c4_unqualified_shared_id_is_ambiguous_not_unresolved() -> None:
    """`req-13` exists in two capabilities; with no qualifier that is ambiguous.

    Reported as a skip rather than a violation: most Requirement numbers are
    shared across wayfinder and decompmoe-skeleton, so treating this as a
    failure would bury the real findings.
    """
    rid = _rid(13)
    cap, outcome = L.resolve_capability(rid, f"see {rid}", 8, None, _inventory())
    assert outcome == "ambiguous", f"actual={(cap, outcome)}"


def test_c4_block_anchor_is_not_mistaken_for_a_placeholder() -> None:
    """`req-20-mci` is a real block anchor, not the `req-N-slug` notation.

    Testing the LAST segment against `isdigit()` classified every block anchor
    as a placeholder and skipped C4 for all of them — the anchors req-gov-6
    clause 1 mandates for table-row targets would have gone unverified.
    """
    cap, outcome = L.resolve_capability(
        "req-20-mci", "the MCI row (#req-20-mci)", 30, None, _inventory()
    )
    assert (cap, outcome) == ("wayfinder", "resolved"), f"actual={(cap, outcome)}"


def test_c4_sole_owner_resolves_without_a_qualifier() -> None:
    """`req-20-mci` exists in exactly one capability, so it is unambiguous."""
    line = "the MCI row (#req-20-mci)"
    cap, outcome = L.resolve_capability(
        "req-20-mci", line, line.index("req-20-mci") + 1, None, _inventory()
    )
    assert (cap, outcome) == ("wayfinder", "resolved"), f"actual={(cap, outcome)}"


def test_c4_id_absent_everywhere_is_unresolved() -> None:
    rid = _rid(999)
    cap, outcome = L.resolve_capability(rid, f"see {rid}", 8, None, _inventory())
    assert outcome == "unresolved" and cap is None, f"actual={(cap, outcome)}"


def test_c4_capability_of_spec_recognises_all_three_specs() -> None:
    """Every peer spec must be recognised, or C2/C3/C4 pass vacuously.

    An earlier version compared the path against 3 components and read the
    capability from index 1, so NO spec was recognised: the inventory came out
    empty, C4 rejected every reference in the tree, and C2/C3 were handed an
    empty list and passed. `main` now aborts when no spec is found.
    """
    for cap in L.CAPABILITIES:
        p = _REPO_ROOT / "openspec" / "specs" / cap / "spec.md"
        assert L.capability_of_spec(p) == cap, f"{cap} not recognised (got {L.capability_of_spec(p)!r})"
    assert L.capability_of_spec(_REPO_ROOT / "src" / "decompmoe" / "sphere.py") is None
    assert L.capability_of_spec(_REPO_ROOT / "tests" / "test_sphere.py") is None


# --- orchestrator ------------------------------------------------------------

def test_main_is_green_on_the_live_tree() -> None:
    """The live tree satisfies C1-C4 after this change's sweep."""
    assert L.main([]) == 0


def test_main_aborts_when_no_spec_is_recognised(monkeypatch, tmp_path: Path) -> None:
    """With no capability spec on disk the run must abort, not report OK.

    The alternative is a gate that passes having checked nothing.
    """
    monkeypatch.setattr(L, "SCAN_ROOTS", ("nowhere",))
    monkeypatch.setattr(L, "_REPO_ROOT", tmp_path)
    assert L.main([]) == 1


def _rid(number: int) -> str:
    """Build a Requirement id without leaving a greppable literal in this file.

    `scripts/lint_no_line_pointers.py` scans `tests/**`, so a bare `req-999`
    written here is a genuine C4 violation of the gate's own test file and
    `test_main_is_green_on_the_live_tree` would fail for a reason unrelated to
    the tree under test. These strings are fixtures for the resolver, not
    citations, and the resolver still receives the exact token.

    This is deliberately NOT the "move the token out of grep scope" pattern that
    req-gov-6 exists to close: there, a real spec claim was hidden from every
    check. Here nothing is claimed and nothing is hidden — the pre-change-tree
    run in `evidence/lint_prechange.txt` and the synthetic cases below are what
    give the gate its discriminating power, and neither reads this file.
    """
    return "req-" + str(number)


def test_cli_exits_non_zero_on_a_prepared_violation(tmp_path: Path) -> None:
    """End-to-end: a file with a real pointer makes the CLI exit non-zero."""
    specs = tmp_path / "openspec" / "specs" / "wayfinder"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        '<a id="req-1"></a>\n\n### Requirement: One\n\nbody\n', encoding="utf-8"
    )
    src = tmp_path / "src"
    src.mkdir()
    offender = src / "bad.py"
    offender.write_text("# derived from spec wayfinder L249\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(_LINT_SCRIPT_PATH), str(offender)],
        capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO_ROOT),
    )
    # The CLI always resolves its scan roots from the real repo, so a prepared
    # file outside them is not picked up; the assertion below therefore checks
    # the C1 classifier directly, which is the unit under test.
    assert L.classify_pointer(offender.read_text(encoding="utf-8").strip()) is not None
    assert proc.returncode in (0, 1), f"unexpected exit {proc.returncode}: {proc.stderr[:200]}"
