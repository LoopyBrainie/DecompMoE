#!/usr/bin/env python3
"""Rebuild the pin->HEAD drift table used by `.audit/.../lists/*.md`'s `基线` field.

WHY THIS EXISTS
---------------
The audit's drift table (`_pin_drift.json`) lived only in an out-of-repo session
directory, and the script that produced it was never preserved. Every downstream
`baseline_status` verdict is a *mechanical lookup* into that table, so the table
is a load-bearing artifact and must be regenerable.

This is the corrected copy carried by change
`2026-10-03-fix-a6-artifact-fidelity-round-2`. The archived original
(`2026-10-03-fix-a6-audit-ledger-accuracy-and-rebaseline/evidence/build_pin_drift.py`)
is left untouched; its two fidelity defects are recorded in the audit list's
`## Errata (A-6 制品复验 侧)` section:

  F-2  its `self_check()` folded key-set differences into interval equality, so
       12 keys that exist only in this generator -- all with EMPTY interval
       lists -- were silently absorbed, and the PASSED line then announced
       "identical ... (60 files, 105 intervals)" while the original table has
       only 48 keys. A reader would conclude the key sets matched too.
  F-3  its `--out` default was `pin_drift_<head[:7]>.json`, whose name reads as
       "the drift table pinned at <head>" while the payload says
       `pin=6593a06, head=95718cf...`.

FIDELITY CONTRACT
-----------------
`--self-check` rebuilds the table for the audit's own freeze
(`pin=6593a06, head=188b9fb`) and checks it against the original
`_pin_drift.json`. If the two disagree, STOP and explain -- never edit the
original table to match this generator.

The check asserts TWO SEPARATE things and reports them separately, because they
can disagree independently:

  1. INTERVAL EQUALITY on the keys the two tables share. This is the invariant
     that `基线` verdicts actually depend on.
  2. KEY-SET SANITY, as a hard assertion with an asymmetric rule:
       * a key in the ORIGINAL but not in MINE  -> FAIL. We lost a key the
         original has; that is a real disagreement.
       * a key in MINE but not in the ORIGINAL  -> FAIL **iff** it carries a
         non-empty interval list (we invented intervals). Empty-interval extras
         are benign: `git diff` registers a key for every `diff --git` header,
         including headers with no hunk (mode-only changes, or paths whose whole
         content moved). They are listed in full, never truncated.

  Key-count equality is deliberately NOT asserted, and the PASSED output says so
  explicitly. Printing a single `files=` number previously let a reader mistake
  "intervals match" for "key sets match".

`compare()` is a pure function over two parsed tables -- no I/O -- so the
negative case (a non-empty extra key MUST fail) is directly testable instead of
requiring a mutated file.

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

    Depth-relative `../..` counting breaks when `openspec archive` moves a
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


def compare(original, mine):
    """Compare two parsed drift tables. PURE -- no I/O, so it is testable.

    Returns (problems, stats). `problems` is a list of human-readable strings;
    an empty list means the check passed. `stats` carries the numbers that must
    be reported separately so that "intervals match" is never read as "key sets
    match".
    """
    problems = []
    stats = {
        "intervals_compared": 0,
        "shared": [],
        "only_original": [],
        "only_mine": [],
        "only_mine_nonempty": [],
    }

    if original.get("pin") != mine["pin"]:
        problems.append(
            "pin: original=%r mine=%r" % (original.get("pin"), mine["pin"])
        )
    if original.get("head") != mine["head"]:
        problems.append(
            "head: original=%r mine=%r" % (original.get("head"), mine["head"])
        )
    if list(original.get("commits", [])) != mine["commits"]:
        problems.append(
            "commits differ: original=%d mine=%d"
            % (len(original.get("commits", [])), len(mine["commits"]))
        )

    o_drift = original.get("drift", {})
    m_drift = mine["drift"]
    stats["only_original"] = sorted(set(o_drift) - set(m_drift))
    stats["only_mine"] = sorted(set(m_drift) - set(o_drift))
    stats["shared"] = sorted(set(o_drift) & set(m_drift))

    # (1) interval equality, on shared keys only
    for path in stats["shared"]:
        want = [list(v) for v in o_drift[path]]
        got = [list(v) for v in m_drift[path]]
        stats["intervals_compared"] += len(want)
        if want != got:
            problems.append(
                "drift[%s]: interval mismatch original=%r mine=%r" % (path, want, got)
            )

    # (2a) a key the original has and we do not is a real loss
    for path in stats["only_original"]:
        problems.append(
            "drift[%s]: present in ORIGINAL but MISSING in mine "
            "(original=%r) -- a key was lost" % (path, o_drift[path])
        )

    # (2b) an extra key is benign ONLY while it carries no intervals
    for path in stats["only_mine"]:
        if m_drift[path]:
            stats["only_mine_nonempty"].append(path)
            problems.append(
                "drift[%s]: present in MINE but not in ORIGINAL and carries "
                "NON-EMPTY intervals mine=%r -- this is a real disagreement, "
                "not a benign extra key" % (path, m_drift[path])
            )

    return problems, stats


def self_check():
    if not os.path.exists(ORIGINAL_TABLE):
        print("SELF-CHECK SKIPPED: original table not found at %s" % ORIGINAL_TABLE)
        return 0
    with io.open(ORIGINAL_TABLE, encoding="utf-8") as handle:
        original = json.load(handle)
    mine = build(AUDIT_PIN, AUDIT_HEAD)
    assert_schema(mine)

    problems, stats = compare(original, mine)

    if problems:
        print("SELF-CHECK FAILED: %d problem(s)" % len(problems))
        for line in problems[:40]:
            print("  " + line)
        if len(problems) > 40:
            print("  ... and %d more" % (len(problems) - 40))
        return 1

    print("SELF-CHECK PASSED")
    print(
        "  interval equality : %d intervals across %d shared keys, all equal"
        % (stats["intervals_compared"], len(stats["shared"]))
    )
    if stats["only_mine"]:
        print(
            "  KEY SETS ARE NOT IDENTICAL: %d key(s) exist only in mine, all "
            "with EMPTY interval lists" % len(stats["only_mine"])
        )
        print(
            "    (benign: `git diff` registers a key for every `diff --git` "
            "header, including headers with no hunk)"
        )
        for path in stats["only_mine"]:
            print("      only-in-mine (empty intervals): %s" % path)
    else:
        print("  key sets are identical (%d keys)" % len(stats["shared"]))
    if stats["only_original"]:
        print(
            "  KEY SETS ARE NOT IDENTICAL: %d key(s) exist only in the original"
            % len(stats["only_original"])
        )
        for path in stats["only_original"]:
            print("      only-in-original: %s" % path)
    print(
        "  NOTE: key-COUNT equality is deliberately not asserted. The invariants "
        "are interval equality on shared keys + every only-in-mine key being empty."
    )
    return 0


def default_out(pin, head):
    """Name the table by BOTH endpoints (F-3).

    The old `pin_drift_<head[:7]>.json` fused a type prefix and one endpoint into
    a single token, so `pin_drift_95718cf.json` read as "the drift table pinned
    at 95718cf" while the payload said `pin=6593a06`.
    """
    return "drift_%s..%s.json" % (pin[:7], head[:7])


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
        os.path.dirname(__file__), default_out(args.pin, head)
    )
    with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(table, ensure_ascii=False, indent=1, sort_keys=True))
        handle.write("\n")
    inserted_files = sum(1 for v in table["inserted"].values() if v)
    print("wrote %s" % out)
    print(
        "  drift_keys=%d  drift_intervals=%d  inserted_intervals=%d (in %d files)"
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
