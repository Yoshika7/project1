"""
Fuzzy membership functions for AdaptIQ-R.
Provides triangular, trapezoidal, and linguistic evaluations for inputs and outputs.
"""

from typing import Union, Tuple, Dict


def triangular_mf(x: float, a: float, b: float, c: float) -> float:
    """
    Standard triangular membership function defined by vertices (a, b, c).
    """
    if x <= a or x >= c:
        return 0.0
    if a < x <= b:
        if b == a:
            return 1.0
        return (x - a) / (b - a)
    if b < x < c:
        if c == b:
            return 1.0
        return (c - x) / (c - b)
    return 0.0


def trapezoidal_mf(x: float, a: float, b: float, c: float, d: float) -> float:
    """
    Standard trapezoidal membership function defined by corners (a, b, c, d).
    Supports left-shoulder (a == b) and right-shoulder (c == d).
    """
    if x < a or x > d:
        return 0.0
    if a <= x < b:
        if b == a:
            return 1.0
        return (x - a) / (b - a)
    if b <= x <= c:
        return 1.0
    if c < x <= d:
        if d == c:
            return 1.0
        return (d - x) / (d - c)
    return 0.0


def evaluate_mf(x: float, params: Union[Tuple[float, float, float], Tuple[float, float, float, float]]) -> float:
    """
    Evaluates membership degree given parameter tuple.
    Length 3 = triangular; Length 4 = trapezoidal.
    """
    if len(params) == 3:
        return triangular_mf(x, params[0], params[1], params[2])
    elif len(params) == 4:
        return trapezoidal_mf(x, params[0], params[1], params[2], params[3])
    else:
        raise ValueError(f"Invalid membership parameter tuple length: {len(params)}")


class LinguisticVariable:
    """
    Represents a linguistic variable (e.g. Diversity, Mutation Rate) with fuzzy sets.
    """

    def __init__(self, name: str, min_val: float, max_val: float, terms: Dict[str, Tuple]):
        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.terms = terms

    def fuzzify(self, val: float) -> Dict[str, float]:
        """Calculates membership degrees for all terms."""
        clamped = max(self.min_val, min(self.max_val, val))
        return {term: evaluate_mf(clamped, params) for term, params in self.terms.items()}
