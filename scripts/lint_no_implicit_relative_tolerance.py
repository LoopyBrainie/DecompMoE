#!/usr/bin/env python3
r"""Lint gate: a numerical comparison MUST NOT rely on an unstated default
relative-tolerance term.

Background (`openspec/changes/generalize-numeric-comparison-tolerance-obligation`):

    `torch.allclose(input, other)` applies the criterion
    `|Δ| <= atol + rtol·|other|` with `rtol` defaulting to `1e-5`. When a test
    omits `rtol`, the pass condition carries a *relative* term that scales with
    the magnitude of the compared quantity and that **no party selected**. At
    `tests/test_extraction.py` the three `atol=1e-12` sites (a machine-precision
    identity claim) sat under a default band of `1e-5·0.81 = 8.1e-6` — roughly
    seven orders of magnitude wider than the claimed `1e-12` bound — so a real
    `1.19e-7` float32 drift passed while `atol`-only would have caught it.

    This is the rule half of one defect family whose test half is the two sites
    that were *actually* flipped. Fixing only the flipped sites would leave the
    rule unenforced for every future comparison; a gate is what stops it
    recurring.

Rule (three independent obligations, matching the delta):

    1. A comparison whose relative-tolerance parameter defaults to a nonzero
       value MUST supply it explicitly (`rtol=`). Req A.
    2. A comparison MUST supply at least one of `atol` / `rtol`. Req B.
    3. (informational, folded into 1) a *negative-polarity* comparison
       (`assert not <comparator>(...)`) has the opposite tolerance direction:
       the relative term widens the band of values considered equal, making the
       negative assertion *harder*. Its bound is therefore even less likely to
       have been chosen deliberately. Req C.

Scope:

    * `src/**/*.py` and `tests/**/*.py` — the product tree. `src/decompmoe/
      sphere.py:514` already declares `rtol=0.0` and is the reference form.
    * NOT `openspec/specs/**` — those are prose contracts, not executed
      comparisons.
    * NOT `.audit/**` — untracked (`git ls-files .audit` returns 0); a gate
      over an unversioned path could pass without ever having been red, which
      is `req-gov-7`'s "a gate that cannot fail is not a gate".

Self-test:

    A detector that cannot fire is not a gate. Before scanning the tree this
    script runs its detector against synthetic positive and negative inputs and
    refuses to report a clean tree if the detector did not distinguish them.
"""

import ast
import contextlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCAN_ROOTS = ("src", "tests")

# Req A is stated generally ("a comparator whose relative-tolerance parameter
# defaults to a nonzero value"), so the gate enumerates the same family rather
# than one function: `torch.allclose`, `torch.isclose`, `torch.testing.assert_close`
# and the NumPy equivalents all default `rtol` to 1e-5. The last two are the
# modern replacements for `allclose` and are STRICTER (they check dtype and
# shape), so they are the most likely way to slip past a gate that only knows
# `allclose`. `math.isclose` is included for the same reason.
_COMPARATORS = frozenset({
    "torch.allclose", "allclose",
    "torch.isclose", "isclose",
    "torch.testing.assert_close", "testing.assert_close", "assert_close",
    "np.allclose", "numpy.allclose",
    "np.isclose", "numpy.isclose",
    "math.isclose",
})


def _dotted(node: ast.AST) -> str:
    """Render `a.b.c` / `a` as text; anything else as its last attribute name."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        return ".".join(reversed(parts))
    return parts[0] if parts else ""


def _is_comparator(node: ast.AST, aliases: dict[str, str]) -> bool:
    """True when `node` names one of the gated comparators.

    Resolution covers the direct forms (`torch.allclose`), a bound method
    (`assert_close`), and an aliased module or from-import
    (`import torch as th; th.allclose`, `from numpy import allclose as ac`).
    A comparator reached through a plain variable (`fn = torch.allclose`) is not
    resolvable statically and is out of scope; that gap is recorded rather than
    papered over.
    """
    dotted = _dotted(node)
    if dotted in _COMPARATORS:
        return True
    parts = dotted.split(".")
    head = aliases.get(parts[0])
    if head is None:
        return False
    return ".".join([head, *parts[1:]]) in _COMPARATORS


def _collect_aliases(tree: ast.AST) -> dict[str, str]:
    """Map a local binding name to the module or symbol it was imported from."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    aliases[alias.name.split(".")[0]] = alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return aliases


def _keyword_names(call: ast.Call) -> set[str]:
    return {kw.arg for kw in call.keywords if kw.arg}


def find_violations(source: str) -> list[tuple[int, str]]:
    """Return `(lineno, reason)` for every comparison call in `source`.

    A call violates when it omits an explicit `rtol` (Req A) or omits both
    tolerances (Req B). Reported structurally via AST, not by grep, so a
    multi-line call or a differently-spaced one cannot evade it.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    out: list[tuple[int, str]] = []
    aliases = _collect_aliases(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_comparator(node.func, aliases):
            names = _keyword_names(node)
            if "rtol" not in names:
                out.append((node.lineno, "unstated default relative term (Req A): "
                                        "comparison MUST supply `rtol` explicitly"))
            if not ({"atol", "rtol"} & names):
                out.append((node.lineno, "no tolerance at all (Req B): comparison "
                                        "MUST supply at least one of `atol`/`rtol`"))
    return out


def scanned_files() -> list[Path]:
    files: list[Path] = []
    for root in _SCAN_ROOTS:
        files.extend(sorted((_REPO_ROOT / root).rglob("*.py")))
    return [p for p in files if p.is_file()]


def _selftest() -> int:
    """Prove the detector distinguishes a violating call from a compliant one."""
    cases = [
        # (source, expect_violations, label)
        ("torch.allclose(a, b, atol=1e-12)", True, "omitted rtol -> must fire"),
        ("torch.allclose(a, b)", True, "no tolerance -> must fire (A and B)"),
        ("torch.allclose(a, b, atol=1e-12, rtol=0.0)", False, "explicit rtol -> clean"),
        ("torch.allclose(\n    a,\n    b,\n    atol=1e-7,\n    rtol=0.0,\n)", False,
         "multi-line compliant -> clean"),
        ("assert not torch.allclose(a, b, atol=1e-6, rtol=0.0)", False,
         "negative-polarity compliant -> clean"),
        ("torch.testing.assert_close(a, b, atol=1e-7)", True,
         "assert_close omitted rtol -> must fire"),
        ("np.allclose(a, b, atol=1e-7)", True, "np.allclose omitted rtol -> must fire"),
        ("torch.isclose(a, b, atol=1e-7)", True, "isclose omitted rtol -> must fire"),
        ("torch.testing.assert_close(a, b, atol=1e-7, rtol=0.0)", False,
         "assert_close compliant -> clean"),
        ("import torch as th\nth.allclose(a, b, atol=1e-6)", True,
         "aliased module must still fire"),
    ]
    failures = 0
    for source, expect, label in cases:
        got = bool(find_violations(source))
        if got != expect:
            failures += 1
            print(f"  SELFTEST FAIL: {label} (expected violations={expect}, got {got})")
    if failures:
        print(f"lint_no_implicit_relative_tolerance: SELFTEST FAILED ({failures} case(s)); "
              "the detector does not discriminate, so a clean report from it would be "
              "meaningless.")
        return 1
    return 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            reconfigure = getattr(stream, "reconfigure", None)
            if reconfigure is not None:
                reconfigure(encoding="utf-8", errors="replace")

    if _selftest() != 0:
        return 1

    violations: list[tuple[Path, int, str]] = []
    scanned = 0
    for path in scanned_files():
        scanned += 1
        rel = path.relative_to(_REPO_ROOT)
        for lineno, reason in find_violations(path.read_text(encoding="utf-8")):
            violations.append((rel, lineno, reason))

    if not violations:
        print(
            f"lint_no_implicit_relative_tolerance: OK "
            f"({scanned} file(s) scanned, every comparison declares its relative term)"
        )
        return 0

    print(f"lint_no_implicit_relative_tolerance: {len(violations)} violation(s) found")
    print()
    for rel, lineno, reason in violations:
        print(f"  {rel}:{lineno}: {reason}")
    print()
    print("`torch.allclose`'s `rtol` defaults to 1e-5 and scales the pass condition")
    print("with |other|. Declare it. `rtol=0.0` states the bound the `atol` already")
    print("claims; a nonzero value is acceptable only when the spec derives it from")
    print("the protected quantity's magnitude.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
