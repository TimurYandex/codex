# Шаг 4: Физика — каркас ядра PhysicsModel

## Цель

Создать верхнеуровневый класс `PhysicsModel` с базовой структурой для последующего добавления физики поверхности, контакта и мяча.

## Созданные модули

### `physics/model.py`

Класс `PhysicsModel` с методами:

| Метод | Описание |
|-------|----------|
| `__init__()` | Инициализация полей, режим IDLE |
| `reset(params)` | Подготовка поверхности/мяча к старту |
| `step(dt)` | Один шаг интеграции (управляется паузой/анимацией) |
| `is_finished()` | Проверка завершения симуляции |
| `get_mode()` | Получить текущий режим (PREFLIGHT/CONTACT/POST/FINISHED) |
| `get_render_snapshot()` | Вернуть снимок для рендера |
| `get_metrics()` | Вернуть итоговые метрики |
| `get_history()` | Вернуть историю для графиков |

### Режимы симуляции

1. **IDLE** — симуляция не запущена
2. **PREFLIGHT** — мяч движется к поверхности (подлёт)
3. **CONTACT** — мяч в контакте с поверхностью
4. **POST** — пост-контактный полёт
5. **FINISHED** — симуляция завершена

### Внутренняя структура

```
PhysicsModel
├── _params: SimulationParams
├── _mode: SimulationMode
├── _ball: BallState
├── _surface: SurfaceState
├── _spikes: SpikesState
├── _contact: ContactState
├── _history: SimulationHistory
├── _metrics: SimulationMetrics
├── _time: float
├── _dt: float (выбирается по качеству)
└── _no_contact_steps: int (для критерия отрыва)
```

### Заглушки методов шага

- `_step_preflight(dt)` — расчёт траектории до контакта
- `_step_contact(dt)` — расчёт сил контакта, деформации, динамики
- `_step_post(dt)` — свободный полёт с гравитацией

На этом шаге реализованы как заглушки — будут заполнены на следующих шагах.

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
cd python_arcade_sim
python tests/test_model.py
```

**Результат:** ✅ All tests passed!

## Статус

✅ `physics/model.py` создан  
✅ `tests/test_model.py` создан  
✅ Все тесты проходят  
✅ `physics/__init__.py` обновлён

---

**Точка вмешательства человека #4**: Проверить, что структура `PhysicsModel` удобна для последующего добавления surface/contact/ball.
