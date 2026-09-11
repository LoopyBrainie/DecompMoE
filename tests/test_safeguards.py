"""Tests for `decompmoe.safeguards`: 5 helpers + STEP_ORDER constant.

ST-10 / Req 13 — Backward → clip_grad_norm_(1.0) → optimizer.step() → L2_norm(c_i).
"""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn

from decompmoe import safeguards


def test_clip_grad_norm_threshold() -> None:
    """When global ‖g‖₂ > 1.0, returns scaled grads to norm ≤ 1.0."""
    p = nn.Parameter(torch.randn(8) * 10.0)
    p.grad = torch.randn_like(p) * 5.0
    pre_norm = safeguards.clip_global_grad_norm_(p, max_norm=1.0)
    assert p.grad.norm().item() <= 1.0 + 1e-5
    assert pre_norm > 1.0


def test_clip_grad_norm_threshold_closed_form() -> None:
    """Closed-form guards for `clip_global_grad_norm_`: return-type + math formula.

    Per skeleton spec L206 (item 1): `clip_global_grad_norm_(params, max_norm: float = 1.0)
    -> float` returning the pre-clip norm as a `float` (**NOT `Tensor`** — code-review
    N6 fix: `src/decompmoe/safeguards.py:54` returns `float(pre_clip_norm.item() ...)`).
    Per `CLAUDE.md §6` last bullet, every spec contract with concrete numeric / typing
    assertions MUST have a `pytest.approx` or exact-typed guard. The functional
    `test_clip_grad_norm_threshold` only asserts ≤ / > inequalities; this test adds
    the three closed-form guards that pin spec L206 word-for-word.

    Closed-form assertions:
    1. **Return-type contract**: `pre_norm` MUST be a Python `float` (NOT `Tensor`).
    2. **Pre-clip norm value**: `pre_norm` MUST equal the original `‖g‖₂` of the
       input gradients (before any scaling); PyTorch's `clip_grad_norm_` returns
       `‖g‖₂` pre-clip and the safeguard wraps via `float(.item())`.
    3. **Post-clip strict bound**: `‖g_scaled‖₂` MUST equal `max_norm = 1.0`
       exactly when `‖g‖₂ > max_norm` (the scaling formula `g * (max/‖g‖₂)` is
       FP-exact in this regime, up to 1e-5 tolerance).
    """
    p = nn.Parameter(torch.randn(8) * 10.0)
    p.grad = torch.randn_like(p) * 5.0

    # Capture the pre-clip ‖g‖₂ BEFORE the function modifies p.grad in-place.
    expected_pre_norm = p.grad.norm().item()

    # Sanity-check the test setup invariant: grads must exceed max_norm so the
    # scaling branch fires (otherwise post-clip == pre-clip is a no-op and the
    # closed-form #3 assertion would not exercise the scaling math).
    assert expected_pre_norm > 1.0, (
        f"test setup invariant broken: ‖g‖₂ = {expected_pre_norm} ≤ 1.0; "
        f"the `torch.randn_like(p) * 5.0` amplitude should guarantee > 1.0 "
        f"(E[‖g‖₂] ≈ 5·√8 ≈ 14.14 for an 8-element isotropic Gaussian)"
    )

    pre_norm = safeguards.clip_global_grad_norm_(p, max_norm=1.0)

    # Closed-form #1: Return-type contract (spec L206: "NOT `Tensor`").
    assert isinstance(pre_norm, float), (
        f"clip_global_grad_norm_ must return Python `float` per spec L206 "
        f"'NOT Tensor'; got type {type(pre_norm).__name__} "
        f"(value: {pre_norm!r})"
    )

    # Closed-form #2: Pre-clip norm value (spec L206: "the pre-clip norm"; math
    # formula = ‖g‖₂ of input gradients before scaling).
    assert pre_norm == pytest.approx(expected_pre_norm, abs=1e-6), (
        f"pre_norm returned = {pre_norm}, expected pre-clip ‖g‖₂ = {expected_pre_norm}"
    )

    # Closed-form #3: Post-clip strict upper bound (spec L206: "all gradients
    # are scaled to ‖g‖₂ ≤ 1.0"). In this regime (pre > max), the scaling
    # formula g ← g · (max/‖g‖₂) targets ‖g_scaled‖₂ = max_norm exactly.
    post_norm = p.grad.norm().item()
    assert post_norm <= 1.0 + 1e-5, (
        f"post-clip norm {post_norm} > max_norm + tolerance 1e-5"
    )
    assert post_norm == pytest.approx(1.0, abs=1e-5), (
        f"post-clip norm = {post_norm}, expected 1.0 (= max_norm); the scaling "
        f"formula g * (max/‖g‖₂) targets exactly 1.0 when ‖g‖₂ > max_norm"
    )


def test_nan_ladder() -> None:
    """nan_ladder(consecutive_nan) returns (action, lr_scale, halt) for (1, 3, 10)."""
    assert safeguards.nan_ladder(1) == ("skip", 1.0, False)
    assert safeguards.nan_ladder(3) == ("halve_lr", 0.1, False)
    assert safeguards.nan_ladder(10) == ("halt", 1.0, True)


def test_resurrection_trigger_window() -> None:
    """Within same 1000-step window, at most one resurrection event.

    Spec (wayfinder Req 13 + archived spec): `threshold = 1 / (2·N_e)`.
    MVP N_e=16 → threshold = 1/32. With `f_i = 1/256 < 1/32` for all
    experts and all 250 steps, the rule fires.
    """
    N_e = 16
    history = [[1 / 256] * N_e for _ in range(250)]
    res = safeguards.should_resurrect(
        history,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    res2 = safeguards.should_resurrect(
        history,
        current_step=300,
        last_resurrection_step=0,
        N_e=N_e,
        consec=200,
    )
    assert len(res) > 0, "first call must flag at least one expert"
    assert len(res2) == 0, "second call within window must be rate-limited to empty"


def test_resurrection_threshold_mvp_value() -> None:
    """Threshold at MVP N_e=16 is `1/32`, NOT the legacy `1/128`.

    Spec: archived `fix-openspec-doc-bugs` corrects the hardcoded `1/128`
    to the parameterized `1/(2·N_e)` form. At MVP N_e=16 the threshold
    evaluates to 1/32 = 0.03125.
    """
    N_e = 16
    history = [[0.02] * N_e for _ in range(250)]  # f_i = 0.02 < 1/32 = 0.03125
    res = safeguards.should_resurrect(
        history,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    assert len(res) > 0, "MVP threshold 1/32 must trigger resurrection at f_i=0.02"
    history2 = [[0.05] * N_e for _ in range(250)]  # 0.05 > 1/32
    res2 = safeguards.should_resurrect(
        history2,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    assert len(res2) == 0, "f_i = 0.05 > 1/32 must NOT trigger resurrection"


def test_resurrection_threshold_N_e_64_legacy_value() -> None:
    """For N_e=64, `1/(2·N_e) = 1/128` — preserved as legacy value.

    Spec (archived `fix-openspec-doc-bugs` Decision 7): the previous
    hardcoded `1/128` was the `N_e=64` instantiation of the same
    `1/(2·N_e)` rule. Parameterizing by N_e restores both MVP (1/32)
    and legacy (1/128) thresholds from a single formula.
    """
    N_e = 64
    history = [[1 / 200] * N_e for _ in range(250)]  # 1/200 < 1/128 = 0.0078125
    res = safeguards.should_resurrect(
        history,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    assert len(res) > 0, "N_e=64 threshold 1/128 must trigger at f_i=1/200"
    history2 = [[0.01] * N_e for _ in range(250)]  # 0.01 > 1/128
    res2 = safeguards.should_resurrect(
        history2,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
        consec=200,
    )
    assert len(res2) == 0, "f_i = 0.01 > 1/128 must NOT trigger"


def test_resurrection_perturb_distribution() -> None:
    """Perturbation contract (per-expert): ε ~ N(0, 0.05²·I), single-expert shape.

    Spec (wayfinder ADDED "Resurrection Perturbation Per-Expert Contract"):
    the perturbation is ONE iid Gaussian vector for the cloned expert —
    shape (d_c,) or (d_model·d_ffn,), NOT (N_e,).
    """
    f = torch.zeros(16)
    f[3] = 0.5
    eps = safeguards.resurrection_perturb_distribution(
        f, target_idx=3, eps_std=0.05, dim=16
    )
    assert eps.dim() == 1
    assert abs(eps.std().item() - 0.05) < 0.02


def test_beta_saturation_warning_at_30_4() -> None:
    """β_i > 30.4 (95% of β_max) triggers WARN."""
    β = torch.full((16,), 20.0)
    β[5] = 30.5
    assert safeguards.beta_saturation_warning(β) is True
    β_all_safe = torch.full((16,), 20.0)
    assert safeguards.beta_saturation_warning(β_all_safe) is False


def test_beta_saturation_global_lr_halve_at_28_8() -> None:
    """More than 50% of β_i > 28.8 (90% of β_max) triggers LR halve."""
    β = torch.full((16,), 30.0)
    assert safeguards.beta_saturation_global_halve(β) is True
    β_most_safe = torch.full((16,), 20.0)
    assert safeguards.beta_saturation_global_halve(β_most_safe) is False


def test_loss_spike_defense_phase3plus() -> None:
    """L_task > 2.5 · EMA(L_task) triggers LR × 0.8 ONLY when phase ≥ 3."""
    assert safeguards.loss_spike_defense(L_task=5.0, L_task_ema=1.0, phase=3) is True
    assert safeguards.loss_spike_defense(L_task=5.0, L_task_ema=1.0, phase=2) is False
    assert safeguards.loss_spike_defense(L_task=2.0, L_task_ema=2.0, phase=3) is False


def test_step_ordering() -> None:
    """STEP_ORDER must equal ('backward', 'clip_grad_norm', 'optimizer_step', 'l2_norm')."""
    assert safeguards.STEP_ORDER == (
        "backward",
        "clip_grad_norm",
        "optimizer_step",
        "l2_norm",
    )


# ---------------------------------------------------------------------------
# Task 3.7 — Resurrection Perturbation Per-Expert Contract (wayfinder ADDED)
# ---------------------------------------------------------------------------


def test_resurrection_perturbation_shape_per_expert() -> None:
    """Perturb returns SINGLE-expert shape (d_c,) or (d_model·d_ffn,), NOT (N_e,).

    Spec: wayfinder ADDED "Resurrection Perturbation Per-Expert Contract".
    """
    torch.manual_seed(0)
    d_c = 16
    f = torch.randn(4, 3, 8)  # (B, N, N_e) legacy input
    eps = safeguards.resurrection_perturb_distribution(f, target_idx=2, dim=d_c)
    assert eps.shape == (d_c,), (
        f"expected single-expert ({d_c},), got {tuple(eps.shape)}"
    )
    assert eps.shape != (f.shape[-1],)


def test_resurrection_perturbation_eps_std_scale() -> None:
    """ε ~ N(0, eps_std²·I): empirical std ≈ eps_std for a large sample."""
    torch.manual_seed(0)
    d_c = 4096
    f = torch.zeros(d_c)
    eps = safeguards.resurrection_perturb_distribution(
        f, target_idx=0, eps_std=0.05, dim=d_c
    )
    assert abs(float(eps.std()) - 0.05) < 0.01


def test_resurrection_perturb_default_requires_dim() -> None:
    """Audit finding MAJ-C2: `dim=None` (implicit) MUST raise TypeError.

    Spec Req 28: returned shape MUST be (d_c,) or (d_model·d_ffn,), NOT
    (N_e,). Silent default to `f_per_expert.shape[-1]` would yield (N_e,)
    and violate the per-expert contract. The fix raises TypeError so
    callers must pass `dim` explicitly.
    """
    f = torch.zeros(16)
    with pytest.raises(TypeError, match="requires explicit `dim`"):
        safeguards.resurrection_perturb_distribution(f, target_idx=0)


def test_resurrection_beta_decay() -> None:
    """β decay mutation: β_i ← 0.85·β_{j*} and β_{j*} ← 0.85·β_{j*} in one event.

    Spec: same-event mutation visible via state inspection. Uses the
    module-level decay helper with factor 0.85.
    """
    beta_params = torch.tensor([4.0, 8.0, 12.0])
    out = safeguards.apply_resurrection_beta_decay(beta_params, j_star=1, i=0)
    expected_j = 0.85 * 8.0
    assert out[1].item() == pytest.approx(expected_j, abs=1e-5)  # β_{j*} ← 0.85·β_{j*}
    assert out[0].item() == pytest.approx(
        expected_j, abs=1e-5
    )  # β_i ← 0.85·β_{j*} (old value)
    assert out[2].item() == pytest.approx(12.0, abs=1e-5)  # untouched


# ---------------------------------------------------------------------------
# Single-event resurrection wrapper (wayfinder spec Req "Resurrection
# Perturbation Per-Expert Contract" Scenario `same-event beta decay`).
# ---------------------------------------------------------------------------


def test_resurrect_expert_single_event_contract() -> None:
    """`resurrect_expert` is the canonical single-event API.

    Spec: wayfinder "Resurrection Perturbation Per-Expert Contract"
    Scenario `same-event beta decay`. The wrapper must run
    `resurrection_perturb_distribution` and `apply_resurrection_beta_decay`
    in the SAME call stack (linear composition, no await/yield/spawn),
    returning `(c_perturbed, β_per_expert_new)` where:
    - `c_perturbed.shape == (cfg.d_c,)`
    - `β_per_expert_new[i] == 0.85 · β_per_expert[j_star].item()`
    - `β_per_expert_new[j_star] == 0.85 · β_per_expert[j_star].item()`
    - other entries unchanged
    - `β_per_expert_new is not β_per_expert` (immutability via clone)
    """
    from decompmoe.config import MVPConfig

    cfg = MVPConfig()
    N_e = cfg.N_e
    torch.manual_seed(0)
    β_per_expert = torch.tensor(
        [2.0, 4.0, 6.0, 8.0] + [10.0] * (N_e - 4), dtype=torch.float32
    )
    i, j_star = 0, 5
    donor = β_per_expert[j_star].item()
    c_perturbed, β_new = safeguards.resurrect_expert(i, j_star, β_per_expert, cfg)

    assert c_perturbed.shape == (cfg.d_c,), (
        f"c_perturbed.shape = {c_perturbed.shape}, expected ({cfg.d_c},)"
    )
    assert β_new[j_star].item() == pytest.approx(0.85 * donor, abs=1e-6), (
        f"β_new[{j_star}] = {β_new[j_star].item()}, expected {0.85 * donor}"
    )
    assert β_new[i].item() == pytest.approx(0.85 * donor, abs=1e-6), (
        f"β_new[{i}] = {β_new[i].item()}, expected {0.85 * donor} (donor value)"
    )
    for k in range(N_e):
        if k not in (i, j_star):
            assert β_new[k].item() == pytest.approx(
                β_per_expert[k].item(), abs=1e-6
            ), f"β_new[{k}] unexpectedly modified"
    assert β_new is not β_per_expert, (
        "β_new must be a NEW tensor (clone), not the input reference"
    )


def test_no_other_module_defines_should_resurrect() -> None:
    """The driver MUST NOT define a same-named helper — only `decompmoe.safeguards.should_resurrect` exists.

    Guards the spec contract introduced at `decompmoe-skeleton` L206:
    > "the driver MUST NOT define a same-named helper"

    Iterates over every submodule of `decompmoe` (via `pkgutil.iter_modules`)
    and asserts no module other than `decompmoe.safeguards` defines a
    `should_resurrect` callable. A regression here would mean another module
    has re-introduced the same helper (which historically caused ownership
    ambiguity — see Finding #10 drift report from `d3689a1` and `0d87e32`).

    **Note on enumeration** (code-review N4 fix): earlier draft iterated over
    `vars(decompmoe)` which only contains modules explicitly re-exported by
    `decompmoe/__init__.py`. That misses the 11 submodules that aren't
    re-exported (`config`, `contracts`, `distance`, `experts`, `extraction`,
    `gating`, `loss`, `metrics`, `schedule`, `sphere`, `viz`). Using
    `pkgutil.iter_modules` against `decompmoe.__path__` enumerates ALL 13
    submodules regardless of `__init__.py` re-exports.
    """
    import importlib
    import pkgutil
    import decompmoe

    module_names = [
        mod_info.name for mod_info in pkgutil.iter_modules(decompmoe.__path__, prefix="decompmoe.")
    ]
    # Also include the package __init__ itself for a sanity check.
    module_names = ["decompmoe"] + sorted(set(module_names))

    canonical_owner = "decompmoe.safeguards"
    offending: list[tuple[str, object]] = []
    for module_name in module_names:
        mod = importlib.import_module(module_name)
        if mod is safeguards:
            continue  # canonical owner; should_resurrect is expected here
        attr = getattr(mod, "should_resurrect", None)
        if attr is not None:
            offending.append((module_name, attr))

    assert not offending, (
        f"Modules other than {canonical_owner!r} define `should_resurrect`: "
        f"{offending!r}. Per spec L206, only `decompmoe.safeguards` may expose "
        f"the dead-expert helper. Re-introducing a same-named helper elsewhere "
        f"is a spec-level regression."
    )


def test_named_constants_have_spec_values() -> None:
    """Guard the 4 named-constant numerical claims in the spec delta (code-review N5 / CLAUDE.md §6 last bullet).

    The skeleton spec L206 (Five Numerical Safeguard Helpers) + L210 (Centroid Driver reference) reference these `Final[int]` / `Final[float]`
    module-level constants by name (rather than literal values) so the spec
    stays in lock-step with the code if these constants are retuned:

    - `DEAD_EXPERT_CONSEC_STEPS = 200` (integer; bare `==`)
    - `RESURRECTION_RATE_LIMIT_STEPS = 1000` (integer; bare `==`)
    - `LOSS_SPIKE_RATIO = 2.5` (float; `pytest.approx` with `abs=1e-12`)
    - `LOSS_SPIKE_LR_SCALE = 0.8` (float; `pytest.approx` with `abs=1e-12`)

    Per `CLAUDE.md` §6 last bullet, every spec formula with concrete numeric
    values MUST have a `pytest.approx` (float closed-form) or exact `==`
    (integer closed-form) direct guard. This test is that guard.
    """
    # Integer closed-form claims: bare `==` per CLAUDE.md §6 last bullet
    # ("integer claims ... MUST use bare `==` integer equality ... NOT
    # pytest.approx(...) in any form" — the effective-tolerance formula
    # `max(abs, rel·|expected|)` scales with magnitude and defeats "钉值零容差").
    assert safeguards.DEAD_EXPERT_CONSEC_STEPS == 200, (
        f"DEAD_EXPERT_CONSEC_STEPS = {safeguards.DEAD_EXPERT_CONSEC_STEPS}, "
        f"expected 200 (per spec L206 (Five Numerical Safeguard Helpers) + L210 (Centroid Driver reference))"
    )
    assert safeguards.RESURRECTION_RATE_LIMIT_STEPS == 1000, (
        f"RESURRECTION_RATE_LIMIT_STEPS = {safeguards.RESURRECTION_RATE_LIMIT_STEPS}, "
        f"expected 1000 (per spec L206 (Five Numerical Safeguard Helpers) + L210 (Centroid Driver reference))"
    )

    # (Integer closed-form claims continue below with the BETA saturation
    # constants in the second-pass assertion block.)

    # Float closed-form claims: pytest.approx with abs=1e-12 (the canonical
    # "钉值零容差" tolerance for FP literals — see CLAUDE.md §6 last bullet
    # integer-vs-float binary exemption rationale).
    assert safeguards.LOSS_SPIKE_RATIO == pytest.approx(2.5, abs=1e-12), (
        f"LOSS_SPIKE_RATIO = {safeguards.LOSS_SPIKE_RATIO}, "
        f"expected 2.5 (per spec L206 item (5))"
    )
    assert safeguards.LOSS_SPIKE_LR_SCALE == pytest.approx(0.8, abs=1e-12), (
        f"LOSS_SPIKE_LR_SCALE = {safeguards.LOSS_SPIKE_LR_SCALE}, "
        f"expected 0.8 (per spec L206 item (5))"
    )

    # β saturation thresholds: closed-form derived from BETA_MAX.
    # Per spec L206 item (4): `BETA_SATURATION_WARN = 0.95 · BETA_MAX` and
    # `BETA_SATURATION_HALVE = 0.90 · BETA_MAX`. At MVP `BETA_MAX = 32`
    # these evaluate to `30.4` and `28.8` respectively. We assert against
    # the closed-form derivation (not the FP-literal rounded value) so the
    # test stays in lock-step with `BETA_MAX` if it is retuned.
    assert safeguards.BETA_SATURATION_WARN == pytest.approx(
        0.95 * 32.0, abs=1e-12
    ), (
        f"BETA_SATURATION_WARN = {safeguards.BETA_SATURATION_WARN}, "
        f"expected 0.95 · 32 = {0.95 * 32.0}"
    )
    assert safeguards.BETA_SATURATION_HALVE == pytest.approx(
        0.90 * 32.0, abs=1e-12
    ), (
        f"BETA_SATURATION_HALVE = {safeguards.BETA_SATURATION_HALVE}, "
        f"expected 0.90 · 32 = {0.90 * 32.0}"
    )
    # Also assert the MVP-evaluated literal value (per wayfinder L249):
    # `BETA_SATURATION_WARN = 30.4` (95% of β_max), `BETA_SATURATION_HALVE
    # = 28.8` (90% of β_max). The literal-evaluated form is FP-exact for
    # `0.95 * 32.0 == 30.4` and `0.90 * 32.0 == 28.8` (both are representable
    # in FP32 / FP64).
    assert safeguards.BETA_SATURATION_WARN == pytest.approx(30.4, abs=1e-12)
    assert safeguards.BETA_SATURATION_HALVE == pytest.approx(28.8, abs=1e-12)


# ---------------------------------------------------------------------------
# Closed-form `_dead_expert_threshold(N_e) = 1/(2·N_e)` direct guard
# (verifies spec's `1/32` at MVP / `1/128` legacy closed-form derivations).
# ---------------------------------------------------------------------------


def test_dead_expert_threshold_mvp_closed_form() -> None:
    """`_dead_expert_threshold(16) == 1/32` — MVP closed-form (per wayfinder L249).

    Per wayfinder L249 + skeleton spec L206: `f_threshold = 1/(2·N_e)` and
    "At MVP scale `N_e = 16`, `1/(2 · N_e) = 1/32`". Per CLAUDE.md §6 last
    bullet, every spec formula with concrete numeric values MUST have a
    `pytest.approx` (float closed-form) direct guard. This test asserts
    both (a) the closed-form derivation `1/(2·16)` and (b) the MVP-evaluated
    literal `1/32 = 0.03125` against `_dead_expert_threshold(16)`.
    """
    thr = safeguards._dead_expert_threshold(16)
    # Closed-form derivation: `1 / (2 · N_e)` evaluated at N_e=16
    assert thr == pytest.approx(1.0 / (2.0 * 16.0), abs=1e-12), (
        f"_dead_expert_threshold(16) = {thr}, expected 1/(2·16) = {1.0 / 32.0}"
    )
    # MVP-evaluated literal: 1/32 = 0.03125 (FP-exact)
    assert thr == pytest.approx(1.0 / 32.0, abs=1e-12), (
        f"_dead_expert_threshold(16) = {thr}, expected 1/32 = {1.0 / 32.0}"
    )
    assert thr == pytest.approx(0.03125, abs=1e-12), (
        f"_dead_expert_threshold(16) = {thr}, expected 0.03125 (FP-exact)"
    )


def test_dead_expert_threshold_legacy_N_e_64_closed_form() -> None:
    """`_dead_expert_threshold(64) == 1/128` — legacy N_e=64 closed-form.

    Per skeleton spec L206 / wayfinder L249: the previous hardcoded `1/128`
    was the `N_e=64` instantiation of the `1/(2·N_e)` rule. Parameterizing
    by N_e restores both MVP (`1/32`) and legacy (`1/128`) thresholds
    from a single formula.
    """
    thr = safeguards._dead_expert_threshold(64)
    assert thr == pytest.approx(1.0 / (2.0 * 64.0), abs=1e-12), (
        f"_dead_expert_threshold(64) = {thr}, expected 1/(2·64) = {1.0 / 128.0}"
    )
    assert thr == pytest.approx(1.0 / 128.0, abs=1e-12), (
        f"_dead_expert_threshold(64) = {thr}, expected 1/128 = {1.0 / 128.0}"
    )
    assert thr == pytest.approx(0.0078125, abs=1e-12), (
        f"_dead_expert_threshold(64) = {thr}, expected 0.0078125 (FP-exact)"
    )


def test_threshold_implicit_in_mvp_test_data_below_spec_value() -> None:
    """Test data `0.02 < 1/32` is a mathematical assumption — assert it explicitly.

    Per CLAUDE.md §6 last bullet, every spec formula with concrete numeric
    values MUST have a `pytest.approx` direct guard. `test_resurrection_
    threshold_mvp_value` uses `0.02` as a value "below `1/32`" but only
    documents the relationship in a comment. This test pins the
    mathematical relationship explicitly so a future change to either
    side breaks loudly.
    """
    # Closed-form derivation: spec `1/(2·N_e)` at N_e=16
    threshold = safeguards._dead_expert_threshold(16)
    # Mathematical premise: `0.02 < 1/32` MUST hold for the test data to be
    # meaningful (otherwise the test is testing against the wrong baseline).
    assert 0.02 < threshold, (
        f"0.02 is NOT below threshold {threshold}; test data premise broken"
    )
    # And the spec-literal threshold 1/32 itself:
    assert 0.02 < 1.0 / 32.0
    # Sanity: 0.05 (the "above threshold" value) MUST be above threshold
    assert 0.05 > threshold, (
        f"0.05 is NOT above threshold {threshold}; test data premise broken"
    )


# ---------------------------------------------------------------------------
# β saturation boundary cases (Finding #5: 50% / 30.4 严格边界未守护).
# ---------------------------------------------------------------------------


def test_beta_saturation_global_halve_at_exactly_50pct_returns_false() -> None:
    """Exactly 50% of β_i > 28.8: NOT 'more than 50%' → returns False.

    Per wayfinder L249: 'global LR ÷ 2 when **more than 50%** of experts
    have `β_i > 28.8`'. `more than 50%` is strict (>50%), so the boundary
    case `n/2` (e.g. 8/16 with N_e=16) MUST return False. Code L265 uses
    `count > n/2` (strict). This test pins the boundary.
    """
    β = torch.zeros(16)
    β[:8] = 30.0  # exactly 8/16 > 28.8 → 50% exactly
    assert safeguards.beta_saturation_global_halve(β) is False, (
        "exactly 50% is NOT 'more than 50%' per wayfinder L249"
    )


def test_beta_saturation_global_halve_just_over_50pct_returns_true() -> None:
    """9/16 β_i > 28.8 (>50% strict): returns True.

    Companion boundary test: just above the 50% threshold. Pins that the
    `>` (strict) comparator is used, not `>=`.
    """
    β = torch.zeros(16)
    β[:9] = 30.0  # 9/16 > 28.8 → 56.25% > 50%
    assert safeguards.beta_saturation_global_halve(β) is True


def test_beta_saturation_warning_at_exactly_30_4_returns_false() -> None:
    """β_i == 30.4 (== threshold, strict `>`): returns False.

    Per wayfinder L249: 'warning at `β_i > 30.4`' — strict greater-than.
    Code L259 uses `(β_per_expert > BETA_SATURATION_WARN)` which is strict.
    This test pins the strict-boundary semantics.
    """
    β = torch.full((16,), 20.0)
    β[5] = 30.4  # exactly at threshold, NOT strictly above
    assert safeguards.beta_saturation_warning(β) is False, (
        "β_i == 30.4 (boundary) is NOT 'β_i > 30.4' per wayfinder L249"
    )


def test_beta_saturation_warning_just_above_30_4_returns_true() -> None:
    """β_i = 30.5 (>30.4): returns True (companion to boundary test)."""
    β = torch.full((16,), 20.0)
    β[5] = 30.5
    assert safeguards.beta_saturation_warning(β) is True


# ---------------------------------------------------------------------------
# `nan_ladder` LR-scale closed-form guard: `lr_scale = 0.1` ≡ `LR ÷ 10`
# (per wayfinder L249 'LR ÷ 10' wording).
# ---------------------------------------------------------------------------


def test_nan_ladder_lr_scale_equivalence_to_lr_div_10() -> None:
    """`nan_ladder(3)[1] == 0.1` is mathematically equivalent to `LR ÷ 10`.

    Per wayfinder L249: '3 consecutive NaN trigger LR ÷ 10'. The code
    expresses this as `lr_scale = 0.1` (multiplicative), which is
    numerically equivalent to `LR × (1/10)`. The `0.1` FP literal is
    FP-exactly equal to `1/10` (both are `0x3FB999999999999A` in IEEE-754
    binary64). This test pins the mathematical equivalence per
    CLAUDE.md §6 last bullet.
    """
    action, lr_scale, halt = safeguards.nan_ladder(3)
    assert action == "halve_lr"
    assert halt is False
    # Closed-form: lr_scale × 10 MUST equal 1.0 (i.e. lr_scale IS 1/10).
    assert lr_scale * 10.0 == pytest.approx(1.0, abs=1e-12), (
        f"nan_ladder(3)[1] = {lr_scale}; lr_scale × 10 = {lr_scale * 10.0} ≠ 1.0"
    )
    # And the literal-evaluated form: 0.1 (FP-exact match with 1/10).
    assert lr_scale == pytest.approx(0.1, abs=1e-12)
    assert lr_scale == pytest.approx(1.0 / 10.0, abs=1e-12)


def test_nan_ladder_zero_returns_skip_per_default() -> None:
    """`nan_ladder(0)` (no NaN): returns ("skip", 1.0, False).

    Per skeleton spec L206: 'for counts (1, 3, 10) respectively' —
    `consecutive_nan ∉ {1, 3, 10}` is not explicitly specified in spec.
    Code L72 fallback to `("skip", 1.0, False)` (defensive: do nothing on
    no NaN). This test pins the default-behavior contract so a future
    change to the ladder edge case breaks loudly.
    """
    assert safeguards.nan_ladder(0) == ("skip", 1.0, False)


# ---------------------------------------------------------------------------
# `should_resurrect` semantics note (Finding #1 — pending spec/code alignment
# decision). The current implementation uses the per-step strict less-than
# interpretation; the wayfinder wording `f_i^avg` is ambiguous. This test
# pins the CURRENT (per-step) behavior so any future change to avg-style
# semantics breaks loudly. Resolution requires a separate ticket.
# ---------------------------------------------------------------------------


def test_should_resurrect_current_per_step_semantic_pinned() -> None:
    """Pin current `should_resurrect` per-step semantics (NOT avg-window).

    Per wayfinder L249: 'triggered when `f_i^avg < 1/(2·N_e)` for 200
    consecutive steps'. The `f_i^avg` notation is ambiguous between
    (a) per-step `f_i` with `avg` as a notation convention, and
    (b) literal average over a window. The current code (L97-L101)
    implements (a): every snapshot in the last `consec` steps must have
    `f_i < threshold`. This test demonstrates the difference with a
    non-constant history where per-step vs avg would diverge.

    Decision pending (separate ticket required): which interpretation is
    canonical. This test PIN the CURRENT behavior — a future change to
    avg-window semantics MUST update this test alongside the code.
    """
    N_e = 16
    threshold = 1.0 / 32.0  # = 0.03125
    # History: 199 snapshots at 0.02 (below), 1 snapshot at 0.04 (above).
    # per-step reading: last snapshot 0.04 > threshold → NOT resurrected.
    # avg reading: mean(0.02 × 199 + 0.04) / 200 = 0.02010 < 0.03125 → resurrected.
    history = [[0.02] * N_e for _ in range(199)] + [[0.04] * N_e]
    res = safeguards.should_resurrect(
        history,
        current_step=300,
        last_resurrection_step=-2000,
        N_e=N_e,
    )
    # Current code behavior (per-step strict less-than):
    assert res == set(), (
        f"per-step semantic: last snapshot 0.04 > threshold {threshold} "
        f"→ expert NOT flagged; got {sorted(res)}. If this changes, the "
        f"spec/code semantic decision has been made — update spec L206, "
        f"wayfinder L249, and this test consistently."
    )
    # Avg-window reading would have flagged (sanity assertion, demonstrating
    # the ambiguity): if we manually compute avg, the rule WOULD trigger.
    avg = sum(sum(snap) for snap in history) / (len(history) * N_e)
    assert avg < threshold, (
        f"avg-window reading: mean(f_i) = {avg} < threshold {threshold}; "
        f"avg interpretation WOULD trigger. See test docstring."
    )
