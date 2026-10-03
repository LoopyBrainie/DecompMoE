#!/usr/bin/env python3
"""Apply a change's spec deltas to the live capability specs.

Handles MODIFIED / ADDED / REMOVED. The repo's own `scripts/merge_spec_deltas.py`
covers MODIFIED and ADDED but not REMOVED, and this change needs a REMOVED
block (req-36), so the logic lives with the change rather than mutating a
shared script.

Block boundary rule (hard-won): a Requirement block starts at an anchor whose
NEXT NON-EMPTY LINE is a `### Requirement:` heading, and ends before the next
such anchor. A BLOCK anchor such as `<a id="req-20-mci">` sits inside a
Requirement and must NOT delimit it -- treating it as a boundary once shipped
req-20 with 0 of its 14 Scenarios.

Usage:
    python evidence/apply_deltas.py --apply
    python evidence/apply_deltas.py          # dry run + verification only
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _repo import REPO  # noqa: E402

REPO = REPO
CHANGE = REPO / "openspec" / "changes" / (
    "2026-10-03-fix-a4-line-pointer-drift-and-anchor-contract"
)
CAPS = ("wayfinder", "decompmoe-skeleton", "governance")

REQ_ANCHOR = re.compile(r'<a id="([\w-]+)"></a>')
REQ_HEAD = "### Requirement:"


def is_block_start(lines: list[str], i: int) -> str | None:
    """Return the anchor id if line i starts a Requirement block, else None."""
    m = REQ_ANCHOR.match(lines[i].strip())
    if not m:
        return None
    for j in range(i + 1, min(i + 4, len(lines))):
        if lines[j].strip():
            if lines[j].startswith(REQ_HEAD):
                return m.group(1)
            return None
    return None


def requirement_slots(lines: list[str]) -> dict[str, tuple[int, int]]:
    """{anchor_id: (start, end_exclusive)} over Requirement blocks only."""
    starts = [(i, is_block_start(lines, i)) for i in range(len(lines))]
    starts = [(i, a) for i, a in starts if a]
    out: dict[str, tuple[int, int]] = {}
    for k, (i, a) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        out[a] = (i, end)
    return out


def title_of(lines: list[str], start: int) -> str:
    for j in range(start, min(start + 6, len(lines))):
        if lines[j].startswith(REQ_HEAD):
            return lines[j][len(REQ_HEAD):].strip()
    return ""


def parse_delta(text: str) -> dict[str, list[tuple[str, list[str]]]]:
    """{section: [(title, block_lines)]} for MODIFIED / ADDED / REMOVED."""
    out: dict[str, list[tuple[str, list[str]]]] = {
        "MODIFIED": [], "ADDED": [], "REMOVED": []
    }
    cur = None
    buf: list[str] = []
    head = None
    pending: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if line.startswith("## ") and "Requirements" in line:
            # FLUSH the block still being accumulated into the PREVIOUS section
            # before switching. Without this every section except the last one
            # is silently discarded -- which is why REMOVED/ADDED came back
            # empty while MODIFIED (always last) parsed fine.
            if head is not None and cur is not None:
                out[cur].append((head, _pad(buf)))
            head, buf, pending = None, [], []
            cur = line[3:].strip().split()[0].upper()
            continue
        if REQ_ANCHOR.match(line.strip()):
            # Only an anchor whose NEXT NON-EMPTY LINE is a `### Requirement:`
            # heading opens a Requirement block. A BLOCK anchor such as
            # `<a id="req-20-mci">` sits inside a Requirement and must stay
            # inline -- treating it as a delimiter truncates the block.
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            opens_block = j < len(lines) and lines[j].startswith(REQ_HEAD)
            if not opens_block:
                if head is not None:
                    buf.append(line)
                else:
                    pending.append(line)
                continue
            if head is not None:
                buf.extend(pending)
                out[cur].append((head, _pad(buf)))
                head, buf = None, []
            pending = [line]
            continue
        if line.startswith(REQ_HEAD):
            if head is not None:
                out[cur].append((head, _pad(buf)))
            head = line[len(REQ_HEAD):].strip()
            # the heading line is part of the block, not just its label --
            # dropping it leaves the merged Requirement unrecognisable
            buf = (list(pending) + [line, ""]) if pending else [line, ""]
            pending = []
            continue
        if head is not None:
            buf.append(line)
    if head is not None:
        out[cur].append((head, _pad(buf)))
    for k in out:
        out[k] = [(t, _pad(b)) for t, b in out[k]]
    return out


def _pad(block: list[str]) -> list[str]:
    while block and not block[-1].strip():
        block.pop()
    return block + [""]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rc = 0
    for cap in CAPS:
        dpath = CHANGE / "specs" / cap / "spec.md"
        mpath = REPO / "openspec" / "specs" / cap / "spec.md"
        if not dpath.exists():
            print("  (no delta for %s)" % cap)
            continue
        delta = parse_delta(dpath.read_text(encoding="utf-8"))
        master = mpath.read_text(encoding="utf-8").splitlines()
        before_sha = sha(mpath)
        slots = requirement_slots(master)

        print("=" * 70)
        print("%s   master sha=%s (%d lines)" % (cap, before_sha, len(master)))
        print("=" * 70)

        # --- validate MODIFIED titles exist in the master -------------------
        for t, _b in delta["MODIFIED"]:
            ids = [i for i, (s, e) in slots.items() if title_of(master, s) == t]
            if len(ids) != 1:
                print("  !! MODIFIED title not uniquely present: %r (%s)"
                      % (t, ids))
                rc = 1
        for t, _b in delta["REMOVED"]:
            ids = [i for i, (s, e) in slots.items() if title_of(master, s) == t]
            if len(ids) != 1:
                print("  !! REMOVED title not uniquely present: %r (%s)" % (t, ids))
                rc = 1
        if rc:
            return rc

        # --- build the new master, editing from the END backwards so earlier
        # --- line numbers stay valid -----------------------------------------
        edits = []  # (start, end, replacement)
        for t, b in delta["MODIFIED"]:
            ids = [i for i, (s, e) in slots.items() if title_of(master, s) == t]
            s, e = slots[ids[0]]
            edits.append((s, e, b, "MODIFIED " + ids[0]))
        for t, b in delta["REMOVED"]:
            ids = [i for i, (s, e) in slots.items() if title_of(master, s) == t]
            s, e = slots[ids[0]]
            # also swallow the blank separator line that precedes the block
            while s > 0 and not master[s - 1].strip():
                s -= 1
            edits.append((s, e, [], "REMOVED " + ids[0]))
        edits.sort(key=lambda x: x[0], reverse=True)

        new = list(master)
        for s, e, repl, label in edits:
            print("  %-24s lines %d..%d -> %d" % (label, s + 1, e, len(repl)))
            new = new[:s] + repl + new[e:]

        # --- append ADDED blocks at the tail --------------------------------
        for t, b in delta["ADDED"]:
            anchor = next(
                (x for x in b if REQ_ANCHOR.match(x.strip())), None
            )
            aid = REQ_ANCHOR.match(anchor.strip()).group(1) if anchor else "?"
            print("  ADDED %-19s anchor=%s lines=%d" % (t[:19], aid, len(b)))
            new = new + [""] + b

        # --- verification ----------------------------------------------------
        nslots = requirement_slots(new)
        heads = sum(1 for l in new if l.startswith(REQ_HEAD))
        anchors = len(REQ_ANCHOR.findall("\n".join(new)))
        ids = [a for a in nslots]
        dupes = {a for a in ids if ids.count(a) > 1}
        problems = 0
        if len(ids) != heads:
            print("  !! anchors %d != Requirement headings %d" % (len(ids), heads))
            problems += 1
        if dupes:
            print("  !! duplicate anchor ids: %s" % dupes)
            problems += 1
        for cap_req, _ in [(t, b) for t, b in delta["MODIFIED"]]:
            if not any(title_of(new, s) == cap_req for s, _e in nslots.values()):
                print("  !! MODIFIED block %r missing after merge" % cap_req)
                problems += 1
        if problems:
            rc = 1
            print("  NOT WRITTEN (verification failed)")
            continue

        if args.apply:
            mpath.write_text("\n".join(new) + "\n", encoding="utf-8")
            print("  -> written  sha=%s (%d lines)" % (sha(mpath), len(new)))
        else:
            print("  -> dry run OK (use --apply to write)")

    return rc


if __name__ == "__main__":
    sys.exit(main())
