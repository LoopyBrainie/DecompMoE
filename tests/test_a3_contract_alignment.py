"""A-3 remediation: contract-alignment guards for the C3 code change.

Every test here exists to pin a claim the re-verdict ledger established, so a
later refactor cannot quietly reintroduce the defect it closed. Numeric
discipline per `governance` req-gov-1:

* integer closed forms (phase boundaries, symbol counts) use a **bare `==`**,
  never `pytest.approx(..., abs=0)` -- approx's `rel=1e-6` default stays live
  alongside `abs`, so `abs=0` is not zero tolerance.
* float closed forms use `pytest.approx(..., abs=...)`.
* every failure message embeds the actual value via `f"actual={...}"`.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import pathlib

import pytest
import torch

torch.manual_seed(0)

import decompmoe
from decompmoe import config, distance, experts, extraction, gating, loss, metrics
from decompmoe import safeguards, schedule, sphere, viz
from decompmoe import contracts  # noqa: F401  (submodule with no exported names)

PKG_DIR = pathlib.Path(decompmoe.__file__).parent


# ===================================================================== AC-78
def test_all_is_deduplicated_union_of_submodule_alls() -> None:
    """req-1: the union is 75 names; the naive per-module sum is 76 and is NOT the total."""
    per_module: dict[str, list[str]] = {}
    for p in sorted(PKG_DIR.glob("*.py")):
        if p.name == "__init__.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                getattr(t, "id", "") == "__all__" for t in node.targets
            ):
                if node.value.elts and isinstance(node.value.elts[0], ast.Constant):
                    per_module[p.stem] = [e.value for e in node.value.elts]

    union = set().union(*[set(v) for v in per_module.values()])
    total_sum = sum(len(v) for v in per_module.values())

    # Integer closed forms -> bare == (governance req-gov-1).
    assert len(union) == 75, f"actual={len(union)} (expected the de-duplicated union 75)"
    assert total_sum == 76, f"actual={total_sum} (the per-module sum, MUST NOT be the target)"
    assert len(decompmoe.__all__) == 78, f"actual={len(decompmoe.__all__)} (75 + 3 dunders)"
    assert len(set(decompmoe.__all__)) == 78, "actual=__all__ contains duplicates"


def test_all_entries_resolve() -> None:
    """Every name in the package `__all__` must actually be an attribute."""
    missing = [n for n in decompmoe.__all__ if not hasattr(decompmoe, n)]
    assert not missing, f"actual missing={missing}"


def test_flops_per_token_binds_to_config_not_the_metrics_mirror() -> None:
    """req-1 binding rule: `config` is canonical; the `metrics` mirror stays reachable."""
    assert decompmoe.flops_per_token is config.flops_per_token, (
        f"actual={decompmoe.flops_per_token.__module__} (expected decompmoe.config)"
    )
    assert metrics.flops_per_token is not config.flops_per_token, (
        "actual=the metrics mirror collapsed onto config; it must remain its own object"
    )


def test_star_import_binds_every_public_name() -> None:
    """`from decompmoe import *` never worked before; req-1 makes it a real contract."""
    ns: dict[str, object] = {}
    exec("from decompmoe import *", ns)  # noqa: S102 - the contract under test
    missing = [n for n in decompmoe.__all__ if n not in ns]
    assert not missing, f"actual missing_after_star_import={missing}"


def test_pre_rename_and_new_symbols_are_absent() -> None:
    """`GeoMoE` is prose-only per req-1; it must not become a code identifier."""
    src = (PKG_DIR / "__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "GeoMoE" not in names, "actual=GeoMoE appears as a code identifier"


# ===================================================================== AC-75
def test_extract_C_accepts_the_req7_declared_signature_by_keyword() -> None:
    """AC-75: the spec's declared signature must be executable, not just documented."""
    torch.manual_seed(0)
    B, H, N, dk, dc = 2, 2, 5, 4, 8
    K = torch.randn(B, H, N, dk, requires_grad=True)
    V = torch.randn(B, H, N, dk, requires_grad=True)
    proj_W_K = torch.randn(H, dk, dc, requires_grad=True)
    proj_W_V = torch.randn(H, dk, dc, requires_grad=True)
    proj_b = torch.randn(H, dc, requires_grad=True)

    C = extraction.extract_C(
        K, V, proj_W_K=proj_W_K, proj_W_V=proj_W_V, proj_b=proj_b, H_kv=H, d_c=dc
    )
    assert C.shape == (B, N, dc), f"actual={tuple(C.shape)}"
    C.sum().backward()
    assert proj_W_K.grad is not None, "actual=proj_W_K.grad is None"


# ===================================================================== AC-73
def test_clip_global_grad_norm_returns_a_float_for_a_0d_norm() -> None:
    """AC-73: `clip_grad_norm_` always returns a 0-dim tensor, so no branch was needed."""
    torch.manual_seed(0)
    p = torch.nn.Parameter(torch.randn(4, 3))
    p.grad = torch.randn(4, 3)
    # The helper returns the PRE-clip norm (per its docstring), not the clipped one.
    expected = float(torch.linalg.norm(p.grad))
    out = safeguards.clip_global_grad_norm_([p], max_norm=1.0)
    assert isinstance(out, float), f"actual={type(out).__name__}"
    assert out == pytest.approx(expected, abs=1e-6), f"actual={out!r} expected={expected!r}"
    # The clip itself still happened: the gradient is now at max_norm.
    assert float(torch.linalg.norm(p.grad)) == pytest.approx(1.0, abs=1e-6), (
        f"actual={float(torch.linalg.norm(p.grad))}"
    )


# ===================================================================== AC-79
def test_voronoi_angle_probe_honours_the_centroids_device() -> None:
    """AC-79: the probe was built on CPU because `randn` had no `device=`."""
    src = inspect.getsource(sphere.voronoi_angle)
    assert "device=centroids.device" in src, (
        "actual=voronoi_angle still builds its probe without a device argument"
    )


# ===================================================================== AC-44
def test_phase_boundaries_at_100k_reproduce_the_legacy_constant() -> None:
    """AC-44: parameterising total_steps must not perturb the 100K run. Integer -> bare ==."""
    assert schedule.phase_boundaries(100_000) == (1_000, 6_000, 26_000, 56_000, 100_000), (
        f"actual={schedule.phase_boundaries(100_000)}"
    )
    assert schedule.phase_boundaries() == (1_000, 6_000, 26_000, 56_000, 100_000), (
        f"actual={schedule.phase_boundaries()} (default must stay 100K)"
    )


def test_lambda_at_100k_schedule_is_unchanged() -> None:
    """AC-44: the λ(t) closed form at the default budget."""
    assert loss._lambda_at(3, 26_000) == pytest.approx(0.0, abs=1e-12), (
        f"actual={loss._lambda_at(3, 26_000)}"
    )
    mid = loss._lambda_at(3, 41_000)
    assert mid == pytest.approx(loss.LAMBDA_MAX / 2, abs=1e-12), f"actual={mid}"
    end = loss._lambda_at(3, 56_000)
    assert end == pytest.approx(loss.LAMBDA_MAX, abs=1e-9), f"actual={end}"


def test_lambda_at_rescales_with_total_steps() -> None:
    """AC-44: a 50K run must ramp over the 50K window, not the 100K one."""
    half = 50_000
    # Same relative position in the Phase-3 window -> same lambda.
    assert loss._lambda_at(3, 13_000, total_steps=half) == pytest.approx(0.0, abs=1e-12), (
        f"actual={loss._lambda_at(3, 13_000, total_steps=half)}"
    )
    mid = loss._lambda_at(3, 20_500, total_steps=half)
    assert mid == pytest.approx(loss.LAMBDA_MAX / 2, abs=1e-12), f"actual={mid}"
    # And it must DIFFER from the un-rescaled 100K reading at the same step.
    assert loss._lambda_at(3, 20_500, total_steps=half) != loss._lambda_at(3, 20_500), (
        "actual=total_steps had no effect on the lambda schedule"
    )


def test_lambda_at_signature_accepts_total_steps() -> None:
    """AC-44: `total_steps` must be part of the signature, not a module global."""
    sig = inspect.signature(loss._lambda_at)
    assert "total_steps" in sig.parameters, f"actual params={list(sig.parameters)}"
    assert sig.parameters["total_steps"].default == 100_000, (
        f"actual default={sig.parameters['total_steps'].default!r}"
    )


def test_beta_effective_forwards_total_steps_to_the_cap() -> None:
    """AC-44: `beta_effective` used to drop `total_steps` on the floor."""
    sig = inspect.signature(schedule.beta_effective)
    assert "total_steps" in sig.parameters, f"actual params={list(sig.parameters)}"
    assert sig.parameters["total_steps"].default == 100_000, (
        f"actual default={sig.parameters['total_steps'].default!r}"
    )
    # gamma_p = 0 gives beta_param = 15.5, so the cap binds in both phases.
    # step 16_000 sits strictly inside Phase 2 for BOTH budgets: the 100K Phase-2
    # window is [6_000, 26_000) and the 50K one is [3_000, 13_000)... note 16_000 is
    # past the 50K window's end, which clamps progress to 1.0. That asymmetry is
    # exactly what makes the two readings differ, so it is the useful probe.
    half = 50_000
    step = 16_000
    cap_100k = schedule.phase_beta_max(2, step, 100_000)
    cap_50k = schedule.phase_beta_max(2, step, half)
    assert cap_100k != cap_50k, (
        f"actual cap_100k={cap_100k} cap_50k={cap_50k} (the two budgets must differ)"
    )
    got_100k = float(schedule.beta_effective(0.0, 2, step, total_steps=100_000))
    got_50k = float(schedule.beta_effective(0.0, 2, step, total_steps=half))
    assert got_100k != got_50k, (
        f"actual beta_effective ignored total_steps: both={got_100k}"
    )
    # And each result is exactly its own budget's cap (beta_param 15.5 exceeds both).
    assert got_100k == pytest.approx(cap_100k, abs=1e-9), f"actual={got_100k} cap={cap_100k}"
    assert got_50k == pytest.approx(cap_50k, abs=1e-9), f"actual={got_50k} cap={cap_50k}"


def test_beta_effective_at_100k_is_unchanged() -> None:
    """AC-44: default-budget beta values must match the pre-change readings."""
    assert float(schedule.beta_effective(0.0, 1, 0)) == pytest.approx(1.0, abs=1e-12), (
        f"actual={float(schedule.beta_effective(0.0, 1, 0))} (Phase 1 is fixed at 1.0)"
    )
    v3 = float(schedule.beta_effective(-5.0, 3, 41_000))
    assert v3 == pytest.approx(
        float(schedule.beta_effective(-5.0, 3, 41_000, total_steps=100_000)), abs=1e-12
    ), f"actual={v3} (explicit 100K must equal the default)"


def test_import_graph_has_no_cycle() -> None:
    """AC-44 introduced `loss -> schedule`; assert the direction stays acyclic."""
    assert importlib.import_module("decompmoe.loss") is loss
    assert importlib.import_module("decompmoe.schedule") is schedule
    # every submodule stays importable in isolation
    for name in ("beta", "config", "contracts", "distance", "experts", "extraction",
                 "gating", "loss", "metrics", "safeguards", "schedule", "sphere", "viz"):
        assert importlib.import_module(f"decompmoe.{name}") is not None
