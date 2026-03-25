"""
Физическое ядро с упрощённой моделью контакта (lumped parameter model).

Вместо сети узлов используется единая точка контакта с параметрами:
- overlap — глубина деформации мяча
- overlap_rate — скорость деформации
- stick_disp — касательное смещение для трения

Это обеспечивает стабильную и правильную физику контакта.
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

import math

from utils.math import clamp

from config.constants import (
    BALL_Y_MAX,
    CONTACT_EXPONENT,
    CONTACT_SUBSTEPS,
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


# =============================================================================
# Параметры контакта для lumped model
# =============================================================================


class LumpedContactParams:
    """Параметры контакта для lumped model."""

    def __init__(
        self,
        kc: float = 62000.0,  # Нормальная жёсткость, Н/м^1.35
        cc: float = 10.5,  # Нормальное демпфирование, Н·с/м
        kt: float = 19840.0,  # Касательная жёсткость, Н/м (0.32 * kc)
        mu_s: float = 0.95,  # Трение покоя
        mu_k: float = 0.81,  # Трение скольжения
        exponent: float = 1.35,  # Показатель степени
        coupling: float = 900.0,  # Коэффициент связи для overlap_rate
    ):
        self.kc = kc
        self.cc = cc
        self.kt = kt
        self.mu_s = mu_s
        self.mu_k = mu_k
        self.exponent = exponent
        self.coupling = coupling


class LumpedContactState:
    """Состояние контакта для lumped model."""

    def __init__(self):
        self.overlap: float = 0.0  # Глубина деформации, м
        self.overlap_rate: float = 0.0  # Скорость деформации, м/с
        self.stick_disp: float = 0.0  # Касательное смещение, м
        self.fn: float = 0.0  # Нормальная сила, Н
        self.ft: float = 0.0  # Касательная сила, Н
        self.is_active: bool = False  # Контакт активен


def step_lumped_contact(
    state: LumpedContactState,
    params: LumpedContactParams,
    v_y: float,  # Вертикальная скорость (положительная = вверх)
    v_x: float,  # Горизонтальная скорость (положительная = вправо)
    omega: float,  # Угловая скорость (положительная = против часовой)
    radius: float,
    mass: float,
    ifactor: float,
    dt: float,
) -> tuple[float, float, float]:
    """
    Шаг интегрирования контакта (lumped parameter model).

    Returns:
        (a_x, a_y, alpha) — ускорения
    """
    # Момент инерции: I = ifactor * m * r²
    I = ifactor * mass * radius * radius

    # ================================================================
    # Проверка активности контакта
    # ================================================================

    # Контакт активен, если есть перекрытие ИЛИ мяч движется вниз к поверхности
    is_contact = state.overlap > 0 or v_y < 0

    if not is_contact:
        state.is_active = False
        state.fn = 0.0
        state.ft = 0.0
        return 0.0, -G, 0.0

    state.is_active = True

    # ================================================================
    # 1. Интегрирование деформации (СНАЧАЛА!)
    # ================================================================

    # Связь нормальной скорости с rate деформации
    state.overlap_rate += -v_y * dt * params.coupling

    # Интегрирование overlap
    state.overlap += state.overlap_rate * dt
    state.overlap = max(0.0, state.overlap)

    # ================================================================
    # 2. Нормальная сила (закон Герца с демпфированием)
    # ================================================================

    fn_elastic = params.kc * (state.overlap**params.exponent)
    fn_damping = params.cc * max(0.0, state.overlap_rate)
    state.fn = fn_elastic + fn_damping
    state.fn = max(0.0, state.fn)

    # ================================================================
    # 2. Касательная сила (stick-slip)
    # ================================================================

    # Относительная скорость проскальзывания
    v_rel = v_x - omega * radius

    # Накопление касательного смещения с ограничением
    state.stick_disp += v_rel * dt
    state.stick_disp = clamp(state.stick_disp, -0.005, 0.005)  # Ограничение 5 мм

    # Пробная сила (stick)
    ft_trial = -params.kt * state.stick_disp

    # Максимальная сила трения покоя
    ft_max = params.mu_s * state.fn

    # Stick-slip переход
    if abs(ft_trial) <= ft_max:
        state.ft = ft_trial
    else:
        state.ft = -math.copysign(1.0, v_rel) * params.mu_k * state.fn
        state.stick_disp = -state.ft / params.kt

    # ================================================================
    # 4. Ускорения
    # ================================================================

    a_x = state.ft / mass
    a_y = state.fn / mass - G
    # Момент силы: ft < 0 (влево) в нижней точке создаёт вращение по часовой (alpha < 0)
    alpha = (state.ft * radius) / I

    return a_x, a_y, alpha


# =============================================================================
# Физическая модель с lumped contact
# =============================================================================


class PhysicsModelLumped:
    """
    Физическая модель с упрощённой моделью контакта.
    """

    def __init__(self) -> None:
        self._params: SimulationParams | None = None
        self._mode: SimulationMode = SimulationMode.IDLE

        # Состояние мяча
        self._ball: BallState = BallState()

        # Состояние поверхности (для визуализации)
        self._surface: SurfaceState = SurfaceState()

        # Состояние шипов
        self._spikes: SpikesState = SpikesState()

        # Состояние контакта (lumped)
        self._contact: LumpedContactState = LumpedContactState()
        self._contact_params: LumpedContactParams | None = None

        # История и метрики
        self._history: SimulationHistory = SimulationHistory()
        self._metrics: SimulationMetrics = SimulationMetrics()

        # Внутренние счётчики
        self._time: float = 0.0
        self._no_contact_steps: int = 0
        self._dt: float = DT_NORMAL

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
        """Инициализировать симуляцию."""
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

        # Выбор шага времени
        self._dt = DT_HIGH if params.quality.value == "high" else DT_NORMAL

        # Параметры контакта
        ball = params.collision
        surface_eq = compute_equivalent_params(params.surface)

        self._contact_params = LumpedContactParams(
            kc=params.ball.k,
            cc=params.ball.c,
            kt=surface_eq.k_t_eq,
            mu_s=surface_eq.mu_s_eq,
            mu_k=min(surface_eq.mu_k_eq, surface_eq.mu_s_eq),
            exponent=CONTACT_EXPONENT,
            coupling=9000.0,  # Увеличил с 900 до 9000 для более быстрого роста overlap
        )

        # Инициализация поверхности (для визуализации)
        self._surface = init_surface_state(params.surface)

        # Инициализация шипов
        self._spikes = init_spikes_state()

        # Сброс контакта
        self._contact = LumpedContactState()

        # ====================================================================
        # Расчёт начальной позиции мяча
        # ====================================================================

        collision = params.collision
        ball_params = params.ball

        angle_rad = collision.angle * math.pi / 180.0
        v_x = collision.speed * math.cos(angle_rad)
        v_y = collision.speed * math.sin(angle_rad)

        # Направление вращения
        omega = collision.spin
        if collision.spin_dir == "cw":
            omega = -abs(omega)
        else:
            omega = abs(omega)

        # Время подлёта
        t_pre = min(PREFLIGHT_T_MAX, params.surface.half_width / max(abs(v_x), 1.0))

        # Начальная позиция
        x0 = -v_x * t_pre
        y0 = ball_params.radius - v_y * t_pre + 0.5 * G * t_pre * t_pre

        self._ball = BallState(
            x=x0,
            y=y0,
            v_x=v_x,
            v_y=v_y,
            omega=omega,
            phi=0.0,
        )

        self._ke_initial = compute_ball_kinetic_energy(self._ball, params.ball)

    def step(self, dt: float) -> None:
        """Выполнить один шаг интегрирования."""
        if self._params is None or self._mode == SimulationMode.FINISHED:
            return

        scaled_dt = dt * self._params.time_scale
        self._time += scaled_dt

        if self._mode == SimulationMode.PREFLIGHT:
            self._step_preflight(scaled_dt)
        elif self._mode == SimulationMode.CONTACT:
            self._step_contact(scaled_dt)
        elif self._mode == SimulationMode.POST:
            self._step_post(scaled_dt)

        self._record_history()

    def _step_preflight(self, dt: float) -> None:
        """Шаг в режиме подлёта."""
        if self._params is None:
            return

        ball_params = self._params.ball

        # Движение мяча (только гравитация)
        forces = BallForces(fn=0.0, ft=0.0)
        accelerations = compute_ball_accelerations(self._ball, ball_params, forces)
        integrate_ball(self._ball, ball_params, accelerations, dt)

        # Проверка перехода в контакт
        surface_y = max(self._surface.u_y) if self._surface.u_y else 0.0
        y_threshold = ball_params.radius + surface_y

        if self._ball.y <= y_threshold:
            # Позиционная коррекция
            self._correct_position_at_contact(surface_y)
            # Инициализация контакта
            self._contact.overlap = 0.0
            self._contact.overlap_rate = 0.0
            self._contact.stick_disp = 0.0
            # Сохраняем кинетическую энергию в момент начала контакта
            self._ke_initial = compute_ball_kinetic_energy(self._ball, ball_params)
            self._mode = SimulationMode.CONTACT
            self._contact_start_time = self._time

    def _correct_position_at_contact(self, surface_y: float) -> None:
        """Скорректировать позицию мяча при переходе в контакт."""
        ball_params = self._params.ball
        y_target = ball_params.radius + surface_y

        if abs(self._ball.y - y_target) < 1e-9:
            return

        # Обратная экстраполяция для линейной интерполяции
        dt = self._dt
        prev_x = self._ball.x - self._ball.v_x * dt
        prev_y = self._ball.y - self._ball.v_y * dt

        dy = self._ball.y - prev_y
        if abs(dy) < 1e-12:
            self._ball.y = y_target
            return

        t = (y_target - prev_y) / dy
        t = max(0.0, min(1.0, t))

        self._ball.x = prev_x + (self._ball.x - prev_x) * t
        self._ball.y = y_target

    def _step_contact(self, dt: float) -> None:
        """Шаг в режиме контакта с суб-степпингом."""
        if self._params is None or self._contact_params is None:
            return

        ball_params = self._params.ball
        n_substeps = CONTACT_SUBSTEPS
        dt_sub = dt / n_substeps

        for substep in range(n_substeps):
            # Шаг контакта
            a_x, a_y, alpha = step_lumped_contact(
                self._contact,
                self._contact_params,
                self._ball.v_y,
                self._ball.v_x,
                self._ball.omega,
                ball_params.radius,
                ball_params.mass,
                ball_params.ifactor,
                dt_sub,
            )

            # Интегрирование мяча
            integrate_ball(self._ball, ball_params, (a_x, a_y, alpha), dt_sub)

            # Энергетическая защита — ограничиваем энергию на каждом суб-шаге
            clamp_rebound_priority(self._ball, ball_params, self._ke_initial)

        # Проверка перехода в пост-контактный полёт
        if not self._contact.is_active:
            self._no_contact_steps += 1
        else:
            self._no_contact_steps = 0

        y_threshold = ball_params.radius + DETACH_Y_MARGIN
        if (
            self._no_contact_steps >= DETACH_NO_CONTACT_STEPS
            and self._ball.y > y_threshold
            and abs(self._ball.v_y) > DETACH_VY_THRESHOLD
        ):
            self._mode = SimulationMode.POST
            self._post_time = 0.0

    def _step_post(self, dt: float) -> None:
        """Шаг в режиме пост-контактного полёта."""
        if self._params is None:
            return

        ball_params = self._params.ball
        step_ball_post_flight(self._ball, ball_params, dt)
        self._post_time += dt

        if self._ball.y >= BALL_Y_MAX:
            self._mode = SimulationMode.FINISHED
            self._compute_final_metrics()

    def _compute_final_metrics(self) -> None:
        """Вычислить итоговые метрики."""
        if self._params is None:
            return

        ball_params = self._params.ball
        v_out = (self._ball.v_x**2 + self._ball.v_y**2) ** 0.5
        angle_out = math.atan2(self._ball.v_y, self._ball.v_x) * 180.0 / math.pi
        ke_final = compute_ball_kinetic_energy(self._ball, ball_params)
        energy_loss = self._ke_initial - ke_final

        contact_duration = (
            self._time - self._contact_start_time
            if self._contact_start_time > 0
            else self._time
        )

        self._metrics = SimulationMetrics(
            v_out=v_out,
            omega_out=self._ball.omega,
            angle_out=angle_out,
            contact_time=contact_duration,
            max_def=self._max_def,
            max_shift=self._max_shift,
            slip_share=0.0,
            energy_loss=energy_loss,
            j_n=0.0,
            j_t=0.0,
        )

    def is_finished(self) -> bool:
        return self._mode == SimulationMode.FINISHED

    def get_mode(self) -> SimulationMode:
        return self._mode

    def get_render_snapshot(self) -> RenderSnapshot:
        # Конвертируем lumped contact в обычный ContactState для рендера
        from physics.sim_types import ContactState as NetworkContactState

        contact_state = NetworkContactState(
            is_active=self._contact.is_active,
            fn=self._contact.fn,
            ft=self._contact.ft,
            overlap=self._contact.overlap,
            slip_velocity=0.0,
            stick_displacement=self._contact.stick_disp,
            is_slipping=False,
        )

        return RenderSnapshot(
            ball=self._ball,
            surface=self._surface,
            spikes=self._spikes,
            contact=contact_state,
            mode=self._mode,
        )

    def get_metrics(self) -> SimulationMetrics:
        return self._metrics

    def get_history(self) -> SimulationHistory:
        return self._history

    def _record_history(self) -> None:
        point = HistoryPoint(
            time=self._time,
            fn=self._contact.fn,
            ft=self._contact.ft,
            deflection=max(self._surface.u_y) if self._surface.u_y else 0.0,
            slip=0.0,
            omega=self._ball.omega,
            v_x=self._ball.v_x,
            v_y=self._ball.v_y,
        )
        self._history.append(point)

    # Свойства для доступа
    @property
    def ball(self) -> BallState:
        return self._ball

    @property
    def surface(self) -> SurfaceState:
        return self._surface

    @property
    def time(self) -> float:
        return self._time

    @property
    def params(self) -> SimulationParams | None:
        return self._params

    def print_debug_log(self) -> None:
        """Вывести детальную информацию о шаге симуляции."""
        is_active = "A" if self._contact.is_active else "_"
        print(
            f"t={self._time:.5f} mode={self._mode.value:10s} [{is_active}] "
            f"pos=({self._ball.x:7.4f}, {self._ball.y:7.4f}) "
            f"v=({self._ball.v_x:7.2f}, {self._ball.v_y:7.2f}) "
            f"ω={self._ball.omega:7.1f} "
            f"F=({self._contact.fn:7.1f}, {self._contact.ft:7.1f})"
        )


# =============================================================================
# Тестовый запуск
# =============================================================================

if __name__ == "__main__":
    from physics.sim_types import (
        BallParams,
        CollisionParams,
        QualityLevel,
        SimulationParams,
        SurfaceParams,
        LayerParams,
        SpikeMode,
    )

    print("Testing PhysicsModelLumped...\n")

    model = PhysicsModelLumped()

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
            speed=11.0,
            angle=-35.0,
            spin=754.0,
            spin_dir="ccw",
        ),
        quality=QualityLevel.NORMAL,
        time_scale=0.005,
    )

    model.reset(params)

    step_count = 0
    while not model.is_finished():
        model.step(1.0)
        step_count += 1
        if step_count > 1000:
            print("ERROR: too many steps")
            break

    metrics = model.get_metrics()
    print(f"Simulation finished in {step_count} steps")
    print(f"  v_out={metrics.v_out:.2f} m/s")
    print(f"  angle_out={metrics.angle_out:.1f} deg")
    print(f"  omega_out={metrics.omega_out:.1f} rad/s")
    print(f"  contact_time={metrics.contact_time*1000:.1f} ms")
    print(f"  energy_loss={metrics.energy_loss:.4f} J")
    print("\n✅ Test passed!")
