"""Tests for `scripts.lint_no_source_field_drift`: structural Source-field checks.

Wayfinder req-34 Scenarios (reverse-link must be wrapped in backticks +
primary reverse-link must be the first top-level item). Verifies the
helpers `_unbackticked_refs`, `_split_top_level_items`, `_first_code_span`,
and the orchestrator `lint_file` against synthetic Source lines and the
post-pre-archive-patch live spec tree.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
# The lint script lives in `scripts/` (not `src/`), so it is not on the
# pyproject-managed pythonpath. Load it via importlib rather than via the
# import system to avoid making `scripts/` a sys.path entry (which would
# leak into unrelated test collections and is a CLAUDE.md anti-pattern:
# lint scripts are infrastructure, not first-party code).
_REPO_ROOT = Path(__file__).resolve().parent.parent
_LINT_SCRIPT_PATH = _REPO_ROOT / "scripts" / "lint_no_source_field_drift.py"
_spec = importlib.util.spec_from_file_location("_lint_no_source_field_drift_under_test", _LINT_SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None, "Could not load lint script spec"
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)
del _spec


# --- Helper tests -----------------------------------------------------------

def test_unbackticked_refs_flags_bare_substring() -> None:
    """`_unbackticked_refs` returns one entry per bare occurrence of the substring."""
    body = "wayfinder/tickets/A6a-2.md (initial A6a-2 design intent)"
    assert L._unbackticked_refs(body, "wayfinder/tickets/") == ["wayfinder/tickets/"]


def test_unbackticked_refs_ignores_backticked_substring() -> None:
    """`_unbackticked_refs` returns [] when the substring is fully backtick-wrapped."""
    body = "`wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent)"
    assert L._unbackticked_refs(body, "wayfinder/tickets/") == []


def test_unbackticked_refs_mixed_backticked_and_bare() -> None:
    """`_unbackticked_refs` flags only the bare occurrence (one entry)."""
    body = "`wayfinder/tickets/A2-1.md`, wayfinder/tickets/A2-2.md"
    assert L._unbackticked_refs(body, "wayfinder/tickets/") == ["wayfinder/tickets/"]


def test_unbackticked_refs_handles_empty_body() -> None:
    """`_unbackticked_refs` returns [] on an empty body."""
    assert L._unbackticked_refs("", "wayfinder/tickets/") == []


# --- Top-level split tests --------------------------------------------------

def test_split_top_level_items_paren_depth() -> None:
    """`_split_top_level_items` does NOT split on commas inside `(...)`."""
    body = (
        "`wayfinder/tickets/A6a-2.md` (initial A6a-2 design intent), "
        "change `fix-openspec-doc-bugs` design.md (Decision 1, 2)"
    )
    items = L._split_top_level_items(body)
    # Expected: 2 items. The first is the backtick-wrapped reverse-link +
    # its inline annotation; the second is the change-decision clause. The
    # comma inside `(Decision 1, 2)` does NOT split, and neither does the
    # comma inside `(initial A6a-2 design intent)`.
    assert len(items) == 2
    assert items[0].startswith("`wayfinder/tickets/A6a-2.md`")
    assert "change" in items[1]


def test_split_top_level_items_code_span_atomic() -> None:
    """`_split_top_level_items` does NOT split on commas inside a code span."""
    body = (
        "`wayfinder/tickets/A2-1.md`, "
        "change `foo, bar, baz` design.md (Decision 1)"
    )
    items = L._split_top_level_items(body)
    # Expected: 2 items. The commas inside `` `foo, bar, baz` `` are
    # inside a code span and do NOT split.
    assert len(items) == 2
    assert items[0] == "`wayfinder/tickets/A2-1.md`"
    assert items[1].startswith("change `foo, bar, baz`")


def test_split_top_level_items_semicolon_separator() -> None:
    """`_split_top_level_items` splits on `;` at top level (governance clause separator)."""
    body = (
        "`CLAUDE.md` §6 第 8 条 (amended by `bec147d`); "
        "change `migrate-l678-source` design.md (Decision 1)"
    )
    items = L._split_top_level_items(body)
    assert len(items) == 2
    assert items[0].startswith("`CLAUDE.md`")
    assert items[1].startswith("change `migrate-l678-source`")


def test_split_top_level_items_handles_no_delimiter() -> None:
    """`_split_top_level_items` returns a single-item list when no top-level delimiter."""
    body = "`wayfinder/tickets/A2-1.md`"
    items = L._split_top_level_items(body)
    assert items == ["`wayfinder/tickets/A2-1.md`"]


# --- Orchestrator tests -----------------------------------------------------

def test_first_item_must_be_primary_reverse_link() -> None:
    """`lint_file` flags a Source line whose first item is `change ... design.md (Decision N)`."""
    import tempfile
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(
            "# Test spec\n\n"
            "**Source:** change `foo` design.md (Decision 1), "
            "`wayfinder/tickets/A2-1.md`\n"
        )
        p = Path(f.name)
    try:
        violations = L.lint_file(p)
        # Expect exactly one violation: "first item is not the primary reverse-link".
        # The line also contains a backtick-wrapped reverse-link so check 2 passes.
        reasons = [v[2] for v in violations]
        assert any("first item is not the primary reverse-link" in r for r in reasons), (
            f"Expected first-item violation, got reasons={reasons}"
        )
    finally:
        p.unlink()


def test_first_item_is_primary_passes() -> None:
    """`lint_file` reports 0 violations when the first item IS the primary reverse-link."""
    import tempfile
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(
            "# Test spec\n\n"
            "**Source:** `wayfinder/tickets/A2-1.md`, "
            "change `foo` design.md (Decision 1)\n"
        )
        p = Path(f.name)
    try:
        violations = L.lint_file(p)
        assert violations == [], f"Expected 0 violations, got {violations}"
    finally:
        p.unlink()


def test_capability_aware_default_requires_wayfinder_tickets() -> None:
    """`lint_file` flags a `wayfinder/` Source line missing `wayfinder/tickets/`."""
    import tempfile
    # Use a path that does NOT match the governance suffix in the per-capability table.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# Test spec\n\n**Source:** `some/other/ref.md`\n")
        p = Path(f.name)
    try:
        violations = L.lint_file(p)
        reasons = [v[2] for v in violations]
        assert any(
            "missing required reverse-link" in r and "wayfinder/tickets/" in r
            for r in reasons
        ), f"Expected wayfinder/tickets/ missing violation, got reasons={reasons}"
    finally:
        p.unlink()


def test_capability_aware_governance_requires_CLAUDE_md() -> None:
    """`lint_file` flags a `governance/` Source line missing `CLAUDE.md`."""
    import tempfile
    # The governance table key is `<repo_root>/openspec/specs/governance/spec.md`.
    # Build the synthetic spec under a temp file but place it via a symlink-like
    # path-resolution trick: we pass the tempfile's resolved path through
    # `required_substring_for` after temporarily replacing the per-capability
    # table with a single entry that matches the tempfile's stem.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        # Source line has the wayfinder reverse-link but NOT CLAUDE.md, simulating
        # a governance spec that was incorrectly annotated.
        f.write(
            "# Test spec\n\n"
            "**Source:** `wayfinder/tickets/A2-1.md`, change `foo` design.md (Decision 1)\n"
        )
        p = Path(f.name).resolve()
    try:
        # Temporarily replace the per-capability table so `p` matches the
        # governance suffix, then restore the original table. This avoids
        # monkey-patching `required_substring_for` (which would change the
        # function's identity, breaking later tests).
        original_table = dict(L.REQUIRED_SUBSTRING_BY_PATH_RELATIVE)
        L.REQUIRED_SUBSTRING_BY_PATH_RELATIVE = {p: "CLAUDE.md"}
        try:
            violations = L.lint_file(p)
        finally:
            L.REQUIRED_SUBSTRING_BY_PATH_RELATIVE = original_table
        reasons = [v[2] for v in violations]
        assert any(
            "missing required reverse-link" in r and "CLAUDE.md" in r
            for r in reasons
        ), f"Expected CLAUDE.md missing violation, got reasons={reasons}"
    finally:
        p.unlink()


def test_unbackticked_refs_via_lint_file() -> None:
    """`lint_file` flags a Source line whose reverse-link is NOT backtick-wrapped."""
    import tempfile
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        # The required substring `wayfinder/tickets/` appears OUTSIDE backticks.
        f.write("# Test spec\n\n**Source:** wayfinder/tickets/A6a-2.md (initial)\n")
        p = Path(f.name)
    try:
        violations = L.lint_file(p)
        reasons = [v[2] for v in violations]
        assert any("unbackticked reverse-link" in r for r in reasons), (
            f"Expected unbackticked violation, got reasons={reasons}"
        )
    finally:
        p.unlink()


def test_first_item_is_primary_with_historical_annotation() -> None:
    """Scenarios 2: a Source line with `(historical, ...)` annotation is recognized as 0 violations.

    The line ``**Source:** `wayfinder/tickets/A6a-2.md` (historical, threshold `1/128`), change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold superseded by `1/(2·N_e)`)``
    is the canonical live form (wayfinder/spec.md L251). The paren annotation
    uses bare values (`1/128`, `1/(2·N_e)`) and bare ticket IDs (e.g. `A6a-2.md`
    as a context reference) — NOT bare full-path references. The lint script
    must produce 0 violations because:
      - check ①: `wayfinder/tickets/` is present (in the backticked first item)
      - check ②: every occurrence of `wayfinder/tickets/` is backtick-wrapped
        (the bare ID `A6a-2.md` does NOT contain the `wayfinder/tickets/` prefix,
        so it is correctly NOT flagged)
      - check ③: the first top-level item is `` `wayfinder/tickets/A6a-2.md` ``
        with the required substring in its code span
    """
    import tempfile
    body = (
        "`wayfinder/tickets/A6a-2.md` (historical, threshold `1/128`), "
        "change `fix-openspec-doc-bugs` design.md (Decision 7 — threshold superseded by `1/(2·N_e)`)"
    )
    # Helper-level structural check first (this is the "principle-level" assertion):
    # the split must produce exactly 2 items (paren comma in `(Decision 7 — ...)`
    # does NOT split, paren-internal commas inside `(historical, threshold ...)`
    # do NOT split), and the first item must be the backticked primary.
    items = L._split_top_level_items(body)
    assert len(items) == 2, (
        f"Expected 2 top-level items (paren-internal commas do not split), "
        f"got {len(items)}: {items}"
    )
    first_span = L._first_code_span(items[0])
    assert first_span == "wayfinder/tickets/A6a-2.md", (
        f"Expected first code span = primary reverse-link, got {first_span!r}"
    )
    assert "wayfinder/tickets/" in (first_span or ""), (
        f"Expected required substring in first code span, got {first_span!r}"
    )
    # No unbackticked occurrences (the bare `1/128` and `1/(2·N_e)` values do
    # NOT contain the `wayfinder/tickets/` prefix; the paren-annotation's
    # ticket references like `A6a-2.md` are bare IDs without prefix).
    assert L._unbackticked_refs(body, "wayfinder/tickets/") == [], (
        "Historical-annotation line must NOT flag unbackticked reverse-links "
        "because its paren annotations use bare values and bare ticket IDs"
    )
    # End-to-end: full lint_file on a synthetic file must report 0 violations.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(f"# Test spec\n\n**Source:** {body}\n")
        p = Path(f.name)
    try:
        violations = L.lint_file(p)
        assert violations == [], (
            f"Historical-annotation line must pass all 3 checks; got {violations}"
        )
    finally:
        p.unlink()


def test_multiple_backticked_reverse_links_pass() -> None:
    """Scenarios 4 第 4 AND: multiple backticked reverse-links on a single line all pass.

    The canonical example is `**Source:** `wayfinder/tickets/A2-1.md`, `wayfinder/tickets/A2-2.md``.
    The lint script must:
      - check ①: pass (line contains `wayfinder/tickets/`)
      - check ②: pass (BOTH occurrences are backtick-wrapped; no unbackticked refs)
      - check ③: pass (first top-level item is `` `wayfinder/tickets/A2-1.md` ``,
        which contains the required substring in its code span)
    """
    import tempfile
    body = "`wayfinder/tickets/A2-1.md`, `wayfinder/tickets/A2-2.md`"
    # Helper-level structural assertions (principle-level):
    items = L._split_top_level_items(body)
    assert len(items) == 2, f"Expected 2 items (comma outside code span splits), got {items}"
    assert L._first_code_span(items[0]) == "wayfinder/tickets/A2-1.md", (
        f"First item's code span must be the first ticket, got {L._first_code_span(items[0])!r}"
    )
    assert L._unbackticked_refs(body, "wayfinder/tickets/") == [], (
        "Both occurrences are backticked; no unbackticked violations expected"
    )
    # End-to-end: full lint_file must report 0 violations.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(f"# Test spec\n\n**Source:** {body}\n")
        p = Path(f.name)
    try:
        violations = L.lint_file(p)
        assert violations == [], (
            f"Multi-ticket line must pass all 3 checks; got {violations}"
        )
    finally:
        p.unlink()


def test_one_line_multiple_independent_violations() -> None:
    """Rule body 3 第 2 句: a single line may trigger multiple independent violations.

    The canonical case: ``**Source:** change `foo` design.md (Decision 1), wayfinder/tickets/A2-1.md``
    - check ①a: PASS (`wayfinder/tickets/` is present in the line)
    - check ①b: FAIL (AC-24 — the only code span on the line is `foo`, so no
      backtick-wrapped span names a concrete `wayfinder/tickets/<ID>.md` file)
    - check ②: FAIL (the `wayfinder/tickets/` occurrence is bare, not backticked)
    - check ③: FAIL (first item is the change-decision clause
      `` change `foo` design.md (Decision 1) ``, not the backticked primary;
      first_code_span is `foo`, which does NOT contain `wayfinder/tickets/`)

    Expected: exactly 3 violations with distinct reason codes, not 1.

    Count moved from 2 to 3 when check ①b (reverse-link form presence) was
    added: the bare `wayfinder/tickets/A2-1.md` on this line is independently
    un-backticked (②) and independently un-formed (①b). The property under
    test — one line, several independent violations — is unchanged; the line is
    now a strictly stronger witness for it.
    """
    import tempfile
    body = "change `foo` design.md (Decision 1), wayfinder/tickets/A2-1.md"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(f"# Test spec\n\n**Source:** {body}\n")
        p = Path(f.name)
    try:
        violations = L.lint_file(p)
        reasons = [v[2] for v in violations]
        assert len(violations) == 3, (
            f"Expected exactly 3 violations (concrete-file + unbackticked + "
            f"first-item-not-primary), got {len(violations)}: {reasons}"
        )
        assert any("must name a concrete file" in r for r in reasons), (
            f"Expected 'must name a concrete file' reason, got {reasons}"
        )
        assert any("unbackticked reverse-link" in r for r in reasons), (
            f"Expected 'unbackticked reverse-link' reason, got {reasons}"
        )
        assert any("first item is not the primary reverse-link" in r for r in reasons), (
            f"Expected 'first item is not the primary reverse-link' reason, got {reasons}"
        )
        # All three violations must be on the same line (the Source line).
        assert all(v[0] == violations[0][0] for v in violations), (
            f"All violations should be on the same Source line, got {violations}"
        )
    finally:
        p.unlink()


# --- Live regression tests --------------------------------------------------

def test_no_violations_after_pre_archive_patch() -> None:
    """The post-pre-archive-patch live spec tree has 0 violations."""
    wayfinder_spec = _REPO_ROOT / "openspec" / "specs" / "wayfinder" / "spec.md"
    skeleton_spec = _REPO_ROOT / "openspec" / "specs" / "decompmoe-skeleton" / "spec.md"
    wf_violations = L.lint_file(wayfinder_spec)
    sk_violations = L.lint_file(skeleton_spec)
    assert wf_violations == [], (
        f"Expected 0 violations in wayfinder/spec.md, got {wf_violations}"
    )
    assert sk_violations == [], (
        f"Expected 0 violations in decompmoe-skeleton/spec.md, got {sk_violations}"
    )


def test_governance_spec_passes_structural_checks() -> None:
    """`openspec/specs/governance/spec.md` passes ① + ② + ③."""
    governance_spec = _REPO_ROOT / "openspec" / "specs" / "governance" / "spec.md"
    violations = L.lint_file(governance_spec)
    assert violations == [], (
        f"Expected 0 violations in governance/spec.md, got {violations}"
    )


# --- AC-24: reverse-link FORM presence (check ①b) -----------------------------
#
# Audit item AC-24: the gate required only the directory prefix
# `wayfinder/tickets/`, so the bare-directory form and the extension-less form
# `wayfinder/tickets/A4-1` were indistinguishable from the canonical
# `wayfinder/tickets/A4-1.md`. An untraceable lineage could therefore pass.
# Check ①b closes that by requiring a backtick-wrapped concrete filename.


def _write_spec_with_source_line(body: str) -> Path:
    """Write a throwaway single-Source-line spec and return its path."""
    import tempfile
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(f"# Test spec\n\n**Source:** {body}\n")
        return Path(f.name)


def test_bare_directory_form_is_rejected() -> None:
    """The bare directory form is NOT lineage — check ①b MUST reject it.

    This is the exact AC-24 gap: before ①b this line produced 0 violations
    because `wayfinder/tickets/` was present, backticked, and first.
    """
    p = _write_spec_with_source_line(
        "`wayfinder/tickets/`, change `foo` design.md (Decision 1)"
    )
    try:
        violations = L.lint_file(p)
        reasons = [v[2] for v in violations]
        assert any("must name a concrete file" in r for r in reasons), (
            f"Bare directory form must be rejected by check ①b, got {reasons}"
        )
    finally:
        p.unlink()


def test_extensionless_ticket_id_form_is_rejected() -> None:
    """``wayfinder/tickets/A4-1`` without ``.md`` MUST be rejected.

    This is the second indistinguishable form named by AC-24: it names a real
    ticket id but is not a file, so the reverse-link does not resolve.
    """
    p = _write_spec_with_source_line(
        "`wayfinder/tickets/A4-1`, change `foo` design.md (Decision 1)"
    )
    try:
        violations = L.lint_file(p)
        reasons = [v[2] for v in violations]
        assert any("must name a concrete file" in r for r in reasons), (
            f"Extension-less ticket id form must be rejected, got {reasons}"
        )
    finally:
        p.unlink()


def test_concrete_ticket_filename_form_passes() -> None:
    """The canonical ``wayfinder/tickets/<ID>.md`` form MUST pass unchanged."""
    p = _write_spec_with_source_line(
        "`wayfinder/tickets/A4-1.md`, change `foo` design.md (Decision 1)"
    )
    try:
        violations = L.lint_file(p)
        assert violations == [], (
            f"Canonical ticket filename form must pass, got {violations}"
        )
    finally:
        p.unlink()


def test_tightened_check_accepts_governance_claude_md_form() -> None:
    """Tightening ①b MUST NOT break the governance ``CLAUDE.md`` form.

    Regression guard against a tightening that is asymmetric: governance has no
    ticket file to name, so its form pattern is the literal ``CLAUDE.md``.
    """
    p = _write_spec_with_source_line("`CLAUDE.md` §6")
    try:
        original_table = dict(L.REQUIRED_SUBSTRING_BY_PATH_RELATIVE)
        L.REQUIRED_SUBSTRING_BY_PATH_RELATIVE = {p.resolve(): "CLAUDE.md"}
        try:
            violations = L.lint_file(p)
        finally:
            L.REQUIRED_SUBSTRING_BY_PATH_RELATIVE = original_table
        assert violations == [], (
            f"Governance CLAUDE.md form must still pass, got {violations}"
        )
    finally:
        p.unlink()


def test_code_spans_ignores_unterminated_backtick() -> None:
    """`_code_spans` must not credit a span the line never closed.

    Without this, a line ending in a dangling backtick could satisfy ①b with a
    span that does not exist — turning the tightening into a new bypass.
    """
    assert L._code_spans("`wayfinder/tickets/A4-1.md`") == ["wayfinder/tickets/A4-1.md"]
    assert L._code_spans("`wayfinder/tickets/A4-1.md") == []
    assert L._code_spans("no code spans here") == []
    assert L._code_spans("`a` and `b`") == ["a", "b"]


def test_live_spec_tree_passes_tightened_form_check() -> None:
    """All three live spec files pass ①b — the tightening breaks no real field.

    Guards the failure mode where a tightening is correct in isolation but
    reddens the live tree (i.e. the change cannot land).
    """
    for capability in ("wayfinder", "decompmoe-skeleton", "governance"):
        spec = _REPO_ROOT / "openspec" / "specs" / capability / "spec.md"
        violations = L.lint_file(spec)
        assert violations == [], (
            f"Expected 0 violations in {capability}/spec.md under the tightened "
            f"check ①b, got {violations}"
        )


# --- AC-81: a leading prefix must not hide a Source field --------------------


def _write_spec_with_prefixed_source_line(prefix: str, body: str) -> Path:
    """Write a spec whose single Source line carries `prefix` before the field."""
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(f"# Test spec\n\n{prefix}**Source:** {body}\n")
        return Path(f.name)


@pytest.mark.parametrize(
    ("label", "prefix"),
    [
        ("blockquote", "> "),
        ("two_spaces", "  "),
        ("ordered_list", "1. "),
    ],
)
def test_prefixed_source_line_is_still_checked(label: str, prefix: str) -> None:
    """AC-81: `^\\*\\*Source:\\*\\*` let a prefixed field bypass every check.

    Under the old line-start anchor, `iter_source_lines` never yielded this
    line at all, so `lint_file` returned `[]` — a Source field with a
    non-canonical reverse-link passed silently. The bare-directory body below is
    the exact form check ①b exists to reject, so a zero-violation result here
    means the prefix is still a bypass.
    """
    p = _write_spec_with_prefixed_source_line(
        prefix, "`wayfinder/tickets/`, change `foo` design.md (Decision 1)"
    )
    try:
        violations = L.lint_file(p)
        reasons = [v[2] for v in violations]
        assert any("must name a concrete file" in r for r in reasons), (
            f"{label}: prefixed Source line was not checked, got {reasons}"
        )
    finally:
        p.unlink()


def test_prefixed_but_canonical_source_line_is_accepted() -> None:
    """The relaxation must not redden a *correct* field that happens to be quoted.

    The other half of AC-81: relaxing the anchor is only safe if the body is
    sliced at the match end. With a fixed-length slice, `> **Source:** ` loses
    its first 10 characters to the slice and the body becomes `ource:** ...`,
    which then fails ① for the wrong reason. This test fails if that coupling
    ever comes back.
    """
    p = _write_spec_with_prefixed_source_line(
        "> ", "`wayfinder/tickets/A4-1.md`, change `foo` design.md (Decision 1)"
    )
    try:
        assert L.lint_file(p) == [], (
            f"a correctly formed quoted Source field must pass, got {L.lint_file(p)}"
        )
    finally:
        p.unlink()


def test_lint_reports_a_source_line_yielded_without_matching_the_pattern(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `internal:` guard is reachable and MUST be driven, not merely present.

    `req-gov-11` requires that a line handed to the body-slicer by
    `iter_source_lines` but not matched by `SOURCE_LINE_RE` be reported as an
    internal inconsistency rather than silently skipped. Without a test, that
    MUST is unfalsifiable: the branch is currently unreachable through the real
    generator, so the clause could be deleted from the spec, or the branch
    deleted from the lint, and the suite would stay green either way.

    Here the generator is stubbed to yield exactly that state, which is the only
    way to reach the branch. This pins the *behaviour* (an unmatchable yielded
    line is reported, not dropped), not the existence of a comment.
    """
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# Test spec\n\nplain prose that is not a Source field\n")
        spec = Path(f.name)

    def _bad_generator(paths):
        # Yields a line the pattern will NOT match -- the exact inconsistency
        # the guard exists to catch.
        for p in paths:
            yield p, 3, "plain prose that is not a Source field"

    monkeypatch.setattr(L, "iter_source_lines", _bad_generator)
    try:
        violations = L.lint_file(spec)
        assert any("internal:" in reason for _, _, reason in violations), (
            f"an unmatchable yielded line must be reported, not skipped: {violations!r}"
        )
        assert any(
            "without matching SOURCE_LINE_RE" in reason for _, _, reason in violations
        ), f"the reason must name the inconsistency: {violations!r}"
    finally:
        spec.unlink()


def test_source_body_is_sliced_at_the_match_end_not_a_fixed_length() -> None:
    """Pin the coupling directly, so the invariant survives a future refactor.

    Asserts the property rather than the symptom: for every prefix, the sliced
    body must start with the reverse-link, never with a fragment of the marker.
    """
    for prefix in ("", "> ", "  ", "1. ", "   >   1. "):
        line = f"{prefix}**Source:** `wayfinder/tickets/A4-1.md`"
        m = L.SOURCE_LINE_RE.match(line)
        assert m is not None, f"prefix {prefix!r} was not matched at all"
        body = line[m.end():].strip()
        assert body.startswith("`wayfinder/"), (
            f"prefix {prefix!r} produced a mis-sliced body {body!r}"
        )


# --- check ④: Source field presence ----------------------------------------


def _write_spec(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "spec.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_requirement_without_a_source_field_is_reported(tmp_path: Path) -> None:
    """A Requirement with no field at all is the gap checks ①-③ cannot see.

    `lint_file` returns `[]` for this file, because `iter_source_lines` yields
    nothing to check. Only the presence check sees it.
    """
    p = _write_spec(
        tmp_path,
        '<a id="req-99"></a>\n\n### Requirement: No Lineage\n\nbody\n',
    )
    assert L.lint_file(p) == [], "format checks should have nothing to say here"
    problems = L.check_source_presence(p, capability="tmpcap")
    assert len(problems) == 1, problems
    assert "no top-level **Source:** field" in problems[0], problems[0]
    assert "req-99" in problems[0], problems[0]


def test_grandfathered_requirement_is_not_reported(tmp_path: Path) -> None:
    p = _write_spec(
        tmp_path,
        '<a id="req-1"></a>\n\n### Requirement: Legacy\n\nbody\n',
    )
    # `decompmoe-skeleton`/`req-1` is in the registry.
    assert L.check_source_presence(p, capability="decompmoe-skeleton") == []
    # The same anchor id in another capability is NOT covered by that entry.
    assert L.check_source_presence(p, capability="wayfinder") != []


def test_exemption_does_not_transfer_across_capabilities(tmp_path: Path) -> None:
    """The registry key is `(capability, anchor_id)`, not the id alone.

    A bare-id registry would let a new capability's `req-1` pass unchecked,
    which is the same shape of bypass as the prefix hole AC-81 found.
    """
    assert all(
        isinstance(k, tuple) and len(k) == 2 for k in L.SOURCE_EXEMPTIONS
    ), "registry entries must be (capability, anchor_id) pairs"
    p = _write_spec(tmp_path, '<a id="req-34"></a>\n\n### Requirement: X\n\nb\n')
    assert L.check_source_presence(p, capability="decompmoe-skeleton") != []


def test_stale_entry_for_a_removed_requirement_is_reported(tmp_path: Path) -> None:
    """A registry entry naming a Requirement that no longer exists is a finding.

    Whole-tree by necessity: "no longer exists" is only decidable against the
    complete spec for a capability, so this lives in `check_registry_stale`
    rather than the per-file presence check.
    """
    specs = tmp_path / "specs" / "decompmoe-skeleton"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        '<a id="req-1"></a>\n\n### Requirement: Still Here\n\nb\n', encoding="utf-8"
    )
    problems = L.check_registry_stale(tmp_path / "specs")
    removed = [m for m in problems if "no longer exists" in m]
    # req-1 is present, so it must not be reported as removed; the 19 other
    # skeleton entries are absent from this synthetic tree and must be.
    assert not any("decompmoe-skeleton/req-1 " in m for m in removed), removed
    assert any("decompmoe-skeleton/req-2 " in m for m in removed), removed


def test_stale_entry_now_carrying_a_field_is_reported(tmp_path: Path) -> None:
    """A backfilled Requirement must retire its exemption, or the gate lies.

    This is the per-file half: decidable from the file alone, because the
    anchor is right there and now carries a field.
    """
    p = _write_spec(
        tmp_path,
        '<a id="req-1"></a>\n\n### Requirement: Backfilled\n\n'
        "**Source:** `wayfinder/tickets/A0-1.md`\n\nbody\n",
    )
    problems = L.check_source_presence(p, capability="decompmoe-skeleton")
    assert any("stale" in m and "prune the registry" in m for m in problems), (
        f"a registry entry whose Requirement now has a field must be reported: {problems}"
    )


def test_stale_entry_for_a_capability_with_no_spec_is_reported(tmp_path: Path) -> None:
    """An entry for a capability that has no spec file exempts nothing."""
    specs = tmp_path / "specs" / "wayfinder"
    specs.mkdir(parents=True)
    (specs / "spec.md").write_text(
        '<a id="req-1"></a>\n\n### Requirement: X\n\nb\n', encoding="utf-8"
    )
    problems = L.check_registry_stale(tmp_path / "specs")
    assert any("no spec file" in m for m in problems), problems


def test_section_sub_anchor_is_not_counted_as_a_requirement(tmp_path: Path) -> None:
    """A block-level sub-anchor must not create a phantom missing-field violation.

    This is the defect that truncated Requirement blocks three times in this
    repository's archive history, seen from the other side: if the sub-anchor
    were treated as a block start, a following `#### Scenario:` would look like
    a Requirement heading with no Source field.
    """
    p = _write_spec(
        tmp_path,
        '<a id="req-1"></a>\n\n### Requirement: Real\n\n'
        "**Source:** `wayfinder/tickets/A0-1.md`\n\n"
        '<a id="req-1-mci"></a>\n\n#### Scenario: inner\n\nbody\n',
    )
    assert L.check_source_presence(p, capability="wayfinder") == []


def test_inline_anchor_in_prose_is_not_a_block_start(tmp_path: Path) -> None:
    p = _write_spec(
        tmp_path,
        "Prose mentioning <a id=\"req-1\"></a> inline.\n\n"
        '<a id="req-2"></a>\n\n### Requirement: Real\n\n'
        "**Source:** `wayfinder/tickets/A0-1.md`\n",
    )
    problems = L.check_source_presence(p, capability="wayfinder")
    assert problems == [], f"inline anchor must not become a Requirement: {problems}"


def test_unparseable_file_is_reported_not_silently_passed(tmp_path: Path) -> None:
    """Zero Requirements parsed is a finding, not an empty pass.

    The `all(...)`-over-an-empty-list failure: a parser that silently matches
    nothing makes every downstream count zero and the gate green.
    """
    p = _write_spec(tmp_path, "just prose, no anchors, no headings\n")
    problems = L.check_source_presence(p, capability="wayfinder")
    assert len(problems) == 1, problems
    assert "no Requirement blocks parsed" in problems[0], problems[0]


def test_live_tree_reports_no_unregistered_missing_field() -> None:
    """The live specs must have no missing field outside the registry."""
    total_exempt = 0
    for capability in ("wayfinder", "decompmoe-skeleton", "governance"):
        spec = _REPO_ROOT / "openspec" / "specs" / capability / "spec.md"
        problems = L.check_source_presence(spec, capability=capability)
        assert problems == [], (
            f"{capability}: ungrandfathered Source-field problems: {problems}"
        )
        lines = spec.read_text(encoding="utf-8").splitlines()
        total_exempt += sum(
            1 for _, aid, _, has in L.requirement_blocks(lines)
            if not has and (capability, aid) in L.SOURCE_EXEMPTIONS
        )
    assert total_exempt == len(L.SOURCE_EXEMPTIONS), (
        f"registry lists {len(L.SOURCE_EXEMPTIONS)} entries but only {total_exempt} "
        "are actually missing a field -- the registry has stale entries"
    )
