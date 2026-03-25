"""
Рендеринг: графики по времени (Fn, Ft, def, slip, ω, vx, vy).

Модуль использует arcade для отрисовки графиков истории симуляции.
"""

import arcade

from physics.sim_types import SimulationHistory


# Цвета для графиков
COLOR_FN = arcade.color.GREEN
COLOR_FT = arcade.color.ORANGE
COLOR_DEF = arcade.color.PURPLE
COLOR_SLIP = arcade.color.BROWN
COLOR_OMEGA = arcade.color.CYAN
COLOR_VX = arcade.color.BLUE
COLOR_VY = arcade.color.RED

COLOR_GRID = arcade.color.DARK_GRAY
COLOR_TEXT = arcade.color.WHITE


class GraphPanel:
    """
    Панель для отрисовки графика.
    
    Отрисовывает один или несколько сигналов по времени.
    """
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str = "",
    ) -> None:
        """
        Инициализировать панель графика.
        
        Args:
            x, y: Позиция левого нижнего угла (пиксели).
            width, height: Размеры панели (пиксели).
            title: Заголовок графика.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.title = title
        
        # Отступы
        self.padding_left = 40
        self.padding_right = 10
        self.padding_top = 30
        self.padding_bottom = 30
        
        # Область построения
        self.plot_x = x + self.padding_left
        self.plot_y = y + self.padding_bottom
        self.plot_width = width - self.padding_left - self.padding_right
        self.plot_height = height - self.padding_top - self.padding_bottom
    
    def draw_frame(self) -> None:
        """Нарисовать рамку и заголовок."""
        # Рамка
        arcade.draw_rectangle_outline(
            self.x + self.width / 2,
            self.y + self.height / 2,
            self.width,
            self.height,
            COLOR_GRID,
            1
        )
        
        # Заголовок
        arcade.draw_text(
            self.title,
            self.x + self.width / 2,
            self.y + self.height - 15,
            COLOR_TEXT,
            12,
            anchor_x="center"
        )
    
    def draw_grid(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
    ) -> None:
        """
        Нарисовать сетку.
        
        Args:
            x_min, x_max: Диапазон по X.
            y_min, y_max: Диапазон по Y.
        """
        # Вертикальные линии (время)
        n_x_lines = 5
        for i in range(n_x_lines + 1):
            t = x_min + (x_max - x_min) * i / n_x_lines
            px = self._time_to_pixel(t, x_min, x_max)
            arcade.draw_line(
                px, self.plot_y,
                px, self.plot_y + self.plot_height,
                COLOR_GRID,
                1
            )
        
        # Горизонтальные линии (значение)
        n_y_lines = 4
        for i in range(n_y_lines + 1):
            v = y_min + (y_max - y_min) * i / n_y_lines
            py = self._value_to_pixel(v, y_min, y_max)
            arcade.draw_line(
                self.plot_x, py,
                self.plot_x + self.plot_width, py,
                COLOR_GRID,
                1
            )
    
    def _time_to_pixel(
        self,
        t: float,
        t_min: float,
        t_max: float,
    ) -> float:
        """Преобразовать время в пиксель по X."""
        if t_max <= t_min:
            return self.plot_x
        ratio = (t - t_min) / (t_max - t_min)
        return self.plot_x + ratio * self.plot_width
    
    def _value_to_pixel(
        self,
        v: float,
        v_min: float,
        v_max: float,
    ) -> float:
        """Преобразовать значение в пиксель по Y."""
        if v_max <= v_min:
            return self.plot_y + self.plot_height / 2
        ratio = (v - v_min) / (v_max - v_min)
        return self.plot_y + (1 - ratio) * self.plot_height
    
    def draw_line(
        self,
        points: list[tuple[float, float]],
        color: tuple[int, int, int],
        t_min: float,
        t_max: float,
        v_min: float,
        v_max: float,
        thickness: int = 2,
    ) -> None:
        """
        Нарисовать линию по точкам.
        
        Args:
            points: Список точек (t, value).
            color: Цвет линии.
            t_min, t_max: Диапазон по времени.
            v_min, v_max: Диапазон по значению.
            thickness: Толщина линии.
        """
        if len(points) < 2:
            return
        
        for i in range(len(points) - 1):
            t1, v1 = points[i]
            t2, v2 = points[i + 1]
            
            x1 = self._time_to_pixel(t1, t_min, t_max)
            y1 = self._value_to_pixel(v1, v_min, v_max)
            x2 = self._time_to_pixel(t2, t_min, t_max)
            y2 = self._value_to_pixel(v2, v_min, v_max)
            
            arcade.draw_line(x1, y1, x2, y2, color, thickness)


def draw_graphs(
    history: SimulationHistory,
    x: int = 10,
    y: int = 10,
    graph_width: int = 300,
    graph_height: int = 150,
    time_scale: float = 1.0,
) -> None:
    """
    Нарисовать все графики истории.
    
    Args:
        history: История симуляции.
        x, y: Позиция левого нижнего угла первого графика.
        graph_width, graph_height: Размеры одного графика.
        time_scale: Масштаб времени для отображения.
    """
    if not history.points:
        return
    
    # Определяем диапазоны
    t_min = 0.0
    t_max = max(p.time for p in history.points) if history.points else 1.0
    
    # Диапазоны для каждого сигнала
    ranges = {
        "fn": (0.0, max((abs(p.fn) for p in history.points), default=100)),
        "ft": (-50, 50),
        "def": (0.0, max((abs(p.deflection) for p in history.points), default=0.01)),
        "slip": (-10, 10),
        "omega": (-100, 100),
        "vx": (-20, 20),
        "vy": (-20, 20),
    }
    
    # Увеличиваем диапазоны на 10%
    for key in ranges:
        vmin, vmax = ranges[key]
        span = vmax - vmin
        ranges[key] = (vmin - span * 0.1, vmax + span * 0.1)
    
    # Создаём графики
    graphs = [
        ("Fn (N)", [(p.time, p.fn) for p in history.points], COLOR_FN, ranges["fn"]),
        ("Ft (N)", [(p.time, p.ft) for p in history.points], COLOR_FT, ranges["ft"]),
        ("Deflection (m)", [(p.time, p.deflection) for p in history.points], COLOR_DEF, ranges["def"]),
        ("Slip (m/s)", [(p.time, p.slip) for p in history.points], COLOR_SLIP, ranges["slip"]),
        ("Omega (rad/s)", [(p.time, p.omega) for p in history.points], COLOR_OMEGA, ranges["omega"]),
        ("Vx (m/s)", [(p.time, p.vx) for p in history.points], COLOR_VX, ranges["vx"]),
        ("Vy (m/s)", [(p.time, p.vy) for p in history.points], COLOR_VY, ranges["vy"]),
    ]
    
    # Отрисовка
    spacing = 10
    current_y = y
    
    for title, points, color, (vmin, vmax) in graphs:
        panel = GraphPanel(x, current_y, graph_width, graph_height, title)
        panel.draw_frame()
        panel.draw_grid(t_min, t_max, vmin, vmax)
        panel.draw_line(points, color, t_min, t_max, vmin, vmax)
        
        current_y += graph_height + spacing
