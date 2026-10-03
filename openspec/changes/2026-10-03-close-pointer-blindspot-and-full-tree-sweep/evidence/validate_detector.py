"""Validate pointer_scan.py BEFORE trusting any number it prints.

The previous change shipped a detector whose blind spot made it certify a
false green. This harness is the countermeasure: it asserts the detector
detects the class it claims to, and that it does not fire on the constructs
the spec deliberately allows.

Run:
    uv run --no-project python evidence/validate_detector.py

Exit 0 means the detector is fit to produce a census. Exit 1 means its
numbers must not be believed yet.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The detector lives in scripts/, not here: the gate and the census MUST
# be the same implementation. A private copy in a change directory is
# exactly how the two drifted apart the first time.
sys.path.insert(0, str(HERE.parents[3] / 'scripts'))

import pointer_scan as ps  # noqa: E402

FAILURES = []

#: The sites the previous change's detector could not see, at the baseline.
#: They are the regression: if the detector stops matching them, it has
#: re-acquired the original blind spot and its "zero" means nothing.
REPRO_SURVIVORS = [
    ("openspec/specs/governance/spec.md", 78),
    ("openspec/specs/governance/spec.md", 81),
    ("openspec/specs/decompmoe-skeleton/spec.md", 651),
    ("tests/test_schedule.py", 64),
    ("tests/test_schedule.py", 66),
    ("tests/test_sphere.py", 883),
]


def check(name, condition, detail=""):
    if condition:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s  %s" % (name, detail))
        FAILURES.append(name)


# ---------------------------------------------------------------------------
# 1. KNOWN POSITIVES — the class the old regex could not see.
# ---------------------------------------------------------------------------

POSITIVES = [
    # (label, line, expected kind)
    # (label, line, expected kind)
    ("wayfinder/spec.md L83, req-6:",
     "SEEDING has no gradient channel at all (wayfinder/spec.md L83, req-6: \"Spherical K-Means seeding\")",
     "path-space-L"),
    ("phase table pointer",
     "wayfinder/spec.md L617, req-27: `| 0 | K-Means seeding |",
     "path-space-L"),
    ("ticket L70+L74",
     "- **WHEN** `wayfinder/tickets/A8-2.md` L70 + L74 italic annotations are appended",
     "path-space-L"),
    ("audit path + L",
     "the `.audit/spec-math-audit.md` L524 edits do NOT require governance anchoring",
     "path-space-L"),
    ("long spec path + range",
     "`openspec/specs/decompmoe-skeleton/spec.md` L500-518 is read for the closed form",
     "path-space-L"),
    ("code line form",
     "implemented in `src/decompmoe/metrics.py:83` for the MCI row",
     "path-colon-line"),
    ("req-N L",
     "cycle-12 finding is about the MCI row in `wayfinder` spec.md L413 per req-20",
     "path-space-L"),
    ("bare capability L",
     "**Source:** `wayfinder/tickets/A4-1.md` (wayfinder L206)",
     "capability-L"),
    ("capital Spec L",
     "**Source:** `CLAUDE.md` \u00a73 (Spec L413 Reason)",
     "capability-L"),    ("reversed L then capability",
     "see L413 wayfinder for the Reason narrative",
     "L-then-capability"),
    ("req-gov-N at L",
     "the existing `req-gov-1` anchor at L7 unchanged",
     "capability-L"),
    ("Ticket id L",
     "cycle-12 finding 1 is specifically about Ticket A8-2 L70 + L74",
     "ticket-L"),
    ("Decision N L",
     "per change 2026-10-02 Decision 3 L412",
     "decision-L"),
    # "code" is itself a capability word, so this classifies as
    # capability-L rather than the weak word-line fallback. That is the
    # stronger classification and is what we want.
    ("word line (weak)",
     "The current code (L71-80) does the literal average",
     "capability-L"),
    ("bare 'line N' with no reference (weak)",
     "see line 495 for the helper",
     "word-line"),
    # Round 3: a bare ``:NNN`` whose path was named earlier on the line.
    # The skeleton spec cites three code ranges that way, so a detector that
    # only knows ``path:NNN`` loses the second and third.
    ("antecedent colon range",
     "returning `set()` at `src/decompmoe/safeguards.py:93-94` — and "
     "`safeguards.py:95-96`, or none (`:100-101`); those are not deferrals",
     "antecedent-colon-line"),
    # Round 4: a bare ticket id with no "Ticket" prefix, as audit-log prose
    # writes it.
    ("bare ticket id + L",
     "核对 (A5-3 L62 + spec L185)", "ticket-L"),
    # Round 5: a symbol reference plus a line locator.
    ("CamelCase symbol + L", "MVPConfig L51 docstring 自承", "symbol-L"),
    ("SCREAMING_CASE symbol + L",
     "see DEAD_EXPERT_CONSEC_STEPS L12 for the constant", "symbol-L"),
]

print("1. KNOWN POSITIVES (must be detected)")
for case in POSITIVES:
    label, payload = case[0], case[1]
    expect = case[2]
    sites = ps.scan_line("t.md", 1, payload)
    kinds = {s.kind for s in sites}
    check(label, expect in kinds, "got %s" % sorted(kinds))

# ---------------------------------------------------------------------------
# 2. KNOWN NEGATIVES — constructs the spec deliberately allows.
# ---------------------------------------------------------------------------

NEGATIVES = [
    ("block anchor id", "Requirement `` `#req-22` `` (\"Eight Metrics\")"),
    ("label not a line", "feedforward sublayer `L2-step2` then `L4-postmean`"),
    ("math L ratio", "the gate threshold is L/2 with L = 4 layers"),
    ("commit-ish", "amended by `bec147d` 2026-09-07 and `83a0503`"),
    ("phase boundary", "Phase boundaries (cumulative cutpoints): 1 K / 6 K / 26 K"),
    ("no locator", "req-20 has two block anchors, req-20-mci and req-20-source"),
    ("url fragment", "see https://example.com/docs#L42 for details"),
    ("ticket id only", "wayfinder/tickets/A8-2.md is the lineage ticket"),
    ("plain text", "line 1 of the docstring is a summary"),
    # Added after round 1 of this harness. A bare decimal number is a legal
    # hex string, so the commit-id marker was exempting the tail of floats
    # like 0.0350601609682665718.
    ("decimal float is not a pin commit id",
     "spec L122 数值差 0.0350601609682665718 verbatim", None),
    # ``Req 11: 4070 MVP hyperparameters`` introduces a quantity.
    ("Req N: quantity", "# MVPConfig field defaults (Req 11: 4070 MVP "
     "hyperparameters)", None),
    ("Req N: parameter count", "# Total / active parameter estimator "
     "(Req 11: 452M / 100M)", None),
    # Round 3: a colon-digit that is prose, not a locator. The antecedent
    # rule is anchored on a closing backtick precisely so this stays clean.
    ("colon-digit in prose",
     "at `src/decompmoe/x.py:12` the ratio a:1 divides b:2 by 3", None),
    # Round 5: a plain word before the locator is NOT a symbol reference.
    ("plain word + L is not a symbol pointer",
     "Phase L4 applies the guard", None),
]

print()
print("2. KNOWN NEGATIVES (must NOT be detected)")
for case in NEGATIVES:
    label, payload = case[0], case[1]
    expect = case[2] if len(case) > 2 else None
    sites = [s for s in ps.scan_line("t.md", 1, payload) if not s.weak]
    if expect is None:
        # For the round-2 additions the failure being guarded is the
        # EXEMPTION, not the detection: a decimal float must not act as a
        # historical marker and quietly hide the pointer.
        check(label, not any(s.historical for s in sites),
              "false exemption: %s" % [s.marker for s in sites])
    else:
        check(label, not sites, "false positive: %s" % [s.detail for s in sites])

# ---------------------------------------------------------------------------
# 3. SELF-EXEMPTION — the governance spec.md:78 failure mode.
# ---------------------------------------------------------------------------

print()
print("3. SELF-EXEMPTION (a quoted marker must not exempt its own line)")
SELF = (
    "- **WHEN** `wayfinder/tickets/A8-2.md` L70 + L74 italic "
    "`(historical, ..., superseded by spec req-20 L413 ...)` annotations "
    "are appended"
)
sites = ps.scan_line("g.md", 78, SELF)
check("detected", len(sites) > 0, "not detected at all")
check(
    "not exempt by the quoted `historical`",
    all(not s.historical for s in sites),
    "marker=%r" % [s.marker for s in sites],
)
REAL = "- per `wayfinder/spec.md` L413, before the change this was L412"
sites = ps.scan_line("g.md", 1, REAL)
check(
    "a genuine `before` marker DOES exempt",
    any(s.historical for s in sites),
    "over-corrected: genuine historical marker no longer exempts",
)

# ---------------------------------------------------------------------------
# 4. REGRESSION — the baseline tree must expose the known population.
# ---------------------------------------------------------------------------

print()
print("4. REGRESSION on the baseline tree (1526b98)")
BASE = Path(r"D:\tmp\a4fix\base1526b98")
if not BASE.exists():
    print("  SKIP  baseline worktree absent: %s" % BASE)
else:
    found = ps.scan(BASE)
    actionable = [s for s in found if not s.historical]
    strong = [s for s in actionable if not s.weak]
    files = {s.path for s in found}
    n = len(strong)
    print("  sites=%d actionable=%d (strong=%d weak=%d) historical=%d files=%d"
          % (len(found), len(actionable), n,
             len(actionable) - n, len(found) - len(actionable), len(files)))
    # Ground truth established by three independent means:
    #   - the shipped census classifier, replayed on this tree: 100 actionable
    #   - the previous independent recheck: 110/20/90/13 (wider scope)
    #   - the archived D1 record: 97 actionable (did not reproduce)
    # A detector that finds materially FEWER than 100 STRONG sites has the
    # same blind-spot class as the one it replaces. Weak sites ("line 495"
    # with no reference token) are reported but not counted as truth.
    check(
        "strong actionable >= 100 on baseline (old blind spot excluded)",
        n >= 100,
        "only %d - detector is still too narrow" % n,
    )
    check("baseline spans >= 14 files", len(files) >= 14,
          "only %d files" % len(files))
    # The named survivors must be detectable ON THE BASELINE. This assertion
    # is permanent: it is the regression that proves the detector sees the
    # class the previous change could not. It used to live in the live-tree
    # section, where it went red the moment the sweep landed and stopped
    # being a gate at all.
    #
    # The check is per FILE, not per line. Those line numbers were read off
    # the current tree; at 1526b98 the same numbers sit on different lines,
    # so a line-pinned assertion fails for a reason that has nothing to do
    # with the detector.
    base_files = {s.path for s in found}
    for rel, _ln in REPRO_SURVIVORS:
        check("baseline has pointer sites in %s" % rel, rel in base_files)

# ---------------------------------------------------------------------------
# 5. CURRENT TREE — asserts the POST-SWEEP state, and proves the gate is
#    not vacuous.
# ---------------------------------------------------------------------------

print()
print("5. CURRENT TREE post-sweep state")
LIVE = Path(r"D:\myProject\DecompMoE")
live = ps.scan(LIVE)
live_actionable = [s for s in live if not s.historical]
print("  sites=%d actionable=%d historical=%d files=%d"
      % (len(live), len(live_actionable), len(live) - len(live_actionable),
         len({s.path for s in live})))
have = {(s.path, s.line) for s in live}

# The sweep is done, so every named survivor must now be GONE.
for rel, ln in REPRO_SURVIVORS:
    check("swept: %s:%d absent" % (rel, ln), (rel, ln) not in have)

# The product tree must be exactly zero. This used to allow a known
# residue (the governance req-gov-2 Scenario heading) and it is now gone:
# the same fix table that sweeps the bodies reworded the heading, so the
# live spec is clean and the delta emits as a plain MODIFIED block.
check("product tree has zero actionable pointers",
      len(live_actionable) == 0,
      "unexpected: %s" % sorted({(s.path, s.line) for s in live_actionable}))

# Not vacuous: the detector must still find the whole class when the class
# is present. Asserting "zero" on a detector that has stopped matching
# anything is exactly how the previous change certified a false green.
probe = ps.scan_line("t.md", 1,
                     "SEEDING has no gradient at all (wayfinder/spec.md L83, "
                     "req-6: \"Spherical K-Means\")")
check("detector still matches the blind-spot form on synthetic input",
      len(probe) > 0, "detector has gone blind; a zero count is meaningless")

print()
if FAILURES:
    print("DETECTOR NOT FIT FOR USE: %d failure(s)" % len(FAILURES))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("DETECTOR FIT: all checks passed")
sys.exit(0)
