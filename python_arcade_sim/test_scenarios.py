"""
Тестовые сценарии для проверки физики контакта.

4 стандартных сценария с заведомо известными правильными ответами:

1) Вертикальное падение с вращением:
   - Если мяч падает почти вертикально, направление и скорость его отскока
     по горизонтали почти полностью определяется начальным вращением
   - Вертикальная скорость отскока немного меньше по модулю, чем была до удара

2) Удар под 45° без вращения:
   - Мяч отскакивает более вертикально (угол > 45°)
   - Горизонтальная скорость падает
   - Появляется вращение по часовой стрелке (omega < 0)

3) Удар под 45° с верхним вращением (против часовой):
   - Мяч отскакивает более заметно быстрее по горизонтали
   - Угол отскока < 45°

4) Удар под 45° с нижним вращением (по часовой):
   - Мяч отскакивает заметно медленнее по горизонтали
   - Угол отскока ближе к 90°
   - Вращение либо уменьшается, либо меняет направление
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Включаем debug-режим
import app.window as window_module

window_module.DEBUG_MODE = False

from physics.model_lumped import PhysicsModelLumped as PhysicsModel
from physics.sim_types import (
    BallParams,
    CollisionParams,
    QualityLevel,
    SimulationParams,
    SurfaceParams,
    LayerParams,
    SpikeMode,
)


def run_scenario(
    name: str,
    speed: float,
    angle: float,
    spin: float,
    spin_dir: str = "cw",
) -> dict:
    """
    Запустить сценарий и вернуть метрики.

    Args:
        name: Название сценария
        speed: Скорость, м/с
        angle: Угол, градусы (отрицательный = вниз)
        spin: Вращение, рад/с
        spin_dir: Направление вращения

    Returns:
        Словарь с метриками
    """
    model = PhysicsModel()

    params = SimulationParams(
        ball=BallParams(radius=0.02, mass=0.0027, ifactor=0.4, k=62000, c=10.5),
        surface=SurfaceParams(
            layers=[
                LayerParams(
                    title="Top",
                    thickness=0.0017,
                    k_n=120000,
                    c_n=34,
                    k_t=56000,
                    c_t=28,
                    mu_s=0.95,
                    mu_k=0.81,
                    spike_mode=SpikeMode.NONE,
                ),
            ],
            half_width=0.15,
            n_nodes=50,
        ),
        collision=CollisionParams(
            speed=speed,
            angle=angle,
            spin=spin,
            spin_dir=spin_dir,
        ),
        quality=QualityLevel.NORMAL,
        time_scale=0.005,
    )

    model.reset(params)

    # Запускаем симуляцию
    step_count = 0
    while not model.is_finished():
        model.step(1.0)
        step_count += 1
        if step_count > 10000:
            print(f"ERROR: {name} - превышено максимальное количество шагов")
            break

    metrics = model.get_metrics()

    return {
        "name": name,
        "v_in": speed,
        "angle_in": angle,
        "omega_in": -spin if spin_dir == "cw" else spin,
        "v_out": metrics.v_out,
        "omega_out": metrics.omega_out,
        "angle_out": metrics.angle_out,
        "contact_time_ms": metrics.contact_time * 1000,
        "energy_loss": metrics.energy_loss,
    }


def print_results(results: list) -> None:
    """Вывести результаты тестов."""
    print("\n" + "=" * 100)
    print("РЕЗУЛЬТАТЫ ТЕСТОВ")
    print("=" * 100)

    for r in results:
        print(f"\n{r['name']}")
        print(
            f"  Вход: v={r['v_in']:.1f} м/с, angle={r['angle_in']:.1f}°, ω={r['omega_in']:.1f} рад/с"
        )
        print(
            f"  Выход: v={r['v_out']:.2f} м/с, angle={r['angle_out']:.1f}°, ω={r['omega_out']:.1f} рад/с"
        )
        print(
            f"  Контакт: {r['contact_time_ms']:.2f} мс, потери: {r['energy_loss']:.4f} Дж"
        )

    print("\n" + "=" * 100)


def check_expectations(results: list) -> None:
    """Проверить ожидания для каждого сценария."""
    print("\nПРОВЕРКА ОЖИДАНИЙ")
    print("=" * 100)

    # Сценарий 1: Вертикальное падение с вращением
    r1 = results[0]
    print(f"\n1. Вертикальное падение с вращением:")
    print(f"   Ожидание: v_x_out определяется вращением, v_y_out ≈ 0.9 * |v_y_in|")
    print(
        f"   Фактически: angle_out={r1['angle_out']:.1f}°, omega_out={r1['omega_out']:.1f}"
    )
    # После вертикального падения с вращением мяч должен отскочить под углом
    # Угол должен быть близок к 90° (вертикально)
    if abs(r1["angle_out"]) > 70:
        print("   ✓ Угол отскока близок к вертикальному")
    else:
        print(f"   ✗ ОШИБКА: Угол отскока слишком пологий ({r1['angle_out']:.1f}°)")

    # Сценарий 2: Удар под 35° без вращения
    r2 = results[1]
    print(f"\n2. Удар под 35° без вращения:")
    print(f"   Ожидание: angle_out > 35°, omega_out < 0 (по часовой)")
    print(
        f"   Фактически: angle_out={r2['angle_out']:.1f}°, omega_out={r2['omega_out']:.1f}"
    )
    if r2["angle_out"] > 35 and r2["omega_out"] < 0:
        print("   ✓ Мяч отскакивает более вертикально с вращением по часовой")
    else:
        print(
            f"   ✗ ОШИБКА: angle_out={r2['angle_out']:.1f}° (ожидалось > 35°), omega_out={r2['omega_out']:.1f}"
        )

    # Сценарий 3: Удар под 35° с верхним вращением
    r3 = results[2]
    print(f"\n3. Удар под 35° с верхним вращением (против часовой):")
    print(f"   Ожидание: angle_out < 35°, v_x_out > v_x_in")
    print(
        f"   Фактически: angle_out={r3['angle_out']:.1f}°, omega_out={r3['omega_out']:.1f}"
    )
    if r3["angle_out"] < 35:
        print("   ✓ Угол отскока меньше 35° (более пологий)")
    else:
        print(f"   ✗ ОШИБКА: angle_out={r3['angle_out']:.1f}° (ожидалось < 35°)")

    # Сценарий 4: Удар под 35° с нижним вращением
    r4 = results[3]
    print(f"\n4. Удар под 35° с нижним вращением (по часовой):")
    print(f"   Ожидание: angle_out >> 35°, omega_out уменьшается или меняет знак")
    print(
        f"   Фактически: angle_out={r4['angle_out']:.1f}°, omega_out={r4['omega_out']:.1f}"
    )
    if r4["angle_out"] > 50:
        print("   ✓ Угол отскока значительно больше 35°")
    else:
        print(f"   ✗ ОШИБКА: angle_out={r4['angle_out']:.1f}° (ожидалось >> 35°)")

    print("\n" + "=" * 100)


def main():
    """Запустить все тестовые сценарии."""
    print("Запуск тестовых сценариев...\n")

    results = []

    # Сценарий 1: Вертикальное падение с вращением
    # angle = -80° (почти вертикально вниз), spin = 120 об/с = 754 рад/с (по часовой)
    results.append(
        run_scenario(
            "1. Вертикальное падение с вращением",
            speed=5.0,
            angle=-80.0,
            spin=754.0,
            spin_dir="cw",
        )
    )

    # Сценарий 2: Удар под 35° без вращения
    results.append(
        run_scenario(
            "2. Удар под 35° без вращения",
            speed=11.0,
            angle=-35.0,
            spin=0.0,
        )
    )

    # Сценарий 3: Удар под 35° с верхним вращением (против часовой)
    results.append(
        run_scenario(
            "3. Удар под 35° с верхним вращением",
            speed=11.0,
            angle=-35.0,
            spin=754.0,
            spin_dir="ccw",
        )
    )

    # Сценарий 4: Удар под 35° с нижним вращением (по часовой)
    results.append(
        run_scenario(
            "4. Удар под 35° с нижним вращением",
            speed=11.0,
            angle=-35.0,
            spin=754.0,
            spin_dir="cw",
        )
    )

    print_results(results)
    check_expectations(results)


if __name__ == "__main__":
    main()
