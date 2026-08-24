#!/usr/bin/env python3
"""Lint gate: detect dead defensive try/except around PyTorch tensor ops.

Background (per review of commit 9978c11, see opsx:fix-math-consistency-audit-2026-08-apply):
    "fix-commit-induced-dead-defensive-code" anti-pattern.

The review identified 3 try/except blocks in src/decompmoe/metrics.py that
were inserted to satisfy an automated linter (pi-lens) but in fact could
never trigger (PyTorch tensor division returns NaN/Inf, never raises).

This script greps the source for the anti-pattern. On hit, exits non-zero.

Anti-patterns flagged:
  1. `except (ValueError, ZeroDivisionError)` around tensor division
  2. `int(...item())` wrapped in try/except (0-d .item() never raises)
  3. `float(shape[i])` wrapped in try/except (int → float never raises)

Lines tagged `# noqa: dead-defensive` are EXPLICITLY by-design; all OTHER
matches are real anti-patterns to fix in code review.

Run as a pre-commit gate or in CI:
    python scripts/lint_no_dead_defensive.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src" / "decompmoe"

NOQA_TAG = "noqa: dead-defensive"

# Patterns that indicate a try/except where the excepted exceptions are
# mathematically unreachable given the wrapped operation.
PATTERNS: list[tuple[str, str]] = [
    # (regex, human-readable rationale)
    (
        r"except\s*\(\s*ValueError\s*,\s*ZeroDivisionError\s*\)",
        "ValueError+ZeroDivisionError around tensor ops (PyTorch never raises these; returns NaN/Inf instead)",
    ),
    (
        r"except\s*\(\s*ValueError\s*,\s*RuntimeError\s*\)",
        "ValueError+RuntimeError around 0-d tensor .item() (never raises on 0-d)",
    ),
    (
        r"except\s*\(\s*TypeError\s*,\s*ValueError\s*\)",
        "TypeError+ValueError around int→float conversion (never raises)",
    ),
]


def main() -> int:
    violations: list[tuple[Path, int, str, str]] = []
    for path in sorted(SRC_DIR.glob("*.py")):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            # Lines with explicit noqa are by-design (see commit message).
            if NOQA_TAG in line:
                continue
            for pat, reason in PATTERNS:
                if re.search(pat, line):
                    violations.append((path, lineno, line.strip(), reason))

    if not violations:
        print("lint_no_dead_defensive: OK (no anti-patterns found)")
        return 0

    print(f"lint_no_dead_defensive: {len(violations)} violation(s) found")
    print()
    for path, lineno, line, reason in violations:
        rel = path.relative_to(path.parents[2])
        print(f"  {rel}:{lineno}: {reason}")
        print(f"    {line}")
    print()
    print("If a try/except IS justified (e.g. user-provided non-tensor input),")
    print("add a `# noqa: dead-defensive` comment on the same line and a brief")
    print("justification in the commit message.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
