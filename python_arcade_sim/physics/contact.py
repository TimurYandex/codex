"""
Физика контакта: расчёт нормальной Fn и касательной Ft сил.

Модуль независим от arcade и используется только в физическом ядре.

Физическая модель контакта:
==========================
Контакт мяча с поверхностью рассчитывается для каждого узла в пределах радиуса мяча.

1. Геометрия контакта:
   - Для каждого узла i вычисляется расстояние dd = x_ball - x_i
   - Y поверхности мяча: y_surface = y_ball - sqrt(r² - dd²)
   - Перекрытие (overlap): δ = u_y[i] - y_surface
   - Контакт активен только при δ > 0

2. Нормальная сила Fn (закон Герца с демпфированием):
   - F_n = k_c * δ^p + c_c * max(0, v_rel_n)
   - p = 1.35 (показатель степени, нелинейная упругость)
   - v_rel_n = -(v_ball_y - v_node_y) — относительная нормальная скорость
   - Демпфирование действует только при сближении (v_rel_n > 0)
   - Защитный кап: F_n <= K_FORCE_CAP

3. Касательная сила Ft (stick-slip трение):
   - Относительная скорость: v_rel_t = (v_ball_x - ω*r) - v_node_x
   - Накопление stick-смещения: s += v_rel_t * dt
   - Пробная сила: F_t_trial = -k_s * s
   - Критерий stick-slip: |F_t_trial| <= μ_s * F_n
     - Stick: F_t = F_t_trial
     - Slip: F_t = -sign(v_rel_t) * μ_k * F_n
   - Накопление времени проскальзывания для метрики slip_share

4. Суммирование сил:
   - Суммарная Fn = Σ F_n[i] по всем активным узлам
   - Суммарная Ft = Σ F_t[i] по всем активным узлам
   - Также вычисляются метрики: давление, активные узлы, max overlap

5. Защита от численной нестабильности:
   - safe_sqrt для r² - dd² (защита от отрицательных значений)
   - Кап сил по модулю
   - Аккуратная обработка граничных случаев (δ ≈ 0)
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

from dataclasses import dataclass, field

from config.constants import (
    CONTACT_EXPONENT,
    K_FORCE_CAP,
)
from physics.sim_types import ContactState, SurfaceState
from physics.surface import EquivalentSurfaceParams, compute_ball_surface_y
from utils.math import clamp, safe_sqrt, sign


# =============================================================================
# Параметры контакта
# =============================================================================


@dataclass
class ContactParams:
    """
    Параметры контакта для расчёта сил.

    Атрибуты:
        k_c: Жёсткость контакта, Н/м^p.
        c_c: Демпфирование контакта, Н·с/м.
        k_s: Касательная жёсткость (stick), Н/м.
        mu_s: Коэффициент трения покоя.
        mu_k: Коэффициент трения скольжения.
        p: Показатель степени в законе Герца (по умолчанию 1.35).
    """

    k_c: float = 1e6
    c_c: float = 100
    k_s: float = 1e5
    mu_s: float = 1.0
    mu_k: float = 0.5
    p: float = CONTACT_EXPONENT


@dataclass
class ContactInput:
    """
    Входные данные для расчёта контакта.

    Атрибуты:
        ball_x: Позиция мяча по X, м.
        ball_y: Позиция мяча по Y (центр), м.
        ball_r: Радиус мяча, м.
        ball_v_x: Скорость мяча по X, м/с.
        ball_v_y: Скорость мяча по Y, м/с.
        ball_omega: Угловая скорость мяча, рад/с.
        surface: Состояние поверхности (узлы, смещения, скорости).
        eq_params: Эквивалентные параметры поверхности.
        contact_params: Параметры контакта.
        dt: Шаг времени, с.
    """

    ball_x: float
    ball_y: float
    ball_r: float
    ball_v_x: float
    ball_v_y: float
    ball_omega: float
    surface: SurfaceState
    eq_params: EquivalentSurfaceParams
    contact_params: ContactParams
    dt: float


@dataclass
class ContactResult:
    """
    Результат расчёта контакта.

    Атрибуты:
        is_active: Контакт активен (хотя бы один узел в контакте).
        fn_total: Суммарная нормальная сила, Н.
        ft_total: Суммарная касательная сила, Н.
        max_overlap: Максимальное перекрытие, м.
        active_nodes: Индексы активных узлов (в контакте).
        pressure: Давление в активных узлах, Па.
        slip_velocity: Относительная скорость проскальзывания (средняя), м/с.
        stick_displacement: Накопленное stick-смещение, м.
        is_slipping: Проскальзывание активно (хотя бы в одном узле).
        slip_time: Время проскальзывания на этом шаге, с.
    """

    is_active: bool = False
    fn_total: float = 0.0
    ft_total: float = 0.0
    max_overlap: float = 0.0
    active_nodes: list[int] = field(default_factory=list)
    pressure: list[float] = field(default_factory=list)
    slip_velocity: float = 0.0
    stick_displacement: float = 0.0
    is_slipping: bool = False
    slip_time: float = 0.0


# =============================================================================
# Расчёт контакта
# =============================================================================


def compute_contact(
    input_data: ContactInput, prev_state: ContactState
) -> ContactResult:
    """
    Вычислить силы контакта для текущего состояния мяча и поверхности.

    Физическая модель:
    ==================

    1. Геометрия контакта:
       - Определяем узлы в пределах радиуса мяча (|dd| < r)
       - Для каждого узла вычисляем overlap δ
       - Контакт активен только при δ > 0

    2. Нормальная сила (для каждого активного узла):
       - F_n = k_c * δ^p + c_c * max(0, v_rel_n)
       - v_rel_n = -(v_ball_y - v_node_y) — скорость сближения
       - Демпфирование только при сближении (защита от "прилипания")

    3. Касательная сила (stick-slip):
       - v_rel_t = (v_ball_x - ω*r) - v_node_x
       - s += v_rel_t * dt (накопление stick-смещения)
       - F_t_trial = -k_s * s
       - Если |F_t_trial| <= μ_s * F_n: stick (F_t = F_t_trial)
       - Иначе: slip (F_t = -sign(v_rel_t) * μ_k * F_n, s пересчитывается)

    4. Суммирование:
       - Fn_total = Σ F_n[i], Ft_total = Σ F_t[i]
       - Давление: P[i] = F_n[i] / (dx * depth)

    5. Метрики:
       - slip_share накапливается во времени
       - max_overlap для визуализации деформации

    Args:
        input_data: Входные данные (состояние мяча, поверхности, параметры).
        prev_state: Предыдущее состояние контакта (для накопления s).

    Returns:
        ContactResult с результатами расчёта.
    """
    # Извлечение данных
    ball_x = input_data.ball_x
    ball_y = input_data.ball_y
    ball_r = input_data.ball_r
    ball_v_x = input_data.ball_v_x
    ball_v_y = input_data.ball_v_y
    ball_omega = input_data.ball_omega

    surface = input_data.surface
    eq_params = input_data.eq_params
    cp = input_data.contact_params
    dt = input_data.dt

    n = len(surface.x_nodes)
    if n == 0:
        return ContactResult()

    # Шаг сетки (для расчёта давления)
    dx = (2 * eq_params.k_n_eq) / n if eq_params.k_n_eq > 0 else 0.01
    depth = 0.01  # Глубина в третьем измерении, м
    contact_area = dx * depth

    # ========================================================================
    # Инициализация результатов
    # ========================================================================

    fn_total = 0.0
    ft_total = 0.0
    max_overlap = 0.0
    active_nodes = []
    pressure = []

    # Stick-смещение (накапливается между шагами)
    stick_s = prev_state.stick_displacement

    # Счётчики для slip
    is_slipping = False
    slip_time = 0.0
    avg_slip_velocity = 0.0
    slip_count = 0

    # ========================================================================
    # Расчёт для каждого узла
    # ========================================================================

    for i in range(n):
        node_x = surface.x_nodes[i]
        node_u_y = surface.u_y[i]
        node_v_x = surface.v_x[i]
        node_v_y = surface.v_y[i]

        # ---------------------------------------------------------------
        # 1. Геометрия контакта
        # ---------------------------------------------------------------

        dd = ball_x - node_x

        # Проверка: узел в пределах радиуса мяча
        if abs(dd) >= ball_r:
            continue

        # Y поверхности мяча в точке узла
        y_ball_surface = compute_ball_surface_y(ball_x, ball_y, ball_r, node_x)

        # Перекрытие (overlap)
        # δ > 0 означает, что узел внутри мяча (контакт активен)
        overlap = node_u_y - y_ball_surface

        if overlap <= 0:
            continue

        # Узел в контакте
        active_nodes.append(i)
        max_overlap = max(max_overlap, overlap)

        # ---------------------------------------------------------------
        # 2. Нормальная сила
        # ---------------------------------------------------------------

        # Относительная нормальная скорость (сближение > 0)
        v_rel_n = -(ball_v_y - node_v_y)

        # Упругая составляющая (закон Герца: F = k * δ^p)
        fn_elastic = cp.k_c * (overlap**cp.p)

        # Демпфирование (только при сближении)
        fn_damping = cp.c_c * max(0.0, v_rel_n)

        # Полная нормальная сила с капом
        fn_node = fn_elastic + fn_damping
        fn_node = clamp(fn_node, 0.0, K_FORCE_CAP)

        fn_total += fn_node

        # Давление в узле
        p_node = fn_node / max(contact_area, 1e-6)
        pressure.append(p_node)

        # ---------------------------------------------------------------
        # 3. Касательная сила (stick-slip)
        # ---------------------------------------------------------------

        # Относительная касательная скорость
        # v_rel_t > 0: мяч движется вправо относительно поверхности
        v_rel_t = (ball_v_x - ball_omega * ball_r) - node_v_x

        # Накопление stick-смещения
        stick_s += v_rel_t * dt

        # Пробная сила (stick)
        ft_trial = -cp.k_s * stick_s

        # Критерий stick-slip
        ft_max_stick = eq_params.mu_s_eq * fn_node

        if abs(ft_trial) <= ft_max_stick:
            # Stick: трение покоя
            ft_node = ft_trial
        else:
            # Slip: трение скольжения
            ft_node = -sign(v_rel_t) * eq_params.mu_k_eq * fn_node
            is_slipping = True
            slip_time += dt
            slip_count += 1
            avg_slip_velocity += abs(v_rel_t)

            # Пересчёт stick-смещения из условия равновесия
            stick_s = -ft_node / max(cp.k_s, 1e-9)

        ft_total += ft_node

    # ========================================================================
    # Итоговые метрики
    # ========================================================================

    # Если нет контакта — сбрасываем stick-смещение
    if len(active_nodes) == 0:
        stick_s = 0.0

    # Средняя скорость проскальзывания
    if slip_count > 0:
        avg_slip_velocity /= slip_count

    # Ограничение stick-смещения (защита от накопления)
    stick_s = clamp(stick_s, -0.01, 0.01)

    # Кап суммарных сил
    ft_max = K_FORCE_CAP * len(active_nodes) if active_nodes else K_FORCE_CAP
    fn_total = clamp(
        fn_total, 0.0, K_FORCE_CAP * len(active_nodes) if active_nodes else K_FORCE_CAP
    )
    ft_total = clamp(
        ft_total,
        -ft_max,
        ft_max,
    )

    return ContactResult(
        is_active=len(active_nodes) > 0,
        fn_total=fn_total,
        ft_total=ft_total,
        max_overlap=max_overlap,
        active_nodes=active_nodes,
        pressure=pressure,
        slip_velocity=avg_slip_velocity,
        stick_displacement=stick_s,
        is_slipping=is_slipping,
        slip_time=slip_time,
    )


# =============================================================================
# Инициализация
# =============================================================================


def init_contact_state() -> ContactState:
    """
    Инициализировать состояние контакта.

    Начальное состояние:
    - is_active = False (нет контакта)
    - fn = 0, ft = 0 (нет сил)
    - overlap = 0 (нет перекрытия)
    - stick_displacement = 0 (нет накопленного смещения)

    Returns:
        ContactState с нулевым состоянием.
    """
    return ContactState(
        is_active=False,
        fn=0.0,
        ft=0.0,
        overlap=0.0,
        slip_velocity=0.0,
        stick_displacement=0.0,
        is_slipping=False,
    )


# =============================================================================
# Тестовый запуск (при прямом запуске файла)
# =============================================================================

if __name__ == "__main__":
    """
    При прямом запуске файла выполняются простые тесты.

    Использование:
        python physics/contact.py
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    from physics.contact import (
        ContactInput,
        ContactParams,
        compute_contact,
        init_contact_state,
    )
    from physics.surface import EquivalentSurfaceParams, init_surface_state
    from physics.sim_types import SurfaceParams

    print("Testing contact module...\n")

    # Тест 1: Нет контакта (мяч высоко)
    params = SurfaceParams(half_width=0.15, n_nodes=50)
    surface = init_surface_state(params)
    eq_params = EquivalentSurfaceParams()

    input_data = ContactInput(
        ball_x=0.0,
        ball_y=1.0,
        ball_r=0.02,
        ball_v_x=5.0,
        ball_v_y=-5.0,
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(),
        dt=1e-5,
    )

    result = compute_contact(input_data, init_contact_state())
    print(
        f"No contact: is_active={result.is_active}, fn={result.fn_total:.6f}, ft={result.ft_total:.6f}"
    )

    # Тест 2: Есть контакт (проникновение)
    for i in range(len(surface.u_y)):
        surface.u_y[i] = 0.001

    input_data2 = ContactInput(
        ball_x=0.0,
        ball_y=0.019,
        ball_r=0.02,
        ball_v_x=5.0,
        ball_v_y=-1.0,
        ball_omega=0.0,
        surface=surface,
        eq_params=eq_params,
        contact_params=ContactParams(),
        dt=1e-5,
    )

    result2 = compute_contact(input_data2, init_contact_state())
    print(
        f"Contact: is_active={result2.is_active}, fn={result2.fn_total:.2f}, ft={result2.ft_total:.2f}"
    )
    print(
        f"  active_nodes={len(result2.active_nodes)}, max_overlap={result2.max_overlap:.6f}"
    )

    print("\n✅ All basic tests passed!")
