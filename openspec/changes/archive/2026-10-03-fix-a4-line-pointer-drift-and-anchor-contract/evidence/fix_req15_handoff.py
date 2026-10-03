"""Task 7.3: make the removed-invariant hand-off resolve in both directions.

req-16's new Scenario already names this test and points back at req-15 by
title, but req-15 only said "the corresponding named test scenario" without
naming the Requirement's anchor, the tests, or the Scenario — so a reader
starting at req-15 had no resolvable target.

req-15 is NOT in this change's delta (which modifies req-16, req-18, req-21 and
req-23), so the live edit is mirrored into a new MODIFIED block. OpenSpec
requires a MODIFIED block to carry the WHOLE Requirement, so the block below is
extracted from the live spec after the edit rather than hand-written.
"""

import re
import sys
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _repo import REPO  # noqa: E402

ROOT = REPO
SPEC = ROOT / "openspec" / "specs" / "decompmoe-skeleton" / "spec.md"
DELTA = (ROOT / "openspec" / "changes"
         / "2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract"
         / "specs" / "decompmoe-skeleton" / "spec.md")

OLD_TAIL = (
    "Both invariants are restated under Requirement \"Centroid Driver Semantic "
    "Invariants\" where they are enforced by the corresponding named test "
    "scenario.)"
)
NEW_TAIL = (
    "Both invariants are restated under decompmoe-skeleton Req 16 Centroid "
    "Driver Semantic Invariants (`#req-16`), each with its own named guard: the "
    "`.clamp_min(ε)` empty-cell denominator by Scenario \"Semantic invariants "
    "are enforced by the named test scenarios\" via "
    "`tests/test_schedule.py::test_empty_cell_preserves_centroid`, and the "
    "`arctan(pi / sqrt(d_c))` token by Scenario \"Voronoi closed form is not the "
    "arctan shortcut\" via "
    "`tests/test_sphere.py::test_canonical_voronoi_angle_not_arctan_shortcut`.)"
)


def requirement_block(lines, req_id):
    """Lines of the Requirement introduced by `<a id="req_id"></a>`, anchor included."""
    start = next(i for i, l in enumerate(lines) if l.strip() == f'<a id="{req_id}"></a>')
    head = next(i for i in range(start + 1, len(lines))
                if lines[i].startswith("### Requirement:"))
    end = next((i for i in range(head + 1, len(lines))
                if lines[i].startswith("### Requirement:")
                or lines[i].strip().startswith("<a id=")), len(lines))
    return lines[start:end]


def main() -> int:
    problems = []
    text = SPEC.read_text(encoding="utf-8", newline="")
    # Re-entrant: a previous run may have written the live edit and then stopped
    # before the delta step. Treating "old absent + new present" as done keeps
    # the script resumable instead of aborting on its own prior output.
    if text.count(OLD_TAIL) == 1:
        with SPEC.open("w", encoding="utf-8", newline="") as fh:
            fh.write(text.replace(OLD_TAIL, NEW_TAIL, 1))
        print("  live spec: hand-off sentence updated")
    elif NEW_TAIL in text:
        print("  live spec: hand-off already updated (resumed)")
    else:
        print(f"PROBLEM: old hand-off count={text.count(OLD_TAIL)}, "
              f"new hand-off present={NEW_TAIL in text}")
        return 1

    lines = SPEC.read_text(encoding="utf-8").splitlines()
    block = requirement_block(lines, "req-15")
    if not any("test_canonical_voronoi_angle_not_arctan_shortcut" in l for l in block):
        problems.append("req-15 block does not name the new test")
    if not any("#req-16" in l for l in block):
        problems.append("req-15 block does not name req-16's anchor")
    scen = [l for l in block if l.startswith("#### Scenario:")]
    if len(scen) != 1:
        problems.append(f"req-15 must keep exactly 1 Scenario, found {len(scen)}")

    # Mirror into the delta as a MODIFIED block, carrying the whole Requirement.
    # The presence test must key on the HEADING, not on the bare title string:
    # req-16's block quotes that title inside its hand-off sentence, so a plain
    # substring test reports a block that does not exist.
    dtext = DELTA.read_text(encoding="utf-8", newline="")
    heading = "### Requirement: Hard-Constraint Grep Invariants"
    if heading in dtext:
        print("  delta: req-15 block already present, leaving as is")
    else:
        title = next(l for l in block if l.startswith("### Requirement:"))
        body = "\n".join(block)
        entry = f"\n### Requirement: {title[len('### Requirement:'):].strip()}\n\n" + \
                "\n".join(block[1:]) + "\n"
        if not entry.endswith("\n"):
            entry += "\n"
        new_delta = dtext.rstrip("\n") + "\n" + entry
        with DELTA.open("w", encoding="utf-8", newline="") as fh:
            fh.write(new_delta)
        print("  delta: req-15 MODIFIED block appended "
              f"({len(block)} lines, {len(scen)} Scenario)")

    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print("\nhand-off resolves both ways: req-15 -> #req-16 -> test, and back")
    return 0


if __name__ == "__main__":
    sys.exit(main())
