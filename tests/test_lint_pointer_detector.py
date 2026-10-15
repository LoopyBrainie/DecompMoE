"""Platform-independent guard for the census path-join in the pointer gate.

The defect guarded here was invisible for many commits for one reason: every
existing test exercises only the NATIVE ``Path`` flavour of the host. This
module reconstructs the OTHER platform's resolution on whichever host runs it,
so a POSIX-fatal join cannot reappear unnoticed on a Windows tree.
"""

from __future__ import annotations

import ast
from pathlib import Path, PurePosixPath, PureWindowsPath

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

#: A tracked relative path exactly as ``git ls-tree`` spells it.
REL = "openspec/specs/wayfinder/spec.md"

#: The two call sites that build a filesystem path out of a tracked relative
#: path before opening it.
GATE_SOURCES = (_SCRIPTS / "pointer_scan.py", _SCRIPTS / "lint_pointer_detector.py")


def _separator_rewrites(path: Path) -> list[int]:
    """Line numbers of executable ``.replace("/", "\\")`` calls in ``path``.

    Parsed rather than grepped: a comment or docstring is allowed to NAME the
    rewrite it documents, so a text search would either fail on the very
    explanation of the defect or be too blunt to tell code from prose.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "replace"):
            continue
        args = [a.value for a in node.args if isinstance(a, ast.Constant)]
        if len(args) == 2 and args[0] == "/" and args[1] == "\\":
            hits.append(node.lineno)
    return hits


def test_plain_join_is_multi_component_on_both_flavours() -> None:
    """The property the fix relies on: ``/`` is a separator on both platforms.

    ``WindowsPath`` accepts ``/`` natively, so the rewrite was never needed;
    ``PosixPath`` accepts it because it IS the separator.
    """
    assert len((PureWindowsPath("C:/repo") / REL).parts) == 6
    assert len((PurePosixPath("/repo") / REL).parts) == 6


def test_separator_rewrite_collapses_the_path_on_posix() -> None:
    """The hazard, asserted so it is on record: one component, not six."""
    collapsed = PurePosixPath("/repo") / REL.replace("/", "\\")
    assert len(collapsed.parts) == 3
    assert collapsed.parts[-1] == REL.replace("/", "\\")
    assert collapsed.name == REL.replace("/", "\\")


def test_separator_rewrite_is_a_noop_on_windows() -> None:
    """Why the defect stayed invisible on a Windows tree, pinned deliberately."""
    plain = PureWindowsPath("C:/repo") / REL
    rewritten = PureWindowsPath("C:/repo") / REL.replace("/", "\\")
    assert str(plain) == str(rewritten)
    assert plain.parts == rewritten.parts


def test_gate_sources_carry_no_separator_rewrite() -> None:
    """The tripwire with teeth: a reintroduction is loud on ANY host.

    Without this, re-adding the rewrite is a silent green on Windows and a
    crash on POSIX -- which is precisely how it survived from ``34b445a``.
    """
    for path in GATE_SOURCES:
        hits = _separator_rewrites(path)
        assert not hits, (
            f"{path.name} reintroduces a separator rewrite at line(s) {hits}"
        )
