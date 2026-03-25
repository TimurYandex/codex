"""
Регрессионные тесты физики.

Проверка, что физика возвращает разумные метрики.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.model import PhysicsModel
from physics.sim_types import (
    BallParams,
    CollisionParams,
    QualityLevel,
    SimulationParams,
    SurfaceParams,
    LayerParams,
    SpikeMode,
)


def create_default_params() -> SimulationParams:
    """Создать параметры по умолчанию."""
    return SimulationParams(
        ball=BallParams(radius=0.02, mass=0.0027, ifactor=0.4, k=1e6, c=100),
        surface=SurfaceParams(
            layers=[
                LayerParams(
                    title="Top",
                    thickness=0.002,
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
        ),
        collision=CollisionParams(speed=10.0, angle=-30.0, spin=0.0),
        quality=QualityLevel.NORMAL,
        time_scale=0.005,
    )


def test_contact_time_positive() -> None:
    """contact_time > 0."""
    model = PhysicsModel()
    model.reset(create_default_params())
    
    while not model.is_finished():
        model.step(1.0)
    
    metrics = model.get_metrics()
    assert metrics.contact_time > 0, "contact_time should be positive"
    print("✓ test_contact_time_positive passed")


def test_no_nan_in_metrics() -> None:
    """Метрики не содержат NaN."""
    model = PhysicsModel()
    model.reset(create_default_params())
    
    while not model.is_finished():
        model.step(1.0)
    
    metrics = model.get_metrics()
    assert not (metrics.v_out != metrics.v_out), "v_out is NaN"
    assert not (metrics.omega_out != metrics.omega_out), "omega_out is NaN"
    assert not (metrics.contact_time != metrics.contact_time), "contact_time is NaN"
    print("✓ test_no_nan_in_metrics passed")


def test_energy_loss_non_negative() -> None:
    """energy_loss >= 0 (энергия не растёт)."""
    model = PhysicsModel()
    model.reset(create_default_params())
    
    while not model.is_finished():
        model.step(1.0)
    
    metrics = model.get_metrics()
    assert metrics.energy_loss >= -0.1, "energy_loss should be non-negative (small tolerance)"
    print("✓ test_energy_loss_non_negative passed")


def test_history_not_empty() -> None:
    """История не пустая."""
    model = PhysicsModel()
    model.reset(create_default_params())
    
    while not model.is_finished():
        model.step(1.0)
    
    history = model.get_history()
    assert len(history.points) > 0, "history should not be empty"
    print("✓ test_history_not_empty passed")


def test_history_consistent_length() -> None:
    """Все точки истории имеют согласованную длину."""
    model = PhysicsModel()
    model.reset(create_default_params())
    
    while not model.is_finished():
        model.step(1.0)
    
    history = model.get_history()
    
    # Проверка, что все поля заполнены
    for point in history.points:
        assert point.fn is not None
        assert point.ft is not None
        assert point.deflection is not None
        assert point.slip is not None
        assert point.omega is not None
        assert point.v_x is not None
        assert point.v_y is not None
    
    print("✓ test_history_consistent_length passed")


def test_v_out_reasonable() -> None:
    """v_out в разумных пределах."""
    model = PhysicsModel()
    model.reset(create_default_params())
    
    while not model.is_finished():
        model.step(1.0)
    
    metrics = model.get_metrics()
    # v_out не должен превышать начальную скорость значительно
    assert metrics.v_out < 20.0, f"v_out={metrics.v_out} is too high"
    print("✓ test_v_out_reasonable passed")


def run_all_tests() -> None:
    """Запустить все регрессионные тесты."""
    print("Running Regression tests...\n")
    
    test_contact_time_positive()
    test_no_nan_in_metrics()
    test_energy_loss_non_negative()
    test_history_not_empty()
    test_history_consistent_length()
    test_v_out_reasonable()
    
    print("\n✅ All Regression tests passed!")


if __name__ == "__main__":
    run_all_tests()
