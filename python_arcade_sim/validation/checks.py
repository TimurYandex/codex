"""
Валидация параметров симуляции.

Проверка допустимости параметров и sanity checks перед запуском.
"""

from dataclasses import dataclass
from typing import Literal

from physics.sim_types import SimulationParams, LayerParams, BallParams
from config.constants import MATERIAL_DENSITIES


@dataclass
class ValidationResult:
    """Результат валидации."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]


def validate_layer_params(layer: LayerParams, index: int) -> tuple[list[str], list[str]]:
    """
    Проверить параметры слоя.
    
    Args:
        layer: Параметры слоя.
        index: Индекс слоя (0 = верхний).
        
    Returns:
        (errors, warnings) — списки ошибок и предупреждений.
    """
    errors = []
    warnings = []
    
    # Толщина
    if layer.thickness <= 0:
        errors.append(f"Layer {index}: thickness must be positive")
    elif layer.thickness > 0.1:
        warnings.append(f"Layer {index}: thickness > 100mm is unusual")
    
    # Жёсткости
    if layer.k_n <= 0:
        errors.append(f"Layer {index}: k_n must be positive")
    if layer.k_t <= 0:
        errors.append(f"Layer {index}: k_t must be positive")
    
    # Демпфирование
    if layer.c_n < 0:
        errors.append(f"Layer {index}: c_n cannot be negative")
    if layer.c_t < 0:
        errors.append(f"Layer {index}: c_t cannot be negative")
    
    # Трение
    if layer.mu_s < 0:
        errors.append(f"Layer {index}: mu_s cannot be negative")
    if layer.mu_k < 0:
        errors.append(f"Layer {index}: mu_k cannot be negative")
    if layer.mu_k > layer.mu_s:
        warnings.append(f"Layer {index}: mu_k > mu_s (physically unusual)")
    
    # Материал
    if layer.material not in MATERIAL_DENSITIES:
        warnings.append(f"Layer {index}: unknown material '{layer.material}'")
    
    return errors, warnings


def validate_ball_params(ball: BallParams) -> tuple[list[str], list[str]]:
    """
    Проверить параметры мяча.
    
    Args:
        ball: Параметры мяча.
        
    Returns:
        (errors, warnings) — списки ошибок и предупреждений.
    """
    errors = []
    warnings = []
    
    # Радиус
    if ball.radius <= 0:
        errors.append("Ball: radius must be positive")
    elif ball.radius > 0.1:
        warnings.append("Ball: radius > 100mm is unusual")
    
    # Масса
    if ball.mass <= 0:
        errors.append("Ball: mass must be positive")
    elif ball.mass > 1:
        warnings.append("Ball: mass > 1kg is unusual")
    
    # Момент инерции
    if ball.ifactor <= 0:
        errors.append("Ball: ifactor must be positive")
    elif ball.ifactor > 1:
        warnings.append("Ball: ifactor > 1 is unusual")
    
    # Жёсткость
    if ball.k <= 0:
        errors.append("Ball: k must be positive")
    
    # Демпфирование
    if ball.c < 0:
        errors.append("Ball: c cannot be negative")
    
    return errors, warnings


def validate_simulation_params(params: SimulationParams) -> ValidationResult:
    """
    Проверить параметры симуляции.
    
    Args:
        params: Параметры симуляции.
        
    Returns:
        ValidationResult с ошибками и предупреждениями.
    """
    errors = []
    warnings = []
    
    # Проверка мяча
    ball_errors, ball_warnings = validate_ball_params(params.ball)
    errors.extend(ball_errors)
    warnings.extend(ball_warnings)
    
    # Проверка поверхности
    if not params.surface.layers:
        errors.append("Surface: at least one layer required")
    
    for i, layer in enumerate(params.surface.layers):
        layer_errors, layer_warnings = validate_layer_params(layer, i)
        errors.extend(layer_errors)
        warnings.extend(layer_warnings)
    
    # Глобальный множитель трения
    if params.surface.fr_mul <= 0:
        errors.append("Surface: fr_mul must be positive")
    elif params.surface.fr_mul > 2:
        warnings.append("Surface: fr_mul > 2 is unusual")
    
    # Проверка столкновения
    if params.collision.speed <= 0:
        errors.append("Collision: speed must be positive")
    elif params.collision.speed > 100:
        warnings.append("Collision: speed > 100 m/s is extreme")
    
    if params.collision.angle > 0:
        warnings.append("Collision: positive angle (upward) is unusual")
    
    # Время симуляции
    if params.time_scale <= 0:
        errors.append("time_scale must be positive")
    elif params.time_scale > 0.1:
        warnings.append("time_scale > 0.1 may cause instability")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def run_sanity_checks(params: SimulationParams) -> list[str]:
    """
    Выполнить sanity checks параметров.
    
    Sanity checks — это проверки на "здравый смысл",
    которые не являются ошибками, но могут указывать на проблемы.
    
    Args:
        params: Параметры симуляции.
        
    Returns:
        Список предупреждений.
    """
    checks = []
    
    # Проверка 1: Очень мягкая поверхность
    for layer in params.surface.layers:
        if layer.k_n < 1e4:
            checks.append(f"Very soft layer: k_n={layer.k_n:.0f} N/m²")
    
    # Проверка 2: Очень высокое трение
    for layer in params.surface.layers:
        if layer.mu_s > 2:
            checks.append(f"Very high friction: mu_s={layer.mu_s:.2f}")
    
    # Проверка 3: Очень большой spin
    if abs(params.collision.spin) > 100:
        checks.append(f"Very high spin: {params.collision.spin:.1f} rad/s")
    
    # Проверка 4: Очень малая масса мяча
    if params.ball.mass < 0.001:
        checks.append(f"Very light ball: {params.ball.mass*1000:.1f} g")
    
    # Проверка 5: Экстремальный угол
    if params.collision.angle < -80:
        checks.append(f"Steep angle: {params.collision.angle:.1f} deg")
    
    return checks


def validate_and_report(params: SimulationParams) -> bool:
    """
    Проверить параметры и вывести отчёт.
    
    Args:
        params: Параметры симуляции.
        
    Returns:
        True, если параметры допустимы.
    """
    result = validate_simulation_params(params)
    
    if result.errors:
        print("Validation ERRORS:")
        for error in result.errors:
            print(f"  ❌ {error}")
    
    if result.warnings:
        print("Validation WARNINGS:")
        for warning in result.warnings:
            print(f"  ⚠️ {warning}")
    
    sanity_checks = run_sanity_checks(params)
    if sanity_checks:
        print("Sanity CHECKS:")
        for check in sanity_checks:
            print(f"  ℹ️ {check}")
    
    if result.is_valid and not result.warnings and not sanity_checks:
        print("Validation: ✅ PASSED")
    
    return result.is_valid
