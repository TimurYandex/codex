"""
Физическое ядро симулятора.

Не зависит от arcade. Используется только для расчёта физики.
"""

from .contact import (
    ContactInput,
    ContactParams,
    ContactResult,
    compute_contact,
    init_contact_state,
)
from .model import PhysicsModel
from .spikes import (
    SpikesInput,
    SpikesOutput,
    apply_spikes_to_friction,
    compute_spikes_dynamics,
    init_spikes_state,
)
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
from .sim_types import (
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
    # Contact
    "ContactInput",
    "ContactParams",
    "ContactResult",
    "compute_contact",
    "init_contact_state",
    # Model
    "PhysicsModel",
    # Spikes
    "SpikesInput",
    "SpikesOutput",
    "compute_spikes_dynamics",
    "init_spikes_state",
    "apply_spikes_to_friction",
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
