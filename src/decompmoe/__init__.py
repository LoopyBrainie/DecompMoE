"""DecompMoE — Decomposed Mixture of Experts (canonical name).

The package provides type-safe contracts, frozen MVP hyperparameters, and
pure-function mathematical primitives that materialize the geometric-routing
design of `openspec/specs/wayfinder/spec.md` into Python. It is formalize-only:
no executable forward/backward pass; downstream changes implement the runtime.

Naming convention (Req 1):
    - canonical name (code identifiers, public API): "DecompMoE"
    - alias (design prose, docstrings only): "GeoMoE"

The public surface is the de-duplicated union of the 13 submodules' `__all__`
entries: 76 names, plus the 3 dunders below for 79 in total (req-1).
"""

from __future__ import annotations


# ---- public surface: the union of the 13 submodules' __all__ (req-1) ----
from decompmoe.beta import (  # noqa: F401
    BETA_MAX,
    BETA_MIN,
    MAX_GRAD_PER_C,
    MAX_GRAD_PER_GAMMA,
    MAX_GRAD_PER_GAMMA_PHASE4,
    inverse_temperature,
    phase4_inverse_temperature,
)
from decompmoe.config import (  # noqa: F401
    ArchKind,
    MVPConfig,
    compute_total_and_active,
    flops_per_token,
)
from decompmoe.contracts import (  # noqa: F401
    BlockAdapter,
    GeometricRouter,
    TerritoryHolder,
)
from decompmoe.distance import (  # noqa: F401
    logit,
    squared_chord,
)
from decompmoe.experts import (  # noqa: F401
    ExpertPool,
    SwiGLUExpert,
)
from decompmoe.extraction import (  # noqa: F401
    CentroidDriver,
    Phase,
    extract_C,
    territory_seeding,
)
from decompmoe.gating import (  # noqa: F401
    local_softmax,
    topk_mask_with_neg_inf,
)
from decompmoe.loss import (  # noqa: F401
    ALPHA,
    LAMBDA_MAX,
    L_total,
    LossParts,
    compute_L_sep,
)
from decompmoe.metrics import (  # noqa: F401
    CG,
    D_chord,
    L_sep,
    MCI,
    OFFLINE,
    REALTIME,
    R_H,
    SP,
    S_load,
    UR,
    flops_per_token,
)
from decompmoe.safeguards import (  # noqa: F401
    BETA_SATURATION_HALVE,
    BETA_SATURATION_WARN,
    DEAD_EXPERT_CONSEC_STEPS,
    LOSS_SPIKE_LR_SCALE,
    LOSS_SPIKE_RATIO,
    RESURRECTION_RATE_LIMIT_STEPS,
    STEP_ORDER,
    apply_resurrection_beta_decay,
    beta_saturation_global_halve,
    beta_saturation_warning,
    clip_global_grad_norm_,
    loss_spike_defense,
    nan_ladder,
    resurrect_expert,
    resurrection_perturb_distribution,
    should_resurrect,
)
from decompmoe.schedule import (  # noqa: F401
    advisory_signals,
    beta_effective,
    gamma_reset_for_phase2,
    gamma_reset_for_phase4,
    phase_beta_box,
    phase_beta_max,
    phase_boundaries,
    phase_id,
    phase_step_frozen_names,
    should_reset_adam,
)
from decompmoe.sphere import (  # noqa: F401
    VORONOI_AREA_SAMPLES,
    VORONOI_AREA_SEED,
    canonical_voronoi_angle,
    spherical_l2_normalize,
    voronoi_angle,
)
from decompmoe.viz import (  # noqa: F401
    DcHeatmap,
    PCA3D,
    PlantUMLDiagram,
    TensorBoardDashboard,
    TrajectoryAnimation,
    Voronoi2D,
)

__version__ = "0.1.0"
__canonical_name__ = "DecompMoE"
__alias__ = "GeoMoE"

# Re-bind after the import block: `flops_per_token` is declared by both
# `config` and `metrics`, and the import block above is alphabetical, so
# `metrics` (the passthrough mirror) would otherwise win on import order
# alone. req-1 makes `config` canonical; doing it explicitly here keeps the
# binding independent of how the block is ordered or regenerated.
from decompmoe.config import flops_per_token  # noqa: E402,F401

# Stable public API surface (req-1).
__all__ = [
    "__version__",
    "__canonical_name__",
    "__alias__",
    "ALPHA",
    "ArchKind",
    "BETA_MAX",
    "BETA_MIN",
    "BETA_SATURATION_HALVE",
    "BETA_SATURATION_WARN",
    "BlockAdapter",
    "CG",
    "CentroidDriver",
    "DEAD_EXPERT_CONSEC_STEPS",
    "D_chord",
    "DcHeatmap",
    "ExpertPool",
    "GeometricRouter",
    "LAMBDA_MAX",
    "LOSS_SPIKE_LR_SCALE",
    "LOSS_SPIKE_RATIO",
    "L_sep",
    "L_total",
    "LossParts",
    "MAX_GRAD_PER_C",
    "MAX_GRAD_PER_GAMMA",
    "MAX_GRAD_PER_GAMMA_PHASE4",
    "MCI",
    "MVPConfig",
    "OFFLINE",
    "PCA3D",
    "Phase",
    "PlantUMLDiagram",
    "REALTIME",
    "RESURRECTION_RATE_LIMIT_STEPS",
    "R_H",
    "SP",
    "STEP_ORDER",
    "S_load",
    "SwiGLUExpert",
    "TensorBoardDashboard",
    "TerritoryHolder",
    "TrajectoryAnimation",
    "UR",
    "VORONOI_AREA_SAMPLES",
    "VORONOI_AREA_SEED",
    "Voronoi2D",
    "advisory_signals",
    "apply_resurrection_beta_decay",
    "beta_effective",
    "beta_saturation_global_halve",
    "beta_saturation_warning",
    "canonical_voronoi_angle",
    "clip_global_grad_norm_",
    "compute_L_sep",
    "compute_total_and_active",
    "extract_C",
    "flops_per_token",
    "gamma_reset_for_phase2",
    "gamma_reset_for_phase4",
    "inverse_temperature",
    "local_softmax",
    "logit",
    "loss_spike_defense",
    "nan_ladder",
    "phase4_inverse_temperature",
    "phase_beta_box",
    "phase_beta_max",
    "phase_boundaries",
    "phase_id",
    "phase_step_frozen_names",
    "resurrect_expert",
    "resurrection_perturb_distribution",
    "should_reset_adam",
    "should_resurrect",
    "spherical_l2_normalize",
    "squared_chord",
    "territory_seeding",
    "topk_mask_with_neg_inf",
    "voronoi_angle",
]
