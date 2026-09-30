"""
Fuzzy membership functions for AdaptIQ-R.

Provides pure-Python implementations of triangular and trapezoidal membership
functions (MFs) used in the Mamdani Fuzzy Inference System.  All functions are
decorated with ``@functools.lru_cache`` where inputs are hashable scalars,
reducing redundant MF evaluations during defuzzification.

Mathematical Definitions
------------------------
Triangular MF (a, b, c):

    μ(x) = max(0, min((x-a)/(b-a), (c-x)/(c-b)))

Trapezoidal MF (a, b, c, d):

    μ(x) = max(0, min((x-a)/(b-a), 1, (d-x)/(d-c)))

Both support degenerate cases (shoulder functions) where a==b or c==d.

Complexity
----------
All MF evaluations: O(1) — constant arithmetic, no loops.
LRU cache hit     : O(1) — hash-table lookup on (x, params) key.
"""

from __future__ import annotations

import functools
from typing import Dict, Tuple, Union

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "triangular_mf",
    "trapezoidal_mf",
    "evaluate_mf",
    "LinguisticVariable",
]

# Type alias for MF parameter tuples
MFParams = Union[Tuple[float, float, float], Tuple[float, float, float, float]]


# ---------------------------------------------------------------------------
# Cached membership function primitives
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=4096)
def triangular_mf(x: float, a: float, b: float, c: float) -> float:
    """Evaluate a triangular membership function at point ``x``.

    The triangle is defined by three vertices:

    * ``a`` — left foot (μ = 0)
    * ``b`` — peak (μ = 1)
    * ``c`` — right foot (μ = 0)

    Supports degenerate left-shoulder (a == b) and right-shoulder (b == c)
    cases where the slope is treated as vertical (step).

    Parameters
    ----------
    x:
        The crisp input value to evaluate.
    a:
        Left foot of the triangle. μ = 0 for x ≤ a.
    b:
        Peak of the triangle. μ = 1 at x = b.
    c:
        Right foot of the triangle. μ = 0 for x ≥ c.

    Returns
    -------
    float
        Membership degree in ``[0.0, 1.0]``.

    Examples
    --------
    >>> triangular_mf(0.5, 0.0, 0.5, 1.0)
    1.0
    >>> triangular_mf(0.25, 0.0, 0.5, 1.0)
    0.5

    Complexity
    ----------
    Time : O(1) — constant arithmetic.
    Cache: O(1) hit on repeated (x, a, b, c) call.
    """
    if x <= a or x >= c:
        return 0.0
    if a < x <= b:
        # Rising slope: (x - a) / (b - a)
        return 1.0 if b == a else (x - a) / (b - a)
    # Falling slope: (c - x) / (c - b)
    return 1.0 if c == b else (c - x) / (c - b)


@functools.lru_cache(maxsize=4096)
def trapezoidal_mf(x: float, a: float, b: float, c: float, d: float) -> float:
    """Evaluate a trapezoidal membership function at point ``x``.

    The trapezoid is defined by four corners:

    * ``a`` — left foot (μ = 0)
    * ``b`` — left shoulder start (μ = 1)
    * ``c`` — right shoulder end (μ = 1)
    * ``d`` — right foot (μ = 0)

    The plateau between ``b`` and ``c`` has full membership (μ = 1).
    Supports left-open (a == b) and right-open (c == d) shoulder variants.

    Parameters
    ----------
    x:
        The crisp input value to evaluate.
    a:
        Left foot. μ = 0 for x < a.
    b:
        Start of full-membership plateau.
    c:
        End of full-membership plateau.
    d:
        Right foot. μ = 0 for x > d.

    Returns
    -------
    float
        Membership degree in ``[0.0, 1.0]``.

    Examples
    --------
    >>> trapezoidal_mf(0.5, 0.0, 0.3, 0.7, 1.0)
    1.0
    >>> trapezoidal_mf(0.15, 0.0, 0.3, 0.7, 1.0)
    0.5

    Complexity
    ----------
    Time : O(1) — constant arithmetic.
    Cache: O(1) hit on repeated (x, a, b, c, d) call.
    """
    if x < a or x > d:
        return 0.0
    if a <= x < b:
        # Rising slope
        return 1.0 if b == a else (x - a) / (b - a)
    if b <= x <= c:
        return 1.0  # Flat plateau — full membership
    # Falling slope
    return 1.0 if d == c else (d - x) / (d - c)


def evaluate_mf(x: float, params: MFParams) -> float:
    """Dispatch to the correct MF primitive based on parameter tuple length.

    Determines MF shape from the length of ``params``:

    * Length 3 → :func:`triangular_mf`
    * Length 4 → :func:`trapezoidal_mf`

    Parameters
    ----------
    x:
        Crisp input value to evaluate.
    params:
        MF parameter tuple.  3-element for triangular, 4-element for
        trapezoidal.

    Returns
    -------
    float
        Membership degree in ``[0.0, 1.0]``.

    Raises
    ------
    ValueError
        If ``params`` has length other than 3 or 4.

    Complexity
    ----------
    Time : O(1) — single dispatch + cached MF call.
    """
    n = len(params)
    if n == 3:
        return triangular_mf(x, params[0], params[1], params[2])
    if n == 4:
        return trapezoidal_mf(x, params[0], params[1], params[2], params[3])
    raise ValueError(
        f"MF parameter tuple must have length 3 (triangular) or 4 (trapezoidal), "
        f"got length {n}."
    )


# ---------------------------------------------------------------------------
# Linguistic variable
# ---------------------------------------------------------------------------


class LinguisticVariable:
    """A fuzzy linguistic variable with named terms and associated MFs.

    Represents one dimension of the Mamdani FIS input or output space.
    Associates each linguistic label (e.g., "LOW", "MED", "HIGH") with an
    MF parameter tuple and provides a vectorised fuzzification method.

    Parameters
    ----------
    name:
        Human-readable name of the variable (e.g., ``"diversity"``).
    min_val:
        Minimum value of the variable's universe of discourse.
    max_val:
        Maximum value of the variable's universe of discourse.
    terms:
        Dictionary mapping term labels to MF parameter tuples.
        E.g. ``{"LOW": (0.0, 0.0, 0.5), "HIGH": (0.5, 1.0, 1.0)}``.

    Attributes
    ----------
    name : str
    min_val : float
    max_val : float
    terms : Dict[str, MFParams]

    Examples
    --------
    >>> lv = LinguisticVariable("x", 0.0, 1.0, {"LOW": (0.0, 0.0, 0.5), "HIGH": (0.5, 1.0, 1.0)})
    >>> lv.fuzzify(0.25)
    {'LOW': 0.5, 'HIGH': 0.0}
    """

    def __init__(
        self,
        name: str,
        min_val: float,
        max_val: float,
        terms: Dict[str, MFParams],
    ) -> None:
        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.terms: Dict[str, MFParams] = terms

    def fuzzify(self, val: float) -> Dict[str, float]:
        """Compute membership degrees for all terms at the given crisp value.

        Clamps ``val`` to ``[min_val, max_val]`` before evaluation to handle
        out-of-range sensor readings gracefully.

        Parameters
        ----------
        val:
            Crisp input measurement to fuzzify.

        Returns
        -------
        Dict[str, float]
            Mapping from term label to membership degree in ``[0.0, 1.0]``.
            All active terms are included; inactive terms have degree 0.0.

        Complexity
        ----------
        Time : O(T) where T = number of terms (typically 3 for LOW/MED/HIGH).
        """
        # Clamp to universe bounds — protects against sensor noise / floating error
        clamped: float = max(self.min_val, min(self.max_val, val))
        return {
            term: evaluate_mf(clamped, params)
            for term, params in self.terms.items()
        }
