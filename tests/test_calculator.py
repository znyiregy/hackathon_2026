import math

import pytest

from src.backend.calculator import CalculationError, calculate_expression


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 3 * 4", 14),
        ("(2 + 3) * 4", 20),
        ("17 // 5", 3),
        ("17 % 5", 2),
        ("2 ** 8", 256),
        ("sqrt(81) + abs(-3)", 12),
        ("round(pi, 3)", 3.142),
        ("floor(2.9) + ceil(2.1)", 5),
        ("log(e)", 1),
    ],
)
def test_calculates_allowed_expressions(expression, expected):
    assert calculate_expression(expression) == pytest.approx(expected)


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "not valid syntax +",
        "__import__('os').getcwd()",
        "[1, 2, 3]",
        "lambda: 1",
        "unknown(2)",
        "round(number=1.2)",
        "2 ** 101",
        "1 / 0",
        "exp(1000)",
        "1e101",
    ],
)
def test_rejects_unsafe_or_invalid_expressions(expression):
    with pytest.raises(CalculationError):
        calculate_expression(expression)


def test_rejects_long_and_complex_expressions():
    with pytest.raises(CalculationError):
        calculate_expression("1" * 501)
    with pytest.raises(CalculationError):
        calculate_expression("+".join(["1"] * 60))


def test_trigonometry_is_available():
    assert calculate_expression("sin(pi / 2) + cos(0) + tan(0)") == pytest.approx(2)
    assert math.isfinite(calculate_expression("log10(1000)"))
