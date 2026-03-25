import arcade

from app.window import SimulationWindow


def main() -> None:
    # Базовый запуск: окно + фон.
    # Дальше физика/рендер/GUI будут подключаться к этому каркасу.
+
    # # Подавляем предупреждение о draw_text (UI панели используют его)
    # import warnings

    # warnings.filterwarnings("ignore", message="draw_text is an extremely slow function")

    window = SimulationWindow(1280, 720, "Ball impact simulator (Python + arcade)")
    arcade.run()


if __name__ == "__main__":
    main()
