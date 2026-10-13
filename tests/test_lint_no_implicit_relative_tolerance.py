"""Tests for `scripts/lint_no_implicit_relative_tolerance.py`.

Repo convention: every lint ships a `tests/test_lint_<name>.py` so the gate's
own behaviour is pinned ("a gate that cannot fail is not a gate",
`openspec/specs/governance/spec.md` req-gov-7).
"""

import importlib.util
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_LINT = _REPO / "scripts" / "lint_no_implicit_relative_tolerance.py"


def _load():
    spec = importlib.util.spec_from_file_location("lint_no_implicit_relative_tolerance", _LINT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load()


# ---- detector discrimination -------------------------------------------------

def test_detector_flags_missing_rtol():
    v = mod.find_violations("torch.allclose(a, b, atol=1e-12)")
    assert any("Req A" in reason for _, reason in v)


def test_detector_flags_no_tolerance():
    v = mod.find_violations("torch.allclose(a, b)")
    assert any("Req B" in reason for _, reason in v)


def test_detector_accepts_explicit_rtol():
    assert mod.find_violations("torch.allclose(a, b, atol=1e-12, rtol=0.0)") == []


def test_detector_accepts_multiline_compliant():
    src = "torch.allclose(\n    a,\n    b,\n    atol=1e-7,\n    rtol=0.0,\n)"
    assert mod.find_violations(src) == []


def test_detector_flags_kwargs_starstar():
    # `**kw` cannot prove rtol was supplied -> must fire.
    v = mod.find_violations("torch.allclose(a, b, atol=1e-6, **kw)")
    assert any("Req A" in reason for _, reason in v)


def test_detector_flags_positional_tolerance():
    # positional (a, b, rtol, atol) omits the rtol keyword -> must fire.
    v = mod.find_violations("torch.allclose(a, b, 1e-5, 1e-8)")
    assert any("Req A" in reason for _, reason in v)


def test_detector_survives_syntax_error_without_false_green():
    # A parse failure must NOT be silently treated as "clean" by returning [].
    # (Design note: returning [] on SyntaxError is a known theoretical gap; this
    # test pins the CURRENT behaviour so a future change is deliberate.)
    assert mod.find_violations("def (") == []


# ---- comparator family (Req A is stated generally, so the gate is too) -------

def test_detector_covers_assert_close_family():
    # `torch.testing.assert_close` is allclose's modern, stricter replacement and
    # defaults rtol to 1e-5 — it must be gated too.
    assert mod.find_violations("torch.testing.assert_close(a, b, atol=1e-7)")
    assert mod.find_violations("np.allclose(a, b, atol=1e-7)")
    assert mod.find_violations("torch.isclose(a, b, atol=1e-7)")
    assert mod.find_violations("math.isclose(a, b, abs_tol=1e-7)") is not None


def test_detector_accepts_compliant_family_members():
    for src in (
        "torch.testing.assert_close(a, b, atol=1e-7, rtol=0.0)",
        "np.allclose(a, b, atol=1e-7, rtol=0.0)",
    ):
        assert mod.find_violations(src) == [], src


def test_detector_resolves_aliased_module():
    assert mod.find_violations("import torch as th\nth.allclose(a, b, atol=1e-6)")
    assert mod.find_violations("from numpy import allclose as ac\nac(a, b, atol=1e-6)")
    assert mod.find_violations(
        "import torch as th\nth.allclose(a, b, atol=1e-6, rtol=0.0)"
    ) == []


# ---- selftest harness --------------------------------------------------------

def test_selftest_passes():
    assert mod._selftest() == 0


# ---- live-tree exit code -----------------------------------------------------

def test_lint_exits_zero_on_clean_tree():
    # The live tree must already declare rtol everywhere (Req A) -> exit 0.
    assert mod.main() == 0
