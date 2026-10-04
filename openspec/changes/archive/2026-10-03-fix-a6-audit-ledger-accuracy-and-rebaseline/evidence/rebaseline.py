#!/usr/bin/env python3
"""Recompute every `baseline_status` in the audit's two lists against a
regenerated drift table, and report the differences.

SCOPE
-----
Reads `_work/classified.json` and covers every item that carries a `基线`
field in the rendered lists:
  * list A  = buckets `opsx-change` (102) + `user-decision` (6)  = 108
  * list B  = bucket `direct-fix`                              = 15

CANONICAL 口径 (UNCHANGED THIS ROUND)
-------------------------------------
The audit explicitly decided NOT to redefine what `基线` means. So the value
written into the lists is computed with the **legacy** reading only:

    pin line falls inside a `drift` interval  ->  touched-since-pin
    otherwise (incl. file absent from table)  ->  unchanged-since-pin

`inserted` intervals are recorded as a SEPARATE, ADVISORY diff
(`inserted_only` in the JSON, `evidence/inserted_only_diff.txt` in text) and
are deliberately NOT written into the lists, so that no item's status flips
this round on the strength of a 口径 nobody has approved yet.

KNOWN SOUNDNESS CAVEAT (documented, not silently fixed)
------------------------------------------------------
`drift` intervals are recorded in HEAD-side (`+`) line numbers, while
`location_line` is a PIN-side number. Comparing a pin-side line against
head-side intervals is not a sound "was this exact line touched" test. The
original table has always worked this way and every one of the audit's 123
values was produced under it; changing it would redefine 口径, which this
round was told not to do. Recorded in `evidence/baseline_basis.md`.
"""

import argparse
import io
import json
import os
import sys

def _repo_root(start):
    """Walk up until a directory holds both `openspec/` and `.audit/`.

    Depth-relative `../..` counting breaks the moment `openspec archive` moves
    this change one level deeper, so locate the root structurally instead.
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
AUDIT = os.path.join(REPO, ".audit", "wayfinder-opsx-code-review")
CLASSIFIED = os.path.join(AUDIT, "_work", "classified.json")

LIST_A_BUCKETS = ("opsx-change", "user-decision")
LIST_B_BUCKETS = ("direct-fix",)

TOUCHED = "touched-since-pin"
UNCHANGED = "unchanged-since-pin"
UNVERIFIABLE = "unverifiable (no pin line)"


def load_table(path):
    with io.open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_items(path):
    with io.open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    items = []
    for bucket in LIST_A_BUCKETS + LIST_B_BUCKETS:
        for entry in data.get(bucket, []):
            record = dict(entry)
            record["_list"] = "A" if bucket in LIST_A_BUCKETS else "B"
            record["_bucket"] = bucket
            items.append(record)
    return items


def covers(intervals, line):
    for lo, hi in intervals:
        if lo <= line <= hi:
            return [lo, hi]
    return None


def classify(item, table):
    """Return (new_status, basis, advisory_only_change)."""
    line = item.get("location_line")
    path = item.get("location_file")
    drift = table["drift"].get(path, [])
    inserted = table.get("inserted", {}).get(path, [])

    if line is None or line == 0 or not path:
        return UNVERIFIABLE, "no usable pin line number", None

    # A path that is not inside the repo is not covered by pin..HEAD at all, so
    # asserting either verdict would be false precision. The audit's own A-6
    # segment has one such item (AC-29 -> out-of-repo report).
    if not os.path.exists(os.path.join(REPO, path)):
        return UNVERIFIABLE, "path is outside the repo (no pin..%s relation)" % table["head"][:7], None

    hit = covers(drift, line)
    new = TOUCHED if hit else UNCHANGED
    if hit:
        basis = "inside drift interval [%d,%d]" % (hit[0], hit[1])
    elif path not in table["drift"]:
        basis = "file absent from drift table (no pin..%s change)" % table["head"][:7]
    else:
        basis = "line not inside any of %d drift intervals" % len(drift)

    # advisory: would the inserted-only reading differ?
    ins_hit = covers(inserted, line)
    advisory = None
    if ins_hit and not hit:
        advisory = "would be %s under the inserted-only reading (inside [%d,%d])" % (
            TOUCHED, ins_hit[0], ins_hit[1]
        )
    return new, basis, advisory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--advisory-txt", required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the recomputed baseline_status back into classified.json",
    )
    args = parser.parse_args()

    table = load_table(args.table)
    items = load_items(CLASSIFIED)

    rows = []
    for item in items:
        old = item.get("baseline_status", "<absent>")
        new, basis, advisory = classify(item, table)
        rows.append(
            {
                "bucket_id": item.get("bucket_id"),
                "list": item["_list"],
                "file": item.get("location_file"),
                "pin_line": item.get("location_line"),
                "old": old,
                "new": new,
                "changed": old != new,
                "basis": basis,
                "advisory_inserted_only": advisory,
            }
        )

    rows.sort(key=lambda r: (r["list"], str(r["bucket_id"])))
    counts = {}
    for row in rows:
        counts[row["new"]] = counts.get(row["new"], 0) + 1
    changed = [r for r in rows if r["changed"]]
    advisory = [r for r in rows if r["advisory_inserted_only"]]

    payload = {
        "pin": table["pin"],
        "head": table["head"],
        "total_items": len(rows),
        "list_a": sum(1 for r in rows if r["list"] == "A"),
        "list_b": sum(1 for r in rows if r["list"] == "B"),
        "new_counts": counts,
        "changed_count": len(changed),
        "advisory_inserted_only_count": len(advisory),
        "rows": rows,
    }
    with io.open(args.out_json, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True))
        handle.write("\n")

    with io.open(args.out_md, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("# Rebaseline diff (pin `%s` -> frozen `%s`)\n\n" % (
            table["pin"][:7], table["head"][:7]))
        handle.write(
            "Computed by `evidence/rebaseline.py` with the **unchanged** legacy "
            "口径 (`drift` intervals only). See `evidence/baseline_basis.md`.\n\n"
        )
        handle.write("| metric | value |\n|---|---|\n")
        for key in ("total_items", "list_a", "list_b", "changed_count",
                    "advisory_inserted_only_count"):
            handle.write("| %s | %s |\n" % (key, payload[key]))
        handle.write("\n### recomputed distribution\n\n")
        for name in sorted(counts):
            handle.write("- `%s`: %d\n" % (name, counts[name]))
        handle.write("\n## rows that change\n\n")
        if not changed:
            handle.write("(none)\n")
        else:
            handle.write("| item | list | file | pin line | old | new | basis |\n")
            handle.write("|---|---|---|---|---|---|---|\n")
            for row in changed:
                handle.write("| %s | %s | `%s` | %s | `%s` | `%s` | %s |\n" % (
                    row["bucket_id"], row["list"], row["file"], row["pin_line"],
                    row["old"], row["new"], row["basis"]))
        handle.write("\n## all rows\n\n")
        handle.write("| item | list | file | pin line | old | new | basis |\n")
        handle.write("|---|---|---|---|---|---|---|\n")
        for row in rows:
            handle.write("| %s | %s | `%s` | %s | `%s` | `%s` | %s |\n" % (
                row["bucket_id"], row["list"], row["file"], row["pin_line"],
                row["old"], row["new"], row["basis"]))

    with io.open(args.advisory_txt, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "Inserted-only reading: rows that WOULD change if a pure-insertion "
            "hunk counted as `touched-since-pin`.\n\n"
            "NOT written into the lists this round -- the audit decided not to "
            "redefine the 口径. Recorded for the next round's decision.\n\n"
        )
        if not advisory:
            handle.write("(none)\n")
        for row in advisory:
            handle.write(
                "- %s (%s) `%s:%s` -> %s\n"
                % (row["bucket_id"], row["list"], row["file"], row["pin_line"],
                   row["advisory_inserted_only"])
            )

    if args.apply:
        # Write the recomputed value back, but only after asserting that the
        # stored old value is the one the diff was computed against. A mismatch
        # means classified.json moved under us and the whole diff is void.
        with io.open(CLASSIFIED, encoding="utf-8") as handle:
            data = json.load(handle)
        lookup = {}
        for bucket in LIST_A_BUCKETS + LIST_B_BUCKETS:
            for entry in data.get(bucket, []):
                lookup[entry.get("bucket_id")] = entry
        drift = []
        written = 0
        for row in rows:
            entry = lookup.get(row["bucket_id"])
            if entry is None:
                drift.append("%s: absent from classified.json" % row["bucket_id"])
                continue
            if entry.get("baseline_status") != row["old"]:
                drift.append("%s: stored %r, diff computed against %r" % (
                    row["bucket_id"], entry.get("baseline_status"), row["old"]))
                continue
            if row["changed"]:
                entry["baseline_status"] = row["new"]
                written += 1
        if drift:
            print("APPLY ABORTED -- %d problem(s); classified.json NOT written" % len(drift))
            for line in drift[:20]:
                print("  " + line)
            return 1
        with io.open(CLASSIFIED, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=1)
            handle.write("\n")
        print("applied %d baseline_status correction(s) to classified.json" % written)

    print("items=%d (A=%d B=%d) changed=%d advisory=%d" % (
        len(rows), payload["list_a"], payload["list_b"], len(changed), len(advisory)))
    for name in sorted(counts):
        print("  %-28s %d" % (name, counts[name]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
