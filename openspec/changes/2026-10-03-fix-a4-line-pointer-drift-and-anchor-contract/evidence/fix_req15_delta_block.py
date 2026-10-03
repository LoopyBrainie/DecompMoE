"""Repair the malformed req-15 MODIFIED block appended to the skeleton delta.

The first append emitted the Requirement heading twice and dropped the anchor
line, because it synthesised a heading and then appended `block[1:]`, which
already contained one. The existing delta blocks in this file carry the anchor
line, then a blank line, then the heading, so the replacement is built by
re-extracting req-15 from the live spec verbatim — no hand-written block.

Everything before the first malformed heading is left byte-identical.
"""

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
HEADING = "### Requirement: Hard-Constraint Grep Invariants"


def requirement_block(lines, req_id):
    start = next(i for i, l in enumerate(lines) if l.strip() == f'<a id="{req_id}"></a>')
    head = next(i for i in range(start + 1, len(lines)) if lines[i].startswith(HEADING[:3]))
    end = next((i for i in range(head + 1, len(lines))
                if lines[i].startswith("### Requirement:")
                or lines[i].strip().startswith("<a id=")), len(lines))
    return lines[start:end]


def main() -> int:
    dlines = DELTA.read_text(encoding="utf-8", newline="").splitlines()
    hits = [i for i, l in enumerate(dlines) if l.startswith(HEADING)]
    if len(hits) < 1:
        print(f"PROBLEM: no req-15 heading in the delta (found {len(hits)})")
        return 1
    cut = hits[0]

    block = requirement_block(SPEC.read_text(encoding="utf-8").splitlines(), "req-15")
    if block[0].strip() != '<a id="req-15"></a>':
        print(f"PROBLEM: extracted block does not start with the anchor: {block[0]!r}")
        return 1
    scen = [l for l in block if l.startswith("#### Scenario:")]
    if len(scen) != 1:
        print(f"PROBLEM: req-15 must carry exactly 1 Scenario, got {len(scen)}")
        return 1

    # Drop everything from the first malformed heading onward, keep one blank
    # separator, then re-emit the block exactly as the live spec has it.
    head = dlines[:cut]
    while head and not head[-1].strip():
        head.pop()
    out = head + [""] + block

    text = "\n".join(out) + "\n"
    with DELTA.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)

    # Read back and assert the block is well formed.
    check = DELTA.read_text(encoding="utf-8").splitlines()
    heads = [i for i, l in enumerate(check) if l.startswith(HEADING)]
    problems = []
    if len(heads) != 1:
        problems.append(f"delta now has {len(heads)} req-15 headings")
    else:
        i = heads[0]
        if check[i - 2].strip() != '<a id="req-15"></a>':
            problems.append(f"anchor line missing before heading; got {check[i-2]!r}")
        if not check[i - 1].strip() == "":
            problems.append("no blank line between anchor and heading")
        block2 = check[i:]
        n_scen = sum(1 for l in block2 if l.startswith("#### Scenario:"))
        if n_scen != 1:
            problems.append(f"appended block has {n_scen} Scenarios")
        if not any("test_canonical_voronoi_angle_not_arctan_shortcut" in l for l in block2):
            problems.append("appended block does not name the new test")
        # `block` starts at the anchor line, `block2` at the heading, so the
        # two are offset by the anchor plus its blank line.
        if block2[:len(block) - 2] != block[2:]:
            problems.append("appended block differs from the live req-15 body")

    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print(f"  delta: req-15 block rewritten from the live spec "
          f"({len(block)} lines, 1 Scenario, anchor restored, 1 heading)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
