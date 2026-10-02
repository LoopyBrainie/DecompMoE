"""Repoint ROOT in the moved tools by SELF-LOCATION, not by counting parents.

`parents[N]` was wrong twice already: the correct index for
openspec/changes/<name>/evidence/tools/<file>.py is 5, not 3. Worse, with the
wrong root the tools did not fail loudly -- verify_anchor_three_ways.py exited 0
while printing CONTROL FAILED, because it was comparing the wrong files and the
comparison happened to be self-consistent.

So: walk up until the directory actually looks like the repository root, and
assert the anchors that make it unambiguous (.git AND .audit AND pyproject.toml).
A probe pointed at the wrong tree is the failure mode this whole exercise is about.
"""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
HERE = ROOT
TOOLS = HERE / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence/tools"

MARKERS = (".git", ".audit", "pyproject.toml")
NEW = ('ROOT = next(p for p in Path(__file__).resolve().parents '
       'if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))')

print(f"tool dir: {TOOLS.relative_to(HERE)}")
print(f"  repo root            = {HERE}")
print(f"  TOOLS.parents[3]     = {TOOLS.parents[3]}   <-- what the first move used")
print(f"  TOOLS.parents[4]     = {TOOLS.parents[4]}   <-- the correct one")
print("  (a file inside tools/ has parents[0] == tools, so the directory index and")
print("   the file index are off by one -- which is how '3' came out)")
assert all((TOOLS.parents[4] / m).exists() for m in MARKERS), "parents[4] is not the repo root"
print()

patched = 0
for p in sorted(TOOLS.glob("*.py")):
    t = p.read_text(encoding="utf-8")
    if "ROOT = next(p for p in Path(__file__).resolve().parents" in t:
        continue
    if "ROOT = Path(__file__).resolve().parents[3]" not in t:
        print(f"  skip (no ROOT line to repoint): {p.name}")
        continue
    p.write_text(t.replace("ROOT = Path(__file__).resolve().parents[3]", NEW), encoding="utf-8", newline="")
    patched += 1
print(f"repointed {patched} scripts by self-location")
print()

RERUN = ["build_baseline.py", "build_audit_index.py", "parse_findings.py",
         "oracle_recheck.py", "build_ledger.py", "check_ledger.py",
         "verify_anchor_three_ways.py", "crlf_discriminator.py", "spec_shape_probe.py"]
print("re-running from the new location (a clean run must ALSO print OK, not just exit 0):")
bad = []
for name in RERUN:
    r = subprocess.run([sys.executable, str(TOOLS / name)], cwd=HERE,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = r.stdout or ""
    bad_words = [w for w in ("CONTROL FAILED", "STILL BROKEN", "FAILED", "DISAGREE",
                             "Traceback", "ABORT") if w in out]
    last = [l for l in out.strip().splitlines() if l.strip()]
    status = "OK" if (r.returncode == 0 and not bad_words) else f"SUSPECT {bad_words}"
    print(f"  {name:<30} exit={r.returncode} {status:<18} {last[-1][:52] if last else ''}")
    if r.returncode != 0 or bad_words:
        bad.append(name)
print()
print("ALL TOOLS RUN CLEAN FROM THEIR NEW HOME" if not bad else f"STILL BROKEN: {bad}")
sys.exit(1 if bad else 0)
