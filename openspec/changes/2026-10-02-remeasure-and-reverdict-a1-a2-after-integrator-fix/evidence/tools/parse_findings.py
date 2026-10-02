"""Change 3 -- corrected field parse + COMPUTED quadrature-chain value set.

Three self-inflicted defects in the previous version, each of which would have
produced a confident wrong answer:

  1. Signature guessed. `canonical_voronoi_angle(n_e=..., d_c=...)` -> TypeError.
     Real signature (inspected, not assumed):
     `canonical_voronoi_angle(num_experts: int, signature_dim: int) -> float`.
  2. `_cap_area(pi/2, d_c)` returns exactly 0.5 -- that is the DOCUMENTED
     early-return plateau (`sin(pi/2)**2` is exactly 1.0 in float64, so the
     `x >= 1.0` branch fires). Feeding it pi/2 measures the plateau, not the
     quadrature. Exercise it with theta < pi/2.
  3. The decimal regex `\\d+\\.\\d+(?![\\w])` had a negative lookahead, which
     silently discarded EVERY scientific-notation number. That is how AC-09's
     `+1.1813e-6 / +1.1818e-6 / +1.3579e-2` -- the actual incomplete-Beta probe
     deltas -- went missing, and the scan then reported `0/95`.

The scan also ran over 问题/Requirement only; numbers live across the whole body.
"""
import inspect
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))   # repo root; this file lives in evidence/tools/
EV = ROOT / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence"
sys.path.insert(0, str(ROOT / "src"))

import mpmath as mp  # noqa: E402
mp.mp.dps = 60
from decompmoe import sphere  # noqa: E402

# --- signatures, inspected not assumed (and asserted so a rename cannot slip by)
SIGS = {n: str(inspect.signature(getattr(sphere, n)))
        for n in ("canonical_voronoi_angle", "voronoi_angle", "_cap_area",
                  "_cap_radius", "_betainc_regularized")}

# ------------------------------------------------- COMPUTED quadrature values
def computed():
    out = {}
    for n_e in (3, 16, 17, 32, 64):
        v = sphere.canonical_voronoi_angle(num_experts=n_e, signature_dim=16)
        out[f"canonical_voronoi_angle(num_experts={n_e}, signature_dim=16)"] = repr(v)
    # theta strictly below pi/2 so the `x >= 1.0` early return does NOT fire
    for theta, d_c in ((1.0, 16), (1.2, 16), (0.9, 16), (1.0, 2), (1.2, 64)):
        out[f"_cap_area(theta={theta}, signature_dim={d_c})"] = repr(
            sphere._cap_area(theta, d_c))
    out["_cap_area(theta=pi/2, signature_dim=16) [PLATEAU, not quadrature]"] = repr(
        sphere._cap_area(mp.pi / 2, 16))
    for x in (0.02, 0.5, 0.9, 0.999):
        out[f"_betainc_regularized(x={x}, a=7.5, b=0.5)"] = repr(
            sphere._betainc_regularized(x, 7.5, 0.5))
    return out


COMPUTED = computed()

# ------------------------------------------------------------------ parse
idx = json.loads((EV / "audit_index.json").read_text(encoding="utf-8"))
LIST = ROOT / idx["source"]
lines = LIST.read_text(encoding="utf-8").splitlines()

FIELD = re.compile(r"^-\s+\*\*(.+?)\*\*[：:]\s*(.*)$")
# scientific notation INCLUDED, and no trailing-word guard
NUM = re.compile(r"(?<![\w.])(\d+\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)(?![\w.])")
LINE_REF = re.compile(r"\bL\d+|\.py:\d+|\.md:\d+|\b行\s?\d+")

findings = []
for b in idx["buckets"]:
    if b["label"] not in idx["scoped_buckets"]:
        continue
    for k, it in enumerate(b["items"]):
        start = it["line"] - 1
        stop = (b["items"][k + 1]["line"] - 1 if k + 1 < len(b["items"])
                else next((j for j in range(start, len(lines)) if re.match(r"^##\s", lines[j])),
                          len(lines)))
        body = lines[start:stop]
        f = dict(ac_id=it["ac_id"], bucket=b["label"], title=it["title"], line=it["line"])
        for ln in body:
            m = FIELD.match(ln)
            if m:
                f.setdefault(m.group(1), m.group(2).strip())
        # numbers from the WHOLE body, minus explicit line references
        scrub = LINE_REF.sub(" ", "\n".join(body))
        f["numbers"] = sorted(set(NUM.findall(scrub)))
        loc = f.get("位置", "")
        m = re.match(r"`?([\w/.\-]+\.(?:py|md))(?::(\d+))?", loc)
        f["location_file"] = m.group(1) if m else None
        f["location_line"] = int(m.group(2)) if (m and m.group(2)) else None
        flat = " ".join(str(v) for v in f.values())
        f["mentions_sphere"] = bool(re.search(
            r"sphere\.py|canonical_voronoi_angle|voronoi_angle|_betainc_regularized|"
            r"_cap_area|不完全\s*Beta|beta\s*积分|Betainc|voronoi", flat, re.I))
        findings.append(f)

# ----------------------------------------------------------------- reporting
print("SIGNATURES (inspected)")
for k, v in SIGS.items():
    print(f"  {k}{v}")
print()
print("COMPUTED quadrature-chain values at HEAD")
for k, v in COMPUTED.items():
    print(f"  {k:<62} {v}")
print()

ac09 = next(f for f in findings if f["ac_id"] == "AC-09")
ac74 = next(f for f in findings if f["ac_id"] == "AC-74")
ac44 = next(f for f in findings if f["ac_id"] == "AC-44")
ac09_pre = set(ac09["numbers"]) >= {"1.1813e-6", "1.1818e-6", "1.3579e-2"}
print("MATCHER CONTROL -- the previous run FAILED this; it must pass now")
print(f"  known-PRESENT AC-09 finds 1.1813e-6/1.1818e-6/1.3579e-2 : {ac09_pre}  "
      f"{'OK' if ac09_pre else 'STILL BROKEN'}")
print(f"  known-PRESENT AC-09 numbers = {ac09['numbers']}")
print(f"  known-PRESENT AC-09 mentions_sphere = {ac09['mentions_sphere']}  "
      f"{'OK' if ac09['mentions_sphere'] else 'CONTROL FAILED'}")
print(f"  known-PRESENT AC-74 mentions_sphere = {ac74['mentions_sphere']}  "
      f"{'OK' if ac74['mentions_sphere'] else 'CONTROL FAILED'}")
print(f"  known-ABSENT  AC-44 mentions_sphere = {ac44['mentions_sphere']}  "
      f"{'OK' if not ac44['mentions_sphere'] else 'CONTROL FAILED'}")
print()
n = sum(1 for f in findings if f["mentions_sphere"])
print(f"findings naming the quadrature path : {n}/{len(findings)}")
print(f"findings whose 位置 is a sphere file : "
      f"{sorted({f['location_file'] for f in findings if f['location_file'] and 'sphere' in f['location_file']})}")
allnums = [x for f in findings for x in f["numbers"]]
print(f"distinct numeric literals across bodies: {len(set(allnums))}  "
      f"(was 83 with scientific notation dropped)")

(EV / "audit_findings.json").write_text(json.dumps(
    dict(signatures=SIGS, computed_quad_chain=COMPUTED, findings=findings),
    indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("\nwrote evidence/audit_findings.json")
