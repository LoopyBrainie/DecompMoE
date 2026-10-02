"""Change 3 / task 0.2 input + task 0.3 input -- which findings cite a number, and
which numbers are downstream of the quadrature?

Two outputs:
  1. for each of the 95 scoped findings: the numeric literals its body cites, and
     whether any of them equals a quadrature-chain quantity (oracle / impl /
     pre-fix / 6dp literal / cap-area / cva).
  2. the reverse index: which spec/src quantities route through
     `_betainc_regularized`.

This is D1 step 1 and 2 only. It deliberately does NOT decide `depends` -- the
derivation is per-item and lands in the ledger (0.3/0.4). It produces the
evidence each derivation must cite.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
EV = ROOT / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence"
SPHERE = ROOT / "src/decompmoe/sphere.py"

# ---- the quadrature chain: functions in sphere.py that call _betainc_regularized
src = SPHERE.read_text(encoding="utf-8")
funcs = re.findall(r"^def (\w+)\(", src, re.M)
callers = {}
for name in funcs:
    m = re.search(rf"^def {name}\(.*?(?=^def |\Z)", src, re.M | re.S)
    if m and "_betainc_regularized" in m.group(0):
        callers[name] = True
direct = "_betainc_regularized" in src
print("sphere.py public functions :", funcs)
print("call _betainc_regularized :", sorted(callers))
print()

# ---- known quadrature-chain numeric constants (measured; see evidence/)
QUAD_NUMBERS = {
    "1.1735474259197175": "oracle theta_voronoi(N_e=16,d_c=16)",
    "1.1735474259196821": "impl theta_voronoi(16,16) post-fix",
    "1.1735482746999482": "PRE-FIX impl theta_voronoi(16,16)",
    "1.1658476215516009": "oracle theta_voronoi(N_e=17,d_c=16)",
    "1.1658482974306132": "PRE-FIX impl theta_voronoi(17,16)",
    "1.0205068247837132": "oracle theta_voronoi(N_e=64,d_c=16)",
    "1.0205068335735599": "PRE-FIX impl theta_voronoi(64,16)",
    "1.0916065844205111": "oracle theta_voronoi(N_e=32,d_c=16)",
    "1.4578378442370083": "oracle theta_voronoi(N_e=3,d_c=16)",
    "1.4578378442369877": "impl theta_voronoi(3,16)",
    "1.173547": "6dp literal N_e=16",
    "1.165847": "6dp literal N_e=17",
    "1.020506": "6dp literal N_e=64",
    "1.5707963162581635": "cva(2,16) pi/2 plateau",
    "67.24": "theta_Voronoi(16,16) in degrees",
    "1.1735": "theta_Voronoi(16,16) rad, 4dp",
    "20.36": "theta_1/e in degrees",
}
# numbers that are NOT downstream of the quadrature -- control set
NON_QUAD = ["452", "100", "1024", "2048", "4096", "1.035", "0.1", "32"]

idx = json.loads((EV / "audit_index.json").read_text(encoding="utf-8"))
LIST = ROOT / idx["source"]
lines = LIST.read_text(encoding="utf-8").splitlines()

num_re = re.compile(r"\d+\.\d{4,}|\b\d{3,}\b")
rows = []
for b in idx["buckets"]:
    if b["label"] not in idx["scoped_buckets"]:
        continue
    for it in b["items"]:
        body = "\n".join(lines[it["line"] - 1: next(
            (j for j in range(it["line"], len(lines))
             if re.match(r"^###\s+(?:AC|UD)-\d+", lines[j]) or re.match(r"^##\s", lines[j])),
            len(lines))])
        cited = sorted(set(num_re.findall(body)))
        hits = {c: QUAD_NUMBERS[c] for c in cited if c in QUAD_NUMBERS}
        rows.append(dict(bucket=b["label"], ac_id=it["ac_id"], title=it["title"],
                         line=it["line"], cited=cited,
                         quad_chain_hits=hits,
                         mentions_betainc="_betainc_regularized" in body or
                                       "sphere.py" in body))

print(f"{'id':<7} {'bk':<4} {'quad?':<6} {'cited':<44} title")
print("-" * 130)
n_quad = 0
for r in rows:
    q = "YES" if r["quad_chain_hits"] else ("path" if r["mentions_betainc"] else "-")
    if r["quad_chain_hits"]:
        n_quad += 1
    cs = ",".join(r["cited"][:6])[:43]
    print(f"{r['ac_id']:<7} {r['bucket']:<4} {q:<6} {cs:<44} {r['title'][:38]}")
print()
print(f"scoped findings citing a KNOWN quadrature-chain number: {n_quad}/{len(rows)}")
print(f"scoped findings naming sphere.py or _betainc_regularized: "
      f"{sum(1 for r in rows if r['mentions_betainc'])}/{len(rows)}")

# Control: the matcher MUST find the known-present sample and must NOT fire on
# the known-absent sample. AC-74's finding text targets _betainc_regularized.
ac74 = next((r for r in rows if r["ac_id"] == "AC-74"), None)
print()
print("MATCHER CONTROL (task 0.2 verification)")
print(f"  known-PRESENT sample AC-74 mentions_betainc = "
      f"{ac74['mentions_betainc'] if ac74 else 'ABSENT FROM SCOPE'}  "
      f"-> {'OK' if ac74 and ac74['mentions_betainc'] else 'CONTROL FAILED'}")
ctrl = [r for r in rows if r["ac_id"] in ("AC-43", "AC-44", "AC-45")]
print(f"  known-ABSENT samples (A-3 loss/config items) mentions_betainc = "
      f"{[r['mentions_betainc'] for r in ctrl]}  "
      f"-> {'OK' if not any(r['mentions_betainc'] for r in ctrl) else 'CONTROL FAILED'}")

(EV / "quad_chain_scan.json").write_text(json.dumps(
    dict(quadrature_callers=sorted(callers), constants=QUAD_NUMBERS,
         control_non_quad=NON_QUAD, findings=rows),
    indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"\nwrote evidence/quad_chain_scan.json")
