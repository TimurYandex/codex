#!/usr/bin/env python3
"""
Запуск простых тестов всех модулей физики.

Использование:
    cd python_arcade_sim
    python physics/run_tests.py
"""

import sys
from pathlib import Path

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("Testing Physics Modules")
print("=" * 60)

# =============================================================================
# Тест physics.model
# =============================================================================

print("\n[1/3] Testing physics.model...")

from physics.model import PhysicsModel
from physics.sim_types import (
    BallParams,
    CollisionParams,
    QualityLevel,
    SimulationParams,
    SurfaceParams,
)

model = PhysicsModel()
print(f"  ✓ PhysicsModel created: mode={model.get_mode().value}")

params = SimulationParams(
    ball=BallParams(radius=0.02, mass=0.0027),
    surface=SurfaceParams(half_width=0.15, n_nodes=50),
    collision=CollisionParams(speed=10.0, angle=-30.0),
    quality=QualityLevel.NORMAL,
    time_scale=0.005,
)

model.reset(params)
print(f"  ✓ After reset: mode={model.get_mode().value}, n_nodes={len(model.surface.x_nodes)}")

for _ in range(10):
    model.step(1.0)

print(f"  ✓ After 10 steps: time={model.time:.6f}, history_points={len(model.get_history().points)}")

snapshot = model.get_render_snapshot()
print(f"  ✓ Snapshot: ball.x={snapshot.ball.x}, mode={snapshot.mode.value}")

# =============================================================================
# Тест physics.surface
# =============================================================================

print("\n[2/3] Testing physics.surface...")

from physics.surface import (
    compute_ball_surface_y,
    compute_equivalent_params,
    compute_internal_forces,
    init_surface_state,
)
from physics.sim_types import LayerParams, SpikeMode, SurfaceParams

params = SurfaceParams(
    layers=[
        LayerParams(
            title="Top",
            thickness=0.001,
            k_n=1e6,
            c_n=100,
            k_t=5e5,
            c_t=50,
            mu_s=1.0,
            mu_k=0.5,
            spike_mode=SpikeMode.NONE,
        ),
    ],
    half_width=0.15,
    n_nodes=50,
)

state = init_surface_state(params)
print(f"  ✓ init_surface_state: n_nodes={len(state.x_nodes)}, x_range=[{state.x_nodes[0]:.3f}, {state.x_nodes[-1]:.3f}]")

eq = compute_equivalent_params(params)
print(f"  ✓ compute_equivalent_params: k_n_eq={eq.k_n_eq:.2f}, mu_s_eq={eq.mu_s_eq:.2f}")

forces = compute_internal_forces(state, params, eq)
print(f"  ✓ compute_internal_forces: n_forces={len(forces.f_y)}, all_zero={all(f == 0 for f in forces.f_y)}")

y_center = compute_ball_surface_y(ball_x=0.0, ball_y=0.02, radius=0.02, node_x=0.0)
y_edge = compute_ball_surface_y(ball_x=0.0, ball_y=0.02, radius=0.02, node_x=0.02)
print(f"  ✓ compute_ball_surface_y: y_center={y_center:.6f}, y_edge={y_edge:.6f}")

# =============================================================================
# Тест physics.spikes
# =============================================================================

print("\n[3/3] Testing physics.spikes...")

from physics.spikes import (
    SpikesInput,
    apply_spikes_to_friction,
    compute_spikes_dynamics,
    init_spikes_state,
)
from physics.surface import SpikeEquivalentParams
from physics.sim_types import SpikeMode

state = init_spikes_state()
print(f"  ✓ init_spikes_state: theta={state.theta}, mu_multiplier={state.mu_multiplier}")

params = SpikeEquivalentParams(k_sh=1000.0, h=0.001, theta_max=0.5)
input_params = SpikesInput(
    spike_params=params,
    mode=SpikeMode.OUT,
    ft_contact=10.0,
    v_rel_t=5.0,
    dt=1e-5,
)

output = compute_spikes_dynamics(state, input_params)
print(f"  ✓ compute_spikes_dynamics: theta={output.theta:.6f}, mu_multiplier={output.mu_multiplier:.4f}")

mu_s_new, mu_k_new = apply_spikes_to_friction(1.0, 0.5, output)
print(f"  ✓ apply_spikes_to_friction: mu_s={mu_s_new:.4f}, mu_k={mu_k_new:.4f}")

# =============================================================================
# Итог
# =============================================================================

print("\n" + "=" * 60)
print("✅ All physics modules tested successfully!")
print("=" * 60)
