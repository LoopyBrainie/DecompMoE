#!/usr/bin/env python3
"""Lint gate: detect dead defensive try/except around PyTorch tensor ops.

Background (per review of commit 9978c11, see opsx:fix-math-consistency-audit-2026-08-apply):
    "fix-commit-induced-dead-defensive-code" anti-pattern.

The review identified 3 try/except blocks in src/decompmoe/metrics.py that
were inserted to satisfy an automated linter (pi-lens) but in fact could
never trigger (PyTorch tensor division returns NaN/Inf, never raises).

This script greps the source for the anti-pattern. On hit, exits non-zero.

Anti-patterns flagged: an `except (...)` TUPLE whose members are all drawn
from the exception set the wrapped numeric operations cannot raise -- tensor
ops return NaN/Inf rather than raising, and int()/round() of a finite float
return without raising. The arity is deliberately NOT constrained: the three
patterns this replaces each hardcoded exactly two names, so the one real
instance in the tree

    except (TypeError, ValueError, OverflowError)

matched none of them and the lint reported OK on a tree that contains it.
Matching any arity over the same member set is that policy applied
consistently, not a widened one.

Lines tagged `# noqa: dead-defensive` are EXPLICITLY by-design; all OTHER
matches are real anti-patterns to fix in code review. There is no exemption
TABLE: a central (path, line) key rots on the first line shift above it and
parks its reason off-document. The inline marker keeps the justification
beside the code it excuses, which is the convention `scripts/
lint_no_line_pointers.py` states for itself.

Run as a pre-commit gate or in CI:
    python scripts/lint_no_dead_defensive.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# `SELF_EXCLUDE` is derived from the detector rather than restated here: the
# two tools once kept separate copies, they drifted, and the census then
# reported the detector and its guard tests as 43 actionable pointers. One
# definition.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pointer_scan as _ps  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]

# `tests/**` is in scope for the reason `lint_no_line_pointers.py` puts it
# there: a lint's own fixtures need real anti-patterns to assert against,
# and a rule only ever exercised against `src/**` cannot tell "no
# anti-patterns" from "no fixtures".
SCAN_ROOTS = ("src/decompmoe", "tests")

#: Directories holding no source that `rglob` would otherwise walk.
_SKIP_DIRS = frozenset({"__pycache__", ".ruff_cache", ".pytest_cache"})

#: A lint never reports its own fixtures. Applied during the walk, so it
#: holds however the paths are spelled.
SELF_TEST_PATTERNS = _ps.SELF_EXCLUDE

NOQA_TAG = "noqa: dead-defensive"

# The exception names the wrapped numeric operations cannot raise. Kept as
# the union of the three two-name patterns this replaces, so matching any
# arity admits no exception type that was not already policy.
_UNREACHABLE = r"TypeError|ValueError|OverflowError|ZeroDivisionError|RuntimeError"

# Patterns that indicate a try/except where the excepted exceptions are
# mathematically unreachable given the wrapped operation.
PATTERNS: list[tuple[str, str]] = [
    # (regex, human-readable rationale)
    (
        r"except\s*\(\s*(?:" + _UNREACHABLE + r")"
        r"(?:\s*,\s*(?:" + _UNREACHABLE + r"))*\s*\)",
        "except tuple drawn entirely from the never-raised set (tensor ops "
        "return NaN/Inf; int()/round() of a finite float return without "
        "raising) -- arity-agnostic",
    ),
]


def _is_self_test(relpath: str) -> bool:
    return any(relpath.startswith(prefix) for prefix in SELF_TEST_PATTERNS)


def _iter_sources() -> list[Path]:
    """Every scannable ``.py`` under SCAN_ROOTS, caches and fixtures skipped."""
    out: list[Path] = []
    for root in SCAN_ROOTS:
        base = REPO_ROOT / root
        for path in base.rglob("*.py"):
            rel = path.relative_to(base)
            if any(part in _SKIP_DIRS for part in rel.parts):
                continue
            if _is_self_test(path.relative_to(REPO_ROOT).as_posix()):
                continue
            out.append(path)
    return sorted(out)


def main() -> int:
    violations: list[tuple[str, int, str, str]] = []
    for path in _iter_sources():
        # Repo-relative. The previous `path.relative_to(path.parents[2])` was
        # hard-wired to the depth of `src/decompmoe/*.py`: the moment the
        # scope reached `tests/`, every reported path -- and every exemption
        # key -- silently gained a `DecompMoE/` prefix.
        relpath = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            # Lines with explicit noqa are by-design (see commit message).
            if NOQA_TAG in line:
                continue
            for pat, reason in PATTERNS:
                if re.search(pat, line):
                    violations.append((relpath, lineno, line.strip(), reason))

    if not violations:
        print("lint_no_dead_defensive: OK (no anti-patterns found)")
        return 0

    print(f"lint_no_dead_defensive: {len(violations)} violation(s) found")
    print()
    for relpath, lineno, line, reason in violations:
        print(f"  {relpath}:{lineno}: {reason}")
        print(f"    {line}")
    print()
    print("If a try/except IS justified (e.g. user-provided non-tensor input),")
    print("add a `# noqa: dead-defensive` comment on the same line and a brief")
    print("justification in the commit message. Inline suppression only -- there")
    print("is no exemption table, whose (path, line) keys rot on the first line")
    print("shift above them and park their reason off-document.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
