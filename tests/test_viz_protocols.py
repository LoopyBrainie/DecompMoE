"""Tests for `decompmoe.viz`: 6 Protocol stubs + IMPLEMENTATION_STACK.

ST-12 / Req 21.
"""
from __future__ import annotations

from decompmoe import viz


def test_viz_modules_complete() -> None:
    """viz.__all__ has exactly 6 module names."""
    assert len(viz.__all__) == 6
    expected = {
        "PCA3D", "DcHeatmap", "Voronoi2D", "TrajectoryAnimation",
        "TensorBoardDashboard", "PlantUMLDiagram",
    }
    assert set(viz.__all__) == expected


def test_viz_stack_pinned() -> None:
    """IMPLEMENTATION_STACK must be the 6-element frozenset per Req 21."""
    assert viz.IMPLEMENTATION_STACK == frozenset(
        {"matplotlib", "scikit-learn", "scipy", "imageio", "tensorboard", "plantuml"}
    )


def test_PCA_camera_angles_fixed() -> None:
    """PCA3D.camera_angles must equal (25.0, 135.0)."""
    assert viz.PCA3D.camera_angles == (25.0, 135.0)