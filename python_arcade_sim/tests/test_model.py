"""
Minimal-тесты для PhysicsModel.

Проверка базовой функциональности:
- после reset состояние корректно
- step не падает
- история записывается
"""

import sys
from pathlib import Path

# Добавляем корень проекта в path для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.model import PhysicsModel
from physics.types import (
    BallParams,
    CollisionParams,
    QualityLevel,
    SimulationMode,
    SimulationParams,
    SurfaceParams,
)


def create_default_params() -> SimulationParams:
    """Создать параметры по умолчанию для тестов."""
    return SimulationParams(
        ball=BallParams(
            radius=0.02,
            mass=0.0027,
            ifactor=0.4,
            k=1e6,
            c=100,
        ),
        surface=SurfaceParams(
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


def test_reset_initializes_state() -> None:
    """После reset состояние корректно."""
    model = PhysicsModel()
    params = create_default_params()
    
    model.reset(params)
    
    # Проверка режима
    assert model.get_mode() == SimulationMode.PREFLIGHT
    
    # Проверка параметров
    assert model.params is not None
    assert model.params.ball.radius == 0.02
    
    # Проверка поверхности
    assert len(model.surface.x_nodes) == 100
    assert len(model.surface.u_y) == 100
    assert len(model.surface.u_x) == 100
    
    # Проверка времени
    assert model.time == 0.0
    
    print("✓ test_reset_initializes_state passed")


def test_step_does_not_crash() -> None:
    """step не падает при вызове."""
    model = PhysicsModel()
    params = create_default_params()
    
    model.reset(params)
    
    # Выполняем несколько шагов
    for _ in range(10):
        model.step(1.0)
    
    # Время должно увеличиться
    assert model.time > 0.0
    
    print("✓ test_step_does_not_crash passed")


def test_history_is_recorded() -> None:
    """История записывается при шагах."""
    model = PhysicsModel()
    params = create_default_params()
    
    model.reset(params)
    
    # До шагов история пуста
    assert len(model.get_history().points) == 0
    
    # После шагов история должна заполниться
    for _ in range(5):
        model.step(1.0)
    
    history = model.get_history()
    assert len(history.points) == 5
    
    # Проверка структуры точек
    for point in history.points:
        assert point.time >= 0.0
        # Остальные поля могут быть нулевыми в заглушке
    
    print("✓ test_history_is_recorded passed")


def test_is_finished_initially_false() -> None:
    """is_finished возвращает False до завершения."""
    model = PhysicsModel()
    params = create_default_params()
    
    model.reset(params)
    
    assert not model.is_finished()
    
    # После нескольких шагов всё ещё не finished
    for _ in range(100):
        model.step(1.0)
    
    # В заглушке режим не меняется на FINISHED
    # Это будет реализовано в полной версии
    assert not model.is_finished()
    
    print("✓ test_is_finished_initially_false passed")


def test_render_snapshot_is_valid() -> None:
    """get_render_snapshot возвращает валидный снимок."""
    model = PhysicsModel()
    params = create_default_params()
    
    model.reset(params)
    
    snapshot = model.get_render_snapshot()
    
    # Проверка структуры снимка
    assert snapshot.ball is not None
    assert snapshot.surface is not None
    assert snapshot.spikes is not None
    assert snapshot.contact is not None
    assert snapshot.mode == SimulationMode.PREFLIGHT
    
    print("✓ test_render_snapshot_is_valid passed")


def run_all_tests() -> None:
    """Запустить все тесты."""
    print("Running PhysicsModel tests...\n")
    
    test_reset_initializes_state()
    test_step_does_not_crash()
    test_history_is_recorded()
    test_is_finished_initially_false()
    test_render_snapshot_is_valid()
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    run_all_tests()
