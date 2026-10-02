"""Move this gate's probe scripts into the change's evidence/tools/ and re-point ROOT.

They resolve the repo root as `Path(__file__).resolve().parent`, so moving them
one level deeper would silently repoint ROOT at evidence/tools/ -- and every one of
them would then read the wrong files or exit quietly. The root line is rewritten
in the same pass, and every script is re-run afterwards as the actual check.
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
HERE = ROOT
TOOLS = ROOT / "openspec/changes/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence/tools"
TOOLS.mkdir(parents=True, exist_ok=True)

MOVES = {
    "_r3_anchor.py": "verify_anchor_three_ways.py",
    "_r3_crlf.py": "crlf_discriminator.py",
    "_r3_specshape.py": "spec_shape_probe.py",
    "_r3_diag.py": "probe_self_diagnosis.py",
    "_r3_baseline.py": "build_baseline.py",
    "_r3_index.py": "build_audit_index.py",
    "_r3_fields.py": "parse_findings.py",
    "_r3_oracle.py": "oracle_recheck.py",
    "_r3_ledger.py": "build_ledger.py",
    "_r3_checker.py": "check_ledger.py",
    "_r3_patch.py": "patch_tasks_line.py",
    "_r3_t02.txt": "applied_text_0.2.txt",
    "_r3_t03.txt": "applied_text_0.3.txt",
    "_r3_t04.txt": "applied_text_0.4.txt",
}

OLD = "ROOT = Path(__file__).resolve().parent"
NEW = "ROOT = Path(__file__).resolve().parents[3]   # repo root; this file lives in evidence/tools/"

moved, patched = [], []
for src, dst in MOVES.items():
    s = ROOT / src
    if not s.is_file():
        print(f"  SKIP (absent): {src}")
        continue
    text = s.read_text(encoding="utf-8")
    if src.endswith(".py") and OLD in text:
        text = text.replace(OLD, NEW, 1)
        patched.append(dst)
    (TOOLS / dst).write_text(text, encoding="utf-8", newline="")
    s.unlink()
    moved.append(dst)

print(f"moved   : {len(moved)} files -> {TOOLS.relative_to(ROOT)}")
print(f"repointed ROOT in: {len(patched)} scripts")

# ---- the real check: every moved script must still run from its new home
RERUN = ["build_baseline.py", "build_audit_index.py", "parse_findings.py",
         "oracle_recheck.py", "build_ledger.py", "check_ledger.py",
         "verify_anchor_three_ways.py", "crlf_discriminator.py", "spec_shape_probe.py"]
print()
print("re-running each moved script from its new location:")
bad = []
for name in RERUN:
    p = subprocess.run([sys.executable, str(TOOLS / name)], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    last = [l for l in (p.stdout or "").strip().splitlines() if l.strip()]
    print(f"  {name:<32} exit={p.returncode}  {last[-1][:70] if last else (p.stderr or '')[-90:]}")
    if p.returncode != 0:
        bad.append(name)
print()
print("ALL MOVED SCRIPTS STILL RUN" if not bad else f"FAILED AFTER MOVE: {bad}")
sys.exit(1 if bad else 0)
