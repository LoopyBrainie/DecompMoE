#!/usr/bin/env python3
"""Lint gate: detect OpenSpec Source fields that lack a wayfinder/tickets/ reverse-link.

Background (per review of `openspec/changes/fix-wayfinder-spec-source-field-drift`):
    CLAUDE.md §2 rule 3 and §3 mandate that every `**Source:**` field in
    `openspec/specs/**/spec.md` contain a literal `wayfinder/tickets/<ID>.md`
    reference. A `change <name> design.md (Decision N)` reference MAY appear
    additionally but never as a substitute.

This script greps OpenSpec spec files for `**Source:**` lines and rejects any
line missing the `wayfinder/tickets/` substring.

Anti-patterns flagged:
  1. `**Source:**` line whose content does not contain the substring `wayfinder/tickets/`.

Design constraints (per `openspec/changes/fix-wayfinder-spec-source-field-drift/design.md`):
  - Independent of `scripts/lint_no_dead_defensive.py` — disjoint file globs, no shared state, no shared imports.
  - NO exemption table (not `JUSTIFIED_EXEMPTIONS`, not per-line `# noqa`, not env var, not CLI flag).
  - Content-based rule (substring search) so the rule survives line shifts without chronic exemption-table rot.
  - Output goes to stdout (aligned with `lint_no_dead_defensive.py` convention; L94/97/101-109 all use `print(...)`).
  - Exit code 0 iff every `**Source:**` line satisfies the substring check; 1 otherwise.

Run as a pre-commit gate or in CI:
    python scripts/lint_no_source_field_drift.py [PATH ...]

KNOWN_OPEN_VIOLATIONS
=====================
This script reports a single violation on `req-33 (L678)` of
`openspec/specs/wayfinder/spec.md` — the `Test Guard Precision for Closed-Form
Numerical Claims` Requirement whose design lineage is the `CLAUDE.md` §6 第 8 条
amendment (commits `bec147d` + `83a0503`), not any `wayfinder/tickets/*.md` ticket.

Expected behavior: exit code 1, exactly 1 violation on L678, output the L678 line.

Do NOT add exemptions to this script to silence the violation. Resolve the spec
line instead — the L678 follow-up migration is tracked under the change
`migrate-l678-source` (referenced from the proposal that introduced this script).

If the lint output signature changes (e.g. 0/33 violations, or 2+ violations on
unrelated lines), treat that as a regression, not a clean bill of health.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
import re
import sys
from pathlib import Path

SPECS_GLOB = "openspec/specs/**/spec.md"

SOURCE_LINE_RE = re.compile(r"^\*\*Source:\*\*")

REQUIRED_SUBSTRING = "wayfinder/tickets/"

VIOLATION_REASON = "source field missing wayfinder/tickets/ reference"


def iter_source_lines(paths: Iterable[Path]) -> Iterator[tuple[Path, int, str]]:
    """Yield (path, line_number, line_content) for every `**Source:**` line in `paths`.

    `paths` is an iterable of file paths. Each path is read line-by-line; lines
    starting with `**Source:**` (no leading whitespace) are yielded with their
    1-based line number.
    """
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                if SOURCE_LINE_RE.match(line):
                    yield path, line_no, line.rstrip("\n")


def lint_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of `(line_no, line_content, reason)` violations in `path`.

    A violation is a `**Source:**` line that does not contain
    `REQUIRED_SUBSTRING`. The returned tuples are sorted by `line_no`.
    """
    violations: list[tuple[int, str, str]] = []
    for _, line_no, line in iter_source_lines([path]):
        if REQUIRED_SUBSTRING not in line:
            violations.append((line_no, line, VIOLATION_REASON))
    return violations


def collect_paths(args: list[str]) -> list[Path]:
    """Resolve CLI positional args to a list of spec files.

    If `args` is empty, walk `SPECS_GLOB` from the repo root (parent of `scripts/`).
    If `args` is non-empty, treat each as a file path. Directories are NOT
    recursively walked — pass explicit files.
    """
    if args:
        return [Path(a) for a in args]
    repo_root = Path(__file__).resolve().parent.parent
    return sorted(repo_root.glob(SPECS_GLOB))


def main(argv: list[str] | None = None) -> int:
    """Walk spec files, print per-line violations to stdout, return exit code.

    Exit code is `1` if any violation exists, `0` otherwise. Output format
    per violation is `{path}:{line_no}: {reason}: {content}`, matching the
    `lint_no_dead_defensive.py` per-line convention (L101-102 of that script).
    """
    args = list(sys.argv[1:] if argv is None else argv)
    paths = collect_paths(args)

    all_violations: list[tuple[Path, int, str, str]] = []
    for path in paths:
        for line_no, content, reason in lint_file(path):
            all_violations.append((path, line_no, content, reason))

    if not all_violations:
        print(f"lint_no_source_field_drift: OK ({len(paths)} file(s) scanned, no violations)")
        return 0

    print(f"lint_no_source_field_drift: {len(all_violations)} violation(s) found")
    print()
    for path, line_no, content, reason in all_violations:
        print(f"  {path}:{line_no}: {reason}")
        print(f"    {content}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
