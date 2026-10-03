"""Tests for the archived change's `evidence/_paths.py` location resolver.

Why this file is tested at all: audit finding L2-F5 (MAJOR) was that
`gen_deltas.py` and `verify_deltas.py` resolved the repository root as
`Path(__file__).resolve().parents[4]`. That index is correct only in the
*pre*-archive layout. In the archived layout the same index lands on
`openspec/`, so every spec read resolved to `openspec/openspec/specs/...` and
both tools died with `FileNotFoundError` — the archive commit that delivered the
evidence is the commit that made the evidence unrunnable.

The class of bug is not the arithmetic, it is that *the tool was never executed
in the state it ships in*. A generator that is only ever run before it is
archived gets no signal that archiving broke it. These tests pin both layouts
explicitly so that moving the change again, or adding a third nesting level,
fails here rather than in a future forensic session.

Load pattern matches the rest of the suite: the module lives under
`openspec/changes/archive/`, which is not importable, so it is loaded with
`importlib` rather than by extending `sys.path`.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_NAME = "2026-10-03-a5-archive-gate-executability"
_MODULE_PATH = (
    _REPO_ROOT / "openspec" / "changes" / "archive" / _NAME / "evidence" / "_paths.py"
)
_spec = importlib.util.spec_from_file_location("_a5_paths_under_test", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None, "Could not load _paths spec"
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
del _spec


def _make_layout(root: Path, *, archived: bool) -> Path:
    """Build a repo-shaped tree with the change in the requested location.

    Returns the evidence directory, which is what the tools pass in as `start`.
    """
    (root / "openspec" / "specs" / "wayfinder").mkdir(parents=True, exist_ok=True)
    (root / "openspec" / "specs" / "wayfinder" / "spec.md").write_text(
        "## Purpose\n", encoding="utf-8"
    )
    if archived:
        change = root / "openspec" / "changes" / "archive" / _NAME
    else:
        change = root / "openspec" / "changes" / _NAME
    evidence = change / "evidence"
    evidence.mkdir(parents=True)
    (change / "specs" / "wayfinder").mkdir(parents=True)
    (change / "specs" / "wayfinder" / "spec.md").write_text(
        "## ADDED Requirements\n", encoding="utf-8"
    )
    (evidence / "_paths.py").write_text("# stand-in\n", encoding="utf-8")
    return evidence


# --- repo-root resolution ---------------------------------------------------


@pytest.mark.parametrize("archived", [False, True], ids=["pre_archive", "post_archive"])
def test_find_repo_root_resolves_in_both_layouts(tmp_path: Path, archived: bool) -> None:
    """The resolver must be indifferent to where the change sits.

    One assertion, two layouts: this is the property the old `parents[4]` could
    not have. If a future change nests its evidence differently, this is the
    test that says so.
    """
    evidence = _make_layout(tmp_path, archived=archived)
    assert P.find_repo_root(evidence) == tmp_path.resolve()


def test_depth_index_approach_is_wrong_in_the_archived_layout(tmp_path: Path) -> None:
    """Pin *why* the resolver is content-based rather than depth-indexed.

    This reproduces the original defect directly. If a future edit ever restores
    `parents[4]`, this test still passes -- but it now documents, in executable
    form, that the archived layout puts a different directory at index 4, so the
    index cannot be chosen to work for both.
    """
    pre = _make_layout(tmp_path / "pre", archived=False) / "_paths.py"
    post = _make_layout(tmp_path / "post", archived=True) / "_paths.py"

    assert pre.resolve().parents[4] == (tmp_path / "pre").resolve(), (
        "pre-archive layout: index 4 is the repo root, so the old code worked"
    )
    assert post.resolve().parents[4] == (tmp_path / "post" / "openspec").resolve(), (
        "post-archive layout: index 4 is openspec/, so the old code resolved "
        "specs to openspec/openspec/specs and every read raised FileNotFoundError"
    )
    assert pre.resolve().parents[4] != post.resolve().parents[4].name, (
        "the two layouts put different directories at the same index"
    )


def test_find_repo_root_refuses_a_tree_without_the_marker(tmp_path: Path) -> None:
    """No marker anywhere up the chain is a usage error, not a silent fallback.

    A resolver that returned `start` (or cwd) on failure would make every
    downstream read point somewhere arbitrary, which is the same class of
    misleading output as the `FileNotFoundError` it replaced.
    """
    orphan = tmp_path / "nowhere"
    orphan.mkdir()
    with pytest.raises(SystemExit) as exc:
        P.find_repo_root(orphan)
    assert "openspec/specs" in str(exc.value), (
        f"error should name the marker that was not found, got {exc.value!r}"
    )


# --- change-directory resolution -------------------------------------------


def test_find_change_dir_returns_the_live_copy(tmp_path: Path) -> None:
    evidence = _make_layout(tmp_path, archived=False)
    found = P.find_change_dir(tmp_path, _NAME)
    assert found.is_dir()
    assert found == evidence.parent, f"got {found}, expected {evidence.parent}"
    assert P.is_archived(found) is False


def test_find_change_dir_falls_back_to_the_archived_copy(tmp_path: Path) -> None:
    evidence = _make_layout(tmp_path, archived=True)
    found = P.find_change_dir(tmp_path, _NAME)
    assert found == evidence.parent, f"got {found}, expected {evidence.parent}"
    assert P.is_archived(found) is True


def test_find_change_dir_prefers_live_when_both_exist(tmp_path: Path) -> None:
    """Duplicate locations resolve to the live copy, matching `run_gates.py`."""
    live = _make_layout(tmp_path, archived=False)
    archived = _make_layout(tmp_path, archived=True)
    assert archived.parent != live.parent
    assert P.find_change_dir(tmp_path, _NAME) == live.parent


def test_find_change_dir_reports_both_places_it_looked(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        P.find_change_dir(tmp_path, "no-such-change")
    msg = str(exc.value)
    assert "openspec/changes" in msg and "archive" in msg, (
        f"error should name every searched location, got {msg!r}"
    )


# --- pre-archive guard ------------------------------------------------------


def test_refuse_if_archived_is_silent_before_the_archive(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    change = _make_layout(tmp_path, archived=False).parent
    P.refuse_if_archived("gen_deltas.py", change)
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == "", (
        f"pre-archive run must be silent, got {captured!r}"
    )


def test_refuse_if_archived_exits_2_and_explains_itself(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exit 2, not 1, and the message must name the cause.

    Exit 1 is this repo's "a check failed" code; a state mismatch is not a
    failed check. Reusing 1 would let a caller read a usage error as evidence
    that the archived delta is corrupt.
    """
    change = _make_layout(tmp_path, archived=True).parent
    with pytest.raises(SystemExit) as exc:
        P.refuse_if_archived("verify_deltas.py", change)
    assert exc.value.code == P.EXIT_WRONG_STATE, (
        f"expected {P.EXIT_WRONG_STATE}, got {exc.value.code!r}"
    )
    err = capsys.readouterr().err
    assert "archived" in err and "verify_deltas.py" in err, (
        f"message must name both the state and the tool, got {err!r}"
    )
    assert "collisions" in err, (
        f"message must explain why the checks would misfire, got {err!r}"
    )


def test_shipped_evidence_scripts_use_the_resolver_not_a_parents_index() -> None:
    """The archived tools themselves must not regress to a depth index.

    Guards the fix at its actual delivery site. Both scripts are read as text
    rather than imported, because importing them executes the preflight and
    would exit non-zero in the state this test is run from.
    """
    evidence_dir = _MODULE_PATH.parent
    for name in ("gen_deltas.py", "verify_deltas.py"):
        src = (evidence_dir / name).read_text(encoding="utf-8")
        assert "parents[4]" not in src, (
            f"{name} regressed to the depth-indexed repo root that only works "
            "before the archive"
        )
        assert "find_repo_root" in src, f"{name} does not use the shared resolver"
        assert "refuse_if_archived" in src, f"{name} lacks the pre-archive guard"
