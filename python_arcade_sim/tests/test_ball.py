"""
Тесты для модуля ball.py.

Проверка:
- Ускорения вычисляются корректно
- Интегратор работает без NaN
- Энергетическая защита срабатывает
- Пост-контактный полёт корректен
"""

import sys
from pathlib import Path

# Добавляем корень проекта в path для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.ball import (
    BallForces,
    clamp_rebound,
    clamp_rebound_priority,
    compute_ball_accelerations,
    compute_ball_kinetic_energy,
    integrate_ball,
    init_ball_state,
    step_ball_post_flight,
)
from physics.sim_types import BallParams


def create_default_ball_params() -> BallParams:
    """Создать параметры мяча по умолчанию."""
    return BallParams(
        radius=0.02,
        mass=0.0027,
        ifactor=0.4,  # Сплошной шар
        k=1e6,
        c=100,
    )


def test_init_ball_state() -> None:
    """Инициализация возвращает состояние с заданными параметрами."""
    state = init_ball_state(x=1.0, y=2.0, v_x=3.0, v_y=4.0, omega=5.0)

    assert state.x == 1.0
    assert state.y == 2.0
    assert state.v_x == 3.0
    assert state.v_y == 4.0
    assert state.omega == 5.0
    assert state.phi == 0.0

    print("✓ test_init_ball_state passed")


def test_compute_ball_accelerations() -> None:
    """Ускорения вычисляются корректно."""
    params = create_default_ball_params()
    state = init_ball_state()
    forces = BallForces(fn=1.0, ft=0.5)

    a_x, a_y, omega_dot = compute_ball_accelerations(state, params, forces)

    # Проверка формул
    m = params.mass
    r = params.radius
    I = params.ifactor * m * r * r

    expected_a_x = forces.ft / m
    expected_a_y = forces.fn / m - 9.81  # G
    expected_omega_dot = -(forces.ft * r) / I

    assert abs(a_x - expected_a_x) < 1e-6
    assert abs(a_y - expected_a_y) < 1e-6
    assert abs(omega_dot - expected_omega_dot) < 1e-6

    print("✓ test_compute_ball_accelerations passed")


def test_compute_ball_accelerations_no_forces() -> None:
    """Без сил только гравитация."""
    params = create_default_ball_params()
    state = init_ball_state()
    forces = BallForces(fn=0.0, ft=0.0)

    a_x, a_y, omega_dot = compute_ball_accelerations(state, params, forces)

    # Только гравитация
    assert abs(a_x) < 1e-9
    assert abs(a_y + 9.81) < 1e-6  # a_y = -G
    assert abs(omega_dot) < 1e-9

    print("✓ test_compute_ball_accelerations_no_forces passed")


def test_integrate_ball() -> None:
    """Интегрирование обновляет скорости и позиции."""
    params = create_default_ball_params()
    state = init_ball_state(x=0.0, y=1.0, v_x=1.0, v_y=0.0, omega=0.0)
    forces = BallForces(fn=0.0, ft=0.0)

    accelerations = compute_ball_accelerations(state, params, forces)
    dt = 0.01

    integrate_ball(state, params, accelerations, dt)

    # После интегрирования:
    # v_y = 0 + (-9.81) * 0.01 = -0.0981
    # y = 1.0 + v_y_new * 0.01 ≈ 1.0 - 0.001

    assert abs(state.v_y + 9.81 * dt) < 1e-6
    assert state.y < 1.0  # Мяч упал
    assert state.x > 0.0  # Мяч движется вправо

    # Проверка отсутствия NaN
    assert not (state.x != state.x)
    assert not (state.y != state.y)
    assert not (state.v_x != state.v_x)
    assert not (state.v_y != state.v_y)

    print("✓ test_integrate_ball passed")


def test_integrate_ball_with_spin() -> None:
    """Вращение влияет на угловую скорость."""
    params = create_default_ball_params()
    state = init_ball_state(v_x=5.0, v_y=0.0, omega=0.0)

    # Сила трения создаёт вращение
    forces = BallForces(fn=10.0, ft=-5.0)  # Ft < 0 → вращение по часовой

    accelerations = compute_ball_accelerations(state, params, forces)
    dt = 0.001

    integrate_ball(state, params, accelerations, dt)

    # Отрицательная Ft должна создать положительное omega_dot
    # (вращение против часовой по нашей конвенции)
    assert state.omega > 0  # Вращение изменилось

    print("✓ test_integrate_ball_with_spin passed")


def test_clamp_rebound() -> None:
    """Энергетическая защита срабатывает при превышении."""
    params = create_default_ball_params()

    # Мяч с большой энергией
    state = init_ball_state(v_x=100.0, v_y=0.0, omega=0.0)
    ke_initial = 0.1  # Малая начальная энергия

    result = clamp_rebound(state, params, ke_initial)

    # Защита должна сработать
    assert result == True

    # Энергия должна уменьшиться
    ke_final = compute_ball_kinetic_energy(state, params)
    assert ke_final <= ke_initial * 0.999

    print("✓ test_clamp_rebound passed")


def test_clamp_rebound_no_action() -> None:
    """Защита не срабатывает при нормальной энергии."""
    params = create_default_ball_params()

    # Мяч с малой энергией
    state = init_ball_state(v_x=1.0, v_y=0.0, omega=0.0)
    ke_initial = 100.0  # Большая начальная энергия

    result = clamp_rebound(state, params, ke_initial)

    # Защита не должна сработать
    assert result == False

    # Скорости не должны измениться
    assert abs(state.v_x - 1.0) < 1e-9

    print("✓ test_clamp_rebound_no_action passed")


def test_clamp_rebound_priority() -> None:
    """Приоритетное ограничение энергии работает."""
    params = create_default_ball_params()

    # Мяч с большой линейной и вращательной энергией
    state = init_ball_state(v_x=50.0, v_y=50.0, omega=1000.0)
    ke_initial = 1.0  # Увеличим начальную энергию для корректной работы

    result = clamp_rebound_priority(state, params, ke_initial)

    # Защита должна сработать
    assert result == True

    # Энергия должна уменьшиться
    ke_final = compute_ball_kinetic_energy(state, params)
    assert (
        ke_final <= ke_initial * 0.999
    ), f"ke_final={ke_final}, target={ke_initial * 0.999}"

    print("✓ test_clamp_rebound_priority passed")


def test_compute_ball_kinetic_energy() -> None:
    """Кинетическая энергия вычисляется корректно."""
    params = create_default_ball_params()

    # Только линейная энергия
    state = init_ball_state(v_x=10.0, v_y=0.0, omega=0.0)
    ke = compute_ball_kinetic_energy(state, params)

    expected_ke = 0.5 * params.mass * 10.0**2
    assert abs(ke - expected_ke) < 1e-9

    # Только вращательная энергия
    state = init_ball_state(v_x=0.0, v_y=0.0, omega=100.0)
    ke = compute_ball_kinetic_energy(state, params)

    I = params.ifactor * params.mass * params.radius**2
    expected_ke = 0.5 * I * 100.0**2
    assert abs(ke - expected_ke) < 1e-9

    print("✓ test_compute_ball_kinetic_energy passed")


def test_step_ball_post_flight() -> None:
    """Пост-контактный полёт корректен."""
    params = create_default_ball_params()
    state = init_ball_state(x=0.0, y=1.0, v_x=5.0, v_y=10.0, omega=100.0)

    dt = 0.01

    # Сохраняем начальные значения
    v_x_initial = state.v_x
    v_y_initial = state.v_y
    omega_initial = state.omega

    step_ball_post_flight(state, params, dt)

    # Гравитация уменьшает v_y
    assert state.v_y < v_y_initial
    assert abs(state.v_y - (v_y_initial - 9.81 * dt)) < 1e-6

    # v_x не меняется (нет сопротивления воздуха)
    assert abs(state.v_x - v_x_initial) < 1e-6

    # Вращение затухает
    assert abs(state.omega) < abs(omega_initial)

    # Позиция обновляется
    assert state.y > 1.0  # Мяч летит вверх
    assert state.x > 0.0  # Мяч летит вправо

    print("✓ test_step_ball_post_flight passed")


def test_ball_velocity_clamp() -> None:
    """Клиппинг скоростей работает."""
    from physics.ball import K_VELOCITY_CAP

    params = create_default_ball_params()
    state = init_ball_state(v_x=200.0, v_y=200.0, omega=0.0)  # > K_VELOCITY_CAP
    forces = BallForces(fn=0.0, ft=0.0)

    accelerations = compute_ball_accelerations(state, params, forces)
    dt = 0.01

    integrate_ball(state, params, accelerations, dt)

    # Скорости должны быть ограничены
    assert abs(state.v_x) <= K_VELOCITY_CAP
    assert abs(state.v_y) <= K_VELOCITY_CAP

    print("✓ test_ball_velocity_clamp passed")


def run_all_tests() -> None:
    """Запустить все тесты."""
    print("Running Ball tests...\n")

    test_init_ball_state()
    test_compute_ball_accelerations()
    test_compute_ball_accelerations_no_forces()
    test_integrate_ball()
    test_integrate_ball_with_spin()
    test_clamp_rebound()
    test_clamp_rebound_no_action()
    test_clamp_rebound_priority()
    test_compute_ball_kinetic_energy()
    test_step_ball_post_flight()
    test_ball_velocity_clamp()

    print("\n✅ All Ball tests passed!")


if __name__ == "__main__":
    run_all_tests()
