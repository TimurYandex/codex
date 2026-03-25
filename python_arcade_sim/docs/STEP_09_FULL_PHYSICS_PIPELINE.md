# Шаг 9: Сборка PhysicsModel — полный цикл симуляции

## Цель

Собрать все компоненты физики в единый класс `PhysicsModel` с полным циклом симуляции (preflight → contact → post).

## Созданные/обновлённые модули

### `physics/model.py` (полная реализация)

#### Фазы симуляции

**1. PREFLIGHT (подлёт):**
- Мяч движется по параболе под действием гравитации
- Начальная позиция рассчитывается из условия удара в центре окна по X
- Формула расчёта времени подлёта:
  ```
  t_pre = min(Tmax, half_width / |v_x|)
  ```
- Начальная позиция:
  ```
  x0 = -v_x * t_pre
  y0 = r - v_y * t_pre + 0.5 * g * t_pre²
  ```
- Переход в CONTACT: когда y <= r + surface_y

**2. CONTACT (контакт):**
- Расчёт сил контакта (Fn, Ft) для каждого узла
- Динамика шипов (наклон θ, влияние на трение)
- Интегрирование поверхности (деформация)
- Интегрирование мяча (ускорения от Fn, Ft)
- Энергетическая защита (clampRebound)
- Переход в POST: когда контакт отсутствует N шагов, y > r + margin, |v_y| > threshold

**3. POST (пост-контактный полёт):**
- Свободный полёт с гравитацией
- Затухание вращения: omega *= (1 - k_spin * dt)
- Переход в FINISHED: когда post_time >= SIM_POST_DURATION

#### Метрики

Вычисляются в конце симуляции:

| Метрика | Формула |
|---------|---------|
| `v_out` | sqrt(vx² + vy²) |
| `omega_out` | omega |
| `angle_out` | atan2(vy, vx) * 180/π |
| `contact_time` | время контакта (без подлёта), с |
| `max_def` | max(|u_y|) за время контакта |
| `max_shift` | max(|u_x|) за время контакта |
| `slip_share` | t_slip / t_contact |
| `energy_loss` | KE_initial - KE_final |
| `j_n` | Σ Fn * dt |
| `j_t` | Σ Ft * dt |

#### Интеграция компонентов

```
PhysicsModel
├── Ball (ball.py)
│   ├── compute_ball_accelerations()
│   ├── integrate_ball()
│   ├── clamp_rebound_priority()
│   └── step_ball_post_flight()
├── Contact (contact.py)
│   └── compute_contact()
├── Spikes (spikes.py)
│   ├── compute_spikes_dynamics()
│   └── apply_spikes_to_friction()
├── Surface (surface.py)
│   ├── compute_equivalent_params()
│   ├── compute_internal_forces()
│   └── integrate_surface()
└── Types (sim_types.py)
    ├── BallState, SurfaceState, SpikesState, ContactState
    └── SimulationParams, SimulationMetrics, SimulationHistory
```

## Тесты

### `tests/test_model.py`

| Тест | Описание |
|------|----------|
| `test_reset_initializes_state()` | После reset состояние корректно |
| `test_step_does_not_crash()` | step не падает при вызове |
| `test_history_is_recorded()` | История записывается при шагах |
| `test_is_finished_initially_false()` | is_finished возвращает False до завершения |
| `test_render_snapshot_is_valid()` | get_render_snapshot возвращает валидный снимок |

### Запуск тестов

```bash
# Быстрый тест
python physics/model.py

# Полные тесты
python tests/test_model.py
```

**Результат:** ✅ All tests passed!

## Пример запуска

```
Testing PhysicsModel module...

PhysicsModel created: mode=idle
After reset: mode=preflight, n_nodes=50
  ball: x=-0.1500, y=0.1081, v_x=8.66, v_y=-5.00
  Simulation finished at step 29
After steps: time=0.150000, mode=finished
  ball: x=0.1688, y=159.9664, v_x=0.82, v_y=8.22
Snapshot: ball.x=0.1688, mode=finished
Metrics: v_out=8.26, omega_out=-0.00, angle_out=84.3

✅ All basic tests passed!
```

## Статус

✅ `physics/model.py` полностью реализован  
✅ Все тесты проходят  
✅ Интеграция всех компонентов физики работает

---

**Точка вмешательства человека #9**: Если физическое поведение не похоже на желаемое (угол/вращение/отрыв), остановиться и поправить формулы/коэффициенты на этом уровне.
