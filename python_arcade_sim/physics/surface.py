"""
Физика поверхности: дискретизация, слои, эквивалентные параметры, внутренние силы.

Модуль независим от arcade и используется только в физическом ядре.
"""

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
from physics.types import LayerParams, SurfaceParams, SurfaceState
from utils.math import clamp, exp_decay, safe_sqrt


# =============================================================================
# Эквивалентные параметры слоёв
# =============================================================================

@dataclass
class EquivalentSurfaceParams:
    """Эквивалентные параметры многослойной поверхности."""
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
    """Эквивалентные параметры шипов."""
    k_sh: float = 0.0
    """Жёсткость шипов."""
    h: float = 0.0
    """Высота шипов, м."""
    theta_max: float = 0.5
    """Максимальный наклон, рад."""


def compute_equivalent_params(params: SurfaceParams) -> EquivalentSurfaceParams:
    """
    Вычислить эквивалентные параметры по слоям.
    
    Используется гармоническое сложение жёсткостей и экспоненциальное
    взвешивание параметров верхних слоёв.
    
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
        cN_i = layer.thickness / max(layer.k_n, 1e-9)
        cT_i = layer.thickness / max(layer.k_t, 1e-9)
        sum_cN += cN_i
        sum_cT += cT_i
    
    # Эквивалентные жёсткости (обратные податливости)
    k_n_eq = 1.0 / max(sum_cN, 1e-9)
    k_t_eq = 1.0 / max(sum_cT, 1e-9)
    
    # ========================================================================
    # Экспоненциальное взвешивание параметров верхних слоёв
    # ========================================================================
    
    # Веса: exp(-i * p), где i — индекс слоя (0 = верхний)
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
    
    # Нормализация
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
    mu_s_eq *= fr_mul
    mu_k_eq *= fr_mul
    
    # Ограничение mu_k <= mu_s
    mu_k_eq = min(mu_k_eq, mu_s_eq)
    
    # ========================================================================
    # Расчёт массы на погонный метр
    # ========================================================================
    
    mass_per_meter = 0.0
    for layer in layers:
        density = MATERIAL_DENSITIES.get(layer.material, MATERIAL_DENSITIES["default"])
        # Масса = плотность * толщина * глубина
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
    """Силы, действующие на узлы поверхности."""
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
    
    Для каждого узла:
    1. Вертикально: базовая пружина/демпфер к основанию + связь с соседями
    2. Горизонтально: базовая пружина/демпфер к основанию + связь с соседями
    3. Edge stiffening на первых/последних узлах
    
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
    k_by = eq_params.k_n_eq * dx  # Вертикальная жёсткость к основанию
    c_by = eq_params.c_n_eq * dx  # Вертикальное демпфирование
    k_bx = eq_params.k_t_eq * dx  # Горизонтальная жёсткость к основанию
    c_bx = eq_params.c_t_eq * dx  # Горизонтальное демпфирование
    
    # Связи с соседями (горизонтальные/вертикальные)
    k_ly = eq_params.k_n_eq * dx * 0.1  # Вертикальная связь
    c_ly = eq_params.c_n_eq * dx * 0.1  # Вертикальная связь демпфер
    k_lx = eq_params.k_t_eq * dx * 0.1  # Горизонтальная связь
    c_lx = eq_params.c_t_eq * dx * 0.1  # Горизонтальная связь демпфер
    
    # Edge stiffening параметры
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
        f_y[i] += -k_by * state.u_y[i] - c_by * state.v_y[i]
        
        # Связь с соседями (вертикально)
        if i > 0:
            f_y[i] += k_ly * (state.u_y[i - 1] - state.u_y[i])
            f_y[i] += c_ly * (state.v_y[i - 1] - state.v_y[i])
        if i < n - 1:
            f_y[i] += k_ly * (state.u_y[i + 1] - state.u_y[i])
            f_y[i] += c_ly * (state.v_y[i + 1] - state.v_y[i])
        
        # Edge stiffening на краях
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
    
    1. Сначала скорости: v += (F / m) * dt
    2. Затем позиции: u += v * dt
    3. Клиппинг скоростей и смещений
    
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

def compute_ball_surface_y(ball_x: float, ball_y: float, radius: float, node_x: float) -> float:
    """
    Вычислить Y поверхности мяча в точке node_x.
    
    y_ball_surface = ball_y - sqrt(r^2 - dd^2)
    
    Args:
        ball_x: Позиция мяча по X.
        ball_y: Позиция мяча по Y (центр).
        radius: Радиус мяча.
        node_x: Позиция узла по X.
        
    Returns:
        Y поверхности мяча в точке node_x.
    """
    dd = ball_x - node_x
    # Защита от округлений: r^2 - dd^2 может стать слегка отрицательным
    under_sqrt = radius * radius - dd * dd
    dy = safe_sqrt(under_sqrt, 0.0)
    return ball_y - dy
