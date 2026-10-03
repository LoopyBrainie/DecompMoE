"""Land the last 10 actionable pointer sites.

schedule.py needs its aligned comment column preserved, so those six sites are
rewritten by hand rather than by a blanket regex; the replacement names the
Requirement plus the row label, which clause 1 of req-gov-6 permits and which
avoids minting a third block anchor for a target already reachable by
Requirement + row.

governance:146 records a past audit verdict, so it is MARKED with the repo's
established `(historical, ...)` convention rather than re-anchored: the pointer
text is the audit trail and rewriting it would falsify the record. Marking makes
the exemption nameable, which is what task 9.2 requires.
"""

import sys
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from _repo import REPO  # noqa: E402

ROOT = REPO

EDITS = [
    # --- schedule.py: docstring header, then the three aligned rows ----------
    (
        "src/decompmoe/schedule.py",
        '"""Operational β^eff (spec Req 24 per-phase formulas, wayfinder L491-507).',
        '"""Operational β^eff (per-phase formulas of wayfinder Req 24 Beta\n'
        '    Parameterization Space vs Operational Domain (`#req-24`)).',
        1,
    ),
    (
        "src/decompmoe/schedule.py",
        "Phase 1: β^eff = 1.0 (fixed, regardless of γ)              — line 495",
        "Phase 1: β^eff = 1.0 (fixed, regardless of γ)              — Req 24 Phase 1 row",
        1,
    ),
    (
        "src/decompmoe/schedule.py",
        "Phase 2-3: Clamp(β^param(γ), 1.0, β_max(t))               — line 496",
        "Phase 2-3: Clamp(β^param(γ), 1.0, β_max(t))               — Req 24 Phase 2-3 row",
        1,
    ),
    (
        "src/decompmoe/schedule.py",
        "Phase 4:  β^eff = 1 + 31 · σ(γ')                          — line 497",
        "Phase 4:  β^eff = 1 + 31 · σ(γ')                          — Req 24 Phase 4 row",
        1,
    ),
    (
        "src/decompmoe/schedule.py",
        "# Spec line 495: fixed 1.0 (γ-independent exploration phase).",
        "# Req 24 Phase 1 row: fixed 1.0 (γ-independent exploration phase).",
        1,
    ),
    (
        "src/decompmoe/schedule.py",
        "# Spec line 496: Clamp(β^param(γ), 1.0, β_max(t))",
        "# Req 24 Phase 2-3 row: Clamp(β^param(γ), 1.0, β_max(t))",
        1,
    ),
    (
        "src/decompmoe/schedule.py",
        "# Spec line 497: 1 + 31 · σ(γ'); the γ' reset already places this",
        "# Req 24 Phase 4 row: 1 + 31 · σ(γ'); the γ' reset already places this",
        1,
    ),
    # --- code pointer -> module::symbol --------------------------------------
    (
        "tests/test_safeguards.py",
        "N6 fix: `src/decompmoe/safeguards.py:54` returns",
        "N6 fix: `safeguards.py::clip_global_grad_norm_` returns",
        1,
    ),
    # --- the line already names its Requirement; only the coordinate is stale -
    (
        "tests/test_sphere.py",
        '"""Spec L370 (req-16): Decode SRAM footprint',
        '"""wayfinder Req 16 Prefill And Decode Share The Same Algorithm '
        '(`#req-16`): Decode SRAM footprint',
        1,
    ),
    # --- historical audit record: marked, not re-anchored --------------------
    (
        "openspec/specs/governance/spec.md",
        "`.audit/audit-verification/audit-verification.md` cycle-5 finding 1 (verify-18 evidence L1349):",
        "`.audit/audit-verification/audit-verification.md` historical cycle-5 finding 1 "
        "(verify-18 evidence L1349):",
        1,
    ),
]


def main() -> int:
    problems, touched = [], set()
    for rel, old, new, want in EDITS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", newline="")
        eol = "\r\n" if "\r\n" in text else "\n"
        old_e, new_e = old.replace("\n", eol), new.replace("\n", eol)
        n = text.count(old_e)
        if n != want:
            problems.append(f"{rel}: expected {want} hit(s) of {old[:60]!r}, got {n}")
            continue
        if len(new) < len(old) * 0.9:
            problems.append(f"{rel}: {old[:40]!r} would truncate ({len(old)}->{len(new)})")
            continue
        with path.open("w", encoding="utf-8", newline="") as fh:
            fh.write(text.replace(old_e, new_e, want))
        touched.add(rel)
        print(f"  {rel}: {old[:55]!r} -> ok")

    for rel in sorted(touched):
        text = (ROOT / rel).read_text(encoding="utf-8")
        for _r, old, new, _w in [e for e in EDITS if e[0] == rel]:
            if old in text:
                problems.append(f"{rel}: old form still present {old[:50]!r}")
            if new not in text:
                problems.append(f"{rel}: new form missing {new[:50]!r}")

    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print("\n10 sites fixed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
