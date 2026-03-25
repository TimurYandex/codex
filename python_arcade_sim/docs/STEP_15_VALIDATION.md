# Шаг 15: Валидация параметров и checks

## Цель

Реализовать валидацию параметров симуляции и sanity checks перед запуском.

## Созданные модули

### `validation/checks.py`

Модуль с функциями валидации параметров.

#### Структуры данных

**ValidationResult:**
```python
@dataclass
class ValidationResult:
    is_valid: bool       # Все ли проверки пройдены
    errors: list[str]    # Список ошибок
    warnings: list[str]  # Список предупреждений
```

#### Функции валидации

| Функция | Описание |
|---------|----------|
| `validate_layer_params(layer, index)` | Проверить параметры слоя |
| `validate_ball_params(ball)` | Проверить параметры мяча |
| `validate_simulation_params(params)` | Проверить все параметры симуляции |
| `run_sanity_checks(params)` | Выполнить sanity checks |
| `validate_and_report(params)` | Проверить и вывести отчёт |

#### Проверки параметров слоя

| Параметр | Проверка | Ошибка/Предупреждение |
|----------|----------|----------------------|
| thickness | > 0 | error |
| thickness | > 100mm | warning |
| k_n, k_t | > 0 | error |
| c_n, c_t | >= 0 | error |
| mu_s, mu_k | >= 0 | error |
| mu_k > mu_s | - | warning (physically unusual) |
| material | в MATERIAL_DENSITIES | warning |

#### Проверки параметров мяча

| Параметр | Проверка | Ошибка/Предупреждение |
|----------|----------|----------------------|
| radius | > 0 | error |
| radius | > 100mm | warning |
| mass | > 0 | error |
| mass | > 1kg | warning |
| ifactor | > 0 | error |
| ifactor | > 1 | warning |
| k | > 0 | error |
| c | >= 0 | error |

#### Проверки столкновения

| Параметр | Проверка | Ошибка/Предупреждение |
|----------|----------|----------------------|
| speed | > 0 | error |
| speed | > 100 m/s | warning |
| angle | > 0 | warning (upward is unusual) |

#### Sanity checks

Проверки на "здравый смысл":

1. **Очень мягкая поверхность:** k_n < 1e4 Н/м²
2. **Очень высокое трение:** mu_s > 2
3. **Очень большой spin:** |spin| > 100 rad/s
4. **Очень малая масса мяча:** mass < 1 г
5. **Экстремальный угол:** angle < -80°

## Интеграция

### Обновление `validation/__init__.py`

```python
from .checks import (
    ValidationResult,
    validate_simulation_params,
    validate_and_report,
    ...
)

__all__ = ["ValidationResult", "validate_simulation_params", ...]
```

### Использование в UI

```python
from validation.checks import validate_and_report

params = ui_state.to_simulation_params()
if not validate_and_report(params):
    # Показать ошибки пользователю
    return
```

## Статус

✅ `validation/checks.py` создан  
✅ `validation/__init__.py` обновлён  
✅ Импорт работает без ошибок

---

**Точка вмешательства человека #15**: Проверить, что неверные вводы не приводят к падениям (или приводят, но с понятной диагностикой).
