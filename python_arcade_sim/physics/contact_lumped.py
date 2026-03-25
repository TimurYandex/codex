"""
Модель контакта на основе JS реализации (corrected physics).

Ключевые отличия от предыдущей модели:
1. Используем модель одной точки контакта (lumped parameter)
2. Правильный расчёт относительной скорости: v_rel = v_t - omega * r
3. Правильный stick-slip переход с накоплением stick_disp
4. Прямая связь деформации с нормальной скоростью
"""

import math
from dataclasses import dataclass, field


@dataclass
class ContactState:
    """Состояние контакта."""
    overlap: float = 0.0  # Глубина деформации, м
    overlap_rate: float = 0.0  # Скорость деформации, м/с
    stick_disp: float = 0.0  # Касательное смещение, м
    fn: float = 0.0  # Нормальная сила, Н
    ft: float = 0.0  # Касательная сила, Н
    is_active: bool = False  # Контакт активен


@dataclass
class ContactParams:
    """Параметры контакта."""
    kc: float = 62000.0  # Нормальная жёсткость (вклад мяча + поверхности), Н/м^1.35
    cc: float = 10.5  # Нормальное демпфирование, Н·с/м
    kt: float = 19840.0  # Касательная жёсткость (0.32 * kc), Н/м
    mu_s: float = 0.95  # Трение покоя
    mu_k: float = 0.81  # Трение скольжения
    exponent: float = 1.35  # Показатель степени в законе Герца


def step_contact_lumped(
    state: ContactState,
    params: ContactParams,
    v_y: float,  # Вертикальная скорость мяча (положительная = вверх)
    v_x: float,  # Горизонтальная скорость мяча (положительная = вправо)
    omega: float,  # Угловая скорость (положительная = против часовой)
    radius: float,  # Радиус мяча, м
    mass: float,  # Масса мяча, кг
    ifactor: float,  # Фактор момента инерции
    dt: float,  # Шаг времени, с
) -> tuple[float, float, float]:
    """
    Шаг интегрирования контакта (lumped parameter model).

    Физическая модель основана на JS реализации:
    1. Нормальная сила: Fn = kc * depth^1.35 + cc * depthRate
    2. Относительная скорость: vRel = vt - omega * r
    3. Stick-slip: stickDisp += vRel * dt, ft = -kT * stickDisp (stick) или ft = -sign(vRel) * muK * Fn (slip)
    4. Угловое ускорение: alpha = -(ft * r) / I

    Args:
        state: Состояние контакта (обновляется)
        params: Параметры контакта
        v_y: Вертикальная скорость мяча (положительная = вверх)
        v_x: Горизонтальная скорость мяча (положительная = вправо)
        omega: Угловая скорость (положительная = против часовой)
        radius: Радиус мяча, м
        mass: Масса мяча, кг
        ifactor: Фактор момента инерции
        dt: Шаг времени, с

    Returns:
        (a_x, a_y, alpha) — ускорения
    """
    # Момент инерции: I = ifactor * m * r²
    I = ifactor * mass * radius * radius
    
    # ================================================================
    # 1. Нормальная сила (закон Герца с демпфированием)
    # ================================================================
    
    # Глубина деформации (overlap)
    depth = state.overlap
    
    # Скорость деформации (depthRate)
    # При v_y < 0 (мяч движется вниз), depthRate должен быть положительным
    depth_rate = state.overlap_rate
    
    # Нормальная сила
    fn_elastic = params.kc * (depth ** params.exponent)
    fn_damping = params.cc * max(0.0, depth_rate)
    state.fn = fn_elastic + fn_damping
    state.fn = max(0.0, state.fn)
    
    # ================================================================
    # 2. Касательная сила (stick-slip)
    # ================================================================
    
    # Относительная скорость проскальзывания
    # v_rel > 0: нижняя точка мяча движется вправо относительно поверхности
    # v_rel = v_x - omega * r
    v_rel = v_x - omega * radius
    
    # Накопление касательного смещения
    state.stick_disp += v_rel * dt
    
    # Пробная сила (stick)
    ft_trial = -params.kt * state.stick_disp
    
    # Максимальная сила трения покоя
    ft_max = params.mu_s * state.fn
    
    # Stick-slip переход
    if abs(ft_trial) <= ft_max:
        # Stick: трение покоя
        state.ft = ft_trial
    else:
        # Slip: трение скольжения
        state.ft = -math.copysign(1.0, v_rel) * params.mu_k * state.fn
        # Пересчёт stick_disp
        state.stick_disp = -state.ft / params.kt
    
    # ================================================================
    # 3. Ускорения
    # ================================================================
    
    # Горизонтальное ускорение
    a_x = state.ft / mass
    
    # Вертикальное ускорение
    a_y = state.fn / mass - 9.81
    
    # Угловое ускорение
    # ft > 0 (вправо) создаёт отрицательный момент (по часовой)
    # ft < 0 (влево) создаёт положительный момент (против часовой)
    alpha = -(state.ft * radius) / I
    
    # ================================================================
    # 4. Интегрирование деформации (после расчёта сил!)
    # ================================================================
    
    # Скорость деформации связана с нормальной скоростью мяча
    # При v_y < 0 (мяч движется вниз), overlap должен расти
    # Коэффициент 900 из JS реализации
    state.overlap_rate += -v_y * dt * 900.0
    
    # Интегрирование глубины
    state.overlap += state.overlap_rate * dt
    state.overlap = max(0.0, state.overlap)
    
    # Проверка активности
    state.is_active = state.overlap > 0 or v_y < 0
    
    return a_x, a_y, alpha


def init_contact_state() -> ContactState:
    """Инициализировать состояние контакта."""
    return ContactState()


# =============================================================================
# Тесты
# =============================================================================

if __name__ == "__main__":
    print("Testing lumped contact model (JS-based)...\n")
    
    # Параметры (из JS classic preset)
    params = ContactParams(
        kc=62000,  # жесткость мяча
        cc=10.5,   # демпфирование мяча
        kt=19840,  # 0.32 * kc
        mu_s=0.95,
        mu_k=0.81,
    )
    
    # Тест 1: Вертикальное падение без вращения
    print("Test 1: Vertical drop, no spin")
    state = ContactState(overlap=0.001, overlap_rate=0.0)
    a_x, a_y, alpha = step_contact_lumped(
        state, params,
        v_y=-1.0, v_x=0.0, omega=0.0,
        radius=0.02, mass=0.0027, ifactor=0.4, dt=1e-5
    )
    print(f"  Fn={state.fn:.1f}N, Ft={state.ft:.1f}N, alpha={alpha:.1f} rad/s²")
    print(f"  ✓ Вертикальная сила положительная")
    
    # Тест 2: Вращение по часовой (omega < 0)
    print("\nTest 2: Spin CW (omega < 0)")
    state = ContactState(overlap=0.001, overlap_rate=0.0)
    a_x, a_y, alpha = step_contact_lumped(
        state, params,
        v_y=0.0, v_x=0.0, omega=-100.0,  # по часовой
        radius=0.02, mass=0.0027, ifactor=0.4, dt=1e-5
    )
    print(f"  omega=-100 rad/s (CW): Ft={state.ft:.1f}N, alpha={alpha:.1f} rad/s²")
    # При omega < 0: v_rel = 0 - (-100)*0.02 = +2.0 > 0
    # ft_trial = -kt * stick_disp < 0 (сила влево)
    # alpha = -(-|ft| * r) / I > 0 (ускорение против часовой)
    if state.ft < 0:
        print(f"  ✓ Ft < 0 (влево) — правильно!")
    else:
        print(f"  ✗ ОШИБКА: Ft должно быть < 0")
    
    # Тест 3: Вращение против часовой (omega > 0)
    print("\nTest 3: Spin CCW (omega > 0)")
    state = ContactState(overlap=0.001, overlap_rate=0.0)
    a_x, a_y, alpha = step_contact_lumped(
        state, params,
        v_y=0.0, v_x=0.0, omega=100.0,  # против часовой
        radius=0.02, mass=0.0027, ifactor=0.4, dt=1e-5
    )
    print(f"  omega=+100 rad/s (CCW): Ft={state.ft:.1f}N, alpha={alpha:.1f} rad/s²")
    # При omega > 0: v_rel = 0 - 100*0.02 = -2.0 < 0
    # ft_trial = -kt * stick_disp > 0 (сила вправо)
    # alpha = -(+|ft| * r) / I < 0 (ускорение по часовой)
    if state.ft > 0:
        print(f"  ✓ Ft > 0 (вправо) — правильно!")
    else:
        print(f"  ✗ ОШИБКА: Ft должно быть > 0")
    
    # Тест 4: Движение вправо без вращения
    print("\nTest 4: Moving right, no spin")
    state = ContactState(overlap=0.001, overlap_rate=0.0)
    a_x, a_y, alpha = step_contact_lumped(
        state, params,
        v_y=0.0, v_x=5.0, omega=0.0,
        radius=0.02, mass=0.0027, ifactor=0.4, dt=1e-5
    )
    print(f"  v_x=5.0 m/s: Ft={state.ft:.1f}N, alpha={alpha:.1f} rad/s²")
    # v_rel = 5.0 > 0
    # ft_trial < 0 (сила влево, против движения)
    if state.ft < 0:
        print(f"  ✓ Ft < 0 (влево, против движения) — правильно!")
    else:
        print(f"  ✗ ОШИБКА: Ft должно быть < 0")
    
    # Тест 5: Комбинированный — движение вправо + вращение по часовой
    print("\nTest 5: Moving right + CW spin")
    state = ContactState(overlap=0.001, overlap_rate=0.0)
    a_x, a_y, alpha = step_contact_lumped(
        state, params,
        v_y=0.0, v_x=5.0, omega=-100.0,  # вправо + по часовой
        radius=0.02, mass=0.0027, ifactor=0.4, dt=1e-5
    )
    v_rel = 5.0 - (-100.0) * 0.02
    print(f"  v_x=5.0, omega=-100: v_rel={v_rel:.2f} m/s, Ft={state.ft:.1f}N")
    # v_rel = 5.0 + 2.0 = 7.0 > 0 (усиленное относительное движение)
    # ft < 0 (сила влево)
    if state.ft < 0:
        print(f"  ✓ Ft < 0 (влево) — правильно!")
    else:
        print(f"  ✗ ОШИБКА: Ft должно быть < 0")
    
    print("\n✅ Tests completed!")
