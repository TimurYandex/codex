"""
Структуры данных для физики: параметры, состояние, метрики.

Все классы независимы от arcade и используются для передачи данных
между физическим ядром, рендером и UI.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class SpikeMode(Enum):
    """Режим шипов верхнего слоя."""

    NONE = "none"
    OUT = "out"
    IN = "in"


class QualityLevel(Enum):
    """Уровень качества симуляции."""

    NORMAL = "normal"
    HIGH = "high"


class SimulationMode(Enum):
    """Режим симуляции."""

    IDLE = "idle"
    PREFLIGHT = "preflight"
    CONTACT = "contact"
    POST = "post"
    FINISHED = "finished"


# =============================================================================
# Входные параметры симуляции
# =============================================================================


@dataclass
class BallParams:
    """Параметры мяча."""

    radius: float = 0.02
    """Радиус мяча, м."""
    mass: float = 0.0027
    """Масса мяча, кг."""
    ifactor: float = 0.4
    """Коэффициент момента инерции (I = if * m * r²)."""
    k: float = 1e6
    """Жёсткость мяча, Н/м."""
    c: float = 100
    """Демпфирование мяча, Н·с/м."""
    is_hollow: bool = False
    """Полый мяч (True) или сплошной (False)."""


@dataclass
class LayerParams:
    """Параметры одного слоя поверхности."""

    title: str = "Layer"
    """Название слоя (для UI)."""
    thickness: float = 0.001
    """Толщина слоя, м."""
    k_n: float = 1e6
    """Нормальная жёсткость, Н/м²."""
    c_n: float = 100
    """Нормальное демпфирование, Н·с/м²."""
    k_t: float = 5e5
    """Касательная жёсткость, Н/м²."""
    c_t: float = 50
    """Касательное демпфирование, Н·с/м²."""
    mu_s: float = 1.0
    """Коэффициент трения покоя."""
    mu_k: float = 0.5
    """Коэффициент трения скольжения."""
    spike_mode: SpikeMode = SpikeMode.NONE
    """Режим шипов."""
    k_sh: float = 1000.0
    """Жёсткость шипов."""
    h: float = 0.001
    """Высота шипов, м."""
    p: float = 0.5
    """Коэффициент экспоненциального затухания для взвешивания."""
    material: str = "default"
    """Материал слоя (для расчёта плотности)."""


@dataclass
class SurfaceParams:
    """Параметры поверхности."""

    layers: list[LayerParams] = field(default_factory=list)
    """Список слоёв (верхний первый)."""
    half_width: float = 0.15
    """Половина ширины поверхности, м."""
    depth: float = 0.01
    """Глубина поверхности, м."""
    n_nodes: int = 100
    """Количество узлов дискретизации."""
    fr_mul: float = 1.0
    """Глобальный множитель трения."""


@dataclass
class CollisionParams:
    """Параметры столкновения."""

    speed: float = 10.0
    """Скорость налета, м/с."""
    angle: float = -30.0
    """Угол входа, градусы (отрицательный = вниз)."""
    spin: float = 0.0
    """Величина вращения, рад/с."""
    spin_dir: Literal["cw", "ccw"] = "cw"
    """Направление вращения: cw (по часовой) или ccw (против)."""


@dataclass
class SimulationParams:
    """Все входные параметры симуляции."""

    ball: BallParams = field(default_factory=BallParams)
    surface: SurfaceParams = field(default_factory=SurfaceParams)
    collision: CollisionParams = field(default_factory=CollisionParams)
    quality: QualityLevel = QualityLevel.NORMAL
    """Качество симуляции (влияет на dt и n_nodes)."""
    time_scale: float = 0.005
    """Масштаб времени анимации (по умолчанию 0.005)."""


# =============================================================================
# Состояние симуляции
# =============================================================================


@dataclass
class BallState:
    """Состояние мяча."""

    x: float = 0.0
    y: float = 0.0
    v_x: float = 0.0
    v_y: float = 0.0
    omega: float = 0.0
    """Угловая скорость, рад/с."""
    phi: float = 0.0
    """Угол поворота (для визуализации), рад."""


@dataclass
class SurfaceState:
    """Состояние поверхности (узлы)."""

    x_nodes: list[float] = field(default_factory=list)
    """Позиции узлов по X, м."""
    u_y: list[float] = field(default_factory=list)
    """Вертикальные смещения узлов, м."""
    u_x: list[float] = field(default_factory=list)
    """Горизонтальные смещения узлов, м."""
    v_y: list[float] = field(default_factory=list)
    """Вертикальные скорости узлов, м/с."""
    v_x: list[float] = field(default_factory=list)
    """Горизонтальные скорости узлов, м/с."""

    # Агрегаты для визуализации/метрик
    active_nodes: list[int] = field(default_factory=list)
    """Индексы активных узлов (в контакте)."""
    pressure: list[float] = field(default_factory=list)
    """Давление в активных узлах, Па."""


@dataclass
class SpikesState:
    """Состояние шипов."""

    theta: float = 0.0
    """Наклон шипов, рад."""
    theta_dot: float = 0.0
    """Скорость наклона, рад/с."""


@dataclass
class ContactState:
    """Состояние контакта."""

    is_active: bool = False
    """Контакт активен в текущий момент."""
    fn: float = 0.0
    """Нормальная сила, Н."""
    ft: float = 0.0
    """Касательная сила, Н."""
    fn_total: float = 0.0
    """Суммарная нормальная сила, Н."""
    ft_total: float = 0.0
    """Суммарная касательная сила, Н."""
    overlap: float = 0.0
    """Перекрытие мяча с поверхностью, м."""
    slip_velocity: float = 0.0
    """Скорость проскальзывания, м/с."""
    stick_displacement: float = 0.0
    """Накопленное stick-смещение, м."""
    is_slipping: bool = False
    """Проскальзывание активно."""
    active_nodes: list[int] = field(default_factory=list)
    """Индексы активных узлов (в контакте)."""
    pressure: list[float] = field(default_factory=list)
    """Давление в активных узлах, Па."""


# =============================================================================
# Метрики и результаты
# =============================================================================


@dataclass
class SimulationMetrics:
    """Итоговые метрики симуляции."""

    v_out: float = 0.0
    """Итоговая скорость, м/с."""
    omega_out: float = 0.0
    """Итоговое вращение, рад/с."""
    angle_out: float = 0.0
    """Итоговый угол, градусы."""
    contact_time: float = 0.0
    """Время контакта (только контакт, без подлёта), с."""
    max_def: float = 0.0
    """Максимальная деформация поверхности, м."""
    max_shift: float = 0.0
    """Максимальное касательное смещение, м."""
    slip_share: float = 0.0
    """Доля времени проскальзывания, 0..1."""
    energy_loss: float = 0.0
    """Потеря энергии, Дж."""
    j_n: float = 0.0
    """Импульс нормальной силы, Н·с."""
    j_t: float = 0.0
    """Импульс касательной силы, Н·с."""


@dataclass
class HistoryPoint:
    """Точка истории для графиков."""

    time: float = 0.0
    fn: float = 0.0
    ft: float = 0.0
    deflection: float = 0.0
    slip: float = 0.0
    omega: float = 0.0
    v_x: float = 0.0
    v_y: float = 0.0


@dataclass
class SimulationHistory:
    """История симуляции для графиков."""

    points: list[HistoryPoint] = field(default_factory=list)

    def append(self, point: HistoryPoint) -> None:
        self.points.append(point)


# =============================================================================
# Снимок состояния для рендера
# =============================================================================


@dataclass
class RenderSnapshot:
    """Снимок состояния для отрисовки."""

    ball: BallState = field(default_factory=BallState)
    surface: SurfaceState = field(default_factory=SurfaceState)
    spikes: SpikesState = field(default_factory=SpikesState)
    contact: ContactState = field(default_factory=ContactState)
    mode: SimulationMode = SimulationMode.IDLE
