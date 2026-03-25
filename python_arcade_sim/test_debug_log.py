"""
Тест отладочного лога симуляции.

Запускает симуляцию в headless-режиме и выводит детальный лог.

Использование:
    python test_debug_log.py --speed 10.0 --angle -30.0
"""

import sys
from pathlib import Path

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent))

# Включаем debug-режим ДО импорта модели
import app.window as window_module

window_module.DEBUG_MODE = False  # Отключить лог по умолчанию

from physics.model_lumped import PhysicsModelLumped as PhysicsModel
from physics.sim_types import (
    BallParams,
    CollisionParams,
    QualityLevel,
    SimulationParams,
    SurfaceParams,
)
from config.constants import BALL_Y_MAX


def run_simulation(
    speed: float = 10.0,
    angle: float = -30.0,
    spin: float = 0.0,
    spin_dir: str = "cw",
) -> None:
    """Запустить симуляцию и вывести лог."""
    print("=" * 100)
    print(
        f"Симуляция: speed={speed} m/s, angle={angle} deg, spin={spin} rad/s ({spin_dir})"
    )
    print(f"Критерий завершения: y >= {BALL_Y_MAX:.3f} м")
    print("=" * 100)
    print()

    model = PhysicsModel()

    params = SimulationParams(
        ball=BallParams(radius=0.02, mass=0.0027, ifactor=0.4, k=62000, c=10.5),
        surface=SurfaceParams(half_width=0.15, n_nodes=50),
        collision=CollisionParams(
            speed=speed, angle=angle, spin=spin, spin_dir=spin_dir
        ),
        quality=QualityLevel.NORMAL,
        time_scale=0.005,  # Как в оригинальном окне
    )

    model.reset(params)

    # Запускаем симуляцию
    step_count = 0
    last_mode = None
    while not model.is_finished():
        model.step(1.0)  # dt = 1.0 (будет масштабирован внутри)
        step_count += 1

        # Вывод режима при смене
        current_mode = model.get_mode().value
        if current_mode != last_mode:
            print(
                f">>> Смена режима: {last_mode} -> {current_mode} на шаге {step_count}"
            )
            last_mode = current_mode

        # Защита от бесконечного цикла
        if step_count > 10000:
            print("ERROR: превышено максимальное количество шагов (10000)")
            break

    print()
    print("=" * 100)
    print(f"Симуляция завершена за {step_count} шагов")
    print(f"Итоговое время: t={model.time:.5f} с")
    print(f"Итоговая позиция: pos=({model.ball.x:.4f}, {model.ball.y:.4f})")
    print(f"Итоговая скорость: v=({model.ball.v_x:.2f}, {model.ball.v_y:.2f})")
    print(f"Итоговое вращение: ω={model.ball.omega:.1f} рад/с")

    metrics = model.get_metrics()
    print()
    print("Метрики:")
    print(f"  v_out={metrics.v_out:.2f} m/s")
    print(f"  angle_out={metrics.angle_out:.1f} deg")
    print(f"  contact_time={metrics.contact_time*1000:.1f} ms")
    print(f"  energy_loss={metrics.energy_loss:.6f} J")
    print("=" * 100)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Тест отладочного лога")
    parser.add_argument("--speed", type=float, default=10.0, help="Скорость, m/s")
    parser.add_argument("--angle", type=float, default=-30.0, help="Угол, deg")
    parser.add_argument("--spin", type=float, default=0.0, help="Вращение, rad/s")
    parser.add_argument(
        "--spin-dir", choices=["cw", "ccw"], default="cw", help="Направление вращения"
    )

    args = parser.parse_args()

    run_simulation(
        speed=args.speed,
        angle=args.angle,
        spin=args.spin,
        spin_dir=args.spin_dir,
    )
