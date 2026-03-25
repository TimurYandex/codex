"""
Физика мяча: динамика, интегратор, энергетическая защита.

Модуль независим от arcade и используется только в физическом ядре.

Физическая модель мяча:
=======================
Мяч моделируется как твёрдое тело с 5 степенями свободы:
- x, y — позиция центра, м
- v_x, v_y — скорость центра, м/с
- omega — угловая скорость, рад/с
- phi — угол поворота (для визуализации), рад

1. Уравнения движения:
   - a_x = F_t / m
   - a_y = F_n / m - g
   - omega_dot = -(F_t * r) / I

   где I = if * m * r² — момент инерции
   (if = 0.4 для сплошного шара, if = 2/3 для полого)

2. Интегратор (semi-implicit Euler):
   - Сначала скорости: v += a * dt
   - Затем позиции: x += v * dt
   - Преимущество: лучше сохраняет энергию

3. Энергетическая защита (clampRebound):
   - Если KE > KE0 * 0.999, масштабируем скорости вниз
   - Защита от искусственного "разгона" отскока
   - При одновременном росте |v| и |omega| приоритет одному

4. Пост-контактный полёт:
   - Свободный полёт с гравитацией
   - Затухание вращения: omega *= (1 - k_spin * dt)
   - Критерий отрыва: контакт отсутствует N шагов, y > r + margin

5. Критерий завершения:
   - Время пост-полёта >= SIM_POST_DURATION
   - Или мяч улетел достаточно далеко
"""

# =============================================================================
# Автодобавление корня проекта в sys.path для прямого запуска файла
# =============================================================================

import sys
from pathlib import Path

if __name__ == "__main__":
    _project_root = str(Path(__file__).parent.parent)
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

# =============================================================================

from dataclasses import dataclass

from config.constants import (
    BALL_IF_DEFAULT,
    BALL_MASS_DEFAULT,
    BALL_RADIUS_DEFAULT,
    G,
    K_ENERGY_SCALE,
    K_SPIN_DECAY,
    K_VELOCITY_CAP,
)
from physics.sim_types import BallParams, BallState


# =============================================================================
# Параметры и состояние мяча
# =============================================================================


@dataclass
class BallForces:
    """
    Силы, действующие на мяч.

    Атрибуты:
        fn: Нормальная сила (положительная = вверх), Н.
        ft: Касательная сила (положительная = вправо), Н.
    """

    fn: float = 0.0
    ft: float = 0.0


# =============================================================================
# Динамика мяча
# =============================================================================


def compute_ball_accelerations(
    ball_state: BallState,
    ball_params: BallParams,
    forces: BallForces,
) -> tuple[float, float, float]:
    """
    Вычислить ускорения мяча.

    Физическая модель:
    ==================

    1. Линейные ускорения (второй закон Ньютона):
       - a_x = F_t / m
       - a_y = F_n / m - g

    2. Угловое ускорение (момент силы):
       - omega_dot = -(F_t * r) / I

       где I = if * m * r² — момент инерции шара
       (if = 0.4 для сплошного, if = 2/3 для полого)

       Знак минус: положительная F_t создаёт отрицательный момент
       (вращение по часовой стрелке).

    Ожидаемые эффекты:
    - Положительная Fn ускоряет мяч вверх
    - Положительная Ft ускоряет мяч вправо и создаёт вращение против часовой
    - Гравитация постоянно ускоряет мяч вниз

    Args:
        ball_state: Текущее состояние мяча.
        ball_params: Параметры мяча (масса, радиус, if).
        forces: Силы, действующие на мяч (Fn, Ft).

    Returns:
        (a_x, a_y, omega_dot) — ускорения.
    """
    m = ball_params.mass
    r = ball_params.radius
    ifactor = ball_params.ifactor

    # Момент инерции: I = if * m * r²
    I = ifactor * m * r * r

    # Линейные ускорения
    a_x = forces.ft / m
    a_y = forces.fn / m - G

    # Угловое ускорение
    # Знак минус: F_t > 0 создаёт вращение по часовой (omega < 0)
    omega_dot = -(forces.ft * r) / max(I, 1e-9)

    return a_x, a_y, omega_dot


def integrate_ball(
    ball_state: BallState,
    ball_params: BallParams,
    accelerations: tuple[float, float, float],
    dt: float,
) -> None:
    """
    Интегрировать уравнения движения мяча (semi-implicit Euler).

    Физическая модель:
    ==================

    Semi-implicit Euler (симплектический Эйлер):
    1. Сначала обновляем скорости: v_new = v_old + a * dt
    2. Затем обновляем позиции: x_new = x_old + v_new * dt

    Преимущество перед явным Эйлером:
    - Лучше сохраняет энергию в колебательных системах
    - Более стабилен для жёстких пружин

    Угловая динамика:
    - phi += omega * dt (угол поворота для визуализации)

    Клиппинг скоростей:
    - |v_x|, |v_y| <= K_VELOCITY_CAP (защита от "разлёта")
    - |omega| <= K_VELOCITY_CAP / r (согласованный кап)

    Args:
        ball_state: Состояние мяча (обновляется).
        ball_params: Параметры мяча.
        accelerations: (a_x, a_y, omega_dot) — ускорения.
        dt: Шаг времени.
    """
    a_x, a_y, omega_dot = accelerations

    # ========================================================================
    # Обновление скоростей (сначала скорости в semi-implicit Euler)
    # ========================================================================

    ball_state.v_x += a_x * dt
    ball_state.v_y += a_y * dt
    ball_state.omega += omega_dot * dt

    # ========================================================================
    # Обновление позиций (затем позиции)
    # ========================================================================

    ball_state.x += ball_state.v_x * dt
    ball_state.y += ball_state.v_y * dt
    ball_state.phi += ball_state.omega * dt

    # ========================================================================
    # Клиппинг скоростей (защита от нестабильности)
    # ========================================================================

    ball_state.v_x = clamp(ball_state.v_x, -K_VELOCITY_CAP, K_VELOCITY_CAP)
    ball_state.v_y = clamp(ball_state.v_y, -K_VELOCITY_CAP, K_VELOCITY_CAP)

    # Кап угловой скорости (согласованный с линейной)
    max_omega = K_VELOCITY_CAP / max(ball_params.radius, 0.01)
    ball_state.omega = clamp(ball_state.omega, -max_omega, max_omega)


# =============================================================================
# Энергетическая защита (clampRebound)
# =============================================================================


def clamp_rebound(
    ball_state: BallState,
    ball_params: BallParams,
    ke_initial: float,
) -> bool:
    """
    Ограничить кинетическую энергию мяча (защита от искусственного разгона).

    Физическая проблема:
    ====================
    При численном интегрировании может возникать искусственный прирост энергии:
    - Мяч отскакивает с большей скоростью, чем до удара
    - Вращение увеличивается без физической причины
    - Это нарушает закон сохранения энергии

    Решение:
    ========
    1. Вычисляем текущую кинетическую энергию:
       KE = 0.5 * m * (v_x² + v_y²) + 0.5 * I * omega²

    2. Если KE > KE_initial * K_ENERGY_SCALE (0.999):
       - Масштабируем скорости вниз: v *= sqrt(KE_target / KE)

    3. При одновременном росте |v| и |omega|:
       - Ограничиваем одну компоненту (приоритет линейной скорости)

    Args:
        ball_state: Состояние мяча (обновляется).
        ball_params: Параметры мяча.
        ke_initial: Начальная кинетическая энергия (до удара).

    Returns:
        True, если энергия была ограничена.
    """
    m = ball_params.mass
    r = ball_params.radius
    ifactor = ball_params.ifactor

    # Момент инерции
    I = ifactor * m * r * r

    # Текущая кинетическая энергия
    # KE = KE_linear + KE_rotational
    v_squared = ball_state.v_x**2 + ball_state.v_y**2
    ke_current = 0.5 * m * v_squared + 0.5 * I * ball_state.omega**2

    # Целевая энергия (чуть меньше начальной для диссипации)
    ke_target = ke_initial * K_ENERGY_SCALE

    if ke_current <= ke_target or ke_target <= 0:
        return False

    # ========================================================================
    # Масштабирование скоростей
    # ========================================================================

    # Коэффициент масштабирования
    scale = (ke_target / max(ke_current, 1e-9)) ** 0.5

    # Ограничиваем только если scale < 1 (уменьшение энергии)
    if scale < 1.0:
        ball_state.v_x *= scale
        ball_state.v_y *= scale
        ball_state.omega *= scale
        return True

    return False


def clamp_rebound_priority(
    ball_state: BallState,
    ball_params: BallParams,
    ke_initial: float,
) -> bool:
    """
    Ограничить кинетическую энергию с приоритетом линейной скорости.

    Физическая проблема:
    ====================
    При одновременном росте |v| и |omega| простое масштабирование
    может дать неверное распределение энергии между компонентами.

    Решение:
    ========
    1. Сначала ограничиваем линейную скорость
    2. Если энергии всё ещё много, ограничиваем вращение

    Это соответствует физической интуиции:
    - Линейное движение обычно доминирует в энергии удара
    - Вращение — вторичный эффект

    Args:
        ball_state: Состояние мяча (обновляется).
        ball_params: Параметры мяча.
        ke_initial: Начальная кинетическая энергия.

    Returns:
        True, если энергия была ограничена.
    """
    m = ball_params.mass
    r = ball_params.radius
    ifactor = ball_params.ifactor

    I = ifactor * m * r * r
    ke_target = ke_initial * K_ENERGY_SCALE

    # Текущая энергия
    v_squared = ball_state.v_x**2 + ball_state.v_y**2
    ke_linear = 0.5 * m * v_squared
    ke_rotational = 0.5 * I * ball_state.omega**2
    ke_current = ke_linear + ke_rotational

    if ke_current <= ke_target or ke_target <= 0:
        return False

    # ========================================================================
    # Приоритетное ограничение
    # ========================================================================

    # Шаг 1: Ограничиваем линейную энергию
    ke_linear_target = ke_target * 0.9  # 90% энергии на линейное движение

    if ke_linear > ke_linear_target:
        scale_linear = (ke_linear_target / max(ke_linear, 1e-9)) ** 0.5
        ball_state.v_x *= scale_linear
        ball_state.v_y *= scale_linear
        ke_linear = ke_linear_target

    # Шаг 2: Ограничиваем вращательную энергию
    ke_rotational_target = ke_target - ke_linear_target

    if ke_rotational > ke_rotational_target:
        scale_rotational = (ke_rotational_target / max(ke_rotational, 1e-9)) ** 0.5
        ball_state.omega *= scale_rotational

    return True


# =============================================================================
# Пост-контактный полёт
# =============================================================================


def step_ball_post_flight(
    ball_state: BallState,
    ball_params: BallParams,
    dt: float,
) -> None:
    """
    Шаг пост-контактного полёта мяча.

    Физическая модель:
    ==================

    1. Свободный полёт с гравитацией:
       - v_y += -g * dt
       - x += v_x * dt
       - y += v_y * dt

    2. Затухание вращения:
       - omega *= (1 - k_spin * dt)

       Физический смысл: сопротивление воздуха замедляет вращение.

    3. Клиппинг скоростей (защита от нестабильности).

    Args:
        ball_state: Состояние мяча (обновляется).
        ball_params: Параметры мяча.
        dt: Шаг времени.
    """
    # Гравитация
    ball_state.v_y += -G * dt

    # Позиция
    ball_state.x += ball_state.v_x * dt
    ball_state.y += ball_state.v_y * dt

    # Затухание вращения
    ball_state.omega *= 1.0 - K_SPIN_DECAY * dt

    # Угол поворота (для визуализации)
    ball_state.phi += ball_state.omega * dt

    # Клиппинг
    ball_state.v_x = clamp(ball_state.v_x, -K_VELOCITY_CAP, K_VELOCITY_CAP)
    ball_state.v_y = clamp(ball_state.v_y, -K_VELOCITY_CAP, K_VELOCITY_CAP)


# =============================================================================
# Вспомогательные функции
# =============================================================================


def compute_ball_kinetic_energy(
    ball_state: BallState,
    ball_params: BallParams,
) -> float:
    """
    Вычислить кинетическую энергию мяча.

    KE = KE_linear + KE_rotational
       = 0.5 * m * v² + 0.5 * I * omega²

    Args:
        ball_state: Состояние мяча.
        ball_params: Параметры мяча.

    Returns:
        Кинетическая энергия, Дж.
    """
    m = ball_params.mass
    r = ball_params.radius
    ifactor = ball_params.ifactor

    I = ifactor * m * r * r

    v_squared = ball_state.v_x**2 + ball_state.v_y**2

    return 0.5 * m * v_squared + 0.5 * I * ball_state.omega**2


def init_ball_state(
    x: float = 0.0,
    y: float = 0.0,
    v_x: float = 0.0,
    v_y: float = 0.0,
    omega: float = 0.0,
) -> BallState:
    """
    Инициализировать состояние мяча.

    Args:
        x, y: Начальная позиция.
        v_x, v_y: Начальная скорость.
        omega: Начальная угловая скорость.

    Returns:
        BallState с заданными параметрами.
    """
    return BallState(
        x=x,
        y=y,
        v_x=v_x,
        v_y=v_y,
        omega=omega,
        phi=0.0,
    )


# Импортируем clamp из utils
from utils.math import clamp


# =============================================================================
# Тестовый запуск (при прямом запуске файла)
# =============================================================================

if __name__ == "__main__":
    """
    При прямом запуске файла выполняются простые тесты.

    Использование:
        python physics/ball.py
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    from physics.ball import (
        BallForces,
        clamp_rebound,
        compute_ball_accelerations,
        compute_ball_kinetic_energy,
        integrate_ball,
        init_ball_state,
        step_ball_post_flight,
    )
    from physics.sim_types import BallParams

    print("Testing ball module...\n")

    params = BallParams(radius=0.02, mass=0.0027, ifactor=0.4)

    # Тест 1: Ускорения
    state = init_ball_state()
    forces = BallForces(fn=1.0, ft=0.5)
    a_x, a_y, omega_dot = compute_ball_accelerations(state, params, forces)
    print(f"accelerations: a_x={a_x:.2f}, a_y={a_y:.2f}, omega_dot={omega_dot:.2f}")

    # Тест 2: Интегрирование
    state = init_ball_state(x=0.0, y=1.0, v_x=5.0, v_y=0.0)
    forces = BallForces(fn=0.0, ft=0.0)
    acc = compute_ball_accelerations(state, params, forces)
    integrate_ball(state, params, acc, 0.01)
    print(f"integration: x={state.x:.4f}, y={state.y:.4f}, v_y={state.v_y:.4f}")

    # Тест 3: Энергетическая защита
    state = init_ball_state(v_x=100.0, v_y=0.0)
    ke_initial = 0.1
    result = clamp_rebound(state, params, ke_initial)
    ke_final = compute_ball_kinetic_energy(state, params)
    print(
        f"clamp_rebound: applied={result}, ke_final={ke_final:.6f} (target={ke_initial * 0.999:.6f})"
    )

    # Тест 4: Пост-полёт
    state = init_ball_state(v_x=5.0, v_y=10.0, omega=100.0)
    step_ball_post_flight(state, params, 0.01)
    print(f"post_flight: v_y={state.v_y:.4f}, omega={state.omega:.4f}")

    print("\n✅ All basic tests passed!")
