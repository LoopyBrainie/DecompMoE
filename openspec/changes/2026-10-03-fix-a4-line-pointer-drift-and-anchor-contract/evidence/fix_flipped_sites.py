"""Fix the 4 sites that became actionable after the historical-marker tightening.

`evidence/measure_marker_tightening.py` predicted exactly these 4 flips; this
script lands them. The mechanical line->Requirement resolution is deliberately
NOT used: `evidence/locate_flipped.py` shows it names the wrong Requirement for
three of the four (wayfinder L426 resolves to req-18, but the quoted ratio lives
in req-19), because the cited line numbers predate this change's own edits.
Each rewrite therefore names the Requirement by number + title + anchor.

One site is historical and is MARKED rather than re-anchored: skeleton req-23
records what cycle-12 finding 1 was, so the pre-change coordinates stay verbatim
and the line gains the explicit `(historical, ...)` marker the exemption is
required to be nameable by.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

# (relative path, exact old, exact new, expected hits)
EDITS = [
    # 1. code pointer -> module::symbol (the nan_ladder implementation)
    (
        "openspec/specs/decompmoe-skeleton/spec.md",
        "and is the implementation in `src/decompmoe/safeguards.py:62-72`)",
        "and is the implementation in `safeguards.py::nan_ladder`)",
        1,
    ),
    # 2. historical narrative -> gains a nameable historical marker
    (
        "openspec/specs/decompmoe-skeleton/spec.md",
        "The cycle-12 finding 1 (ticket A8-2 L70 centered-covariance",
        "The cycle-12 finding 1 (historical: ticket A8-2 L70 centered-covariance",
        1,
    ),
    # 3. routing-overhead allowance -> wayfinder req-19, not the resolved req-18
    (
        "tests/test_config.py",
        '"""Spec L426: routing ratio',
        '"""wayfinder Req 19 Six Baseline Set On 4070 MVP (`#req-19`): routing ratio',
        1,
    ),
    # 4. specialist-collapse boundary -> wayfinder req-11 (owns theta_Voronoi > theta_1/e)
    (
        "tests/test_sphere.py",
        "# Spec L245 literal: `arccos(15/16)",
        "# wayfinder Req 11 4070 MVP Hyperparameter Set (`#req-11`) literal: `arccos(15/16)",
        1,
    ),
]


def eol_profile(path: Path) -> tuple[int, int]:
    raw = path.read_bytes()
    crlf = raw.count(b"\r\n")
    return crlf, raw.count(b"\n") - crlf


def main() -> int:
    problems = []
    touched: set[str] = set()
    before: dict[str, tuple[int, int]] = {}
    for rel, old, new, want in EDITS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", newline="")
        n = text.count(old)
        if n != want:
            problems.append(f"{rel}: expected {want} hit(s) of {old[:60]!r}, got {n}")
            continue
        if len(new) < len(old) * 0.8:
            problems.append(f"{rel}: {old[:40]!r} would truncate ({len(old)} -> {len(new)})")
            continue
        before[rel] = eol_profile(path)
        with path.open("w", encoding="utf-8", newline="") as fh:
            fh.write(text.replace(old, new, want))
        touched.add(rel)
        print(f"  {rel}: {old[:50]!r} -> ok")

    # Re-read from disk: each replacement must be present and the old form gone.
    # Line endings are compared against the profile captured before the write —
    # an absolute CRLF expectation is wrong, since the .py files are LF and the
    # .md specs are CRLF.
    for rel in sorted(touched):
        text = (ROOT / rel).read_text(encoding="utf-8")
        for _rel, old, new, _w in [e for e in EDITS if e[0] == rel]:
            if old in text:
                problems.append(f"{rel}: old form still present: {old[:50]!r}")
            if new not in text:
                problems.append(f"{rel}: new form missing: {new[:50]!r}")
        if eol_profile(ROOT / rel) != before[rel]:
            problems.append(f"{rel}: line-ending profile changed {before[rel]} -> {eol_profile(ROOT / rel)}")

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print("\nall 4 flipped sites fixed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
