"""
Sample Python project for testing.
A simple calculator module.
"""



class Calculator:
    """A simple calculator class."""

    def __init__(self, precision: int = 2):
        """
        Initialize calculator.

        Args:
            precision: Decimal precision for results
        """
        self.precision = precision
        self.history: list[str] = []

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = round(a + b, self.precision)
        self._record(f"{a} + {b} = {result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a."""
        result = round(a - b, self.precision)
        self._record(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = round(a * b, self.precision)
        self._record(f"{a} * {b} = {result}")
        return result

    def divide(self, a: float, b: float) -> float | None:
        """Divide a by b. Returns None if b is zero."""
        if b == 0:
            return None
        result = round(a / b, self.precision)
        self._record(f"{a} / {b} = {result}")
        return result

    def _record(self, operation: str) -> None:
        """Record operation in history."""
        self.history.append(operation)

    def get_history(self) -> list[str]:
        """Get calculation history."""
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear calculation history."""
        self.history.clear()


class ScientificCalculator(Calculator):
    """Extended calculator with scientific functions."""

    def __init__(self, precision: int = 6):
        super().__init__(precision)

    def power(self, base: float, exponent: float) -> float:
        """Calculate base raised to exponent."""
        result = round(base ** exponent, self.precision)
        self._record(f"{base} ^ {exponent} = {result}")
        return result

    def square_root(self, value: float) -> float | None:
        """Calculate square root. Returns None for negative values."""
        if value < 0:
            return None
        result = round(value ** 0.5, self.precision)
        self._record(f"sqrt({value}) = {result}")
        return result


def calculate_sum(numbers: list[float]) -> float:
    """Calculate sum of a list of numbers."""
    return sum(numbers)


def calculate_average(numbers: list[float]) -> float | None:
    """Calculate average of a list of numbers."""
    if not numbers:
        return None
    return sum(numbers) / len(numbers)
