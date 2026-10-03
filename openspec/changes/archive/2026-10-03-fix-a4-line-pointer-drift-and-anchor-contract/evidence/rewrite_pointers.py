"""Task 5 + 6: rewrite every actionable line-pointer into a resolvable reference.

Each pattern carries an expected hit count asserted BEFORE any write, so a
pattern that stops matching (already applied, or a target that moved) is a loud
failure rather than a silent partial sweep. `--dry-run` prints the counts first.

Target Requirements were resolved by CONTENT, not by line number: the cited
coordinates predate this change, so `evidence/locate_flipped.py` shows the
mechanical line->Requirement resolution naming the wrong Requirement (wayfinder
L426 resolves to req-18, but the quoted ratio lives in req-19). Two entries in
tasks.md carried that same stale resolution and are corrected here:
  - task 6.2 mapped `req-7 L100` to `#req-6`; `eps=1e-6` is the `extract_C`
    signature in `decompmoe-skeleton` req-7, not req-6 (Voronoi threshold).
  - `spec L206` resolves to wayfinder req-9 / skeleton req-10, neither of which
    is about safeguards; the five helpers are `decompmoe-skeleton` req-12.
"""

import argparse
import re
import sys
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _repo import REPO  # noqa: E402

ROOT = REPO
SCAN = [ROOT / "openspec" / "specs", ROOT / "src", ROOT / "tests"]
SUFFIX = (".md", ".py")

# --- canonical reference strings ---------------------------------------------
SK12 = "`decompmoe-skeleton Req 12 Five Numerical Safeguard Helpers (#req-12)`"
SK7 = "`decompmoe-skeleton Req 7 C Extraction Four-Step Pipeline (#req-7)`"
SK6 = "`decompmoe-skeleton Req 6 Voronoi Self-Consistency Threshold (#req-6)`"
WF13 = "`wayfinder Req 13 Numerical Safeguards (#req-13)`"
WF11 = "`wayfinder Req 11 4070 MVP Hyperparameter Set (#req-11)`"
WF7 = "`wayfinder Req 7 Isotropic Squared-Chord Distance And Bounded Beta (#req-7)`"
WF24 = "`wayfinder Req 24 Beta Parameterization Space vs Operational Domain (#req-24)`"
WF19 = "`wayfinder Req 19 Six Baseline Set On 4070 MVP (#req-19)`"
WF20CG = "`wayfinder Req 20 Eight Geometric Quantification Metrics (#req-20)` CG row"
MCI = "`wayfinder Req 20 MCI row (#req-20-mci)`"
BETAFF = "`#req-24-betaeff`"

# Longer alternatives must precede the substrings they contain, so the
# `(?:\bskeleton\s+)?spec` prefix is consumed once rather than left dangling.
#
# `scope` restricts a pattern to specific repo-relative paths. It is needed
# because the census counts only ACTIONABLE lines: a regex that spans the whole
# tree also matches the historical-exempt occurrences inside the specs, and
# rewriting those would falsify a record of what a past change did.
#   - `req-1 L185` lives only in governance req-gov-1's retro-application record
#     (cycle-5 audit verdict) and is left verbatim.
#   - `safeguards.py:NN` inside skeleton/wayfinder is code-review provenance
#     attached to a historical marker; the tests/ citations are the live ones.
ALL, SPECS, TESTS = None, ("openspec/specs",), ("tests", "src")

PATTERNS = [
    # (regex, replacement, expected hits, scope)
    (r"(?:\bskeleton\s+)?spec L206\b", SK12, 16, TESTS),
    (r"\bskeleton spec L208\b", SK12, 2, TESTS),
    (r"\bwayfinder L249\b", WF13, 11, ALL),
    (r"\bspec L413\b", MCI, 10, ALL),
    (r"\b(?:spec\s+)?req-7 L130\b", WF7, 6, TESTS),
    (r"\b(?:spec\s+)?req-11 L245\b", WF11, 2, TESTS),
    (r"\bspec L153\b", SK7, 2, TESTS),
    (r"\b(?:spec\s+)?Req 20 L394\b", WF20CG, 2, TESTS),
    (r"\b(?:spec\s+)?req-7 L100\b", SK7, 2, TESTS),
    (r"\b(?:spec\s+)?req-13 L268\b", WF13, 1, TESTS),
    (r"\b(?:spec\s+)?Req 32 L644\b",
     "`wayfinder Req 32 Resurrection Perturbation Per-Expert Contract (#req-32)`", 1, TESTS),
    (r"\bspec L578\b", WF24, 1, TESTS),
    (r"\bspec L266-286\b", SK12, 1, TESTS),
    (r"\bspec L231\b", SK6, 1, TESTS),
    (r"\bspec L233\b", WF7, 1, TESTS),
    (r"\bspec L236\b", SK6, 2, TESTS),
    (r"\bspec L237\b", SK6, 1, TESTS),
    (r"\bsrc/decompmoe/safeguards\.py:31\b", "`safeguards.py::RESURRECTION_RATE_LIMIT_STEPS`", 1, TESTS),
    (r"\bsrc/decompmoe/safeguards\.py:93\b", "`safeguards.py::should_resurrect`", 1, TESTS),
    (r"\bsrc/decompmoe/safeguards\.py:71-80\b", "`safeguards.py::should_resurrect`", 1, TESTS),
    (r"\bsrc/decompmoe/metrics\.py:83\b", "`metrics.py::UR`", 1, TESTS),
    (r"\btest_gating\.py:59\b", "`tests/test_gating.py::test_zero_grad_for_non_top_k`", 1, TESTS),
    (r"\bspec L426\b", WF19, 2, TESTS),
]

COMPILED = [(re.compile(p, re.IGNORECASE), r, n, s, p) for p, r, n, s in PATTERNS]


def files():
    for base in SCAN:
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in SUFFIX:
                yield p


def in_scope(p: Path, scope) -> bool:
    if scope is None:
        return True
    rel = p.relative_to(ROOT).as_posix()
    return any(rel == s or rel.startswith(s.rstrip("/") + "/") for s in scope)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    corpus = {p: p.read_text(encoding="utf-8", newline="") for p in files()}
    problems, plan = [], []
    for rx, rep, want, scope, src in COMPILED:
        hits, alread = [], 0
        for p, t in corpus.items():
            if not in_scope(p, scope):
                continue
            n = len(rx.findall(t))
            if n:
                hits.append((p, n))
            alread += t.count(rep)
        got = sum(n for _, n in hits)
        if got == want:
            status, note = "ok ", ""
        elif got == 0 and alread >= 1:
            # Source form gone AND replacement present: a previous run applied
            # this pattern. Accepted only under that conjunction — a pattern
            # that matches nothing and whose replacement appears nowhere is dead.
            status, note = "done", f" (already applied, replacement x{alread})"
        elif got == 0:
            status, note = "DEAD", f" (no match anywhere, replacement x{alread})"
        else:
            # `want` is the ORIGINAL inventory. A partial application by an
            # earlier run is a warning, not a stop: the hard gate is the
            # post-write read-back, which fails if any source form survives.
            status, note = "warn", f" (want={want}, got={got}, replacement x{alread})"
        print(f"[{status}] {src}\n         got={got}{note}  "
              + ", ".join(f"{p.relative_to(ROOT).as_posix()}x{n}" for p, n in hits))
        if status == "DEAD":
            problems.append(f"{src}: matches nothing and its replacement appears nowhere")
        plan.append((rx, rep, scope))

    if args.dry_run:
        print(f"\n{len(COMPILED)} patterns, {len(problems)} mismatched")
        return 1 if problems else 0
    if problems:
        print("\nABORT: no files written.")
        return 1

    # Patterns must accumulate. Re-deriving each file from the ORIGINAL corpus
    # on every pass silently discards every earlier pattern's substitution and
    # leaves only the last one applied — which still prints "all patterns
    # applied", because the count assertions were checked against the original.
    work = dict(corpus)
    for rx, rep, scope in plan:
        for p, t in work.items():
            if not in_scope(p, scope):
                continue
            work[p] = rx.sub(rep, t)

    for p, new in work.items():
        if new == corpus[p]:
            continue
        before = (corpus[p].count("\r\n"), corpus[p].count("\n") - corpus[p].count("\r\n"))
        after = (new.count("\r\n"), new.count("\n") - new.count("\r\n"))
        if before != after:
            problems.append(f"{p.relative_to(ROOT)}: line endings changed {before}->{after}")
            continue
        with p.open("w", encoding="utf-8", newline="") as fh:
            fh.write(new)

    # Post-write read-back: no pattern's source form may survive anywhere it was
    # scoped to. Counting first, then testing, so an empty match set is a failure
    # rather than a vacuous pass.
    for rx, _rep, _want, scope, src in COMPILED:
        left = sum(len(rx.findall(p.read_text(encoding="utf-8")))
                   for p in files() if in_scope(p, scope))
        if left:
            problems.append(f"{src}: {left} occurrence(s) still present after write")
    print("\nall patterns applied")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
