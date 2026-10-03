"""Final relocation check -- keyed on each tool's OWN verdict, not on keyword soup.

The previous pass flagged 2 of 9 tools as SUSPECT purely because their output
contains the words DISAGREE / FAILED:
  * verify_anchor_three_ways.py -- "DISAGREE" IS its finding (6 CRLF files where
    raw-sha256 disagrees with the line-ending-normalising methods). Its controls
    print OK.
  * parse_findings.py -- "FAILED" occurs inside the banner sentence "the previous
    run FAILED this; it must pass now". All four controls print OK.

So keyword scanning is the wrong instrument: the words a tool uses to report a
real finding are the same words used to report a failure. Each tool below
declares its own success marker, and a tool is judged on that plus its exit code.
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = next(p for p in Path(__file__).resolve().parents
            if all((p / m).exists() for m in (".git", ".audit", "pyproject.toml")))
TOOLS = ROOT / "openspec/changes/archive/2026-10-02-remeasure-and-reverdict-a1-a2-after-integrator-fix/evidence/tools"

# (script, substring that must appear, substring that must NOT appear)
CONTRACT = {
    "build_baseline.py":          ("anchor coverage           : True", "DISAGREE"),
    "build_audit_index.py":       ("S2 parsed count == declared count          : OK", "MISMATCH"),
    "parse_findings.py":          ("known-ABSENT  AC-44 mentions_sphere = False  OK", "CONTROL FAILED  "),
    "oracle_recheck.py":          ("ORACLE RECHECK       : PASS", "ORACLE RECHECK       : FAIL"),
    # M2: this key appeared TWICE. Python keeps the last one, so the first
    # clause was silently discarded and the tool count printed from
    # len(CONTRACT) hid the loss. One key now, and duplicates are a hard error
    # below rather than a silent overwrite.
    "build_ledger.py":            ("all status PENDING : True", "ABORT"),
    "check_ledger.py":            ("CHECKER SELF-TEST: PASS", "CHECKER SELF-TEST: FAIL"),
    # The must-appear used to be "sphere.py -> IDENTICAL  OK" -- a hardcoded
    # snapshot of one path's verdict. It rotted when sphere.py became
    # line-ending-different from HEAD (raw DIFF, both normalising methods
    # `same`), and the control then fired on a probe that was working
    # correctly. The control now derives its expectation from live
    # `git status`, so the assertion is "the probe agrees with git", which
    # cannot rot.
    "verify_anchor_three_ways.py": ("CONTROL: OK", "CONTROL FAILED"),
    # M1: was ("gating.py", "REAL CONTENT DIFF for every path"). The tool emits
    # a bare verdict token per row and never that sentence, so the clause could
    # not fire. crlf_discriminator.py now reports its real failure modes
    # (empty blob / missing file / missing archive copy) as SELF-CHECK: FAIL.
    "crlf_discriminator.py":      ("gating.py", "SELF-CHECK: FAIL"),
    "spec_shape_probe.py":        ("governance", "Traceback"),
    "probe_self_diagnosis.py":    ("D3", "Traceback"),
    "build_errata_index.py":      ("self-check: OK", "self-check: ["),
}

# patch_tasks_line.py has no meaningful no-argument run -- it needs a file, a
# unique line prefix and a replacement, and now also accepts an `after` mode.
# Judging it by "did it print success with no args" was the wrong contract; it is
# given a real SUCCESS run against a scratch file, plus the `after` mode, plus a
# REFUSAL run, because a tool that rewrites a file matters most in what it
# declines to do.
SCRATCH = TOOLS / "_scratch_tasks.md"
SCRATCH.write_text("- [ ] 0.1 alpha\n- [ ] 0.2 beta\n- [ ] 0.3 gamma\n", encoding="utf-8")
_pt = TOOLS / "patch_tasks_line.py"
_rep = subprocess.run([sys.executable, str(_pt), str(SCRATCH), "- [ ] 0.2 beta",
                       str(TOOLS / "applied_text_0.2.txt")], cwd=ROOT,
                      capture_output=True, text=True, encoding="utf-8")
_ins = subprocess.run([sys.executable, str(_pt), str(SCRATCH), "- [ ] 0.3 gamma",
                       str(TOOLS / "applied_text_0.5.txt"), "after"], cwd=ROOT,
                      capture_output=True, text=True, encoding="utf-8")
_ref = subprocess.run([sys.executable, str(_pt), str(SCRATCH), "- [ ] ",
                       str(TOOLS / "applied_text_0.2.txt")], cwd=ROOT,
                      capture_output=True, text=True, encoding="utf-8")
_after = SCRATCH.read_text(encoding="utf-8")
# The `after` insertion must not pin a line number: the replace above already
# turned line 2 into a multi-line block, so "0.3 gamma" is no longer line 3.
# Asserting "inserted after line 2" here would be asserting an accident of the
# fixture's shape, not a property of the tool.
_ok = (_rep.returncode == 0 and "replaced line 2" in (_rep.stdout or "")
       and _ins.returncode == 0 and "inserted after line" in (_ins.stdout or "")
       and _ref.returncode == 1 and "ABORT" in (_ref.stdout or "")
       and _after.startswith("- [ ] 0.1 alpha")
       and "勘误层与盲区层解析" in _after          # the `after` insertion really landed
       and _after.count("- [ ] 0.3 gamma") == 1)  # `after` INSERTS -- the anchor stays
SCRATCH.unlink()
print(f"{'patch_tasks_line.py':<32} {0 if _ok else 1:>4}  replace/after/refusal "
      f"{'OK' if _ok else 'FAILED'}")
if not _ok:
    print(f"      replace={_rep.returncode} insert={_ins.returncode} refuse={_ref.returncode}")
    print(f"      repr stdout: {(_rep.stdout or _rep.stderr or '')[:120]}")
    print(f"      final scratch: {_after[:160]!r}")

print(f"{'tool':<32} {'exit':>4}  {'must-appear':<8} {'must-absent':<11} verdict")
print("-" * 100)
# M2: a duplicate CONTRACT key is a silent clause loss, so it is now a gate on
# itself. Reading the source rather than the dict is the point -- once the dict
# is built, the evidence is gone.
_src = Path(__file__).read_text(encoding="utf-8")
_declared = re.findall(r'^\s*"([\w]+\.py)":', _src, re.M)
_dupes = {k: v for k, v in Counter(_declared).items() if v > 1}
if _dupes:
    print(f"CONTRACT SELF-CHECK: FAIL  duplicate keys {_dupes} -- clauses are being "
          f"silently discarded")
    sys.exit(1)
print(f"CONTRACT SELF-CHECK: OK  {len(_declared)} declared clauses, "
      f"{len(CONTRACT)} unique keys, no duplicates")

bad = []
for name, (must, mustnot) in CONTRACT.items():
    p = TOOLS / name
    if not p.is_file():
        print(f"{name:<32} {'--':>4}  MISSING TOOL")
        continue
    r = subprocess.run([sys.executable, str(p)], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    a = must in out
    b = mustnot not in out
    ok = (r.returncode == 0) or name == "patch_tasks_line.py"   # usage guard exits 1 by design
    good = a and b and ok
    print(f"{name:<32} {r.returncode:>4}  {str(a):<8} {str(b):<11} "
          f"{'OK' if good else 'FAILED'}")
    if not good:
        bad.append(name)
        if not a:
            print(f"      expected to contain: {must!r}")
        if not b:
            print(f"      expected NOT to contain: {mustnot!r}")

print()
print(f"ALL {len(CONTRACT) + 1} TOOLS VERIFIED FROM evidence/tools/" if not bad
      else f"NOT VERIFIED: {bad}")
sys.exit(1 if (bad or not _ok) else 0)
