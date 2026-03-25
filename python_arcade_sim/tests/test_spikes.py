"""
Тесты для модуля spikes.py.

Проверка:
- Динамика наклона работает без NaN
- Ограничения наклона соблюдаются
- Влияние на трение корректно
"""

import sys
from pathlib import Path

# Добавляем корень проекта в path для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.spikes import (
    SpikesInput,
    SpikesOutput,
    apply_spikes_to_friction,
    compute_spikes_dynamics,
    init_spikes_state,
)
from physics.surface import SpikeEquivalentParams
from physics.sim_types import SpikeMode


def create_spike_params() -> SpikeEquivalentParams:
    """Создать тестовые параметры шипов."""
    return SpikeEquivalentParams(
        k_sh=1000.0,
        h=0.001,
        theta_max=0.5,  # ~28 градусов
    )


def test_init_spikes_state() -> None:
    """Инициализация возвращает нулевое состояние."""
    state = init_spikes_state()

    assert state.theta == 0.0
    assert state.theta_dot == 0.0
    assert state.mu_multiplier == 1.0
    assert state.ft_additional == 0.0

    print("✓ test_init_spikes_state passed")


def test_compute_spikes_dynamics_no_nan() -> None:
    """Динамика шипов не производит NaN."""
    state = init_spikes_state()
    params = create_spike_params()

    input_params = SpikesInput(
        spike_params=params,
        mode=SpikeMode.OUT,
        ft_contact=10.0,  # 10 Н касательной силы
        v_rel_t=5.0,  # 5 м/с относительная скорость
        dt=1e-5,
    )

    output = compute_spikes_dynamics(state, input_params)

    # Проверка отсутствия NaN
    assert not (output.theta != output.theta)
    assert not (output.theta_dot != output.theta_dot)
    assert not (output.mu_multiplier != output.mu_multiplier)
    assert not (output.ft_additional != output.ft_additional)

    print("✓ test_compute_spikes_dynamics_no_nan passed")


def test_compute_spikes_dynamics_theta_limit() -> None:
    """Наклон шипов ограничивается theta_max."""
    state = init_spikes_state()
    params = create_spike_params()

    # Много шагов с большой силой
    input_params = SpikesInput(
        spike_params=params,
        mode=SpikeMode.OUT,
        ft_contact=1000.0,  # Большая сила
        v_rel_t=10.0,
        dt=1e-5,
    )

    # Симулируем много шагов
    for _ in range(1000):
        output = compute_spikes_dynamics(state, input_params)
        state = output

    # Наклон должен быть ограничен
    assert abs(output.theta) <= params.theta_max + 1e-6

    print("✓ test_compute_spikes_dynamics_theta_limit passed")


def test_compute_spikes_dynamics_direction() -> None:
    """Наклон зависит от направления движения."""
    state = init_spikes_state()
    params = create_spike_params()

    # Движение вправо (v_rel_t > 0)
    input_right = SpikesInput(
        spike_params=params,
        mode=SpikeMode.OUT,
        ft_contact=10.0,
        v_rel_t=5.0,  # Вправо
        dt=1e-5,
    )

    output_right = compute_spikes_dynamics(state, input_right)

    # Движение влево (v_rel_t < 0)
    input_left = SpikesInput(
        spike_params=params,
        mode=SpikeMode.OUT,
        ft_contact=10.0,
        v_rel_t=-5.0,  # Влево
        dt=1e-5,
    )

    output_left = compute_spikes_dynamics(state, input_left)

    # Наклоны должны быть противоположных знаков
    # (или хотя бы дополнительная сила должна быть противоположной)
    assert output_right.ft_additional * output_left.ft_additional <= 0

    print("✓ test_compute_spikes_dynamics_direction passed")


def test_spikes_mode_effect() -> None:
    """Режимы out/in влияют на трение по-разному."""
    params = create_spike_params()
    state = init_spikes_state()

    # Симулируем несколько шагов для накопления наклона
    for mode in [SpikeMode.OUT, SpikeMode.IN]:
        state = init_spikes_state()
        input_params = SpikesInput(
            spike_params=params,
            mode=mode,
            ft_contact=10.0,
            v_rel_t=5.0,
            dt=1e-5,
        )

        for _ in range(100):
            state = compute_spikes_dynamics(state, input_params)

        # Проверка множителя трения
        if mode == SpikeMode.OUT:
            # "out" должен увеличивать трение
            assert state.mu_multiplier >= 1.0
        elif mode == SpikeMode.IN:
            # "in" должен уменьшать трение (но не ниже 0.5)
            assert 0.5 <= state.mu_multiplier <= 1.0

    print("✓ test_spikes_mode_effect passed")


def test_apply_spikes_to_friction() -> None:
    """Применение шипов к трению корректно."""
    mu_s_base = 1.0
    mu_k_base = 0.5

    # Без шипов (mu_multiplier = 1.0)
    state_no_spikes = SpikesOutput(
        theta=0.0, theta_dot=0.0, mu_multiplier=1.0, ft_additional=0.0
    )
    mu_s_new, mu_k_new = apply_spikes_to_friction(mu_s_base, mu_k_base, state_no_spikes)

    assert mu_s_new == mu_s_base
    assert mu_k_new == mu_k_base

    # С шипами (mu_multiplier = 1.5)
    state_with_spikes = SpikesOutput(
        theta=0.25, theta_dot=0.0, mu_multiplier=1.5, ft_additional=0.0
    )
    mu_s_new, mu_k_new = apply_spikes_to_friction(
        mu_s_base, mu_k_base, state_with_spikes
    )

    assert abs(mu_s_new - 1.5) < 1e-6
    assert abs(mu_k_new - 0.75) < 1e-6

    # Проверка mu_k <= mu_s
    assert mu_k_new <= mu_s_new

    print("✓ test_apply_spikes_to_friction passed")


def test_compute_spikes_dynamics_none_mode() -> None:
    """Режим NONE не изменяет состояние."""
    state = init_spikes_state()
    params = create_spike_params()

    input_params = SpikesInput(
        spike_params=params,
        mode=SpikeMode.NONE,
        ft_contact=10.0,
        v_rel_t=5.0,
        dt=1e-5,
    )

    output = compute_spikes_dynamics(state, input_params)

    # Состояние не должно измениться
    assert output.theta == 0.0
    assert output.theta_dot == 0.0
    assert output.mu_multiplier == 1.0
    assert output.ft_additional == 0.0

    print("✓ test_compute_spikes_dynamics_none_mode passed")


def test_compute_spikes_dynamics_no_params() -> None:
    """Отсутствие параметров шипов не изменяет состояние."""
    state = init_spikes_state()

    input_params = SpikesInput(
        spike_params=None,  # Нет параметров
        mode=SpikeMode.NONE,
        ft_contact=10.0,
        v_rel_t=5.0,
        dt=1e-5,
    )

    output = compute_spikes_dynamics(state, input_params)

    # Состояние не должно измениться
    assert output.theta == 0.0
    assert output.theta_dot == 0.0

    print("✓ test_compute_spikes_dynamics_no_params passed")


def run_all_tests() -> None:
    """Запустить все тесты."""
    print("Running Spikes tests...\n")

    test_init_spikes_state()
    test_compute_spikes_dynamics_no_nan()
    test_compute_spikes_dynamics_theta_limit()
    test_compute_spikes_dynamics_direction()
    test_spikes_mode_effect()
    test_apply_spikes_to_friction()
    test_compute_spikes_dynamics_none_mode()
    test_compute_spikes_dynamics_no_params()

    print("\n✅ All Spikes tests passed!")


if __name__ == "__main__":
    run_all_tests()
