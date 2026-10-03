"""Fix a generation-time corruption in the arctan-guard Scenario.

The Scenario asserted that the ROOT of the defining equation is
`0.665773750028 rad` — which is the FORBIDDEN TOKEN's value, not the root's.
The same number was substituted into both slots, and the sentence then
contradicted its own next line, which requires `pytest.approx(1.173547,
abs=1e-6)`. The delta carries the identical corruption, so both copies are
fixed together; leaving the delta alone would reintroduce it at archive time.

Values are not re-derived here: `evidence/ac63_numeric_verification.py` measured
the root at 1.173547425920 rad (= 67.239315 deg) and the shortcut at
0.665773750028 rad (= 38.146026 deg) at d_c = 16.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TARGETS = [
    "openspec/specs/decompmoe-skeleton/spec.md",
    "openspec/changes/2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract"
    "/specs/decompmoe-skeleton/spec.md",
]

OLD = (
    "which is `0.665773750028 rad` **NOT** — the forbidden token "
    "`arctan(pi / sqrt(d_c))` evaluates to `0.665773750028 rad` at `d_c = 16`, "
    "i.e. `38.146026°`, and MUST NOT be the implementation's closed form"
)
NEW = (
    "which is `1.173547425920 rad` (`67.239315°`) at `d_c = 16` — **NOT** the "
    "forbidden token `arctan(pi / sqrt(d_c))`, which evaluates to "
    "`0.665773750028 rad` (`38.146026°`) at the same point and MUST NOT be the "
    "implementation's closed form"
)


def main() -> int:
    problems, changed = [], []
    for rel in TARGETS:
        p = ROOT / rel
        text = p.read_text(encoding="utf-8", newline="")
        n = text.count(OLD)
        if n != 1:
            problems.append(f"{rel}: expected 1 occurrence, got {n}")
            continue
        if len(NEW) < len(OLD) * 0.8:
            problems.append(f"{rel}: replacement would truncate")
            continue
        with p.open("w", encoding="utf-8", newline="") as fh:
            fh.write(text.replace(OLD, NEW, 1))
        changed.append(rel)

    # Read back: both copies must now carry the root's value in the first slot
    # and the shortcut's value in the second, and must agree byte for byte.
    lines = []
    for rel in changed:
        body = (ROOT / rel).read_text(encoding="utf-8")
        hit = [l for l in body.splitlines() if "forbidden token" in l and "1.173547425920" in l]
        if len(hit) != 1:
            problems.append(f"{rel}: fixed line not found after write")
            continue
        if not hit[0].startswith("- **THEN** it returns the root of the defining equation"):
            problems.append(f"{rel}: fixed line lost its leading clause")
        lines.append(hit[0])
    if len(lines) == 2 and lines[0] != lines[1]:
        problems.append("delta and live spec disagree on the fixed line")

    if problems:
        print("PROBLEMS:")
        for x in problems:
            print("  -", x)
        return 1
    for rel in changed:
        print(f"  fixed: {rel}")
    print("\ndelta and live spec agree; root value now 1.173547425920 rad")
    return 0


if __name__ == "__main__":
    sys.exit(main())
