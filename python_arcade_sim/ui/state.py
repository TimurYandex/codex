"""
UI State: состояние интерфейса и управление параметрами симуляции.

Хранит все параметры, которые пользователь может изменять через UI.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from physics.sim_types import (
    BallParams,
    CollisionParams,
    LayerParams,
    QualityLevel,
    SimulationParams,
    SpikeMode,
    SurfaceParams,
)


class UIMode(Enum):
    """Режимы UI."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPARING = "comparing"


@dataclass
class UIState:
    """
    Состояние интерфейса и параметры симуляции.
    
    Хранит все параметры, которые пользователь может изменять:
    - Параметры столкновения (скорость, угол, spin, направление)
    - Параметры мяча (полый/сплошной, радиус, жёсткость, демпфирование)
    - Параметры поверхности (список слоёв)
    - Параметры трения (mu_s, mu_k, глобальный множитель)
    - Параметры анимации (скорость, масштаб)
    - Режимы (idle/running/paused/comparing)
    """
    
    # ========================================================================
    # Параметры столкновения
    # ========================================================================
    
    speed: float = 10.0
    """Скорость налета, м/с."""
    
    angle: float = -30.0
    """Угол входа, градусы (отрицательный = вниз)."""
    
    spin: float = 0.0
    """Величина вращения, рад/с."""
    
    spin_dir: Literal["cw", "ccw"] = "cw"
    """Направление вращения: cw (по часовой) или ccw (против)."""
    
    # ========================================================================
    # Параметры мяча
    # ========================================================================
    
    ball_is_hollow: bool = False
    """Полый мяч (True) или сплошной (False)."""
    
    ball_radius: float = 0.02
    """Радиус мяча, м."""
    
    ball_mass: float = 0.0027
    """Масса мяча, кг."""
    
    ball_k: float = 1e6
    """Жёсткость мяча, Н/м."""
    
    ball_c: float = 100
    """Демпфирование мяча, Н·с/м."""
    
    # ========================================================================
    # Параметры поверхности
    # ========================================================================
    
    surface_layers: list[LayerParams] = field(default_factory=list)
    """Список слоёв поверхности."""
    
    surface_fr_mul: float = 1.0
    """Глобальный множитель трения."""
    
    # ========================================================================
    # Параметры анимации
    # ========================================================================
    
    time_scale: float = 0.005
    """Скорость анимации (по умолчанию 0.005)."""
    
    view_scale: float = 1.0
    """Масштаб отображения (120% → 100% → 85% → 70% → 55%)."""
    
    show_overlays: bool = True
    """Показать оверлеи (векторы, контактное пятно)."""
    
    show_graphs: bool = False
    """Показать графики."""
    
    # ========================================================================
    # Режимы
    # ========================================================================
    
    ui_mode: UIMode = UIMode.IDLE
    """Текущий режим UI."""
    
    comparison_runs: int = 0
    """Количество прогонов для сравнения (0-3)."""
    
    quality: QualityLevel = QualityLevel.NORMAL
    """Качество симуляции."""
    
    # ========================================================================
    # Пресеты
    # ========================================================================
    
    SURFACE_PRESETS = {
        "classic": [
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
        "inv": [
            LayerParams(
                title="Top",
                thickness=0.002,
                k_n=2e6,
                c_n=200,
                k_t=1e6,
                c_t=100,
                mu_s=0.8,
                mu_k=0.4,
                spike_mode=SpikeMode.NONE,
            ),
            LayerParams(
                title="Base",
                thickness=0.01,
                k_n=1e6,
                c_n=100,
                k_t=5e5,
                c_t=50,
                mu_s=1.0,
                mu_k=0.5,
                spike_mode=SpikeMode.NONE,
            ),
        ],
        "hard": [
            LayerParams(
                title="Hard",
                thickness=0.005,
                k_n=5e6,
                c_n=500,
                k_t=2e6,
                c_t=200,
                mu_s=0.6,
                mu_k=0.3,
                spike_mode=SpikeMode.NONE,
            ),
        ],
    }
    """Пресеты поверхности."""
    
    def __post_init__(self) -> None:
        """Инициализация после создания."""
        if not self.surface_layers:
            self.surface_layers = self.SURFACE_PRESETS["classic"].copy()
    
    def to_simulation_params(self) -> SimulationParams:
        """
        Преобразовать UI состояние в параметры симуляции.
        
        Returns:
            SimulationParams для передачи в PhysicsModel.
        """
        # Параметры мяча
        ball = BallParams(
            radius=self.ball_radius,
            mass=self.ball_mass,
            ifactor=2/3 if self.ball_is_hollow else 0.4,
            k=self.ball_k,
            c=self.ball_c,
            is_hollow=self.ball_is_hollow,
        )
        
        # Параметры поверхности
        surface = SurfaceParams(
            layers=self.surface_layers,
            half_width=0.15,
            depth=0.01,
            n_nodes=100 if self.quality == QualityLevel.NORMAL else 200,
            fr_mul=self.surface_fr_mul,
        )
        
        # Параметры столкновения
        collision = CollisionParams(
            speed=self.speed,
            angle=self.angle,
            spin=self.spin,
            spin_dir=self.spin_dir,
        )
        
        return SimulationParams(
            ball=ball,
            surface=surface,
            collision=collision,
            quality=self.quality,
            time_scale=self.time_scale,
        )
    
    def cycle_view_scale(self) -> float:
        """
        Циклически переключить масштаб отображения.
        
        Последовательность: 120% → 100% → 85% → 70% → 55% → 120%
        
        Returns:
            Новое значение масштаба.
        """
        scales = [1.2, 1.0, 0.85, 0.70, 0.55]
        
        # Найти текущий индекс
        current_idx = 0
        for i, s in enumerate(scales):
            if abs(self.view_scale - s) < 0.01:
                current_idx = i
                break
        
        # Следующий индекс (циклически)
        next_idx = (current_idx + 1) % len(scales)
        self.view_scale = scales[next_idx]
        
        return self.view_scale
    
    def apply_surface_preset(self, preset_name: str) -> None:
        """
        Применить пресет поверхности.
        
        Args:
            preset_name: Название пресета ("classic", "inv", "hard").
        """
        if preset_name in self.SURFACE_PRESETS:
            self.surface_layers = [
                LayerParams(
                    title=layer.title,
                    thickness=layer.thickness,
                    k_n=layer.k_n,
                    c_n=layer.c_n,
                    k_t=layer.k_t,
                    c_t=layer.c_t,
                    mu_s=layer.mu_s,
                    mu_k=layer.mu_k,
                    spike_mode=layer.spike_mode,
                )
                for layer in self.SURFACE_PRESETS[preset_name]
            ]
    
    def add_layer(self) -> None:
        """Добавить новый слой поверхности."""
        self.surface_layers.append(
            LayerParams(
                title=f"Layer {len(self.surface_layers) + 1}",
                thickness=0.002,
                k_n=1e6,
                c_n=100,
                k_t=5e5,
                c_t=50,
                mu_s=1.0,
                mu_k=0.5,
                spike_mode=SpikeMode.NONE,
            )
        )
    
    def remove_layer(self, index: int) -> None:
        """
        Удалить слой по индексу.
        
        Args:
            index: Индекс слоя для удаления.
        """
        if 0 <= index < len(self.surface_layers):
            self.surface_layers.pop(index)
    
    def move_layer(self, index: int, direction: int) -> None:
        """
        Переместить слой вверх/вниз.
        
        Args:
            index: Индекс слоя.
            direction: -1 (вверх) или +1 (вниз).
        """
        new_index = index + direction
        if 0 <= new_index < len(self.surface_layers):
            # Меняем местами
            self.surface_layers[index], self.surface_layers[new_index] = \
                self.surface_layers[new_index], self.surface_layers[index]
