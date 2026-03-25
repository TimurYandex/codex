# Шаг 3: Контракт данных (состояние/параметры/метрики)

## Цель

Определить "границу" между физикой и рендером/UI. Все структуры данных независимы от `arcade`.

## Созданные модули

### `utils/math.py`

Вспомогательные функции:

| Функция | Описание |
|---------|----------|
| `clamp(value, min_val, max_val)` | Ограничение значения диапазоном |
| `sign(value)` | Вернуть знак: -1, 0, +1 |
| `safe_sqrt(value, default)` | Безопасный квадратный корень (защита от отрицательных значений) |
| `lerp(a, b, t)` | Линейная интерполяция |
| `exp_decay(x, rate)` | Экспоненциальное затухание `exp(-x * rate)` |

### `config/constants.py`

Константы устойчивости и масштабирования (`K`):

| Константа | Значение | Описание |
|-----------|----------|----------|
| `G` | 9.81 | Ускорение свободного падения, м/с² |
| `BALL_RADIUS_DEFAULT` | 0.02 | Радиус мяча по умолчанию, м |
| `BALL_MASS_DEFAULT` | 0.0027 | Масса мяча по умолчанию, кг |
| `DT_NORMAL` | 1e-5 | Шаг времени для качества 'normal', с |
| `DT_HIGH` | 5e-6 | Шаг времени для качества 'high', с |
| `K_FORCE_CAP` | 1e5 | Защитный кап для сил, Н |
| `K_VELOCITY_CAP` | 100.0 | Защитный кап для скоростей, м/с |
| `K_ENERGY_SCALE` | 0.999 | Коэффициент сохранения энергии |
| `CONTACT_EXPONENT` | 1.35 | Показатель степени в законе Герца |
| `MATERIAL_DENSITIES` | dict | Таблица плотностей материалов |

### `physics/types.py`

#### Перечисления (Enums)

- `SpikeMode`: `NONE`, `OUT`, `IN` — режим шипов
- `QualityLevel`: `NORMAL`, `HIGH` — качество симуляции
- `SimulationMode`: `IDLE`, `PREFLIGHT`, `CONTACT`, `POST`, `FINISHED` — режим симуляции

#### Входные параметры

| Класс | Описание |
|-------|----------|
| `BallParams` | Параметры мяча: `radius`, `mass`, `ifactor`, `k`, `c`, `is_hollow` |
| `LayerParams` | Параметры слоя: `thickness`, `k_n`, `c_n`, `k_t`, `c_t`, `mu_s`, `mu_k`, `spike_mode`, `k_sh`, `h`, `p`, `material` |
| `SurfaceParams` | Параметры поверхности: `layers`, `half_width`, `depth`, `n_nodes`, `fr_mul` |
| `CollisionParams` | Параметры столкновения: `speed`, `angle`, `spin`, `spin_dir` |
| `SimulationParams` | Все параметры: `ball`, `surface`, `collision`, `quality`, `time_scale` |

#### Состояние

| Класс | Описание |
|-------|----------|
| `BallState` | Состояние мяча: `x`, `y`, `v_x`, `v_y`, `omega`, `phi` |
| `SurfaceState` | Состояние поверхности: `x_nodes`, `u_y`, `u_x`, `v_y`, `v_x`, `active_nodes`, `pressure` |
| `SpikesState` | Состояние шипов: `theta`, `theta_dot` |
| `ContactState` | Состояние контакта: `is_active`, `fn`, `ft`, `penetration`, `slip_velocity`, `stick_displacement`, `is_slipping` |

#### Метрики и история

| Класс | Описание |
|-------|----------|
| `SimulationMetrics` | Итоговые метрики: `v_out`, `omega_out`, `angle_out`, `contact_time`, `max_def`, `max_shift`, `slip_share`, `energy_loss`, `j_n`, `j_t` |
| `HistoryPoint` | Точка истории: `time`, `fn`, `ft`, `deflection`, `slip`, `omega`, `v_x`, `v_y` |
| `SimulationHistory` | История симуляции: список `points` |

#### Снимок для рендера

| Класс | Описание |
|-------|----------|
| `RenderSnapshot` | Снимок состояния: `ball`, `surface`, `spikes`, `contact`, `mode` |

## Контракт между модулями

```
UI → SimulationParams → PhysicsModel
                              ↓
                      RenderSnapshot → Renderer
                              ↓
                      SimulationMetrics → UI
```

1. **UI** передаёт `SimulationParams` в `PhysicsModel`
2. **PhysicsModel** возвращает `RenderSnapshot` для отрисовки
3. **PhysicsModel** возвращает `SimulationMetrics` для отображения
4. **Renderer** не содержит физической логики, только читает данные

## Статус

✅ `utils/math.py` создан  
✅ `config/constants.py` создан  
✅ `physics/types.py` создан  
✅ `__init__.py` для пакетов созданы

---

**Точка вмешательства человека #3**: Проверить согласованность данных: рендер должен быть способен рисовать "как в плане" только из данных физики + параметров.
