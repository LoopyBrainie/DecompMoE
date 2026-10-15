#!/usr/bin/env python3
r"""Re-verify the 8 `opsx-change` bucket entries at a pinned commit.

Produces `evidence/reverify_opsx_changes.txt`, the mechanical backbone of the
per-item records in `evidence/reverify/`. Each check re-runs a real command or
AST query at this commit; nothing here is transcribed from the planning
conversation, which is the same untrusted channel that produced the defect this
change repairs.

Every check prints OBSERVED values. Adjudication (which of the four D-1 verdicts
applies) lives in the per-item records, not here -- this script refuses to emit a
verdict so that a mechanical pass can never masquerade as a semantic one.

Run from the repository root:
    PYTHONIOENCODING=utf-8 uv run python openspec/changes/2026-10-15-audit-ledger-rebaseline-and-selfdefect-correction/evidence/reverify_opsx_changes.py
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import torch

WAYFINDER = Path("openspec/specs/wayfinder/spec.md")
GOVERNANCE = Path("openspec/specs/governance/spec.md")
SKELETON = Path("openspec/specs/decompmoe-skeleton/spec.md")
METRICS = Path("src/decompmoe/metrics.py")
SOURCE_LINT = Path("scripts/lint_no_source_field_drift.py")
TEST_METRICS = Path("tests/test_metrics.py")

# Function whose relative-tolerance parameter defaults to a nonzero value.
IMPLICIT_RTOL_FUNCS = {
    "torch.allclose", "allclose", "torch.isclose", "isclose",
    "torch.testing.assert_close", "numpy.allclose", "np.allclose",
    "numpy.isclose", "np.isclose",
}


def head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, check=True
    ).stdout.decode().strip()


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def requirement_block(spec: Path, anchor_id: str) -> str:
    """Return the text of the Requirement owning `anchor_id`, up to the next anchor."""
    text = spec.read_text(encoding="utf-8")
    start = text.find(f'<a id="{anchor_id}"></a>')
    if start < 0:
        return ""
    nxt = re.search(r'<a id="[^"]+"></a>', text[start + 1:])
    return text[start:start + 1 + nxt.start()] if nxt else text[start:]


# --------------------------------------------------------------------------
# FIX-001 — implicit relative tolerance in the product tree
# --------------------------------------------------------------------------
def check_fix001() -> None:
    section("FIX-001  implicit rtol on comparison calls (tests/ + src/)")
    offenders: list[str] = []
    scanned = 0
    for root in (Path("tests"), Path("src")):
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                dotted = (
                    fn.attr if isinstance(fn, ast.Attribute)
                    else fn.id if isinstance(fn, ast.Name) else ""
                )
                if dotted not in IMPLICIT_RTOL_FUNCS:
                    continue
                # Skip calls whose arguments are string literals handed to the
                # detector itself (the lint's own self-test fixtures).
                if node.args and all(
                    isinstance(a, ast.Constant) and isinstance(a.value, str)
                    for a in node.args
                ):
                    continue
                scanned += 1
                kw = {k.arg for k in node.keywords if k.arg}
                if "rtol" not in kw:
                    offenders.append(f"{path}:{node.lineno}  {dotted}()")
    print(f"  comparison calls scanned (non-fixture) : {scanned}")
    print(f"  calls WITHOUT an explicit rtol=       : {len(offenders)}")
    for line in offenders:
        print(f"      {line}")


# --------------------------------------------------------------------------
# FIX-006 — all-dead SP sentinel
# --------------------------------------------------------------------------
def check_fix006() -> None:
    section("FIX-006  metrics.py all-dead SP sentinel")
    source = METRICS.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(METRICS))
    returns_nan = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
            fn = node.value.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name == "full" and "nan" in ast.dump(node.value).lower():
                returns_nan = True
    print(f"  `return torch.full(..., float('nan'))` present : {returns_nan}")
    print(f"  docstring forbids reporting 0.0              : "
          f"{'never as ``0.0``' in source or 'never as `0.0`' in source}")


# --------------------------------------------------------------------------
# FIX-007 — wayfinder req-30 closed-form gradient bound
# --------------------------------------------------------------------------
def check_fix007() -> None:
    section("FIX-007  wayfinder req-30 three-in-one-line defects")
    block = requirement_block(WAYFINDER, "req-30")
    if not block:
        print("  req-30 anchor NOT FOUND")
        return
    line_no = WAYFINDER.read_text(encoding="utf-8").split('<a id="req-30">')[0].count("\n") + 1
    print(f"  req-30 anchor line : {line_no}")
    probes = {
        "witness demoted ('one WITNESS')": "one WITNESS",
        "off-sphere form declared WRONG": "WRONG off the sphere",
        "supremum, not attained": "supremum over the closed range",
        "beta_max not attained by finite gamma": "MUST NOT be reported as attained",
        "legacy beta*c/||C|| named as wrong": "β · c / ‖C‖` is WRONG",
    }
    for label, needle in probes.items():
        print(f"  {label:<42}: {block.find(needle) >= 0}")


# --------------------------------------------------------------------------
# FIX-020 — governance req-gov-1 threshold obligation form
# --------------------------------------------------------------------------
def check_fix020() -> None:
    section("FIX-020  governance req-gov-1 enumeration vs general obligation")
    text = GOVERNANCE.read_text(encoding="utf-8")
    block = requirement_block(GOVERNANCE, "req-gov-1")
    # `^(\d+)\. \*\*` dropped obligation 5, which is written `5. Every
    # assertion…` with no leading bold. Match the number and the separator,
    # then take whatever follows, so an unbolded item is not silently lost.
    obligations = sorted({int(m.group(1))
                          for m in re.finditer(r"^(\d+)\.\s+\S", block, re.M)})
    scenarios = len(re.findall(r"^#### Scenario:", block, re.M))
    print(f"  req-gov-1 numbered obligations : {obligations or 'none'}")
    print(f"  req-gov-1 Scenario blocks      : {scenarios}")
    # The scope limitation that leaves FIX-020 partly open: the derivation
    # obligation is written against the RELATIVE-tolerance parameter, and its
    # closing sentence explicitly EXEMPTS the absolute-only form. A bare-scalar
    # absolute threshold therefore falls inside the exemption, not the rule.
    derived = [m.group(0) for m in re.finditer(
        r"[^\n]*relative-tolerance parameter[^\n]*", text)]
    print(f"  derivation obligation scoped to rtol : {len(derived)} clause(s)")
    for clause in derived:
        print(f"      …{clause.strip()[:150]}…")
    exemption_needle = "is not constrained by this Requirement"
    exemption = text.find(exemption_needle) >= 0
    print(f"  explicit EXEMPTION of the absolute-only form : {exemption}")
    if exemption:
        for ln_no, ln in enumerate(text.splitlines(), 1):
            if ln.find(exemption_needle) >= 0:
                print(f"      spec.md:{ln_no}  …{ln.strip()[-140:]}…")


# --------------------------------------------------------------------------
# FIX-034 — wayfinder req-11 seeded-MC disclosure
# --------------------------------------------------------------------------
def check_fix034() -> None:
    section("FIX-034  wayfinder req-11 seeded-MC co-location")
    block = requirement_block(WAYFINDER, "req-11")
    if not block:
        print("  req-11 anchor NOT FOUND")
        return
    line_no = WAYFINDER.read_text(encoding="utf-8").split('<a id="req-11">')[0].count("\n") + 1
    print(f"  req-11 anchor line : {line_no}")
    # Probe for the DISCLOSURE, not for a literal keyword. The property "A_i is
    # a seeded Monte-Carlo estimate" is discharged by naming A_i as the MC
    # estimator in the same sentence as theta-hat AND cross-referencing the
    # obligation that carries the seed/sample-count derivation. Searching for
    # the word "seed" inside req-11 finds nothing and would wrongly report the
    # defect as still present -- that mistake was made once during planning.
    probes = {
        "A_i named the MC estimator, same sentence as theta-hat":
            "Monte-Carlo estimator of the cell areas",
        "theta-hat estimator form present":
            "θ̂ = (1/N_e)",
        "tolerance obligation cross-referenced by id":
            "req-gov-1 obligation 7",
    }
    for label, needle in probes.items():
        print(f"  {label:<52}: {block.find(needle) >= 0}")
    # The entry's own notation: does the symbol it cites still exist anywhere?
    hits = subprocess.run(
        ["git", "grep", "-c", "Â", "--", "openspec/specs/"],
        capture_output=True,
    ).stdout.decode("utf-8", "replace").strip()
    print(f"  symbol 'Â' anywhere under openspec/specs/ : "
          f"{hits if hits else 'NOT FOUND'}")


# --------------------------------------------------------------------------
# FIX-041 — req-gov-9 dangling reference
# --------------------------------------------------------------------------
def check_fix041() -> None:
    section("FIX-041  governance req-gov-9 dangling reference")
    anchor_hits = 0
    for spec in (GOVERNANCE, WAYFINDER, SKELETON):
        anchor_hits += spec.read_text(encoding="utf-8").count('id="req-gov-9"')
    prose = subprocess.run(
        ["git", "grep", "-c", "req-gov-9", "--", "openspec/"],
        capture_output=True,
    ).stdout.decode("utf-8", "replace")
    total = sum(int(line.rsplit(":", 1)[1])
                for line in prose.strip().splitlines() if ":" in line)
    print(f"  `req-gov-9` anchors across the 3 specs : {anchor_hits}")
    print(f"  `req-gov-9` prose references in openspec/ : {total}")
    print("  per-file counts:")
    for line in prose.strip().splitlines():
        print(f"      {line}")


# --------------------------------------------------------------------------
# FIX-042 — SOURCE_EXEMPTIONS registry size
# --------------------------------------------------------------------------
def check_fix042() -> None:
    section("FIX-042  SOURCE_EXEMPTIONS grandfathered absences")
    source = SOURCE_LINT.read_text(encoding="utf-8")
    match = re.search(r"SOURCE_EXEMPTIONS[^=]*=\s*frozenset\((.*?)\n\)", source, re.S)
    if not match:
        print("  SOURCE_EXEMPTIONS block not found")
        return
    entries = re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', match.group(1))
    by_cap: dict[str, int] = {}
    for cap, _ in entries:
        by_cap[cap] = by_cap.get(cap, 0) + 1
    print(f"  total exemptions : {len(entries)}")
    for cap, count in sorted(by_cap.items()):
        print(f"      {cap:<22} {count}")


def main() -> None:
    print(f"HEAD = {head()}")
    print(f"torch = {torch.__version__}")
    check_fix001()
    check_fix006()
    check_fix007()
    check_fix020()
    check_fix034()
    check_fix041()
    check_fix042()


if __name__ == "__main__":
    main()
