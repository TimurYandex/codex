"""
Физическое ядро: верхнеуровневый класс PhysicsModel.

Каркас с базовой структурой и заглушками для последующей реализации.

Физическая модель:
===================
Симуляция удара мяча о многослойную поверхность состоит из трёх фаз:

1. PREFLIGHT (подлёт): Мяч движется по параболической траектории к поверхности.
   - Начальная позиция рассчитывается так, чтобы удар произошёл в центре окна по X
   - Время подлёта: t_pre = min(Tmax, PX / (scale * speed))
   - Гравитация действует на всём протяжении

2. CONTACT (контакт): Мяч взаимодействует с поверхностью.
   - Нормальная сила Fn: упругая + демпфирование (закон Герца с показателем 1.35)
   - Касательная сила Ft: трение со stick-slip переходом
   - Деформация поверхности: пружинно-демпферная сеть узлов
   - Шипы: наклон θ влияет на трение и касательную силу
   - Вращение мяча: omega_dot = -(Ft * r) / I

3. POST (пост-контактный полёт): Мяч отскакивает и летит дальше.
   - Свободный полёт с гравитацией
   - Затухание вращения: omega *= (1 - k_spin * dt)
   - Критерий завершения: контакт отсутствует N шагов, y > r + margin, v_y > threshold

Энергетическая защита:
- Если кинетическая энергия растёт сверх начальной — масштабирование скоростей вниз
- Защита от искусственного "разгона" отскока
"""

# =============================================================================
# Автодобавление корня проекта в sys.path для прямого запуска файла
# =============================================================================

import sys
from pathlib import Path

if __name__ == "__main__":
    # При прямом запуске файла добавляем родительскую директорию в path
    _project_root = str(Path(__file__).parent.parent)
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

# =============================================================================

from typing import Final

from config.constants import (
    DT_HIGH,
    DT_NORMAL,
    SIM_POST_DURATION,
)
from physics.sim_types import (
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

    Атрибуты:
        _params: Параметры симуляции (мяч, поверхность, столкновение)
        _mode: Текущий режим симуляции (PREFLIGHT/CONTACT/POST/FINISHED)
        _ball: Состояние мяча (позиция, скорость, вращение)
        _surface: Состояние поверхности (узлы, смещения, скорости)
        _spikes: Состояние шипов (наклон, скорость наклона)
        _contact: Состояние контакта (силы, penetration, slip)
        _history: История для графиков (Fn, Ft, def, slip, omega, vx, vy)
        _metrics: Итоговые метрики (v_out, omega_out, contact_time, ...)
        _time: Текущее время симуляции
        _no_contact_steps: Счётчик шагов без контакта (для критерия отрыва)
        _dt: Шаг времени (выбирается по качеству: normal/high)
    """

    def __init__(self) -> None:
        """
        Инициализировать физиическую модель.

        Начальное состояние:
        - Режим: IDLE (симпуляция не запущена)
        - Все массивы: нулевые/пустые
        - Время: 0.0
        """
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

        Физический смысл:
        - Подготовка поверхности: создание сетки узлов, инициализация смещений/скоростей
        - Сброс мяча: позиция будет рассчитана при первом шаге (подлёт)
        - Сброс истории и метрик: начало новой симуляции
        - Выбор шага времени: high quality → dt=5e-6, normal → dt=1e-5

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
        """
        Инициализировать массивы поверхности.

        Геометрия:
        - Равномерная сетка из n_nodes узлов
        - Диапазон X: от -half_width до +half_width
        - Шаг сетки: dx = (2 * half_width) / (n_nodes - 1)

        Начальное состояние:
        - Все смещения u_y, u_x = 0 (поверхность недеформирована)
        - Все скорости v_y, v_x = 0 (поверхность покоится)
        """
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

        Физический смысл:
        - dt умножается на time_scale для управления скоростью анимации
        - В зависимости от режима (PREFLIGHT/CONTACT/POST) выполняются разные расчёты
        - После каждого шага записывается точка истории для графиков

        Этапы шага:
        1. Применение масштаба времени: scaled_dt = dt * time_scale
        2. Обновление времени: time += scaled_dt
        3. Вызов соответствующего метода шага (_step_preflight/contact/post)
        4. Запись точки истории (Fn, Ft, def, slip, omega, vx, vy)

        Args:
            dt: Базовый шаг времени (будет умножен на time_scale из params).
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
        """
        Шаг в режиме подлёта (мяч движется к поверхности).

        Физическая модель:
        - Мяч движется по параболе под действием гравитации
        - Начальная позиция рассчитывается из условия удара в центре окна по X
        - Время подлёта: t_pre = min(Tmax, PX / (scale * speed))
        - Позиция: x(t) = x0 + vx * t, y(t) = y0 + vy * t - 0.5 * g * t²

        Переход в режим CONTACT:
        - Когда мяч достигает поверхности (y <= r + max(u_y))
        - Или когда начинается контакт (penetration > 0)

        Заглушка: в полной реализации здесь будет расчёт траектории
        до первого контакта с поверхностью.

        Args:
            dt: Шаг времени (уже масштабированный).
        """
        # Заглушка: в полной реализации здесь будет расчёт траектории
        # до первого контакта с поверхностью
        _ = dt

    def _step_contact(self, dt: float) -> None:
        """
        Шаг в режиме контакта (мяч взаимодействует с поверхностью).

        Физическая модель:

        1. Нормальная сила Fn (для каждого узла в контакте):
           - Геометрия: dd = x_ball - x_i, y_surface = y_ball - sqrt(r² - dd²)
           - Penetration: δ = u_y[i] - y_surface (если > 0, то контакт активен)
           - Сила: Fn = k_c * δ^1.35 + c_c * max(0, v_rel_n)
           - Защитный кап: Fn <= K_FORCE_CAP

        2. Касательная сила Ft (stick-slip):
           - Относительная скорость: v_rel_t = (vx - ω*r) - v_node_x
           - Накопление stick-смещения: s += v_rel_t * dt
           - Пробная сила: Ft_trial = -k_s * s
           - Критерий: |Ft_trial| <= μ_s * Fn → stick, иначе slip
           - Slip: Ft = -sign(v_rel_t) * μ_k * Fn

        3. Динамика поверхности:
           - Внутренние силы: пружины/демпферы к основанию + связи с соседями
           - Интегрирование: semi-implicit Euler
           - Клиппинг: защита от чрезмерных смещений/скоростей

        4. Динамика мяча:
           - Ускорения: ax = Ft/m, ay = Fn/m - g, omega_dot = -(Ft * r) / I
           - Интегрирование: semi-implicit Euler

        5. Шипы (если активны):
           - Динамика наклона: θ¨ = f_th - k_sh * θ - c_sh * θ_dot
           - Влияние на трение: μ_s, μ_k увеличиваются
           - Ограничение: θ ∈ [-θ_max, +θ_max]

        Переход в режим POST:
        - Когда контакт отсутствует N шагов подряд
        - И y > r + margin, v_y > threshold

        Заглушка: в полной реализации здесь будет полный расчёт контакта.

        Args:
            dt: Шаг времени (уже масштабированный).
        """
        # Заглушка: в полной реализации здесь будет расчёт:
        # - сил контакта (Fn, Ft)
        # - деформации поверхности
        # - динамики мяча
        # - шипов
        _ = dt

    def _step_post(self, dt: float) -> None:
        """
        Шаг в режиме пост-контактного полёта.

        Физическая модель:
        - Свободный полёт с гравитацией: vy += -g * dt, y += vy * dt
        - Горизонтальная скорость постоянна (без сопротивления воздуха): vx = const
        - Затухание вращения: omega *= (1 - k_spin * dt)
        - Длительность: SIM_POST_DURATION (по умолчанию 0.1 с)

        Критерий завершения (FINISHED):
        - Время пост-полёта >= SIM_POST_DURATION
        - Или мяч улетел достаточно далеко

        Итоговые метрики вычисляются в конце:
        - v_out = sqrt(vx² + vy²)
        - omega_out = omega
        - angle_out = atan2(vy, vx) в градусах
        - energy_loss = KE_initial - KE_final
        - slip_share = t_slip / t_contact

        Заглушка: в полной реализации здесь будет расчёт пост-контактного полёта.

        Args:
            dt: Шаг времени (уже масштабированный).
        """
        # Заглушка: в полной реализации здесь будет:
        # - свободный полёт с гравитацией
        # - затухание вращения
        # - проверка критерия завершения
        _ = dt

    def is_finished(self) -> bool:
        """
        Проверить, завершена ли симуляция.

        Returns:
            True, если режим FINISHED (пост-полёт завершён).
        """
        return self._mode == SimulationMode.FINISHED

    def get_mode(self) -> SimulationMode:
        """
        Получить текущий режим симуляции.

        Returns:
            Текущий режим (IDLE/PREFLIGHT/CONTACT/POST/FINISHED).
        """
        return self._mode

    def get_render_snapshot(self) -> RenderSnapshot:
        """
        Получить снимок состояния для отрисовки.

        Физический смысл:
        - Рендер получает только данные, необходимые для визуализации
        - Никакой физической логики в рендере
        - Снимок содержит: мяч, поверхность, шипы, контакт, режим

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

        Физический смысл метрик:
        - v_out: итоговая скорость мяча после отскока, м/с
        - omega_out: итоговое вращение, рад/с
        - angle_out: итоговый угол вылета (от горизонтали), градусы
        - contact_time: полное время контакта (включая подлёт), с
        - max_def: максимальная деформация поверхности, м
        - max_shift: максимальное касательное смещение узлов, м
        - slip_share: доля времени проскальзывания (0=весь stick, 1=весь slip)
        - energy_loss: потеря энергии (рассеяние в тепло/деформацию), Дж
        - j_n: импульс нормальной силы (интеграл Fn по времени), Н·с
        - j_t: импульс касательной силы, Н·с

        Returns:
            SimulationMetrics с итоговыми значениями.
        """
        return self._metrics

    def get_history(self) -> SimulationHistory:
        """
        Получить историю симуляции для графиков.

        Физический смысл истории:
        - Временные ряды для построения графиков
        - Fn(t), Ft(t): силы контакта по времени
        - def(t): деформация поверхности
        - slip(t): скорость проскальзывания
        - omega(t), vx(t), vy(t): динамика мяча

        Returns:
            SimulationHistory со списком точек истории.
        """
        return self._history

    def _record_history(self) -> None:
        """
        Записать текущее состояние в историю.

        Записываемые величины:
        - time: текущее время симуляции
        - fn, ft: нормальная и касательная силы
        - deflection: максимальное смещение поверхности (max u_y)
        - slip: скорость проскальзывания
        - omega, v_x, v_y: состояние мяча

        Эти данные используются для построения графиков после симуляции.
        """
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


# =============================================================================
# Тестовый запуск (при прямом запуске файла)
# =============================================================================

if __name__ == "__main__":
    """
    При прямом запуске файла выполняются простые тесты.

    Использование:
        python physics/model.py
    """
    import sys
    from pathlib import Path

    # Добавляем корень проекта в path для импортов ПЕРЕД остальными импортами
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from physics.model import PhysicsModel
    from physics.sim_types import (
        BallParams,
        CollisionParams,
        QualityLevel,
        SimulationParams,
        SurfaceParams,
    )

    print("Testing PhysicsModel module...\n")

    # Создание модели
    model = PhysicsModel()
    print(f"PhysicsModel created: mode={model.get_mode().value}")

    # Параметры по умолчанию
    params = SimulationParams(
        ball=BallParams(radius=0.02, mass=0.0027),
        surface=SurfaceParams(half_width=0.15, n_nodes=50),
        collision=CollisionParams(speed=10.0, angle=-30.0),
        quality=QualityLevel.NORMAL,
        time_scale=0.005,
    )

    # Reset
    model.reset(params)
    print(
        f"After reset: mode={model.get_mode().value}, n_nodes={len(model.surface.x_nodes)}"
    )

    # Несколько шагов
    for _ in range(10):
        model.step(1.0)

    print(
        f"After 10 steps: time={model.time:.6f}, history_points={len(model.get_history().points)}"
    )

    # Snapshot
    snapshot = model.get_render_snapshot()
    print(f"Snapshot: ball.x={snapshot.ball.x}, mode={snapshot.mode.value}")

    print("\n✅ All basic tests passed!")
