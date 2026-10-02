"""Change 3 / task 0.4 -- the structural checker for the ledger.

Enforces design.md D1 (three-step dependency derivation must be complete) and D2
(a non-dependent finding must still carry a written basis -- silent omission must
be indistinguishable from "judged and excluded", so silence is not an option).

THE CHECKER IS ITSELF THE THING UNDER TEST. A checker that has never been shown
to fail will pass everything and tell you the ledger is complete. So:

  T1  a deliberately broken entry must be reported, with the right reason
  T2  every OTHER entry in that fixture must stay clean -- a checker that flags
      everything is as useless as one that flags nothing
  T3  on the real 95-entry skeleton it must report "missing" for all 95 and
      invent no other category of complaint

Run: python _r3_checker.py          (exit 0 only if all three tests pass)
"""
import copy
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
EV = ROOT / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence"
LEDGER = EV / "ledger.json"

# Single source of truth for the partition (risk R-a: several call sites used to
# hardcode 95, which is exactly how a scope change goes unnoticed).
EXPECT_TOTAL = 104
EXPECT_IN_SOURCE = 95
EXPECT_UNREGISTERED = 9

# D3's five values, exactly. `NOT_REAL` used to sit in this set while appearing
# nowhere in D3 -- a value the checker would accept that the design never
# sanctioned. Conversely `MOVED` (the audit's own word for a coordinate shift)
# is deliberately absent: D3 rejects it, so an A-4 row carried over from the
# audit's own wording must be re-decided on this change's terms.
VERDICTS = {"STILL_REAL", "PARTIALLY_REAL", "DOWNGRADED", "REMEASURED_SAME",
            "RESOLVED_BY_UPSTREAM"}
KINDS = {"numeric", "coordinate", "provenance", "none"}
STATUSES = {"PENDING", "DONE"}
DERIV_STEPS = ("1_quantity", "2_chain", "3_line")
CODEREF = re.compile(r"(src|tests|openspec|wayfinder|scripts|\.audit)/[\w./-]+(:\d+)?")

# ---- H2: the in-source id set must come from the audit source, not from a count
# `denominator` used to compare only counts (104 / 95 / 9). A count cannot tell
# "the right 95" from "95 of something else": swapping every in-source ac_id for
# a fabricated AC-9xx kept all three counts and still reported a clean ledger.
# The set difference now lives here, not only in build_ledger.py, because
# build_ledger.py writes the artefact it would be checking.
SCOPED = {"A-1", "A-2", "A-3", "A-4", "A-5", "A-7"}
SRC_LIST = ROOT / ".audit/wayfinder-opsx-code-review/lists/opsx-changes.md"
BUCKET_RE = re.compile(r"^##\s+(A-\d)\b")
HEADING_RE = re.compile(r"^###\s+((?:AC|UD)-\d+)")


def source_id_sets():
    """(the 95 in-source ids, every id the source uses) read straight from the
    audit list. Returns (None, None) when the source is not present -- `.audit`
    is gitignored, so a clean clone legitimately has none. Callers must treat
    that as UNVERIFIABLE, never as a pass."""
    if not SRC_LIST.is_file():
        return None, None
    cur, in_scope, every = None, set(), set()
    for ln in SRC_LIST.read_text(encoding="utf-8").splitlines():
        b = BUCKET_RE.match(ln)
        if b:
            cur = b.group(1)
            continue
        m = HEADING_RE.match(ln)
        if m and cur:
            every.add(m.group(1))
            if cur in SCOPED:
                in_scope.add(m.group(1))
    return in_scope, every


# ---- D8: errata are pointers, never evidence
# Tokens that exist only because the errata recorded them: the pre-fix literals
# and the errata ids. A verdict_evidence that mentions one is fine ONLY if it
# also carries an independent anchor (a commit object or a recomputed value),
# because then the number was re-derived rather than copied.
ERRATA_TOKENS = ("1.1735482746999482", "1.0205068335735599", "1.1658482974306132",
                 "81.3148", "82.6036", "83.7313")
# H4: was `E(?:1[0-9]|[1-9])`, which matches E1..E19 and silently misses E20 --
# even though tasks 2.3 names E1..E20 explicitly and errata_index registers an
# E20. One erratum could therefore be cited as a verdict with no anchor.
ERRATA_ID = re.compile(r"(?<![A-Za-z0-9])E\d{1,2}(?![0-9])")
INDEPENDENT_ANCHOR = re.compile(r"git\s+show|git\s+grep|@HEAD|@6593a06|pytest|实测|复算|"
                                r"mp\.quad|betainc|approximation|resid")


def _x_issues(e):
    """D9: an `X-` entry must be registered as unregistered, and when DONE must
    carry a coordinate that `git show` can reach."""
    p = []
    a = e.get("ac_id", "<no ac_id>")
    if not a.startswith("X-"):
        return p
    if e.get("in_source_as_heading") is not False:
        p.append(f"{a}: X- entry must set in_source_as_heading=false (it is a blind-spot "
                 f"table row, not a `###` heading)")
    if (e.get("provenance") or {}).get("source_ref") is None:
        p.append(f"{a}: X- entry must cite provenance.source_ref (the blind-spot table row)")
    if e.get("status") == "DONE":
        refs = (e.get("dependency") or {}).get("code_refs") or []
        if not any(CODEREF.search(str(r)) for r in (refs if isinstance(refs, list) else [refs])):
            p.append(f"{a}: D9 -- DONE requires a code_ref built from zero; the blind-spot "
                     f"table supplies no pin coordinate to inherit")
    return p


def _errata_evidence_issues(e):
    """D8: a verdict that leans on an errata token without its own anchor.

    H3: this used to read `verdict_evidence` only. But tasks 1.2 REQUIRES
    `remeasurement.old` to be quoted verbatim from the audit body -- which is
    precisely where the pre-fix literals live. So the field the process compels
    us to fill by transcription was the one field D8 never looked at. Both
    fields are scanned now, and the message names which one tripped.
    """
    p = []
    a = e.get("ac_id", "<no ac_id>")
    rm = e.get("remeasurement") if isinstance(e.get("remeasurement"), dict) else {}
    # Anchor scoping is per-field, not pooled across the entry. Pooling was
    # tried and it silently gutted the rule: a well-anchored `method` would
    # launder an unanchored claim in `verdict_evidence`.
    #   verdict_evidence  -> must carry its own anchor; it IS the argument.
    #   remeasurement.old -> may be anchored by its sibling `method`, because
    #     tasks 1.2 compels `old` to be a verbatim audit quote and the
    #     recomputation is by construction recorded in `method`.
    fields = [
        ("verdict_evidence", e.get("verdict_evidence"), e.get("verdict_evidence")),
        ("remeasurement.old", rm.get("old"),
         " ".join(str(x) for x in (rm.get("method"), rm.get("new")) if x)),
    ]

    for fname, val, anchor_src in fields:
        if not isinstance(val, str) or not val:
            continue
        anchor_src = anchor_src if isinstance(anchor_src, str) else ""
        hits = [t for t in ERRATA_TOKENS if t in val]
        if hits and not INDEPENDENT_ANCHOR.search(anchor_src):
            p.append(f"{a}: D8 -- {fname} cites errata-only token(s) {hits} with no "
                     f"independent anchor (git show / recomputation); looks like transcription")
        m = ERRATA_ID.search(val)
        if m and not INDEPENDENT_ANCHOR.search(anchor_src):
            p.append(f"{a}: D8 -- {fname} references an errata id "
                     f"({m.group(0)}) with no independent anchor")
    return p


def check_entry(e, registered_x=frozenset()):
    """Return a list of problem strings. Empty list == entry is structurally sound."""
    p = []
    a = e.get("ac_id", "<no ac_id>")

    if e.get("status") not in STATUSES:
        p.append(f"{a}: status {e.get('status')!r} not in {sorted(STATUSES)}")
    if e.get("status") == "PENDING":
        # a skeleton entry is legitimately empty; the only thing it may not do is
        # half-fill -- e.g. set depends but leave the derivation blank
        dep = e.get("dependency", {})
        if dep.get("depends") is not None and not dep.get("derivation"):
            p.append(f"{a}: half-filled -- depends={dep.get('depends')!r} but derivation is empty")
        if (e.get("invalidation_kind") is not None
                and e.get("invalidation_kind") not in KINDS):
            p.append(f"{a}: invalidation_kind {e.get('invalidation_kind')!r} not in {sorted(KINDS)}")
        if e.get("verdict_new") is not None:
            p.append(f"{a}: verdict_new set while status is PENDING")
        return p

    # ---- status DONE: everything must be present
    dep = e.get("dependency") or {}
    depends = dep.get("depends")
    if depends is None:
        p.append(f"{a}: status DONE but dependency.depends is null -- "
                 f"D2 forbids silence; write true or false with a basis")
    d = dep.get("derivation")
    if not d:
        p.append(f"{a}: D1 -- dependency.derivation is empty")
    else:
        if isinstance(d, str):
            missing = [s for s in DERIV_STEPS if s not in d]
            if missing:
                p.append(f"{a}: D1 -- derivation missing step(s) {missing}")
        elif isinstance(d, dict):
            for s in DERIV_STEPS:
                if not d.get(s):
                    p.append(f"{a}: D1 -- derivation step {s} empty")
    refs = dep.get("code_refs")
    if not refs:
        p.append(f"{a}: D1 step 3 -- code_refs empty (which line?)")
    elif not any(CODEREF.search(str(r)) for r in (refs if isinstance(refs, list) else [refs])):
        p.append(f"{a}: D1 step 3 -- code_refs has no file:line-shaped reference")

    if depends is True:
        rm = e.get("remeasurement") or {}
        for k in ("old", "new", "method"):
            if rm.get(k) in (None, ""):
                p.append(f"{a}: depends=True but remeasurement.{k} is empty")
    # D2: depends=False must still justify itself
    if depends is False and not (d or dep.get("code_refs")):
        p.append(f"{a}: D2 -- depends=False with no written basis "
                 f"(silence is indistinguishable from a missing judgement)")

    if e.get("invalidation_kind") not in KINDS:
        p.append(f"{a}: invalidation_kind {e.get('invalidation_kind')!r} not in {sorted(KINDS)}")
    if e.get("verdict_new") not in VERDICTS:
        p.append(f"{a}: verdict_new {e.get('verdict_new')!r} not in {sorted(VERDICTS)}")
    if not e.get("verdict_evidence"):
        p.append(f"{a}: verdict_evidence empty (D3 requires a basis for every verdict)")
    # D8 / D9 apply to DONE entries
    p += _errata_evidence_issues(e)
    p += _x_issues(e)
    if a.startswith("X-") and registered_x and a not in registered_x:
        p.append(f"{a}: not registered in evidence/errata_index.json as an unregistered "
                 f"finding -- an X- id with no blind-spot row is an invented item")
    return p


def check(entries):
    """Three SEPARATE reports, because conflating them is the dangerous bug.

    `problems`     -- structural defects. An entry with none is well-formed.
    `outstanding`  -- entries still at status PENDING.
    `denominator`  -- the 104 / 95+9 partition (rule R-a: the count must be read
                      from one place, not hardcoded at several call sites).

    A PENDING skeleton has ZERO structural problems. If `check` returned only
    `problems`, then "104 entries still to do" and "104 entries complete" would
    print identically -- a checker that certifies an unfinished ledger as clean.
    That is the failure mode this function exists to prevent, so completion is
    reported in its own channel and gated on separately.
    """
    registered_x = frozenset()
    ei = EV / "errata_index.json"
    if ei.is_file():
        data = json.loads(ei.read_text(encoding="utf-8"))
        registered_x = frozenset(e["ac_id"] for e in
                                 data["unregistered_findings"]["entries"])

    problems, outstanding = {}, []
    for e in entries:
        probs = check_entry(e, registered_x)
        if probs:
            problems[e.get("ac_id", "<no ac_id>")] = probs
        if e.get("status") == "PENDING":
            outstanding.append(e.get("ac_id", "<no ac_id>"))

    ids = [e.get("ac_id") for e in entries]
    in_src = [i for i in ids if not str(i).startswith("X-")]
    out_src = [i for i in ids if str(i).startswith("X-")]
    denom = {
        "total": len(entries),
        "expected_total": EXPECT_TOTAL,
        "in_source": len(in_src),
        "expected_in_source": EXPECT_IN_SOURCE,
        "unregistered": len(out_src),
        "expected_unregistered": EXPECT_UNREGISTERED,
        "registered_unregistered_available": bool(registered_x),
        "unregistered_not_registered": sorted(set(out_src) - set(registered_x)),
        "namespace_overlap": sorted(set(in_src) & set(out_src)),
        "duplicate_ids": sorted({i for i in ids if ids.count(i) > 1}),
    }
    denom["ok"] = (denom["total"] == EXPECT_TOTAL
                   and denom["in_source"] == EXPECT_IN_SOURCE
                   and denom["unregistered"] == EXPECT_UNREGISTERED
                   and not denom["duplicate_ids"]
                   and not denom["namespace_overlap"]
                   and not denom["unregistered_not_registered"])

    # ---- H2: scope, as its own channel -----------------------------------
    # A count is not a set. This is the check that makes tasks 7.2(a) and 7.2(b)
    # executable against the committed ledger, with no write path involved.
    # UNVERIFIABLE is a third state on purpose: `.audit` is gitignored, so a
    # clean clone has no source to diff against, and silently returning True
    # there would recreate the exact hole this closes.
    src_in_scope, src_every = source_id_sets()
    if src_in_scope is None:
        scope = {"reference": "UNAVAILABLE (.audit is gitignored)",
                 "expected_in_source": None, "ok": None,
                 "missing_from_ledger": [], "unexpected_in_ledger": [],
                 "x_ids_present_in_source": []}
    else:
        missing = sorted(src_in_scope - set(in_src))
        unexpected = sorted(set(in_src) - src_in_scope)
        # 7.2(b): an X- row is a blind-spot table row, never a `###` heading.
        x_in_source = sorted(set(out_src) & src_every)
        scope = {"reference": str(SRC_LIST.relative_to(ROOT)),
                 "expected_in_source": len(src_in_scope),
                 "ok": not missing and not unexpected and not x_in_source,
                 "missing_from_ledger": missing,
                 "unexpected_in_ledger": unexpected,
                 "x_ids_present_in_source": x_in_source}
    return {"problems": problems, "outstanding": outstanding,
            "denominator": denom, "scope": scope}



# =============================================================== T1 / T2
GOOD = {
    "ac_id": "AC-XX", "bucket": "A-1", "title": "t", "status": "DONE",
    "dependency": {"depends": True,
                   "derivation": {"1_quantity": "theta_voronoi(16,16)",
                                  "2_chain": "canonical_voronoi_angle -> _betainc_regularized",
                                  "3_line": "src/decompmoe/sphere.py:285"},
                   "code_refs": ["src/decompmoe/sphere.py:285"]},
    "invalidation_kind": "numeric",
    "remeasurement": {"old": "1.1735482746999482", "new": "1.173547425919682", "method": "oracle@HEAD"},
    "verdict_old": "STILL_REAL", "verdict_new": "REMEASURED_SAME", "verdict_evidence": "dev 3.55e-14",
}

BAD_CASES = {
    "half_filled_depends": ({**GOOD, "status": "PENDING",
                             "dependency": {"depends": True, "derivation": None,
                                            "code_refs": None}}, "half-filled"),
    "silence_D2": ({**GOOD, "dependency": {"depends": None, "derivation": None, "code_refs": None}},
                   "D2 forbids silence"),
    "depends_true_no_remeasure": ({**GOOD, "remeasurement": {"old": None, "new": None, "method": None}},
                                  "remeasurement.old is empty"),
    "depends_false_no_basis": ({**GOOD, "dependency": {"depends": False, "derivation": None,
                                                      "code_refs": None}}, "D2"),
    "no_code_refs": ({**GOOD, "dependency": {**GOOD["dependency"], "code_refs": []}},
                     "code_refs empty"),
    "derivation_missing_step": ({**GOOD, "dependency": {**GOOD["dependency"],
                                                       "derivation": {"1_quantity": "q", "2_chain": "c"}}},
                                "derivation step 3_line empty"),
    "bad_kind": ({**GOOD, "invalidation_kind": "numeric-ish"}, "not in"),
    "bad_verdict": ({**GOOD, "verdict_new": "PROBABLY_REAL"}, "not in"),
    "no_evidence": ({**GOOD, "verdict_evidence": ""}, "verdict_evidence empty"),
    "pending_with_verdict": ({**GOOD, "status": "PENDING", "verdict_new": "STILL_REAL"},
                             "verdict_new set while status is PENDING"),
}

print("=" * 96)
print("T1  a deliberately broken entry must be caught, with the right reason")
print("=" * 96)
t1_ok = True
for name, (entry, expect) in BAD_CASES.items():
    probs = check_entry(entry)
    hit = any(expect in s for s in probs)
    t1_ok &= hit
    print(f"  {name:<26} {'CAUGHT' if probs else 'MISSED':<7} "
          f"{'OK' if hit else 'CONTROL FAILED  <-- expected a message containing %r' % expect}")
    for s in probs:
        print(f"        {s}")

print()
print("  sanity: the well-formed entry must produce NO complaint")
good_probs = check_entry(GOOD)
t1_ok &= not good_probs
print(f"    {'OK' if not good_probs else 'FALSE POSITIVE: ' + str(good_probs)}")

print()
print("=" * 96)
print("T2  a checker that flags everything is as useless as one that flags nothing")
print("=" * 96)
real = json.loads(LEDGER.read_text(encoding="utf-8"))["entries"]
clean = [copy.deepcopy(e) for e in real[:5]]
for e in clean:
    e.update({k: v for k, v in GOOD.items() if k not in ("ac_id", "title")})
    e["ac_id"] = e["ac_id"] + "-CLEAN"
fixture = clean[:4] + [copy.deepcopy(BAD_CASES["no_code_refs"][0])]
fixture[-1]["ac_id"] = "AC-BAD"
res = check(fixture)
t2_ok = set(res["problems"]) == {"AC-BAD"} and res["outstanding"] == []
print(f"  5-entry fixture, 1 broken -> problems flagged: {sorted(res['problems'])}, "
      f"outstanding: {len(res['outstanding'])}")
print(f"  {'OK' if t2_ok else 'CONTROL FAILED -- expected exactly {AC-BAD} and no outstanding'}")

print()
print("=" * 96)
print("T3  on the real 104-entry ledger: OUTSTANDING is tracked and separate, zero structural problems")
print("=" * 96)
r95 = check(real)
res95, out95 = r95["problems"], r95["outstanding"]
n_p3 = sum(1 for e in real if e["status"] == "PENDING")
# The invariant is "outstanding tracks PENDING exactly, and is reported on its own
# channel", NOT "every entry is PENDING". The old form asserted len(out)==len(real),
# which is a pristine-fixture coincidence that breaks the moment a single bucket is
# legitimately adjudicated -- i.e. it made the control unrunnable as soon as the
# change started doing its job. `n_p3 > 0` keeps the original teeth: a ledger with
# no work left must fail here rather than read as closed.
print(f"  entries at status PENDING   : {n_p3}/{len(real)}")
print(f"  reported OUTSTANDING        : {len(out95)}   "
      f"{'OK' if len(out95) == n_p3 and n_p3 > 0 else 'CONTROL FAILED -- a PENDING ledger must not read as clean'}")
print(f"  structural problems         : {len(res95)}   "
      f"{'OK (a partially-adjudicated ledger is well-formed, not complete)' if not res95 else res95}")
# "every complaint is a PENDING/half-fill notice" only has content when there IS a
# complaint. Guard the branch instead of writing `bool(res95) and ...`, which is
# False on an empty dict -- and would report a vacuous truth as a failed control.
if res95:
    vac = all(all("PENDING" in s or "half-filled" in s for s in v) for v in res95.values())
    vac_note = f"checked against {len(res95)} complaint(s)"
else:
    vac = True
    vac_note = "no complaints to check -- vacuously satisfied, and separately 0 complaints"
print(f"  {vac_note}")
t3_ok = (len(out95) == n_p3) and (n_p3 > 0) and not res95 and vac

print()
print("=" * 96)
print("T4  a fully-populated ledger must read CLEAN *and* COMPLETE (no false alarm)")
print("=" * 96)
full = []
for e in real:
    x = copy.deepcopy(e)
    x.update({k: v for k, v in GOOD.items() if k not in ("ac_id", "title", "in_source_as_heading")})
    full.append(x)
rf = check(full)
t4_ok = not rf["problems"] and not rf["outstanding"] and rf["denominator"]["ok"]
print(f"  {len(real)} well-formed DONE entries -> problems {len(rf['problems'])}, "
      f"outstanding {len(rf['outstanding'])}, denominator {rf['denominator']['ok']}")
print(f"  {'OK' if t4_ok else 'CONTROL FAILED -- the checker would never let the change close'}")

print()
print("=" * 96)
print("T5  D8 -- a verdict transcribed from the errata must be caught")
print("=" * 96)
TRANSCRIBED = {**GOOD, "ac_id": "AC-TRANSCRIBED",
               "verdict_evidence": "E13 says the 6dp literal is guarded; see 1.1735482746999482"}
REDERIVED = {**GOOD, "ac_id": "AC-REDERIVED",
             "verdict_evidence": ("git show 6593a06:src/decompmoe/sphere.py 取到修前值 "
                                  "1.1735482746999482；当前 HEAD 复算为 1.173547425919682")}
t5a, t5b = check_entry(TRANSCRIBED), check_entry(REDERIVED)
t5_ok = any("D8" in s for s in t5a) and not any("D8" in s for s in t5b)
print(f"  transcribed verdict  -> {'CAUGHT' if any('D8' in s for s in t5a) else 'MISSED'}  OK")
for s in t5a:
    print(f"        {s}")
print(f"  re-derived verdict   -> {'false alarm' if any('D8' in s for s in t5b) else 'OK (not flagged)'}")

print()
print("=" * 96)
print("T6  D9 -- an X- entry without a blind-spot row, or without its own locus, is caught")
print("=" * 96)
X_GOOD = {**GOOD, "ac_id": "X-D1-02", "in_source_as_heading": False,
          "provenance": {"source_ref": ".audit/.../opsx-changes.md:1426"}}
X_NO_ROW = {**X_GOOD, "ac_id": "X-INVENTED"}
X_NO_LOCUS = {**X_GOOD, "dependency": {**GOOD["dependency"], "code_refs": []}}
# The registration rule needs the real set. Calling check_entry() with the default
# empty `registered_x` would skip the rule entirely and the test would pass for
# the wrong reason -- a control that cannot fail is not a control.
_ei = json.loads((EV / "errata_index.json").read_text(encoding="utf-8"))
REG_X = frozenset(e["ac_id"] for e in _ei["unregistered_findings"]["entries"])
t6a = check_entry(X_GOOD, REG_X)
t6b = check_entry(X_NO_ROW, REG_X)
t6c = check_entry(X_NO_LOCUS, REG_X)
t6_ok = (not t6a) and any("not registered" in s for s in t6b) and any("from zero" in s for s in t6c)
print(f"  registered set available: {len(REG_X)} ids  "
      f"{'OK' if REG_X else 'CONTROL FAILED -- errata_index.json not readable'}")
print(f"  registered X- entry      -> {'false alarm' if t6a else 'OK (not flagged)'}")
print(f"  X- with no blind-spot row-> {'CAUGHT' if any('not registered' in s for s in t6b) else 'MISSED'}")
for s in t6b:
    print(f"        {s}")
print(f"  X- DONE without a locus  -> {'CAUGHT' if any('from zero' in s for s in t6c) else 'MISSED'}")
for s in t6c:
    print(f"        {s}")

print()
print("=" * 96)
print("T7  the 104/95+9 partition is a checked invariant, not a comment")
print("=" * 96)
d = r95["denominator"]
print(f"  total {d['total']} (expect {d['expected_total']})   in-source "
      f"{d['in_source']} (expect {d['expected_in_source']})   unregistered "
      f"{d['unregistered']} (expect {d['expected_unregistered']})")
print(f"  duplicates {d['duplicate_ids']}   overlap {d['namespace_overlap']}   "
      f"unregistered-but-unregistered {d['unregistered_not_registered']}")
short = check(real[:-1])["denominator"]
added = check(real + [copy.deepcopy(real[0])])["denominator"]
t7_ok = d["ok"] and not short["ok"] and not added["ok"]
print(f"  dropping one entry breaks it : {not short['ok']}   "
      f"duplicating one breaks it: {not added['ok']}   "
      f"{'OK' if t7_ok else 'CONTROL FAILED -- the partition is not actually enforced'}")

print()
print("=" * 96)
print("T8  H2 -- a ledger of FABRICATED ac_ids must be caught, not certified")
print("=" * 96)
# This is the review's decisive experiment, promoted to a standing control.
# It used to pass: swapping every in-source id for a fake one left all three
# counts untouched, so `denominator` reported ok=True on an invented ledger.
# The mutation is the whole in-source namespace, not one row, because a
# single-row swap is also caught and would prove less.
_src, _every = source_id_sets()
fabricated = []
for i, e in enumerate(real, 1):
    x = copy.deepcopy(e)
    if str(x.get("ac_id", "")).startswith("X-"):
        fabricated.append(x)
    else:
        x["ac_id"] = f"AC-9{i:02d}"
        fabricated.append(x)
rfab = check(fabricated)
_counts_intact = (rfab["denominator"]["total"] == EXPECT_TOTAL
                  and rfab["denominator"]["in_source"] == EXPECT_IN_SOURCE
                  and rfab["denominator"]["unregistered"] == EXPECT_UNREGISTERED)
_scope_sees_it = rfab["scope"]["ok"] is False
t8_ok = _scope_sees_it and _counts_intact
print(f"  {len([e for e in fabricated if not str(e['ac_id']).startswith('X-')])} in-source ids "
      f"replaced by fabricated AC-9xx")
print(f"  counts still read 104/95+9 (the hole this test exists for) : {_counts_intact}")
print(f"  scope channel verdict on the fabricated ledger            : {rfab['scope']['ok']}")
print(f"  first unexpected ids : {rfab['scope']['unexpected_in_ledger'][:6]}")
if _src is None:
    print("  CONTEXT: .audit absent -> scope is UNVERIFIABLE here, so T8 cannot pass. "
          "That is the third state working as designed, not a failure of the check.")
    t8_ok = None
print(f"  {'OK -- fabricated ids are rejected' if t8_ok else 'CONTROL FAILED' if t8_ok is False else 'N/A'}")

print()
print("=" * 96)
print("T9  H4 -- E20 must be inside the D8 errata-id matcher (it was E1..E19 only)")
print("=" * 96)
_covered = {e: bool(ERRATA_ID.search(e)) for e in ("E1", "E9", "E10", "E19", "E20", "E21")}
t9_ok = all(_covered[k] for k in ("E1", "E9", "E10", "E19", "E20"))
E20_TRANSCRIBED = {**GOOD, "ac_id": "AC-E20",
                   "verdict_evidence": "per E20 the d_c=2 deviation is 7.017798e-15",
                   # GOOD carries method="oracle@HEAD", which is itself a valid
                   # anchor for remeasurement.old -- but not for verdict_evidence.
                   # Leaving it would have tested nothing, so neutralise it.
                   "remeasurement": {"old": "n/a", "new": "n/a", "method": "n/a"}}
t9b = check_entry(E20_TRANSCRIBED)
t9_ok = t9_ok and any("D8" in s and "E20" in s for s in t9b)
print(f"  matcher coverage : {_covered}")
print(f"  E20-only citation -> {'CAUGHT' if any('D8' in s for s in t9b) else 'MISSED'}")
for s in t9b:
    print(f"        {s}")
print(f"  {'OK' if t9_ok else 'CONTROL FAILED -- E20 can be cited with no anchor'}")

print()
print("=" * 96)
print("T10  H3 -- remeasurement.old is the field tasks 1.2 compels us to transcribe, "
      "so D8 must scan it")
print("=" * 96)
OLD_TRANSCRIBED = {**GOOD, "ac_id": "AC-OLD",
                   "verdict_evidence": "see 1.1735482746999482",
                   "remeasurement": {"old": "1.1735482746999482",
                                     "new": "n/a", "method": "n/a"}}
ANCHORED = {**GOOD, "ac_id": "AC-OLD-OK",
            "verdict_evidence": "recounted below",
            "remeasurement": {"old": "1.1735482746999482",
                              "new": "1.173547425919682",
                              "method": "复算: mp.quad at 50 dps reproduces 1.173547425919682"}}
t10a, t10b = check_entry(OLD_TRANSCRIBED), check_entry(ANCHORED)
t10_ok = any("remeasurement.old" in s for s in t10a) and not t10b
print(f"  transcription in .old, no anchor -> "
      f"{'CAUGHT' if any('remeasurement.old' in s for s in t10a) else 'MISSED'}")
for s in t10a:
    print(f"        {s}")
print(f"  .old quoted but recomputed in .method -> "
      f"{'false alarm' if t10b else 'OK (not flagged)'}")
print(f"  {'OK' if t10_ok else 'CONTROL FAILED -- the transcription field is unscanned'}")

ALL_OK = all((t1_ok, t2_ok, t3_ok, t4_ok, t5_ok, t6_ok, t7_ok, t9_ok, t10_ok)) \
    and t8_ok is not False
print("=" * 96)
print(f"CHECKER SELF-TEST: {'PASS' if ALL_OK else 'FAIL'}  (T1={t1_ok} T2={t2_ok} T3={t3_ok} "
      f"T4={t4_ok} T5={t5_ok} T6={t6_ok} T7={t7_ok} T8={t8_ok} T9={t9_ok} T10={t10_ok})")
print("=" * 96)

# ---- the real ledger, through the same four channels ------------------------
rr = check(real)
sc = rr["scope"]
print()
print("=" * 96)
print("REAL LEDGER")
print("=" * 96)
print(f"  problems    {len(rr['problems'])}")
for k, v in rr["problems"].items():
    for s in v:
        print(f"        {s}")
print(f"  outstanding {len(rr['outstanding'])} entries still PENDING")
print(f"  denominator ok={rr['denominator']['ok']}  "
      f"({rr['denominator']['total']} = {rr['denominator']['in_source']} + "
      f"{rr['denominator']['unregistered']})")
print(f"  scope       reference={sc['reference']}  ok={sc['ok']}")
print(f"        expected in-source {sc['expected_in_source']}   "
      f"missing {len(sc['missing_from_ledger'])}   "
      f"unexpected {len(sc['unexpected_in_ledger'])}   "
      f"X- in source {len(sc['x_ids_present_in_source'])}")
if sc["unexpected_in_ledger"]:
    print(f"        UNEXPECTED (invented ids): {sc['unexpected_in_ledger'][:20]}")
if sc["missing_from_ledger"]:
    print(f"        MISSING: {sc['missing_from_ledger'][:20]}")
# An unverifiable scope must not be laundered into a pass by the exit code.
sys.exit(0 if (ALL_OK and not rr["problems"] and rr["denominator"]["ok"]
               and sc["ok"] is not False) else 1)
