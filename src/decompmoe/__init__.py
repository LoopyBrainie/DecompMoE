"""DecompMoE — Decomposed Mixture of Experts (canonical name).

The package provides type-safe contracts, frozen MVP hyperparameters, and
pure-function mathematical primitives that materialize the 21 Requirements ×
34 Scenarios of `openspec/specs/wayfinder/spec.md`. It is formalize-only:
no executable forward/backward pass; downstream changes implement the runtime.

Naming convention (Req 1):
    - canonical name (code identifiers, public API): "DecompMoE"
    - alias (design prose, docstrings only): "GeoMoE"

This module exposes the canonical name and the public `__all__` list so that
downstream consumers can introspect the package.
"""
from __future__ import annotations

__version__ = "0.1.0"
__canonical_name__ = "DecompMoE"
__alias__ = "GeoMoE"

# Public API surface — populated lazily by submodules. Listed statically here
# so `dir(decompmoe)` and `from decompmoe import *` are stable.
__all__ = [
    "__version__",
    "__canonical_name__",
    "__alias__",
]