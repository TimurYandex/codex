import arcade

from app.window import SimulationWindow


def main() -> None:
    # Базовый запуск: окно + фон.
    # Дальше физика/рендер/GUI будут подключаться к этому каркасу.
    window = SimulationWindow(1280, 720, "Ball impact simulator (Python + arcade)")
    arcade.run()


if __name__ == "__main__":
    main()

