"""Change 3 task 7.1: register the excluded buckets A-6 / A-8 with reasons.

Emits evidence/excluded.json. The item lists are READ FROM ledger.json rather
than retyped, so the registration cannot drift from the ledger it describes.

Required registrations (tasks.md 7.1):
  - A-6 (7 items) and A-8 (6 items) with exclusion reasons
  - A-8 uses the `### UD-` heading prefix, not `### AC-` -- this was the source
    of a real false alarm ("ledger is missing 6 items"), so the registration
    must record that the alarm was the scanner's, not the ledger's
  - blind-spot 3 / 4 items (7 of them) measured to fall entirely in A-6
  - the ledger's own denominator arithmetic: 95 in-source + 9 unregistered
    + 13 excluded = 117 handled, of which 104 are ledger entries
"""
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for cand in [start, *start.parents]:
        if (cand / "openspec" / "changes").is_dir():
            return cand
    raise SystemExit("repo root not found")


REPO = find_repo_root(Path(__file__).resolve().parent)
CHANGE = ("2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix")
EV = REPO / "openspec" / "changes" / CHANGE / "evidence"
LEDGER = EV / "ledger.json"

REASONS = {
    "A-6": {
        "name": "verdict-criteria / mirror-divergence / precedent disputes",
        "reason": (
            "These items dispute the audit's own adjudication criteria, the "
            "divergence between the pin-state and its mirror, or which prior "
            "precedent governs. Re-deciding them requires settling a "
            "methodological question that is out of scope for this change; "
            "doing it here would silently pick a side of an open dispute and "
            "then report it as a measurement."
        ),
    },
    "A-8": {
        "name": "UD-01..UD-06, awaiting user adjudication",
        "reason": (
            "Six `### UD-` headings (not `### AC-`) that the audit raised but "
            "did not decide; they need a user call, not a remeasurement."
        ),
    },
}

BLIND_SPOT_3_4 = ["AC-06", "AC-26", "AC-27", "AC-29", "AC-30", "AC-50", "AC-51"]


def main():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    excluded = ledger["excluded_items"]

    by_bucket = {}
    for it in excluded:
        by_bucket.setdefault(it["bucket"], []).append(it)

    # Control: the counts in tasks.md 7.1 (A-6=7, A-8=6, total 13).
    expected = {"A-6": 7, "A-8": 6}
    for b, n in expected.items():
        got = len(by_bucket.get(b, []))
        if got != n:
            raise SystemExit(
                f"bucket {b}: expected {n} items, ledger has {got} -- "
                "tasks.md 7.1 registration is stale, fix it before writing")

    # Control: blind-spot 3/4 items must all be A-6, else the "no impact on
    # the 104 scope" claim in 7.1 is false.
    bucket_of = {it["ac_id"]: it["bucket"] for it in excluded}
    stragglers = [i for i in BLIND_SPOT_3_4 if bucket_of.get(i) != "A-6"]
    if stragglers:
        raise SystemExit(
            f"blind-spot 3/4 items not all in A-6: {stragglers} -- "
            "tasks.md 7.1's 'no impact on the 104-item scope' claim is false")

    report = {
        "change": CHANGE,
        "source": "evidence/ledger.json :: excluded_items",
        "why_a_separate_file": (
            "excluded_items inside ledger.json is a bare id+bucket+title list. "
            "tasks.md 7.1 requires the *reasons*, and a reason that lives only "
            "in prose is the same citation-drift class this change exists to "
            "eliminate."
        ),
        "buckets": {
            b: {
                "item_count": len(items),
                "ids": [i["ac_id"] for i in items],
                "items": items,
                **REASONS[b],
            }
            for b, items in sorted(by_bucket.items())
        },
        "ud_prefix_note": {
            "claim": "A-8 headings use `### UD-`, not `### AC-`",
            "evidence": "ledger excluded_items carry ac_id UD-01..UD-06",
            "false_alarm": (
                "An earlier scan of this change reported 'the ledger is missing "
                "6 items'. The defect was the scanner's regex (it only matched "
                "`### AC-`), not a gap in the ledger. Recorded because a "
                "corrected alarm is still evidence."
            ),
        },
        "blind_spots_3_and_4": {
            "ids": BLIND_SPOT_3_4,
            "all_in": "A-6",
            "impact": (
                "All 7 fall in an excluded bucket, so the 104-item scope is "
                "unaffected by excluding A-6."
            ),
        },
        "denominators": {
            "in_source": ledger["total_in_source"],
            "unregistered": ledger["total_unregistered"],
            "excluded": len(excluded),
            "handled_total": (ledger["total_in_source"]
                              + ledger["total_unregistered"]
                              + len(excluded)),
            "ledger_entries": ledger["total"],
            "identity": (
                f"{ledger['total_in_source']} + {ledger['total_unregistered']} "
                f"+ {len(excluded)} = "
                f"{ledger['total_in_source'] + ledger['total_unregistered'] + len(excluded)}"
                f" handled, of which {ledger['total']} are ledger entries"
            ),
        },
        "source_bucket_counts_unchanged": dict(Counter(
            it["bucket"] for it in excluded)),
    }

    out = EV / "excluded.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"A-6: {report['buckets']['A-6']['item_count']} items")
    print(f"A-8: {report['buckets']['A-8']['item_count']} items")
    print(f"blind-spot 3/4: {len(BLIND_SPOT_3_4)} items, all in A-6 -> confirmed")
    print(f"denominators: {report['denominators']['identity']}")
    print(f"written: {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
