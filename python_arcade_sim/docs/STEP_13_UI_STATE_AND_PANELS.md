# Шаг 13: UI — UIState и панели управления

## Цель

Реализовать состояние интерфейса (UIState) и панели управления параметрами симуляции.

## Созданные модули

### `ui/state.py`

Класс `UIState` для хранения всех параметров интерфейса.

#### Параметры столкновения

| Параметр | Тип | По умолчанию |
|----------|-----|--------------|
| `speed` | float | 10.0 м/с |
| `angle` | float | -30.0° |
| `spin` | float | 0.0 рад/с |
| `spin_dir` | "cw"/"ccw" | "cw" |

#### Параметры мяча

| Параметр | Тип | По умолчанию |
|----------|-----|--------------|
| `ball_is_hollow` | bool | False (сплошной) |
| `ball_radius` | float | 0.02 м |
| `ball_mass` | float | 0.0027 кг |
| `ball_k` | float | 1e6 Н/м |
| `ball_c` | float | 100 Н·с/м |

#### Параметры поверхности

| Параметр | Тип | По умолчанию |
|----------|-----|--------------|
| `surface_layers` | list[LayerParams] | classic (2 слоя) |
| `surface_fr_mul` | float | 1.0 |

#### Параметры анимации

| Параметр | Тип | По умолчанию |
|----------|-----|--------------|
| `time_scale` | float | 0.005 |
| `view_scale` | float | 1.0 (100%) |
| `show_overlays` | bool | True |
| `show_graphs` | bool | False |

#### Режимы

| Параметр | Тип | Описание |
|----------|-----|----------|
| `ui_mode` | UIMode | IDLE/RUNNING/PAUSED/COMPARING |
| `comparison_runs` | int | Количество прогонов для сравнения (0-3) |
| `quality` | QualityLevel | NORMAL/HIGH |

#### Методы

| Метод | Описание |
|-------|----------|
| `to_simulation_params()` | Преобразовать в SimulationParams для PhysicsModel |
| `cycle_view_scale()` | Переключить масштаб (120% → 100% → 85% → 70% → 55%) |
| `apply_surface_preset(name)` | Применить пресет поверхности |
| `add_layer()` | Добавить новый слой |
| `remove_layer(index)` | Удалить слой по индексу |
| `move_layer(index, direction)` | Переместить слой вверх/вниз |

#### Пресеты поверхности

| Пресет | Описание |
|--------|----------|
| `classic` | Топшит + губка (классическая ракетка) |
| `inv` | Инвертированная (жёсткий верхний слой) |
| `hard` | Жёсткая поверхность (один слой) |

### `ui/panels.py`

Функции для отрисовки панелей управления.

#### Базовые функции

| Функция | Описание |
|---------|----------|
| `draw_panel_background(x, y, w, h, title)` | Фон панели с заголовком |
| `draw_button(x, y, w, h, label, enabled, hover)` | Кнопка |
| `draw_slider(x, y, w, h, value, min, max, label)` | Слайдер |
| `draw_label_value(x, y, label, value)` | Пара label-value |

#### Панели параметров

| Функция | Описание |
|---------|----------|
| `draw_collision_panel(ui_state, x, y)` | Параметры столкновения |
| `draw_ball_panel(ui_state, x, y)` | Параметры мяча |
| `draw_surface_panel(ui_state, x, y)` | Параметры поверхности |
| `draw_animation_panel(ui_state, x, y)` | Параметры анимации |
| `draw_action_buttons(ui_state, x, y)` | Кнопки действий |

#### Кнопки действий

| Кнопка | Действие |
|--------|----------|
| Run/Pause | Запуск/пауза симуляции |
| Compare (0/3) | Режим сравнения (до 3 прогонов) |
| Self Test | Самопроверка (sanity checks) |
| Zoom 100% | Циклическое переключение масштаба |

## Интеграция

### Обновление `ui/__init__.py`

```python
from .panels import draw_action_buttons, draw_collision_panel, ...
from .state import UIState, UIMode

__all__ = ["UIState", "UIMode", "draw_action_buttons", ...]
```

## Статус

✅ `ui/state.py` создан  
✅ `ui/panels.py` создан  
✅ `ui/__init__.py` обновлён  
✅ Импорт работает без ошибок

---

**Точка вмешательства человека #13**: Проверить, что интерфейс соответствует плану: все элементы есть и корректно обновляют состояние до запуска.
