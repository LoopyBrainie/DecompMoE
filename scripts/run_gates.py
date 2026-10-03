#!/usr/bin/env python3
"""Single-command gate runner for the DecompMoE repository.

This is the one entry point that `CLAUDE.md` §3 names as the `/opsx:archive`
precondition. It exists because the previous arrangement — a hand-written list
of lint scripts in a Markdown file — failed three distinct ways (audit section
A-5 of `.audit/wayfinder-opsx-code-review/lists/opsx-changes.md`):

  * **AC-20 / AC-21** — the list was the *only* thing enforcing the gates, and it
    returned exit 0 on a spec tree whose anchors had already been silently
    dropped by `openspec archive`. A gate that cannot fail is not a gate.
  * **AC-49** — the list omitted `openspec validate <change> --type change
    --strict`, so a change with no delta and no `skip_specs` walked all the way
    to archive.
  * **AC-25** — a gate run sampled `git status` twice and got a different answer,
    because a concurrent session was writing the worktree. The two runs both
    printed green, and the second green described a tree the first never saw.

Lints are therefore *discovered* (`scripts/lint_*.py`), never enumerated, so a
newly added lint joins the gate without anyone editing this file or `CLAUDE.md`.

Subcommands
-----------
    python scripts/run_gates.py                       # repository-level gates
    python scripts/run_gates.py --change <name>       # + strict-validate that change
    python scripts/run_gates.py anchor-ledger --write <file> [--expect-new ID ...]
    python scripts/run_gates.py anchor-ledger --verify <file>

Exit codes
----------
    0  every gate passed on a stable worktree
    1  at least one gate reported a violation
    2  the worktree changed *while the gates ran* — the result is UNKNOWN and
       must not be read as either pass or fail

Exit 2 is deliberately distinct from exit 1. "No violations" and "we cannot
tell" are different claims, and collapsing them is what produced the AC-25
false green.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = _REPO_ROOT / "openspec" / "specs"
SCRIPTS_DIR = _REPO_ROOT / "scripts"

LINT_GLOB = "lint_*.py"
SPEC_FILENAME = "spec.md"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_INVALID = 2

# An anchor only introduces a Requirement if the FIRST non-empty line after it
# is the Requirement heading. Getting this wrong silently truncates a block:
# using "the next line is `### Requirement:`" instead yields a one-line shell,
# and a block-level anchor inserted mid-body would cut its own Requirement in
# half. Reproduced three times in this repository's archive history.
_ANCHOR_RE = re.compile(r'^<a id="([A-Za-z0-9._-]+)"></a>$')
_REQUIREMENT_RE = re.compile(r"^### Requirement: (.+)$")


# --- process helpers ---------------------------------------------------------


def _run(cmd: list[str]) -> tuple[int, str]:
    """Run `cmd` in the repo root, returning `(returncode, combined output)`."""
    proc = subprocess.run(
        cmd,
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _git(*args: str) -> tuple[int, str]:
    return _run(["git", *args])


# --- worktree snapshot (AC-25) ----------------------------------------------


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tracked_content_digest() -> str:
    """Digest the *content* of every tracked change, staged and unstaged.

    `git diff HEAD` is used rather than `git status --porcelain` on purpose.
    Porcelain encodes **path + status letter, not content**: two worktrees that
    are both dirty in the same files with the same status letters produce a
    byte-identical porcelain listing, and therefore an identical digest, no
    matter how far the contents have diverged.

    That is not a corner case. It is the *modal* case whenever another session
    is editing files that are already dirty, which is exactly the situation
    `req-gov-8` exists to police: a concurrent edit to an already-dirty file
    would slip through a porcelain fingerprint while every gate still printed
    green.

    `git diff HEAD` spans both the index and the worktree, so staged and
    unstaged edits to the same path are both covered by one digest.
    """
    rc, out = _git("diff", "HEAD")
    if rc != 0:
        raise RuntimeError(f"cannot read `git diff HEAD`: {out.strip()}")
    return _sha256_bytes(out.encode("utf-8", errors="replace"))


def _untracked_content_digest() -> str:
    """Digest the content of every untracked file, individually.

    `git status --porcelain` collapses an untracked *directory* to a single
    `?? dir/` line, so adding a second file inside it changes nothing in the
    listing. `--others --exclude-standard` enumerates the individual paths
    instead, and hashing each one's bytes makes the digest content-sensitive.
    """
    rc, out = _git("ls-files", "--others", "--exclude-standard")
    if rc != 0:
        raise RuntimeError(f"cannot enumerate untracked files: {out.strip()}")
    parts: list[str] = []
    for rel in sorted(p for p in out.splitlines() if p.strip()):
        path = _REPO_ROOT / rel
        try:
            digest = _sha256_bytes(path.read_bytes())
        except OSError as exc:
            # A file that vanished or is locked between the listing and the read
            # is itself a concurrent change; record the failure rather than
            # silently skipping the path.
            digest = f"UNREADABLE:{exc.errno}"
        parts.append(f"{rel}\0{digest}")
    return _sha256_bytes("\n".join(parts).encode("utf-8"))


def worktree_snapshot() -> dict[str, object]:
    """Return a stable, content-sensitive fingerprint of the tree.

    Three components, each failing for a different reason:

    * `head` — the committed base. Catches a commit landing mid-run, which moves
      the base while the working-tree content may be unchanged.
    * `tracked_digest` — a digest of `git diff HEAD`, i.e. of the *content* of
      every tracked modification, staged and unstaged. This is the component
      that catches a concurrent edit to an already-dirty file; a
      `git status --porcelain` digest cannot, because porcelain carries path +
      status letter only.
    * `untracked_digest` — a digest of every untracked file's bytes, enumerated
      individually so that a new file inside an untracked directory counts.

    `status_lines` is deliberately *not* among them: it is a strictly coarser
    function of the same porcelain string, so counting it as an independent
    signal would overstate how much the fingerprint discriminates. It is kept
    only so a human reading an INVALID result can see how busy the tree was.
    """
    rc_head, head = _git("rev-parse", "HEAD")
    if rc_head != 0:
        raise RuntimeError(f"cannot read HEAD (is this a git repo?): {head.strip()}")
    rc_st, st = _git("status", "--porcelain")
    if rc_st != 0:
        raise RuntimeError(f"cannot read worktree status: {st.strip()}")
    return {
        "head": head.strip(),
        "tracked_digest": _tracked_content_digest(),
        "untracked_digest": _untracked_content_digest(),
        "status_lines": len(st.splitlines()),
    }


def _snapshot_differs(before: dict[str, object], after: dict[str, object]) -> list[str]:
    """Return human-readable descriptions of every field that moved.

    Digest fields are reported as equal/unequal rather than as their full value:
    a 64-hex string in an error message hides the thing the reader needs, which
    is *which* signal tripped.
    """
    moved: list[str] = []
    for key in ("head", "tracked_digest", "untracked_digest", "status_lines"):
        if before.get(key) == after.get(key):
            continue
        if key.endswith("_digest"):
            moved.append(f"  {key}: CHANGED")
        else:
            moved.append(f"  {key}: {before.get(key)!r} -> {after.get(key)!r}")
    return moved


# --- gate discovery ----------------------------------------------------------


def discover_lints() -> list[Path]:
    """Return every `scripts/lint_*.py`, sorted.

    Discovery, not enumeration: a lint added later becomes part of the gate with
    no edit to this file or to `CLAUDE.md` (that is the AC-20/AC-21 fix).
    """
    return sorted(SCRIPTS_DIR.glob(LINT_GLOB))


# --- anchor ledger (AC-19 / AC-80) ------------------------------------------


def spec_paths(specs_dir: Path = SPECS_DIR) -> list[Path]:
    """Return every capability spec file, sorted."""
    if not specs_dir.is_dir():
        return []
    return sorted(p for p in specs_dir.glob(f"*/{SPEC_FILENAME}") if p.is_file())


def block_starts(lines: list[str]) -> list[tuple[int, str, str]]:
    """Return `(anchor_line, anchor_id, requirement_title)` for each block.

    A line is a block start only when it is a standalone anchor AND the first
    non-empty line following it is a `### Requirement:` heading. A bare anchor
    with anything else after it is an inline mention, not a block header.
    """
    starts: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        m = _ANCHOR_RE.match(line.strip())
        if not m:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines):
            continue
        rm = _REQUIREMENT_RE.match(lines[j])
        if rm:
            starts.append((i + 1, m.group(1), rm.group(1)))
    return starts


def anchor_ledger(specs_dir: Path = SPECS_DIR) -> dict[str, dict[str, str]]:
    """Return `{capability: {anchor_id: requirement_title}}`.

    The ledger is the unit of comparison for archive. A point-in-time coverage
    count cannot detect the archive defect, because after the archive the count
    is internally consistent: `openspec archive` drops the anchor of the
    Requirement *following* the one it rewrote, and also drops the blank line
    after it, so `anchors == headings` still holds. Only a before/after
    comparison names the loss.
    """
    ledger: dict[str, dict[str, str]] = {}
    for spec in spec_paths(specs_dir):
        lines = spec.read_text(encoding="utf-8").splitlines()
        capability = spec.parent.name
        ledger[capability] = {
            anchor_id: title for _, anchor_id, title in block_starts(lines)
        }
    return ledger


def check_anchor_coverage(specs_dir: Path = SPECS_DIR) -> list[str]:
    """Return one message per Requirement missing an anchor, plus duplicates.

    Point-in-time only, and deliberately cheap. It *does* catch the archive
    defect this runner is built around: a swallowed anchor removes a block start
    while leaving the heading count alone, so `H - A` grows by one and cannot be
    cancelled by any simultaneous addition (an added Requirement carries its own
    anchor, so `H` and `A` move together). Measured, not assumed -- see
    `tests/test_run_gates.py::test_a_swallow_cannot_be_masked_by_simultaneous_additions`,
    which exists because that negative claim was originally believed wrong.

    What it does *not* do is name anything: it reports a per-capability deficit,
    not which anchor id or which Requirement lost it, it cannot see an anchor
    id that survived but was re-attached to a different Requirement, and it
    cannot separate a lost anchor from one the change declared but never added.
    Those three are what `anchor_ledger` adds, and `req-gov-10` is the
    requirement that asks for them.
    """
    problems: list[str] = []
    for spec in spec_paths(specs_dir):
        capability = spec.parent.name
        lines = spec.read_text(encoding="utf-8").splitlines()
        starts = block_starts(lines)
        headings = [
            (i + 1, _REQUIREMENT_RE.match(l).group(1))
            for i, l in enumerate(lines)
            if _REQUIREMENT_RE.match(l)
        ]
        if len(starts) != len(headings):
            missing = len(headings) - len(starts)
            problems.append(
                f"{capability}: {len(headings)} Requirement heading(s) but "
                f"{len(starts)} anchor(s) — {missing} uncovered"
            )
        seen: dict[str, int] = {}
        for line_no, raw in enumerate(lines, 1):
            m = _ANCHOR_RE.match(raw.strip())
            if m:
                seen[m.group(1)] = seen.get(m.group(1), 0) + 1
        for anchor_id, count in sorted(seen.items()):
            if count > 1:
                problems.append(
                    f"{capability}: anchor id {anchor_id!r} declared {count} times "
                    f"(duplicate HTML id)"
                )
    return problems


def _load_ledger(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "ledger" not in data:
        raise ValueError(f"{path}: not a run_gates ledger (missing 'ledger' key)")
    return data


def declared_added_anchors(change_name: str) -> list[str]:
    """Return the anchor ids a change's delta declares it will ADD.

    Read from the change's own `specs/*/spec.md` `## ADDED Requirements` blocks.
    Without this, a ledger written before an archive cannot distinguish "the new
    Requirement landed with its anchor" from "the new Requirement landed and the
    archive ate its anchor" — the two differ only in an id that the *baseline*
    does not contain, so the `lost` comparison is blind to it by construction.

    That blindness is not theoretical: archiving this repository's own change
    `2026-10-03-a5-archive-gate-executability` silently dropped the
    `<a id="req-gov-7">` line while leaving the Requirement text fully intact, and
    a `lost`-only comparison reported a clean pass. `openspec archive` swallows
    the anchor of the Requirement *following* the one it rewrote, and that
    Requirement was itself one of the additions.

    Looks in `openspec/changes/<name>/` first, then
    `openspec/changes/archive/<name>/`, so the same call works before an archive
    (when the ledger is normally written) and afterwards (for forensics).
    """
    declared: list[str] = []
    for base in (
        _REPO_ROOT / "openspec" / "changes" / change_name,
        _REPO_ROOT / "openspec" / "changes" / "archive" / change_name,
    ):
        specs_dir = base / "specs"
        if not specs_dir.is_dir():
            continue
        for spec in sorted(specs_dir.glob(f"*/{SPEC_FILENAME}")):
            lines = spec.read_text(encoding="utf-8").splitlines()
            # Only anchors that actually introduce a Requirement. A block-level
            # sub-anchor inside an ADDED delta (e.g. `req-20-mci`) is a section
            # header, not a Requirement header, and `never_added` is computed
            # against `present` — which comes from `block_starts` only. Counting
            # sub-anchors here would report one forever-absent for every ADDED
            # block that carries them.
            added_ranges: list[tuple[int, int]] = []
            start: int | None = None
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    if start is not None:
                        added_ranges.append((start, i))
                    start = i if line.strip() == "## ADDED Requirements" else None
            if start is not None:
                added_ranges.append((start, len(lines)))
            for lo, hi in added_ranges:
                for line_no, anchor_id, _title in block_starts(lines[lo:hi]):
                    declared.append(anchor_id)
        if declared:
            break
    return declared


def removed_anchors(change_name: str) -> set[str]:
    """Return the anchor ids a change's delta declares it will REMOVE.

    A `## REMOVED Requirements` block has no anchor of its own -- the block is
    `### Requirement: <title>` plus Reason and Migration -- so the id has to be
    recovered by matching the title against the *baseline* ledger. Passing the
    title straight back to `--verify` would be circular: the ledger exists to
    report what the archive actually did, not to re-assert what the delta asked
    for.

    Without this, the first change that removes a Requirement produces a
    permanent false `LOST` report, and the protocol's own instruction --
    "restore surgically, do NOT re-run archive" -- becomes unfollowable, because
    restoring the anchor of a Requirement that was deliberately deleted is
    wrong. Observed on this repository: archiving
    `2026-10-03-fix-a5-review-findings-round-2` reported
    `lost governance: req-gov-9` for a Requirement the same archive had just
    removed on purpose.
    """
    titles: set[str] = set()
    for base in (
        _REPO_ROOT / "openspec" / "changes" / change_name,
        _REPO_ROOT / "openspec" / "changes" / "archive" / change_name,
    ):
        specs_dir = base / "specs"
        if not specs_dir.is_dir():
            continue
        for spec in sorted(specs_dir.glob(f"*/{SPEC_FILENAME}")):
            lines = spec.read_text(encoding="utf-8").splitlines()
            lo = hi = None
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    if lo is not None and line.strip() == "## ADDED Requirements":
                        hi = i
                    if lo is None and line.strip() == "## REMOVED Requirements":
                        lo = i
            if lo is None:
                continue
            for line in lines[lo : hi if hi is not None else len(lines)]:
                m = _REQUIREMENT_RE.match(line)
                if m:
                    titles.add(m.group(1).strip())
    return titles


def cmd_anchor_ledger(args: argparse.Namespace) -> int:
    """`anchor-ledger --write` / `--verify`."""
    if args.write:
        current = anchor_ledger()
        # Explicit `--expect-new` wins; otherwise derive the expectation from the
        # change being archived, so the comparison is meaningful by default.
        expect_new = list(args.expect_new or [])
        if not expect_new and args.change:
            expect_new = declared_added_anchors(args.change)
        payload = {
            "written_at_head": worktree_snapshot()["head"],
            "change": args.change,
            "expect_new": sorted(expect_new),
            "ledger": current,
        }
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        # `newline="\n"` explicitly: on Windows the default text mode would emit
        # CRLF, and the resulting file fails the repository's own whitespace gate
        # (`git diff --check` reports the stray CR as trailing whitespace). A gate
        # tool that writes files its own gate rejects is a defect.
        with out.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(
                json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
            )
        total = sum(len(v) for v in current.values())
        print(
            f"anchor-ledger: wrote {out} ({total} anchor(s) across "
            f"{len(current)} capabilit(ies), {len(expect_new)} declared-new)"
        )
        return EXIT_OK

    if args.verify:
        baseline = _load_ledger(Path(args.verify))
        before = baseline["ledger"]
        expect_new = set(baseline.get("expect_new") or [])
        after = anchor_ledger()

        lost: list[str] = []
        # An anchor the change deliberately removed is *supposed* to vanish, so
        # it is excluded from `lost` and reported separately. Keeping it in
        # would make every removal-architecture change emit a false
        # "restore surgically" instruction forever.
        #
        # The set holds (capability, anchor_id) pairs, not bare ids: anchor ids
        # are per-capability, and a flat id set makes a lookup against the wrong
        # capability's ledger raise KeyError.
        removed_titles = (
            removed_anchors(baseline["change"]) if baseline.get("change") else set()
        )
        deliberate = {
            (capability, anchor_id)
            for capability, entries in before.items()
            for anchor_id, title in entries.items()
            if title in removed_titles
        }
        expected_removals = sorted(
            f"{cap}: {aid} ({before[cap][aid]})" for cap, aid in deliberate
        )
        for capability, entries in sorted(before.items()):
            now = after.get(capability, {})
            for anchor_id, title in sorted(entries.items()):
                if (capability, anchor_id) in deliberate:
                    continue
                if anchor_id not in now:
                    lost.append(f"{capability}: {anchor_id} ({title})")
                elif now[anchor_id] != title:
                    lost.append(
                        f"{capability}: {anchor_id} now introduces "
                        f"{now[anchor_id]!r}, was {title!r}"
                    )

        # `never_added`: an anchor the change declared it would add, which is
        # absent from the tree. Reported separately from `lost` because the two
        # are indistinguishable from raw counts — one lost plus one never
        # added nets to the same total as no change at all.
        present = {a for entries in after.values() for a in entries}
        never_added = sorted(expect_new - present)

        if not lost and not never_added:
            total = sum(len(v) for v in after.values())
            note = (
                f", {len(deliberate)} deliberate removal(s)" if deliberate else ""
            )
            print(
                f"anchor-ledger: OK ({total} anchor(s) intact, "
                f"{len(expect_new)} declared-new anchor(s) present{note})"
            )
            return EXIT_OK

        if lost:
            print(f"anchor-ledger: {len(lost)} LOST anchor(s) — restore surgically, do NOT re-run archive:")
            for item in lost:
                print(f"  lost          {item}")
        if expected_removals:
            print(
                f"anchor-ledger: {len(expected_removals)} anchor(s) removed on purpose "
                f"by this change's ## REMOVED block (not a loss):"
            )
            for item in expected_removals:
                print(f"  removed       {item}")
        if never_added:
            print(f"anchor-ledger: {len(never_added)} NEVER-ADDED anchor(s) — declared by the change but absent:")
            for item in never_added:
                print(f"  never-added   {item}")
        print()
        print("Counts alone cannot separate these two classes; compare the per-anchor lists above.")
        return EXIT_FAIL

    raise ValueError("anchor-ledger needs either --write or --verify")


# --- gate execution ----------------------------------------------------------


def cmd_gates(args: argparse.Namespace) -> int:
    """Run every gate, then re-verify the snapshot."""
    lints = discover_lints()
    # Assert the count BEFORE iterating. `all([])` is vacuously true, so a
    # glob that silently matches nothing would report a clean gate while
    # running zero checks — the exact "green but hollow" failure this script
    # exists to end.
    if not lints:
        print(
            f"GATE FAIL: no lints discovered under "
            f"{(SCRIPTS_DIR / LINT_GLOB).as_posix()}",
            file=sys.stderr,
        )
        print(
            "  Refusing to report a pass: zero checks is not a passing gate.",
            file=sys.stderr,
        )
        return EXIT_FAIL

    try:
        before = worktree_snapshot()
    except RuntimeError as exc:
        print(f"GATE FAIL: {exc}", file=sys.stderr)
        return EXIT_FAIL

    print(f"run_gates: snapshot head={before['head'][:12]} "
          f"dirty_entries={before['status_lines']}")
    print(f"run_gates: {len(lints)} lint(s) discovered "
          f"(glob, not an enumerated list)")
    print()

    failures: list[str] = []
    for lint in lints:
        rc, out = _run([sys.executable, str(lint)])
        name = lint.name
        if rc == 0:
            print(f"  PASS  {name}")
        else:
            print(f"  FAIL  {name} (exit {rc})")
            for line in out.strip().splitlines()[-20:]:
                print(f"        {line}")
            failures.append(f"{name} exit {rc}")

    rc, out = _run(["openspec", "validate", "--specs", "--strict"])
    if rc == 0:
        print("  PASS  openspec validate --specs --strict")
    else:
        print(f"  FAIL  openspec validate --specs --strict (exit {rc})")
        for line in out.strip().splitlines()[-20:]:
            print(f"        {line}")
        failures.append(f"openspec validate --specs --strict exit {rc}")

    if args.change:
        # Validate ONLY the change being archived, not every unarchived change.
        # The archive precondition is about the change under the knife; sweeping
        # the whole directory would let unrelated stale changes redden a gate
        # that is about to pass, which is how gates get switched off.
        rc, out = _run(
            ["openspec", "validate", args.change, "--type", "change", "--strict"]
        )
        if rc == 0:
            print(f"  PASS  openspec validate {args.change} --type change --strict")
        else:
            print(f"  FAIL  openspec validate {args.change} --type change --strict (exit {rc})")
            for line in out.strip().splitlines()[-20:]:
                print(f"        {line}")
            failures.append(f"openspec validate {args.change} --type change --strict exit {rc}")

    problems = check_anchor_coverage()
    if problems:
        print("  FAIL  anchor coverage")
        for problem in problems:
            print(f"        {problem}")
        failures.append("anchor coverage")
    else:
        total = sum(len(v) for v in anchor_ledger().values())
        print(f"  PASS  anchor coverage ({total} anchor(s) across {len(spec_paths())} capabilit(ies))")

    if not args.skip_pytest:
        rc, out = _run([sys.executable, "-m", "pytest", "-q"])
        if rc == 0:
            tail = [l for l in out.strip().splitlines() if l.strip()][-1:]
            print(f"  PASS  pytest{' — ' + tail[0] if tail else ''}")
        else:
            print(f"  FAIL  pytest (exit {rc})")
            for line in out.strip().splitlines()[-30:]:
                print(f"        {line}")
            failures.append(f"pytest exit {rc}")
    else:
        print("  SKIP  pytest (--skip-pytest)")

    print()
    try:
        after = worktree_snapshot()
    except RuntimeError as exc:
        print(f"GATE RESULT INVALID: {exc}")
        return EXIT_INVALID

    moved = _snapshot_differs(before, after)
    if moved:
        print("GATE RESULT INVALID: worktree changed during run")
        for line in moved:
            print(line)
        print(
            "  The pass/fail above describes a tree that no longer exists. "
            "Re-run on a quiesced worktree; do not read this as a pass."
        )
        return EXIT_INVALID

    if failures:
        print(f"GATE FAIL: {len(failures)} gate(s) reported violations")
        for item in failures:
            print(f"  - {item}")
        return EXIT_FAIL

    print("GATE OK: all gates passed on a stable worktree")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_gates.py",
        description="Single-command gate runner (see module docstring).",
    )
    sub = parser.add_subparsers(dest="command")

    ledger = sub.add_parser(
        "anchor-ledger",
        help="write or verify the per-capability anchor ledger (AC-19/AC-80)",
    )
    ledger.add_argument("--write", metavar="FILE", help="write the ledger here")
    ledger.add_argument(
        "--verify",
        metavar="FILE",
        help="compare the tree against a previously written ledger",
    )
    ledger.add_argument(
        "--expect-new",
        metavar="ID",
        action="append",
        default=None,
        help="anchor id this change declares it will add (repeatable); "
             "reported as never_added when absent. With --change, derived "
             "automatically from that change's ADDED delta.",
    )
    ledger.add_argument(
        "--change",
        metavar="NAME",
        default=None,
        help="the change about to be archived; its ADDED delta supplies the "
             "expected-new anchor list when --expect-new is not given",
    )

    # Repository-level gates are the default (no subcommand needed), so
    # `python scripts/run_gates.py` is the single command CLAUDE.md names.
    parser.add_argument(
        "--change",
        metavar="NAME",
        default=None,
        help="also strictly validate this change (the one being archived)",
    )
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="skip the pytest gate (faster inner loop; not a full gate result)",
    )

    args = parser.parse_args(argv)
    if args.command == "anchor-ledger":
        try:
            return cmd_anchor_ledger(args)
        except ValueError as exc:
            print(f"anchor-ledger: {exc}", file=sys.stderr)
            return EXIT_FAIL
    return cmd_gates(args)


if __name__ == "__main__":
    sys.exit(main())
