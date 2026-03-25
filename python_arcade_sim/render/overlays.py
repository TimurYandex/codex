"""
Рендеринг: оверлеи (векторы сил, контактное пятно, карта давления).

Модуль использует arcade для отрисовки оверлеев поверх базовой сцены.
"""

import arcade

from physics.sim_types import RenderSnapshot, ContactState
from config.constants import K_FORCE_CAP


# Цвета для оверлеев
COLOR_FN = arcade.color.GREEN  # Нормальная сила
COLOR_FT = arcade.color.ORANGE  # Касательная сила
COLOR_V = arcade.color.BLUE  # Скорость мяча
COLOR_PRESSURE_LOW = arcade.color.YELLOW
COLOR_PRESSURE_HIGH = arcade.color.RED


def draw_vector(
    start_x: float,
    start_y: float,
    vx: float,
    vy: float,
    color: tuple[int, int, int],
    scale: float = 1.0,
    thickness: int = 3,
) -> None:
    """
    Нарисовать вектор (стрелку).
    
    Args:
        start_x, start_y: Начальная точка вектора.
        vx, vy: Компоненты вектора (в пикселях).
        color: Цвет вектора.
        scale: Масштаб длины вектора.
        thickness: Толщина линии.
    """
    end_x = start_x + vx * scale
    end_y = start_y + vy * scale
    
    # Длина вектора
    length = (vx ** 2 + vy ** 2) ** 0.5
    if length < 1:
        return  # Слишком короткий вектор
    
    # Рисуем линию
    arcade.draw_line(start_x, start_y, end_x, end_y, color, thickness)
    
    # Рисуем наконечник стрелки
    arrow_size = min(10, length / 4)
    
    # Угол вектора
    import math
    angle = math.atan2(vy, vx)
    
    # Два крыла наконечника
    left_angle = angle + math.pi * 0.8
    right_angle = angle - math.pi * 0.8
    
    left_x = end_x + arrow_size * math.cos(left_angle)
    left_y = end_y + arrow_size * math.sin(left_angle)
    right_x = end_x + arrow_size * math.cos(right_angle)
    right_y = end_y + arrow_size * math.sin(right_angle)
    
    arcade.draw_line(end_x, end_y, left_x, left_y, color, thickness)
    arcade.draw_line(end_x, end_y, right_x, right_y, color, thickness)


def draw_force_vectors(
    snapshot: RenderSnapshot,
    renderer: "Renderer",
    scale: float = 0.5,
) -> None:
    """
    Нарисовать векторы сил Fn и Ft.
    
    Args:
        snapshot: Снимок состояния.
        renderer: Рендерер для преобразования координат.
        scale: Масштаб длины векторов.
    """
    contact = snapshot.contact
    
    if not contact.is_active:
        return
    
    # Позиция мяча (центр)
    ball_x, ball_y = renderer.world_to_screen(snapshot.ball.x, snapshot.ball.y)
    
    # Вектор нормальной силы Fn (вверх, зелёный)
    # Нормализуем для визуализации
    fn_scaled = (contact.fn_total / K_FORCE_CAP) * 100 * scale
    draw_vector(ball_x, ball_y, 0, fn_scaled, COLOR_FN, scale=1.0)
    
    # Вектор касательной силы Ft (горизонтально, оранжевый)
    ft_scaled = (contact.ft_total / K_FORCE_CAP) * 100 * scale
    draw_vector(ball_x, ball_y, ft_scaled, 0, COLOR_FT, scale=1.0)
    
    # Подписи
    arcade.draw_text(
        f"Fn={contact.fn_total:.1f}N",
        ball_x + 10, ball_y + fn_scaled + 10,
        COLOR_FN, 12
    )
    arcade.draw_text(
        f"Ft={contact.ft_total:.1f}N",
        ball_x + ft_scaled + 10, ball_y - 20,
        COLOR_FT, 12
    )


def draw_velocity_vector(
    snapshot: RenderSnapshot,
    renderer: "Renderer",
    scale: float = 5.0,
) -> None:
    """
    Нарисовать вектор скорости мяча.
    
    Args:
        snapshot: Снимок состояния.
        renderer: Рендерер для преобразования координат.
        scale: Масштаб длины вектора.
    """
    ball = snapshot.ball
    
    # Позиция мяча
    ball_x, ball_y = renderer.world_to_screen(ball.x, ball.y)
    
    # Вектор скорости (синий)
    vx_px = ball.v_x * renderer.pixels_per_meter * 0.05 * scale
    vy_px = ball.v_y * renderer.pixels_per_meter * 0.05 * scale
    
    draw_vector(ball_x, ball_y, vx_px, vy_px, COLOR_V, scale=1.0, thickness=2)
    
    # Подпись
    v_mag = (ball.v_x ** 2 + ball.v_y ** 2) ** 0.5
    arcade.draw_text(
        f"v={v_mag:.2f}m/s",
        ball_x + vx_px + 10, ball_y + vy_px,
        COLOR_V, 12
    )


def draw_contact_patch(
    snapshot: RenderSnapshot,
    renderer: "Renderer",
) -> None:
    """
    Нарисовать контактное пятно и карту давления.
    
    Args:
        snapshot: Снимок состояния.
        renderer: Рендерер для преобразования координат.
    """
    contact = snapshot.contact
    surface = snapshot.surface
    
    if not contact.is_active or not contact.active_nodes:
        return
    
    # Рисуем активные узлы (контактное пятно)
    for i, node_idx in enumerate(contact.active_nodes):
        if node_idx >= len(surface.x_nodes):
            continue
        
        x = surface.x_nodes[node_idx]
        u_y = surface.u_y[node_idx] if node_idx < len(surface.u_y) else 0.0
        
        sx, sy = renderer.world_to_screen(x, u_y)
        
        # Цвет по давлению
        if i < len(contact.pressure):
            pressure = contact.pressure[i]
            # Нормализуем давление для цвета (0-1e6 Па)
            pressure_norm = min(pressure / 1e6, 1.0)
            
            # Интерполяция цвета: жёлтый → красный
            r = int(255)
            g = int(255 * (1 - pressure_norm))
            b = int(0)
            color = (r, g, b)
        else:
            color = COLOR_PRESSURE_LOW
        
        # Рисуем кружок в узле
        arcade.draw_circle_filled(sx, sy, 5, color)


def draw_overlays(
    snapshot: RenderSnapshot,
    renderer: "Renderer",
    show_fn: bool = True,
    show_ft: bool = True,
    show_v: bool = True,
    show_contact: bool = True,
) -> None:
    """
    Нарисовать все оверлеи.
    
    Args:
        snapshot: Снимок состояния.
        renderer: Рендерер для преобразования координат.
        show_fn: Показать вектор Fn.
        show_ft: Показать вектор Ft.
        show_v: Показать вектор скорости.
        show_contact: Показать контактное пятно.
    """
    if show_fn or show_ft:
        draw_force_vectors(snapshot, renderer)
    
    if show_v:
        draw_velocity_vector(snapshot, renderer)
    
    if show_contact:
        draw_contact_patch(snapshot, renderer)
