#!/usr/bin/env python3
r"""Mechanical drift spine for the 32 `direct-fix` bucket entries.

For every entry this reports, per cited repository path:
  * the number of commits touching that path between the ledger pin and HEAD,
  * whether the path still exists,
  * whether the cited line(s) are still in range.

This answers a narrow question only: **did the code the entry points at move?**
A verdict requires that plus reading the entry (design.md D-4), so this script
deliberately emits no verdict of its own.

Run from the repository root:
    PYTHONIOENCODING=utf-8 uv run python openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction/evidence/reverify_direct_fixes.py
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

LEDGER = Path(".audit/gradual-review-2026-10-07/lists/direct-fixes.md")
PIN = "dde0e1d"

ENTRY_HEADING = re.compile(r"^### ((?:FIX|ARC)-\d+) — (.+)$", re.MULTILINE)
LOCATION = re.compile(r"^- \*\*location\*\*：(.*)$", re.MULTILINE)
# `scripts/foo.py:12`, `scripts/foo.py:12-18,20`, `src/x.py:1` — repo-relative.
PATH_WITH_LINES = re.compile(r"([A-Za-z0-9_./-]+\.(?:py|md|json|toml|yaml|yml))"
                            r"(?::([0-9]+)(?:-([0-9]+))?)?")
PATH_NO_LINES = re.compile(r"([A-Za-z0-9_./-]+\.(?:py|md|json|toml|yaml|yml))(?![0-9])")


def sh(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True).stdout.decode("utf-8", "replace")


def line_count(ref: str) -> int:
    text = sh("show", f"{ref}:{LEDGER.as_posix()}")
    return len(text.splitlines()) if text else 0


def entry_blocks() -> list[tuple[str, str, str]]:
    """(ref, severity, body) for every entry, in file order."""
    text = LEDGER.read_text(encoding="utf-8")
    marks = list(ENTRY_HEADING.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((m.group(1), m.group(2).strip(), text[m.end():end]))
    return out


def cited_paths(location: str) -> list[tuple[str, int | None, int | None]]:
    found: list[tuple[str, int | None, int | None]] = []
    seen: set[str] = set()
    for m in PATH_WITH_LINES.finditer(location):
        path = m.group(1).rstrip(".,;:")
        if path in seen:
            continue
        seen.add(path)
        lo = int(m.group(2)) if m.group(2) else None
        hi = int(m.group(3)) if m.group(3) else lo
        found.append((path, lo, hi))
    for m in PATH_NO_LINES.finditer(location):
        path = m.group(1).rstrip(".,;:")
        if path not in seen:
            seen.add(path)
            found.append((path, None, None))
    return found


def main() -> None:
    head = sh("rev-parse", "HEAD").strip()
    print(f"PIN     = {PIN}")
    print(f"HEAD    = {head}")
    print()

    blocks = entry_blocks()
    assert len(blocks) == 32, f"expected 32 entries, parsed {len(blocks)}"

    totals = {"untouched": 0, "touched": 0, "unresolvable": 0}
    for ref, severity, body in blocks:
        loc_match = LOCATION.search(body)
        location = loc_match.group(1).strip() if loc_match else "(none)"
        paths = cited_paths(location)
        print(f"### {ref} — {severity}")
        print(f"    location: {location[:150]}")
        if not paths:
            print("    -> NO repository path parsed from location")
            totals["unresolvable"] += 1
            print()
            continue
        for path, lo, _hi in paths:
            n_commits = len([x for x in sh(
                "log", "--oneline", f"{PIN}..HEAD", "--", path).splitlines() if x.strip()])
            exists = Path(path).is_file()
            in_range = "n/a"
            if exists and lo is not None:
                n_lines = len(Path(path).read_text(encoding="utf-8",
                                                   errors="replace").splitlines())
                in_range = "IN-RANGE" if lo <= n_lines else f"OUT-OF-RANGE(file has {n_lines})"
            flag = "untouched" if n_commits == 0 else "touched"
            totals[flag] += 1
            print(f"    {path:<48} commits pin..HEAD={n_commits:<3} "
                  f"exists={exists}  cited-line={in_range}")
        print()

    print("=" * 78)
    print(f"cited-path totals: untouched={totals['untouched']} "
          f"touched={totals['touched']} unresolvable={totals['unresolvable']}")
    print("A verdict still requires reading each entry (design.md D-4).")


if __name__ == "__main__":
    main()
