#!/usr/bin/env python3
"""Rebuild the pin->HEAD drift table used by `.audit/.../lists/*.md`'s `基线` field.

WHY THIS EXISTS
---------------
The audit's drift table (`_pin_drift.json`) lived only in an out-of-repo session
directory, and the script that produced it was never preserved. Every downstream
`baseline_status` verdict is a *mechanical lookup* into that table, so the table
is a load-bearing artifact and must be regenerable.

FIDELITY CONTRACT
-----------------
`--self-check` rebuilds the table for the audit's own freeze
(`pin=6593a06, head=188b9fb`) and asserts key-by-key equality with the original
`_pin_drift.json`. If the two disagree, STOP and explain -- never edit the
original table to match this generator.

RECORDED SEMANTICS (reverse-engineered from the original table, then confirmed
hunk-by-hunk against `git diff -U0`):
  * one `git diff -U0 <pin> <head>` is parsed as a whole (default rename detection)
  * each `diff --git a/A b/B` header registers BOTH `A` and `B` as keys
  * each `@@ -a[,n] +b[,m] @@` yields the interval `[b, b + m - 1]`, clamped so
    `hi >= lo`  -->  a pure deletion (`m == 0`, `b == 0`) records `[0, 0]`, and
    `@@ -337 +340,0 @@` records `[340, 340]`
  * per-hunk intervals are NOT merged (adjacent `[166,167]` and `[168,168]` stay
    separate), and a file with no hunk at all records `[]`
  * scope is the unfiltered diff file set; `.audit/` is gitignored so it cannot
    appear

KEY ORDER IS NOT SIGNIFICANT. The self-check compares parsed objects, never raw
bytes, because the original's key order follows git's diff emission order rather
than any sort.

DISAGGREGATED VIEWS
-------------------
`drift` is deliberately LEGACY-COMPATIBLE (insertions folded in, deletions
clamped) so that the `基线` field keeps its existing definition -- the audit
decided NOT to redefine that 口径 this round. `inserted` and `modified` are the
disaggregated views, recorded as data for the next round's decision; they do not
change what gets written.
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys

def _repo_root(start):
    """Walk up until a directory holds both `openspec/` and `.audit/`.

    Depth-relative `../..` counting breaks when `openspec archive` moves this
    change one level deeper. Locate the root structurally instead.
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


REPO = _repo_root(os.path.dirname(os.path.abspath(__file__)))

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
DIFF_HEADER = re.compile(r"^diff --git a/(.+?) b/(.+)$")

AUDIT_PIN = "6593a06"
AUDIT_HEAD = "188b9fb"
ORIGINAL_TABLE = (
    "C:/Users/LamKo/.claude/projects/D--myProject-DecompMoE/"
    "a553f54e-8635-46b2-a435-55d871698d88/audit/_pin_drift.json"
)


def git(*args):
    out = subprocess.run(
        ["git"] + list(args), cwd=REPO, capture_output=True, check=True
    )
    return out.stdout.decode("utf-8", "replace")


def build(pin, head):
    """Return {pin, head, commits, drift, inserted, modified}."""
    diff = git("diff", "-U0", pin, head)
    drift = {}
    inserted = {}
    modified = {}

    def key(path):
        for table in (drift, inserted, modified):
            if path not in table:
                table[path] = []

    current = []
    for line in diff.splitlines():
        header = DIFF_HEADER.match(line)
        if header:
            old_path, new_path = header.group(1), header.group(2)
            # a rename contributes both sides; an ordinary file contributes its
            # single path once (appending twice would duplicate every interval)
            current = [old_path] if old_path == new_path else [old_path, new_path]
            for path in current:
                key(path)
            continue
        hunk = HUNK.match(line)
        if hunk and current:
            old_start, old_count, new_start, new_count = (
                int(hunk.group(1)),
                int(hunk.group(2) or 1),
                int(hunk.group(3)),
                int(hunk.group(4) or 1),
            )
            lo = new_start
            hi = max(new_start + new_count - 1, new_start)
            pure_insert = old_count == 0
            pure_delete = new_count == 0
            for path in current:
                # legacy-compatible: every hunk contributes, clamped
                drift[path].append([lo, hi])
                if pure_insert:
                    inserted[path].append([lo, hi])
                elif not pure_delete:
                    modified[path].append([lo, hi])

    def normalise(table):
        return {k: sorted(v) for k, v in sorted(table.items())}

    # newest-first, abbreviated -- matches the original table's `commits` field
    commits = git("rev-list", "--abbrev-commit", "%s..%s" % (pin, head)).split()
    return {
        "pin": pin,
        "head": head,
        "commits": commits,
        "drift": normalise(drift),
        "inserted": normalise(inserted),
        "modified": normalise(modified),
    }


def assert_schema(table):
    """Structure is asserted, never eyeballed."""
    assert set(table) == {
        "pin", "head", "commits", "drift", "inserted", "modified",
    }, "unexpected top-level keys: %r" % (sorted(table),)
    assert isinstance(table["commits"], list)
    for name in ("drift", "inserted", "modified"):
        for path, intervals in table[name].items():
            assert isinstance(path, str) and path
            for interval in intervals:
                assert (
                    isinstance(interval, list)
                    and len(interval) == 2
                    and all(isinstance(v, int) for v in interval)
                ), "bad interval in %s: %r" % (name, interval)
                assert interval[1] >= interval[0], "inverted interval %r" % interval


def self_check():
    if not os.path.exists(ORIGINAL_TABLE):
        print("SELF-CHECK SKIPPED: original table not found at %s" % ORIGINAL_TABLE)
        return 0
    with io.open(ORIGINAL_TABLE, encoding="utf-8") as handle:
        original = json.load(handle)
    mine = build(AUDIT_PIN, AUDIT_HEAD)
    assert_schema(mine)

    problems = []
    if original.get("pin") != mine["pin"]:
        problems.append("pin: original=%r mine=%r" % (original.get("pin"), mine["pin"]))
    if original.get("head") != mine["head"]:
        problems.append("head: original=%r mine=%r" % (original.get("head"), mine["head"]))
    if list(original.get("commits", [])) != mine["commits"]:
        problems.append("commits differ: original=%d mine=%d" % (
            len(original.get("commits", [])), len(mine["commits"])))

    o_drift = original.get("drift", {})
    m_drift = mine["drift"]
    for path in sorted(set(o_drift) | set(m_drift)):
        want = [list(v) for v in o_drift.get(path, [])]
        got = m_drift.get(path)
        if got is None:
            problems.append("drift[%s]: missing in mine (original=%r)" % (path, want))
        elif [list(v) for v in want] != [list(v) for v in got]:
            problems.append("drift[%s]: original=%r mine=%r" % (path, want, got))

    if problems:
        print("SELF-CHECK FAILED: %d problem(s)" % len(problems))
        for line in problems[:40]:
            print("  " + line)
        return 1
    print(
        "SELF-CHECK PASSED: drift identical to the original table "
        "(%d files, %d intervals)" % (
            len(m_drift), sum(len(v) for v in m_drift.values())
        )
    )
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pin", default=AUDIT_PIN)
    parser.add_argument("--head", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        return self_check()

    head = args.head or git("rev-parse", "HEAD").strip()
    print("pin  = %s" % args.pin)
    print("head = %s" % head)
    table = build(args.pin, head)
    assert_schema(table)
    out = args.out or os.path.join(
        os.path.dirname(__file__), "pin_drift_%s.json" % head[:7]
    )
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(table, ensure_ascii=False, indent=1, sort_keys=True))
        handle.write("\n")
    inserted_files = sum(1 for v in table["inserted"].values() if v)
    print("wrote %s" % out)
    print(
        "  files=%d  drift_intervals=%d  inserted_intervals=%d (in %d files)"
        % (
            len(table["drift"]),
            sum(len(v) for v in table["drift"].values()),
            sum(len(v) for v in table["inserted"].values()),
            inserted_files,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
