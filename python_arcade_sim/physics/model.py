"""
Физическое ядро: верхнеуровневый класс PhysicsModel.

Каркас с базовой структурой и заглушками для последующей реализации.
"""

from typing import Final

from config.constants import (
    DT_HIGH,
    DT_NORMAL,
    SIM_POST_DURATION,
)
from physics.types import (
    BallState,
    ContactState,
    HistoryPoint,
    RenderSnapshot,
    SimulationHistory,
    SimulationMetrics,
    SimulationMode,
    SimulationParams,
    SpikesState,
    SurfaceState,
)


class PhysicsModel:
    """
    Верхнеуровневый класс физической модели.
    
    Управление симуляцией через:
    - reset(params) — инициализация
    - step(dt) — шаг интегрирования
    - is_finished() — проверка завершения
    - get_render_snapshot() — снимок для рендера
    - get_metrics() — итоговые метрики
    """

    def __init__(self) -> None:
        self._params: SimulationParams | None = None
        self._mode: SimulationMode = SimulationMode.IDLE
        
        # Состояние мяча
        self._ball: BallState = BallState()
        
        # Состояние поверхности
        self._surface: SurfaceState = SurfaceState()
        
        # Состояние шипов
        self._spikes: SpikesState = SpikesState()
        
        # Состояние контакта
        self._contact: ContactState = ContactState()
        
        # История и метрики
        self._history: SimulationHistory = SimulationHistory()
        self._metrics: SimulationMetrics = SimulationMetrics()
        
        # Внутренние счётчики
        self._time: float = 0.0
        self._no_contact_steps: int = 0
        self._dt: float = DT_NORMAL

    def reset(self, params: SimulationParams) -> None:
        """
        Инициализировать симуляцию с заданными параметрами.
        
        Args:
            params: Входные параметры симуляции.
        """
        self._params = params
        self._mode = SimulationMode.PREFLIGHT
        self._time = 0.0
        self._no_contact_steps = 0
        self._history = SimulationHistory()
        self._metrics = SimulationMetrics()
        
        # Выбор шага времени по качеству
        self._dt = DT_HIGH if params.quality.value == "high" else DT_NORMAL
        
        # Инициализация мяча (будет рассчитана в step)
        self._ball = BallState()
        
        # Инициализация поверхности (создание узлов)
        self._init_surface()
        
        # Инициализация шипов
        self._spikes = SpikesState()
        
        # Сброс контакта
        self._contact = ContactState()

    def _init_surface(self) -> None:
        """Инициализировать массивы поверхности."""
        if self._params is None:
            return
        
        surf = self._params.surface
        n = surf.n_nodes
        hw = surf.half_width
        
        # Равномерная сетка от -hw до +hw
        dx = (2 * hw) / (n - 1) if n > 1 else 0
        
        self._surface = SurfaceState(
            x_nodes=[-hw + i * dx for i in range(n)],
            u_y=[0.0] * n,
            u_x=[0.0] * n,
            v_y=[0.0] * n,
            v_x=[0.0] * n,
            active_nodes=[],
            pressure=[],
        )

    def step(self, dt: float) -> None:
        """
        Выполнить один шаг интегрирования.
        
        Args:
            dt: Шаг времени (будет умножен на time_scale из params).
        """
        if self._params is None or self._mode == SimulationMode.FINISHED:
            return
        
        # Применяем масштаб времени
        scaled_dt = dt * self._params.time_scale
        
        # Обновляем время
        self._time += scaled_dt
        
        # В зависимости от режима выполняем разные действия
        if self._mode == SimulationMode.PREFLIGHT:
            self._step_preflight(scaled_dt)
        elif self._mode == SimulationMode.CONTACT:
            self._step_contact(scaled_dt)
        elif self._mode == SimulationMode.POST:
            self._step_post(scaled_dt)
        
        # Записываем точку истории
        self._record_history()

    def _step_preflight(self, dt: float) -> None:
        """Шаг в режиме подлёта (мяч движется к поверхности)."""
        # Заглушка: в полной реализации здесь будет расчёт траектории
        # до первого контакта с поверхностью
        _ = dt

    def _step_contact(self, dt: float) -> None:
        """Шаг в режиме контакта (мяч взаимодействует с поверхностью)."""
        # Заглушка: в полной реализации здесь будет расчёт:
        # - сил контакта (Fn, Ft)
        # - деформации поверхности
        # - динамики мяча
        # - шипов
        _ = dt

    def _step_post(self, dt: float) -> None:
        """Шаг в режиме пост-контактного полёта."""
        # Заглушка: в полной реализации здесь будет:
        # - свободный полёт с гравитацией
        # - затухание вращения
        # - проверка критерия завершения
        _ = dt

    def is_finished(self) -> bool:
        """Проверить, завершена ли симуляция."""
        return self._mode == SimulationMode.FINISHED

    def get_mode(self) -> SimulationMode:
        """Получить текущий режим симуляции."""
        return self._mode

    def get_render_snapshot(self) -> RenderSnapshot:
        """
        Получить снимок состояния для отрисовки.
        
        Returns:
            RenderSnapshot с текущим состоянием мяча, поверхности, шипов и контакта.
        """
        return RenderSnapshot(
            ball=self._ball,
            surface=self._surface,
            spikes=self._spikes,
            contact=self._contact,
            mode=self._mode,
        )

    def get_metrics(self) -> SimulationMetrics:
        """
        Получить итоговые метрики симуляции.
        
        Returns:
            SimulationMetrics с итоговыми значениями.
        """
        return self._metrics

    def get_history(self) -> SimulationHistory:
        """
        Получить историю симуляции для графиков.
        
        Returns:
            SimulationHistory со списком точек истории.
        """
        return self._history

    def _record_history(self) -> None:
        """Записать текущее состояние в историю."""
        point = HistoryPoint(
            time=self._time,
            fn=self._contact.fn,
            ft=self._contact.ft,
            deflection=max(self._surface.u_y) if self._surface.u_y else 0.0,
            slip=self._contact.slip_velocity,
            omega=self._ball.omega,
            v_x=self._ball.v_x,
            v_y=self._ball.v_y,
        )
        self._history.append(point)

    # ========================================================================
    # Свойства для доступа извне (для отладки и тестов)
    # ========================================================================

    @property
    def ball(self) -> BallState:
        """Состояние мяча."""
        return self._ball

    @property
    def surface(self) -> SurfaceState:
        """Состояние поверхности."""
        return self._surface

    @property
    def time(self) -> float:
        """Текущее время симуляции."""
        return self._time

    @property
    def params(self) -> SimulationParams | None:
        """Параметры симуляции."""
        return self._params
