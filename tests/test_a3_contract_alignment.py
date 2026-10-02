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


# ======================================================== AC-43 / AC-76
def test_resurrect_expert_requires_a_per_call_centroid_matrix() -> None:
    """AC-43: req-32 declares a per-call `c_centroids`; the code must take it.

    AC-76 recorded that the wrapper's docstring and its arguments had drifted
    apart, and AC-43 that the returned "perturbed centroid" was the bare `ε`.
    The fix has to land in BOTH: the signature gains the required argument
    (spec-first, `wayfinder` req-32) and the return value becomes
    `L2Normalize(c_centroids[j_star] + ε)`.
    """
    params = list(inspect.signature(safeguards.resurrect_expert).parameters)
    assert params == ["i", "j_star", "β_per_expert", "c_centroids", "cfg",
                      "eps_std"], f"actual={params}"
    # `c_centroids` is REQUIRED (no default) and positional-or-keyword; the
    # centroid matrix is per-call data, never a field of the frozen MVPConfig.
    sig = inspect.signature(safeguards.resurrect_expert)
    assert sig.parameters["c_centroids"].default is inspect.Parameter.empty, (
        "actual=c_centroids has a default; spec req-32 declares it required"
    )
    assert "centroid" not in config.MVPConfig.__dataclass_fields__, (
        f"actual={sorted(config.MVPConfig.__dataclass_fields__)}"
    )


def test_resurrect_expert_docstring_matches_its_call_site() -> None:
    """AC-76: the docstring described `torch.empty(0)`; the code passed `f_per_expert`."""
    doc = safeguards.resurrect_expert.__doc__ or ""
    assert "torch.empty(0)" not in doc, (
        "actual=docstring still claims the primitive is fed torch.empty(0)"
    )
    assert "f_per_expert" in doc, "actual=docstring never names the real first argument"
    src = inspect.getsource(safeguards.resurrect_expert)
    # The primitive call must name `f_per_expert`, not an ad-hoc literal.
    assert "f_per_expert, j_star, eps_std=eps_std, dim=cfg.d_c" in src, (
        "actual=wrapper no longer passes f_per_expert as the leading argument"
    )


def test_resurrect_expert_returns_a_unit_norm_point_near_the_donor() -> None:
    """AC-43: float closed forms -- `‖c_perturbed‖₂ == 1.0` and `cos(donor) > 0`.

    The pre-A-3 wrapper returned the bare `ε`; over 200 000 samples at
    `d_c = 16, eps_std = 0.05` that gave `E[cos] = -0.000289` (90.02 deg) and
    `E‖ε‖₂ = 0.197012` -- a vector orthogonal to its donor and off the sphere.
    """
    torch.manual_seed(0)
    cfg = config.MVPConfig()
    β = torch.ones(cfg.N_e)
    C = torch.nn.functional.normalize(torch.randn(cfg.N_e, cfg.d_c), dim=-1)
    i, j_star = 0, 5

    c_perturbed, _ = safeguards.resurrect_expert(i, j_star, β, C, cfg)
    n = float(torch.linalg.norm(c_perturbed))
    assert n == pytest.approx(1.0, abs=1e-6), f"actual=norm {n!r} expected 1.0"
    cos = float(torch.dot(c_perturbed, C[j_star]))
    assert cos > 0, f"actual=cos {cos!r} (bare-epsilon behaviour is ~-0.000289)"


def test_resurrect_expert_clones_the_donor_row_not_the_dead_expert() -> None:
    """req-32 Scenario "clone source is the donor row, not the dead expert".

    With `eps_std = 0` the perturbation is identically zero, so the closed
    form is exact: `c_perturbed == c_centroids[j_star]` and NOT
    `c_centroids[i]`. This is what makes the clone observable at all -- with a
    random draw the two rows are merely "probably" distinguishable.
    """
    torch.manual_seed(0)
    cfg = config.MVPConfig()
    β = torch.ones(cfg.N_e)
    C = torch.nn.functional.normalize(torch.randn(cfg.N_e, cfg.d_c), dim=-1)
    i, j_star = 0, 5

    c_perturbed, _ = safeguards.resurrect_expert(
        i, j_star, β, C, cfg, eps_std=0.0
    )
    donor = C[j_star]
    dead = C[i]
    err_donor = float((c_perturbed - donor).abs().max())
    assert err_donor == pytest.approx(0.0, abs=1e-6), (
        f"actual=max|c_perturbed - c_centroids[{j_star}]| = {err_donor}"
    )
    assert not torch.allclose(c_perturbed, dead, atol=1e-3), (
        f"actual=c_perturbed equals the dead expert row c_centroids[{i}]"
    )
    # `spherical_l2_normalize` clamps at eps, so a unit-norm donor survives
    # renormalization to float precision; the residual must be float noise.
    n = float(torch.linalg.norm(c_perturbed))
    assert n == pytest.approx(1.0, abs=1e-6), f"actual=norm {n!r} expected 1.0"


def test_resurrect_expert_rejects_a_mis_shaped_centroid_matrix() -> None:
    """req-32 pins `c_centroids` at shape `(N_e, d_c)`; anything else is a bug."""
    torch.manual_seed(0)
    cfg = config.MVPConfig()
    β = torch.ones(cfg.N_e)
    for bad in (
        torch.randn(cfg.d_c),                 # a bare row vector: `C[j]` -> scalar
        torch.randn(cfg.N_e, cfg.d_c + 1),    # wrong d_c
        torch.randn(cfg.N_e + 1, cfg.d_c),    # wrong N_e
    ):
        with pytest.raises(ValueError, match=r"c_centroids must have shape"):
            safeguards.resurrect_expert(0, 5, β, bad, cfg)


# ===================================================================== AC-17
def test_centroid_driver_step_requires_mask_positionally() -> None:
    """AC-17: req-18 declares `mask` a REQUIRED positional parameter."""
    params = inspect.signature(extraction.CentroidDriver.step).parameters
    assert "mask" in params, f"actual={list(params)}"
    assert params["mask"].default is inspect.Parameter.empty, (
        f"actual=mask default is {params['mask'].default!r}; req-18 forbids a default"
    )
    names = [n for n, p in params.items() if p.kind is p.POSITIONAL_OR_KEYWORD]
    assert names == ["self", "centroids", "X", "mask"], f"actual={names}"


def test_centroid_driver_step_rejects_a_missing_mask() -> None:
    """AC-17: "an implementation MUST reject a missing `mask`, not substitute one"."""
    torch.manual_seed(0)
    centroids = torch.randn(4, 8)
    X = torch.randn(20, 8)
    # 1) omitted entirely -> the signature itself refuses
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        extraction.CentroidDriver(extraction.Phase.EMA_090).step(centroids, X)
    # 2) passed as None -> rejected explicitly, with a self-locating message
    with pytest.raises(TypeError, match="requires an explicit per-expert `mask`"):
        extraction.CentroidDriver(extraction.Phase.EMA_090).step(centroids, X, None)


def test_centroid_driver_per_expert_mask_does_not_collapse_territories() -> None:
    """AC-17 regression pin for the removed whole-batch-mean substitution.

    `mask=None` fed `X.mean(dim=0)` broadcast to every centroid, so all N_e
    territories converged to one point. Measured over 999 EMA steps at
    `N_e = 16, d_c = 16` (re-derived here, not copied):

        per-expert mask      mean pairwise dist =  1.421196, cos = -0.023137
        mask=None (removed)  mean pairwise dist =  0.396100, cos = +0.916776

    The same run taken to 5999 steps ends at dist 0.000291 / cos +1.000000
    for the removed path -- terminal consensus on a single point.
    """
    torch.manual_seed(0)
    N_e, d_c, steps = 16, 16, 999
    C = torch.nn.functional.normalize(torch.randn(N_e, d_c), dim=-1)
    driver = extraction.CentroidDriver(extraction.Phase.EMA_090)
    for t in range(steps):
        X = torch.randn(64, d_c)
        assign = torch.arange(64) % N_e
        mask = torch.zeros(64, N_e)
        mask[torch.arange(64), assign] = 1.0
        C = driver.step(C, X, mask)

    iu = torch.triu_indices(N_e, N_e, offset=1)
    dist = float(torch.cdist(C, C)[iu[0], iu[1]].mean())
    cos = float((C @ C.T)[iu[0], iu[1]].mean())
    assert dist == pytest.approx(1.421196, abs=1e-4), (
        f"actual=mean pairwise distance {dist!r} after {steps} per-expert EMA steps"
    )
    assert cos == pytest.approx(-0.023137, abs=1e-4), (
        f"actual=mean pairwise cosine {cos!r} (the removed path reaches +1.000000)"
    )


# ===================================================================== AC-41
def test_ur_window_constant_is_100_and_stays_off_the_public_surface() -> None:
    """AC-41: req-20 fixes `W = 100`; req-1 fixes the public surface at 75 names.

    Integer closed form -> bare `==`, never `pytest.approx(..., abs=0)`.
    The package-level count is 78 = the 75-name union plus the 3 dunder
    entries `__version__` / `__canonical_name__` / `__alias__`; req-1 pins all
    three numbers and forbids the naive per-module sum of 76.
    """
    assert metrics._UR_WINDOW_STEPS == 100, (
        f"actual=W {metrics._UR_WINDOW_STEPS!r} expected 100 (spec wayfinder req-20)"
    )
    assert "_UR_WINDOW_STEPS" not in metrics.__all__, (
        "actual=_UR_WINDOW_STEPS is exported from metrics.__all__"
    )
    assert "_UR_WINDOW_STEPS" not in decompmoe.__all__, (
        "actual=_UR_WINDOW_STEPS leaked into the package __all__; req-1 pins 75"
    )
    assert len(decompmoe.__all__) == 78, f"actual={len(decompmoe.__all__)}"


def test_ur_truncates_to_the_most_recent_100_steps() -> None:
    """AC-41: `UR` is defined "over the most recent W = 100 steps".

    200 steps whose first half activates 3 experts and whose second half
    activates 2 of those same 3: the windowed answer is 2/16 = 0.125, while
    reducing all 200 steps (the pre-fix behaviour) gives 3/16 = 0.1875.
    """
    torch.manual_seed(0)
    N_e = 16
    hist = torch.zeros(200, N_e)
    hist[0:100, 0] = 1.0
    hist[0:100, 1] = 1.0
    hist[0:100, 2] = 1.0
    hist[100:200, 0] = 1.0
    hist[100:200, 1] = 1.0

    n_active_in_window = int((hist[-100:] > 0).any(dim=0).sum())
    assert n_active_in_window == 2, f"actual={n_active_in_window} expected 2"

    ur = float(metrics.UR(hist))
    assert ur == pytest.approx(0.125, abs=1e-9), f"actual={ur!r} expected 2/16"
    # the truncation is invisible to the caller: windowed == trailing W
    assert float(metrics.UR(hist)) == float(metrics.UR(hist[-100:])), (
        f"actual={float(metrics.UR(hist))!r} vs {float(metrics.UR(hist[-100:]))!r}"
    )
    # and the unwindowed value is genuinely different, so the test can fail
    n_active_all = int((hist > 0).any(dim=0).sum())
    assert n_active_all == 3, f"actual={n_active_all} expected 3 (pre-fix reading)"


def test_ur_single_step_matches_the_spec_closed_form() -> None:
    """req-20: `UR = (1/N_e) * sum_i I[f_i > 0]`; the single step is T = 1."""
    N_e = 16
    single = torch.zeros(N_e)
    single[[0, 1, 2]] = 1.0
    n_active = int((single > 0).sum())
    assert n_active == 3, f"actual={n_active} expected 3 (integer closed form)"
    ur = float(metrics.UR(single))
    assert ur == pytest.approx(3 / N_e, abs=1e-9), f"actual={ur!r} expected 3/16"
    assert float(metrics.UR([])) == 0.0, "actual=UR([]) must be 0.0"


def test_ur_reads_axis_0_as_the_time_axis() -> None:
    """A 2-D `(B, N_e)` input is a B-step history, not a `(B, N_e)` batch.

    req-20's gloss is "fraction of experts actually selected", so the window
    reduction is the union over the window. Eight single-expert steps cycling
    over 4 distinct experts therefore give 4/16 = 0.25; the competing reading
    (mean of the per-step fractions) would give 1/16 = 0.0625. req-20 states no
    closed-form Scenario for `UR`, so this pins the reading the gloss and the
    metric's purpose support, and the test name records that it is a choice.
    """
    torch.manual_seed(0)
    N_e = 16
    batch = torch.zeros(8, N_e)
    for t in range(8):
        batch[t, t % 4] = 1.0
    ur = float(metrics.UR(batch))
    assert ur == pytest.approx(0.25, abs=1e-9), (
        f"actual={ur!r} expected 4/16 (union over the window)"
    )
    # list and tensor forms must agree
    assert float(metrics.UR(list(batch))) == ur, (
        f"actual={float(metrics.UR(list(batch)))!r} vs {ur!r}"
    )


def test_ur_rejects_a_0_dim_input() -> None:
    """A 0-d tensor carries neither a time axis nor an expert axis."""
    with pytest.raises(ValueError, match="0-dim input"):
        metrics.UR(torch.tensor(1.0))
