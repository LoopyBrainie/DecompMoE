"""Validate `pointer_scan.py` BEFORE trusting any number it prints.

This file is a GATE (`scripts/lint_*.py`, discovered by `run_gates.py` by
glob). That placement is the whole point, and it is what the previous home
got wrong three ways at once:

  * it lived in a change's `evidence/` directory and derived the detector
    path as ``HERE.parents[3] / "scripts"``. Archiving the change moved the
    file, that resolved to ``openspec/scripts``, and the harness died with
    ``ModuleNotFoundError`` -- after the commit that delivered it;
  * no gate ran it, so nothing noticed;
  * its baseline section materialised a tree at a HARDCODED absolute path
    and printed ``SKIP`` when the path was absent, so the one check that
    proved the detector is not vacuous at scale quietly stopped running and
    the gate stayed green either way.

Here the repo root is derived from ``__file__`` (so the file is
position-independent), the baseline is read straight out of the object store
by revision (so there is no path to go missing), and an absent baseline is a
FAILURE rather than a skip.

Exit 0 means the detector is fit to produce a census. Exit 1 means its
numbers must not be believed yet.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import pointer_scan as ps  # noqa: E402

#: The tree the first sweep started from. It must still expose the class the
#: ORIGINAL detector could not see; a detector that finds materially fewer
#: strong sites than this has the same blind spot as the one it replaces.
BASELINE_REV = "1526b98"
BASELINE_MIN_STRONG = 100

BT = "`"

FAILURES: list[str] = []
CHECKS = 0


def check(name, condition, detail=""):
    global CHECKS
    CHECKS += 1
    if condition:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s  %s" % (name, detail))
        FAILURES.append(name)


# ---------------------------------------------------------------------------
# 1. KNOWN POSITIVES -- the class the original regex could not see.
# ---------------------------------------------------------------------------

POSITIVES = [
    ("wayfinder/spec.md L83, req-6:",
     'SEEDING has no gradient channel at all (wayfinder/spec.md L83, req-6: '
     '"Spherical K-Means seeding")', "path-space-L"),
    ("phase table pointer",
     "wayfinder/spec.md L617, req-27: `| 0 | K-Means seeding |", "path-space-L"),
    ("ticket L70+L74",
     "- **WHEN** " + BT + "wayfinder/tickets/A8-2.md" + BT
     + " L70 + L74 italic annotations are appended", "path-space-L"),
    ("audit path + L",
     "the " + BT + ".audit/spec-math-audit.md" + BT
     + " L524 edits do NOT require governance anchoring", "path-space-L"),
    ("long spec path + range",
     BT + "openspec/specs/decompmoe-skeleton/spec.md" + BT
     + " L500-518 is read for the closed form", "path-space-L"),
    ("code line form",
     "implemented in " + BT + "src/decompmoe/metrics.py:83" + BT
     + " for the MCI row", "path-colon-line"),
    ("req-N L",
     "cycle-12 finding is about the MCI row in " + BT + "wayfinder" + BT
     + " spec.md L413 per req-20", "path-space-L"),
    ("bare capability L",
     "**Source:** " + BT + "wayfinder/tickets/A4-1.md" + BT
     + " (wayfinder L206)", "capability-L"),
    ("capital Spec L",
     "**Source:** " + BT + "CLAUDE.md" + BT + " \u00a73 (Spec L413 Reason)",
     "capability-L"),
    ("reversed L then capability",
     "see L413 wayfinder for the Reason narrative", "L-then-capability"),
    ("req-gov-N at L",
     "the existing " + BT + "req-gov-1" + BT + " anchor at L7 unchanged",
     "capability-L"),
    ("Ticket id L",
     "cycle-12 finding 1 is specifically about Ticket A8-2 L70 + L74",
     "ticket-L"),
    ("Decision N L",
     "per change 2026-10-02 Decision 3 L412", "decision-L"),
    ("word line (weak)",
     "The current code (L71-80) does the literal average", "capability-L"),
    ("bare 'line N' with no reference (weak)",
     "see line 495 for the helper", "word-line"),
    ("antecedent colon range",
     "returning " + BT + "set()" + BT + " at " + BT
     + "src/decompmoe/safeguards.py:93-94" + BT + " \u2014 and " + BT
     + "safeguards.py:95-96" + BT + ", or none (" + BT + ":100-101" + BT
     + "); those are not deferrals", "antecedent-colon-line"),
    ("bare ticket id + L",
     "\u6838\u5bf9 (A5-3 L62 + spec L185)", "ticket-L"),
    ("CamelCase symbol + L",
     "MVPConfig L51 docstring \u81ea\u627f", "symbol-L"),
    ("SCREAMING_CASE symbol + L",
     "see DEAD_EXPERT_CONSEC_STEPS L12 for the constant", "symbol-L"),
]

print("1. KNOWN POSITIVES (must be detected)")
for label, payload, expect in POSITIVES:
    kinds = {s.kind for s in ps.scan_line("t.md", 1, payload)}
    check(label, expect in kinds, "got %s" % sorted(kinds))

# ---------------------------------------------------------------------------
# 2. KNOWN NEGATIVES -- constructs the spec deliberately allows.
# ---------------------------------------------------------------------------

NEGATIVES = [
    ("block anchor id",
     "Requirement " + BT + BT + " `#req-22` " + BT + BT
     + ' ("Eight Metrics")'),
    ("label not a line",
     "feedforward sublayer " + BT + "L2-step2" + BT + " then " + BT
     + "L4-postmean" + BT),
    ("math L ratio", "the gate threshold is L/2 with L = 4 layers"),
    ("commit-ish", "amended by " + BT + "bec147d" + BT + " 2026-09-07 and "
                   + BT + "83a0503" + BT),
    ("phase boundary",
     "Phase boundaries (cumulative cutpoints): 1 K / 6 K / 26 K"),
    ("no locator",
     "req-20 has two block anchors, req-20-mci and req-20-source"),
    ("url fragment", "see https://example.com/docs#L42 for details"),
    ("ticket id only", "wayfinder/tickets/A8-2.md is the lineage ticket"),
    ("plain text", "line 1 of the docstring is a summary"),
    ("decimal float is not a pin commit id",
     "spec L122 \u6570\u503c\u5dee 0.0350601609682665718 verbatim", None),
    ("Req N: quantity",
     "# MVPConfig field defaults (Req 11: 4070 MVP hyperparameters)", None),
    ("Req N: parameter count",
     "# Total / active parameter estimator (Req 11: 452M / 100M)", None),
    ("colon-digit in prose",
     "at " + BT + "src/decompmoe/x.py:12" + BT
     + " the ratio a:1 divides b:2 by 3", None),
    ("plain word + L is not a symbol pointer",
     "Phase L4 applies the guard", None),
    # Round 3: ``history`` is a technical NOUN, not a past-state claim. The
    # old ``\bhistor\w*`` accepted it, so a pointer to the CURRENT ``UR``
    # docstring exempted itself on the word "history stacked".
    ("technical noun 'history' does not exempt",
     "is called with (e.g. " + BT + "(100, N_e)" + BT + " history stacked by "
     + BT + "metrics.UR" + BT + " per " + BT
     + "src/decompmoe/metrics.py:83" + BT + ")", None),
]

print()
print("2. KNOWN NEGATIVES (must NOT be detected)")
for case in NEGATIVES:
    label, payload = case[0], case[1]
    expect = case[2] if len(case) > 2 else None
    sites = [s for s in ps.scan_line("t.md", 1, payload) if not s.weak]
    if expect is None:
        check(label, not any(s.historical for s in sites),
              "false exemption: %s" % [s.marker for s in sites])
    else:
        check(label, not sites, "false positive: %s" % [s.detail for s in sites])

# ---------------------------------------------------------------------------
# 3. EXEMPTION SEMANTICS. Every one of these is a defect the detector has
#    actually shipped, in a form that a green gate did not catch.
# ---------------------------------------------------------------------------

print()
print("3. EXEMPTION SEMANTICS")

# 3a. A token in backticks is a quotation, not a claim about the line.
SELF = ("- **WHEN** " + BT + "wayfinder/tickets/A8-2.md" + BT
        + " L70 + L74 italic " + BT + "(historical, ..., superseded by spec "
        "req-20 L413 ...)" + BT + " annotations are appended")
sites = ps.scan_line("g.md", 78, SELF)
check("3a detected", len(sites) > 0, "not detected at all")
check("3a quoted marker does not exempt",
      all(not s.historical for s in sites),
      "marker=%r" % [s.marker for s in sites])

# 3b. A DOUBLE-backtick span contributes four backticks, so a parity count
#     put its contents OUTSIDE a code span. That is how the word
#     ``historical`` inside a quoted annotation example came to hide a live
#     pointer 84 lines out of date.
DQUOTE = ("- **AND** the canonical live example is " + BT
          + "openspec/specs/wayfinder/spec.md" + BT
          + " L251: " + BT + BT + "**Source:** " + BT
          + "wayfinder/tickets/A6a-2.md" + BT
          + " (historical, threshold " + BT + "1/128" + BT + ")" + BT + BT
          + " the paren annotation uses bare " + BT + "1/128" + BT)
sites = ps.scan_line("w.md", 898, DQUOTE)
check("3b detected", len(sites) > 0, "not detected at all")
check("3b marker inside a double-backtick span does not exempt",
      all(not s.historical for s in sites),
      "marker=%r" % [s.marker for s in sites])

# 3c. Exemption is per LOCATOR, not per line. A marker buried in one clause
#     of a 2000-character Source field used to exempt every other locator on
#     that line, including ones naming the current state of current files.
FAR = ("**Source:** " + BT + "CLAUDE.md" + BT
       + " \u00a73; " + BT + "wayfinder/tickets/A6a-2.md" + BT
       + " historical \u539f " + BT + "f_i^avg < 1/128" + BT
       + " vs spec, the boundary now uses " + BT
       + "src/decompmoe/safeguards.py:34-36" + BT)
sites = ps.scan_line("c.md", 94, FAR)
check("3c a marker 200+ chars away does not exempt",
      any(not s.historical for s in sites),
      "over-exempted: %s" % [(s.detail, s.marker) for s in sites])

# 3d. ...but a marker ADJACENT to the locator still exempts it.
NEAR = "- per " + BT + "wayfinder/spec.md" + BT + " L413, before the change"
check("3d adjacent `before` still exempts",
      any(s.historical for s in ps.scan_line("g.md", 1, NEAR)),
      "over-corrected: a genuine historical marker no longer exempts")

# 3e. The repository's own canonical annotation is split by a semicolon.
#     Treating ``;`` as a clause boundary cut the marker off from the very
#     locator it annotates and reported nine historical annotations as live.
ANNOT = ("- \u03bb_j = C \u5206\u5e03\u534f\u65b9\u5dee  "
         + "*(historical, centered-covariance reading; superseded by spec "
         "req-20 L453 uncentered second moment via " + BT
         + "fix-openspec-doc-bugs" + BT + " design.md Decision 8)*")
check("3e the locator introduced by `superseded by` is NOT exempt",
      any(not s.historical for s in ps.scan_line("a.md", 70, ANNOT)),
      "the `by` complement names the CURRENT text; no marker may exempt it")
# ...and the semicolon must not be the reason. A locator the marker really
# does annotate, on a line that also carries a semicolon, still exempts.
ANNOT2 = ("- \u03bb_j = C \u5206\u5e03\u534f\u65b9\u5dee  "
          + "*(historical, ticket reading at " + BT
          + "wayfinder/tickets/A8-2.md" + BT + " L70; superseded by "
          + BT + "fix-openspec-doc-bugs" + BT + " design.md Decision 8)*")
check("3e' a genuine historical locator on a semicolon line still exempts",
      any(s.historical for s in ps.scan_line("a.md", 70, ANNOT2)),
      "over-corrected: the ticket's own stale pointer stopped being exempt")

# 3f. The window bounds where a marker may START, and is read with a tail so
#     a marker at the edge is recognised whole. Truncating first turned
#     ``**pre-edit**`` into ``**pre``, which no pattern can match.
EDGE = ("> **Note**: The " + BT + "LOOPS.md" + BT
        + " line ranges (L64-69, L118-122) reference **pre-edit** positions; "
        "post this change the sections shift")
check("3f a marker at the window edge is recognised whole",
      any(s.historical for s in ps.scan_line("g.md", 135, EDGE)),
      "the window sliced the marker in half")

# 3g. A pin commit is a structured token, and backticks around it are
#     formatting rather than quotation.
PIN = "signature mirrors " + BT + "src/decompmoe/safeguards.py:71-80" + BT \
      + " at commit " + BT + "d3689a1" + BT
check("3g `at commit <pin>` exempts even inside backticks",
      any(s.historical for s in ps.scan_line("s.md", 261, PIN)),
      "a pinned locator was reported as live")

# ---------------------------------------------------------------------------
# 4. REGRESSION on the baseline tree, read from git objects.
# ---------------------------------------------------------------------------

print()
print("4. REGRESSION on baseline %s" % BASELINE_REV)
try:
    found = ps.scan_commit(REPO, BASELINE_REV)
except Exception as exc:                      # noqa: BLE001
    # An unreadable baseline is a FAILURE. The previous harness printed SKIP
    # and exited 0, which is how a missing directory turned into a green gate.
    found = []
    check("baseline %s is readable" % BASELINE_REV, False, repr(exc))
else:
    check("baseline %s is readable" % BASELINE_REV, True)

# An EMPTY baseline is not a pass either. `if found:` used to wrap every
# substantive check below, so a `scan_commit` that returned [] -- meaning "the
# detector found nothing at 224 sites of scale" -- exited 0 and reported a
# clean run with six checks silently missing. The gate has to be able to tell
# "found 224 sites" from "found 0".
check("baseline scan returned a non-empty population",
      len(found) > 0,
      "scan_commit returned %d sites -- the scale check would be vacuous"
      % len(found))

if found:
    actionable = [s for s in found if not s.historical]
    strong = [s for s in actionable if not s.weak]
    files = {s.path for s in found}
    print("  sites=%d actionable=%d (strong=%d weak=%d) historical=%d files=%d"
          % (len(found), len(actionable), len(strong),
             len(actionable) - len(strong),
             len(found) - len(actionable), len(files)))
    check("strong actionable >= %d on baseline" % BASELINE_MIN_STRONG,
          len(strong) >= BASELINE_MIN_STRONG,
          "only %d - the detector is too narrow" % len(strong))
    check("baseline spans >= 14 files", len(files) >= 14,
          "only %d files" % len(files))
    for rel in ("openspec/specs/governance/spec.md",
                "openspec/specs/decompmoe-skeleton/spec.md",
                "openspec/specs/wayfinder/spec.md", "CLAUDE.md"):
        check("baseline has sites in %s" % rel, rel in files)

# ---------------------------------------------------------------------------
# 5. CURRENT TREE -- asserts the post-sweep state, and proves the gate is
#    not vacuous.
# ---------------------------------------------------------------------------

print()
print("5. CURRENT TREE post-sweep state")
live = ps.scan(REPO)
live_actionable = [s for s in live if not s.historical]
print("  sites=%d actionable=%d historical=%d files=%d"
      % (len(live), len(live_actionable),
         len(live) - len(live_actionable), len({s.path for s in live})))
check("product tree has zero actionable pointers",
      len(live_actionable) == 0,
      "unexpected: %s"
      % sorted({(s.path, s.line, s.detail) for s in live_actionable}))

# Not vacuous: a zero on a detector that has stopped matching anything is
# exactly how the previous change certified a false green. Assert the count
# is what we expect BEFORE trusting the zero, and probe the blind-spot form.
check("detector still finds the blind-spot form on synthetic input",
      len(ps.scan_line("t.md", 1,
                       "SEEDING has no gradient at all (wayfinder/spec.md L83, "
                       "req-6: \"Spherical K-Means\")")) > 0,
      "detector has gone blind; a zero count is meaningless")
check("detector still finds the file-level population",
      len(live) > 0,
      "zero sites on the live tree -- the scan is not looking at the tree")

# The sweep rewrote `openspec/specs/**` in place. A delta is emitted from the
# swept text, so an unapplied or half-applied sweep would show up here as a
# live pointer rather than as a validate error.
for rel in ("openspec/specs/wayfinder/spec.md",
            "openspec/specs/decompmoe-skeleton/spec.md",
            "openspec/specs/governance/spec.md"):
    txt = (REPO / rel.replace("/", "\\")).read_text(encoding="utf-8")
    per_line = []
    for n, line in enumerate(txt.splitlines(), 1):
        per_line.extend(
            (n, s.detail) for s in ps.scan_line(rel, n, line) if not s.historical)
    check("no actionable pointer in %s" % rel, not per_line, str(per_line[:5]))

# ---------------------------------------------------------------------------
# 6. POPULATION SCOPE. The census and the grammar must agree on what is
#    scannable, and the gate has to be the thing that says so.
#
#    The list used to be sliced with ``EXT[3:-2]``, which turns the last
#    alternative ``ini`` into ``in``: the census globbed a file type that does
#    not exist. A pytest test caught it, but the GATE did not -- so a gate
#    green did not mean the scope was right.
# ---------------------------------------------------------------------------

print()
print("6. POPULATION SCOPE")
canonical = tuple(ps.EXT.removeprefix("(?:").removesuffix(")").split("|"))
check("EXT_EXTENSIONS is derived from EXT, not sliced out of it",
      ps.EXT_EXTENSIONS == canonical,
      "%r != %r" % (ps.EXT_EXTENSIONS, canonical))
check("every EXT alternative survives the derivation",
      "ini" in ps.EXT_EXTENSIONS and "in" not in ps.EXT_EXTENSIONS,
      "the last alternative was truncated: %r" % (ps.EXT_EXTENSIONS,))
scope_files = ps.tracked_files(REPO)
check("census population is substantial", len(scope_files) >= 50,
      "only %d files in scope" % len(scope_files))
# The composition matters more than the total: 594 of 682 tracked files of
# these extensions live under openspec/changes/archive/ and are excluded by
# design, so "80 in scope" is the correct number and a >500 bound would be
# asserting an exclusion away.
non_mdpy = [f for f in scope_files if not f.endswith((".md", ".py"))]
check("non-md/py files are actually in scope", len(non_mdpy) >= 1,
      "no non-md/py file reached the census -- the extension derivation is "
      "not taking effect (%d of %d in scope)"
      % (len(non_mdpy), len(scope_files)))
yaml_in_scope = [f for f in scope_files if f.endswith((".yaml", ".yml"))]
check("a tracked .yaml reached the census", bool(yaml_in_scope),
      "no .yaml file reached the census")

# F3: the composition checks above all pass when a WHOLE DIRECTORY is added to
# the exclusion list. `and not f.startswith("wayfinder/tickets/")` in
# `in_scope` took the census from 80 files to 56, the baseline from 24 to 18,
# and left this gate at exit 0 with all 64 checks green and pytest green --
# while the round-4 sweep had just edited six ticket files, and the zero this
# gate certifies is computed over exactly that population. A total cannot
# catch a subtraction; named files can.
PINNED_IN_SCOPE = (
    "CLAUDE.md",
    "openspec/specs/wayfinder/spec.md",
    "openspec/specs/decompmoe-skeleton/spec.md",
    "openspec/specs/governance/spec.md",
    "wayfinder/tickets/A1-1.md",
    "wayfinder/tickets/A4-1.md",
    "wayfinder/tickets/A5-3.md",
    "wayfinder/tickets/A6a-2.md",
    "wayfinder/tickets/A6b-1.md",
    "wayfinder/tickets/A8-2.md",
    "LOOPS.md",
    "src/decompmoe/safeguards.py",
    "src/decompmoe/metrics.py",
    "src/decompmoe/gating.py",
    "tests/test_safeguards.py",
)
pinned_set = set(scope_files)
for rel in PINNED_IN_SCOPE:
    check("pinned in scope: %s" % rel, rel in pinned_set,
          "a file the census is supposed to cover fell out of scope")

# ...and the other direction: the detector and its own guard tests must stay
# OUT, or the census reports the fixtures it uses as live pointers.
for rel in ("scripts/pointer_scan.py", "scripts/lint_no_line_pointers.py",
            "scripts/lint_pointer_detector.py", "tests/test_pointer_scan.py"):
    check("pinned OUT of scope: %s" % rel, rel not in pinned_set,
          "a self-referential tool entered the census")

# The run itself must not be short. A gate that silently executes fewer checks
# than it has -- because a branch went untaken -- is the same class of vacuity
# as the empty baseline above.
#
# This bound is a TRIPWIRE, not a proof, and the previous value was not even a
# tripwire: at 45, deleting the six checks inside `if found:` left 58 and
# stayed green. At 80 the same deletion leaves 77 and is caught. Losing a whole
# section (10 checks in section 3, 18 in section 1) is caught comfortably; a
# single missing check is not, and no count-based bound can catch that. The
# guard that actually carries the weight is the unbracketed `len(found) > 0`
# above, which cannot be tuned away from its own purpose.
MIN_CHECKS = 80
check("at least %d checks executed" % MIN_CHECKS, CHECKS >= MIN_CHECKS,
      "only %d checks ran; a section was skipped" % CHECKS)

print()
print("checks executed: %d" % CHECKS)
if FAILURES:
    print("DETECTOR NOT FIT FOR USE: %d failure(s)" % len(FAILURES))
    for f in FAILURES:
        print("  - %s" % f)
    sys.exit(1)
print("DETECTOR FIT: all checks passed")
sys.exit(0)
