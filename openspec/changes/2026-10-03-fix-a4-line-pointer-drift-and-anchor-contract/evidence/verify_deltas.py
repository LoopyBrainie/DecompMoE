"""Verify the generated deltas.

Two independent checks:

1. BLOCK DIFF — for every Requirement the delta modifies, extract that block
   from the DELTA and difflib-unify it against the same block from the LIVE
   spec, printing every changed line. A delta that silently drops a Scenario
   or a Source field shows up here as a large unexplained `-` run.

2. RESIDUAL POINTER SCAN — re-run the census pointer detector over the
   generated delta files. Any hit is a line pointer the change claims to
   remove but did not. This is the check that actually catches a partial sweep,
   which is how this defect family survived five previous fixes.
"""
from __future__ import annotations

import difflib
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
CHANGE = REPO / "openspec" / "changes" / (
    "2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract"
)

# load the census module to reuse its (self-checked) pointer detector
spec = importlib.util.spec_from_file_location(
    "_census", CHANGE / "evidence" / "pointer_census.py"
)
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)


def blocks_of(lines):
    """{anchor_id: [lines]} using the same extraction the generator uses."""
    out = {}
    starts = {}
    for i, l in enumerate(lines):
        m = re.match(r'<a id="([\w-]+)"></a>', l.strip())
        if m:
            for j in range(i + 1, min(i + 4, len(lines))):
                if lines[j].strip():
                    if lines[j].startswith("### Requirement:"):
                        starts.setdefault(m.group(1), i)
                    break
    for r, s in starts.items():
        e = len(lines)
        for _q, si in starts.items():
            if si > s:
                e = min(e, si)
        out[r] = lines[s:e]
    return out


def main() -> int:
    problems = 0
    expected = {
        "wayfinder": ["req-2", "req-6", "req-13", "req-20", "req-32"],
        "decompmoe-skeleton": ["req-16", "req-18", "req-21", "req-23"],
        "governance": ["req-gov-2", "req-gov-4", "req-gov-6"],
    }

    print("=" * 72)
    print("1) BLOCK DIFF (delta vs live)")
    print("=" * 72)
    for cap, reqs in expected.items():
        dpath = CHANGE / "specs" / cap / "spec.md"
        dlines = dpath.read_text(encoding="utf-8").splitlines()
        llines = (REPO / "openspec" / "specs" / cap / "spec.md").read_text(
            encoding="utf-8"
        ).splitlines()
        dblocks, lblocks = blocks_of(dlines), blocks_of(llines)
        for r in reqs:
            if r not in dblocks:
                print("  !! %s/%s MISSING from delta" % (cap, r))
                problems += 1
                continue
            if r not in lblocks and r != "req-gov-6":
                print("  !! %s/%s not in live spec" % (cap, r))
                problems += 1
                continue
            if r == "req-gov-6":
                print("  -- %s/%s : ADDED, %d lines (no live counterpart)"
                      % (cap, r, len(dblocks[r])))
                continue
            diff = list(
                difflib.unified_diff(
                    lblocks[r], dblocks[r], n=0, lineterm=""
                )
            )
            chg = [
                l for l in diff
                if (l[:1] in "+-") and not l.startswith(("+++", "---"))
            ]
            dropped = [l for l in chg if l.startswith("-")]
            added = [l for l in chg if l.startswith("+")]
            print(
                "  -- %s/%s : %d removed / %d added (live %d -> delta %d lines)"
                % (cap, r, len(dropped), len(added), len(lblocks[r]), len(dblocks[r]))
            )
            # a MODIFIED block must not silently lose whole Scenarios
            sc_l = sum(1 for l in lblocks[r] if l.startswith("#### Scenario:"))
            sc_d = sum(1 for l in dblocks[r] if l.startswith("#### Scenario:"))
            if sc_d < sc_l:
                print(
                    "     !! Scenario count DROPPED %d -> %d" % (sc_l, sc_d)
                )
                problems += 1
            elif sc_d > sc_l:
                print(
                    "     ++ Scenario count %d -> %d (intentional addition)"
                    % (sc_l, sc_d)
                )
            if not any("**Source:**" in l for l in dblocks[r]) and any(
                "**Source:**" in l for l in lblocks[r]
            ):
                print("     !! **Source:** field dropped")
                problems += 1
            # replace_line swaps the WHOLE line, so a replacement that supplies
            # only a tail fragment silently destroys the rest of that line.
            # Pair each removed line with the most similar added line and
            # report a large length collapse.
            import difflib as _dl
            sm = _dl.SequenceMatcher(None, lblocks[r], dblocks[r], autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag != "replace":
                    continue
                for oi, nj in zip(range(i1, i2), range(j1, j2)):
                    a, b = lblocks[r][oi], dblocks[r][nj]
                    if len(a) >= 120 and len(b) < len(a) * 0.7:
                        print(
                            "     !! line %d COLLAPSED %d -> %d chars: %r"
                            % (oi + 1, len(a), len(b), a[:70])
                        )
                        problems += 1

    print()
    print("=" * 72)
    print("2) RESIDUAL POINTER SCAN over generated deltas")
    print("=" * 72)
    for cap in expected:
        dpath = CHANGE / "specs" / cap / "spec.md"
        for i, line in enumerate(dpath.read_text(encoding="utf-8").splitlines(), 1):
            if "http" in line:
                continue
            if census.classify(line) is None:
                continue
            exempt = census.has_historical_marker(line)
            tag = "EXEMPT" if exempt else "ACTIONABLE"
            if not exempt:
                problems += 1
            print("  %-9s delta %s:%d | %s" % (tag, cap, i, line.strip()[:150]))
    if problems == 0:
        print("  (no residual actionable pointers)")

    print()
    print("PROBLEMS =", problems)
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
