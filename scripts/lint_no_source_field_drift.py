#!/usr/bin/env python3
"""Lint gate: detect OpenSpec Source fields that lack a per-capability reverse-link.

Background (per review of `openspec/changes/fix-wayfinder-spec-source-field-drift`
and `openspec/changes/migrate-l678-source`):
    CLAUDE.md §2 rule 3 and §3 mandate that every `**Source:**` field in
    `openspec/specs/**/spec.md` carry a primary reverse-link to the spec's
    design lineage. The primary reverse-link is per-capability:
      - `openspec/specs/governance/spec.md` (governance-origin specs, whose
        lineage is `CLAUDE.md` amendments rather than wayfinder tickets):
        Source lines MUST contain the substring `CLAUDE.md`.
      - All other `openspec/specs/**/spec.md` (wayfinder-ticketed specs +
        decompmoe-skeleton + future peers that cite wayfinder tickets):
        Source lines MUST contain the substring `wayfinder/tickets/`.

    A `change <name> design.md (Decision N)` reference MAY appear additionally
    as a secondary link, but its presence does NOT substitute for the primary
    ticket / governance reverse-link.

This script greps OpenSpec spec files for `**Source:**` lines and rejects any
line missing its capability's required primary reverse-link substring.

Anti-patterns flagged:
  1. `**Source:**` line in a wayfinder-lineage spec whose content does not contain the substring `wayfinder/tickets/`.
  2. `**Source:**` line in a governance-lineage spec whose content does not contain the substring `CLAUDE.md`.

Design constraints (per `openspec/changes/fix-wayfinder-spec-source-field-drift/design.md`,
extended by `openspec/changes/migrate-l678-source/design.md` Decision 3):
  - Independent of `scripts/lint_no_dead_defensive.py` — disjoint file globs, no shared state, no shared imports.
  - NO exemption table (not `JUSTIFIED_EXEMPTIONS`, not per-line `# noqa`, not env var, not CLI flag).
  - Content-based rule (substring search) so the rule survives line shifts without chronic exemption-table rot.
  - Per-capability mapping is hardcoded as a small in-script table (NOT an exemption registry, NOT a CLI flag, NOT an env var) — same anti-pattern guardrails as the original rule. Adding a new governance-lineage capability is a script edit + L678-style follow-up change, not a runtime toggle.
  - Output goes to stdout (aligned with `lint_no_dead_defensive.py` convention).
  - Exit code 0 iff every `**Source:**` line satisfies its capability's required substring check; 1 otherwise.

Run as a pre-commit gate or in CI:
    python scripts/lint_no_source_field_drift.py [PATH ...]
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

SPECS_GLOB = "openspec/specs/**/spec.md"

SOURCE_LINE_RE = re.compile(r"^\*\*Source:\*\*")

# Per-capability Source reverse-link substring map (hardcoded — NOT an exemption table).
# Keys are paths (relative to repo root) of spec files whose Source lines use a non-default
# primary reverse-link. The default `DEFAULT_REQUIRED_SUBSTRING` (wayfinder ticket lineage)
# applies to every other spec path. Adding a new governance-lineage capability is a script
# edit + follow-up OpenSpec change, NOT a runtime toggle.
# Paths are derived from `_REPO_ROOT` (computed from `__file__`) at module load so the
# script remains correct if it is moved to a sub-directory under `scripts/`. The lookup
# uses suffix matching so callers passing either absolute (from `glob`) or relative (from
# CLI args with cwd at repo root) `path` values both resolve correctly.
def _repo_root() -> Path:
    """Return the repo root inferred from this script's location.

    `__file__` is at `scripts/lint_no_source_field_drift.py`; its parent's parent is the
    repo root. The same anchor is used by `collect_paths()` (which builds `SPECS_GLOB`
    matches from the same root), keeping the table key and the glob root in lock-step so
    both remain consistent if the script is relocated.
    """
    return Path(__file__).resolve().parent.parent


_REPO_ROOT = _repo_root()

# Per-capability paths derived from `_REPO_ROOT` (so the script is robust to relocation).
REQUIRED_SUBSTRING_BY_PATH_RELATIVE: dict[Path, str] = {
    _REPO_ROOT / "openspec" / "specs" / "governance" / "spec.md": "CLAUDE.md",
}

DEFAULT_REQUIRED_SUBSTRING = "wayfinder/tickets/"


def required_substring_for(path: Path) -> str:
    """Return the primary reverse-link substring required for `path`.

    Per-capability lookup against `REQUIRED_SUBSTRING_BY_PATH_RELATIVE`; falls back to
    `DEFAULT_REQUIRED_SUBSTRING` for paths not in the table (i.e., the
    wayfinder-ticket lineage default). Matches by suffix (the last N path components
    of the candidate `path` must match the last N path components of a table key) so
    the lookup is robust against whether `path` is absolute or relative, and against
    cwd differences.

    The input path is resolved to absolute via `Path.resolve()` first so relative
    CLI args (e.g. `openspec/specs/governance/spec.md`) and absolute paths from
    `collect_paths()` glob both compare against the table keys on equal terms. This
    also normalizes Windows backslash/forward-slash representations.
    """
    path = path.resolve()
    for k, v in REQUIRED_SUBSTRING_BY_PATH_RELATIVE.items():
        if len(path.parts) >= len(k.parts) and path.parts[-len(k.parts):] == k.parts:
            return v
    return DEFAULT_REQUIRED_SUBSTRING


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

    A violation is a `**Source:**` line that does not contain the per-capability
    required substring (looked up via `required_substring_for(path)`). The
    returned tuples are sorted by `line_no`.
    """
    required = required_substring_for(path)
    reason = f"source field missing required reverse-link {required!r} for capability"
    violations: list[tuple[int, str, str]] = []
    for _, line_no, line in iter_source_lines([path]):
        if required not in line:
            violations.append((line_no, line, reason))
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
    `lint_no_dead_defensive.py` per-line convention.
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
