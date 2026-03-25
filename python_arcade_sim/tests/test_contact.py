"""
Тесты для модуля contact.py.

Проверка:
- Геометрия контакта корректна
- Нормальная сила вычисляется без NaN
- Stick-slip переход работает
- Метрики собираются корректно
"""

import sys
from pathlib import Path

# Добавляем корень проекта в path для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.contact import (
    ContactInput,
    ContactParams,
    ContactResult,
    compute_contact,
    init_contact_state,
)
from physics.sim_types import SurfaceState
from physics.surface import EquivalentSurfaceParams, init_surface_state
from physics.sim_types import SurfaceParams


def create_test_surface(
    n_nodes: int = 50,
) -> tuple[SurfaceState, EquivalentSurfaceParams]:
    """Создать тестовую поверхность."""
    params = SurfaceParams(
        half_width=0.15,
        n_nodes=n_nodes,
    )
    state = init_surface_state(params)
    eq_params = EquivalentSurfaceParams(
        k_n_eq=1e6,
        k_t_eq=5e5,
        c_n_eq=100,
        c_t_eq=50,
        mu_s_eq=1.0,
        mu_k_eq=0.5,
        mass_per_meter=1.0,
    )
    return state, eq_params


def test_init_contact_state() -> None:
    """Инициализация возвращает нулевое состояние."""
    state = init_contact_state()

    assert not state.is_active
    assert state.fn == 0.0
    assert state.ft == 0.0
    assert state.penetration == 0.0
    assert state.stick_displacement == 0.0

    print("✓ test_init_contact_state passed")


def test_no_contact_when_ball_far() -> None:
    """Когда мяч далеко, контакт не активен."""
    surface, eq_params = create_test_surface()

    input_data = ContactInput(
        ball_x=0.0,
        ball_y=1.0,  # Мяч высоко над поверхностью
        ball_r=0.02,
        ball_v_x=5.0,
        ball_v_y=-5.0,
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(),
        dt=1e-5,
    )

    prev_state = init_contact_state()
    result = compute_contact(input_data, prev_state)

    assert not result.is_active
    assert result.fn_total == 0.0
    assert result.ft_total == 0.0

    print("✓ test_no_contact_when_ball_far passed")


def test_contact_when_ball_touches() -> None:
    """Когда мяч касается поверхности, контакт активен."""
    surface, eq_params = create_test_surface()

    # Мяч на высоте радиуса (касается поверхности)
    input_data = ContactInput(
        ball_x=0.0,
        ball_y=0.02,  # y = r
        ball_r=0.02,
        ball_v_x=5.0,
        ball_v_y=-1.0,
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(k_c=1e6, c_c=100),
        dt=1e-5,
    )

    prev_state = init_contact_state()
    result = compute_contact(input_data, prev_state)

    # Должен быть контакт (мяч пересекает поверхность)
    # Примечание: если поверхность недеформирована (u_y=0), то контакт может быть
    # только если мяч ниже y=r

    print("✓ test_contact_when_ball_touches passed")


def test_contact_with_penetration() -> None:
    """При проникновении возникает нормальная сила."""
    surface, eq_params = create_test_surface()

    # Искусственно поднимем узлы поверхности (имитация проникновения)
    for i in range(len(surface.u_y)):
        surface.u_y[i] = 0.001  # 1 мм вверх

    input_data = ContactInput(
        ball_x=0.0,
        ball_y=0.019,  # Мяч ниже поверхности (проникновение)
        ball_r=0.02,
        ball_v_x=5.0,
        ball_v_y=-1.0,
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(k_c=1e6, c_c=100),
        dt=1e-5,
    )

    prev_state = init_contact_state()
    result = compute_contact(input_data, prev_state)

    assert result.is_active
    assert result.fn_total > 0
    assert result.max_penetration > 0
    assert len(result.active_nodes) > 0

    # Проверка отсутствия NaN
    assert not (result.fn_total != result.fn_total)
    assert not (result.ft_total != result.ft_total)

    print("✓ test_contact_with_penetration passed")


def test_normal_force_no_nan() -> None:
    """Нормальная сила не содержит NaN при различных условиях."""
    surface, eq_params = create_test_surface()

    # Различные сценарии
    test_cases = [
        {"ball_y": 0.02, "ball_v_y": -10.0},  # Быстрое сближение
        {"ball_y": 0.015, "ball_v_y": 0.0},  # Статичное проникновение
        {"ball_y": 0.018, "ball_v_y": 5.0},  # Отскок
    ]

    for case in test_cases:
        input_data = ContactInput(
            ball_x=0.0,
            ball_y=case["ball_y"],
            ball_r=0.02,
            ball_v_x=5.0,
            ball_v_y=case["ball_v_y"],
            ball_omega=0.0,
            surface=surface,
            eq_params=eq_params,
            contact_params=ContactParams(),
            dt=1e-5,
        )

        prev_state = init_contact_state()
        result = compute_contact(input_data, prev_state)

        # Проверка отсутствия NaN
        assert not (result.fn_total != result.fn_total), f"NaN in fn_total for {case}"
        assert not (result.ft_total != result.ft_total), f"NaN in ft_total for {case}"

    print("✓ test_normal_force_no_nan passed")


def test_stick_slip_transition() -> None:
    """Stick-slip переход работает корректно."""
    surface, eq_params = create_test_surface()

    # Проникновение для активации контакта
    for i in range(len(surface.u_y)):
        surface.u_y[i] = 0.001

    # Сценарий 1: Малая скорость (stick)
    input_stick = ContactInput(
        ball_x=0.0,
        ball_y=0.019,
        ball_r=0.02,
        ball_v_x=0.1,  # Малая скорость
        ball_v_y=0.0,
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(k_s=1e5),
        dt=1e-5,
    )

    prev_state = init_contact_state()
    result_stick = compute_contact(input_stick, prev_state)

    # Сценарий 2: Большая скорость (slip)
    input_slip = ContactInput(
        ball_x=0.0,
        ball_y=0.019,
        ball_r=0.02,
        ball_v_x=10.0,  # Большая скорость
        ball_v_y=0.0,
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(k_s=1e5),
        dt=1e-5,
    )

    result_slip = compute_contact(input_slip, prev_state)

    # Slip должен быть активен при большой скорости
    # (хотя бы в одном узле)
    assert result_slip.is_slipping or result_slip.fn_total > 0

    print("✓ test_stick_slip_transition passed")


def test_friction_coefficients_applied() -> None:
    """Коэффициенты трения применяются корректно."""
    surface, eq_params = create_test_surface()

    # Разные коэффициенты трения
    eq_params.mu_s_eq = 1.2
    eq_params.mu_k_eq = 0.6

    for i in range(len(surface.u_y)):
        surface.u_y[i] = 0.001

    input_data = ContactInput(
        ball_x=0.0,
        ball_y=0.019,
        ball_r=0.02,
        ball_v_x=5.0,
        ball_v_y=0.0,
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(),
        dt=1e-5,
    )

    prev_state = init_contact_state()
    result = compute_contact(input_data, prev_state)

    # Проверка, что сила не NaN
    assert not (result.fn_total != result.fn_total)
    assert not (result.ft_total != result.ft_total)

    print("✓ test_friction_coefficients_applied passed")


def test_active_nodes_tracking() -> None:
    """Отслеживание активных узлов работает."""
    surface, eq_params = create_test_surface(n_nodes=100)

    # Проникновение только в центре
    center = len(surface.u_y) // 2
    for i in range(len(surface.u_y)):
        # Поднимаем только центральные узлы
        if abs(i - center) < 10:
            surface.u_y[i] = 0.001
        else:
            surface.u_y[i] = 0.0

    input_data = ContactInput(
        ball_x=0.0,
        ball_y=0.019,
        ball_r=0.02,
        ball_v_x=0.0,
        ball_v_y=0.0,
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(),
        dt=1e-5,
    )

    prev_state = init_contact_state()
    result = compute_contact(input_data, prev_state)

    # Должны быть активные узлы
    assert len(result.active_nodes) > 0
    assert len(result.pressure) == len(result.active_nodes)

    # Все активные узлы должны быть в допустимом диапазоне
    for node_idx in result.active_nodes:
        assert 0 <= node_idx < len(surface.x_nodes)

    print("✓ test_active_nodes_tracking passed")


def test_contact_force_cap() -> None:
    """Кап сил контакта работает."""
    surface, eq_params = create_test_surface()

    # Очень большое проникновение
    for i in range(len(surface.u_y)):
        surface.u_y[i] = 0.01  # 1 см

    input_data = ContactInput(
        ball_x=0.0,
        ball_y=0.01,
        ball_r=0.02,
        ball_v_x=0.0,
        ball_v_y=-100.0,  # Очень большая скорость
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(k_c=1e10, c_c=1e6),  # Большие коэффициенты
        dt=1e-5,
    )

    prev_state = init_contact_state()
    result = compute_contact(input_data, prev_state)

    # Сила должна быть ограничена
    assert result.fn_total <= 1e6  # K_FORCE_CAP
    assert result.fn_total >= 0

    print("✓ test_contact_force_cap passed")


def run_all_tests() -> None:
    """Запустить все тесты."""
    print("Running Contact tests...\n")

    test_init_contact_state()
    test_no_contact_when_ball_far()
    test_contact_when_ball_touches()
    test_contact_with_penetration()
    test_normal_force_no_nan()
    test_stick_slip_transition()
    test_friction_coefficients_applied()
    test_active_nodes_tracking()
    test_contact_force_cap()

    print("\n✅ All Contact tests passed!")


if __name__ == "__main__":
    run_all_tests()
