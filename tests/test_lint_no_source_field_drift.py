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
    - check ①: PASS (`wayfinder/tickets/` is present in the line)
    - check ②: FAIL (the `wayfinder/tickets/` occurrence is bare, not backticked)
    - check ③: FAIL (first item is the change-decision clause
      `` change `foo` design.md (Decision 1) ``, not the backticked primary;
      first_code_span is `foo`, which does NOT contain `wayfinder/tickets/`)

    Expected: exactly 2 violations with distinct reason codes, not 1.
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
        assert len(violations) == 2, (
            f"Expected exactly 2 violations (unbackticked + first-item-not-primary), "
            f"got {len(violations)}: {reasons}"
        )
        assert any("unbackticked reverse-link" in r for r in reasons), (
            f"Expected 'unbackticked reverse-link' reason, got {reasons}"
        )
        assert any("first item is not the primary reverse-link" in r for r in reasons), (
            f"Expected 'first item is not the primary reverse-link' reason, got {reasons}"
        )
        # The two violations must both be on the same line (the Source line).
        assert all(v[0] == violations[0][0] for v in violations), (
            f"Both violations should be on the same Source line, got {violations}"
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
