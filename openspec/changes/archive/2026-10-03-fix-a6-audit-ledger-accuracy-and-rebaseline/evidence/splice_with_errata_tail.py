# -*- coding: utf-8 -*-
"""Splice a fresh generator run onto the manually-appended Errata tail.

WHY
---
`lists/opsx-changes.md` is NOT a pure product of `_gen_listA2.py`. Three changes
(A-1, A-2, A-4) each appended a `## Errata` section AFTER the generator last ran.
Running the generator alone therefore destroys ~369 lines of reviewed content --
measured, not assumed: the pre-edit file is 1842 lines while a plain regeneration
produces 1473.

So the write is: new generated prefix + byte-identical old tail. The tail boundary
is found structurally (the `---` that immediately precedes the first `## Errata`),
not by a hardcoded line number, and both halves are verified afterwards.

Refuses to run if the live file no longer matches the pre-edit snapshot, because
that means someone else edited it and this splice would clobber their work.
"""
import hashlib
import io
import os
import sys

REPO = r"D:/myProject/DecompMoE"
LIVE = os.path.join(REPO, ".audit", "wayfinder-opsx-code-review", "lists", "opsx-changes.md")
SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "_pre_edit_opsx-changes.md")
GENERATED = sys.argv[1] if len(sys.argv) > 1 else r"C:/Users/LamKo/AppData/Local/Temp/a6_new_gen.md"


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
    if live != snapshot:
        print("ABORTED: live file differs from the pre-edit snapshot.")
        print("  live sha=%s" % sha("\n".join(live))[:16])
        print("  snap sha=%s" % sha("\n".join(snapshot))[:16])
        print("Someone edited the list after this change snapshotted it. Re-read and merge by hand.")
        return 1

    cut = tail_start(live)
    if cut is None:
        print("ABORTED: no `## Errata` section found in the live file; refusing to guess the boundary.")
        return 1

    tail = live[cut:]
    generated = read_lines(GENERATED)
    # a trailing "" from the final newline must not become a blank line
    while generated and generated[-1] == "":
        generated.pop()

    merged = generated + tail
    text = "\n".join(merged)
    if not text.endswith("\n"):
        text += "\n"

    with io.open(LIVE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    # ---- verify the write by reading it back ----
    after = read_lines(LIVE)
    problems = []
    if after[:len(generated)] != generated:
        problems.append("prefix mismatch after write")
    if after[len(generated):] != tail:
        problems.append("errata tail changed")
    if len(after) != len(generated) + len(tail):
        problems.append("length mismatch: %d != %d + %d" % (
            len(after), len(generated), len(tail)))
    if problems:
        print("WRITE VERIFICATION FAILED:")
        for line in problems:
            print("  " + line)
        return 1

    print("spliced OK")
    print("  old file      : %d lines (generated %d + tail %d)" % (
        len(live), len(live) - len(tail), len(tail)))
    print("  new file      : %d lines (generated %d + tail %d)" % (
        len(after), len(generated), len(tail)))
    print("  errata tail   : %d lines preserved byte-identically (sha %s)" % (
        len(tail), sha("\n".join(tail))[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
