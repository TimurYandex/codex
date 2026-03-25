"""
Вспомогательные математические функции для симулятора.

Все функции независимы от arcade и могут использоваться в физическом ядре.
"""

import math
from typing import Final


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Ограничить значение диапазоном [min_val, max_val]."""
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value


def sign(value: float) -> int:
    """Вернуть знак значения: -1, 0, или +1."""
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def safe_sqrt(value: float, default: float = 0.0) -> float:
    """
    Безопасный квадратный корень с защитой от отрицательных значений.
    
    Используется для вычисления y_ball_surface = sqrt(r^2 - dd^2).
    При округлениях значение под корнем может стать слегка отрицательным.
    """
    if value <= 0:
        return default
    return math.sqrt(value)


def lerp(a: float, b: float, t: float) -> float:
    """Линейная интерполяция между a и b по коэффициенту t."""
    return a + (b - a) * clamp(t, 0.0, 1.0)


def exp_decay(x: float, rate: float) -> float:
    """Экспоненциальное затухание: exp(-x * rate)."""
    return math.exp(-x * rate)


# Константы для вычислений
EPS: Final[float] = 1e-9
"""Малое число для защиты от деления на ноль и численной нестабильности."""
