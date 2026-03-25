"""
Рендеринг: базовая отрисовка разреза поверхности и мяча.

Модуль использует arcade для отрисовки, но не содержит физической логики.
Все данные для отрисовки берутся из RenderSnapshot.
"""

import math

import arcade

from physics.sim_types import RenderSnapshot, SimulationMode, SurfaceParams, LayerParams
from config.constants import SURFACE_HALF_WIDTH, BALL_RADIUS_DEFAULT


# Цвета для отрисовки
COLOR_BACKGROUND = arcade.color.DARK_SLATE_GRAY
COLOR_BALL = arcade.color.WHITE
COLOR_BALL_OUTLINE = arcade.color.BLACK
COLOR_MARK = arcade.color.RED
COLOR_SURFACE_BASE = arcade.color.BROWN
COLOR_LAYER_OUTLINE = arcade.color.GRAY

# Цвета слоёв (по умолчанию)
DEFAULT_LAYER_COLORS = [
    arcade.color.LIGHT_GREEN,
    arcade.color.LIGHT_BLUE,
    arcade.color.LIGHT_YELLOW,
    arcade.color.LIGHT_PINK,
    arcade.color.LAVENDER,
]


def get_layer_color(index: int) -> tuple[int, int, int]:
    """Получить цвет для слоя по индексу."""
    return DEFAULT_LAYER_COLORS[index % len(DEFAULT_LAYER_COLORS)]


class Renderer:
    """
    Рендерер для симуляции.

    Отрисовывает:
    - Мяч (круг с меткой и стрелкой вращения)
    - Поверхность (слои в разрезе)
    - Базовую сетку/оси
    """

    def __init__(
        self,
        window_width: int = 1280,
        window_height: int = 720,
        scale: float = 1.0,
    ) -> None:
        """
        Инициализировать рендерер.

        Args:
            window_width: Ширина окна, пиксели.
            window_height: Высота окна, пиксели.
            scale: Масштаб отображения (1.0 = базовый).
        """
        self.window_width = window_width
        self.window_height = window_height
        self.scale = scale

        # Центр окна (точка удара)
        self.center_x = window_width / 2
        self.center_y = window_height / 2 + 100

        # Масштаб: пикселей на метр
        self.pixels_per_meter = 2000 * scale

    def set_scale(self, scale: float) -> None:
        """Установить масштаб отображения."""
        self.scale = scale
        self.pixels_per_meter = 2000 * scale

    def world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        """
        Преобразовать координаты мира (метры) в экранные (пиксели).

        Система координат мира:
        - X: 0 в центре (точка удара)
        - Y: 0 на уровне недеформированной поверхности

        Args:
            x: Позиция по X в метрах.
            y: Позиция по Y в метрах.

        Returns:
            (screen_x, screen_y) в пикселях.
        """
        screen_x = self.center_x + x * self.pixels_per_meter
        screen_y = self.center_y + y * self.pixels_per_meter
        return screen_x, screen_y

    def draw_background(self) -> None:
        """Нарисовать фон."""
        arcade.set_background_color(COLOR_BACKGROUND)

    def draw_grid(self) -> None:
        """Нарисовать базовую сетку и оси."""
        # Ось X (уровень поверхности)
        start_x, start_y = self.world_to_screen(-SURFACE_HALF_WIDTH, 0)
        end_x, end_y = self.world_to_screen(SURFACE_HALF_WIDTH, 0)
        arcade.draw_line(start_x, start_y, end_x, end_y, arcade.color.GRAY, 1)

        # Ось Y (центр удара)
        start_x, start_y = self.world_to_screen(0, -0.05)
        end_x, end_y = self.world_to_screen(0, 0.15)
        arcade.draw_line(start_x, start_y, end_x, end_y, arcade.color.GRAY, 1)

        # Сетка: линии каждые 5 см
        for x in [i * 0.05 for i in range(-6, 7)]:
            if x == 0:
                continue
            sx, sy = self.world_to_screen(x, -0.02)
            arcade.draw_line(sx, sy, sx, sy + 10, arcade.color.DARK_GRAY, 1)

    def draw_surface(
        self,
        surface_params: SurfaceParams,
        snapshot: RenderSnapshot | None = None,
    ) -> None:
        """
        Нарисовать поверхность (слои в разрезе).

        Args:
            surface_params: Параметры поверхности (слои).
            snapshot: Снимок состояния (для отрисовки деформации, если есть).
        """
        hw = surface_params.half_width
        layers = surface_params.layers

        if not layers:
            # Пустая поверхность — рисуем базовую линию
            start_x, start_y = self.world_to_screen(-hw, 0)
            end_x, end_y = self.world_to_screen(hw, 0)
            arcade.draw_line(start_x, start_y, end_x, end_y, COLOR_SURFACE_BASE, 3)
            return

        # Рисуем слои сверху вниз
        y_offset = 0.0

        for i, layer in enumerate(layers):
            thickness = layer.thickness
            color = get_layer_color(i)

            # Верхняя граница слоя
            y_top = y_offset
            y_bottom = y_offset - thickness

            # Координаты для отрисовки прямоугольника
            left_x, _ = self.world_to_screen(-hw, y_top)
            right_x, _ = self.world_to_screen(hw, y_top)
            bottom_y = self.center_y + y_bottom * self.pixels_per_meter

            # Рисуем прямоугольник слоя
            width = right_x - left_x
            height = (y_top - y_bottom) * self.pixels_per_meter

            if height > 0:
                arcade.draw_lbwh_rectangle_filled(
                    left_x, bottom_y, width, height, color
                )

                # Контур слоя
                arcade.draw_lbwh_rectangle_outline(
                    left_x, bottom_y, width, height, COLOR_LAYER_OUTLINE, 1
                )

            y_offset = y_bottom

        # Верхняя граница поверхности (возможно деформированная)
        if snapshot and snapshot.surface.x_nodes:
            self._draw_deformed_surface(snapshot)
        else:
            # Прямая линия
            start_x, start_y = self.world_to_screen(-hw, 0)
            end_x, end_y = self.world_to_screen(hw, 0)
            arcade.draw_line(start_x, start_y, end_x, end_y, COLOR_SURFACE_BASE, 3)

    def _draw_deformed_surface(self, snapshot: RenderSnapshot) -> None:
        """Нарисовать деформированную поверхность (по узлам)."""
        surface = snapshot.surface

        if not surface.x_nodes or not surface.u_y:
            return

        # Рисуем линию по узлам
        points = []
        for i, x in enumerate(surface.x_nodes):
            u_y = surface.u_y[i] if i < len(surface.u_y) else 0.0
            sx, sy = self.world_to_screen(x, u_y)
            points.append((sx, sy))

        if len(points) >= 2:
            for i in range(len(points) - 1):
                arcade.draw_line(
                    points[i][0],
                    points[i][1],
                    points[i + 1][0],
                    points[i + 1][1],
                    COLOR_SURFACE_BASE,
                    3,
                )

    def draw_ball(
        self,
        snapshot: RenderSnapshot,
        ball_radius: float = 0.02,
    ) -> None:
        """
        Нарисовать мяч.

        Args:
            snapshot: Снимок состояния с позицией мяча.
            ball_radius: Радиус мяча, м.
        """
        ball = snapshot.ball

        # Позиция мяча
        sx, sy = self.world_to_screen(ball.x, ball.y)

        # Радиус в пикселях
        radius_px = ball_radius * self.pixels_per_meter

        # Основной круг
        arcade.draw_circle_filled(sx, sy, radius_px, COLOR_BALL)
        arcade.draw_circle_outline(sx, sy, radius_px, COLOR_BALL_OUTLINE, 2)

        # Метка на мяче (для визуализации вращения)
        # Метка на "экваторе" мяча, угол зависит от phi
        mark_angle = ball.phi
        mark_x = sx + radius_px * math.cos(mark_angle)
        mark_y = sy + radius_px * math.sin(mark_angle)
        arcade.draw_circle_filled(mark_x, mark_y, 4, COLOR_MARK)

        # Стрелка направления вращения
        self._draw_spin_arrow(sx, sy, ball.omega, radius_px)

    def _draw_spin_arrow(
        self,
        cx: float,
        cy: float,
        omega: float,
        radius_px: float,
    ) -> None:
        """
        Нарисовать стрелку направления вращения.

        Args:
            cx, cy: Центр мяча.
            omega: Угловая скорость.
            radius_px: Радиус мяча в пикселях.
        """
        if abs(omega) < 0.1:
            return  # Слишком медленное вращение

        # Стрелка над мячом
        arrow_x = cx
        arrow_y = cy + radius_px + 15
        arrow_size = 15

        if omega > 0:
            # Против часовой (CCW) — стрелка влево
            arcade.draw_triangle_filled(
                arrow_x - arrow_size,
                arrow_y,
                arrow_x + arrow_size,
                arrow_y,
                arrow_x,
                arrow_y + arrow_size,
                COLOR_MARK,
            )
        else:
            # По часовой (CW) — стрелка вправо
            arcade.draw_triangle_filled(
                arrow_x - arrow_size,
                arrow_y,
                arrow_x + arrow_size,
                arrow_y,
                arrow_x,
                arrow_y - arrow_size,
                COLOR_MARK,
            )

    def draw_status_text(
        self,
        snapshot: RenderSnapshot,
        metrics: "SimulationMetrics | None" = None,
    ) -> None:
        """
        Нарисовать текстовую информацию о статусе.

        Args:
            snapshot: Снимок состояния.
            metrics: Метрики симуляции (если есть).
        """
        mode_text = f"Mode: {snapshot.mode.value}"
        arcade.draw_text(mode_text, 10, self.window_height - 30, arcade.color.WHITE, 14)

        # Время симуляции
        time_text = f"Time: {snapshot.ball.x:.3f}"
        arcade.draw_text(time_text, 10, self.window_height - 50, arcade.color.WHITE, 14)

    def render(
        self,
        snapshot: RenderSnapshot,
        surface_params: SurfaceParams,
        metrics: "SimulationMetrics | None" = None,
        show_overlays: bool = True,
    ) -> None:
        """
        Выполнить полную отрисовку кадра.

        Args:
            snapshot: Снимок состояния.
            surface_params: Параметры поверхности.
            metrics: Метрики симуляции (опционально).
            show_overlays: Показать оверлеи (векторы, контактное пятно).
        """
        self.draw_background()
        self.draw_grid()
        self.draw_surface(surface_params, snapshot)
        self.draw_ball(snapshot, 0.02)  # Радиус по умолчанию

        if show_overlays:
            from render.overlays import draw_overlays

            draw_overlays(snapshot, self)

        self.draw_status_text(snapshot, metrics)
