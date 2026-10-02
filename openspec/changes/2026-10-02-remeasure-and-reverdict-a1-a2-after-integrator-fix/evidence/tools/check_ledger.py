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

VERDICTS = {"STILL_REAL", "PARTIALLY_REAL", "DOWNGRADED", "REMEASURED_SAME",
            "RESOLVED_BY_UPSTREAM", "NOT_REAL"}
KINDS = {"numeric", "coordinate", "provenance", "none"}
STATUSES = {"PENDING", "DONE"}
DERIV_STEPS = ("1_quantity", "2_chain", "3_line")
CODEREF = re.compile(r"(src|tests|openspec|wayfinder|scripts|\.audit)/[\w./-]+(:\d+)?")

# ---- D8: errata are pointers, never evidence
# Tokens that exist only because the errata recorded them: the pre-fix literals
# and the errata ids. A verdict_evidence that mentions one is fine ONLY if it
# also carries an independent anchor (a commit object or a recomputed value),
# because then the number was re-derived rather than copied.
ERRATA_TOKENS = ("1.1735482746999482", "1.0205068335735599", "1.1658482974306132",
                 "81.3148", "82.6036", "83.7313")
ERRATA_ID = re.compile(r"(?<![A-Za-z0-9])E(?:1[0-9]|[1-9])(?![0-9])")
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
    """D8: a verdict that leans on an errata token without its own anchor."""
    p = []
    a = e.get("ac_id", "<no ac_id>")
    ev = e.get("verdict_evidence")
    if not isinstance(ev, str) or not ev:
        return p
    hits = [t for t in ERRATA_TOKENS if t in ev]
    if hits and not INDEPENDENT_ANCHOR.search(ev):
        p.append(f"{a}: D8 -- verdict_evidence cites errata-only token(s) {hits} with no "
                 f"independent anchor (git show / recomputation); looks like transcription")
    if ERRATA_ID.search(ev) and not INDEPENDENT_ANCHOR.search(ev):
        p.append(f"{a}: D8 -- verdict_evidence references an errata id "
                 f"({ERRATA_ID.search(ev).group(0)}) with no independent anchor")
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
    return {"problems": problems, "outstanding": outstanding, "denominator": denom}



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

ALL_OK = all((t1_ok, t2_ok, t3_ok, t4_ok, t5_ok, t6_ok, t7_ok))
print("=" * 96)
print(f"CHECKER SELF-TEST: {'PASS' if ALL_OK else 'FAIL'}  (T1={t1_ok} T2={t2_ok} T3={t3_ok} "
      f"T4={t4_ok} T5={t5_ok} T6={t6_ok} T7={t7_ok})")
print("=" * 96)
sys.exit(0 if ALL_OK else 1)
