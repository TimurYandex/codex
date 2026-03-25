import arcade
from arcade import Text


class SimulationWindow(arcade.Window):
    def __init__(self, width: int, height: int, title: str) -> None:
        super().__init__(width=width, height=height, title=title)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self._frame_count = 0
        self._status_text = Text(
            "Baseline window: arcade runs correctly.",
            x=20,
            y=height - 40,
            font_size=14,
            color=arcade.color.WHITE,
        )

    def on_draw(self) -> None:
        self.clear()
        self._frame_count += 1
        self._status_text.draw()

    def on_update(self, delta_time: float) -> None:
        # Пока логика сведена к минимуму; на следующих шагах подключим симуляцию.
        _ = delta_time
