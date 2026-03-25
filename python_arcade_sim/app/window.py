import arcade


class SimulationWindow(arcade.Window):
    def __init__(self, width: int, height: int, title: str) -> None:
        super().__init__(width=width, height=height, title=title)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self._frame_count = 0

    def on_draw(self) -> None:
        arcade.start_render()
        self._frame_count += 1
        arcade.draw_text(
            "Baseline window: arcade runs correctly.",
            20,
            self.height - 40,
            arcade.color.WHITE,
            font_size=14,
        )

    def on_update(self, delta_time: float) -> None:
        # Пока логика сведена к минимуму; на следующих шагах подключим симуляцию.
        _ = delta_time

