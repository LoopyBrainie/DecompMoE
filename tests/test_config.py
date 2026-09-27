"""Tests for `decompmoe.config`: MVPConfig + compute_total_and_active + flops_per_token.

ST-01 / Req 1, 2, 11, 19 (form factor / FLOPs parity).

These tests are written FIRST (TDD Red) — they intentionally fail at import time
because `decompmoe.config` does not exist yet. The GREEN step implements the
module to make these pass.
"""

from __future__ import annotations

import dataclasses

import pytest

import decompmoe
from decompmoe import config

# ---------------------------------------------------------------------------
# MVPConfig field defaults (Req 11: 4070 MVP hyperparameters)
# ---------------------------------------------------------------------------


def test_mvp_locked_constants() -> None:
    """MVPConfig() must return the locked 4070 MVP hyperparameter set."""
    cfg = config.MVPConfig()
    assert cfg.d_model == 1024
    assert cfg.N_e == 16
    assert cfg.k == 2
    assert cfg.d_ffn == 2048
    assert cfg.L == 4
    # Extended geometry constants required by extraction/distance
    assert cfg.d_ffn_dense == 4096
    assert cfg.d_c == 16
    assert cfg.H_kv == 8
    assert cfg.d_k == 128


def test_mvp_is_frozen() -> None:
    """Mutating any field of MVPConfig must raise FrozenInstanceError."""
    cfg = config.MVPConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.d_model = 2048  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.N_e = 32  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Total / active parameter estimator (Req 11: 452M / 100M)
# ---------------------------------------------------------------------------


def test_total_param_estimate() -> None:
    """compute_total_and_active returns the spec EXACT totals.

    Spec: wayfinder "4070 MVP Hyperparameter Set", Scenario
    "Closed-form parameter totals": total ≈ 452_329_984,
    active ≈ 100_008_448, P_router/layer ≈ 32_896 (the router term
    previously misclassified as rounding), all guarded via
    `pytest.approx(value, abs=...)`（浮点闭式）或精确 `==`（整数闭式）per §6 第 8 条.
    """
    cfg = config.MVPConfig()
    total, active = config.compute_total_and_active(cfg)

    assert total == 452_329_984, f"actual={total}"
    assert active == 100_008_448, f"actual={active}"
    # Router per layer: H_kv · (2·d_k·d_c + d_c) = 8 · (2·128·16 + 16) = 32_896
    router_per_layer = config._router_params_per_layer(cfg)
    assert router_per_layer == 32_896, f"actual={router_per_layer}"


def test_flops_per_layer_exact_33554432() -> None:
    """Per-layer MoE FLOPs == 33_554_432 exact.

    Spec: wayfinder "4070 MVP Hyperparameter Set", Scenario
    "Closed-form parameter totals": L × (4·2·d_model² + k·3·2·d_model·d_ffn)
    with SwiGLU counting 3 matrices (g, u, d).
    """
    cfg = config.MVPConfig()
    per_layer = 4 * 2 * cfg.d_model**2 + cfg.k * 3 * 2 * cfg.d_model * cfg.d_ffn
    flops_actual = config.flops_per_token(cfg, "MOE")

    # 结构恒等: 实现输出 == 闭式 L × per_layer
    assert flops_actual == cfg.L * per_layer, (
        f"impl={flops_actual} vs closed={cfg.L * per_layer}"
    )
    # 闭式锚: per_layer 变量 == 2^25 (SwiGLU 3-matrix closed form)
    assert per_layer == 33_554_432, f"actual={per_layer}"
    # 实现直钉常量: 实现输出 == 134_217_728 = 4 × 2^25 (MoE active forward FLOPs/token)
    assert flops_actual == 134_217_728, f"actual={flops_actual}"


def test_flops_total_exact_134217728() -> None:
    """Total MoE active FLOPs per token == 134_217_728 exact (spec closed form)."""
    flops_actual = config.flops_per_token(config.MVPConfig(), "MOE")
    assert flops_actual == 134_217_728, f"actual={flops_actual}"


def test_flops_routing_closed_form_66048() -> None:
    """Spec L420: `FLOPs_Routing^(l) = 4·d_c·H_kv·d_k + 2·N_e·d_c == 66_048` per layer.

    Integer closed form → bare `==` per `governance/spec.md` req-gov-1 §1
    (never `pytest.approx(..., abs=0)`, whose `rel=1e-12` default would scale
    with magnitude and defeat the 钉值零容差 intent).

    These spec literals previously had NO guarding test at all.
    """
    cfg = config.MVPConfig()
    H_kv, d_k, d_c, N_e = 8, cfg.d_k, cfg.d_c, cfg.N_e
    projection = 4 * d_c * H_kv * d_k  # 65_536
    gating = 2 * N_e * d_c  # 512
    flops_routing = projection + gating
    assert projection == 65_536, f"actual={projection}"
    assert gating == 512, f"actual={gating}"
    assert flops_routing == 66_048, f"actual={flops_routing}"
    # L = 4 layers → 264_192 FLOPs/token (integer closed form → bare ==).
    assert cfg.L * flops_routing == 264_192, f"actual={cfg.L * flops_routing}"


def test_flops_routing_ratio_within_allowance() -> None:
    """Spec L420: routing ratio ≈ 0.001968 → ≈ 0.20%, within the 0.3% allowance.

    Float closed form (involves division) → `pytest.approx(abs=...)` per
    `governance/spec.md` req-gov-1 §2.
    """
    cfg = config.MVPConfig()
    flops_routing = 4 * cfg.d_c * 8 * cfg.d_k + 2 * cfg.N_e * cfg.d_c
    core = 33_554_432  # FLOPs_MoE,core^(l) per spec L420
    ratio = flops_routing / core
    assert ratio == pytest.approx(0.001968, abs=1e-6), f"actual={ratio}"
    assert ratio == pytest.approx(0.0020, abs=1e-4), f"actual={ratio} (≈0.20%)"
    assert ratio < 0.003, f"actual={ratio} exceeds the 0.3% allowance"


def test_flops_routing_cross_req_net_delta_32() -> None:
    """Spec L422: net `+32 FLOPs = (128+144)·2 − 2·N_e·d_c = 544 − 512` ≈ 0.05%.

    Guards the cross-req consistency claim between Req 20's `FLOPs_Routing`
    and Req 17's `extract_C` accounting (66_080 − 66_048 = 32).
    """
    cfg = config.MVPConfig()
    projection = 4 * cfg.d_c * 8 * cfg.d_k
    macs_bias_l2 = 128 + 144
    extract_c_flops = projection + macs_bias_l2 * 2
    flops_routing = projection + 2 * cfg.N_e * cfg.d_c
    net_delta = extract_c_flops - flops_routing
    assert extract_c_flops == 66_080, f"actual={extract_c_flops}"
    assert net_delta == 32, f"actual={net_delta}"
    assert net_delta / flops_routing == pytest.approx(0.0005, abs=1e-4), (
        f"actual={net_delta / flops_routing} (≈0.05% of FLOPs_Routing)"
    )


def test_active_flops_parity() -> None:
    """flops_per_token(MOE_MVP) must equal flops_per_token(DENSE_4096) within the agreed accounting."""
    cfg = config.MVPConfig()
    moe_flops = config.flops_per_token(cfg, arch="MOE")
    dense_flops = config.flops_per_token(cfg, arch="DENSE")

    # Strict parity per Req 11 / Req 19
    assert moe_flops == dense_flops, (
        f"MoE active FLOPs ({moe_flops}) must equal Dense 4096 FLOPs ({dense_flops})"
    )


# ---------------------------------------------------------------------------
# Package-level canonical name (Req 1: Naming And Alias Convention)
# ---------------------------------------------------------------------------


def test_canonical_name() -> None:
    """`decompmoe.__canonical_name__` must be the literal string "DecompMoE"."""
    assert decompmoe.__canonical_name__ == "DecompMoE"


def test_alias_adopted() -> None:
    """`decompmoe.__alias__` must be the literal string "GeoMoE" for documentation continuity."""
    assert decompmoe.__alias__ == "GeoMoE"


def test_geomee_not_used_as_code_identifier() -> None:
    """`GeoMoE` MUST appear only as string literal/docstring, never as a Python identifier.

    Principle guard (NAR-1 wording: "The alias MUST appear only in design prose and
    never as a code identifier."). Source-tree audit uses `ast.walk` to enumerate
    every Name / FunctionDef.name / ClassDef.name / Attribute.attr in
    `src/decompmoe/**/*.py` EXCLUDING `__init__.py` (the latter legitimately
    exposes `__alias__ = "GeoMoE"` as a public string constant). Any identifier
    named `GeoMoE` or starting with `GeoMoE` in any other module violates the
    principle.

    This is review-based enforcement (no runtime regression risk because the
    implementation never imports `GeoMoE` as a symbol), but it guards against
    accidental future drift such as `class GeoMoEFoo` or `def GeoMoE_bar()`.
    """
    import ast
    import pathlib

    pkg_root = pathlib.Path(decompmoe.__file__).resolve().parent
    violations: list[tuple[str, int, str]] = []

    for py_path in sorted(pkg_root.glob("**/*.py")):
        if py_path.name == "__init__.py":
            # `__init__.py` is the single canonical home for `__alias__ = "GeoMoE"`
            # and the alias docstring; skip it.
            continue
        try:
            tree = ast.parse(py_path.read_text(encoding="utf-8"))
        except SyntaxError:
            # Don't mask unrelated syntax errors with this principle guard.
            continue
        for node in ast.walk(tree):
            ident: str | None = None
            kind: str | None = None
            if isinstance(node, ast.Name) and node.id.startswith("GeoMoE"):
                ident, kind = node.id, "Name"
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name.startswith("GeoMoE"):
                ident, kind = node.name, type(node).__name__
            elif isinstance(node, ast.Attribute) and node.attr.startswith("GeoMoE"):
                ident, kind = node.attr, "Attribute"
            if ident is not None:
                violations.append((str(py_path.relative_to(pkg_root.parent)), node.lineno, f"{kind}={ident}"))

    assert not violations, (
        "GeoMoE must not appear as a Python identifier outside `__init__.py`. "
        "Per NAR-1 wording: 'The alias MUST appear only in design prose and never "
        "as a code identifier.' Violations:\n"
        + "\n".join(f"  {p}:L{ln} {kind}" for p, ln, kind in violations)
    )
