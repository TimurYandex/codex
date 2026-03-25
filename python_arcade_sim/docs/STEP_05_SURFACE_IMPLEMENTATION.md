# Шаг 5: Физика поверхности — узлы, слои, эквивалентные параметры

## Цель

Реализовать дискретную поверхность с массивами узлов, расчёт эквивалентных параметров по слоям, внутренние силы (пружины/демпферы/связи) и граничные условия.

## Созданные модули

### `physics/surface.py`

#### Эквивалентные параметры слоёв

Функция `compute_equivalent_params(params)`:

| Параметр | Формула |
|----------|---------|
| `k_n_eq` | Гармоническое сложение: `1 / Σ(t_i / k_n_i)` |
| `k_t_eq` | Гармоническое сложение: `1 / Σ(t_i / k_t_i)` |
| `mu_s_eq`, `mu_k_eq` | Взвешенное среднее с `exp(-i * p)` |
| `mass_per_meter` | `Σ(ρ_i * t_i * depth)` |
| `spike_params` | Параметры шипов из верхнего слоя (если режим != `none`) |

**Ограничения:**
- `mu_k <= mu_s` (принудительное ограничение)
- Применение глобального множителя `fr_mul`

#### Внутренние силы поверхности

Функция `compute_internal_forces(state, params, eq_params)`:

Для каждого узла `i`:

1. **Вертикально:**
   - Базовая пружина/демпфер: `F_y += -k_by * u_y - c_by * v_y`
   - Связь с соседями: `k_ly*(u_{i±1}-u_i) + c_ly*(v_{i±1}-v_i)`
   - Edge stiffening на первых/последних 3 узлах

2. **Горизонтально:**
   - Базовая пружина/демпфер: `F_x += -k_bx * u_x - c_bx * v_x`
   - Связь с соседями: `k_lx*(u_{i±1}-u_i) + c_lx*(v_{i±1}-v_i)`

#### Интегратор (semi-implicit Euler)

Функция `integrate_surface(state, forces, eq_params, params, dt)`:

```python
# 1. Скорости
a_y = F_y / m_node
v_y += a_y * dt
u_y += v_y * dt

# 2. Клиппинг
v_y = clamp(v_y, -K_VELOCITY_CAP, K_VELOCITY_CAP)
u_y = clamp(u_y, -K_DISPLACEMENT_CAP, K_DISPLACEMENT_CAP)
```

#### Геометрия контакта

Функция `compute_ball_surface_y(ball_x, ball_y, radius, node_x)`:

```python
dd = ball_x - node_x
y_ball_surface = ball_y - sqrt(r^2 - dd^2)
```

Защита от отрицательного подкорня: `safe_sqrt()`.

#### Инициализация

Функция `init_surface_state(params)`:
- Равномерная сетка от `-half_width` до `+half_width`
- `n_nodes` узлов
- Нулевые смещения и скорости

## Тесты

### `tests/test_surface.py`

| Тест | Описание |
|------|----------|
| `test_init_surface_state()` | Массивы имеют корректные размеры |
| `test_compute_equivalent_params()` | Параметры вычисляются корректно |
| `test_compute_internal_forces_no_nan()` | При нулевых смещениях силы без NaN |
| `test_compute_internal_forces_with_displacement()` | При смещениях возникают силы |
| `test_integrate_surface()` | Интегрирование обновляет скорости/позиции |
| `test_compute_ball_surface_y()` | Геометрия мяча вычисляется корректно |
| `test_equivalent_params_with_spikes()` | Параметры шипов для режима out/in |

### Запуск тестов

```bash
cd python_arcade_sim
python tests/test_surface.py
```

**Результат:** ✅ All Surface tests passed!

## Структура данных поверхности

```
SurfaceState
├── x_nodes: list[float]       # Позиции узлов по X
├── u_y: list[float]           # Вертикальные смещения
├── u_x: list[float]           # Горизонтальные смещения
├── v_y: list[float]           # Вертикальные скорости
├── v_x: list[float]           # Горизонтальные скорости
├── active_nodes: list[int]    # Индексы активных узлов (контакт)
└── pressure: list[float]      # Давление в активных узлах
```

## Статус

✅ `physics/surface.py` создан  
✅ `tests/test_surface.py` создан  
✅ Все тесты проходят  
✅ `physics/__init__.py` обновлён

---

**Точка вмешательства человека #5**: Проверить: соответствует ли "геометрия узлов" и сбор параметров слоям плану (иначе дальше физика будет неверной).
