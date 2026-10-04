#!/usr/bin/env python3
"""RECOVERY: restore the hand-appended Errata tail that a generator run destroyed.

WHAT HAPPENED
-------------
While verifying the `ANNOT` duplicate-key fix, this change imported
`.audit/wayfinder-opsx-code-review/_work/_gen_listA2.py` to inspect its dict.
That module performs its write at IMPORT time, so merely importing it
regenerated `lists/opsx-changes.md` and overwrote the 4 hand-appended
`## Errata` sections -- 1930 lines collapsed to 1495.

`lists/opsx-changes.md` is NOT a pure generator product: changes A-1, A-2 and A-4
each appended an `## Errata` section after the generator last ran, and the A-6
change appended a fourth. Regenerating alone destroys that reviewed tail. This
is recorded as a hard prohibition in the change's `tasks.md` section 7.

WHAT SURVIVED
-------------
The regenerated prefix is correct and is kept as-is: the generator carries the
A-6 corrections (`OVERRIDE` + the `a6_expected.json` lock) and the expanded
`基线状态字段怎么读` section, and `_work/classified.json` was not touched.

WHAT IS RESTORED
----------------
The Errata tail is taken from the A-6 change's own pre-edit snapshot
(`evidence/_pre_edit_opsx-changes.md`), which predates the A-6 edits and
therefore still holds the 3 older Errata sections verbatim. The 4th section
(`## Errata (A-6 侧)`) did not exist at snapshot time and is restored afterwards
by the A-6 change's own `write_a6_errata_and_readme.py`, which is idempotent.

This is the same structural splice the A-6 change used, with ONE deviation: the
tail is sourced from the snapshot instead of from the live file, because the live
file no longer contains a tail. The boundary is still found structurally (the
`---` immediately preceding the first `## Errata`), never by a hardcoded line
number, and the tail is verified byte-identical against the snapshot.
"""

from __future__ import annotations

import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _repo_root(start):
    """Walk up until a directory holds both `openspec/` and `.audit/`.

    Structural, not depth-counted: `../..` counting breaks the moment this change
    is archived one level deeper.
    """
    path = os.path.abspath(start)
    while True:
        if (os.path.isdir(os.path.join(path, "openspec"))
                and os.path.isdir(os.path.join(path, ".audit"))):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            raise RuntimeError("repo root not found above %s" % start)
        path = parent


REPO = _repo_root(HERE)
A6 = os.path.join(
    REPO,
    "openspec",
    "changes",
    "archive",
    "2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline",
    "evidence",
)
SNAPSHOT = os.path.join(A6, "_pre_edit_opsx-changes.md")
LIVE = os.path.join(
    REPO, ".audit", "wayfinder-opsx-code-review", "lists", "opsx-changes.md"
)


def read_lines(path):
    with io.open(path, encoding="utf-8", newline="") as handle:
        return handle.read().split("\n")


def tail_start(lines):
    """Index of the `---` that introduces the first Errata section."""
    try:
        first = lines.index("## Errata")
    except ValueError:
        return None
    for i in range(first - 1, -1, -1):
        if lines[i].strip() == "---":
            return i
    return None


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    live = read_lines(LIVE)
    snapshot = read_lines(SNAPSHOT)

    problems = []

    # The live file must currently be the DAMAGED state, or this script would
    # compound the loss instead of repairing it.
    if "## Errata" in live:
        print("ABORTED: the live file already has an `## Errata` section.")
        print("  Nothing to recover; re-read the situation by hand.")
        return 1

    cut = tail_start(snapshot)
    if cut is None:
        print("ABORTED: no `## Errata` section in the snapshot; cannot recover.")
        return 1

    tail = snapshot[cut:]
    while tail and tail[-1] == "":
        tail.pop()

    generated = list(live)
    while generated and generated[-1] == "":
        generated.pop()

    merged = generated + tail
    text = "\n".join(merged)
    if not text.endswith("\n"):
        text += "\n"

    with io.open(LIVE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    # ---- read the file back and check it STRUCTURALLY ----
    after = read_lines(LIVE)
    while after and after[-1] == "":
        after.pop()
    if after[: len(generated)] != generated:
        problems.append("prefix mismatch after write")
    if after[len(generated):] != tail:
        problems.append("errata tail does not match the snapshot byte-for-byte")
    if len(after) != len(generated) + len(tail):
        problems.append(
            "length mismatch: %d != %d + %d" % (len(after), len(generated), len(tail))
        )
    if "## Errata" not in after:
        problems.append("`## Errata` still absent after write")

    # assert the COUNT, not just membership -- `in` on an empty list would be
    # vacuously true, and a partial restore must not read as success
    n_errata = sum(1 for line in after if line.startswith("## Errata"))
    if n_errata != 3:
        problems.append("expected 3 restored Errata sections, found %d" % n_errata)

    if problems:
        print("RECOVERY VERIFICATION FAILED:")
        for line in problems:
            print("  " + line)
        return 1

    print("recovery OK")
    print("  damaged prefix : %d lines" % len(generated))
    print("  restored tail  : %d lines (sha %s)" % (len(tail), sha("\n".join(tail))[:16]))
    print("  file now       : %d lines" % len(after))
    print("  Errata sections: %d restored (+1 pending: the A-6 side, appended next)"
          % n_errata)
    return 0


if __name__ == "__main__":
    sys.exit(main())
