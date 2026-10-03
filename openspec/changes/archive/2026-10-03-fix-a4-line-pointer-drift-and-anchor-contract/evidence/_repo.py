"""Locate the repository root from anywhere inside a change's `evidence/`.

A fixed `Path(__file__).resolve().parents[N]` breaks the moment the change is
archived: `openspec/changes/<name>/evidence/x.py` becomes
`openspec/changes/archive/<name>/evidence/x.py`, one level deeper, so the same
index points at `openspec/` instead of the repo root. Every evidence script in
this change used `parents[4]`, so all of them would have become non-reproducible
**on the very commit that archives the change that justifies them**.

The locator therefore searches upward for the directory that actually contains
`openspec/specs/` and `pyproject.toml`, which is stable under the move.

Usage (scripts are run directly, so the script's own directory is importable):

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _repo import REPO
"""

from __future__ import annotations

from pathlib import Path

MARKERS = ("openspec/specs", "pyproject.toml")


def find_repo_root(start: Path) -> Path:
    """Walk upward from `start` to the directory holding every marker in MARKERS."""
    here = start.resolve()
    for candidate in (here, *here.parents):
        if all((candidate / m).exists() for m in MARKERS):
            return candidate
    raise SystemExit(
        f"could not locate the repository root above {start}: none of the "
        f"ancestors contains all of {list(MARKERS)}"
    )


REPO = find_repo_root(Path(__file__).resolve().parent)
