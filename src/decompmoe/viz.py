"""6-module visualization toolchain Protocol stubs (Req 21).

This module provides ONLY Protocol-level stubs. Real implementations are
deferred to a §6/§7 waiver change (per CLAUDE.md §7 Out-of-Scope).
"""
from __future__ import annotations

from typing import Final, Protocol

from torch import Tensor


IMPLEMENTATION_STACK: Final[frozenset[str]] = frozenset(
    {"matplotlib", "scikit-learn", "scipy", "imageio", "tensorboard", "plantuml"}
)


class PCA3D(Protocol):
    """3D PCA scatter with fixed camera angles (25°, 135°)."""

    camera_angles: tuple[float, float] = (25.0, 135.0)

    def render(self, centroids: Tensor, *, camera_angles: tuple[float, float] = (25.0, 135.0)) -> object:
        ...


class DcHeatmap(Protocol):
    """`D_c` heatmap with Optimal Leaf Ordering."""

    def render(self, d_c_matrix: Tensor) -> object:
        ...


class Voronoi2D(Protocol):
    """2D Voronoi tessellation with elliptical β fitting."""

    def render(self, centroids_2d: Tensor, betas: Tensor) -> object:
        ...


class TrajectoryAnimation(Protocol):
    """Trajectory animation with fixed `W_PCA` across frames."""

    def render(self, frames: list[Tensor], W_PCA: Tensor) -> object:
        ...


class TensorBoardDashboard(Protocol):
    """TensorBoard dashboard writer."""

    def write(self, scalars: dict[str, float], step: int) -> None:
        ...


class PlantUMLDiagram(Protocol):
    """PlantUML diagram documentation writer."""

    def render(self, components: dict[str, object]) -> str:
        ...


__all__ = [
    "PCA3D",
    "DcHeatmap",
    "Voronoi2D",
    "TrajectoryAnimation",
    "TensorBoardDashboard",
    "PlantUMLDiagram",
]