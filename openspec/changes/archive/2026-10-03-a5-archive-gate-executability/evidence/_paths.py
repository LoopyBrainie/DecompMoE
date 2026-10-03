#!/usr/bin/env python3
"""Repository-root and change-directory resolution for this change's evidence.

Single source of truth for *where* things are, shared by `gen_deltas.py` and
`verify_deltas.py` so the two cannot disagree about the answer.

Why this module exists
----------------------
Both scripts used to open with:

    REPO   = Path(__file__).resolve().parents[4]
    CHANGE = REPO / "openspec" / "changes" / "2026-10-03-a5-archive-gate-executability"

Both lines are correct **only before the archive**:

    evidence/gen_deltas.py   parents[0]=evidence [1]=<name> [2]=changes [3]=openspec [4]=REPO  OK
    archive/<name>/evidence  parents[0]=evidence [1]=<name> [2]=archive [3]=changes [4]=openspec  WRONG

Post-archive that yields `openspec/openspec/specs/wayfinder/spec.md` and a
`FileNotFoundError`. The same class of defect already cost this repository one
commit (`1612778`, "make the evidence tools survive archiving") and was
re-introduced by the follow-up that rewrote the scripts: an evidence tool whose
own delivery commit breaks it is not reproducible evidence.

`parents[N]` cannot be rescued by picking a different N — the depth differs
between the two states by construction, and the change directory *moves*. So
resolution is done by content (a marker that only the repo root has) instead of
by counting parents.
"""
from __future__ import annotations

import sys
from pathlib import Path

#: Marker that identifies the repository root. Chosen because it is a
#: directory of this repository's own structure, not a name that could collide
#: with a nested checkout or a vendored copy.
REPO_MARKER = ("openspec", "specs")

#: Directories a change may live in, in lookup order: live first, then archived.
CHANGE_BASES = (
    ("openspec", "changes"),
    ("openspec", "changes", "archive"),
)


def find_repo_root(start: Path) -> Path:
    """Return the nearest ancestor of `start` that contains the repo marker.

    `start` is the evidence directory, not this file, so a caller that copies or
    moves the script still resolves correctly.
    """
    here = start.resolve()
    for cand in (here, *here.parents):
        if cand.joinpath(*REPO_MARKER).is_dir():
            return cand
    raise SystemExit(
        f"evidence/_paths.py: no ancestor of {here} contains "
        f"{'/'.join(REPO_MARKER)}; run this from inside the repository"
    )


def find_change_dir(repo_root: Path, name: str) -> Path:
    """Return the change directory, whether or not it has been archived.

    Checks the live location first so a change that somehow exists in both is
    resolved to the live copy, matching `run_gates.py`'s own lookup order.
    """
    for base in CHANGE_BASES:
        cand = repo_root.joinpath(*base, name)
        if cand.is_dir():
            return cand
    searched = ", ".join("/".join(b) for b in CHANGE_BASES)
    raise SystemExit(f"evidence/_paths.py: change {name!r} not found under {searched}")


def is_archived(change_dir: Path) -> bool:
    """True when `change_dir` sits under `openspec/changes/archive/`."""
    return change_dir.parent.name == "archive"


#: Exit code for "ran in the wrong state" — distinct from 1 ("a check failed"),
#: following `scripts/run_gates.py`'s exit 2 = "cannot tell" convention. These
#: two tools assert the delta against the *live* spec, which only makes sense
#: before the archive absorbs the change; afterwards the collision is expected
#: and reporting it as a verification failure would be a false positive.
EXIT_WRONG_STATE = 2


def refuse_if_archived(script: str, change_dir: Path) -> None:
    """Exit with an explanation when a pre-archive tool is run post-archive.

    Without this, re-running the tools in their archived home produced four
    confusing failures — three `anchor collision` assertions and a Scenario
    count of `8 -> 8` where the tool demanded `live + 1` — that read as evidence
    corruption rather than as a state mismatch. Red output on an archived tool
    is worse than no output, because the next reader cannot tell which it is.
    """
    if not is_archived(change_dir):
        return
    rel = "/".join(change_dir.parts[-3:])
    print(
        f"{script}: {rel} is archived, so its live spec has already absorbed\n"
        f"  this change's delta. {script} is a pre-archive tool: it compares the\n"
        f"  delta against the live spec and would now report the already-landed\n"
        f"  anchors as collisions. Re-run it from the pre-archive checkout, or\n"
        f"  verify the archived spec directly with scripts/run_gates.py.",
        file=sys.stderr,
    )
    raise SystemExit(EXIT_WRONG_STATE)
