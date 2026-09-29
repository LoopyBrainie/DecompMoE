"""Tests for `decompmoe.viz`: 6 Protocol stubs + IMPLEMENTATION_STACK.

ST-12 / Req 21.
"""
from __future__ import annotations

import pytest

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
    """PCA3D.camera_angles must equal (25.0, 135.0).

    Float closed-form → `pytest.approx(abs=...)` per `governance/spec.md`
    req-gov-1 §2. Disclosing the cost: both constants are exactly representable
    (`0x1.9000000000000p+4`, `0x1.0e00000000000p+7`), so obligation 2's
    "carries floating-point rounding" rationale does not literally bite; the
    migration is compliance-driven and marginally weaker than `==`.
    """
    assert viz.PCA3D.camera_angles[0] == pytest.approx(25.0, abs=1e-12), (
        f"actual={viz.PCA3D.camera_angles[0]}"
    )
    assert viz.PCA3D.camera_angles[1] == pytest.approx(135.0, abs=1e-12), (
        f"actual={viz.PCA3D.camera_angles[1]}"
    )