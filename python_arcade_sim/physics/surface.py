"""
Физика поверхности: дискретизация, слои, эквивалентные параметры, внутренние силы.

Модуль независим от arcade и используется только в физическом ядре.

Физическая модель поверхности:
==============================
Поверхность моделируется как дискретная сеть узлов, соединённых пружинами и демпферами.

1. Дискретизация:
   - Поверхность разбивается на n_nodes узлов по оси X
   - Каждый узел имеет степени свободы по X и Y (смещения u_x, u_y)
   - Каждый узел имеет скорости v_x, v_y

2. Многослойная структура:
   - Каждый слой имеет: толщину, жёсткости (k_n, k_t), демпфирование (c_n, c_t)
   - Коэффициенты трения: mu_s (покоя), mu_k (скольжения)
   - Режим шипов: none/out/in (влияет на трение и касательную силу)

3. Эквивалентные параметры:
   - Гармоническое сложение жёсткостей: 1/k_eq = Σ(t_i / k_i)
   - Экспоненциальное взвешивание: верхние слои влияют сильнее
   - Глобальный множитель трения: fr_mul * mu_s, mu_k

4. Внутренние силы:
   - Вертикально: пружина/демпфер к основанию + связи с соседями
   - Горизонтально: пружина/демпфер к основанию + связи с соседями
   - Edge stiffening: усиление краёв для имитации зафиксированного основания

5. Интегрирование:
   - Semi-implicit Euler: сначала скорости, потом позиции
   - Клиппинг: защита от чрезмерных смещений/скоростей
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

import math
from dataclasses import dataclass, field

from config.constants import (
    K_DISPLACEMENT_CAP,
    K_VELOCITY_CAP,
    MATERIAL_DENSITIES,
    SURFACE_DEPTH,
    SURFACE_HALF_WIDTH,
    SURFACE_NODES_DEFAULT,
)
from physics.sim_types import LayerParams, SurfaceParams, SurfaceState
from utils.math import clamp, exp_decay, safe_sqrt


# =============================================================================
# Эквивалентные параметры слоёв
# =============================================================================


@dataclass
class EquivalentSurfaceParams:
    """
    Эквивалентные параметры многослойной поверхности.

    Эти параметры используются для расчёта сил в узлах поверхности.

    Атрибуты:
        k_n_eq: Эквивалентная нормальная жёсткость, Н/м².
                Определяет сопротивление поверхности вертикальной деформации.
        k_t_eq: Эквивалентная касательная жёсткость, Н/м².
                Определяет сопротивление горизонтальному смещению.
        c_n_eq: Эквивалентное нормальное демпфирование, Н·с/м².
                Рассеяние энергии при вертикальной деформации.
        c_t_eq: Эквивалентное касательное демпфирование, Н·с/м².
                Рассеяние энергии при горизонтальном смещении.
        mu_s_eq: Эквивалентное трение покоя.
                Максимальное трение до начала проскальзывания.
        mu_k_eq: Эквивалентное трение скольжения.
                Трение во время проскальзывания (всегда <= mu_s).
        mass_per_meter: Масса на погонный метр, кг/м.
                Используется для расчёта инерции узлов.
        spike_params: Параметры шипов (если верхний слой имеет режим out/in).
    """

    k_n_eq: float = 0.0
    """Эквивалентная нормальная жёсткость, Н/м²."""
    k_t_eq: float = 0.0
    """Эквивалентная касательная жёсткость, Н/м²."""
    c_n_eq: float = 0.0
    """Эквивалентное нормальное демпфирование, Н·с/м²."""
    c_t_eq: float = 0.0
    """Эквивалентное касательное демпфирование, Н·с/м²."""
    mu_s_eq: float = 0.0
    """Эквивалентное трение покоя."""
    mu_k_eq: float = 0.0
    """Эквивалентное трение скольжения."""
    mass_per_meter: float = 0.0
    """Масса на погонный метр, кг/м."""
    spike_params: SpikeEquivalentParams | None = None
    """Параметры шипов (если есть)."""


@dataclass
class SpikeEquivalentParams:
    """
    Эквивалентные параметры шипов.

    Шипы моделируются как упругие элементы с наклоном θ.
    Наклон влияет на трение и касательную силу в контакте.

    Атрибуты:
        k_sh: Жёсткость шипов. Определяет сопротивление наклону.
        h: Высота шипов, м. Влияет на геометрию контакта.
        theta_max: Максимальный наклон, рад. Ограничение для устойчивости.
    """

    k_sh: float = 0.0
    """Жёсткость шипов."""
    h: float = 0.0
    """Высота шипов, м."""
    theta_max: float = 0.5
    """Максимальный наклон, рад."""


def compute_equivalent_params(params: SurfaceParams) -> EquivalentSurfaceParams:
    """
    Вычислить эквивалентные параметры по слоям.

    Физический смысл:
    =================
    Многослойная поверхность ведёт себя как единый материал с эффективными
    параметрами, которые зависят от свойств каждого слоя и их порядка.

    1. Гармоническое сложение жёсткостей:
       - Податливость слоя = толщина / жёсткость
       - Общая податливость = сумма податливостей всех слоёв
       - Эквивалентная жёсткость = 1 / общая податливость
       - Физика: последовательное соединение пружин (как в электричестве)

    2. Экспоненциальное взвешивание:
       - Вес слоя i: exp(-i * p), где p — коэффициент затухания
       - Верхние слои (i=0) имеют вес 1.0
       - Нижние слои затухают экспоненциально
       - Физика: деформация локализуется у поверхности, глубокие слои
         влияют меньше

    3. Глобальный множитель трения:
       - mu_s *= fr_mul, mu_k *= fr_mul
       - Позволяет регулировать трение без изменения параметров слоёв

    4. Ограничение mu_k <= mu_s:
       - Физическое требование: трение скольжения не может превышать
         трение покоя
       - Иначе модель становится неустойчивой

    5. Масса на погонный метр:
       - Сумма по слоям: ρ_i * t_i * depth
       - Используется для расчёта инерции узлов поверхности

    Args:
        params: Параметры поверхности со списком слоёв.

    Returns:
        EquivalentSurfaceParams с вычисленными эквивалентными параметрами.
    """
    if not params.layers:
        # Пустая поверхность — возврат нулевых параметров
        return EquivalentSurfaceParams()

    layers = params.layers
    fr_mul = params.fr_mul

    # ========================================================================
    # Гармоническое сложение нормальных/касательных жёсткостей
    # ========================================================================

    sum_cN: float = 0.0  # Сумма податливостей по нормали
    sum_cT: float = 0.0  # Сумма податливостей по касательной

    for layer in layers:
        # Податливость = толщина / жёсткость
        # Чем толще слой или мягче материал, тем больше податливость
        cN_i = layer.thickness / max(layer.k_n, 1e-9)
        cT_i = layer.thickness / max(layer.k_t, 1e-9)
        sum_cN += cN_i
        sum_cT += cT_i

    # Эквивалентные жёсткости (обратные податливости)
    # Если слои мягкие (большая податливость), то k_eq будет маленькой
    k_n_eq = 1.0 / max(sum_cN, 1e-9)
    k_t_eq = 1.0 / max(sum_cT, 1e-9)

    # ========================================================================
    # Экспоненциальное взвешивание параметров верхних слоёв
    # ========================================================================

    # Веса: exp(-i * p), где i — индекс слоя (0 = верхний)
    # p — коэффициент затухания из параметров слоя
    total_weight: float = 0.0
    weighted_k_n: float = 0.0
    weighted_k_t: float = 0.0
    weighted_c_n: float = 0.0
    weighted_c_t: float = 0.0
    weighted_mu_s: float = 0.0
    weighted_mu_k: float = 0.0

    for i, layer in enumerate(layers):
        weight = exp_decay(i, layer.p)
        total_weight += weight

        weighted_k_n += weight * layer.k_n
        weighted_k_t += weight * layer.k_t
        weighted_c_n += weight * layer.c_n
        weighted_c_t += weight * layer.c_t
        weighted_mu_s += weight * layer.mu_s
        weighted_mu_k += weight * layer.mu_k

    # Нормализация (деление на сумму весов)
    if total_weight > 1e-9:
        k_n_eq = weighted_k_n / total_weight
        k_t_eq = weighted_k_t / total_weight
        c_n_eq = weighted_c_n / total_weight
        c_t_eq = weighted_c_t / total_weight
        mu_s_eq = weighted_mu_s / total_weight
        mu_k_eq = weighted_mu_k / total_weight
    else:
        c_n_eq = 0.0
        c_t_eq = 0.0
        mu_s_eq = 0.0
        mu_k_eq = 0.0

    # Применение глобального множителя трения
    # fr_mul > 1 увеличивает трение, < 1 уменьшает
    mu_s_eq *= fr_mul
    mu_k_eq *= fr_mul

    # Ограничение mu_k <= mu_s (физическое требование)
    mu_k_eq = min(mu_k_eq, mu_s_eq)

    # ========================================================================
    # Расчёт массы на погонный метр
    # ========================================================================

    mass_per_meter = 0.0
    for layer in layers:
        density = MATERIAL_DENSITIES.get(layer.material, MATERIAL_DENSITIES["default"])
        # Масса = плотность * толщина * глубина (в третьем измерении)
        mass_per_meter += density * layer.thickness * SURFACE_DEPTH

    # ========================================================================
    # Параметры шипов (из верхнего слоя)
    # ========================================================================

    spike_params = None
    top_layer = layers[0]
    if top_layer.spike_mode.value != "none":
        spike_params = SpikeEquivalentParams(
            k_sh=top_layer.k_sh,
            h=top_layer.h,
            theta_max=0.5,  # Максимальный наклон рад
        )

    return EquivalentSurfaceParams(
        k_n_eq=k_n_eq,
        k_t_eq=k_t_eq,
        c_n_eq=c_n_eq,
        c_t_eq=c_t_eq,
        mu_s_eq=mu_s_eq,
        mu_k_eq=mu_k_eq,
        mass_per_meter=mass_per_meter,
        spike_params=spike_params,
    )


# =============================================================================
# Внутренние силы поверхности
# =============================================================================


@dataclass
class SurfaceForces:
    """
    Силы, действующие на узлы поверхности.

    Атрибуты:
        f_y: Вертикальные силы на узлы, Н.
             Положительные силы направлены вверх.
        f_x: Горизонтальные силы на узлы, Н.
             Положительные силы направлены вправо.
    """

    f_y: list[float] = field(default_factory=list)
    """Вертикальные силы на узлы, Н."""
    f_x: list[float] = field(default_factory=list)
    """Горизонтальные силы на узлы, Н."""


def compute_internal_forces(
    state: SurfaceState,
    params: SurfaceParams,
    eq_params: EquivalentSurfaceParams,
) -> SurfaceForces:
    """
    Вычислить внутренние силы поверхности (пружины/демпферы/связи).

    Физическая модель:
    ==================
    Поверхность моделируется как сеть узлов, соединённых пружинами и демпферами.

    1. Базовая пружина/демпфер к основанию:
       - F = -k * u - c * v
       - Возвращающая сила пропорциональна смещению (закон Гука)
       - Демпфирование пропорционально скорости (рассеяние энергии)

    2. Связи с соседями:
       - F = k * (u_neighbor - u_self) + c * (v_neighbor - v_self)
       - Передаёт силы между соседними узлами
       - Имитирует упругость материала поверхности

    3. Edge stiffening (усиление краёв):
       - Дополнительные k и c на первых/последних 3 узлах
       - Физический смысл: края поверхности зафиксированы в основании
       - Предотвращает "расползание" поверхности по краям

    4. Масштабирование параметров на узел:
       - k_node = k_eq * dx (dx — шаг сетки)
       - Чем мельче сетка, тем меньше жёсткость на узел

    Ожидаемые эффекты:
    - При ударе мяча узлы в центре прогибаются вниз
    - Соседние узлы тоже смещаются (передача через связи)
    - Края остаются почти неподвижными (edge stiffening)
    - После удара поверхность колеблется и затухает

    Args:
        state: Текущее состояние поверхности.
        params: Параметры поверхности.
        eq_params: Эквивалентные параметры слоёв.

    Returns:
        SurfaceForces с вычисленными силами.
    """
    n = len(state.x_nodes)
    if n == 0:
        return SurfaceForces()

    f_y = [0.0] * n
    f_x = [0.0] * n

    # Параметры для внутренних сил
    # Базовые жёсткости и демпфирование (на узел)
    dx = (2 * params.half_width) / (n - 1) if n > 1 else params.half_width
    node_mass = eq_params.mass_per_meter * dx / max(n, 1)

    # Жёсткости на узел (распределяем эквивалентные параметры)
    # Умножение на dx переводит удельные параметры (на м²) в параметры узла
    k_by = eq_params.k_n_eq * dx  # Вертикальная жёсткость к основанию
    c_by = eq_params.c_n_eq * dx  # Вертикальное демпфирование
    k_bx = eq_params.k_t_eq * dx  # Горизонтальная жёсткость к основанию
    c_bx = eq_params.c_t_eq * dx  # Горизонтальное демпфирование

    # Связи с соседями (горизонтальные/вертикальные)
    # Коэффициент 0.1 — калибровка, чтобы связи были слабее основания
    k_ly = eq_params.k_n_eq * dx * 0.1  # Вертикальная связь
    c_ly = eq_params.c_n_eq * dx * 0.1  # Вертикальная связь демпфер
    k_lx = eq_params.k_t_eq * dx * 0.1  # Горизонтальная связь
    c_lx = eq_params.c_t_eq * dx * 0.1  # Горизонтальная связь демпфер

    # Edge stiffening параметры
    # Усиление в 10 раз делает края почти неподвижными
    edge_stiffness = k_by * 10.0
    edge_damping = c_by * 2.0
    edge_nodes = 3  # Количество усиленных узлов на краю

    # ========================================================================
    # Расчёт сил для каждого узла
    # ========================================================================

    for i in range(n):
        # ---------------------------------------------------------------
        # Вертикальные силы
        # ---------------------------------------------------------------

        # Базовая пружина/демпфер к основанию
        # Отрицательный знак: сила направлена против смещения
        f_y[i] += -k_by * state.u_y[i] - c_by * state.v_y[i]

        # Связь с соседями (вертикально)
        # Сосед тянет узел к своей позиции
        if i > 0:
            f_y[i] += k_ly * (state.u_y[i - 1] - state.u_y[i])
            f_y[i] += c_ly * (state.v_y[i - 1] - state.v_y[i])
        if i < n - 1:
            f_y[i] += k_ly * (state.u_y[i + 1] - state.u_y[i])
            f_y[i] += c_ly * (state.v_y[i + 1] - state.v_y[i])

        # Edge stiffening на краях
        # factor плавно спадает от края к центру (1.0 → 0.0)
        if i < edge_nodes:
            factor = (edge_nodes - i) / edge_nodes
            f_y[i] += -edge_stiffness * state.u_y[i] * factor
            f_y[i] += -edge_damping * state.v_y[i] * factor
        if i >= n - edge_nodes:
            factor = (i - (n - edge_nodes) + 1) / edge_nodes
            f_y[i] += -edge_stiffness * state.u_y[i] * factor
            f_y[i] += -edge_damping * state.v_y[i] * factor

        # ---------------------------------------------------------------
        # Горизонтальные силы
        # ---------------------------------------------------------------

        # Базовая пружина/демпфер к основанию
        f_x[i] += -k_bx * state.u_x[i] - c_bx * state.v_x[i]

        # Связь с соседями (горизонтально)
        if i > 0:
            f_x[i] += k_lx * (state.u_x[i - 1] - state.u_x[i])
            f_x[i] += c_lx * (state.v_x[i - 1] - state.v_x[i])
        if i < n - 1:
            f_x[i] += k_lx * (state.u_x[i + 1] - state.u_x[i])
            f_x[i] += c_lx * (state.v_x[i + 1] - state.v_x[i])

    return SurfaceForces(f_y=f_y, f_x=f_x)


# =============================================================================
# Интегратор поверхности (semi-implicit Euler)
# =============================================================================


def integrate_surface(
    state: SurfaceState,
    forces: SurfaceForces,
    eq_params: EquivalentSurfaceParams,
    params: SurfaceParams,
    dt: float,
) -> None:
    """
    Интегрировать уравнения движения поверхности (semi-implicit Euler).

    Физическая модель:
    ==================
    Уравнение движения для каждого узла:
        m * a = F_internal + F_external
        a = F / m
        v += a * dt
        u += v * dt

    Semi-implicit Euler (симплектический Эйлер):
    - Сначала обновляем скорости: v_new = v_old + a * dt
    - Затем обновляем позиции: u_new = u_old + v_new * dt
    - Преимущество: лучше сохраняет энергию, чем явный Эйлер

    Клиппинг (ограничение):
    - Скорости: |v| <= K_VELOCITY_CAP (100 м/с)
    - Смещения: |u| <= K_DISPLACEMENT_CAP (0.01 м)
    - Защита от численной нестабильности и "разлёта" модели

    Ожидаемые эффекты:
    - При ударе мяча узлы ускоряются вниз (отрицательное u_y)
    - Затем возвращаются вверх (возвращающая сила пружин)
    - Колебания затухают со временем (демпфирование)

    Args:
        state: Состояние поверхности (обновляется).
        forces: Силы, действующие на узлы.
        eq_params: Эквивалентные параметры.
        params: Параметры поверхности.
        dt: Шаг времени.
    """
    n = len(state.x_nodes)
    if n == 0:
        return

    # Масса на узел
    dx = (2 * params.half_width) / (n - 1) if n > 1 else params.half_width
    node_mass = max(eq_params.mass_per_meter * dx / max(n, 1), 1e-6)

    # ========================================================================
    # Обновление скоростей и позиций
    # ========================================================================

    for i in range(n):
        # Вертикально
        # Второй закон Ньютона: a = F / m
        a_y = forces.f_y[i] / node_mass
        state.v_y[i] += a_y * dt
        state.u_y[i] += state.v_y[i] * dt

        # Горизонтально
        a_x = forces.f_x[i] / node_mass
        state.v_x[i] += a_x * dt
        state.u_x[i] += state.v_x[i] * dt

    # ========================================================================
    # Клиппинг скоростей и смещений (защита от нестабильности)
    # ========================================================================

    for i in range(n):
        state.v_y[i] = clamp(state.v_y[i], -K_VELOCITY_CAP, K_VELOCITY_CAP)
        state.v_x[i] = clamp(state.v_x[i], -K_VELOCITY_CAP, K_VELOCITY_CAP)
        state.u_y[i] = clamp(state.u_y[i], -K_DISPLACEMENT_CAP, K_DISPLACEMENT_CAP)
        state.u_x[i] = clamp(state.u_x[i], -K_DISPLACEMENT_CAP, K_DISPLACEMENT_CAP)


# =============================================================================
# Инициализация поверхности
# =============================================================================


def init_surface_state(params: SurfaceParams) -> SurfaceState:
    """
    Инициализировать состояние поверхности.

    Геометрия:
    - Равномерная сетка из n_nodes узлов
    - Диапазон X: от -half_width до +half_width
    - Шаг сетки: dx = (2 * half_width) / (n_nodes - 1)

    Начальное состояние:
    - Все смещения u_y, u_x = 0 (поверхность недеформирована)
    - Все скорости v_y, v_x = 0 (поверхность покоится)
    - active_nodes = [] (нет контакта)
    - pressure = [] (нет давления)

    Args:
        params: Параметры поверхности.

    Returns:
        SurfaceState с инициализированными массивами.
    """
    n = params.n_nodes
    hw = params.half_width

    # Равномерная сетка от -hw до +hw
    dx = (2 * hw) / (n - 1) if n > 1 else 0

    return SurfaceState(
        x_nodes=[-hw + i * dx for i in range(n)],
        u_y=[0.0] * n,
        u_x=[0.0] * n,
        v_y=[0.0] * n,
        v_x=[0.0] * n,
        active_nodes=[],
        pressure=[],
    )


# =============================================================================
# Геометрия контакта (вычисление y_ball_surface)
# =============================================================================


def compute_ball_surface_y(
    ball_x: float, ball_y: float, radius: float, node_x: float
) -> float:
    """
    Вычислить Y поверхности мяча в точке node_x.

    Геометрия:
    ==========
    Мяч — окружность радиуса r с центром в (ball_x, ball_y).

    Уравнение окружности:
        (x - ball_x)² + (y - ball_y)² = r²

    Для данной точки node_x (по X) находим Y нижней полуокружности:
        y = ball_y - sqrt(r² - dd²)
    где dd = ball_x - node_x (горизонтальное расстояние от центра мяча)

    Защита от округлений:
    - При dd ≈ r выражение r² - dd² может стать слегка отрицательным
    - safe_sqrt возвращает 0 в этом случае (вместо NaN)

    Ожидаемые значения:
    - В центре (node_x = ball_x): y = ball_y - r (нижняя точка мяча)
    - На краю (node_x = ball_x ± r): y = ball_y (центр мяча)
    - За пределами (|dd| > r): y = ball_y (защита)

    Args:
        ball_x: Позиция мяча по X.
        ball_y: Позиция мяча по Y (центр).
        radius: Радиус мяча.
        node_x: Позиция узла по X.

    Returns:
        Y поверхности мяча в точке node_x (нижняя полуокружность).
    """
    dd = ball_x - node_x
    # Защита от округлений: r^2 - dd^2 может стать слегка отрицательным
    under_sqrt = radius * radius - dd * dd
    dy = safe_sqrt(under_sqrt, 0.0)
    return ball_y - dy


# =============================================================================
# Тестовый запуск (при прямом запуске файла)
# =============================================================================

if __name__ == "__main__":
    """
    При прямом запуске файла выполняются простые тесты.

    Использование:
        python physics/surface.py
    """
    import sys
    from pathlib import Path

    # Добавляем корень проекта в path для импортов
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from physics.surface import (
        EquivalentSurfaceParams,
        compute_ball_surface_y,
        compute_equivalent_params,
        compute_internal_forces,
        init_surface_state,
        integrate_surface,
    )
    from physics.sim_types import LayerParams, SpikeMode, SurfaceParams

    print("Testing surface module...\n")

    # Тест инициализации поверхности
    params = SurfaceParams(
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
            ),
        ],
        half_width=0.15,
        n_nodes=50,
    )

    state = init_surface_state(params)
    print(
        f"init_surface_state: n_nodes={len(state.x_nodes)}, x_range=[{state.x_nodes[0]:.3f}, {state.x_nodes[-1]:.3f}]"
    )

    # Тест эквивалентных параметров
    eq = compute_equivalent_params(params)
    print(
        f"compute_equivalent_params: k_n_eq={eq.k_n_eq:.2f}, mu_s_eq={eq.mu_s_eq:.2f}"
    )

    # Тест внутренних сил
    forces = compute_internal_forces(state, params, eq)
    print(
        f"compute_internal_forces: n_forces={len(forces.f_y)}, all_zero={all(f == 0 for f in forces.f_y)}"
    )

    # Тест геометрии мяча
    y_center = compute_ball_surface_y(ball_x=0.0, ball_y=0.02, radius=0.02, node_x=0.0)
    y_edge = compute_ball_surface_y(ball_x=0.0, ball_y=0.02, radius=0.02, node_x=0.02)
    print(f"compute_ball_surface_y: y_center={y_center:.6f}, y_edge={y_edge:.6f}")

    print("\n✅ All basic tests passed!")
