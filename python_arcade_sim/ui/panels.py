"""
UI Panels: панели управления интерфейса.

Отрисовка панелей управления параметрами симуляции.
"""

import arcade

from ui.state import UIState, UIMode


# Цвета UI
COLOR_PANEL_BG = arcade.color.DARK_GRAY
COLOR_PANEL_BORDER = arcade.color.GRAY
COLOR_BUTTON = arcade.color.BLUE
COLOR_BUTTON_HOVER = arcade.color.LIGHT_BLUE
COLOR_BUTTON_DISABLED = arcade.color.DARK_BLUE
COLOR_TEXT = arcade.color.WHITE
COLOR_LABEL = arcade.color.LIGHT_GRAY


def draw_panel_background(
    x: int,
    y: int,
    width: int,
    height: int,
    title: str = "",
) -> None:
    """
    Нарисовать фон панели.

    Args:
        x, y: Позиция левого нижнего угла.
        width, height: Размеры панели.
        title: Заголовок панели.
    """
    # Фон
    arcade.draw_lbwh_rectangle_filled(x, y, width, height, COLOR_PANEL_BG)

    # Граница
    arcade.draw_lbwh_rectangle_outline(x, y, width, height, COLOR_PANEL_BORDER, 1)

    # Заголовок
    if title:
        arcade.draw_text(
            title, x + 10, y + height - 20, COLOR_TEXT, 12, anchor_x="left"
        )


def draw_button(
    x: int,
    y: int,
    width: int,
    height: int,
    label: str,
    enabled: bool = True,
    hover: bool = False,
) -> None:
    """
    Нарисовать кнопку.

    Args:
        x, y: Позиция левого нижнего угла.
        width, height: Размеры кнопки.
        label: Текст кнопки.
        enabled: Активна ли кнопка.
        hover: Наведён ли курсор.
    """
    if not enabled:
        color = COLOR_BUTTON_DISABLED
    elif hover:
        color = COLOR_BUTTON_HOVER
    else:
        color = COLOR_BUTTON

    arcade.draw_lbwh_rectangle_filled(x, y, width, height, color)

    arcade.draw_lbwh_rectangle_outline(x, y, width, height, COLOR_PANEL_BORDER, 1)

    arcade.draw_text(
        label,
        x + width / 2,
        y + height / 2,
        COLOR_TEXT,
        11,
        anchor_x="center",
        anchor_y="center",
    )


def draw_slider(
    x: int,
    y: int,
    width: int,
    height: int,
    value: float,
    min_val: float,
    max_val: float,
    label: str = "",
) -> None:
    """
    Нарисовать слайдер.

    Args:
        x, y: Позиция левого нижнего угла.
        width, height: Размеры слайдера.
        value: Текущее значение.
        min_val, max_val: Диапазон значений.
        label: Подпись.
    """
    # Подпись
    if label:
        arcade.draw_text(
            f"{label}: {value:.3f}", x, y + height + 5, COLOR_LABEL, 10, anchor_x="left"
        )

    # Фон слайдера
    arcade.draw_lbwh_rectangle_filled(x, y, width, height, COLOR_PANEL_BG)

    arcade.draw_lbwh_rectangle_outline(x, y, width, height, COLOR_PANEL_BORDER, 1)

    # Ползунок
    ratio = (value - min_val) / max(max_val - min_val, 1e-9)
    handle_x = x + ratio * width
    handle_size = height + 4

    arcade.draw_rectangle_filled(
        handle_x, y + height / 2, handle_size, handle_size, COLOR_BUTTON
    )


def draw_label_value(
    x: int,
    y: int,
    label: str,
    value: str,
) -> None:
    """
    Нарисовать пару label-value.

    Args:
        x, y: Позиция.
        label: Текст метки.
        value: Текст значения.
    """
    arcade.draw_text(label, x, y, COLOR_LABEL, 10, anchor_x="left")

    arcade.draw_text(value, x + 120, y, COLOR_TEXT, 10, anchor_x="left")


def draw_collision_panel(
    ui_state: UIState,
    x: int,
    y: int,
    width: int = 200,
    height: int = 150,
) -> None:
    """
    Нарисовать панель параметров столкновения.

    Args:
        ui_state: Состояние UI.
        x, y: Позиция.
        width, height: Размеры.
    """
    draw_panel_background(x, y, width, height, "Collision")

    py = y + height - 45

    draw_label_value(x + 10, py, "Speed:", f"{ui_state.speed:.1f} m/s")
    draw_label_value(x + 10, py - 20, "Angle:", f"{ui_state.angle:.1f} deg")
    draw_label_value(x + 10, py - 40, "Spin:", f"{ui_state.spin:.1f} rad/s")
    draw_label_value(x + 10, py - 60, "Spin Dir:", ui_state.spin_dir)


def draw_ball_panel(
    ui_state: UIState,
    x: int,
    y: int,
    width: int = 200,
    height: int = 150,
) -> None:
    """
    Нарисовать панель параметров мяча.

    Args:
        ui_state: Состояние UI.
        x, y: Позиция.
        width, height: Размеры.
    """
    draw_panel_background(x, y, width, height, "Ball")

    py = y + height - 45

    ball_type = "Hollow" if ui_state.ball_is_hollow else "Solid"
    draw_label_value(x + 10, py, "Type:", ball_type)
    draw_label_value(
        x + 10, py - 20, "Radius:", f"{ui_state.ball_radius * 1000:.1f} mm"
    )
    draw_label_value(x + 10, py - 40, "Mass:", f"{ui_state.ball_mass * 1000:.1f} g")
    draw_label_value(x + 10, py - 60, "Stiffness:", f"{ui_state.ball_k / 1e6:.1f} MN/m")


def draw_surface_panel(
    ui_state: UIState,
    x: int,
    y: int,
    width: int = 250,
    height: int = 200,
) -> None:
    """
    Нарисовать панель параметров поверхности.

    Args:
        ui_state: Состояние UI.
        x, y: Позиция.
        width, height: Размеры.
    """
    draw_panel_background(x, y, width, height, "Surface")

    py = y + height - 45

    draw_label_value(x + 10, py, "Layers:", str(len(ui_state.surface_layers)))
    draw_label_value(x + 10, py - 20, "Friction Mul:", f"{ui_state.surface_fr_mul:.2f}")

    # Список слоёв
    for i, layer in enumerate(ui_state.surface_layers[:3]):
        arcade.draw_text(
            f"  {i + 1}. {layer.title} ({layer.thickness * 1000:.1f}mm)",
            x + 10,
            py - 45 - i * 20,
            COLOR_TEXT,
            10,
            anchor_x="left",
        )

    if len(ui_state.surface_layers) > 3:
        arcade.draw_text(
            f"  ... and {len(ui_state.surface_layers) - 3} more",
            x + 10,
            py - 105,
            COLOR_LABEL,
            10,
            anchor_x="left",
        )


def draw_animation_panel(
    ui_state: UIState,
    x: int,
    y: int,
    width: int = 200,
    height: int = 100,
) -> None:
    """
    Нарисовать панель анимации.

    Args:
        ui_state: Состояние UI.
        x, y: Позиция.
        width, height: Размеры.
    """
    draw_panel_background(x, y, width, height, "Animation")

    py = y + height - 45

    draw_label_value(x + 10, py, "Time Scale:", f"{ui_state.time_scale:.4f}")
    draw_label_value(
        x + 10, py - 20, "View Scale:", f"{ui_state.view_scale * 100:.0f}%"
    )
    draw_label_value(
        x + 10, py - 40, "Overlays:", "On" if ui_state.show_overlays else "Off"
    )


def draw_action_buttons(
    ui_state: UIState,
    x: int,
    y: int,
    button_width: int = 100,
    button_height: int = 30,
) -> None:
    """
    Нарисовать кнопки действий.

    Args:
        ui_state: Состояние UI.
        x, y: Позиция.
        button_width, button_height: Размеры кнопок.
    """
    spacing = 10

    # Кнопка Запустить/Пауза
    is_running = ui_state.ui_mode == UIMode.RUNNING
    run_label = "Pause" if is_running else "Run"
    draw_button(x, y, button_width, button_height, run_label, enabled=True)

    # Кнопка Сравнить
    draw_button(
        x + button_width + spacing,
        y,
        button_width,
        button_height,
        f"Compare ({ui_state.comparison_runs}/3)",
        enabled=ui_state.ui_mode == UIMode.IDLE,
    )

    # Кнопка Самопроверка
    draw_button(
        x + 2 * (button_width + spacing),
        y,
        button_width,
        button_height,
        "Self Test",
        enabled=True,
    )

    # Кнопка Масштаб
    draw_button(
        x + 3 * (button_width + spacing),
        y,
        button_width,
        button_height,
        f"Zoom {ui_state.view_scale * 100:.0f}%",
        enabled=True,
    )
