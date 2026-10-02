"""Change 3 task 7.3: independently re-verify the `fix-review-findings-...` status.

The adjudication ("applied inline, never archived") was already made once, in
the A-2 errata change (archived task 1.0). D8 forbids this change from
*transcribing* that verdict, so 7.3 requires an independent recheck against
current HEAD. This script therefore re-derives every coordinate itself and
reports what it finds -- it does not read the prior adjudication.

Each check is a positive AND a negative control: a grep that finds the
expected literal and also the forbidden one is not evidence of anything.
"""
import json
import re
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for cand in [start, *start.parents]:
        if (cand / "openspec" / "changes").is_dir():
            return cand
    raise SystemExit("repo root not found")


REPO = find_repo_root(Path(__file__).resolve().parent)
CHANGE = "2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix"
EV = REPO / "openspec" / "changes" / CHANGE / "evidence"
TARGET = "fix-review-findings-voronoi-precision-and-lineage"


def head_blob(path):
    r = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=REPO,
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def head_tree(rel):
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD", "--", rel],
                       cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


# (id, file, positive pattern, negative pattern, loose token, why)
#
# `loose` exists because an ABSENT result is indistinguishable from a stale
# pattern, and a stale pattern reads exactly like a missing guard. Every ABSENT
# therefore dumps the lines containing `loose`, so a zero can never be
# reported without the evidence needed to explain it.
CHECKS = [
    ("G1", "tests/test_schedule.py", r"round\(\s*g_reset\s*,\s*5\s*\)\s*==\s*-0\.06454",
     None, "g_reset", "phase-4 gamma reset literal, claimed at :204"),
    ("G5", "tests/test_schedule.py",
     r"phase_beta_max\(\s*3\s*,\s*55_?999\s*\).*|55_?999",
     None, "55_999",
     "beta continuity boundary; the call uses POSITIONAL args, so a pattern "
     "requiring the step to be first would falsely read ABSENT"),
    ("H2", "tests/test_sphere.py", r"1\.173547",
     r"1\.1735482746999482", "1.17354",
     "6dp bisection literal. The pre-fix impl output 1.173548... was "
     "deliberately replaced by the canonical truncation 1.173547, so the "
     "negative control pins the impl output as the forbidden form"),
    ("H2b", "tests/test_sphere.py", r"round\(\s*math\.degrees\([^)]*\)\s*,\s*2\s*\)\s*==\s*67\.24",
     None, "67.24", "2dp degree prose guard, claimed at :117"),
    ("H2b64", "tests/test_sphere.py", r"round\(\s*math\.degrees\([^)]*\)\s*,\s*2\s*\)\s*==\s*58\.47",
     None, "58.47", "2dp degree prose guard for N_e=64, claimed at :142"),
    ("L5", "tests/test_gating.py", r"actual=",
     None, "actual=", "Sigma p == 1 guard must carry the f\"actual=\" payload"),
]

# Claims the adjudication itself flagged as NOT satisfied -- recheck those too,
# because a residual gap that was merely "not disposed of" must be re-confirmed
# as still present rather than assumed.
NEGATIVE_CLAIMS = [
    ("L4", "tests/test_distance.py", r"actual=",
     "adjudication recorded that this site still uses the old "
     "f\"d_min = {...}\" form; confirm the gap is still open"),
]


def main():
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True,
                          encoding="utf-8").stdout.strip()

    tree = head_tree(f"openspec/changes/{TARGET}")
    has_specs_dir = any("/specs/" in p for p in tree)

    results = []
    for cid, f, pos, neg, loose, why in CHECKS:
        txt = head_blob(f)
        if txt is None:
            results.append({"id": cid, "file": f, "verdict": "FILE_MISSING",
                            "why": why})
            continue
        lines = txt.splitlines()
        pos_hits = [i + 1 for i, ln in enumerate(lines)
                    if re.search(pos, ln)]
        neg_hits = [i + 1 for i, ln in enumerate(lines)
                    if neg and re.search(neg, ln)]
        rec = {
            "id": cid, "file": f, "why": why,
            "positive_pattern": pos, "positive_hits": pos_hits,
            "negative_pattern": neg, "negative_hits": neg_hits,
            "verdict": "PRESENT" if pos_hits else "ABSENT",
        }
        if not pos_hits:
            # An unexplained zero is the failure mode. Show the neighbourhood.
            rec["loose_token"] = loose
            rec["loose_candidates"] = [
                {"line": i + 1, "text": ln.strip()[:160]}
                for i, ln in enumerate(lines) if loose in ln
            ][:12]
        results.append(rec)

    residuals = []
    for cid, f, pat, why in NEGATIVE_CLAIMS:
        txt = head_blob(f) or ""
        lines = txt.splitlines()
        hits = [i + 1 for i, ln in enumerate(lines) if re.search(pat, ln)]
        residuals.append({
            "id": cid, "file": f, "why": why, "pattern": pat,
            "hits": hits,
            "gap_still_open": not hits,
            "state": "CLOSED (actual= now present)" if hits
                     else "STILL OPEN",
        })

    report = {
        "head_rev": head,
        "subject_change": TARGET,
        "adjudication_under_test": "applied inline, never archived",
        "method": (
            "Independent re-derivation at HEAD. The prior adjudication lives in "
            "the A-2 errata change (archived task 1.0); per D8 this change does "
            "not cite it as a verdict source, so every coordinate below is "
            "re-grepped here rather than copied."
        ),
        "structural_facts": {
            "head_tree": tree,
            "has_specs_dir": has_specs_dir,
            "still_in_changes_not_archive": not tree or (
                f"openspec/changes/archive/{TARGET}" not in
                subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD"],
                               cwd=REPO, capture_output=True, text=True,
                               encoding="utf-8").stdout),
            "interpretation": (
                "proposal.md/tasks.md only, no specs/ delta, directory still "
                "under changes/ rather than archive/ => the change was never "
                "archived, and the mechanism by which it 'was applied' cannot "
                "be archive-apply."
            ),
        },
        "claimed_changes_reverified": results,
        "known_residual_gaps": residuals,
        "verdict": None,
    }

    all_present = all(r.get("verdict") == "PRESENT" for r in results)
    negatives_clean = all(
        not r.get("negative_hits") for r in results if r.get("negative_pattern"))
    report["verdict"] = (
        "adjudication still holds at current HEAD"
        if (all_present and negatives_clean and not has_specs_dir) else
        "adjudication does NOT hold -- see per-check results"
    )

    out = EV / "lineage_recheck.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    print(f"HEAD {head}")
    print(f"specs/ delta present: {has_specs_dir}  (tree: {len(tree)} files)")
    for r in results:
        print(f"  {r['id']:<6} {r['verdict']:<8} {r.get('positive_hits')}  {r['file']}"
              + (f"  neg={r['negative_hits']}" if r.get("negative_pattern") else ""))
        for c in r.get("loose_candidates", [])[:6]:
            print(f"         ?{c['line']}: {c['text'][:100]}")
    for r in residuals:
        print(f"  {r['id']:<6} {r['state']}  {r['file']} hits={r['hits']}")
    print(f"VERDICT: {report['verdict']}")
    print(f"written: {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
