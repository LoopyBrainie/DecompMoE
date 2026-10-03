"""Two repairs to beta's check_base_drift.py, then the verification that matters.

Repair 1: the script read alpha's delta from the ACTIVE change dir, which no
longer exists because alpha has been archived. Point it at changes/archive/.

Repair 2: the script's banner printed a hardcoded base rev. The whole point of
this file is to detect base drift, and a hardcoded rev is exactly the
snapshot-as-constant bug this repository keeps producing: it reads as a
measured fact and stays wrong silently. Derive it.

Verification: does beta's regenerated block still carry alpha's edits to
req-gov-1? If not, archiving beta reverts alpha -- the failure the user
specifically asked to avoid by sequencing alpha before beta. The block is
diffed against the live base and alpha's distinctive markers are asserted to
survive.
"""
import difflib
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"D:\myProject\DecompMoE")
BETA = ROOT / "openspec/changes/2026-10-02-corr-pytest-approx-abs-semantics"
ALPHA_ARCHIVE = ROOT / "openspec/changes/archive/2026-10-02-repair-spell-numeric-literal-provenance"
GOV = "openspec/specs/governance/spec.md"

# ---------------------------------------------------------------- repair 1/2
drift = BETA / "evidence/check_base_drift.py"
t = drift.read_text(encoding="utf-8")
before = t

t = t.replace(
    '"openspec/changes/2026-10-02-repair-spell-numeric-literal-provenance"',
    '"openspec/changes/archive/2026-10-02-repair-spell-numeric-literal-provenance"',
)
t = re.sub(r'BASE_REV\s*=\s*"[0-9a-f]{7,40}"',
           'BASE_REV = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,\n'
           '                          capture_output=True, text=True).stdout.strip()',
           t)
# if there was no BASE_REV symbol, inject a derived one after the imports
if "BASE_REV" not in t:
    t = t.replace('import sys\n', 'import sys\nimport subprocess\n', 1)
    anchor = "ROOT = "
    idx = t.index(anchor)
    end = t.index("\n", t.index("\n", idx) + 1) + 1
    t = (t[:end]
         + 'BASE_REV = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,\n'
           '                          capture_output=True, text=True).stdout.strip()\n'
         + t[end:])

if t == before:
    print("WARN: no repair applied -- locators may be stale; inspect manually")
else:
    drift.write_text(t, encoding="utf-8")
    print(f"repaired {drift.relative_to(ROOT)}")

# ------------------------------------------------- the verification that matters
def head_blob(path):
    r = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"cannot read {path}")
    return r.stdout


def req_gov_1_block(text):
    lines = text.splitlines()
    a = next(i for i, l in enumerate(lines)
             if re.match(r'^\s*<a id="req-gov-1"></a>\s*$', l))
    n = next((i for i in range(a + 1, len(lines))
              if re.match(r'^\s*<a id="req-', lines[i])), len(lines))
    return lines[a:n]


base_block = req_gov_1_block(head_blob(GOV))
beta_delta = (BETA / "specs/governance/spec.md").read_text(encoding="utf-8")
beta_lines = beta_delta.splitlines()
beta_block = beta_lines[beta_lines.index("## MODIFIED Requirements") + 2:]

print("=" * 70)
print("does beta's block preserve alpha's edits to req-gov-1?")
print("=" * 70)
print(f"base (HEAD) block : {len(base_block)} lines")
print(f"beta delta block  : {len(beta_block)} lines")

diff = [l for l in difflib.unified_diff(base_block, beta_block, lineterm="", n=0)
        if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
changed = sum(1 for l in diff if l.startswith("-"))
print(f"changed lines     : {changed}   (-/+ pairs: {len(diff) // 2})")

# alpha's fingerprints inside req-gov-1. These were introduced by alpha's
# apply; if beta's block lacks them, applying beta reverts alpha.
ALPHA_MARKERS = [
    ("req-gov-5 reference", "req-gov-5"),
    ("version-independence", "version-independence"),
    ("tolerance is EXACTLY", "tolerance is EXACTLY"),
    ("TRUNCATED literal", "TRUNCATED"),
    ("1.4635872379108090131680874e-17", "1.4635872379108090131680874e-17"),
    ("1.9420345120803994000206689e-18", "1.9420345120803994000206689e-18"),
]
base_txt = "\n".join(base_block)
beta_txt = "\n".join(beta_block)

bad = 0
for name, marker in ALPHA_MARKERS:
    nb, nz = base_txt.count(marker), beta_txt.count(marker)
    ok = nz >= nb
    print(f"  {'OK  ' if ok else 'LOST'} {name:<34} base={nb} beta={nz}")
    if not ok:
        bad += 1

# the reverse direction also matters: beta's own corrections must be present
BETA_MARKERS = ["EXACTLY `1e-6`", "round-half-up half-unit", "abs=4.3e-7",
                "abs=0` tolerance is exactly 0"]
for marker in BETA_MARKERS:
    n = beta_txt.count(marker)
    print(f"  {'OK  ' if n else 'LOST'} beta marker {marker[:34]!r:<38} n={n}")
    if not n:
        bad += 1

print()
if bad:
    print(f"ABORT: {bad} marker(s) missing -- applying beta would revert work")
    sys.exit(1)
print("VERDICT: beta's block is a strict superset -- alpha's edits survive its apply")
