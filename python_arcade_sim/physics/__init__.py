"""
Физическое ядро симулятора.

Не зависит от arcade. Используется только для расчёта физики.
"""

from .model import PhysicsModel
from .surface import (
    EquivalentSurfaceParams,
    SpikeEquivalentParams,
    SurfaceForces,
    compute_ball_surface_y,
    compute_equivalent_params,
    compute_internal_forces,
    init_surface_state,
    integrate_surface,
)
from .types import (
    BallParams,
    BallState,
    CollisionParams,
    ContactState,
    HistoryPoint,
    LayerParams,
    QualityLevel,
    RenderSnapshot,
    SimulationHistory,
    SimulationMetrics,
    SimulationMode,
    SimulationParams,
    SpikeMode,
    SpikesState,
    SurfaceParams,
    SurfaceState,
)

__all__ = [
    # Model
    "PhysicsModel",
    # Surface
    "EquivalentSurfaceParams",
    "SpikeEquivalentParams",
    "SurfaceForces",
    "compute_equivalent_params",
    "compute_internal_forces",
    "integrate_surface",
    "init_surface_state",
    "compute_ball_surface_y",
    # Types
    "BallParams",
    "BallState",
    "CollisionParams",
    "ContactState",
    "HistoryPoint",
    "LayerParams",
    "QualityLevel",
    "RenderSnapshot",
    "SimulationHistory",
    "SimulationMetrics",
    "SimulationMode",
    "SimulationParams",
    "SpikeMode",
    "SpikesState",
    "SurfaceParams",
    "SurfaceState",
]
