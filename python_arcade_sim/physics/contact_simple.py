"""
Упрощенная модель контакта мяча с поверхностью (lumped parameter model).

Вместо сети узлов используется единая точка контакта с параметрами:
- overlap — перекрытие мяча с поверхностью (глубина деформации)
- overlap_rate — скорость перекрытия
- stick_disp — касательное смещение (для трения)

Физическая модель:
==================

1. Нормальная сила (закон Герца с демпфированием):
   Fn = kc * overlap^1.35 + cc * max(0, overlap_rate)

2. Касательная сила (stick-slip трение):
   v_rel = v_t - omega * r  (относительная скорость проскальзывания)
   stick_disp += v_rel * dt
   ft_trial = -kt * stick_disp
   ft_max = mu_s * Fn
   
   если |ft_trial| <= ft_max:
       ft = ft_trial  (stick, трение покоя)
   иначе:
       ft = -sign(v_rel) * mu_k * Fn  (slip, трение скольжения)
       stick_disp = -ft / kt

3. Угловое ускорение:
   alpha = -(ft * r) / I

4. Интегрирование:
   a_n = Fn / m - g
   a_t = ft / m
   
   v_n += a_n * dt
   v_t += a_t * dt
   omega += alpha * dt
   
   overlap_rate += -v_n * dt * K_coupling
   overlap += overlap_rate * dt
   overlap = max(0, overlap)
"""

import math
from dataclasses import dataclass


@dataclass
class ContactState:
    """Состояние контакта."""
    overlap: float = 0.0  # Перекрытие, м
    overlap_rate: float = 0.0  # Скорость перекрытия, м/с
    stick_disp: float = 0.0  # Касательное смещение, м
    fn: float = 0.0  # Нормальная сила, Н
    ft: float = 0.0  # Касательная сила, Н
    is_active: bool = False  # Контакт активен


@dataclass
class ContactParams:
    """Параметры контакта."""
    kc: float = 5000.0  # Нормальная жёсткость, Н/м^1.35
    cc: float = 50.0  # Нормальное демпфирование, Н·с/м
    kt: float = 1600.0  # Касательная жёсткость, Н/м
    mu_s: float = 0.95  # Трение покоя
    mu_k: float = 0.81  # Трение скольжения
    exponent: float = 1.35  # Показатель степени в законе Герца
    coupling: float = 900.0  # Коэффициент связи для overlap_rate


def step_contact(
    state: ContactState,
    params: ContactParams,
    v_n: float,  # Нормальная скорость (положительная = вверх)
    v_t: float,  # Касательная скорость (положительная = вправо)
    omega: float,  # Угловая скорость (положительная = против часовой)
    radius: float,  # Радиус мяча, м
    mass: float,  # Масса мяча, кг
    ifactor: float,  # Фактор момента инерции
    dt: float,  # Шаг времени, с
) -> tuple[float, float, float]:
    """
    Шаг интегрирования контакта.

    Args:
        state: Состояние контакта (обновляется)
        params: Параметры контакта
        v_n: Нормальная скорость мяча (положительная = вверх)
        v_t: Касательная скорость мяча (положительная = вправо)
        omega: Угловая скорость мяча (положительная = против часовой)
        radius: Радиус мяча, м
        mass: Масса мяча, кг
        ifactor: Фактор момента инерции (0.4 для сплошного, 0.67 для полого)
        dt: Шаг времени, с

    Returns:
        (a_n, a_t, alpha) — ускорения
    """
    # Момент инерции: I = ifactor * m * r²
    I = ifactor * mass * radius * radius
    
    # ================================================================
    # 1. Нормальная сила (закон Герца с демпфированием)
    # ================================================================
    
    # Упругая составляющая
    fn_elastic = params.kc * (state.overlap ** params.exponent)
    
    # Демпфирование (только при сближении)
    fn_damping = params.cc * max(0.0, -state.overlap_rate)
    
    # Полная нормальная сила
    state.fn = fn_elastic + fn_damping
    state.fn = max(0.0, state.fn)  # Fn не может быть отрицательной
    
    # ================================================================
    # 2. Касательная сила (stick-slip)
    # ================================================================
    
    # Относительная скорость проскальзывания
    # v_rel > 0: мяч движется вправо относительно поверхности
    # v_rel = v_t - omega * r
    v_rel = v_t - omega * radius
    
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
        state.ft = -math.copysign(1, v_rel) * params.mu_k * state.fn
        # Пересчёт stick_disp из условия равновесия
        state.stick_disp = -state.ft / params.kt
    
    # ================================================================
    # 3. Ускорения
    # ================================================================
    
    # Нормальное ускорение
    a_n = state.fn / mass - 9.81
    
    # Касательное ускорение
    a_t = state.ft / mass
    
    # Угловое ускорение
    # ft > 0 (вправо) создаёт отрицательный момент (по часовой)
    alpha = -(state.ft * radius) / I
    
    # ================================================================
    # 4. Интегрирование деформации
    # ================================================================
    
    # Связь нормальной скорости с rate деформации
    # При v_n < 0 (мяч движется вниз) overlap_rate должен расти
    state.overlap_rate += -v_n * dt * params.coupling
    
    # Интегрирование overlap
    state.overlap += state.overlap_rate * dt
    state.overlap = max(0.0, state.overlap)
    
    # Проверка активности контакта
    state.is_active = state.overlap > 0 or v_n < 0
    
    return a_n, a_t, alpha


def init_contact_state() -> ContactState:
    """Инициализировать состояние контакта."""
    return ContactState()


# =============================================================================
# Тесты
# =============================================================================

if __name__ == "__main__":
    print("Testing lumped contact model...\n")
    
    # Параметры
    params = ContactParams(
        kc=5000,
        cc=50,
        kt=1600,
        mu_s=0.95,
        mu_k=0.81,
    )
    
    state = init_contact_state()
    
    # Тест 1: Вертикальное падение без вращения
    print("Test 1: Vertical drop, no spin")
    state = ContactState(overlap=0.001, overlap_rate=0.0)
    a_n, a_t, alpha = step_contact(
        state, params,
        v_n=-1.0, v_t=0.0, omega=0.0,
        radius=0.02, mass=0.0027, ifactor=0.4, dt=1e-5
    )
    print(f"  Fn={state.fn:.1f}N, Ft={state.ft:.1f}N, alpha={alpha:.1f} rad/s²")
    
    # Тест 2: Касательное движение с вращением
    print("\nTest 2: Tangential motion with spin")
    state = ContactState(overlap=0.001, overlap_rate=0.0)
    
    # Вращение по часовой (omega < 0) должно создавать Ft < 0
    a_n, a_t, alpha = step_contact(
        state, params,
        v_n=0.0, v_t=0.0, omega=-100.0,  # по часовой
        radius=0.02, mass=0.0027, ifactor=0.4, dt=1e-5
    )
    print(f"  omega=-100 rad/s (CW): Ft={state.ft:.1f}N (ожидалось < 0)")
    
    # Вращение против часовой (omega > 0) должно создавать Ft > 0
    state = ContactState(overlap=0.001, overlap_rate=0.0)
    a_n, a_t, alpha = step_contact(
        state, params,
        v_n=0.0, v_t=0.0, omega=100.0,  # против часовой
        radius=0.02, mass=0.0027, ifactor=0.4, dt=1e-5
    )
    print(f"  omega=+100 rad/s (CCW): Ft={state.ft:.1f}N (ожидалось > 0)")
    
    # Тест 3: Проверка v_rel
    print("\nTest 3: Relative velocity check")
    state = ContactState(overlap=0.001, overlap_rate=0.0)
    v_t = 5.0
    omega = -100.0  # по часовой
    v_rel = v_t - omega * 0.02
    print(f"  v_t={v_t}, omega={omega}: v_rel = {v_rel:.2f} м/с")
    print(f"  (нижняя точка мяча движется вправо со скоростью {abs(omega * 0.02):.1f} м/с)")
    
    print("\n✅ Tests completed!")
