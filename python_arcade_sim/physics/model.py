"""
Физическое ядро: верхнеуровневый класс PhysicsModel.

Полная реализация симуляции удара мяча о многослойную поверхность.

Физическая модель:
===================
Симуляция состоит из трёх фаз:

1. PREFLIGHT (подлёт): Мяч движется по параболической траектории к поверхности.
   - Начальная позиция рассчитывается так, чтобы удар произошёл в центре окна по X
   - Время подлёта: t_pre = PX / (scale * speed)
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
    _project_root = str(Path(__file__).parent.parent)
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

# =============================================================================

from typing import Final

from config.constants import (
    DETACH_NO_CONTACT_STEPS,
    DETACH_VY_THRESHOLD,
    DETACH_Y_MARGIN,
    DT_HIGH,
    DT_NORMAL,
    G,
    K_ENERGY_SCALE,
    PREFLIGHT_T_MAX,
    SIM_POST_DURATION,
)
from physics.ball import (
    BallForces,
    clamp_rebound_priority,
    compute_ball_accelerations,
    compute_ball_kinetic_energy,
    integrate_ball,
    step_ball_post_flight,
)
from physics.contact import (
    ContactInput,
    ContactParams,
    compute_contact,
    init_contact_state,
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
from physics.spikes import (
    SpikesInput,
    SpikesOutput,
    apply_spikes_to_friction,
    compute_spikes_dynamics,
    init_spikes_state,
)
from physics.surface import (
    EquivalentSurfaceParams,
    compute_equivalent_params,
    compute_internal_forces,
    init_surface_state,
    integrate_surface,
)
from utils.math import clamp


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
        _eq_params: Эквивалентные параметры поверхности
        _contact_params: Параметры контакта
        _ke_initial: Начальная кинетическая энергия (для энергетической защиты)
        _post_time: Время пост-контактного полёта
        _max_def: Максимальная деформация поверхности
        _max_shift: Максимальное касательное смещение
        _slip_time: Общее время проскальзывания
        _contact_start_time: Время начала контакта (для расчёта contact_time)
    """

    def __init__(self) -> None:
        """
        Инициализировать физическую модель.

        Начальное состояние:
        - Режим: IDLE (симуляция не запущена)
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

        # Эквивалентные параметры
        self._eq_params: EquivalentSurfaceParams = EquivalentSurfaceParams()
        self._contact_params: ContactParams = ContactParams()

        # Энергетическая защита
        self._ke_initial: float = 0.0

        # Пост-контактный полёт
        self._post_time: float = 0.0

        # Метрики
        self._max_def: float = 0.0
        self._max_shift: float = 0.0
        self._slip_time: float = 0.0
        self._contact_start_time: float = 0.0

    def reset(self, params: SimulationParams) -> None:
        """
        Инициализировать симуляцию с заданными параметрами.

        Физический смысл:
        - Подготовка поверхности: создание сетки узлов, инициализация смещений/скоростей
        - Расчёт начальной позиции мяча для удара в центре окна по X
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
        self._post_time = 0.0
        self._max_def = 0.0
        self._max_shift = 0.0
        self._slip_time = 0.0
        self._contact_start_time = 0.0

        # Выбор шага времени по качеству
        self._dt = DT_HIGH if params.quality.value == "high" else DT_NORMAL

        # Расчёт эквивалентных параметров поверхности
        self._eq_params = compute_equivalent_params(params.surface)

        # Параметры контакта
        self._contact_params = ContactParams(
            k_c=params.ball.k,
            c_c=params.ball.c,
            k_s=self._eq_params.k_t_eq,
            mu_s=self._eq_params.mu_s_eq,
            mu_k=min(self._eq_params.mu_k_eq, self._eq_params.mu_s_eq),
        )

        # Инициализация поверхности
        self._surface = init_surface_state(params.surface)

        # Инициализация шипов
        self._spikes = init_spikes_state()

        # Сброс контакта
        self._contact = init_contact_state()

        # ====================================================================
        # Расчёт начальной позиции мяча (для удара в центре окна по X)
        # ====================================================================

        collision = params.collision
        ball = params.ball

        # Скорость мяча (разложение по углу)
        angle_rad = collision.angle * 3.141592653589793 / 180.0
        v_x = (
            collision.speed * (angle_rad**0).conjugate().real
            if hasattr(collision.speed, "conjugate")
            else collision.speed
        )
        import math

        angle_rad = collision.angle * math.pi / 180.0
        v_x = collision.speed * math.cos(angle_rad)
        v_y = collision.speed * math.sin(angle_rad)

        # Направление вращения
        omega = collision.spin
        if collision.spin_dir == "cw":
            omega = -abs(omega)
        else:
            omega = abs(omega)

        # Время подлёта (чтобы удар был в центре окна по X)
        # t_pre = PX / v_x, где PX — половина ширины поверхности
        t_pre = min(PREFLIGHT_T_MAX, params.surface.half_width / max(abs(v_x), 1.0))

        # Начальная позиция (обратная интеграция от точки удара)
        # x0 = -v_x * t_pre
        # y0 = r - v_y * t_pre + 0.5 * g * t_pre^2
        x0 = -v_x * t_pre
        y0 = ball.radius - v_y * t_pre + 0.5 * G * t_pre * t_pre

        # Инициализация состояния мяча
        self._ball = BallState(
            x=x0,
            y=y0,
            v_x=v_x,
            v_y=v_y,
            omega=omega,
            phi=0.0,
        )

        # Начальная кинетическая энергия (для энергетической защиты)
        self._ke_initial = compute_ball_kinetic_energy(self._ball, params.ball)

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
        - Начальная позиция рассчитана из условия удара в центре окна по X
        - Позиция: x(t) = x0 + vx * t, y(t) = y0 + vy * t - 0.5 * g * t²

        Переход в режим CONTACT:
        - Когда мяч достигает поверхности (y <= r + max(u_y))
        - Или когда начинается контакт (penetration > 0)

        Args:
            dt: Шаг времени (уже масштабированный).
        """
        if self._params is None:
            return

        ball_params = self._params.ball

        # Движение мяча в подлёте (только гравитация)
        forces = BallForces(fn=0.0, ft=0.0)
        accelerations = compute_ball_accelerations(self._ball, ball_params, forces)
        integrate_ball(self._ball, ball_params, accelerations, dt)

        # Проверка перехода в контакт
        # Контакт начинается, когда мяч достигает поверхности
        surface_y = max(self._surface.u_y) if self._surface.u_y else 0.0
        if self._ball.y <= ball_params.radius + surface_y:
            self._mode = SimulationMode.CONTACT
            self._contact_start_time = self._time

    def _step_contact(self, dt: float) -> None:
        """
        Шаг в режиме контакта (мяч взаимодействует с поверхностью).

        Физическая модель:

        1. Расчёт сил контакта (Fn, Ft) для каждого узла
        2. Динамика шипов (наклон θ, влияние на трение)
        3. Интегрирование поверхности (деформация)
        4. Интегрирование мяча (ускорения от Fn, Ft)
        5. Энергетическая защита (clampRebound)
        6. Проверка перехода в пост-контактный полёт

        Args:
            dt: Шаг времени (уже масштабированный).
        """
        if self._params is None:
            return

        ball_params = self._params.ball

        # ====================================================================
        # 1. Расчёт сил контакта
        # ====================================================================

        contact_input = ContactInput(
            ball_x=self._ball.x,
            ball_y=self._ball.y,
            ball_r=ball_params.radius,
            ball_v_x=self._ball.v_x,
            ball_v_y=self._ball.v_y,
            ball_omega=self._ball.omega,
            surface=self._surface,
            eq_params=self._eq_params,
            contact_params=self._contact_params,
            dt=dt,
        )

        contact_result = compute_contact(contact_input, self._contact)

        # Копируем поля из ContactResult в ContactState
        self._contact.is_active = contact_result.is_active
        self._contact.fn_total = contact_result.fn_total
        self._contact.ft_total = contact_result.ft_total
        self._contact.penetration = contact_result.max_penetration
        self._contact.slip_velocity = contact_result.slip_velocity
        self._contact.stick_displacement = contact_result.stick_displacement
        self._contact.is_slipping = contact_result.is_slipping

        # ====================================================================
        # 2. Динамика шипов
        # ====================================================================

        # Определяем режим шипов из верхнего слоя
        spike_mode = (
            self._params.surface.layers[0].spike_mode
            if self._params.surface.layers
            else None
        )

        spikes_input = SpikesInput(
            spike_params=self._eq_params.spike_params,
            mode=spike_mode,
            ft_contact=self._contact.ft_total,
            v_rel_t=self._contact.slip_velocity,
            dt=dt,
        )

        self._spikes = compute_spikes_dynamics(self._spikes, spikes_input)

        # Применяем влияние шипов на трение
        if spike_mode and spike_mode.value != "none":
            mu_s_new, mu_k_new = apply_spikes_to_friction(
                self._eq_params.mu_s_eq,
                self._eq_params.mu_k_eq,
                self._spikes,
            )
            self._contact_params.mu_s = mu_s_new
            self._contact_params.mu_k = mu_k_new

        # ====================================================================
        # 3. Интегрирование поверхности
        # ====================================================================

        forces_surface = compute_internal_forces(
            self._surface, self._params.surface, self._eq_params
        )
        integrate_surface(
            self._surface, forces_surface, self._eq_params, self._params.surface, dt
        )

        # Обновляем метрики деформации
        if self._surface.u_y:
            current_def = max(abs(u) for u in self._surface.u_y)
            self._max_def = max(self._max_def, current_def)
        if self._surface.u_x:
            current_shift = max(abs(u) for u in self._surface.u_x)
            self._max_shift = max(self._max_shift, current_shift)

        # Накопление времени проскальзывания
        if self._contact.is_slipping:
            self._slip_time += dt

        # ====================================================================
        # 4. Интегрирование мяча
        # ====================================================================

        ball_forces = BallForces(
            fn=self._contact.fn_total,
            ft=self._contact.ft_total + self._spikes.ft_additional,
        )

        accelerations = compute_ball_accelerations(self._ball, ball_params, ball_forces)
        integrate_ball(self._ball, ball_params, accelerations, dt)

        # ====================================================================
        # 5. Энергетическая защита
        # ====================================================================

        clamp_rebound_priority(self._ball, ball_params, self._ke_initial)

        # ====================================================================
        # 6. Проверка перехода в пост-контактный полёт
        # ====================================================================

        if not self._contact.is_active:
            self._no_contact_steps += 1
        else:
            self._no_contact_steps = 0

        # Критерий отрыва:
        # - Контакт отсутствует N шагов подряд
        # - y > r + margin
        # - v_y > threshold
        y_threshold = ball_params.radius + DETACH_Y_MARGIN
        if (
            self._no_contact_steps >= DETACH_NO_CONTACT_STEPS
            and self._ball.y > y_threshold
            and abs(self._ball.v_y) > DETACH_VY_THRESHOLD
        ):
            self._mode = SimulationMode.POST
            self._post_time = 0.0

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

        Итоговые метрики вычисляются в конце:
        - v_out = sqrt(vx² + vy²)
        - omega_out = omega
        - angle_out = atan2(vy, vx) в градусах
        - energy_loss = KE_initial - KE_final
        - slip_share = t_slip / t_contact

        Args:
            dt: Шаг времени (уже масштабированный).
        """
        if self._params is None:
            return

        ball_params = self._params.ball

        # Пост-контактный полёт
        step_ball_post_flight(self._ball, ball_params, dt)
        self._post_time += dt

        # Проверка завершения
        if self._post_time >= SIM_POST_DURATION:
            self._mode = SimulationMode.FINISHED
            self._compute_final_metrics()

    def _compute_final_metrics(self) -> None:
        """
        Вычислить итоговые метрики симуляции.

        Метрики:
        - v_out: итоговая скорость, м/с
        - omega_out: итоговое вращение, рад/с
        - angle_out: итоговый угол, градусы
        - contact_time: полное время контакта (включая подлёт), с
        - max_def: максимальная деформация поверхности, м
        - max_shift: максимальное касательное смещение, м
        - slip_share: доля времени проскальзывания
        - energy_loss: потеря энергии, Дж
        - j_n, j_t: импульсы сил, Н·с
        """
        if self._params is None:
            return

        ball_params = self._params.ball

        # Итоговая скорость
        v_out = (self._ball.v_x**2 + self._ball.v_y**2) ** 0.5

        # Итоговый угол (в градусах)
        import math

        angle_out = math.atan2(self._ball.v_y, self._ball.v_x) * 180.0 / math.pi

        # Потеря энергии
        ke_final = compute_ball_kinetic_energy(self._ball, ball_params)
        energy_loss = self._ke_initial - ke_final

        # Доля проскальзывания
        contact_duration = (
            self._time - self._contact_start_time
            if self._contact_start_time > 0
            else self._time
        )
        slip_share = (
            self._slip_time / max(contact_duration, 1e-9)
            if contact_duration > 0
            else 0.0
        )

        # Импульсы сил (приближённо, из истории)
        j_n = sum(p.fn for p in self._history.points) * self._dt
        j_t = sum(p.ft for p in self._history.points) * self._dt

        self._metrics = SimulationMetrics(
            v_out=v_out,
            omega_out=self._ball.omega,
            angle_out=angle_out,
            contact_time=self._time,  # Включает подлёт
            max_def=self._max_def,
            max_shift=self._max_shift,
            slip_share=slip_share,
            energy_loss=energy_loss,
            j_n=j_n,
            j_t=j_t,
        )

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
            fn=self._contact.fn_total,
            ft=self._contact.ft_total,
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
    print(
        f"  ball: x={model.ball.x:.4f}, y={model.ball.y:.4f}, v_x={model.ball.v_x:.2f}, v_y={model.ball.v_y:.2f}"
    )

    # Несколько шагов
    for i in range(50):
        model.step(1.0)
        if model.is_finished():
            print(f"  Simulation finished at step {i}")
            break

    print(f"After steps: time={model.time:.6f}, mode={model.get_mode().value}")
    print(
        f"  ball: x={model.ball.x:.4f}, y={model.ball.y:.4f}, v_x={model.ball.v_x:.2f}, v_y={model.ball.v_y:.2f}"
    )

    # Snapshot
    snapshot = model.get_render_snapshot()
    print(f"Snapshot: ball.x={snapshot.ball.x}, mode={snapshot.mode.value}")

    # Метрики (если симуляция завершена)
    if model.is_finished():
        metrics = model.get_metrics()
        print(
            f"Metrics: v_out={metrics.v_out:.2f}, omega_out={metrics.omega_out:.2f}, angle_out={metrics.angle_out:.1f}"
        )

    print("\n✅ All basic tests passed!")
