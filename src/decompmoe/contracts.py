"""Wire-level Protocol stubs for DecompMoE's geometric routing chain.

Each Protocol class is a `typing.Protocol` with method signatures only — no
executable bodies. These represent the type-level contract between:

    - the geometric router chain (Req 3: Post-FFN mount, Req 4: head-aggregated
      routing, Req 16: Prefill/Decode share algorithm, Req 17: stateless
      per-frame recompute, Req 18: hardware / kernel friendliness)
    - the territory holder (Req 4: per-expert territory semantics)
    - the block adapter (Req 3: the Post-FFN mount point itself)

Hard invariants enforced by the Protocol surface:

    - `GeometricRouter` does NOT expose `kv_cache_c` (Req 16 forbids writing
      C_t into KV cache).
    - No method in `GeometricRouter` accepts a parameter named `w_i` (A4-2
      decision: w_i is reserved for post-aggregation mixing; never in logit).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from torch import Tensor


# ---------------------------------------------------------------------------
# GeometricRouter (Req 3, 4, 16, 17, 18)
# ---------------------------------------------------------------------------


@runtime_checkable
class GeometricRouter(Protocol):
    """Per-layer geometric routing chain (Post-FFN mount point).

    Required methods (from Req 3, 4, 16, 17):
        - `extract_C(K, V)`: stateless per-frame C recompute (Req 17).
          MUST NOT write to a KV cache (Req 16).
        - `gating_logits(C)`: per-layer territory routing logits.
          MUST NOT depend on a learnable per-expert scalar `w_i` (A4-2).
        - `route(x, logits)`: top-k sparse convex combination.

    NOTE: `kv_cache_c` is intentionally absent — `C_t^l` lives only in
    SRAM / registers during Decode (Req 16).
    """

    def extract_C(self, K: Tensor, V: Tensor) -> Tensor:
        """Stateless per-frame C extraction from (K, V).

        K, V: shape `[B, H_kv, N, d_k]`. Return: shape `[B, N, d_c]` on the
        unit sphere. No state is retained between calls (Req 17).
        """
        ...

    def gating_logits(self, C: Tensor) -> Tensor:
        """Compute per-expert gating logits from per-token territory C.

        C: shape `[B, N, d_c]`. Return: shape `[B, N, N_e]` of logits.
        """
        ...

    def route(self, x: Tensor, logits: Tensor) -> Tensor:
        """Top-k sparse convex combination.

        x:      shape `[B, N, d_model]` — residual stream input.
        logits: shape `[B, N, N_e]`. Return: shape `[B, N, d_model]` to be
        added back into the residual stream.
        """
        ...


# ---------------------------------------------------------------------------
# TerritoryHolder (Req 4)
# ---------------------------------------------------------------------------


@runtime_checkable
class TerritoryHolder(Protocol):
    """Per-layer territory state: per-expert centroids + auxiliary signals."""

    def territory_volume(self) -> float:
        """Sum of per-expert territory volumes (for monitoring)."""
        ...

    def active_territories(self) -> set[int]:
        """Indices of experts whose usage exceeds the resurrection boundary."""
        ...

    def coverage_balance_loss(self) -> Tensor:
        """Scalar coverage-balance loss (Switch-style, weighted by alpha)."""
        ...


# ---------------------------------------------------------------------------
# BlockAdapter (Req 3: Post-FFN mount point)
# ---------------------------------------------------------------------------


@runtime_checkable
class BlockAdapter(Protocol):
    """The Post-FFN adapter that consumes attention output and emits the
    routing chain's residual-stream add."""

    def forward_residual(self, x: Tensor) -> Tensor:
        """Apply the geometric routing chain and return its residual add."""
        ...


__all__ = [
    "GeometricRouter",
    "TerritoryHolder",
    "BlockAdapter",
]