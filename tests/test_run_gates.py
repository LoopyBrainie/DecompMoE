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
    """A changed HEAD, a changed tracked digest, or a changed untracked digest
    must each be reported — not collapsed into one boolean.

    The derived `status_lines` count is deliberately absent. `req-gov-8` forbids
    treating a coarser function of the same porcelain string as an independent
    signal, so the count is recorded but never compared. See the next test.
    """
    before = {"head": "aaaa", "tracked_digest": "t1", "untracked_digest": "u1", "status_lines": 3}
    after = {"head": "bbbb", "tracked_digest": "t2", "untracked_digest": "u2", "status_lines": 4}
    moved = G._snapshot_differs(before, after)
    assert len(moved) == 3, f"Expected all 3 compared fields reported, got {moved}"
    for key in ("head", "tracked_digest", "untracked_digest"):
        assert any(key in m for m in moved), f"{key} not reported: {moved}"


def test_derived_entry_count_alone_does_not_invalidate_the_run() -> None:
    """A moved `status_lines` with all three compared signals fixed MUST NOT report INVALID.

    This is the regression for the F1 finding: `status_lines` sat in the compared
    tuple, so a derived count of changed entries acted as an independent signal --
    which `req-gov-8` forbids and which `worktree_snapshot`'s own docstring denies.
    The field is still recorded, so this asserts the contract directly (a derived
    count never trips INVALID), not the absence of a hypothetical counterexample.
    """
    before = {"head": "aaaa", "tracked_digest": "t1", "untracked_digest": "u1", "status_lines": 3}
    after = {"head": "aaaa", "tracked_digest": "t1", "untracked_digest": "u1", "status_lines": 99}
    assert G._snapshot_differs(before, after) == [], (
        f"a derived count must not act as an independent signal: {before} {after}"
    )


def test_snapshot_differs_reports_digests_as_changed_not_as_hex() -> None:
    """A digest is reported as CHANGED, not dumped as 64 hex chars.

    A full digest in the error message buries the one fact the reader needs,
    which is *which* signal tripped.
    """
    before = {"head": "aaaa", "tracked_digest": "t" * 64, "untracked_digest": "u" * 64, "status_lines": 0}
    after = {"head": "aaaa", "tracked_digest": "T" * 64, "untracked_digest": "u" * 64, "status_lines": 0}
    moved = G._snapshot_differs(before, after)
    assert moved == ["  tracked_digest: CHANGED"], moved


def test_snapshot_differs_is_empty_for_identical_snapshots() -> None:
    """Two identical snapshots must report no movement at all."""
    snap = {"head": "aaaa", "tracked_digest": "t1", "untracked_digest": "u1", "status_lines": 3}
    assert G._snapshot_differs(snap, dict(snap)) == []


def test_worktree_snapshot_has_all_components() -> None:
    """The real repo snapshot must carry every discriminating component."""
    snap = G.worktree_snapshot()
    assert set(snap) == {"head", "tracked_digest", "untracked_digest", "status_lines"}
    assert len(snap["head"]) == 40, f"HEAD should be a full sha, got {snap['head']!r}"
    assert len(snap["tracked_digest"]) == 64
    assert len(snap["untracked_digest"]) == 64
    assert isinstance(snap["status_lines"], int)


# --- snapshot collision regression (the defect this change was reviewed for) ---


def _temp_repo() -> str:
    import pathlib
    import subprocess
    import tempfile
    d = tempfile.mkdtemp(prefix="run_gates_repo_")
    subprocess.run(["git", "init", "-q", d], capture_output=True)
    subprocess.run(["git", "-C", d, "config", "user.email", "t@t"], capture_output=True)
    subprocess.run(["git", "-C", d, "config", "user.name", "t"], capture_output=True)
    pathlib.Path(d, "b.py").write_text("v1\n", encoding="utf-8")
    pathlib.Path(d, "c.py").write_text("other\n", encoding="utf-8")
    subprocess.run(["git", "-C", d, "add", "-A"], capture_output=True)
    subprocess.run(["git", "-C", d, "commit", "-qm", "init"], capture_output=True)
    return d


def test_porcelain_digest_collides_which_is_why_content_is_hashed() -> None:
    """Document the collision that motivates hashing content, not the listing.

    `git status --porcelain` encodes path + status letter. Two states that are
    both dirty in the same file produce byte-identical porcelain, so a
    porcelain-derived fingerprint cannot tell them apart. This test pins the
    *git behaviour*; the gate's own guarantee is asserted separately below.
    """
    import hashlib
    import pathlib
    import subprocess
    d = _temp_repo()
    pathlib.Path(d, "b.py").write_text("DIRTY CONTENT A\n", encoding="utf-8")

    def porcelain() -> str:
        return subprocess.run(
            ["git", "-C", d, "status", "--porcelain"], capture_output=True, text=True
        ).stdout

    before = porcelain()
    pathlib.Path(d, "b.py").write_text("ENTIRELY DIFFERENT DIRTY CONTENT B\n", encoding="utf-8")
    after = porcelain()

    assert before == after, "precondition: porcelain is identical for both states"
    assert hashlib.sha256(before.encode()).hexdigest() == hashlib.sha256(after.encode()).hexdigest()
    assert "ENTIRELY" in pathlib.Path(d, "b.py").read_text(encoding="utf-8"), (
        "the file really did change content"
    )


def test_tracked_digest_detects_content_change_in_already_dirty_file(
    tmp_path, monkeypatch
) -> None:
    """The gate's own digest MUST move when a dirty file's content changes.

    This is the regression for the CRITICAL review finding: a porcelain-based
    fingerprint reported the two states as identical, so a concurrent edit to an
    already-dirty file passed the gate while every gate still printed green.
    """
    import pathlib
    import subprocess
    d = _temp_repo()
    pathlib.Path(d, "b.py").write_text("DIRTY CONTENT A\n", encoding="utf-8")

    monkeypatch.setattr(G, "_REPO_ROOT", pathlib.Path(d))
    first = G.worktree_snapshot()
    pathlib.Path(d, "b.py").write_text("ENTIRELY DIFFERENT DIRTY CONTENT B\n", encoding="utf-8")
    second = G.worktree_snapshot()

    assert first["head"] == second["head"], "precondition: HEAD did not move"
    assert first["status_lines"] == second["status_lines"], (
        "precondition: the porcelain entry count is unchanged"
    )
    assert first["tracked_digest"] != second["tracked_digest"], (
        "tracked_digest must be content-sensitive: a concurrent edit to an "
        "already-dirty file has to move the fingerprint"
    )
    assert G._snapshot_differs(first, second) == ["  tracked_digest: CHANGED"]


def test_untracked_digest_detects_new_file_inside_untracked_dir(
    tmp_path, monkeypatch
) -> None:
    """A new file inside an untracked *directory* must move the fingerprint.

    `git status --porcelain` collapses an untracked directory to one `?? dir/`
    line, so adding a second file inside it leaves the listing untouched.
    """
    import pathlib
    d = _temp_repo()
    (pathlib.Path(d) / "scratch").mkdir()
    (pathlib.Path(d) / "scratch" / "one.py").write_text("x\n", encoding="utf-8")

    monkeypatch.setattr(G, "_REPO_ROOT", pathlib.Path(d))
    first = G.worktree_snapshot()
    (pathlib.Path(d) / "scratch" / "two.py").write_text("y\n", encoding="utf-8")
    second = G.worktree_snapshot()

    assert first["untracked_digest"] != second["untracked_digest"], (
        "untracked_digest must be content-sensitive per file, not per collapsed directory"
    )
    assert any("untracked_digest" in m for m in G._snapshot_differs(first, second))


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
            return {"head": "a" * 40, "tracked_digest": "t1", "untracked_digest": "u1", "status_lines": 1}
        return {"head": "a" * 40, "tracked_digest": "t2", "untracked_digest": "u2", "status_lines": 2}

    monkeypatch.setattr(G, "worktree_snapshot", fake_snapshot)
    monkeypatch.setattr(G, "discover_lints", lambda: [Path("fake_lint.py")])
    monkeypatch.setattr(G, "_run", lambda cmd: (0, "ok"))
    monkeypatch.setattr(G, "check_anchor_coverage", lambda: [])

    rc = G.main(["--skip-pytest"])
    out = capsys.readouterr().out
    assert rc == G.EXIT_INVALID, f"Expected exit 2, got {rc}. Output:\n{out}"
    assert "GATE RESULT INVALID" in out, out
    assert "do not read this as a pass" in out, out


def test_gates_stay_valid_when_only_the_derived_count_moves(monkeypatch, capsys) -> None:
    """A moved `status_lines` alone MUST NOT turn a green run into INVALID.

    The call-level counterpart to the unit guard. That one drives
    `_snapshot_differs` with synthetic dicts, so it cannot see a broken
    end-to-end verdict; this one goes through `cmd_gates`, which is where the
    snapshot is sampled twice and exit 2 is actually decided. The companion test
    above proves the tree moved; this proves a *derived count* moving is not
    treated as the tree moving, at the level where that decision is made.
    """
    calls = {"n": 0}

    def fake_snapshot() -> dict[str, object]:
        calls["n"] += 1
        base = {"head": "a" * 40, "tracked_digest": "t1", "untracked_digest": "u1"}
        return {**base, "status_lines": 1 if calls["n"] == 1 else 99}

    monkeypatch.setattr(G, "worktree_snapshot", fake_snapshot)
    monkeypatch.setattr(G, "discover_lints", lambda: [Path("fake_lint.py")])
    monkeypatch.setattr(G, "_run", lambda cmd: (0, "ok"))
    monkeypatch.setattr(G, "check_anchor_coverage", lambda: [])

    rc = G.main(["--skip-pytest"])
    out = capsys.readouterr().out
    assert rc == G.EXIT_OK, f"a derived count must not invalidate the run, got {rc}:\n{out}"
    assert "GATE RESULT INVALID" not in out, out
    # The count is still surfaced for a human reading the result.
    assert "dirty_entries=1" in out, out


def test_gates_exit_0_on_stable_worktree(monkeypatch, capsys) -> None:
    """The control case: a stable worktree with all gates green is exit 0."""
    snap = {"head": "a" * 40, "tracked_digest": "t1", "untracked_digest": "u1", "status_lines": 1}
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
        "head": "a" * 40, "tracked_digest": "t1", "untracked_digest": "u1", "status_lines": 0})
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
        "head": "a" * 40, "tracked_digest": "t1", "untracked_digest": "u1", "status_lines": 0})
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


def _write_ledger_file_named(
    tmp_path: Path, ledger: dict, change: str | None, expect_new: list[str] | None = None
) -> Path:
    """Baseline ledger that also records which change it was written for."""
    path = tmp_path / "ledger.json"
    path.write_text(
        json.dumps(
            {
                "written_at_head": "0" * 40,
                "change": change,
                "expect_new": expect_new or [],
                "ledger": ledger,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _write_removed_delta(tmp_path: Path, change: str, title: str) -> None:
    """Create a change whose delta removes the Requirement titled `title`."""
    spec = (
        tmp_path
        / "openspec"
        / "changes"
        / change
        / "specs"
        / "governance"
        / "spec.md"
    )
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text(
        "## REMOVED Requirements\n\n"
        f"### Requirement: {title}\n\n"
        "**Reason**: because\n\n"
        "**Migration**: elsewhere\n",
        encoding="utf-8",
    )


def test_deliberately_removed_anchor_is_not_reported_as_lost(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A Requirement the change removed on purpose MUST NOT be a LOST anchor.

    Observed on this repository while archiving
    `2026-10-03-fix-a5-review-findings-round-2`: the delta's `## REMOVED
    Requirements` block deleted a then-live governance anchor, and `--verify`
    reported it as lost alongside a genuinely swallowed one

        lost          governance: <the removed id>  (Spec Anchor Ledger ...)
        never-added   <the swallowed id>

    The first is not a defect at all - the archive did exactly what it was told.
    Reporting it makes the protocol's own instruction ("restore surgically, do
    NOT re-run archive") unfollowable, because restoring the anchor of a
    Requirement that was deliberately deleted is itself wrong. A gate that cries
    wolf on every removal-architecture change trains its readers to ignore it.
    """
    _write_removed_delta(tmp_path, "synthetic-remove", "Doomed Requirement")
    monkeypatch.setattr(G, "_REPO_ROOT", tmp_path)
    baseline = _write_ledger_file_named(
        tmp_path,
        {"governance": {"req-a": "Doomed Requirement", "req-b": "Survivor"}},
        change="synthetic-remove",
    )
    # After the archive: req-a is gone (removed on purpose), req-b survives.
    monkeypatch.setattr(G, "anchor_ledger", lambda: {"governance": {"req-b": "Survivor"}})
    rc = G.main(["anchor-ledger", "--verify", str(baseline)])
    out = capsys.readouterr().out
    assert rc == G.EXIT_OK, out
    assert "LOST" not in out, out
    assert "req-a" not in out, f"the removed anchor must not appear at all: {out}"
    assert "removal(s)" in out, f"it should be reported as a deliberate removal: {out}"


def test_genuine_loss_is_still_reported_when_a_removal_is_also_declared(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Excluding deliberate removals must not hide a *real* loss alongside one.

    The failure mode of the fix is over-filtering: if the exclusion were applied
    to "any anchor missing during a change with a REMOVED block", a swallowed
    anchor would be silently accepted. So both classes must appear together.
    """
    _write_removed_delta(tmp_path, "synthetic-mixed", "Doomed Requirement")
    monkeypatch.setattr(G, "_REPO_ROOT", tmp_path)
    baseline = _write_ledger_file_named(
        tmp_path,
        {
            "governance": {
                "req-a": "Doomed Requirement",
                "req-b": "Survivor",
                "req-c": "Also A Survivor",
            }
        },
        change="synthetic-mixed",
    )
    # req-a removed on purpose; req-c genuinely swallowed.
    monkeypatch.setattr(G, "anchor_ledger", lambda: {"governance": {"req-b": "Survivor"}})
    rc = G.main(["anchor-ledger", "--verify", str(baseline)])
    out = capsys.readouterr().out
    assert rc == G.EXIT_FAIL, out
    assert "LOST" in out and "req-c" in out, f"the real loss must still be caught: {out}"
    assert "req-a" in out, f"the deliberate removal should still be disclosed: {out}"
    lost_line = [l for l in out.splitlines() if l.strip().startswith("lost")][0]
    assert "req-c" in lost_line, f"req-a must not be in the lost list: {lost_line!r}"
    # `req-gov-10` requires the report to state how many classes counts cannot
    # separate, so this wording is normative, not incidental. Note it names the
    # code's class *vocabulary* (three), not how many lists this run printed --
    # only two print here, because the change declares no added anchor.
    assert "three classes" in out, f"the summary must state three classes: {out}"
    # ...and that "three" must equal the number of distinct class labels the code
    # can actually emit, so adding or dropping a class turns this red instead of
    # leaving the prose quietly stale.
    src = Path(G.__file__).read_text(encoding="utf-8")
    vocabulary = sum(
        h in src
        for h in ("LOST anchor(s)", "removed on purpose", "NEVER-ADDED anchor(s)")
    )
    assert f"these {('two', 'three', 'four')[vocabulary - 2]} classes" in out, (
        f"the prose must track the code's class vocabulary ({vocabulary}): {out}"
    )


def test_removed_anchor_lookup_is_scoped_per_capability(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`deliberate` must key on (capability, id), not a flat id set.

    Anchor ids are per-capability, so a flat set makes a lookup against another
    capability's ledger raise KeyError. This is the bug the first implementation
    of the exclusion actually had, found by running it against the real archive.
    """
    _write_removed_delta(tmp_path, "synthetic-caps", "Doomed Requirement")
    monkeypatch.setattr(G, "_REPO_ROOT", tmp_path)
    baseline = _write_ledger_file_named(
        tmp_path,
        {
            "governance": {"req-a": "Doomed Requirement"},
            "wayfinder": {"req-a": "Unrelated Requirement", "req-z": "Another"},
        },
        change="synthetic-caps",
    )
    # Only governance/req-a is removed; wayfinder/req-a must be untouched and
    # therefore must still be reported as lost.
    monkeypatch.setattr(G, "anchor_ledger", lambda: {"wayfinder": {"req-z": "Another"}})
    rc = G.main(["anchor-ledger", "--verify", str(baseline)])
    out = capsys.readouterr().out
    assert rc == G.EXIT_FAIL, out
    lost_block = out.split("LOST")[1].split("removed")[0]
    assert "wayfinder: req-a" in lost_block, (
        f"wayfinder/req-a was not removed and must be reported lost: {lost_block}"
    )


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
    # That change declared three governance additions. The third was later
    # removed from the spec, so it is not named here: `lint_no_line_pointers`
    # check C4 resolves every `req-*` mention against the live specs and has no
    # historical-marker escape (unlike C1), so a dangling id in this file fails
    # the gate. The ids that still resolve are asserted directly, and the count
    # carries the rest of the intent: only the ADDED block contributes.
    assert len(declared) == 3, f"expected the three added governance anchors, got {declared}"
    assert all(d.startswith("req-gov-") for d in declared), declared
    assert "req-gov-7" in declared and "req-gov-8" in declared, declared


def test_declared_added_anchors_ignores_modified_and_sub_anchors(
    tmp_path, monkeypatch
) -> None:
    """Only `## ADDED Requirements` block starts supply expectations.

    Two things must NOT leak in:

    * A MODIFIED block's existing anchors — they are already in the baseline, so
      counting them as "expected new" is wrong.
    * A block-level **sub-anchor** inside an ADDED block (e.g. `req-20-mci`) —
      it is a section header, not a Requirement header. `never_added` is
      computed against `present`, which comes from `block_starts` only, so
      counting a sub-anchor here would report one forever-absent entry for every
      ADDED block that carries one.

    Built as a synthetic change tree so the parser is actually exercised, rather
    than asserted against whatever the repository happens to contain today.

    The synthetic anchor ids are deliberately non-numeric (`req-alpha`, rather
    than a digits-suffixed id): `scripts/lint_no_line_pointers.py` classifies a
    numeric `req-` id as a cross-Requirement reference and then fails this file
    for naming Requirements that do not exist. The ids are opaque strings to
    `declared_added_anchors`, so nothing about the parser is under test here.
    """
    change = tmp_path / "openspec" / "changes" / "synthetic"
    spec = change / "specs" / "wayfinder" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "## ADDED Requirements\n"
        "\n"
        '<a id="req-alpha"></a>\n'
        "\n"
        "### Requirement: Real Addition\n"
        "\n"
        "body\n"
        "\n"
        '<a id="req-alpha-sub"></a>\n'
        "\n"
        "#### Scenario: a section inside the same block\n"
        "\n"
        "still the same Requirement's body\n"
        "\n"
        "## MODIFIED Requirements\n"
        "\n"
        '<a id="req-preexisting"></a>\n'
        "\n"
        "### Requirement: Pre-existing\n"
        "\n"
        "body\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(G, "_REPO_ROOT", tmp_path)
    declared = G.declared_added_anchors("synthetic")
    assert declared == ["req-alpha"], (
        f"only the ADDED block's Requirement anchor may be declared, got {declared}"
    )


def test_write_records_expect_new_derived_from_change(tmp_path) -> None:
    """A ledger written with `--change` must persist the derived expectation."""
    out = tmp_path / "derived.json"
    rc = G.main([
        "anchor-ledger", "--write", str(out),
        "--change", "2026-10-03-a5-archive-gate-executability",
    ])
    assert rc == G.EXIT_OK
    payload = json.loads(out.read_text(encoding="utf-8"))
    # That change declared three additions; the third was later removed, so it
    # is not named here (C4 resolves `req-*` against live specs, no historical
    # escape). See the sibling test for the same reason.
    assert len(payload["expect_new"]) == 3, payload
    assert "req-gov-7" in payload["expect_new"], payload
    assert "req-gov-8" in payload["expect_new"], payload
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


# --- what the point-in-time check can and cannot see ------------------------


def _coverage_problems(spec_text: str, tmp_path: Path) -> list[str]:
    """Run `check_anchor_coverage` over a one-capability synthetic tree."""
    cap_dir = tmp_path / "wayfinder"
    cap_dir.mkdir(parents=True, exist_ok=True)
    (cap_dir / "spec.md").write_text(spec_text, encoding="utf-8")
    return G.check_anchor_coverage(tmp_path)


def _req(anchor_id: str | None, title: str) -> str:
    head = f'<a id="{anchor_id}"></a>\n\n' if anchor_id else ""
    return f"{head}### Requirement: {title}\n\nbody\n\n"


def test_swallow_is_detected_when_the_archive_adds_nothing(tmp_path: Path) -> None:
    """With no simultaneous addition, a swallow leaves a deficit of one.

    Measured shapes, all reported as `1 uncovered`:
    a lone swallowed anchor; and a Requirement removed alongside a swallow
    (headings -1, anchors -1, so the net is a single missing anchor).
    """
    for label, text in [
        ("swallowed_anchor", _req("req-1", "A") + _req(None, "B")),
        ("removed_plus_swallowed", _req(None, "A") + _req("req-2", "B")),
    ]:
        problems = _coverage_problems(text, tmp_path)
        assert problems, f"{label}: swallow went undetected -> {problems}"
        assert "1 uncovered" in problems[0], f"{label}: {problems[0]}"


def test_a_swallow_cannot_be_masked_by_simultaneous_additions(tmp_path: Path) -> None:
    """Arithmetic guard: additions never cancel a swallow, so the check always fires.

    An earlier draft of this file asserted the opposite -- that an archive which
    adds a Requirement with its own anchor can mask a swallowed neighbour into a
    net-zero count, leaving the point check green. That was believed on
    inspection and killed by running it.

    The arithmetic: a swallow removes one block-start anchor and leaves the
    heading count alone, so `H - A` grows by 1. An added Requirement carries its
    own anchor, so it moves `H` and `A` together. The two therefore cannot
    cancel, and any sequence of ordinary archive operations leaves the deficit
    non-zero. Being unable to construct a counterexample is the point of the
    test -- it is the negative claim that the current ledger Requirement
    rests on.
    """
    for label, text in [
        ("added_with_anchor", _req("req-1", "A") + _req("req-new", "New") + _req(None, "B")),
        (
            "added_with_anchor_and_sub_anchor",
            _req("req-1", "A")
            + _req("req-new", "New")
            + '<a id="req-new-mci"></a>\n\n#### Scenario: s\n\nbody\n\n'
            + _req(None, "B"),
        ),
        ("added_without_anchor", _req("req-1", "A") + _req(None, "New") + _req(None, "B")),
    ]:
        problems = _coverage_problems(text, tmp_path)
        assert problems, (
            f"{label}: expected the deficit to survive, got {problems} -- if this "
            "now passes, re-derive the req-gov-10 rationale before touching it"
        )


def test_point_check_cannot_see_a_retargeted_anchor(tmp_path: Path) -> None:
    """A second count-equal shape: the id survives, attached to a different title."""
    problems = _coverage_problems(_req("req-1", "Renamed") + _req("req-2", "B"), tmp_path)
    assert problems == [], (
        "a retargeted anchor is expected to be INVISIBLE to the point check; "
        f"if it is now visible, {problems}, and the ledger rationale in "
        "req-gov-10 needs revisiting"
    )


def test_point_check_sees_a_duplicate_id_even_though_counts_match(tmp_path: Path) -> None:
    """Two headings sharing one id: counts match, but the duplicate check fires.

    Recorded because it is the other count-equal shape, and it lands on the
    duplicate branch rather than the coverage branch -- worth pinning so a
    refactor does not merge the two and lose the diagnosis.
    """
    text = _req("req-1", "A") + _req("req-1", "B")
    problems = _coverage_problems(text, tmp_path)
    assert len(problems) == 1, f"expected exactly the duplicate diagnosis, got {problems}"
    assert "declared 2 times" in problems[0], problems[0]


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
