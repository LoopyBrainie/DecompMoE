"""Tests for `scripts.run_gates`: snapshot discipline and the anchor ledger.

The gate runner exists to fix audit items AC-19, AC-20, AC-21, AC-25, AC-49
and AC-80. Each of those was a way for a gate to report green without having
checked anything, so the tests below are mostly *negative*: they assert the
runner goes red (or, for a changed worktree, goes to exit 2) on inputs where a
hollow runner would have passed.

Load pattern mirrors `tests/test_lint_no_source_field_drift.py`: the script
lives in `scripts/`, which is NOT on the pyproject `pythonpath`, so it is loaded
with `importlib` rather than by putting `scripts/` on `sys.path` (the repo
treats that as an anti-pattern — lint infrastructure is not first-party code).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "run_gates.py"
_spec = importlib.util.spec_from_file_location("_run_gates_under_test", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None, "Could not load run_gates spec"
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)
del _spec


# --- snapshot discipline (AC-25) --------------------------------------------


def test_snapshot_differs_names_every_moved_field() -> None:
    """A changed HEAD, a changed dirty-state digest, or a changed line count
    must each be reported — not collapsed into a single boolean."""
    before = {"head": "aaaa", "status_sha256": "1111", "status_lines": 3}
    after = {"head": "bbbb", "status_sha256": "2222", "status_lines": 4}
    moved = G._snapshot_differs(before, after)
    assert len(moved) == 3, f"Expected all 3 fields reported, got {moved}"
    assert any("head" in m for m in moved)
    assert any("status_sha256" in m for m in moved)
    assert any("status_lines" in m for m in moved)


def test_snapshot_differs_is_empty_for_identical_snapshots() -> None:
    """Two identical snapshots must report no movement at all."""
    snap = {"head": "aaaa", "status_sha256": "1111", "status_lines": 3}
    assert G._snapshot_differs(snap, dict(snap)) == []


def test_worktree_snapshot_has_all_three_components() -> None:
    """The real repo snapshot must carry all three discriminating components."""
    snap = G.worktree_snapshot()
    assert set(snap) == {"head", "status_sha256", "status_lines"}
    assert len(snap["head"]) == 40, f"HEAD should be a full sha, got {snap['head']!r}"
    assert len(snap["status_sha256"]) == 64
    assert isinstance(snap["status_lines"], int)


def test_gates_exit_2_when_worktree_changes_during_run(monkeypatch, capsys) -> None:
    """A worktree that moves mid-run must yield exit 2, NOT exit 0.

    This is the AC-25 regression in its sharpest form. A hollow runner would
    print green here: every gate passed, and nobody looked at whether the tree
    they judged still existed afterwards.
    """
    calls = {"n": 0}

    def fake_snapshot() -> dict[str, object]:
        calls["n"] += 1
        if calls["n"] == 1:
            return {"head": "a" * 40, "status_sha256": "1" * 64, "status_lines": 1}
        return {"head": "a" * 40, "status_sha256": "2" * 64, "status_lines": 2}

    monkeypatch.setattr(G, "worktree_snapshot", fake_snapshot)
    monkeypatch.setattr(G, "discover_lints", lambda: [Path("fake_lint.py")])
    monkeypatch.setattr(G, "_run", lambda cmd: (0, "ok"))
    monkeypatch.setattr(G, "check_anchor_coverage", lambda: [])

    rc = G.main(["--skip-pytest"])
    out = capsys.readouterr().out
    assert rc == G.EXIT_INVALID, f"Expected exit 2, got {rc}. Output:\n{out}"
    assert "GATE RESULT INVALID" in out, out
    assert "do not read this as a pass" in out, out


def test_gates_exit_0_on_stable_worktree(monkeypatch, capsys) -> None:
    """The control case: a stable worktree with all gates green is exit 0."""
    snap = {"head": "a" * 40, "status_sha256": "1" * 64, "status_lines": 1}
    monkeypatch.setattr(G, "worktree_snapshot", lambda: dict(snap))
    monkeypatch.setattr(G, "discover_lints", lambda: [Path("fake_lint.py")])
    monkeypatch.setattr(G, "_run", lambda cmd: (0, "ok"))
    monkeypatch.setattr(G, "check_anchor_coverage", lambda: [])

    rc = G.main(["--skip-pytest"])
    out = capsys.readouterr().out
    assert rc == G.EXIT_OK, f"Expected exit 0, got {rc}. Output:\n{out}"
    assert "GATE OK" in out, out


# --- gate discovery (AC-20 / AC-21) -----------------------------------------


def test_zero_discovered_lints_is_a_failure_not_a_pass(monkeypatch, capsys) -> None:
    """Zero checks must NOT report a pass.

    `all([])` is vacuously true in Python, so the obvious implementation of
    "run every discovered lint and pass if none failed" reports green having
    run nothing. The runner must assert the count first.
    """
    monkeypatch.setattr(G, "discover_lints", lambda: [])
    rc = G.main(["--skip-pytest"])
    err = capsys.readouterr().err
    assert rc == G.EXIT_FAIL, f"Expected exit 1 with zero lints, got {rc}"
    assert "no lints discovered" in err, err
    assert "zero checks is not a passing gate" in err, err


def test_discover_lints_glob_returns_every_lint_and_is_sorted() -> None:
    """Discovery is a glob, so a newly added lint joins the gate automatically.

    This is the property that makes `CLAUDE.md` §3 able to stop enumerating
    lint scripts (AC-20): the list and the gate can no longer drift apart.
    """
    lints = G.discover_lints()
    assert len(lints) >= 2, f"Expected the repo's lints, got {[p.name for p in lints]}"
    assert lints == sorted(lints), "discover_lints must return a stable order"
    assert all(p.name.startswith("lint_") and p.suffix == ".py" for p in lints)
    assert all(p.parent == G.SCRIPTS_DIR for p in lints)


# --- `--change` scoping (AC-49) ---------------------------------------------


def test_change_flag_validates_only_the_named_change(monkeypatch) -> None:
    """`--change X` must run `openspec validate X --type change --strict` and
    nothing else — no sweep over the other unarchived changes.

    Sweeping the whole directory would let two unrelated stale changes redden
    a gate that is about to pass, which is precisely how a gate list gets
    switched off in practice.
    """
    monkeypatch.setattr(G, "worktree_snapshot", lambda: {
        "head": "a" * 40, "status_sha256": "1" * 64, "status_lines": 0})
    monkeypatch.setattr(G, "discover_lints", lambda: [])
    recorded: list[list[str]] = []

    def fake_run(cmd: list[str]) -> tuple[int, str]:
        recorded.append(list(cmd))
        return 0, "ok"

    monkeypatch.setattr(G, "_run", fake_run)
    G.main(["--skip-pytest"])  # expected to fail on zero lints; recorded is reset below
    recorded.clear()

    monkeypatch.setattr(G, "discover_lints", lambda: [Path("fake_lint.py")])
    G.main(["--change", "my-change", "--skip-pytest"])

    openspec_cmds = [c for c in recorded if c[0] == "openspec"]
    assert openspec_cmds == [
        ["openspec", "validate", "--specs", "--strict"],
        ["openspec", "validate", "my-change", "--type", "change", "--strict"],
    ], f"Unexpected openspec invocations: {openspec_cmds}"


def test_change_flag_absent_runs_no_change_validation(monkeypatch) -> None:
    """Without `--change`, no change-level validation is performed."""
    monkeypatch.setattr(G, "worktree_snapshot", lambda: {
        "head": "a" * 40, "status_sha256": "1" * 64, "status_lines": 0})
    monkeypatch.setattr(G, "discover_lints", lambda: [Path("fake_lint.py")])
    recorded: list[list[str]] = []
    monkeypatch.setattr(
        G, "_run", lambda cmd: (recorded.append(list(cmd)) or (0, "ok"))
    )
    monkeypatch.setattr(G, "check_anchor_coverage", lambda: [])

    G.main(["--skip-pytest"])
    assert [c for c in recorded if "--type" in c] == [], (
        f"Change validation must not run without --change, got {recorded}"
    )


# --- block boundary rule ----------------------------------------------------


def test_block_starts_requires_requirement_heading_after_anchor() -> None:
    """Only an anchor immediately followed by `### Requirement:` opens a block.

    Using "the next line is a heading" instead yields a one-line shell, and a
    block-level anchor inserted mid-body would truncate its own Requirement —
    reproduced three times in this repo's archive history.
    """
    lines = [
        '<a id="req-1"></a>',
        '### Requirement: First',
        '',
        'body',
        '',
        '<a id="req-2-thing"></a>',      # inline mention inside prose
        '',
        'not a heading',
        '',
        '<a id="req-3"></a>',           # separated by a blank line — still a block
        '',
        '### Requirement: Third',
    ]
    starts = G.block_starts(lines)
    assert [a for _, a, _ in starts] == ["req-1", "req-3"], starts
    assert [t for _, _, t in starts] == ["First", "Third"], starts


def test_block_starts_ignores_anchor_with_no_following_heading() -> None:
    """An anchor at end-of-file, or one followed by prose, is not a block."""
    assert G.block_starts(['<a id="req-9"></a>']) == []
    assert G.block_starts(['<a id="req-9"></a>', 'just prose']) == []
    assert G.block_starts(['<a id="req-9"></a>', '', '   ', '']) == []


# --- anchor ledger (AC-19 / AC-80) ------------------------------------------


def _write_ledger_file(tmp_path: Path, ledger: dict, expect_new: list[str] | None = None) -> Path:
    path = tmp_path / "ledger.json"
    path.write_text(
        json.dumps(
            {"written_at_head": "0" * 40, "expect_new": expect_new or [], "ledger": ledger},
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def test_ledger_round_trip_on_live_tree(tmp_path, capsys) -> None:
    """write → verify against the real spec tree must report OK.

    Anchors the regression this guards: a ledger that reports drift on a
    healthy tree gets ignored, and then it never catches a real loss.
    """
    ledger_file = tmp_path / "before.json"
    assert G.main(["anchor-ledger", "--write", str(ledger_file)]) == G.EXIT_OK
    payload = json.loads(ledger_file.read_text(encoding="utf-8"))
    total = sum(len(v) for v in payload["ledger"].values())
    assert total > 0, "Live tree must have anchors"

    assert G.main(["anchor-ledger", "--verify", str(ledger_file)]) == G.EXIT_OK
    assert "OK" in capsys.readouterr().out


def test_verify_reports_lost_anchor_by_id_and_title(tmp_path, monkeypatch, capsys) -> None:
    """A dropped anchor MUST be named — id and the Requirement it introduced.

    An unnamed "1 anchor missing" is not actionable: the archive operator needs
    to know *which* Requirement lost its header to put it back.
    """
    live = {"wayfinder": {"req-1": "First"}}
    baseline = _write_ledger_file(tmp_path, {"wayfinder": {"req-1": "First", "req-2": "Second"}})
    monkeypatch.setattr(G, "anchor_ledger", lambda *a, **k: live)

    rc = G.main(["anchor-ledger", "--verify", str(baseline)])
    out = capsys.readouterr().out
    assert rc == G.EXIT_FAIL, out
    assert "req-2" in out, out
    assert "Second" in out, out
    assert "LOST" in out, out
    assert "do NOT re-run archive" in out, out


def test_verify_reports_never_added_separately_from_lost(tmp_path, monkeypatch, capsys) -> None:
    """`never_added` and `lost` are distinct classes and must be listed apart.

    One lost plus one never-added nets out to the same raw count as no change
    at all (`4+1-1=4` vs `4-1=3`), so a count-only report cannot distinguish
    "one anchor rotated" from "one anchor quietly vanished".
    """
    baseline = _write_ledger_file(
        tmp_path,
        {"wayfinder": {"req-1": "First", "req-2": "Second"}},
        expect_new=["req-3"],
    )
    # req-1 vanished; req-2 survives; req-3 was declared but never added.
    monkeypatch.setattr(G, "anchor_ledger", lambda *a, **k: {"wayfinder": {"req-2": "Second"}})

    rc = G.main(["anchor-ledger", "--verify", str(baseline)])
    out = capsys.readouterr().out
    assert rc == G.EXIT_FAIL, out
    assert "LOST" in out and "req-1" in out, out
    assert "NEVER-ADDED" in out and "req-3" in out, out
    assert "Counts alone cannot separate" in out, out


def test_verify_flags_retargeted_anchor(tmp_path, monkeypatch, capsys) -> None:
    """An anchor id that now introduces a DIFFERENT Requirement is drift."""
    baseline = _write_ledger_file(tmp_path, {"wayfinder": {"req-1": "First"}})
    monkeypatch.setattr(G, "anchor_ledger", lambda *a, **k: {"wayfinder": {"req-1": "Impostor"}})

    rc = G.main(["anchor-ledger", "--verify", str(baseline)])
    out = capsys.readouterr().out
    assert rc == G.EXIT_FAIL, out
    assert "Impostor" in out and "First" in out, out


def test_verify_rejects_a_file_that_is_not_a_ledger(tmp_path, capsys) -> None:
    """A JSON file that is not a run_gates ledger must be an error, not a pass."""
    bogus = tmp_path / "bogus.json"
    bogus.write_text('{"something": "else"}', encoding="utf-8")
    rc = G.main(["anchor-ledger", "--verify", str(bogus)])
    assert rc == G.EXIT_FAIL, "A non-ledger JSON must not verify as a ledger"
    assert "not a run_gates ledger" in capsys.readouterr().err


def test_anchor_ledger_omits_inline_anchor_mentions() -> None:
    """An anchor quoted inside prose is a mention, not a Requirement header."""
    lines = [
        '<a id="req-1"></a>',
        '### Requirement: Real',
        '',
        'the prose quotes <a id="req-17"></a> inline',
    ]
    assert [a for _, a, _ in G.block_starts(lines)] == ["req-1"]


def test_declared_added_anchors_reads_the_added_delta() -> None:
    """`--write --change <name>` must derive the expected-new anchors from the
    change's own `## ADDED Requirements` block.

    Without this, a ledger written *before* an archive cannot distinguish "the
    new Requirement landed with its anchor" from "the archive ate the new
    Requirement's anchor": the missing id is absent from the baseline too, so the
    `lost` comparison is blind to it by construction. That is not theoretical —
    it is exactly what happened when archiving this repository's own change
    dropped `<a id="req-gov-7">` while a `lost`-only comparison reported a clean
    pass.
    """
    name = "2026-10-03-a5-archive-gate-executability"
    declared = G.declared_added_anchors(name)
    assert sorted(declared) == ["req-gov-7", "req-gov-8", "req-gov-9"], (
        f"expected the three added governance anchors, got {declared}"
    )


def test_declared_added_anchors_ignores_modified_blocks() -> None:
    """Only `## ADDED Requirements` supplies expectations.

    A MODIFIED block's existing anchors are already in the baseline, so counting
    them as "expected new" would be harmless-but-wrong; a REMOVED block's anchors
    would make the comparison permanently unsatisfiable.
    """
    import tempfile
    from pathlib import Path as _P
    base = G._REPO_ROOT / "openspec" / "changes"
    with tempfile.TemporaryDirectory() as td:
        # Exercise the parser through the real function against a synthetic tree
        # is not possible without touching the repo, so assert the negative on
        # the real change: its MODIFIED req-34 anchor is NOT in the declared set.
        declared = set(G.declared_added_anchors("2026-10-03-a5-archive-gate-executability"))
        assert "req-34" not in declared, (
            "MODIFIED-block anchors must not be reported as expected-new"
        )
        assert declared, "sanity: the real change does declare additions"


def test_write_records_expect_new_derived_from_change(tmp_path) -> None:
    """A ledger written with `--change` must persist the derived expectation."""
    out = tmp_path / "derived.json"
    rc = G.main([
        "anchor-ledger", "--write", str(out),
        "--change", "2026-10-03-a5-archive-gate-executability",
    ])
    assert rc == G.EXIT_OK
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert sorted(payload["expect_new"]) == ["req-gov-7", "req-gov-8", "req-gov-9"], payload
    assert payload["change"] == "2026-10-03-a5-archive-gate-executability"


def test_verify_catches_an_anchor_the_archive_swallowed(tmp_path, monkeypatch, capsys) -> None:
    """The end-to-end case: baseline predates the addition, the addition is
    declared, and the tree is missing the anchor while keeping the text.

    This is the archive defect reproduced in miniature. A `lost`-only comparison
    passes it silently, because the id is in neither the baseline nor the tree —
    only in the declaration.
    """
    baseline = _write_ledger_file(
        tmp_path,
        {"governance": {"req-gov-6": "Pre-existing"}},
        expect_new=["req-gov-7"],
    )
    # The tree kept the Requirement's *content* but not its anchor, which is
    # precisely how `openspec archive` fails.
    monkeypatch.setattr(
        G, "anchor_ledger", lambda *a, **k: {"governance": {"req-gov-6": "Pre-existing"}}
    )
    rc = G.main(["anchor-ledger", "--verify", str(baseline)])
    out = capsys.readouterr().out
    assert rc == G.EXIT_FAIL, out
    assert "NEVER-ADDED" in out and "req-gov-7" in out, out


# --- live tree --------------------------------------------------------------


def test_live_anchor_coverage_is_complete() -> None:
    """Every live Requirement must have its own anchor, with no duplicate ids."""
    problems = G.check_anchor_coverage()
    assert problems == [], f"Live spec tree has anchor problems: {problems}"


def test_ledger_records_every_capability() -> None:
    """The ledger must key by capability so a whole-spec loss is visible."""
    ledger = G.anchor_ledger()
    assert set(ledger) >= {"wayfinder", "decompmoe-skeleton", "governance"}, (
        f"Expected all three capabilities, got {sorted(ledger)}"
    )
    for capability, entries in ledger.items():
        assert entries, f"{capability} ledger is empty — glob or parse broke"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
