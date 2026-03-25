import argparse
import arcade

from app.window import SimulationWindow


def parse_args():
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Симулятор удара мяча")

    # Параметры столкновения
    parser.add_argument(
        "--speed",
        type=float,
        default=10.0,
        help="Скорость мяча, м/с (по умолчанию: 10.0)",
    )
    parser.add_argument(
        "--angle",
        type=float,
        default=-30.0,
        help="Угол входа, градусы (по умолчанию: -30.0)",
    )
    parser.add_argument(
        "--spin",
        type=float,
        default=0.0,
        help="Начальное вращение, рад/с (по умолчанию: 0.0)",
    )
    parser.add_argument(
        "--spin-dir",
        choices=["cw", "ccw"],
        default="cw",
        help="Направление вращения (по умолчанию: cw)",
    )

    # Отладка
    parser.add_argument(
        "--debug", action="store_true", help="Режим отладки (вывод сил в консоль)"
    )
    parser.add_argument(
        "--no-slowdown", action="store_true", help="Отключить замедление при контакте"
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Сохраняем параметры в глобальной переменной для доступа из window
    import app.window as window_module

    window_module.DEBUG_MODE = args.debug
    window_module.NO_SLOWDOWN = args.no_slowdown
    window_module.INITIAL_SPEED = args.speed
    window_module.INITIAL_ANGLE = args.angle
    window_module.INITIAL_SPIN = args.spin
    window_module.INITIAL_SPIN_DIR = args.spin_dir

    print(f"Запуск симуляции:")
    print(f"  Speed: {args.speed:.1f} m/s")
    print(f"  Angle: {args.angle:.1f} deg")
    print(f"  Spin: {args.spin:.1f} rad/s ({args.spin_dir})")
    print(f"  Debug: {args.debug}")
    print()

    window = SimulationWindow(1280, 720, "Ball impact simulator (Python + arcade)")
    arcade.run()


if __name__ == "__main__":
    main()
