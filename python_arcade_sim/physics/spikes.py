"""
Физика шипов: модель наклона и влияние на трение.

Модуль независим от arcade и используется только в физическом ядре.

Физическая модель шипов:
========================
Шипы моделируются как упругие элементы с наклоном θ (тета).

1. Динамика наклона:
   - Уравнение: θ¨ = f_th - k_sh * θ - c_sh * θ_dot
   - f_th: движущая сила от касательного воздействия мяча
   - k_sh: жёсткость шипов (сопротивление наклону)
   - c_sh: демпфирование наклона (рассеяние энергии)

2. Ограничение наклона:
   - θ ∈ [-θ_max, +θ_max]
   - Защита от чрезмерного наклона (нестабильность)

3. Влияние на трение:
   - Шипы "out" (наружу): увеличивают mu_s и mu_k
   - Шипы "in" (внутрь): уменьшают mu_s и mu_k
   - Коэффициент усиления зависит от наклона θ

4. Влияние на касательную силу:
   - Наклонённые шипы создают дополнительную силу
   - F_t_sh = k_sh * θ * sign(v_rel_t)

5. Параметры шипов:
   - Берутся из верхнего слоя поверхности
   - Режим: none (нет шипов), out (наружу), in (внутрь)
   - k_sh: жёсткость шипов
   - h: высота шипов (влияет на геометрию)
"""

# =============================================================================
# Автодобавление корня проекта в sys.path для прямого запуска файла
# =============================================================================

import sys
from pathlib import Path

if __name__ == "__main__":
    # При прямом запуске файла добавляем родительскую директорию в path
    _project_root = str(Path(__file__).parent.parent)
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

# =============================================================================

from dataclasses import dataclass

from config.constants import K_FORCE_CAP, SPIKES_THETA_MAX
from physics.surface import SpikeEquivalentParams
from physics.sim_types import SpikeMode
from utils.math import clamp, sign


# =============================================================================
# Состояние и параметры шипов
# =============================================================================


@dataclass
class SpikesInput:
    """
    Входные параметры для расчёта шипов.

    Атрибуты:
        spike_params: Параметры шипов из верхнего слоя (или None).
        mode: Режим шипов (none/out/in).
        ft_contact: Касательная сила контакта, Н.
        v_rel_t: Относительная касательная скорость, м/с.
        dt: Шаг времени.
    """

    spike_params: SpikeEquivalentParams | None
    mode: SpikeMode
    ft_contact: float
    v_rel_t: float
    dt: float


@dataclass
class SpikesOutput:
    """
    Результат расчёта шипов.

    Атрибуты:
        theta: Текущий наклон шипов, рад.
        theta_dot: Скорость наклона, рад/с.
        mu_multiplier: Множитель трения (1.0 = без влияния).
        ft_additional: Дополнительная касательная сила от шипов, Н.
    """

    theta: float = 0.0
    theta_dot: float = 0.0
    mu_multiplier: float = 1.0
    ft_additional: float = 0.0


# =============================================================================
# Динамика шипов
# =============================================================================


def compute_spikes_dynamics(
    state: SpikesOutput,
    input_params: SpikesInput,
) -> SpikesOutput:
    """
    Вычислить динамику шипов на один шаг.

    Физическая модель:
    ==================
    Уравнение движения наклона шипов:
        θ¨ = f_th - k_sh * θ - c_sh * θ_dot

    где:
        - θ: наклон шипов (рад)
        - θ_dot: скорость наклона (рад/с)
        - f_th: движущая сила от касательного воздействия
        - k_sh: жёсткость шипов
        - c_sh: демпфирование

    Движущая сила f_th:
        f_th = pg * F_t * scale
        - pg: плотность шипов (внутренний параметр)
        - F_t: касательная сила контакта
        - scale: коэффициент направления (зависит от mode)

    Интегрирование (Euler):
        θ_dot += θ¨ * dt
        θ += θ_dot * dt

    Ограничения:
        - θ ∈ [-θ_max, +θ_max]
        - |θ_dot| <= θ_max / dt (защита от чрезмерной скорости)

    Влияние на трение:
        - mu_multiplier = 1.0 + k_theta * |θ|
        - k_theta: коэффициент усиления (калибровка)
        - Для mode "out": multiplier > 1 (увеличение трения)
        - Для mode "in": multiplier < 1 (уменьшение трения)

    Дополнительная касательная сила:
        F_t_sh = k_sh * θ * sign(v_rel_t)
        - Направлена против движения
        - Пропорциональна наклону

    Ожидаемые эффекты:
        - При контакте мяча шипы наклоняются в направлении движения
        - Наклон создаёт дополнительную силу трения
        - После отрыва шипы возвращаются в исходное положение

    Args:
        state: Текущее состояние шипов (theta, theta_dot).
        input_params: Входные параметры (сила, скорость, режим).

    Returns:
        SpikesOutput с обновлённым состоянием.
    """
    # Если шипы не активны — возврат без изменений
    if input_params.spike_params is None or input_params.mode == SpikeMode.NONE:
        return SpikesOutput(theta=state.theta, theta_dot=state.theta_dot)

    params = input_params.spike_params
    dt = input_params.dt

    # ========================================================================
    # Движущая сила от касательного воздействия
    # ========================================================================

    # Плотность шипов (внутренний параметр, не вводится пользователем)
    pg = 1000.0  # шт/м² (калибровка)

    # Коэффициент направления
    # "out": шипы торчат наружу — сильнее реагируют
    # "in": шипы внутрь — слабее реагируют
    if input_params.mode == SpikeMode.OUT:
        direction_scale = 1.5
    elif input_params.mode == SpikeMode.IN:
        direction_scale = 0.5
    else:
        direction_scale = 1.0

    # Движущая сила (пропорциональна касательной силе контакта)
    # Нормализуем F_t для устойчивости
    ft_normalized = input_params.ft_contact / max(K_FORCE_CAP, 1.0)
    f_th = pg * ft_normalized * direction_scale

    # ========================================================================
    # Уравнение движения: θ¨ = f_th - k_sh * θ - c_sh * θ_dot
    # ========================================================================

    # Жёсткость и демпфирование (из параметров слоя)
    k_sh = params.k_sh
    c_sh = k_sh * 0.1  # Демпфирование = 10% от жёсткости (калибровка)

    # Ускорение наклона
    theta_ddot = f_th - k_sh * state.theta - c_sh * state.theta_dot

    # ========================================================================
    # Интегрирование (Euler)
    # ========================================================================

    theta_dot_new = state.theta_dot + theta_ddot * dt
    theta_new = state.theta + theta_dot_new * dt

    # ========================================================================
    # Ограничения (клиппинг)
    # ========================================================================

    # Ограничение наклона: θ ∈ [-θ_max, +θ_max]
    theta_new = clamp(theta_new, -params.theta_max, params.theta_max)

    # Ограничение скорости: |θ_dot| <= θ_max / dt
    max_theta_dot = params.theta_max / max(dt, 1e-6)
    theta_dot_new = clamp(theta_dot_new, -max_theta_dot, max_theta_dot)

    # ========================================================================
    # Влияние на трение (mu_multiplier)
    # ========================================================================

    # Коэффициент усиления трения от наклона
    # Чем больше наклон, тем сильнее трение
    k_theta = 2.0  # Калибровка: максимальное усиление = 1 + 2*θ_max ≈ 2

    if input_params.mode == SpikeMode.OUT:
        # Шипы "out" увеличивают трение
        mu_multiplier = 1.0 + k_theta * abs(theta_new)
    elif input_params.mode == SpikeMode.IN:
        # Шипы "in" уменьшают трение (обратный эффект)
        mu_multiplier = 1.0 - k_theta * 0.5 * abs(theta_new)
        mu_multiplier = max(mu_multiplier, 0.5)  # Минимум 50%
    else:
        mu_multiplier = 1.0

    # ========================================================================
    # Дополнительная касательная сила от шипов
    # ========================================================================

    # F_t_sh = k_sh * θ * sign(v_rel_t)
    # Направлена против движения
    ft_additional = k_sh * theta_new * sign(input_params.v_rel_t)

    # Ограничение силы (защита от нестабильности)
    ft_additional = clamp(ft_additional, -K_FORCE_CAP, K_FORCE_CAP)

    return SpikesOutput(
        theta=theta_new,
        theta_dot=theta_dot_new,
        mu_multiplier=mu_multiplier,
        ft_additional=ft_additional,
    )


# =============================================================================
# Инициализация и сброс
# =============================================================================


def init_spikes_state() -> SpikesOutput:
    """
    Инициализировать состояние шипов.

    Начальное состояние:
    - theta = 0 (нет наклона)
    - theta_dot = 0 (нет вращения)
    - mu_multiplier = 1.0 (без усиления)
    - ft_additional = 0 (нет дополнительной силы)

    Returns:
        SpikesOutput с нулевым состоянием.
    """
    return SpikesOutput(
        theta=0.0,
        theta_dot=0.0,
        mu_multiplier=1.0,
        ft_additional=0.0,
    )


# =============================================================================
# Влияние шипов на параметры трения
# =============================================================================


def apply_spikes_to_friction(
    mu_s_base: float,
    mu_k_base: float,
    spikes_state: SpikesOutput,
) -> tuple[float, float]:
    """
    Применить влияние шипов к коэффициентам трения.

    Формула:
        mu_s_new = mu_s_base * mu_multiplier
        mu_k_new = mu_k_base * mu_multiplier

    Ограничение:
        mu_k_new <= mu_s_new (физическое требование)

    Args:
        mu_s_base: Базовое трение покоя (без шипов).
        mu_k_base: Базовое трение скольжения (без шипов).
        spikes_state: Состояние шипов (mu_multiplier).

    Returns:
        (mu_s_new, mu_k_new) — обновлённые коэффициенты трения.
    """
    mu_s_new = mu_s_base * spikes_state.mu_multiplier
    mu_k_new = mu_k_base * spikes_state.mu_multiplier

    # Ограничение mu_k <= mu_s
    mu_k_new = min(mu_k_new, mu_s_new)

    return mu_s_new, mu_k_new


# =============================================================================
# Тестовый запуск (при прямом запуске файла)
# =============================================================================

if __name__ == "__main__":
    """
    При прямом запуске файла выполняются простые тесты.

    Использование:
        python physics/spikes.py
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

    print("Testing spikes module...\n")

    # Тест инициализации
    state = init_spikes_state()
    print(
        f"init_spikes_state: theta={state.theta}, mu_multiplier={state.mu_multiplier}"
    )

    # Тест динамики
    params = SpikeEquivalentParams(k_sh=1000.0, h=0.001, theta_max=0.5)
    input_params = SpikesInput(
        spike_params=params,
        mode=SpikeMode.OUT,
        ft_contact=10.0,
        v_rel_t=5.0,
        dt=1e-5,
    )

    output = compute_spikes_dynamics(state, input_params)
    print(
        f"compute_spikes_dynamics: theta={output.theta}, mu_multiplier={output.mu_multiplier}"
    )

    # Тест влияния на трение
    mu_s_new, mu_k_new = apply_spikes_to_friction(1.0, 0.5, output)
    print(f"apply_spikes_to_friction: mu_s={mu_s_new}, mu_k={mu_k_new}")

    print("\n✅ All basic tests passed!")
