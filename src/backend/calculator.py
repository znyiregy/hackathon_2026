"""A deliberately small and safe mathematical expression evaluator."""

import ast
import math
import operator
from collections.abc import Callable


MAX_EXPRESSION_LENGTH = 500
MAX_AST_NODES = 100
MAX_EXPONENT = 100
MAX_ABSOLUTE_VALUE = 1e100


class CalculationError(ValueError):
    """Raised when an expression is invalid or outside the safety limits."""


_BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_CONSTANTS = {"pi": math.pi, "e": math.e}
_FUNCTIONS: dict[str, Callable[..., float]] = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
}


def _validate_result(value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CalculationError("The expression did not produce a number.")
    try:
        finite = math.isfinite(value)
    except OverflowError as exc:
        raise CalculationError("The result is too large.") from exc
    if not finite:
        raise CalculationError("The result must be finite.")
    if abs(value) > MAX_ABSOLUTE_VALUE:
        raise CalculationError("The result is too large.")
    return value


def _evaluate(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant):
        return _validate_result(node.value)

    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return _CONSTANTS[node.id]

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _validate_result(_UNARY_OPERATORS[type(node.op)](_evaluate(node.operand)))

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise CalculationError(f"Exponents must be between {-MAX_EXPONENT} and {MAX_EXPONENT}.")
        try:
            result = _BINARY_OPERATORS[type(node.op)](left, right)
        except (ArithmeticError, OverflowError, ValueError) as exc:
            raise CalculationError(str(exc)) from exc
        return _validate_result(result)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS:
            raise CalculationError("That function is not allowed.")
        if node.keywords:
            raise CalculationError("Keyword arguments are not allowed.")
        arguments = [_evaluate(argument) for argument in node.args]
        try:
            result = _FUNCTIONS[node.func.id](*arguments)
        except (ArithmeticError, OverflowError, TypeError, ValueError) as exc:
            raise CalculationError(str(exc)) from exc
        return _validate_result(result)

    raise CalculationError(f"Unsupported expression element: {type(node).__name__}.")


def calculate_expression(expression: str) -> int | float:
    """Evaluate a restricted mathematical expression without using ``eval``."""

    expression = expression.strip()
    if not expression:
        raise CalculationError("The expression is empty.")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise CalculationError(f"Expressions may contain at most {MAX_EXPRESSION_LENGTH} characters.")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalculationError("The expression is not valid syntax.") from exc

    if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
        raise CalculationError(f"Expressions may contain at most {MAX_AST_NODES} syntax elements.")
    return _evaluate(tree.body)
