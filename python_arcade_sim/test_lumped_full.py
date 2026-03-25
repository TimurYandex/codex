"""
Тест полной симуляции с lumped model.

Интегрирует уравнения движения мяча с новой моделью контакта.
"""

import math
from physics.contact_lumped import ContactState, ContactParams, step_contact_lumped


def simulate_ball_impact(
    v_x0: float,
    v_y0: float,
    omega0: float,
    radius: float = 0.02,
    mass: float = 0.0027,
    ifactor: float = 0.4,
    dt: float = 1.2e-5,
    max_t: float = 0.08,
) -> dict:
    """
    Симулировать удар мяча о поверхность.

    Args:
        v_x0: Начальная горизонтальная скорость, м/с
        v_y0: Начальная вертикальная скорость, м/с (отрицательная = вниз)
        omega0: Начальная угловая скорость, рад/с (положительная = против часовой)
        radius: Радиус мяча, м
        mass: Масса мяча, кг
        ifactor: Фактор момента инерции
        dt: Шаг времени, с
        max_t: Максимальное время, с

    Returns:
        Словарь с результатами
    """
    params = ContactParams(
        kc=62000,
        cc=10.5,
        kt=19840,
        mu_s=0.95,
        mu_k=0.81,
    )
    
    state = ContactState()
    
    # Начальные условия
    v_x = v_x0
    v_y = v_y0
    omega = omega0
    overlap = 0.0
    overlap_rate = 0.0
    
    # Переменные для отслеживания
    t = 0.0
    contact_started = False
    contact_ended = False
    peak_fn = 0.0
    peak_overlap = 0.0
    
    # История
    history = []
    
    while t < max_t and not contact_ended:
        # ============================================================
        # Проверка начала контакта
        # ============================================================
        
        # Контакт начинается, когда мяч достигает поверхности
        # (упрощённо: всегда считаем контакт активным при v_y < 0)
        if v_y < 0 and not contact_started:
            contact_started = True
            overlap = 0.0001  # Начальное перекрытие
            overlap_rate = 0.0
        
        # ============================================================
        # Шаг контакта
        # ============================================================
        
        if contact_started and not contact_ended:
            state.overlap = overlap
            state.overlap_rate = overlap_rate
            
            a_x, a_y, alpha = step_contact_lumped(
                state, params,
                v_y, v_x, omega,
                radius, mass, ifactor, dt
            )
            
            # Обновление состояния
            overlap = state.overlap
            overlap_rate = state.overlap_rate
            
            # ========================================================
            # Интегрирование скоростей
            # ========================================================
            
            v_x += a_x * dt
            v_y += a_y * dt
            omega += alpha * dt
            
            # Отслеживание пиков
            peak_fn = max(peak_fn, state.fn)
            peak_overlap = max(peak_overlap, overlap)
            
            # Проверка окончания контакта
            if overlap <= 0 and v_y > 0.02 and t > 0.0016:
                contact_ended = True
            
            # Запись в историю
            history.append({
                't': t,
                'v_x': v_x,
                'v_y': v_y,
                'omega': omega,
                'fn': state.fn,
                'ft': state.ft,
                'overlap': overlap,
            })
        
        t += dt
    
    # ================================================================
    # Пост-контактный полёт (упрощённо)
    # ================================================================
    
    post_duration = 0.06
    post_t = 0.0
    while post_t < post_duration:
        v_y -= 9.81 * dt
        post_t += dt
        t += dt
    
    # ================================================================
    # Результаты
    # ================================================================
    
    v_out = math.sqrt(v_x**2 + v_y**2)
    angle_out = math.atan2(v_y, v_x) * 180.0 / math.pi
    contact_time = len(history) * dt
    
    return {
        'v_out': v_out,
        'omega_out': omega,
        'angle_out': angle_out,
        'contact_time_ms': contact_time * 1000,
        'peak_fn': peak_fn,
        'peak_overlap_mm': peak_overlap * 1000,
        'history': history,
    }


def run_tests():
    """Запустить тестовые сценарии."""
    print("Тестирование полной симуляции (lumped model)\n")
    print("=" * 100)
    
    # Сценарий 1: Вертикальное падение с вращением
    print("\n1. Вертикальное падение с вращением (v=5 м/с, angle=-80°, omega=-100 рад/с)")
    v_in = 5.0
    angle_in = -80.0
    v_x0 = v_in * math.cos(math.radians(angle_in))
    v_y0 = v_in * math.sin(math.radians(angle_in))
    result = simulate_ball_impact(v_x0, v_y0, omega0=-100.0)
    print(f"   Выход: v={result['v_out']:.2f} м/с, angle={result['angle_out']:.1f}°, ω={result['omega_out']:.1f} рад/с")
    print(f"   Контакт: {result['contact_time_ms']:.2f} мс, Fn_max={result['peak_fn']:.1f}Н")
    if abs(result['angle_out']) > 70:
        print("   ✓ Угол близок к вертикальному")
    else:
        print("   ✗ Угол слишком пологий")
    
    # Сценарий 2: Удар под 45° без вращения
    print("\n2. Удар под 45° без вращения (v=10 м/с, angle=-45°, omega=0)")
    v_in = 10.0
    angle_in = -45.0
    v_x0 = v_in * math.cos(math.radians(angle_in))
    v_y0 = v_in * math.sin(math.radians(angle_in))
    result = simulate_ball_impact(v_x0, v_y0, omega0=0.0)
    print(f"   Выход: v={result['v_out']:.2f} м/с, angle={result['angle_out']:.1f}°, ω={result['omega_out']:.1f} рад/с")
    print(f"   Контакт: {result['contact_time_ms']:.2f} мс, Fn_max={result['peak_fn']:.1f}Н")
    if result['angle_out'] > 45 and result['omega_out'] < 0:
        print("   ✓ angle > 45°, omega < 0 (по часовой)")
    else:
        print(f"   ✗ angle={result['angle_out']:.1f}° (ожидалось > 45°), omega={result['omega_out']:.1f}")
    
    # Сценарий 3: Удар под 45° с верхним вращением
    print("\n3. Удар под 45° с верхним вращением (v=10 м/с, angle=-45°, omega=+100 рад/с)")
    v_in = 10.0
    angle_in = -45.0
    v_x0 = v_in * math.cos(math.radians(angle_in))
    v_y0 = v_in * math.sin(math.radians(angle_in))
    result = simulate_ball_impact(v_x0, v_y0, omega0=100.0)
    print(f"   Выход: v={result['v_out']:.2f} м/с, angle={result['angle_out']:.1f}°, ω={result['omega_out']:.1f} рад/с")
    print(f"   Контакт: {result['contact_time_ms']:.2f} мс, Fn_max={result['peak_fn']:.1f}Н")
    if result['angle_out'] < 45:
        print("   ✓ angle < 45° (более пологий)")
    else:
        print(f"   ✗ angle={result['angle_out']:.1f}° (ожидалось < 45°)")
    
    # Сценарий 4: Удар под 45° с нижним вращением
    print("\n4. Удар под 45° с нижним вращением (v=10 м/с, angle=-45°, omega=-100 рад/с)")
    v_in = 10.0
    angle_in = -45.0
    v_x0 = v_in * math.cos(math.radians(angle_in))
    v_y0 = v_in * math.sin(math.radians(angle_in))
    result = simulate_ball_impact(v_x0, v_y0, omega0=-100.0)
    print(f"   Выход: v={result['v_out']:.2f} м/с, angle={result['angle_out']:.1f}°, ω={result['omega_out']:.1f} рад/с")
    print(f"   Контакт: {result['contact_time_ms']:.2f} мс, Fn_max={result['peak_fn']:.1f}Н")
    if result['angle_out'] > 60:
        print("   ✓ angle >> 45° (более вертикальный)")
    else:
        print(f"   ✗ angle={result['angle_out']:.1f}° (ожидалось >> 45°)")
    
    print("\n" + "=" * 100)


if __name__ == "__main__":
    run_tests()
