"""
Главное окно симуляции с полным UI.

Интегрирует физику, рендеринг и UI в единое приложение.
"""

import arcade
from arcade import Text

from physics.model_lumped import PhysicsModelLumped as PhysicsModel
from physics.sim_types import SimulationMetrics
from render.renderer import Renderer
from render.graphs import draw_graphs
from render.overlays import draw_overlays
from ui.state import UIState, UIMode
from ui.panels import (
    draw_action_buttons,
    draw_animation_panel,
    draw_ball_panel,
    draw_collision_panel,
    draw_surface_panel,
)

# Глобальные переменные для отладки (устанавливаются из main.py)
DEBUG_MODE = False
NO_SLOWDOWN = False
INITIAL_SPEED = 10.0
INITIAL_ANGLE = -30.0
INITIAL_SPIN = 0.0
INITIAL_SPIN_DIR = "cw"


class SimulationWindow(arcade.Window):
    """
    Окно симуляции удара мяча о поверхность.

    Обработчики:
    - on_draw: отрисовка кадра
    - on_update: обновление физики
    - on_mouse_press: обработка кликов
    - on_mouse_motion: отслеживание курсора для hover-эффектов
    - on_key_press: горячие клавиши
    """

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        title: str = "Ball impact simulator",
    ) -> None:
        super().__init__(width=width, height=height, title=title)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        # Физическая модель
        self.model = PhysicsModel()

        # Рендерер
        self.renderer = Renderer(width, height, scale=1.0)

        # UI состояние
        self.ui_state = UIState()

        # Состояние
        self._frame_count = 0
        self._mouse_x = 0
        self._mouse_y = 0

        # Позиции панелей
        self._panel_x = 10
        self._panel_y = height - 180
        self._panel_spacing = 210

        # Кнопки действий
        self._action_buttons_y = 10
        self._button_width = 100
        self._button_height = 30
        self._button_spacing = 10

        # Текстовые объекты для сообщений (создаются один раз)
        self._pause_text = Text(
            "PAUSED - Click or Space to resume",
            width // 2 - 120,
            height // 2,
            arcade.color.YELLOW,
            20,
        )
        self._finished_text = Text(
            "FINISHED - Click or R to restart",
            width // 2 - 110,
            height // 2 + 30,
            arcade.color.GREEN,
            20,
        )

        # Текстовые объекты для статуса (создаются один раз)
        self._status_texts = [
            Text("", 10, height - 30 - i * 20, arcade.color.WHITE, 14)
            for i in range(7)  # Максимум 7 строк статуса
        ]

        # Запуск симуляции
        self.reset_simulation()

    def reset_simulation(self) -> None:
        """Сбросить и инициализировать симуляцию."""
        # Применяем параметры из командной строки (если заданы)
        if INITIAL_SPEED != 10.0 or INITIAL_ANGLE != -30.0:
            self.ui_state.speed = INITIAL_SPEED
            self.ui_state.angle = INITIAL_ANGLE
            self.ui_state.spin = INITIAL_SPIN
            self.ui_state.spin_dir = INITIAL_SPIN_DIR

        params = self.ui_state.to_simulation_params()
        self.model.reset(params)
        self.ui_state.ui_mode = UIMode.RUNNING
        self._frame_count = 0
        self.renderer.set_scale(self.ui_state.view_scale)

    def on_draw(self) -> None:
        """Отрисовка кадра."""
        self.clear()

        # Получаем снимок состояния
        snapshot = self.model.get_render_snapshot()
        metrics = self.model.get_metrics() if self.model.is_finished() else None

        # Рендерим симуляцию
        self.renderer.render(
            snapshot,
            self.ui_state.to_simulation_params().surface,
            metrics,
            show_overlays=self.ui_state.show_overlays and not self.ui_state.show_graphs,
        )

        # Рендерим графики (если включены)
        if self.ui_state.show_graphs:
            draw_graphs(
                self.model.get_history(),
                x=10,
                y=10,
                graph_width=300,
                graph_height=120,
            )

        # Рендерим UI панели
        self._draw_ui_panels()

        # Счётчик кадров
        self._frame_count += 1

        # Текст статуса
        self._draw_status_text(snapshot, metrics)

    def _draw_ui_panels(self) -> None:
        """Нарисовать панели управления."""
        # Панели параметров (сверху справа)
        panel_x = self.width - 270
        panel_y = self.height - 200
        panel_spacing = 210

        draw_collision_panel(self.ui_state, panel_x, panel_y)
        draw_ball_panel(self.ui_state, panel_x, panel_y - panel_spacing)
        draw_surface_panel(self.ui_state, panel_x, panel_y - 2 * panel_spacing)
        draw_animation_panel(self.ui_state, panel_x, panel_y - 3 * panel_spacing)

        # Кнопки действий (внизу)
        draw_action_buttons(
            self.ui_state,
            x=10,
            y=self._action_buttons_y,
            button_width=self._button_width,
            button_height=self._button_height,
        )

    def _draw_status_text(
        self,
        snapshot,
        metrics: SimulationMetrics | None,
    ) -> None:
        """Нарисовать текст статуса."""
        # Основная информация
        status_lines = [
            f"Mode: {snapshot.mode.value}",
            f"Frame: {self._frame_count}",
            f"Time: {self.model.time:.4f}s",
        ]

        if metrics and self.model.is_finished():
            status_lines.extend(
                [
                    f"v_out: {metrics.v_out:.2f} m/s",
                    f"angle_out: {metrics.angle_out:.1f} deg",
                    f"contact_time: {metrics.contact_time*1000:.1f} ms",
                ]
            )

        # Обновляем и рисуем текстовые объекты
        for i, line in enumerate(status_lines[:7]):
            self._status_texts[i].text = line
            self._status_texts[i].draw()

        # Сообщение о паузе
        if self.ui_state.ui_mode == UIMode.PAUSED:
            self._pause_text.draw()

        # Сообщение о завершении
        if self.model.is_finished():
            self._finished_text.draw()

    def on_update(self, delta_time: float) -> None:
        """Обновление физики."""
        if self.ui_state.ui_mode == UIMode.RUNNING and not self.model.is_finished():
            # Замедление в 20 раз во время контакта (для отладки физики)
            if not NO_SLOWDOWN:
                snapshot = self.model.get_render_snapshot()
                if snapshot.contact.is_active:
                    # Контакт активен - замедляем в 20 раз
                    delta_time = delta_time / 20

            self.model.step(delta_time)

        # Закрытие окна при завершении симуляции в debug-режиме
        if DEBUG_MODE and self.model.is_finished():
            print("\n=== Симуляция завершена, закрытие окна ===")
            arcade.close_window()

    def on_mouse_press(
        self,
        x: float,
        y: float,
        button: int,
        modifiers: int,
    ) -> None:
        """Обработка кликов мыши."""
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Проверка клика по кнопкам действий
        if self._is_action_button_click(x, y):
            return

        # Клик по области окна = пауза/продолжение
        if self.ui_state.ui_mode == UIMode.RUNNING:
            self.ui_state.ui_mode = UIMode.PAUSED
        elif self.ui_state.ui_mode == UIMode.PAUSED:
            self.ui_state.ui_mode = UIMode.RUNNING
        elif self.model.is_finished():
            self.reset_simulation()

    def _is_action_button_click(self, x: float, y: float) -> bool:
        """
        Проверить, был ли клик по кнопке действий.

        Returns:
            True, если клик по кнопке (обработано).
        """
        button_total_width = self._button_width + self._button_spacing

        # Кнопка Run/Pause
        if (
            x < 10 + self._button_width
            and y < self._action_buttons_y + self._button_height
        ):
            if self.ui_state.ui_mode == UIMode.RUNNING:
                self.ui_state.ui_mode = UIMode.PAUSED
            else:
                self.ui_state.ui_mode = UIMode.RUNNING
            return True

        # Кнопка Compare
        if (
            10 + button_total_width <= x < 10 + 2 * button_total_width
            and y < self._action_buttons_y + self._button_height
        ):
            if self.ui_state.ui_mode == UIMode.IDLE:
                self.ui_state.comparison_runs = min(
                    3, self.ui_state.comparison_runs + 1
                )
            return True

        # Кнопка Self Test
        if (
            10 + 2 * button_total_width <= x < 10 + 3 * button_total_width
            and y < self._action_buttons_y + self._button_height
        ):
            self._run_self_test()
            return True

        # Кнопка Zoom
        if (
            10 + 3 * button_total_width <= x < 10 + 4 * button_total_width
            and y < self._action_buttons_y + self._button_height
        ):
            self.ui_state.cycle_view_scale()
            self.renderer.set_scale(self.ui_state.view_scale)
            return True

        return False

    def _run_self_test(self) -> None:
        """Запустить самопроверку (sanity checks)."""
        # Простая проверка: запустить симуляцию с дефолтными параметрами
        # и проверить, что метрики разумные
        self.reset_simulation()

        # Быстрая симуляция
        for _ in range(100):
            self.model.step(1.0)
            if self.model.is_finished():
                break

        metrics = self.model.get_metrics()

        # Проверки
        checks_passed = True
        if metrics.contact_time <= 0:
            checks_passed = False
        if metrics.v_out < 0:
            checks_passed = False

        # Вывод результата (в консоль)
        if checks_passed:
            print("Self test: PASSED")
        else:
            print("Self test: FAILED")

    def _print_help(self) -> None:
        """Вывести справку по управлению."""
        print("\n" + "=" * 50)
        print("УПРАВЛЕНИЕ СИМУЛЯТОРОМ")
        print("=" * 50)
        print("Пробел  - Пауза/продолжение")
        print("R       - Перезапуск")
        print("G       - Графики вкл/выкл")
        print("O       - Оверлеи вкл/выкл")
        print("Escape  - Выход")
        print("-" * 50)
        print("1/2/3   - Пресеты поверхности (classic/inv/hard)")
        print("-" * 50)
        print("↑/↓     - Скорость ±1 m/s")
        print("←/→     - Угол ±5°")
        print("W/S     - Вращение ±20 rad/s")
        print("D       - Направление вращения")
        print("+/-     - Скорость анимации")
        print("-" * 50)
        print("H       - Эта справка")
        print("=" * 50 + "\n")

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        """Отслеживание движения мыши."""
        self._mouse_x = int(x)
        self._mouse_y = int(y)

    def on_key_press(self, key: int, modifiers: int) -> None:
        """Обработка нажатий клавиш."""
        if key == arcade.key.SPACE:
            # Пробел: пауза/продолжение
            if self.ui_state.ui_mode == UIMode.RUNNING:
                self.ui_state.ui_mode = UIMode.PAUSED
            elif self.ui_state.ui_mode == UIMode.PAUSED:
                self.ui_state.ui_mode = UIMode.RUNNING
            elif self.model.is_finished():
                self.reset_simulation()

        elif key == arcade.key.R:
            # R: перезапуск
            self.reset_simulation()

        elif key == arcade.key.G:
            # G: переключить графики
            self.ui_state.show_graphs = not self.ui_state.show_graphs
            self.ui_state.show_overlays = not self.ui_state.show_graphs

        elif key == arcade.key.O:
            # O: переключить оверлеи
            self.ui_state.show_overlays = not self.ui_state.show_overlays
            if self.ui_state.show_overlays:
                self.ui_state.show_graphs = False

        elif key == arcade.key.ESCAPE:
            # Escape: выход
            arcade.close_window()

        elif key == arcade.key.NUM_1:
            # 1: применить пресет classic
            self.ui_state.apply_surface_preset("classic")
            self.reset_simulation()

        elif key == arcade.key.NUM_2:
            # 2: применить пресет inv
            self.ui_state.apply_surface_preset("inv")
            self.reset_simulation()

        elif key == arcade.key.NUM_3:
            # 3: применить пресет hard
            self.ui_state.apply_surface_preset("hard")
            self.reset_simulation()

        # ================================================================
        # Быстрое изменение параметров (для "игры" с моделью)
        # ================================================================

        elif key == arcade.key.UP:
            # Стрелка вверх: увеличить скорость
            self.ui_state.speed = min(20.0, self.ui_state.speed + 1.0)
            print(f"Speed: {self.ui_state.speed:.1f} m/s")
            self.reset_simulation()

        elif key == arcade.key.DOWN:
            # Стрелка вниз: уменьшить скорость
            self.ui_state.speed = max(1.0, self.ui_state.speed - 1.0)
            print(f"Speed: {self.ui_state.speed:.1f} m/s")
            self.reset_simulation()

        elif key == arcade.key.LEFT:
            # Стрелка влево: уменьшить угол (более пологий)
            self.ui_state.angle = max(-80.0, self.ui_state.angle - 5.0)
            print(f"Angle: {self.ui_state.angle:.1f} deg")
            self.reset_simulation()

        elif key == arcade.key.RIGHT:
            # Стрелка вправо: увеличить угол (более крутой)
            self.ui_state.angle = min(10.0, self.ui_state.angle + 5.0)
            print(f"Angle: {self.ui_state.angle:.1f} deg")
            self.reset_simulation()

        elif key == arcade.key.W:
            # W: увеличить вращение
            self.ui_state.spin = min(200.0, self.ui_state.spin + 20.0)
            print(f"Spin: {self.ui_state.spin:.1f} rad/s ({self.ui_state.spin_dir})")
            self.reset_simulation()

        elif key == arcade.key.S:
            # S: уменьшить вращение
            self.ui_state.spin = max(-200.0, self.ui_state.spin - 20.0)
            print(f"Spin: {self.ui_state.spin:.1f} rad/s ({self.ui_state.spin_dir})")
            self.reset_simulation()

        elif key == arcade.key.D:
            # D: изменить направление вращения
            self.ui_state.spin_dir = "ccw" if self.ui_state.spin_dir == "cw" else "cw"
            print(f"Spin direction: {self.ui_state.spin_dir}")
            self.reset_simulation()

        elif key == arcade.key.EQUAL:
            # = или +: увеличить масштаб времени (быстрее)
            self.ui_state.time_scale = min(0.1, self.ui_state.time_scale * 1.5)
            print(f"Time scale: {self.ui_state.time_scale:.4f}")
            self.reset_simulation()

        elif key == arcade.key.MINUS:
            # -: уменьшить масштаб времени (медленнее)
            self.ui_state.time_scale = max(0.001, self.ui_state.time_scale / 1.5)
            print(f"Time scale: {self.ui_state.time_scale:.4f}")
            self.reset_simulation()

        elif key == arcade.key.H:
            # H: показать справку
            self._print_help()
