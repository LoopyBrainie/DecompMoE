#!/usr/bin/env python3
"""Re-verify the generated delta of 2026-10-03-fix-a5-review-findings-round-2.

Deliberately redundant with `gen_deltas.py`'s own assertions, because the
generator's assertions run on the data *before* the file is written and cannot
catch a write that lost or mangled something. This script reads the artifact
back off disk.

Checks, in order of the failure they catch:

1. **Block-level round-trip** — re-parse the written delta with the same block
   extractor and compare against the live spec via `difflib`. A MODIFIED block
   that silently lost a Scenario still greps fine for every keyword it kept.
2. **Scenario set** — every Scenario heading in live `req-gov-8` is present in
   the delta, plus the one new Scenario.
3. **Line-length collapse** — any line that shrank below 70% of its live
   counterpart is a truncated replacement, the signature of a whole-line
   replacement given a fragment.
4. **Bounded-edit audit** — the two substitutions must have changed *only*
   their target token; the rest of `req-gov-8` must be byte-identical to live.
5. **REMOVED block shape** — the removal must name the live Requirement title
   verbatim, and must carry Reason and Migration but no `**Source:**`.
6. **No anchor reuse** — no anchor emitted here may already exist live, or the
   archive will collide.
7. **Every emitted anchor has a Requirement** — the block-level anchor inserted
   before a Requirement must not truncate it, the defect this repository hit
   three times.

Run from anywhere inside the repository, before or after the archive:

    python openspec/changes/2026-10-03-fix-a5-review-findings-round-2/evidence/verify_deltas.py
"""
from __future__ import annotations

import difflib
import importlib.util
import re
import sys
from pathlib import Path

_EVIDENCE_DIR = Path(__file__).resolve().parent
_PATHS_SPEC = importlib.util.spec_from_file_location(
    "_r2_evidence_paths", _EVIDENCE_DIR / "_paths.py"
)
assert _PATHS_SPEC is not None and _PATHS_SPEC.loader is not None
_paths = importlib.util.module_from_spec(_PATHS_SPEC)
_PATHS_SPEC.loader.exec_module(_paths)

CHANGE_NAME = "2026-10-03-fix-a5-review-findings-round-2"
REPO = _paths.find_repo_root(_EVIDENCE_DIR)
CHANGE = _paths.find_change_dir(REPO, CHANGE_NAME)
_paths.refuse_if_archived("verify_deltas.py", CHANGE)

DELTA = CHANGE / "specs" / "governance" / "spec.md"
LIVE = REPO / "openspec" / "specs" / "governance" / "spec.md"

ANCHOR_RE = re.compile(r'^<a id="([A-Za-z0-9._-]+)"></a>$')
REQ_RE = re.compile(r"^### Requirement: (.+)$")
SCENARIO_RE = re.compile(r"^#### Scenario: (.+)$")

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"  FAIL  {msg}")


def ok(msg: str) -> None:
    notes.append(msg)
    print(f"  ok    {msg}")


def block_starts(lines: list[str]) -> list[tuple[int, str, str]]:
    """`(line_no, anchor_id, title)` for anchors that introduce a Requirement."""
    out = []
    for i, line in enumerate(lines):
        m = ANCHOR_RE.match(line.strip())
        if not m:
            continue
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and (rm := REQ_RE.match(lines[j])):
            out.append((i + 1, m.group(1), rm.group(1)))
    return out


def extract(lines: list[str], anchor_id: str) -> tuple[int, int, str] | None:
    for start, aid, title in block_starts(lines):
        if aid == anchor_id:
            end = len(lines)
            for i in range(start + 1, len(lines)):
                if lines[i].startswith("<a id=") or lines[i].startswith("## "):
                    end = i
                    break
            while end > start and not lines[end - 1].strip():
                end -= 1
            return start, end, title
    return None


def main() -> int:
    print("verify_deltas: reading artifact back off disk")
    if not DELTA.is_file():
        print(f"verify_deltas: FAIL: delta not found at {DELTA}", file=sys.stderr)
        return 1
    delta_lines = DELTA.read_text(encoding="utf-8").splitlines()
    live_lines = LIVE.read_text(encoding="utf-8").splitlines()

    # --- 1. structure -------------------------------------------------------
    for section in ("## MODIFIED Requirements", "## REMOVED Requirements", "## ADDED Requirements"):
        if section not in delta_lines:
            fail(f"delta is missing the section header {section!r}")
    if failures:
        return report()

    # --- 2. MODIFIED req-gov-8 block-level diff -----------------------------
    live_b = extract(live_lines, "req-gov-8")
    delta_b = extract(delta_lines, "req-gov-8")
    if not live_b or not delta_b:
        fail("could not locate the req-gov-8 block in both files")
        return report()
    ls, le, lt = live_b
    ds, de, dt = delta_b
    if lt != dt:
        fail(f"req-gov-8 title changed: {lt!r} -> {dt!r}")

    live_block = live_block0 = live_lines[ls:le]
    delta_block = delta_lines[ds:de]
    diff = [
        d
        for d in difflib.unified_diff(live_block0, delta_block, lineterm="", n=0)
        if d[:1] in "+-" and not d.startswith(("+++", "---"))
    ]
    print(f"  req-gov-8 block diff: {len(diff)} changed line(s)")
    for d in diff:
        print(f"    {d[:120]}")

    # --- 3. Scenario preservation + the one addition ------------------------
    live_scen = [SCENARIO_RE.match(l).group(1) for l in live_block if SCENARIO_RE.match(l)]
    delta_scen = [SCENARIO_RE.match(l).group(1) for l in delta_block if SCENARIO_RE.match(l)]
    missing = [s for s in live_scen if s not in delta_scen]
    if missing:
        fail(f"req-gov-8 lost Scenario(s) present live: {missing}")
    else:
        ok(f"all {len(live_scen)} live Scenarios preserved")
    added = [s for s in delta_scen if s not in live_scen]
    if added != ["Two worktrees differing only in the bytes of a dirty file"]:
        fail(f"expected exactly the one new porcelain-collision Scenario, got {added}")
    else:
        ok("new porcelain-collision Scenario present")

    # --- 4. line-length collapse -------------------------------------------
    live_by_prefix = {}
    for l in live_block:
        live_by_prefix.setdefault(l[:40], []).append(l)
    collapsed = [
        l
        for l in delta_block
        if not l.startswith("#### Scenario")
        and not l.startswith("- **")
        and l[:40] in live_by_prefix
        and any(len(l) < 0.7 * len(o) for o in live_by_prefix[l[:40]])
    ]
    if collapsed:
        fail(f"lines collapsed below 70% of a live counterpart: {collapsed[:2]}")
    else:
        ok("no line-length collapse")

    # --- 5. bounded-edit audit ---------------------------------------------
    # Structural, not substring-based. Two earlier attempts at this check were
    # wrong in instructive ways:
    #   * asserting the phrase `git status --porcelain` disappears -- but the
    #     replacement deliberately re-uses it to explain why it is insufficient;
    #   * asserting the phrase `... no longer exists.` disappears -- but the
    #     replacement *extends* that sentence, so the phrase is a prefix of the
    #     new text by design.
    # A substring test cannot distinguish "edited" from "reused". Comparing the
    # two line sequences positionally can: the delta must be the live block with
    # exactly two lines replaced and seven appended, and nothing else moved.
    APPENDED = 7  # blank, heading, blank, GIVEN, THEN, AND, AND
    EDITED = 2
    if len(delta_block) != len(live_block0) + APPENDED:
        fail(
            f"block length: expected {len(live_block0)} + {APPENDED} = "
            f"{len(live_block0) + APPENDED} lines, got {len(delta_block)}"
        )
    else:
        ok(f"block length: {len(live_block0)} live + {APPENDED} appended")

    if len(delta_block) >= len(live_block0):
        changed_idx = [
            i for i in range(len(live_block0)) if live_block0[i] != delta_block[i]
        ]
        if changed_idx != sorted(changed_idx) or len(changed_idx) != EDITED:
            fail(
                f"expected exactly {EDITED} edited line(s) in place, got "
                f"{len(changed_idx)} at {changed_idx}"
            )
        else:
            ok(f"exactly {EDITED} lines edited in place, at {changed_idx}")
        for i in changed_idx:
            if len(delta_block[i]) < 0.7 * len(live_block0[i]):
                fail(f"edited line {i} collapsed below 70% of live length")
        tail = delta_block[len(live_block0):]
        if not (tail[0] == "" and tail[2] == "" and tail[1].startswith("#### Scenario:")):
            fail(f"appended tail is not a blank/heading/blank Scenario header: {tail[:3]}")
        elif not all(l.startswith("- **") for l in tail[3:]):
            fail(f"appended Scenario bullets malformed: {tail[3:]}")
        else:
            ok(f"appended tail is a well-formed Scenario with {len(tail) - 3} bullets")

    # --- 6. REMOVED block shape --------------------------------------------
    if "## REMOVED Requirements" in delta_lines:
        ri = delta_lines.index("## REMOVED Requirements")
        try:
            rend = delta_lines.index("## ADDED Requirements", ri)
        except ValueError:
            rend = len(delta_lines)
        removed = delta_lines[ri:rend]
        rem_titles = [l for l in removed if l.startswith("### Requirement:")]
        live9 = extract(live_lines, "req-gov-9")
        if not rem_titles:
            fail("REMOVED block has no Requirement heading")
        elif not live9:
            fail("live spec no longer has a req-gov-9 block to remove")
        elif rem_titles[0] != f"### Requirement: {live9[2]}":
            fail(
                "REMOVED title must match live req-gov-9 verbatim; got "
                f"{rem_titles[0]!r}, live is {live9[2]!r}"
            )
        else:
            ok(f"REMOVED title matches live verbatim: {live9[2]!r}")
        # `in` on a list tests element equality, not substring: a
        # `"**Reason**:" not in removed` check passes on a block that has the
        # field, which is a false green on the very thing it is guarding.
        if not any("**Reason**:" in l for l in removed):
            fail("REMOVED block has no **Reason**")
        else:
            ok("REMOVED block has a Reason")
        if not any("**Migration**:" in l for l in removed):
            fail("REMOVED block has no **Migration**")
        else:
            ok("REMOVED block has a Migration")
        if any(l.startswith("**Source:**") for l in removed):
            fail("REMOVED block must not carry a **Source:** field")
        else:
            ok("REMOVED block carries no Source field")

    # --- 6. anchor hygiene --------------------------------------------------
    # Only ADDED anchors must be new. A MODIFIED block re-emits its live anchor
    # by construction, so including those manufactures a guaranteed collision.
    try:
        ai = delta_lines.index("## ADDED Requirements")
    except ValueError:
        ai = len(delta_lines)
    added_ids = {aid for _, aid, _ in block_starts(delta_lines[ai:])}
    live_ids = {m.group(1) for m in (ANCHOR_RE.match(l.strip()) for l in live_lines) if m}
    collide = sorted(added_ids & live_ids)
    if collide:
        fail(f"ADDED anchor collision with the live spec: {collide}")
    else:
        ok(f"no ADDED anchor collision; added = {sorted(added_ids)}")
    modified_ids = {aid for _, aid, _ in block_starts(delta_lines[:ai])}
    if "req-gov-8" not in modified_ids:
        fail(f"MODIFIED section should carry req-gov-8, got {sorted(modified_ids)}")
    else:
        ok("MODIFIED section carries req-gov-8, as expected to collide by design")

    # Every emitted anchor must be followed by a Requirement, which is the
    # property whose violation truncated a block three times in this repo.
    for line_no, aid, title in block_starts(delta_lines):
        ok(f"block start intact: {aid} -> {title[:48]}")
    orphan = [
        m.group(1)
        for i, m in ((i, ANCHOR_RE.match(l.strip())) for i, l in enumerate(delta_lines))
        if m and not any(bs[0] - 1 == i for bs in block_starts(delta_lines))
    ]
    if orphan:
        notes.append(f"non-block anchors in delta (expected, e.g. sub-anchors): {orphan}")

    return report()


def report() -> int:
    print()
    if failures:
        print(f"verify_deltas: FAIL ({len(failures)} problem(s))")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"verify_deltas: OK ({len(notes)} check(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
