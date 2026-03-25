"""
Тесты для модуля surface.py.

Проверка:
- после инициализации массивы имеют корректные размеры
- при нулевых скоростях/смещениях внутренние силы не содержат NaN
- эквивалентные параметры вычисляются корректно
"""

import sys
from pathlib import Path

# Добавляем корень проекта в path для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.surface import (
    EquivalentSurfaceParams,
    compute_equivalent_params,
    compute_internal_forces,
    compute_ball_surface_y,
    init_surface_state,
    integrate_surface,
)
from physics.types import LayerParams, SpikeMode, SurfaceParams


def create_test_surface_params() -> SurfaceParams:
    """Создать тестовые параметры поверхности."""
    return SurfaceParams(
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
                p=0.5,
            ),
            LayerParams(
                title="Base",
                thickness=0.005,
                k_n=2e6,
                c_n=200,
                k_t=1e6,
                c_t=100,
                mu_s=0.8,
                mu_k=0.4,
                spike_mode=SpikeMode.NONE,
                p=0.3,
            ),
        ],
        half_width=0.15,
        depth=0.01,
        n_nodes=100,
        fr_mul=1.0,
    )


def test_init_surface_state() -> None:
    """После инициализации массивы имеют корректные размеры."""
    params = create_test_surface_params()
    state = init_surface_state(params)
    
    # Проверка размеров
    assert len(state.x_nodes) == 100
    assert len(state.u_y) == 100
    assert len(state.u_x) == 100
    assert len(state.v_y) == 100
    assert len(state.v_x) == 100
    
    # Проверка диапазона X
    assert state.x_nodes[0] == -0.15
    assert state.x_nodes[-1] == 0.15
    
    # Проверка нулевых смещений
    assert all(u == 0.0 for u in state.u_y)
    assert all(u == 0.0 for u in state.u_x)
    
    print("✓ test_init_surface_state passed")


def test_compute_equivalent_params() -> None:
    """Эквивалентные параметры вычисляются корректно."""
    params = create_test_surface_params()
    eq = compute_equivalent_params(params)
    
    # Проверка, что параметры не нулевые
    assert eq.k_n_eq > 0
    assert eq.k_t_eq > 0
    assert eq.c_n_eq > 0
    assert eq.c_t_eq > 0
    assert eq.mu_s_eq > 0
    assert eq.mu_k_eq > 0
    
    # Проверка mu_k <= mu_s
    assert eq.mu_k_eq <= eq.mu_s_eq
    
    # Проверка массы
    assert eq.mass_per_meter > 0
    
    # Шипы не активны
    assert eq.spike_params is None
    
    print("✓ test_compute_equivalent_params passed")


def test_compute_internal_forces_no_nan() -> None:
    """При нулевых скоростях/смещениях силы не содержат NaN."""
    params = create_test_surface_params()
    state = init_surface_state(params)
    eq = compute_equivalent_params(params)
    
    forces = compute_internal_forces(state, params, eq)
    
    # Проверка размеров
    assert len(forces.f_y) == 100
    assert len(forces.f_x) == 100
    
    # Проверка отсутствия NaN
    assert all(not (f != f) for f in forces.f_y)  # NaN check
    assert all(not (f != f) for f in forces.f_x)
    
    # При нулевых смещениях силы должны быть нулевыми (или близкими)
    # (в данном случае они будут нулевыми, т.к. u=v=0)
    assert all(f == 0.0 for f in forces.f_y)
    assert all(f == 0.0 for f in forces.f_x)
    
    print("✓ test_compute_internal_forces_no_nan passed")


def test_compute_internal_forces_with_displacement() -> None:
    """При смещениях возникают возвращающие силы."""
    params = create_test_surface_params()
    state = init_surface_state(params)
    
    # Зададим смещения
    for i in range(len(state.u_y)):
        state.u_y[i] = 0.001  # 1 мм вверх
        state.u_x[i] = 0.0005  # 0.5 мм вправо
    
    eq = compute_equivalent_params(params)
    forces = compute_internal_forces(state, params, eq)
    
    # Проверка отсутствия NaN
    assert all(not (f != f) for f in forces.f_y)
    assert all(not (f != f) for f in forces.f_x)
    
    # Силы должны быть ненулевыми (возвращающая сила)
    # (проверяем хотя бы некоторые узлы в центре)
    center = len(forces.f_y) // 2
    assert forces.f_y[center] != 0.0 or forces.f_x[center] != 0.0
    
    print("✓ test_compute_internal_forces_with_displacement passed")


def test_integrate_surface() -> None:
    """Интегрирование обновляет скорости и позиции."""
    params = create_test_surface_params()
    state = init_surface_state(params)
    eq = compute_equivalent_params(params)
    
    # Зададим начальные смещения
    for i in range(len(state.u_y)):
        state.u_y[i] = 0.001
    
    forces = compute_internal_forces(state, params, eq)
    
    # Интегрирование
    dt = 1e-5
    integrate_surface(state, forces, eq, params, dt)
    
    # Проверка, что скорости изменились (стали ненулевыми)
    # (не все, но хотя бы некоторые)
    non_zero_vy = sum(1 for v in state.v_y if v != 0.0)
    assert non_zero_vy > 0
    
    # Проверка отсутствия NaN
    assert all(not (v != v) for v in state.v_y)
    assert all(not (v != v) for v in state.v_x)
    
    print("✓ test_integrate_surface passed")


def test_compute_ball_surface_y() -> None:
    """Вычисление Y поверхности мяча корректно."""
    ball_x = 0.0
    ball_y = 0.02  # Центр мяча на высоте радиуса
    radius = 0.02
    
    # В центре (dd = 0): y = ball_y - r = 0
    y_center = compute_ball_surface_y(ball_x, ball_y, radius, 0.0)
    assert abs(y_center - 0.0) < 1e-9
    
    # На краю (dd = r): y = ball_y - 0 = ball_y
    y_edge = compute_ball_surface_y(ball_x, ball_y, radius, radius)
    assert abs(y_edge - ball_y) < 1e-9
    
    # За пределами радиуса (защита от отрицательного подкорня)
    y_outside = compute_ball_surface_y(ball_x, ball_y, radius, radius * 1.1)
    assert y_outside == ball_y  # Возвращается ball_y при защите
    
    # Проверка отсутствия NaN
    assert not (y_center != y_center)
    assert not (y_edge != y_edge)
    assert not (y_outside != y_outside)
    
    print("✓ test_compute_ball_surface_y passed")


def test_equivalent_params_with_spikes() -> None:
    """Параметры шипов вычисляются для верхнего слоя с режимом out/in."""
    params = SurfaceParams(
        layers=[
            LayerParams(
                title="Spiky",
                thickness=0.001,
                k_n=1e6,
                c_n=100,
                k_t=5e5,
                c_t=50,
                mu_s=1.0,
                mu_k=0.5,
                spike_mode=SpikeMode.OUT,
                k_sh=1000.0,
                h=0.001,
                p=0.5,
            ),
        ],
        half_width=0.15,
        depth=0.01,
        n_nodes=100,
        fr_mul=1.0,
    )
    
    eq = compute_equivalent_params(params)
    
    # Шипы должны быть активны
    assert eq.spike_params is not None
    assert eq.spike_params.k_sh == 1000.0
    assert eq.spike_params.h == 0.001
    
    print("✓ test_equivalent_params_with_spikes passed")


def run_all_tests() -> None:
    """Запустить все тесты."""
    print("Running Surface tests...\n")
    
    test_init_surface_state()
    test_compute_equivalent_params()
    test_compute_internal_forces_no_nan()
    test_compute_internal_forces_with_displacement()
    test_integrate_surface()
    test_compute_ball_surface_y()
    test_equivalent_params_with_spikes()
    
    print("\n✅ All Surface tests passed!")


if __name__ == "__main__":
    run_all_tests()
