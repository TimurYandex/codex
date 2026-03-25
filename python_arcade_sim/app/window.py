"""
Главное окно симуляции.

Использует arcade для отрисовки и управления окном.
"""

import arcade

from physics.model import PhysicsModel
from physics.sim_types import SimulationParams, SurfaceParams
from render.renderer import Renderer


class SimulationWindow(arcade.Window):
    """
    Окно симуляции удара мяча о поверхность.

    Обработчики:
    - on_draw: отрисовка кадра
    - on_update: обновление физики
    - on_mouse_press: пауза/продолжение по клику
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

        # Параметры симуляции (по умолчанию)
        self.params = self._create_default_params()

        # Состояние
        self._running = False
        self._frame_count = 0

        # Запуск симуляции
        self.reset_simulation()

    def _create_default_params(self) -> SimulationParams:
        """Создать параметры симуляции по умолчанию."""
        from physics.sim_types import (
            BallParams,
            CollisionParams,
            QualityLevel,
            SurfaceParams,
            LayerParams,
            SpikeMode,
        )

        return SimulationParams(
            ball=BallParams(
                radius=0.02,
                mass=0.0027,
                ifactor=0.4,
                k=1e6,
                c=100,
            ),
            surface=SurfaceParams(
                layers=[
                    LayerParams(
                        title="Top",
                        thickness=0.002,
                        k_n=1e6,
                        c_n=100,
                        k_t=5e5,
                        c_t=50,
                        mu_s=1.0,
                        mu_k=0.5,
                        spike_mode=SpikeMode.NONE,
                    ),
                    LayerParams(
                        title="Base",
                        thickness=0.01,
                        k_n=2e6,
                        c_n=200,
                        k_t=1e6,
                        c_t=100,
                        mu_s=0.8,
                        mu_k=0.4,
                        spike_mode=SpikeMode.NONE,
                    ),
                ],
                half_width=0.15,
                depth=0.01,
                n_nodes=100,
                fr_mul=1.0,
            ),
            collision=CollisionParams(
                speed=10.0,
                angle=-30.0,
                spin=0.0,
                spin_dir="cw",
            ),
            quality=QualityLevel.NORMAL,
            time_scale=0.005,
        )

    def reset_simulation(self) -> None:
        """Сбросить и инициализировать симуляцию."""
        self.model.reset(self.params)
        self._running = True
        self._frame_count = 0

    def on_draw(self) -> None:
        """Отрисовка кадра."""
        self.clear()

        # Получаем снимок состояния
        snapshot = self.model.get_render_snapshot()

        # Рендерим
        self.renderer.render(
            snapshot,
            self.params.surface,
            self.model.get_metrics() if self.model.is_finished() else None,
        )

        # Счётчик кадров
        self._frame_count += 1

        # Текст статуса
        status = f"Mode: {snapshot.mode.value} | Frame: {self._frame_count}"
        arcade.draw_text(status, 10, self.height - 30, arcade.color.WHITE, 14)

        if not self._running:
            arcade.draw_text(
                "PAUSED - Click to resume",
                self.width // 2 - 100,
                self.height // 2,
                arcade.color.YELLOW,
                20,
            )

    def on_update(self, delta_time: float) -> None:
        """Обновление физики."""
        if self._running and not self.model.is_finished():
            self.model.step(delta_time)

    def on_mouse_press(
        self,
        x: float,
        y: float,
        button: int,
        modifiers: int,
    ) -> None:
        """Пауза/продолжение по клику."""
        if button == arcade.MOUSE_BUTTON_LEFT:
            self._running = not self._running
            if self._running and self.model.is_finished():
                self.reset_simulation()

    def on_key_press(self, key: int, modifiers: int) -> None:
        """Обработка клавиш."""
        if key == arcade.key.SPACE:
            # Пробел: пауза/продолжение
            self._running = not self._running
        elif key == arcade.key.R:
            # R: перезапуск
            self.reset_simulation()
        elif key == arcade.key.ESCAPE:
            # Escape: выход
            arcade.close_window()
